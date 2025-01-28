# attachment_processor.py

import os
import tempfile
from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_attachment(attachment):
    """
    Extrahuje text z přílohy na základě typu souboru.

    Parametry:
        attachment (dict): Slovník obsahující informace o příloze:
            - 'filename': název souboru
            - 'content': obsah souboru v bytes
            - 'content_type': MIME typ obsahu

    Návratová hodnota:
        str: Extrahovaný text z přílohy nebo prázdný řetězec, pokud typ není podporován.
    """
    filename = attachment['filename']
    content = attachment['content']
    content_type = attachment['content_type']
    _, file_extension = os.path.splitext(filename)
    file_extension = file_extension.lower()
    
    if file_extension in ['.txt', '.md', '.csv', '.json']:
        # Předpokládáme textový obsah, dekódujeme do řetězce
        text = content.decode('utf-8', errors='ignore')
    elif file_extension == '.pdf':
        text = extract_text_from_pdf(content)
    elif file_extension == '.docx':
        text = extract_text_from_docx(content)
    else:
        # Nepodporovaný typ souboru
        text = ""
    return text

def extract_text_from_pdf(pdf_content):
    """
    Extrahuje text z PDF souboru.

    Parametry:
        pdf_content (bytes): Obsah PDF souboru v bytes.

    Návratová hodnota:
        str: Extrahovaný text z PDF.
    """
    text = ""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(pdf_content)
        tmp_file.flush()
        reader = PdfReader(tmp_file.name)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

def extract_text_from_docx(docx_content):
    """
    Extrahuje text z DOCX souboru.

    Parametry:
        docx_content (bytes): Obsah DOCX souboru v bytes.

    Návratová hodnota:
        str: Extrahovaný text z DOCX.
    """
    text = ""
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
        tmp_file.write(docx_content)
        tmp_file.flush()
        doc = Document(tmp_file.name)
        text = "\n".join([para.text for para in doc.paragraphs])
    return text