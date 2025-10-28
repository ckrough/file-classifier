"""
Application workflow orchestration.

This module coordinates the main application workflow, processing
files or directories and handling user interactions.
"""

import logging
import os

from src.ai.client import AIClient
from src.files.processor import process_file, process_directory

__all__ = ["process_path"]

logger = logging.getLogger(__name__)


def process_path(path: str, client: AIClient) -> list[dict[str, str]]:
    """
    Process a single file or directory.

    Args:
        path (str): Path to a file or directory to process.
        client (AIClient): The AI client to use for analysis.

    Returns:
        list[dict[str, str]]: List of change dicts for processed
            files.
    """
    if os.path.isfile(path):
        logger.info("Processing single file: %s", path)
        change = process_file(path, client)
        return [change] if change else []

    if os.path.isdir(path):
        logger.info("Processing directory: %s", path)
        return process_directory(path, client)

    logger.error(
        "Invalid path: %s\n"
        "  → Path must be an existing file or directory\n"
        "  → Check that the path is spelled correctly\n"
        "  → Verify the file/directory exists",
        path,
    )
    return []
