"""
This module provides functions for extracting text from different file types.
"""

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
    except IOError as e:
        logger.error("Error opening PDF file: %s", e, exc_info=True)
    except pypdf.errors.PdfReadError as e:
        logger.error("Error reading PDF file: %s", e, exc_info=True)
    except ValueError as e:
        logger.error("Value error in PDF extraction: %s", e, exc_info=True)
    return None


def extract_text_from_txt(file_path: str) -> Optional[str]:
    """
    Extracts text from a text file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        logger.debug("Extracted text from TXT '%s'", file_path)
        return content
    except IOError as e:
        logger.error("Error opening text file: %s", e, exc_info=True)
    except UnicodeDecodeError as e:
        logger.error("Error decoding text file: %s", e, exc_info=True)
    return None
