"""
Folder structure recommendations based on file categories.

This module analyzes categorized files and suggests organizational
folder structures.
"""

import logging
import sqlite3

from src.config.settings import DB_FILE

__all__ = ["recommend_folder_structure"]

logger = logging.getLogger(__name__)


def recommend_folder_structure():
    """
    Recommend a folder structure based on the file categories.

    Analyzes all categorized files in the cache and suggests a folder
    structure organized by category.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM files WHERE category IS NOT NULL")
        categories = [row[0] for row in cursor.fetchall()]

    # Display recommended structure
    logger.info("Recommended Folder Structure:")
    for category in categories:
        logger.info("- %s", category)
