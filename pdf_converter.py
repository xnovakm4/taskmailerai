# pdf_converter.py

import pdfkit
import markdown
import os
import tempfile
from markdown.extensions import tables, fenced_code, attr_list, def_list, footnotes



def convert_markdown_to_pdf(markdown_text):
    """
    Převádí markdownový text na PDF a vrací obsah PDF jako bytes.

    Parametry:
        markdown_text (str): Vstupní markdownový text.

    Návratová hodnota:
        bytes: Obsah generovaného PDF souboru.
    """

    # Seznam použitých rozšíření
    extensions = [
        'tables',                    # podpora tabulek
        'fenced_code',              # podpora ohraničených bloků kódu
        'attr_list',                # podpora HTML atributů
        'def_list',                 # podpora definičních seznamů
        'footnotes',                # podpora poznámek pod čarou
        'markdown.extensions.nl2br', # převod nových řádků na <br>
        'markdown.extensions.sane_lists', # lepší zpracování seznamů
    ]

    # Převod markdownu na HTML
    html_content = markdown.markdown(markdown_text, extensions=extensions)

    options = {
        'encoding': 'UTF-8',
        'enable-local-file-access': None,
        'margin-top': '20mm',
        'margin-right': '20mm',
        'margin-bottom': '20mm',
        'margin-left': '20mm'
    }

    # CSS styly
    css_styles = """
    <style>
    body { font-family: Arial; line-height: 1.6; margin: 20px; }
    table { border-collapse: collapse; width: 100%; margin: 15px 0; border: 2px solid black; }
    th, td { border: 1px solid black; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; font-weight: bold; }
    tr:nth-child(even) { background-color: #f9f9f9; }
    </style>
    """

    # Sestavení HTML dokumentu
    html_template = (
        "<!DOCTYPE html>"
        "<html>"
        "<head>"
        "<meta charset='UTF-8'>"
        f"{css_styles}"
        "</head>"
        "<body>"
        f"{html_content}"
        "</body>"
        "</html>"
    )
    
    # Nastavení dočasného souboru pro výstup PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        pdfkit.from_string(html_template, tmp_file.name, options=options)
        tmp_file.seek(0)
        pdf_content = tmp_file.read()
    # Odstranění dočasného souboru
    os.unlink(tmp_file.name)
    return pdf_content