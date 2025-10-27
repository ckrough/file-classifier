"""
File operations including validation and renaming.

This module provides functions for file system operations such as checking
file types and renaming files based on analysis results.
"""

import logging
import os

import magic

from src.config.settings import SUPPORTED_MIMETYPES

__all__ = ["is_supported_filetype", "rename_files"]

logger = logging.getLogger(__name__)

# Module-level singleton for MIME detection
# Initialized lazily on first use to avoid loading the MIME database at import time
_MIME_DETECTOR = None


def _get_mime_detector() -> magic.Magic:
    """
    Get or create the singleton Magic instance for MIME type detection.

    This ensures the MIME type database is loaded only once per application run,
    significantly improving performance when checking multiple files.

    Returns:
        magic.Magic: Cached Magic instance for MIME detection.
    """
    global _MIME_DETECTOR
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
