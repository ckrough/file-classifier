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


def process_path(path: str, client: AIClient) -> None:
    """
    Process a single file or directory.

    Args:
        path (str): Path to a file or directory to process.
        client (AIClient): The AI client to use for analysis.

    Returns:
        None
    """
    if os.path.isfile(path):
        process_file(path, client)
    elif os.path.isdir(path):
        process_directory(path, client)
    else:
        logger.error("The provided path is neither a file nor a directory.")
