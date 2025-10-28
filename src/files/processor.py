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

__all__ = ["process_file", "process_directory"]

logger = logging.getLogger(__name__)


def process_file(
    file_path: str, client: AIClient, validate_type: bool = True
) -> Optional[dict[str, str]]:
    """
    Process a single file by analyzing its content and returning the change.

    Args:
        file_path (str): Path to the file.
        client (AIClient): The AI client used for file analysis.
        validate_type (bool): Whether to validate file type. Set to False
            when caller has already validated to avoid redundant checks.
            Defaults to True for safety.

    Returns:
        Optional[dict[str, str]]: Dictionary containing file_path, suggested_name,
            and metadata (category, vendor, description, date), or None if
            processing fails.
    """
    if not os.path.exists(file_path):
        logger.error("The file '%s' does not exist.", file_path)
        return None

    if not os.path.isfile(file_path):
        logger.error("The path '%s' is not a file.", file_path)
        return None

    # Skip type validation if caller already validated (performance optimization)
    if validate_type and not is_supported_filetype(file_path):
        logger.error("The file '%s' is not a supported file type.", file_path)
        return None

    try:
        (
            suggested_name,
            category,
            vendor,
            description,
            date,
            destination_relative_path,
        ) = analyze_file_content(file_path, client)
        if suggested_name:
            logger.info("Suggested name for the file: %s", suggested_name)
            return {
                "file_path": file_path,
                "suggested_name": suggested_name,
                "category": category or "",
                "vendor": vendor or "",
                "description": description or "",
                "date": date or "",
                "destination_relative_path": destination_relative_path or "",
            }
        logger.error("Could not determine a suitable name for the file.")
        return None
    except RuntimeError as e:
        logger.error(str(e))
        raise


def process_directory(directory: str, client: AIClient) -> list[dict[str, str]]:
    """
    Process all supported files in a directory.

    Filters files by type before processing to avoid redundant validation,
    improving performance for batch operations.

    Args:
        directory (str): Path to the directory.
        client (AIClient): The AI client used for file analysis.

    Returns:
        list[dict[str, str]]: List of change dictionaries for successfully
            processed files.
    """
    changes: list[dict[str, str]] = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path: str = os.path.join(root, file)
            if is_supported_filetype(file_path):
                # Skip validation in process_file since we already validated
                change = process_file(file_path, client, validate_type=False)
                if change:
                    changes.append(change)
    return changes
