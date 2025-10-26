"""
Filename generation from analysis metadata.

This module provides functions to generate standardized filenames
based on analyzed file metadata.
"""

import logging

from src.analysis.models import Analysis

__all__ = ["generate_filename"]

logger = logging.getLogger(__name__)


def generate_filename(analysis: Analysis) -> str:
    """
    Generate a standardized filename based on the analysis data.

    Args:
        analysis (Analysis): The analyzed metadata of the file.

    Returns:
        str: A standardized filename in the format:
             {vendor}-{category}-{description}-{date} (if date present)
             {vendor}-{category}-{description} (if no date)
    """
    category: str = analysis.category
    vendor: str = analysis.vendor
    description: str = analysis.description
    date: str = analysis.date if analysis.date else ""

    filename: str = f"{vendor}-{category}-{description}"
    if date:
        filename += f"-{date}"

    logger.debug("Generated filename: %s", filename)
    return filename
