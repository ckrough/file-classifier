"""
File processing orchestration.

This module coordinates the processing of individual files and directories,
combining file validation, content analysis, and database caching.
"""

import logging
import os

from src.ai.client import AIClient
from src.analysis.analyzer import analyze_file_content
from src.files.operations import is_supported_filetype
from src.storage.database import insert_or_update_file

__all__ = ["process_file", "process_directory"]

logger = logging.getLogger(__name__)


def process_file(file_path: str, client: AIClient) -> None:
    """
    Process a single file by analyzing its content and caching metadata.

    Args:
        file_path (str): Path to the file.
        client (AIClient): The AI client used for file analysis.

    Returns:
        None
    """
    if not os.path.exists(file_path):
        logger.error("The file '%s' does not exist.", file_path)
        return

    if not os.path.isfile(file_path):
        logger.error("The path '%s' is not a file.", file_path)
        return

    if not is_supported_filetype(file_path):
        logger.error("The file '%s' is not a supported file type.", file_path)
        return

    try:
        suggested_name, category, vendor, description, date = analyze_file_content(
            file_path, client
        )
        if suggested_name:
            logger.info("Suggested name for the file: %s", suggested_name)
            metadata = {
                "category": category,
                "description": description,
                "vendor": vendor,
                "date": date,
            }
            insert_or_update_file(file_path, suggested_name, metadata)
        else:
            logger.error("Could not determine a suitable name for the file.")
    except RuntimeError as e:
        logger.error(str(e))
        raise


def process_directory(directory: str, client: AIClient) -> None:
    """
    Process all supported files in a directory.

    Args:
        directory (str): Path to the directory.
        client (AIClient): The AI client used for file analysis.

    Returns:
        None
    """
    for root, _, files in os.walk(directory):
        for file in files:
            file_path: str = os.path.join(root, file)
            if is_supported_filetype(file_path):
                process_file(file_path, client)
