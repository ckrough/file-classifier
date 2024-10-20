import logging

import PyPDF2


def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF file.
    """
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n"
        return content
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_txt(file_path):
    """
    Extracts text from a text file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error extracting text from text file: {e}")
        return ""
