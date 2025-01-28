# main.py

import time
import email
import email.utils
import logging
import argparse
import sys
from config_loader import load_config, load_tasks
from email_handler import EmailHandler
from ai_agent import AIAgent
from attachment_processor import extract_text_from_attachment
from pdf_converter import convert_markdown_to_pdf
from rate_limiter import RateLimiter
import os
import re

def get_charset(part):
    """Získá charset z části emailu, defaultně vrací 'utf-8'"""
    if part.get_content_charset():
        return part.get_content_charset()
    return 'utf-8'

def get_task_from_subject(subject, tasks):
    task_name, api, model = parse_subject(subject)
    for task in tasks:
        if task['subject'].lower() == task_name.lower():
            task['api'] = api
            task['model'] = model
            return task
    return None

def parse_subject(subject):
    pattern = r'^((?:RE:|FW:)\s*)?(\w*)(\s*\((\w*)(:(.*))?\))?$'
    match = re.match(pattern, subject, re.IGNORECASE)
    logging.debug(f"Parsuji subject: {subject}")
    if match:
        task_name = match.group(2).strip()
        if match.group(4):
            api = match.group(4).strip()
        else:
            api = None
        if match.group(6):
            model = match.group(6).strip()
        else:
            model = None
        logging.debug(f"Identifikován úkol: {task_name}, API: {api}, Model: {model}")
        return task_name, api, model
    logging.debug(f"Nebyl nalezen žádný úkol v subjectu: {subject}")
    return subject, None, None

def get_email_content(msg):
    body = ""
    attachments = []
    
    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = part.get("Content-Disposition", "")
            if part.get_content_type() == 'text/plain' and 'attachment' not in content_disposition:
                # Tělo e-mailu
                charset = get_charset(part)
                try:
                    # Zkusíme nejdřív původní charset
                    body += part.get_payload(decode=True).decode(charset)
                except UnicodeDecodeError:
                    try:
                        # Pokud selže, zkusíme windows-1250 (běžné pro české emaily)
                        body += part.get_payload(decode=True).decode('windows-1250')
                    except UnicodeDecodeError:
                        try:
                            # Případně iso-8859-2
                            body += part.get_payload(decode=True).decode('iso-8859-2')
                        except UnicodeDecodeError:
                            # Pokud vše selže, použijeme 'utf-8' s ignorováním chyb
                            body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
            elif 'attachment' in content_disposition:
                # Příloha - zde zůstává stejné
                filename = part.get_filename()
                if filename:
                    attachment_content = part.get_payload(decode=True)
                    attachments.append({
                        'filename': filename,
                        'content': attachment_content,
                        'content_type': part.get_content_type()
                    })
    else:
        # Jednoduché zprávy bez multipart
        body = msg.get_payload(decode=True).decode()
    
    return body, attachments

