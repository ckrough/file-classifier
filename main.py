"""
Main module for the AI File Classifier application.

This module contains the main entry point for the application, which processes
files or directories to suggest and apply file renaming based on AI analysis.
It handles command-line arguments, sets up logging, and manages the application
lifecycle including cleanup on exit.
"""

import atexit
import logging
import signal
import sys

from dotenv import load_dotenv

from src.config.logging import setup_logging
from src.storage.cache import initialize_cache, delete_cache
from src.ai.factory import create_ai_client
from src.ai.client import AIClient
from src.cli.arguments import parse_arguments
from src.cli.workflow import process_path
from src.cli.display import handle_suggested_changes

# Load environment variables
load_dotenv()

setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    """Execute the main application logic for AI File Classifier."""
    logger.info("Application started")

    atexit.register(delete_cache)
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    try:
        args = parse_arguments()
        initialize_cache()

        # Initialize the AI client using factory function
        # The factory will read AI_PROVIDER from .env to determine which provider to use
        client: AIClient = create_ai_client()

        if args.path:
            process_path(args.path, client)
            handle_suggested_changes(dry_run=args.dry_run, auto_rename=args.auto_rename)
        else:
            logger.error("Please provide a valid path to a file or directory.")

    except (FileNotFoundError, PermissionError, ValueError, OSError) as e:
        logger.error("An error occurred: %s", e, exc_info=True)
    finally:
        delete_cache()


if __name__ == "__main__":
    main()
