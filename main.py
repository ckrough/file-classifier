"""
Main module for the AI File Classifier application.

This module contains the main entry point for the application, which processes
files or directories to suggest and apply file renaming based on AI analysis.
It handles command-line arguments, sets up logging, and manages the application
lifecycle including cleanup on exit.
"""

import atexit
import logging
import os
import signal
import sys

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


def process_path(path: str, ai_model: str, client: OpenAI) -> None:
    """Process a single file or directory."""
    if os.path.isfile(path):
        process_file(path, ai_model, client)
    elif os.path.isdir(path):
        process_directory(path, ai_model, client)
    else:
        logger.error("The provided path is neither a file nor a directory.")


def process_directory(directory: str, ai_model: str, client: OpenAI) -> None:
    """Process all supported files in a directory."""
    for root, _, files in os.walk(directory):
        for file in files:
            file_path: str = os.path.join(root, file)
            if is_supported_filetype(file_path):
                process_file(file_path, ai_model, client)


def handle_suggested_changes() -> None:
    """Handle user verification and approval of suggested changes."""
    suggested_changes = get_all_suggested_changes()
    if not suggested_changes:
        print("No changes were suggested.")
        return

    for change in suggested_changes:
        print(f"Current Name: {change['file_path']}")
        print(f"Suggested Name: {change['suggested_name']}\n")

    user_confirmation = input("Approve rename? (yes/no): ").strip().lower()
    if user_confirmation == 'yes':
        rename_files(suggested_changes)
        print("Files have been renamed.")
    else:
        print("Renaming was canceled by the user.")


def main() -> None:
    """Execute the main application logic for AI File Classifier."""
    logger.info("Application started")

    atexit.register(delete_cache)
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    client: OpenAI = OpenAI()
    try:
        args = get_user_arguments()
        initialize_cache()

        if args.path:
            process_path(args.path, AI_MODEL, client)
            handle_suggested_changes()
        else:
            logger.error("Please provide a valid path to a file or directory.")

    except (FileNotFoundError, PermissionError, ValueError, OSError) as e:
        logger.error("An error occurred: %s", e, exc_info=True)
    finally:
        delete_cache()


if __name__ == "__main__":
    main()
