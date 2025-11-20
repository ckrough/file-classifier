"""
Application workflow orchestration.

This module coordinates the main application workflow, processing
files from paths or stdin in batch mode, generating classification results.
"""

import logging
import os
import sys
from typing import Optional

from src.ai.client import AIClient
from src.files.processor import process_file
from src.files.extractors import ExtractionConfig
from src.output.models import ClassificationResult

__all__ = ["process_path", "process_stdin_batch"]

logger = logging.getLogger(__name__)


def process_path(
    path: str,
    client: AIClient,
    extraction_config: Optional[ExtractionConfig] = None,
) -> list[ClassificationResult]:
    """
    Process a single file.

    Args:
        path: Path to a file to process
        client: The AI client to use for analysis
        extraction_config: Optional extraction configuration for performance tuning.
            If None, will be loaded from environment variables.

    Returns:
        List containing the ClassificationResult for the file, or empty list if failed.
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
    result = process_file(path, client, extraction_config=extraction_config)
    return [result] if result else []


def process_stdin_batch(
    client: AIClient,
    extraction_config: Optional[ExtractionConfig] = None,
) -> list[ClassificationResult]:
    """
    Process files from stdin in batch mode.

    Reads file paths from stdin (one per line), processes each file,
    and returns classification results. Skips invalid or unsupported files.

    Args:
        client: The AI client to use for analysis
        extraction_config: Optional extraction configuration for performance tuning.
            If None, will be loaded from environment variables.

    Returns:
        List of ClassificationResult objects for successfully processed files.
    """
    results: list[ClassificationResult] = []

    logger.info("Batch mode: reading file paths from stdin")

    for line in sys.stdin:
        file_path = line.strip()

        if not file_path:
            continue  # Skip empty lines

        logger.debug("Processing: %s", file_path)

        try:
            result = process_file(
                file_path, client, extraction_config=extraction_config
            )
            if result:
                results.append(result)
                logger.debug("Successfully classified: %s", file_path)
            else:
                logger.warning("Skipped (unsupported or failed): %s", file_path)
        except Exception as e:
            # Log error but continue processing other files
            logger.error("Error processing '%s': %s", file_path, str(e))
            continue

    logger.info("Batch processing complete: %d files classified", len(results))
    return results
