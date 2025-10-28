"""
Main module for the AI File Classifier application.

This module contains the main entry point for the application, which processes
files or directories to suggest and apply file renaming based on AI analysis.
It handles command-line arguments and sets up logging.
"""

import logging
import signal
import sys
import time

from dotenv import load_dotenv

from src.config.logging import setup_logging
from src.ai.factory import create_ai_client
from src.ai.client import AIClient
from src.cli.arguments import parse_arguments
from src.cli.workflow import process_path
from src.cli.display import handle_suggested_changes

# Load environment variables
load_dotenv()


def main() -> None:
    """Execute the main application logic for AI File Classifier."""
    start_time = time.perf_counter()

    # Parse arguments first to get verbosity level
    args = parse_arguments()

    # Setup logging with verbosity from CLI args
    setup_logging(verbosity=args.verbosity)
    logger = logging.getLogger(__name__)

    logger.info("AI File Classifier started (verbosity: %s)", args.verbosity)
    logger.debug("Arguments: %s", vars(args))

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    try:
        # Initialize the AI client using factory function
        # The factory will read AI_PROVIDER from .env to determine which provider to use
        client: AIClient = create_ai_client()

        if args.path:
            changes = process_path(args.path, client)

            if not changes:
                logger.warning("No changes generated for path: %s", args.path)
            else:
                logger.info("Generated %d suggested change(s)", len(changes))

            handle_suggested_changes(
                changes,
                dry_run=args.dry_run,
                destination_root=args.destination,
                move_enabled=args.move,
            )
        else:
            logger.error(
                "No path provided\n"
                "  → Use: python main.py <path> [options]\n"
                "  → Run with --help for usage"
            )

        elapsed = time.perf_counter() - start_time
        logger.info("Application completed successfully (%.2fs)", elapsed)

    except FileNotFoundError as e:
        logger.error(
            "File or directory not found: %s\n"
            "  → Check that the path exists\n"
            "  → Verify spelling and permissions",
            e,
            exc_info=True,
        )
        sys.exit(1)
    except PermissionError as e:
        logger.error(
            "Permission denied: %s\n"
            "  → Check file/directory permissions\n"
            "  → Try running with appropriate access rights",
            e,
            exc_info=True,
        )
        sys.exit(1)
    except ValueError as e:
        logger.error(
            "Invalid value or configuration: %s\n"
            "  → Check command-line arguments\n"
            "  → Verify .env file configuration\n"
            "  → See --help for valid options",
            e,
            exc_info=True,
        )
        sys.exit(1)
    except (OSError, RuntimeError) as e:
        elapsed = time.perf_counter() - start_time
        logger.error(
            "Application error after %.2fs: %s\n"
            "  → Check logs for details\n"
            "  → See error message above for guidance",
            elapsed,
            e,
            exc_info=True,
        )
        sys.exit(1)
    except KeyboardInterrupt:
        elapsed = time.perf_counter() - start_time
        logger.info("Application interrupted by user (ran for %.2fs)", elapsed)
        sys.exit(130)  # Standard exit code for SIGINT


if __name__ == "__main__":
    main()
