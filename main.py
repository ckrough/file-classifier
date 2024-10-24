import atexit
import logging
import os
import signal
import sys

from dotenv import load_dotenv
from openai import OpenAI

from src.ai_file_classifier.config import delete_cache
from src.ai_file_classifier.file_inventory import (initialize_cache,
                                                   inventory_files)
from src.ai_file_classifier.logging_config import setup_logging
from src.ai_file_classifier.utils import (rename_files,
                                          get_all_suggested_changes,
                                          get_user_arguments,
                                          is_supported_filetype, process_file)

# Load environment variables
load_dotenv()
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"


def main():
    setup_logging()

    # Register delete_cache to be called upon exit
    atexit.register(delete_cache)

    # Handle termination signals to clean up
    def handle_signal(signum, frame):
        delete_cache()
        sys.exit(0)

    # Register signal handlers for SIGINT (Ctrl+C) and SIGTERM
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    logger = logging.getLogger('file-classifier')
    client = OpenAI()
    try:
        args = get_user_arguments()
        initialize_cache()
        if args.path:
            if os.path.isfile(args.path):
                # Process single file
                process_file(args.path, AI_MODEL, client, logger)
                suggested_changes = get_all_suggested_changes()
                for change in suggested_changes:
                    if change['file_path'] == args.path:
                        logger.info(
                            f"Current Name: {change['file_path']}, "
                            f"Suggested Name: {change['suggested_name']}"
                        )
                        user_confirmation = input("Approve rename? (yes/no):"
                                                  ).strip().lower()
                        if user_confirmation == 'yes':
                            rename_files([change])
                        else:
                            logger.info("Renaming was canceled by the user.")
            elif os.path.isdir(args.path):
                # Inventory Files
                directory = args.path

                # Analyze Files
                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if is_supported_filetype(file_path):
                            process_file(file_path, AI_MODEL, client, logger)

                # Present Suggested Changes to User
                suggested_changes = get_all_suggested_changes()
                for change in suggested_changes:
                    logger.info(
                        f"Current Name: {change['file_path']}, "
                        f"Suggested Name: {change['suggested_name']}"
                    )
                user_confirmation = input("Approve rename? (yes/no):"
                                          ).strip().lower()
                if user_confirmation == 'yes':
                    rename_files(suggested_changes)
                    delete_cache()
                else:
                    logger.info("Bulk renaming was canceled by the user.")
            else:
                logger.error(
                    "The provided path is neither a file nor a directory.")
        else:
            logger.error("Please provide a valid path to a file or directory.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        delete_cache()


if __name__ == "__main__":
    main()
