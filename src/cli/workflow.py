"""
Application workflow orchestration.

This module coordinates the main application workflow, processing
files from paths or stdin in batch mode, generating path suggestions.
"""

import logging
import os
import sys
from typing import Optional

from src.ai.client import AIClient
from src.files.processor import process_file, PathResult, ProcessingOptions
from src.files.extractors import ExtractionConfig

__all__ = ["process_path", "process_stdin_batch"]

logger = logging.getLogger(__name__)


def process_path(
    path: str,
    client: AIClient,
    extraction_config: Optional[ExtractionConfig] = None,
) -> list[PathResult]:
    """
    Process a single file.

    Args:
        path: Path to a file to process
        client: The AI client to use for analysis
        extraction_config: Optional extraction configuration for performance tuning.
            If None, will be loaded from environment variables.

    Returns:
        List containing the PathResult for the file, or empty list if failed.
    """
    if not os.path.exists(path):
        logger.error(
            "Path does not exist: %s\n"
            "  → Check that the path is spelled correctly\n"
            "  → Verify the file exists",
            path,
        )
        return []

    if not os.path.isfile(path):
        logger.error(
            "Path is not a file: %s\n"
            "  → This tool processes single files only\n"
            "  → For directories, use: find <dir> -type f | %s --batch",
            path,
            os.path.basename(sys.argv[0]) if sys.argv else "classifier",
        )
        return []

    logger.info("Processing file: %s", path)
    options = ProcessingOptions(extraction_config=extraction_config)
    result = process_file(path, client, options)
    return [result] if result else []


def process_stdin_batch(
    client: AIClient,
    extraction_config: Optional[ExtractionConfig] = None,
) -> list[PathResult]:
    """
    Process files from stdin in batch mode.

    Reads file paths from stdin (one per line), processes each file,
    and returns path results. Skips invalid or unsupported files.

    Args:
        client: The AI client to use for analysis
        extraction_config: Optional extraction configuration for performance tuning.
            If None, will be loaded from environment variables.

    Returns:
        List of PathResult objects for successfully processed files.
    """
    results: list[PathResult] = []

    logger.info("Batch mode: reading file paths from stdin")

    for line in sys.stdin:
        file_path = line.strip()

        if not file_path:
            continue  # Skip empty lines

        logger.debug("Processing: %s", file_path)

        try:
            options = ProcessingOptions(extraction_config=extraction_config)
            result = process_file(file_path, client, options)
            if result:
                results.append(result)
                logger.debug("Successfully classified: %s", file_path)
            else:
                logger.warning("Skipped (unsupported or failed): %s", file_path)
        except (RuntimeError, ValueError, OSError) as e:
            # Catch expected exceptions from file processing:
            # - RuntimeError: AI processing failures
            # - ValueError: Invalid content or configuration
            # - OSError: File system errors (FileNotFoundError, PermissionError, etc.)
            # Log error but continue processing other files in batch
            logger.error("Error processing '%s': %s", file_path, str(e))
            continue

    logger.info("Batch processing complete: %d files classified", len(results))
    return results
