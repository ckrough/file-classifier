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

__all__ = ["process_file", "process_directory"]

logger = logging.getLogger(__name__)


def process_file(
    file_path: str,
    client: AIClient,
    validate_type: bool = True,
    file_index: Optional[int] = None,
    total_files: Optional[int] = None,
    extraction_config: Optional[ExtractionConfig] = None,
) -> Optional[dict[str, str]]:
    """
    Process a single file by analyzing its content and returning the change.

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
        Dictionary containing file_path, suggested_name, and metadata
        (category, vendor, description, date), or None if processing fails.
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
            return {
                "file_path": file_path,
                "suggested_name": result["suggested_name"],
                "category": result["category"],
                "vendor": result["vendor"],
                "description": result["description"],
                "date": result["date"],
                "destination_relative_path": result["destination_relative_path"],
            }

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


def process_directory(
    directory: str,
    client: AIClient,
    extraction_config: Optional[ExtractionConfig] = None,
) -> list[dict[str, str]]:
    """
    Process all supported files in a directory.

    Filters files by type before processing to avoid redundant validation,
    improving performance for batch operations. Shows progress for each file.

    Args:
        directory: Path to the directory
        client: The AI client used for file analysis
        extraction_config: Optional extraction configuration for performance tuning.
            If None, will be loaded from environment variables.

    Returns:
        List of change dictionaries for successfully processed files.
    """
    # First, collect all supported files to show total count
    supported_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path: str = os.path.join(root, file)
            if is_supported_filetype(file_path):
                supported_files.append(file_path)

    total_files = len(supported_files)
    if total_files == 0:
        logger.warning(
            "No supported files found in directory: %s\n"
            "  → Only .pdf and .txt files are supported\n"
            "  → Check directory contains files",
            directory,
        )
        return []

    logger.info("Found %d supported file(s) in %s", total_files, directory)

    # Process each file with progress tracking
    changes: list[dict[str, str]] = []
    for index, file_path in enumerate(supported_files, start=1):
        # Skip validation in process_file since we already validated
        change = process_file(
            file_path,
            client,
            validate_type=False,
            file_index=index,
            total_files=total_files,
            extraction_config=extraction_config,
        )
        if change:
            changes.append(change)

    logger.info(
        "Batch processing complete: %d/%d files successfully processed",
        len(changes),
        total_files,
    )

    return changes
