import logging

import PyPDF2

logger = logging.getLogger(__name__)


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
        logger.debug(f"Extracted text from PDF '{file_path}'")
        return content
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}", exc_info=True)
        return ""


def extract_text_from_txt(file_path):
    """
    Extracts text from a text file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            logger.debug(f"Extracted text from TXT '{file_path}'")
            return content
    except Exception as e:
        logger.error(f"Error extracting text from text file: {
                     e}", exc_info=True)
        return ""
