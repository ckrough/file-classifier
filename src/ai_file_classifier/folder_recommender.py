import logging
import sqlite3

logger = logging.getLogger(__name__)


def recommend_folder_structure(directory):
    """
    Recommend a folder structure based on the file categories.
    """
    conn = sqlite3.connect('file_cache.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT category FROM files WHERE category IS NOT NULL")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()

    # Display recommended structure
    logger.info("Recommended Folder Structure:")
    for category in categories:
        logger.info("- %s", category)
