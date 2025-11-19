"""
Application workflow orchestration.

This module coordinates the main application workflow, processing
files or directories and handling user interactions.
"""

import logging
import os
from typing import Optional

from src.ai.client import AIClient
from src.files.processor import process_file, process_directory
from src.files.extractors import ExtractionConfig

__all__ = ["process_path"]

logger = logging.getLogger(__name__)


def process_path(
    path: str,
    client: AIClient,
    extraction_config: Optional[ExtractionConfig] = None,
) -> list[dict[str, str]]:
    """
    Process a single file or directory.

    Args:
        path: Path to a file or directory to process
        client: The AI client to use for analysis
        extraction_config: Optional extraction configuration for performance tuning.
            If None, will be loaded from environment variables.

    Returns:
        List of change dicts for processed files.
    """
    if os.path.isfile(path):
        logger.info("Processing single file: %s", path)
        change = process_file(path, client, extraction_config=extraction_config)
        return [change] if change else []

    if os.path.isdir(path):
        logger.info("Processing directory: %s", path)
        return process_directory(path, client, extraction_config)

    logger.error(
        "Invalid path: %s\n"
        "  → Path must be an existing file or directory\n"
        "  → Check that the path is spelled correctly\n"
        "  → Verify the file/directory exists",
        path,
    )
    return []
