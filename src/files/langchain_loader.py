"""LangChain-backed document loaders for text and PDF files.

This module uses LangChain's document loaders to turn file paths into
plain-text content strings plus basic loader metadata.

It is the canonical entry point for document loading in the classifier.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

from langchain_community.document_loaders import PyPDFLoader, TextLoader

from src.files.extractors import ExtractionConfig, _get_pages_to_extract

logger = logging.getLogger(__name__)


@dataclass
class LoaderMetadata:
    """Metadata about how a document was loaded.

    Attributes:
        file_type: Logical file type (e.g., "pdf", "txt").
        loader: Name of the LangChain loader class.
        page_count: Total number of pages (for paged formats), if known.
        pages_sampled: Indices of pages that were actually used.
        char_count: Number of characters in the returned content string.
    """

    file_type: str
    loader: str
    page_count: Optional[int]
    pages_sampled: list[int]
    char_count: int


def _build_metadata(
    *,
    file_type: str,
    loader_name: str,
    page_count: Optional[int],
    pages_sampled: list[int],
    content: str,
) -> LoaderMetadata:
    return LoaderMetadata(
        file_type=file_type,
        loader=loader_name,
        page_count=page_count,
        pages_sampled=pages_sampled,
        char_count=len(content),
    )


def load_pdf_text_with_langchain(
    file_path: str,
    extraction_config: ExtractionConfig,
) -> tuple[Optional[str], Optional[LoaderMetadata]]:
    """Load a PDF file using LangChain's PyPDFLoader.

    Returns a tuple of (content, metadata). On failure, returns (None, None)
    and logs an error.
    """

    try:
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        logger.debug(
            "[LC] Loading PDF via PyPDFLoader: %s (%.2fMB)", file_path, file_size_mb
        )

        loader = PyPDFLoader(file_path, mode="page")
        documents = loader.load()
        if not documents:
            logger.error("[LC] No documents returned by PyPDFLoader for %s", file_path)
            return None, None

        page_count = len(documents)
        pages_to_extract = _get_pages_to_extract(
            page_count, file_path, extraction_config
        )
        logger.info(
            "[LC] Extracting %d of %d pages (strategy=%s) for %s",
            len(pages_to_extract),
            page_count,
            extraction_config.strategy,
            file_path,
        )

        # Concat selected pages
        pieces: list[str] = []
        for i in pages_to_extract:
            if 0 <= i < page_count:
                text = documents[i].page_content or ""
                if text:
                    pieces.append(text)

        content = "\n".join(pieces)

        # Apply character limit if configured
        if extraction_config.max_chars and len(content) > extraction_config.max_chars:
            logger.info(
                "[LC] Truncating PDF content from %d to %d characters",
                len(content),
                extraction_config.max_chars,
            )
            content = content[: extraction_config.max_chars]

        metadata = _build_metadata(
            file_type="pdf",
            loader_name=type(loader).__name__,
            page_count=page_count,
            pages_sampled=pages_to_extract,
            content=content,
        )

        logger.info(
            "[LC] Loaded PDF via LangChain: %d chars from %d pages (sampled=%s)",
            metadata.char_count,
            metadata.page_count,
            metadata.pages_sampled,
        )
        return content, metadata

    except (OSError, ValueError) as e:
        logger.error(
            "[LC] Error loading PDF %s: %s\n"
            "  → Check file permissions and integrity\n"
            "  → Verify the file is a valid PDF",
            file_path,
            e,
            exc_info=True,
        )
        return None, None


def load_txt_text_with_langchain(
    file_path: str,
    extraction_config: ExtractionConfig,
) -> tuple[Optional[str], Optional[LoaderMetadata]]:
    """Load a text file using LangChain's TextLoader.

    Returns a tuple of (content, metadata). On failure, returns (None, None)
    and logs an error.
    """

    try:
        file_size = os.path.getsize(file_path)
        file_size_kb = file_size / 1024
        logger.debug(
            "[LC] Loading TXT via TextLoader: %s (%.2fKB)", file_path, file_size_kb
        )

        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()
        if not documents:
            logger.error("[LC] No documents returned by TextLoader for %s", file_path)
            return None, None

        # TextLoader typically returns a single Document; treat all as one stream
        raw_text = "\n".join(doc.page_content or "" for doc in documents)

        # Apply character limit
        if extraction_config.max_chars and len(raw_text) > extraction_config.max_chars:
            logger.info(
                "[LC] Truncating TXT content from %d to %d characters",
                len(raw_text),
                extraction_config.max_chars,
            )
            content = raw_text[: extraction_config.max_chars]
        else:
            content = raw_text

        metadata = _build_metadata(
            file_type="txt",
            loader_name=type(loader).__name__,
            page_count=None,
            pages_sampled=[],
            content=content,
        )

        logger.info(
            "[LC] Loaded TXT via LangChain: %d chars from %d underlying chunk(s)",
            metadata.char_count,
            len(documents),
        )
        return content, metadata

    except OSError as e:
        logger.error(
            "[LC] Error loading TXT %s: %s\n"
            "  → Check file permissions\n"
            "  → Verify file exists and is readable",
            file_path,
            e,
            exc_info=True,
        )
        return None, None
