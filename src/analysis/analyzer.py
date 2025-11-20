"""
File content analysis and metadata extraction.

This module coordinates the analysis workflow using the multi-agent pipeline
for document processing with a 4-agent system for intelligent file classification.
"""

import logging
import os
from typing import Optional, TypedDict

from src.ai.client import AIClient
from src.files.extractors import (
    extract_text_from_pdf,
    extract_text_from_txt,
    ExtractionConfig,
)
from src.agents.pipeline import process_document_multi_agent

__all__ = ["analyze_file_content", "AnalysisResult"]

logger = logging.getLogger(__name__)


class AnalysisResult(TypedDict):
    """
    Result of file content analysis.

    Attributes:
        suggested_name: Suggested basename for the file
        domain: Primary domain (Financial, Property, Insurance, Tax, Legal, Medical)
        category: Functional category within domain
        doctype: Document type (statement, receipt, invoice, etc.)
        vendor: Vendor or source name
        description: Brief description or subject
        date: Date in YYYYMMDD format
        destination_relative_path: Full path relative to archive root
    """

    suggested_name: str
    domain: str
    category: str
    doctype: str
    vendor: str
    description: str
    date: str
    destination_relative_path: str


def analyze_file_content(
    file_path: str,
    client: AIClient,
    extraction_config: Optional[ExtractionConfig] = None,
) -> AnalysisResult:
    """
    Analyze the content of a file using the multi-agent pipeline.

    Uses a 4-agent pipeline for intelligent document processing:
    1. Classification Agent: Semantic analysis and metadata extraction
    2. Standards Agent: Apply naming conventions and normalization
    3. Path Construction Agent: Build directory structure and filename
    4. Conflict Resolution Agent: Handle edge cases and ambiguities

    Args:
        file_path: The path to the file to analyze
        client: The AI client to use for analysis
        extraction_config: Optional extraction configuration for performance tuning.
            If None, loads from environment variables (default: adaptive strategy).

    Returns:
        AnalysisResult: Dictionary containing:
            - suggested_name: basename only (for backward compatibility)
            - category: file category (doctype)
            - vendor: vendor or source name
            - description: brief description or subject
            - date: date in YYYYMMDD format
            - destination_relative_path: full path relative to archive root
              (e.g., "Financial/Banking/chase/statement-chase-...")
    """
    try:
        # Load extraction config from environment if not provided
        if extraction_config is None:
            extraction_config = ExtractionConfig.from_env()
            logger.debug(
                "Using extraction strategy: %s (max_pages=%s, max_chars=%s)",
                extraction_config.strategy,
                extraction_config.max_pages,
                extraction_config.max_chars,
            )

        # Extract content based on file type
        if file_path.lower().endswith(".pdf"):
            content: Optional[str] = extract_text_from_pdf(file_path, extraction_config)
        else:
            content: Optional[str] = extract_text_from_txt(file_path, extraction_config)

        if content is None:
            raise ValueError(f"Failed to extract content from file: {file_path}")

        filename = os.path.basename(file_path)

        logger.info("Using multi-agent pipeline for analysis")
        raw_metadata, normalized, resolved = process_document_multi_agent(
            content, filename, client
        )

        # Extract filename from the final path
        # Path format: Domain/Category/Vendor/doctype-vendor-subject-YYYYMMDD.ext
        suggested_name = os.path.basename(resolved.final_path)
        destination_relative_path = resolved.final_path

        # Log alternative paths if present
        if resolved.alternative_paths:
            logger.info(
                "Alternative paths available: %s", ", ".join(resolved.alternative_paths)
            )
        if resolved.resolution_notes:
            logger.info("Resolution notes: %s", resolved.resolution_notes)

        # Get metadata directly from pipeline instead of parsing path
        logger.debug(
            "Multi-agent result: domain=%s, category=%s, doctype=%s, "
            "vendor=%s, date=%s, subject=%s, destination=%s",
            raw_metadata.domain,
            raw_metadata.category,
            raw_metadata.doctype,
            normalized.vendor_name,
            normalized.date,
            normalized.subject,
            destination_relative_path,
        )

        return AnalysisResult(
            suggested_name=suggested_name,
            domain=raw_metadata.domain,
            category=raw_metadata.category,
            doctype=raw_metadata.doctype,
            vendor=normalized.vendor_name,
            description=normalized.subject,
            date=normalized.date,
            destination_relative_path=destination_relative_path,
        )

    except ValueError as e:
        logger.error(
            "Content extraction failed for %s: %s\n"
            "  → Ensure file contains readable text\n"
            "  → Check file is not corrupted\n"
            "  → Verify file format is supported (.pdf or .txt)",
            file_path,
            e,
            exc_info=True,
        )
        raise RuntimeError(f"Failed to extract content from {file_path}") from e
    except FileNotFoundError as e:
        logger.error(
            "File not found: %s\n"
            "  → Check path is correct\n"
            "  → Verify file exists",
            file_path,
            exc_info=True,
        )
        raise RuntimeError(f"File not found: {file_path}") from e
