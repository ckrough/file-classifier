"""
Module for extracting text from various file formats.

This module provides functions to extract text content from PDF and TXT files.
It utilizes the `pypdf` library for PDF parsing and handles common exceptions to ensure
robust text extraction. The extracted text can be used for further analysis or processing
within the AI File Classifier application.
"""

import logging
from typing import Optional

import pypdf

__all__ = ["extract_text_from_pdf", "extract_text_from_txt"]

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """
    Extracts text content from a PDF file.

    Args:
        file_path (str): The path to the PDF file from which to extract text.

    Returns:
        Optional[str]: The extracted text as a string if successful; otherwise, None.
    """
    try:
        with open(file_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            content: str = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
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
    Extracts text content from a TXT file.

    Args:
        file_path (str): The path to the text file from which to extract text.

    Returns:
        Optional[str]: The extracted text as a string if successful; otherwise, None.
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
