"""
Main module for the AI File Classifier application.

This module contains the main entry point for the application, which processes
files or directories to suggest and apply file renaming based on AI analysis.
It handles command-line arguments and sets up logging.
"""

import logging
import signal
import sys

from dotenv import load_dotenv

from src.config.logging import setup_logging
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

    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    try:
        args = parse_arguments()

        # Initialize the AI client using factory function
        # The factory will read AI_PROVIDER from .env to determine which provider to use
        client: AIClient = create_ai_client()

        if args.path:
            changes = process_path(args.path, client)
            handle_suggested_changes(
                changes,
                dry_run=args.dry_run,
                destination_root=args.destination,
                move_enabled=args.move,
            )
        else:
            logger.error("Please provide a valid path to a file or directory.")

    except (FileNotFoundError, PermissionError, ValueError, OSError) as e:
        logger.error("An error occurred: %s", e, exc_info=True)


if __name__ == "__main__":
    main()
