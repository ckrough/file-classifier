# pylint: disable=R0801

"""
File operations for file type validation.

This module provides functions for validating supported file types
using MIME type detection.
"""

import logging

import magic

from src.config.settings import SUPPORTED_MIMETYPES

__all__ = ["is_supported_filetype"]

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
