import atexit
import logging
import os
import signal
import sys
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from src.config.cache_config import delete_cache
from src.ai_file_classifier.file_inventory import initialize_cache
from src.ai_file_classifier.utils import (get_all_suggested_changes,
                                          get_user_arguments,
                                          is_supported_filetype, process_file,
                                          rename_files)
from src.config.logging_config import setup_logging

# Load environment variables
load_dotenv()
AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o-mini")
DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"


setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Application started")

    # Register delete_cache to be called upon exit
    atexit.register(delete_cache)

    # Handle termination signals to clean up
    def handle_signal(signum: int, frame: Any) -> None:
        delete_cache()
        sys.exit(0)

    # Register signal handlers for SIGINT (Ctrl+C) and SIGTERM
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    client: OpenAI = OpenAI()
    try:
        args = get_user_arguments()
        initialize_cache()
        if args.path:
            if os.path.isfile(args.path):
                # Process single file
                process_file(args.path, AI_MODEL, client)
            elif os.path.isdir(args.path):
                # Process directory
                for root, _, files in os.walk(args.path):
                    for file in files:
                        file_path: str = os.path.join(root, file)
                        if is_supported_filetype(file_path):
                            process_file(file_path, AI_MODEL, client)
            else:
                logger.error(
                    "The provided path is neither a file nor a directory.")
                return

            # User verification and approval step
            suggested_changes = get_all_suggested_changes()
            if suggested_changes:
                for change in suggested_changes:
                    print(
                        f"Current Name: {change['file_path']}\n"
                        f"Suggested Name: {change['suggested_name']}\n"
                    )
                user_confirmation = input(
                    "Approve rename? (yes/no): "
                ).strip().lower()
                if user_confirmation == 'yes':
                    rename_files(suggested_changes)
                    print("Files have been renamed.")
                else:
                    print("Renaming was canceled by the user.")
            else:
                print("No changes were suggested.")
        else:
            logger.error("Please provide a valid path to a file or directory.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        delete_cache()


if __name__ == "__main__":
    main()
