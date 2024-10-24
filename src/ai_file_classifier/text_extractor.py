import logging
from typing import Optional

import pypdf

# Configure logging
logging.basicConfig(level=logging.DEBUG)
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
        logger.debug(f"Extracted text from PDF '{file_path}'")
        return content
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}", exc_info=True)
        return None


def extract_text_from_txt(file_path: str) -> Optional[str]:
    """
    Extracts text from a text file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content: str = file.read()
            logger.debug(f"Extracted text from TXT '{file_path}'")
            return content
    except Exception as e:
        logger.error(f"Error extracting text from text file: {
                     e}", exc_info=True)
        return None