def process_email(msg, email_handler, ai_agent, config, tasks, rate_limiter):

    # Omezení pro přílohy
    MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_ATTACHMENTS = config['app_settings']['max_attachments']
    ALLOWED_EXTENSIONS = ['.txt', '.md', '.csv', '.json', '.pdf', '.docx']

    subject = msg['subject']
    from_email = email.utils.parseaddr(msg['From'])[1]
    allowed_users = config['allowed_users']

    # Ověření, zda je uživatel povolen
    user_config = allowed_users.get(from_email.lower())
    if not user_config:
        logging.warning(f"Uživatel {from_email.lower()} není oprávněn používat tuto službu.")
        return

    # Načtení rate limitu pro uživatele s defaultními hodnotami
    rate_limit_defaults = config.get('rate_limit_defaults', {'max_requests': 10, 'time_window': 3600})
    rate_limit = user_config.get('rate_limit', {})
    max_requests = rate_limit.get('max_requests', rate_limit_defaults['max_requests'])
    time_window = rate_limit.get('time_window', rate_limit_defaults['time_window'])

    # Ověření rate limitu
    if not rate_limiter.is_allowed(from_email, max_requests, time_window):
        time_until_reset = rate_limiter.get_time_until_reset(from_email, time_window)
        logging.warning(f"Uživatel {from_email} překročil limit požadavků. Další požadavek může odeslat za {time_until_reset} sekund.")
        # Odeslání e-mailu s upozorněním
        email_handler.send_email(
            to_address=from_email,
            subject="Limit požadavků překročen",
            body=f"Překročili jste maximální počet {max_requests} požadavků za poslední časové okno. Prosím, zkuste to znovu za {time_until_reset} sekund."
        )
        return

    task = get_task_from_subject(subject, tasks)
    if task:
        body, attachments = get_email_content(msg)

        # Filtrování a omezení příloh
        if len(attachments) > MAX_ATTACHMENTS:
            logging.warning(f"Příliš mnoho příloh. Maximální počet je {MAX_ATTACHMENTS}.")
            email_handler.send_email(
                to_address=from_email,
                subject="Příliš mnoho příloh",
                body=f"Vaše zpráva obsahuje příliš mnoho příloh. Maximální povolený počet je {MAX_ATTACHMENTS}."
            )
            return

        valid_attachments = []
        for attachment in attachments:
            _, file_extension = os.path.splitext(attachment['filename'])
            if file_extension.lower() in ALLOWED_EXTENSIONS:
                if len(attachment['content']) <= MAX_ATTACHMENT_SIZE:
                    valid_attachments.append(attachment)
                else:
                    logging.warning(f"Příloha {attachment['filename']} je příliš velká a bude přeskočena.")
            else:
                logging.warning(f"Přípona {file_extension} není podporována. Příloha {attachment['filename']} bude přeskočena.")

        # Zpracování příloh
        attachments_text = ""
        for attachment in valid_attachments:
            text = extract_text_from_attachment(attachment)
            if text:
                attachments_text += f"\n[Obsah přílohy {attachment['filename']}]:\n{text}\n"
            else:
                logging.warning(f"Příloha {attachment['filename']} nelze zpracovat nebo je prázdná.")

        # Vytvoření promptu pro AI model
        prompt = f"{task['base_prompt']}\n{body}\n{attachments_text}"

        if task['api'] == 'openai':
            ai_response = ai_agent.call_openai_api(prompt, model=task['model'] if task['model'] else None)
        elif task['api'] == 'openrouter':
            ai_response = ai_agent.call_openrouter_api(prompt, model=task['model'] if task['model'] else None)
        elif task['api'] == 'azure':
            ai_response = ai_agent.call_azure_openai_api(prompt, model=task['model'] if task['model'] else None)
        elif task['api'] == 'ollama':
            ai_response = ai_agent.call_ollama_api(prompt, model=task['model'] if task['model'] else None)
        else:
            # Default to OpenAI API if no API specified
            ai_response = ai_agent.call_openai_api(prompt, model=task['model'] if task['model'] else None)

        if ai_response:
            if task['output_format'] == 'pdf':
                pdf_content = convert_markdown_to_pdf(ai_response)
                attachment = {
                    'content': pdf_content,
                    'filename': 'vysledek.pdf'
                }
                email_handler.send_email(
                    to_address=from_email,
                    subject="Výsledek úkolu",
                    body="Viz příloha.",
                    attachment=attachment
                )
            else:
                logging.warning(f"Send Email - Odpověď od AI: {ai_response}")
                email_handler.send_email(
                    to_address=from_email,
                    subject="Výsledek úkolu",
                    body=ai_response
                )
        else:
            logging.error("Nepodařilo se získat odpověď od AI.")
    else:
        logging.warning(f"Nenašel jsem odpovídající úkol pro předmět: {subject}")

