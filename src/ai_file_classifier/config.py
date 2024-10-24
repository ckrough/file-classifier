import os
import sys
from typing import Any

DB_FILE: str = "file_cache.db"


def delete_cache() -> None:
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Deleted cache file: {DB_FILE}")


# Handle termination signals to clean up
def handle_signal(signum: int, frame: Any) -> None:
    delete_cache()
    sys.exit(0)
