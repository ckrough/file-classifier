"""
Folder structure recommendations based on file categories.

This module analyzes categorized files and suggests organizational
folder structures.
"""

import logging

__all__ = ["recommend_folder_structure"]

logger = logging.getLogger(__name__)


def recommend_folder_structure(changes: list[dict[str, str]]) -> list[str]:
    """
    Recommend a folder structure based on the file categories.

    Analyzes categorized files and suggests a folder structure organized by category.

    Args:
        changes (list[dict[str, str]]): List of change dictionaries containing
            file metadata including category information.

    Returns:
        list[str]: List of unique categories for folder organization.
    """
    # Extract unique categories from changes
    categories = sorted(
        {change.get("category") for change in changes if change.get("category")}
    )

    # Display recommended structure
    logger.info("Recommended Folder Structure:")
    for category in categories:
        logger.info("- %s", category)

    return categories
