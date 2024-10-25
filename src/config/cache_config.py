import logging
import os
import sys
from typing import Any

logger = logging.getLogger(__name__)

DB_FILE: str = "file_cache.db"


def delete_cache() -> None:
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        logger.debug(f"Deleted cache file: {DB_FILE}")


# Handle termination signals to clean up
def handle_signal(signum: int, frame: Any) -> None:
    delete_cache()
    sys.exit(0)
