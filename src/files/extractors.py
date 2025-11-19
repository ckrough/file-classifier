"""
Text extraction from various file formats.

This module provides functions to extract text content from PDF and TXT files.
It utilizes the `pypdf` library for PDF parsing and handles common exceptions to ensure
robust text extraction.
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Literal, Optional

import pypdf

__all__ = ["extract_text_from_pdf", "extract_text_from_txt", "ExtractionConfig"]

logger = logging.getLogger(__name__)

# Warn if PDF file exceeds this size (10MB)
LARGE_PDF_THRESHOLD_BYTES = 10 * 1024 * 1024


@dataclass
class ExtractionConfig:
    """
    Configuration for content extraction strategies.

    Attributes:
        strategy: Extraction strategy to use:
            - "full": Extract all content (backward compatible default)
            - "first_n_pages": Extract first N pages (optionally + last page)
            - "char_limit": Extract until character limit reached
            - "adaptive": Smart strategy based on document size/page count
        max_pages: Maximum number of pages to extract (for page-based strategies)
        max_chars: Maximum characters to extract (character limit safety net)
        include_last_page: Whether to include last page (for multi-page documents)
    """

    strategy: Literal["full", "first_n_pages", "char_limit", "adaptive"] = "adaptive"
    max_pages: Optional[int] = 3
    max_chars: Optional[int] = 10_000
    include_last_page: bool = True

    @classmethod
    def from_env(cls) -> "ExtractionConfig":
        """
        Load extraction configuration from environment variables.

        Returns:
            ExtractionConfig: Configuration loaded from environment with defaults
        """
        return cls(
            strategy=os.getenv("CLASSIFICATION_STRATEGY", "adaptive"),  # type: ignore
            max_pages=int(os.getenv("CLASSIFICATION_MAX_PAGES", "3")),
            max_chars=int(os.getenv("CLASSIFICATION_MAX_CHARS", "10000")),
            include_last_page=os.getenv(
                "CLASSIFICATION_INCLUDE_LAST_PAGE", "true"
            ).lower()
            == "true",
        )


def _get_pages_to_extract(
    num_pages: int, file_path: str, config: ExtractionConfig
) -> list[int]:
    """
    Determine which page indices to extract based on strategy.

    Args:
        num_pages: Total number of pages in document
        file_path: Path to the file (for adaptive strategy)
        config: Extraction configuration

    Returns:
        List of 0-indexed page numbers to extract
    """
    if config.strategy == "full":
        return list(range(num_pages))

    if config.strategy == "first_n_pages":
        n = min(config.max_pages or num_pages, num_pages)
        pages = list(range(n))
        if config.include_last_page and num_pages > n:
            pages.append(num_pages - 1)
        return pages

    if config.strategy == "char_limit":
        # For char_limit, extract first N pages (will be truncated later)
        return list(range(min(config.max_pages or 3, num_pages)))

    if config.strategy == "adaptive":
        return _adaptive_page_selection(num_pages, file_path, config)

    # Fallback to first N pages
    logger.warning(
        "Unknown extraction strategy: %s, falling back to first_n_pages",
        config.strategy,
    )
    return list(range(min(config.max_pages or 3, num_pages)))


def _adaptive_page_selection(
    num_pages: int, file_path: str, config: ExtractionConfig
) -> list[int]:
    """
    Adaptive page selection based on document characteristics.

    Strategy:
    - Small documents (<3 pages or <1MB): Extract all pages
    - Large compilations (>50 pages or >10MB): Sparse sampling (first 3, middle, last)
    - Standard documents (3-50 pages): First N + last page

    Args:
        num_pages: Total number of pages in document
        file_path: Path to the file (for file size check)
        config: Extraction configuration

    Returns:
        List of 0-indexed page numbers to extract
    """
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    # Small documents: extract everything
    if num_pages <= 3 or file_size_mb < 1.0:
        logger.debug(
            "Small document detected (%d pages, %.2fMB), extracting all pages",
            num_pages,
            file_size_mb,
        )
        return list(range(num_pages))

    # Large compilations (likely multi-document PDFs)
    if num_pages > 50 or file_size_mb > 10:
        logger.debug(
            "Large compilation detected (%d pages, %.2fMB), using sparse sampling",
            num_pages,
            file_size_mb,
        )
        # First 3 + middle + last
        pages = [0, 1, 2, num_pages // 2, num_pages - 1]
        return [p for p in pages if p < num_pages]

    # Standard multi-page documents: first N + last
    logger.debug(
        "Standard document detected (%d pages, %.2fMB), using first + last strategy",
        num_pages,
        file_size_mb,
    )
    pages = list(range(min(config.max_pages or 3, num_pages)))
    if config.include_last_page and num_pages > (config.max_pages or 3):
        pages.append(num_pages - 1)

    return pages


def extract_text_from_pdf(
    file_path: str, extraction_config: Optional[ExtractionConfig] = None
) -> Optional[str]:
    """
    Extract text content from a PDF file with configurable sampling.

    Args:
        file_path: Path to PDF file
        extraction_config: Extraction strategy configuration.
            If None, uses full extraction (backward compatible).

    Returns:
        Extracted text or None on failure
    """
    start_time = time.perf_counter()

    # Backward compatibility: None config = extract everything
    if extraction_config is None:
        extraction_config = ExtractionConfig(strategy="full")

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

            # Determine which pages to extract based on strategy
            pages_to_extract = _get_pages_to_extract(
                num_pages, file_path, extraction_config
            )

            logger.info(
                "Extracting %d of %d pages (%.1f%%, strategy: %s)",
                len(pages_to_extract),
                num_pages,
                (len(pages_to_extract) / num_pages * 100) if num_pages > 0 else 0,
                extraction_config.strategy,
            )

            # Extract selected pages
            content: str = "\n".join(
                [
                    reader.pages[i].extract_text()
                    for i in pages_to_extract
                    if reader.pages[i].extract_text()
                ]
            )

            # Apply character limit if configured
            if (
                extraction_config.max_chars
                and len(content) > extraction_config.max_chars
            ):
                logger.info(
                    "Truncating content from %d to %d characters",
                    len(content),
                    extraction_config.max_chars,
                )
                content = content[: extraction_config.max_chars]

        elapsed = time.perf_counter() - start_time
        estimated_tokens = len(content) // 4  # Rough token estimate

        logger.info(
            "Extracted %d characters from %d pages "
            "(%.2fs, ~%d tokens, %.1f%% of document)",
            len(content),
            len(pages_to_extract),
            elapsed,
            estimated_tokens,
            (len(pages_to_extract) / num_pages * 100) if num_pages > 0 else 0,
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


def extract_text_from_txt(
    file_path: str, extraction_config: Optional[ExtractionConfig] = None
) -> Optional[str]:
    """
    Extract text content from a TXT file with optional truncation.

    Args:
        file_path: Path to text file
        extraction_config: Optional extraction configuration.
            If None, uses full extraction (backward compatible).

    Returns:
        Extracted text or None on failure
    """
    # Backward compatibility: None config = extract everything
    if extraction_config is None:
        extraction_config = ExtractionConfig(strategy="full")

    try:
        file_size = os.path.getsize(file_path)
        file_size_kb = file_size / 1024

        logger.debug("Extracting text from TXT: %s (%.2fKB)", file_path, file_size_kb)

        with open(file_path, "r", encoding="utf-8") as file:
            if extraction_config.strategy == "full":
                content = file.read()
            else:
                # Apply character limit for TXT files
                max_chars = extraction_config.max_chars or 10_000
                content = file.read(max_chars)

                # Check if there's more content (file was truncated)
                if file.read(1):
                    logger.info(
                        "Truncated TXT file at %d characters (strategy: %s)",
                        max_chars,
                        extraction_config.strategy,
                    )

        estimated_tokens = len(content) // 4  # Rough token estimate
        logger.info(
            "Extracted %d characters from TXT file (~%d tokens)",
            len(content),
            estimated_tokens,
        )
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
