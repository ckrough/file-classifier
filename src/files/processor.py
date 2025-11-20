"""
File processing orchestration.

This module coordinates the processing of individual files and directories,
combining file validation and content analysis.
"""

import logging
import os
from typing import Optional

from src.ai.client import AIClient
from src.analysis.analyzer import analyze_file_content
from src.files.operations import is_supported_filetype
from src.files.extractors import ExtractionConfig
from src.output.models import ClassificationResult, ClassificationMetadata

__all__ = ["process_file"]

logger = logging.getLogger(__name__)


def process_file(
    file_path: str,
    client: AIClient,
    validate_type: bool = True,
    file_index: Optional[int] = None,
    total_files: Optional[int] = None,
    extraction_config: Optional[ExtractionConfig] = None,
) -> Optional[ClassificationResult]:
    """
    Process a single file by analyzing its content and returning classification result.

    Args:
        file_path: Path to the file
        client: The AI client used for file analysis
        validate_type: Whether to validate file type. Set to False
            when caller has already validated to avoid redundant checks.
            Defaults to True for safety.
        file_index: Current file number (1-based) for progress display
        total_files: Total number of files for progress display
        extraction_config: Optional extraction configuration for performance tuning.
            If None, will be loaded from environment variables.

    Returns:
        ClassificationResult object containing original path, suggested path/name,
        and metadata, or None if processing fails.
    """
    # Log progress if batch processing
    if file_index is not None and total_files is not None:
        logger.info(
            "Processing file %d/%d: %s",
            file_index,
            total_files,
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
    if validate_type and not is_supported_filetype(file_path):
        logger.error(
            "Unsupported file type: %s\n"
            "  → Only .pdf and .txt files are supported\n"
            "  → Convert to supported format or skip this file",
            file_path,
        )
        return None

    try:
        result = analyze_file_content(file_path, client, extraction_config)

        if result["suggested_name"]:
            logger.info("  → Suggested: %s", result["suggested_name"])

            # Build full path from destination_relative_path
            full_path = result["destination_relative_path"]
            suggested_path = os.path.dirname(full_path) if full_path else ""

            # Extract domain from path (first component)
            path_parts = suggested_path.split(os.sep) if suggested_path else []
            domain = path_parts[0] if len(path_parts) > 0 else "uncategorized"

            # Create ClassificationResult
            return ClassificationResult(
                original=file_path,
                suggested_path=suggested_path,
                suggested_name=result["suggested_name"],
                full_path=full_path,
                metadata=ClassificationMetadata(
                    domain=domain,
                    category=result.get("category", ""),
                    vendor=result.get("vendor", ""),
                    date=result.get("date", ""),
                    doctype=result.get("doctype", ""),
                    subject=result.get("description", ""),
                ),
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
