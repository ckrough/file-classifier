"""
File operations including validation and renaming.

This module provides functions for file system operations such as checking
file types and renaming files based on analysis results.
"""

import logging
import os
import shutil

import magic

from src.config.settings import SUPPORTED_MIMETYPES

__all__ = ["is_supported_filetype", "rename_files", "move_files"]

logger = logging.getLogger(__name__)

# Module-level singleton for MIME detection
# Initialized lazily on first use to avoid loading the MIME database at import time
_MIME_DETECTOR = None  # pylint: disable=invalid-name


def _get_mime_detector() -> magic.Magic:
    """
    Get or create the singleton Magic instance for MIME type detection.

    This ensures the MIME type database is loaded only once per application run,
    significantly improving performance when checking multiple files.

    Returns:
        magic.Magic: Cached Magic instance for MIME detection.
    """
    global _MIME_DETECTOR  # pylint: disable=global-statement
    if _MIME_DETECTOR is None:
        _MIME_DETECTOR = magic.Magic(mime=True)
        logger.debug("Initialized singleton MIME detector")
    return _MIME_DETECTOR


def is_supported_filetype(file_path: str) -> bool:
    """
    Validate if the specified file is a supported type.

    Uses a cached Magic instance to avoid repeatedly loading the MIME database,
    providing significant performance improvements for batch file processing.

    Args:
        file_path (str): Path to the file to be checked.

    Returns:
        bool: True if the file type is supported, False otherwise.
    """
    try:
        mime = _get_mime_detector()
        mimetype: str = mime.from_file(file_path)
        logger.debug("Detected MIME type for file '%s': %s", file_path, mimetype)
        return mimetype in SUPPORTED_MIMETYPES
    except ImportError:
        logger.error("Failed to import 'magic' module", exc_info=True)
        return False
    except (IOError, OSError) as e:
        logger.error("Error accessing file '%s': %s", file_path, str(e), exc_info=True)
        return False


def rename_files(suggested_changes: list[dict[str, str]]) -> None:
    """
    Rename files in bulk based on the approved suggested changes.
    File extensions are preserved from the original filename.

    Args:
        suggested_changes (list[dict[str, str]]): A list of dictionaries containing
            file paths and suggested names.

    Returns:
        None
    """
    for change in suggested_changes:
        file_path: str = change["file_path"]
        suggested_name: str = change["suggested_name"]
        try:
            # Extract extension from original file path
            _, ext = os.path.splitext(file_path)

            # Defensive check: ensure we have an extension for supported files
            if not ext:
                logger.warning(
                    "File '%s' has no extension. This may indicate an issue.", file_path
                )

            directory: str = os.path.dirname(file_path)
            new_path: str = os.path.join(directory, f"{suggested_name}{ext}")

            logger.debug(
                "Renaming '%s' to '%s' (extension: '%s')", file_path, new_path, ext
            )

            os.rename(file_path, new_path)
            logger.info("File '%s' renamed to '%s'.", file_path, new_path)
        except (OSError, IOError) as e:
            logger.error(
                "Error renaming file '%s' to '%s': %s",
                file_path,
                suggested_name,
                str(e),
                exc_info=True,
            )
            raise


def move_files(
    suggested_changes: list[dict[str, str]],
    destination_root: str,
    dry_run: bool = False,
) -> dict[str, list[str]]:
    """
    Move files to archive directory structure based on suggested changes.

    Creates the full directory taxonomy (Domain/Category/Vendor/) under the
    destination root. Skips files that already exist at the destination.

    Args:
        suggested_changes (list[dict[str, str]]): List of dictionaries containing
            file_path and destination_relative_path.
        destination_root (str): Root directory for the archive structure.
        dry_run (bool): If True, preview changes without executing. Defaults to False.

    Returns:
        dict[str, list[str]]: Dictionary with keys 'succeeded', 'skipped', 'failed'
            containing lists of file paths for each outcome.
    """
    results = {"succeeded": [], "skipped": [], "failed": []}

    for change in suggested_changes:
        file_path: str = change["file_path"]
        destination_relative_path: str = change.get("destination_relative_path", "")

        if not destination_relative_path:
            logger.error(
                "Missing destination_relative_path for file '%s'. Skipping.", file_path
            )
            results["failed"].append(file_path)
            continue

        try:
            # Construct full destination path
            destination_full_path = os.path.join(
                destination_root, destination_relative_path
            )

            # Check if file already exists at destination
            if os.path.exists(destination_full_path):
                logger.warning(
                    "File already exists at destination: '%s'. Skipping '%s'.",
                    destination_full_path,
                    file_path,
                )
                results["skipped"].append(file_path)
                continue

            if dry_run:
                logger.info(
                    "[DRY-RUN] Would move '%s' to '%s'",
                    file_path,
                    destination_full_path,
                )
                results["succeeded"].append(file_path)
                continue

            # Create directory structure if it doesn't exist
            destination_dir = os.path.dirname(destination_full_path)
            os.makedirs(destination_dir, exist_ok=True)
            logger.debug("Created directory structure: '%s'", destination_dir)

            # Move the file
            shutil.move(file_path, destination_full_path)
            logger.info("Moved '%s' to '%s'", file_path, destination_full_path)
            results["succeeded"].append(file_path)

        except (OSError, IOError, shutil.Error) as e:
            logger.error(
                "Error moving file '%s' to '%s': %s",
                file_path,
                destination_relative_path,
                str(e),
                exc_info=True,
            )
            results["failed"].append(file_path)

    return results
