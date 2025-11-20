"""
File processing orchestration.

This module coordinates the processing of individual files,
combining file validation and content analysis.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Optional, TypedDict

from src.ai.client import AIClient
from src.analysis.analyzer import analyze_file_content
from src.files.operations import is_supported_filetype
from src.files.extractors import ExtractionConfig


@dataclass
class ProcessingOptions:
    """
    Configuration options for file processing.

    Groups optional parameters to reduce function signature complexity
    and improve code organization.

    Attributes:
        validate_type: Whether to validate file type. Set to False when
            caller has already validated to avoid redundant checks.
        file_index: Current file number (1-based) for progress display.
        total_files: Total number of files for progress display.
        extraction_config: Configuration for content extraction strategies.
    """

    validate_type: bool = True
    file_index: Optional[int] = None
    total_files: Optional[int] = None
    extraction_config: Optional[ExtractionConfig] = field(default=None)


class PathResult(TypedDict):
    """
    Result structure containing file classification metadata and suggested path.

    Attributes:
        original: Original file path
        suggested_path: Suggested destination path
        domain: Primary domain (Financial, Property, Insurance, Tax, Legal, Medical)
        category: Functional category within domain
        doctype: Document type (statement, receipt, invoice, etc.)
        vendor: Standardized vendor name
        date: Date in YYYYMMDD format
        subject: Brief subject/description
    """

    original: str
    suggested_path: str
    domain: str
    category: str
    doctype: str
    vendor: str
    date: str
    subject: str


__all__ = ["process_file", "PathResult", "ProcessingOptions"]

logger = logging.getLogger(__name__)


def process_file(
    file_path: str,
    client: AIClient,
    options: Optional[ProcessingOptions] = None,
) -> Optional[PathResult]:
    """
    Process a single file by analyzing its content and returning suggested path.

    This function coordinates file validation and AI-powered content analysis
    to generate an organized path structure.

    Args:
        file_path: Path to the file to process
        client: The AI client used for file analysis
        options: Optional processing configuration. If None, uses defaults.
            See ProcessingOptions for available settings.

    Returns:
        PathResult object containing original path, suggested destination path,
        and extracted metadata (domain, category, doctype, vendor, date, subject),
        or None if processing fails.

    Example:
        >>> client = create_ai_client()
        >>> result = process_file("invoice.pdf", client)
        >>> print(result["suggested_path"])
        financial/invoices/acme/invoice-acme-services-20240115.pdf

        >>> # With custom options
        >>> opts = ProcessingOptions(validate_type=False, file_index=1, total_files=10)
        >>> result = process_file("doc.pdf", client, opts)
    """
    # Use default options if none provided
    if options is None:
        options = ProcessingOptions()

    # Log progress if batch processing
    if options.file_index is not None and options.total_files is not None:
        logger.info(
            "Processing file %d/%d: %s",
            options.file_index,
            options.total_files,
            os.path.basename(file_path),
        )

    if not os.path.exists(file_path):
        logger.error(
            "File does not exist: %s\n"
            "  → Check that the path is correct\n"
            "  → Verify the file was not moved or deleted",
            file_path,
        )
        return None

    if not os.path.isfile(file_path):
        logger.error(
            "Path is not a file: %s\n"
            "  → Path may be a directory\n"
            "  → Check path type",
            file_path,
        )
        return None

    # Skip type validation if caller already validated (performance optimization)
    if options.validate_type and not is_supported_filetype(file_path):
        logger.error(
            "Unsupported file type: %s\n"
            "  → Only .pdf and .txt files are supported\n"
            "  → Convert to supported format or skip this file",
            file_path,
        )
        return None

    try:
        result = analyze_file_content(file_path, client, options.extraction_config)

        if result["suggested_name"]:
            # Build full path from destination_relative_path
            full_path = result["destination_relative_path"]
            logger.info("  → Suggested: %s", full_path)

            # Return path result with full metadata
            return PathResult(
                original=file_path,
                suggested_path=full_path,
                domain=result["domain"],
                category=result["category"],
                doctype=result["doctype"],
                vendor=result["vendor"],
                date=result["date"],
                subject=result["description"],
            )

        logger.error(
            "Could not determine suitable name for %s\n"
            "  → Document may not contain enough metadata\n"
            "  → Try improving document content quality",
            file_path,
        )
        return None

    except RuntimeError as e:
        logger.error("File processing failed: %s", str(e))
        raise