def process_cli_task(task_name, input_text, input_file, api, model, subject, config, tasks, ai_agent):
    """Zpracuje úkol přímo z příkazové řádky"""
    # Najít odpovídající úkol
    task = None
    
    if subject:
        # Použít stejné zpracování jako u emailů
        task = get_task_from_subject(subject, tasks)
        if not task:
            print(f"Chyba: Úkol ze subjectu '{subject}' nebyl nalezen.")
            print("Dostupné úkoly:")
            for t in tasks:
                print(f"- {t['subject']}")
            return
    else:
        # Původní zpracování pomocí task_name
        for t in tasks:
            if t['subject'].lower() == task_name.lower():
                task = t.copy()
                # Použít explicitní parametry pouze pokud subject není zadán
                task['api'] = api
                task['model'] = model
                break
    
    if not task:
        print(f"Chyba: Úkol '{task_name}' nebyl nalezen.")
        print("Dostupné úkoly:")
        for t in tasks:
            print(f"- {t['subject']}")
        return

    # Získat vstupní text
    if input_file:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Chyba při čtení souboru: {e}")
            return
    else:
        content = input_text if input_text else sys.stdin.read()

    # Vytvořit prompt
    prompt = f"{task['base_prompt']}\n{content}"

    # Zpracovat pomocí AI
    try:
        # Použít model z command line pokud je zadán, jinak použít model z tasku
        selected_model = model if model else task['model']
        
        if task['api'] == 'openai':
            ai_response = ai_agent.call_openai_api(prompt, model=selected_model)
        elif task['api'] == 'openrouter':
            ai_response = ai_agent.call_openrouter_api(prompt, model=selected_model)
        elif task['api'] == 'azure':
            ai_response = ai_agent.call_azure_openai_api(prompt, model=selected_model)
        elif task['api'] == 'ollama':
            ai_response = ai_agent.call_ollama_api(prompt, model=selected_model)
        else:
            ai_response = ai_agent.call_openai_api(prompt, model=selected_model)

        if ai_response:
            if task['output_format'] == 'pdf':
                pdf_content = convert_markdown_to_pdf(ai_response)
                output_file = 'vysledek.pdf'
                with open(output_file, 'wb') as f:
                    f.write(pdf_content)
                print(f"Výsledek byl uložen do souboru: {output_file}")
            else:
                print(ai_response)
        else:
            print("Chyba: Nepodařilo se získat odpověď od AI.")
    except Exception as e:
        print(f"Chyba při zpracování úkolu: {e}")

def main():
    parser = argparse.ArgumentParser(description='TaskMailer AI - Zpracování úkolů pomocí AI')
    parser.add_argument('--task', '-t', help='Název úkolu k provedení (nepoužívat společně s --subject)')
    parser.add_argument('--subject', '-s', help='Subject ve formátu jako u emailu, např. "Shrnuti (openai:gpt-4)"')
    parser.add_argument('--input', '-i', help='Vstupní text pro zpracování')
    parser.add_argument('--file', '-f', help='Cesta k souboru se vstupním textem')
    parser.add_argument('--api', help='API k použití (openai, openrouter, azure, ollama) - ignorováno při použití --subject')
    parser.add_argument('--model', help='Model k použití - ignorováno při použití --subject')
    parser.add_argument('--list-tasks', '-l', action='store_true', help='Vypíše dostupné úkoly')
    
    args = parser.parse_args()
    
    config = load_config()
    tasks = load_tasks()
    
    # Výpis dostupných úkolů
    if args.list_tasks:
        print("Dostupné úkoly:")
        for task in tasks:
            print(f"- {task['subject']}")
        return

    # CLI mód
    if args.task and args.subject:
        print("Chyba: Nelze použít --task a --subject současně. Použijte pouze jeden z parametrů.")
        return
        
    if args.task or args.subject:
        ai_agent = AIAgent(config)
        process_cli_task(args.task, args.input, args.file, args.api, args.model, args.subject, config, tasks, ai_agent)
        return

    # Email mód
    email_handler = EmailHandler(config)
    ai_agent = AIAgent(config)
    rate_limiter = RateLimiter()

    try:
        while True:
            email_handler.connect_imap()
            email_handler.connect_smtp()
            emails = email_handler.fetch_unseen_emails()
            logging.warning(f"Kontroluji emaily")
            for msg in emails:
                subject = msg['subject']
                logging.warning(f"Procesuji email s predmetem: {subject}")
                process_email(msg, email_handler, ai_agent, config, tasks, rate_limiter)
            time.sleep(2)    
            email_handler.disconnect()
            time.sleep(config.get('app_settings', {}).get('check_interval', 60))
    except KeyboardInterrupt:
        logging.info("Ukončuji aplikaci...")
    except Exception as e:
        logging.error(f"Neočekávaná chyba: {e}")
    finally:
        email_handler.disconnect()

if __name__ == "__main__":
    main()
