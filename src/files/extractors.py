"""
Text extraction from various file formats.

This module provides functions to extract text content from PDF and TXT files.
It utilizes the `pypdf` library for PDF parsing and handles common exceptions to ensure
robust text extraction.
"""

import logging
import os
import time
from typing import Optional

import pypdf

__all__ = ["extract_text_from_pdf", "extract_text_from_txt"]

logger = logging.getLogger(__name__)

# Warn if PDF file exceeds this size (10MB)
LARGE_PDF_THRESHOLD_BYTES = 10 * 1024 * 1024


def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """
    Extract text content from a PDF file.

    Args:
        file_path (str): The path to the PDF file from which to extract text.

    Returns:
        Optional[str]: The extracted text as a string if successful; otherwise, None.
    """
    start_time = time.perf_counter()

    try:
        # Check file size and warn if large
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        if file_size > LARGE_PDF_THRESHOLD_BYTES:
            logger.warning(
                "Large PDF file detected: %.2fMB (may take longer to process)",
                file_size_mb,
            )

        logger.debug("Extracting text from PDF: %s (%.2fMB)", file_path, file_size_mb)

        with open(file_path, "rb") as file:
            reader = pypdf.PdfReader(file)
            num_pages = len(reader.pages)
            logger.debug("PDF has %d pages", num_pages)

            content: str = "\n".join(
                [page.extract_text() for page in reader.pages if page.extract_text()]
            )

        elapsed = time.perf_counter() - start_time
        logger.info(
            "Extracted %d characters from PDF (%.2fs, %d pages)",
            len(content),
            elapsed,
            num_pages,
        )
        return content

    except IOError as e:
        elapsed = time.perf_counter() - start_time
        logger.error(
            "Error opening PDF file %s (failed after %.2fs): %s\n"
            "  → Check file permissions\n"
            "  → Verify file is not corrupted\n"
            "  → Ensure file exists at path",
            file_path,
            elapsed,
            e,
            exc_info=True,
        )
    except pypdf.errors.PdfReadError as e:
        elapsed = time.perf_counter() - start_time
        logger.error(
            "Error reading PDF file %s (failed after %.2fs): %s\n"
            "  → PDF may be corrupted or password-protected\n"
            "  → Try opening in PDF reader to verify\n"
            "  → Check if PDF is a scanned image (OCR required)",
            file_path,
            elapsed,
            e,
            exc_info=True,
        )
    except ValueError as e:
        elapsed = time.perf_counter() - start_time
        logger.error(
            "Value error extracting from PDF %s (failed after %.2fs): %s\n"
            "  → PDF structure may be invalid\n"
            "  → Try re-saving PDF in a PDF editor",
            file_path,
            elapsed,
            e,
            exc_info=True,
        )
    return None


def extract_text_from_txt(file_path: str) -> Optional[str]:
    """
    Extract text content from a TXT file.

    Args:
        file_path (str): The path to the text file from which to extract text.

    Returns:
        Optional[str]: The extracted text as a string if successful; otherwise, None.
    """
    try:
        file_size = os.path.getsize(file_path)
        file_size_kb = file_size / 1024

        logger.debug("Extracting text from TXT: %s (%.2fKB)", file_path, file_size_kb)

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        logger.debug("Extracted %d characters from TXT file", len(content))
        return content

    except IOError as e:
        logger.error(
            "Error opening text file %s: %s\n"
            "  → Check file permissions\n"
            "  → Verify file exists at path",
            file_path,
            e,
            exc_info=True,
        )
    except UnicodeDecodeError as e:
        logger.error(
            "Error decoding text file %s: %s\n"
            "  → File may not be UTF-8 encoded\n"
            "  → Try converting to UTF-8 encoding\n"
            "  → Check if file is actually binary (not text)",
            file_path,
            e,
            exc_info=True,
        )
    return None
