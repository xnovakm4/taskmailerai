import imaplib
import smtplib
import email
import logging
from email.message import EmailMessage

class EmailHandler:
    def __init__(self, config):
        """
        Inicializace handleru s konfigurací
        
        Args:
            config (dict): Slovník s konfigurací obsahující:
                - email.imap_server: IMAP server address
                - email.smtp_server: SMTP server address
                - email.email_address: Email address
                - email.password: Password
        """
        self.imap_server = config['email']['imap_server']
        self.smtp_server = config['email']['smtp_server']
        self.email_address = config['email']['email_address']
        self.password = config['email']['password']
        self.imap = None
        self.smtp = None
        
        # Nastavení loggeru
        self.logger = logging.getLogger(__name__)
        
    def connect_imap(self):
        """Připojení k IMAP serveru"""
        try:
            self.imap = imaplib.IMAP4_SSL(self.imap_server)
            self.imap.login(self.email_address, self.password)
            self.imap.select('inbox')
            self.logger.info("Úspěšně připojeno k IMAP serveru")
        except Exception as e:
            self.logger.error(f"Chyba při připojování k IMAP serveru: {e}")
            self.imap = None
            raise

    def connect_smtp(self):
        """Připojení k SMTP serveru"""
        try:
            self.smtp = smtplib.SMTP_SSL(self.smtp_server, timeout=30)
            self.smtp.login(self.email_address, self.password)
            self.logger.info("Úspěšně připojeno k SMTP serveru")
        except Exception as e:
            self.logger.error(f"Chyba při připojování k SMTP serveru: {e}")
            self.smtp = None
            raise

    def check_smtp_connection(self):
        """Kontrola SMTP připojení a případné znovupřipojení"""
        try:
            if self.smtp:
                self.smtp.noop()
            else:
                self.connect_smtp()
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPResponseException):
            self.logger.warning("SMTP spojení ztraceno, pokus o znovupřipojení")
            try:
                self.smtp = None
                self.connect_smtp()
            except Exception as e:
                self.logger.error(f"Nelze obnovit SMTP spojení: {e}")
                raise

    def disconnect(self):
        """Bezpečné odpojení od IMAP a SMTP serverů"""
        if self.imap:
            try:
                self.imap.logout()
                self.logger.info("Úspěšně odpojeno od IMAP serveru")
            except Exception as e:
                self.logger.warning(f"Chyba při odpojování od IMAP: {e}")
            finally:
                self.imap = None
                
        if self.smtp:
            try:
                self.check_smtp_connection()
                self.smtp.quit()
                self.logger.info("Úspěšně odpojeno od SMTP serveru")
            except Exception as e:
                self.logger.warning(f"Chyba při odpojování od SMTP: {e}")
            finally:
                self.smtp = None

    def fetch_unseen_emails(self):
        """
        Načtení nepřečtených emailů
        
        Returns:
            list: Seznam nepřečtených emailů
        """
        try:
            if not self.imap:
                self.connect_imap()
                
            status, messages = self.imap.search(None, '(UNSEEN)')
            email_id_list = messages[0].split()
            emails = []
            
            for email_id in email_id_list:
                try:
                    status, msg_data = self.imap.fetch(email_id, '(RFC822)')
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            emails.append(msg)
                except Exception as e:
                    self.logger.error(f"Chyba při načítání emailu {email_id}: {e}")
                    continue
                    
            self.logger.info(f"Úspěšně načteno {len(emails)} nepřečtených emailů")
            return emails
            
        except Exception as e:
            self.logger.error(f"Chyba při načítání nepřečtených emailů: {e}")
            raise

    def send_email(self, to_address, subject, body, attachment=None, max_retries=3):
        """
        Odeslání emailu s možností opakování při selhání
        
        Args:
            to_address (str): Cílová emailová adresa
            subject (str): Předmět emailu
            body (str): Tělo emailu
            attachment (dict, optional): Slovník s přílohou obsahující 'content' a 'filename'
            max_retries (int): Maximální počet pokusů o odeslání
        
        Returns:
            bool: True pokud byl email úspěšně odeslán
        """
        for attempt in range(max_retries):
            try:
                self.check_smtp_connection()
                
                msg = EmailMessage()
                msg['Subject'] = subject
                msg['From'] = self.email_address
                msg['To'] = to_address
                msg.set_content(body)

                if attachment:
                    msg.add_attachment(
                        attachment['content'],
                        maintype='application',
                        subtype='octet-stream',
                        filename=attachment['filename']
                    )

                self.smtp.send_message(msg)
                self.logger.info(f"Email úspěšně odeslán na {to_address}")
                return True

            except (smtplib.SMTPServerDisconnected, smtplib.SMTPResponseException) as e:
                self.logger.warning(f"Pokus {attempt + 1} o odeslání selhal: {e}")
                self.smtp = None  # Reset spojení
                
                if attempt == max_retries - 1:
                    self.logger.error("Vyčerpány všechny pokusy o odeslání emailu")
                    raise
                    
            except Exception as e:
                self.logger.error(f"Neočekávaná chyba při odesílání emailu: {e}")
                raise

