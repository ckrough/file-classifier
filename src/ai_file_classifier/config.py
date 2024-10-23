import os
import sys

DB_FILE = "file_cache.db"


def delete_cache():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Deleted cache file: {DB_FILE}")


# Handle termination signals to clean up
def handle_signal(signum, frame):
    delete_cache()
    sys.exit(0)
