import logging
from typing import Optional

import pypdf

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """
    Extracts text from a PDF file.
    """
    try:
        with open(file_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            content: str = ""
            for page in reader.pages:
                content += page.extract_text() + "\n"
        logger.debug("Extracted text from PDF '%s'", file_path)
        return content
    except Exception as e:
        logger.error("Error extracting text from PDF: %s", e, exc_info=True)
        return None


def extract_text_from_txt(file_path: str) -> Optional[str]:
    """
    Extracts text from a text file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content: str = file.read()
            logger.debug("Extracted text from TXT '%s'", file_path)
            return content
    except Exception as e:
        logger.error("Error extracting text from text file: %s", e,
                     exc_info=True)
        return None
