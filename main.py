"""
Main module for the AI File Classifier application.

This module contains the main entry point for the Unix-style classification tool.
It processes files and outputs JSON metadata to stdout,
following Unix philosophy for composability with standard tools.
All logs are sent to stderr to keep stdout clean for piping.
"""

import json
import logging
import signal
import sys
import time

from dotenv import load_dotenv

from src.config.logging import setup_logging
from src.ai.factory import create_ai_client
from src.ai.client import AIClient
from src.cli.arguments import parse_arguments
from src.cli.workflow import process_path, process_stdin_batch
from src.files.extractors import ExtractionConfig

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

    # Apply taxonomy override from CLI if provided
    from src.config import settings as app_settings
    from src.taxonomy import set_taxonomy, get_active_taxonomy
    from src.ai.prompts import clear_prompt_cache

    if getattr(args, "taxonomy", None):
        set_taxonomy(args.taxonomy)
        clear_prompt_cache()  # Ensure prompts reload with new taxonomy
        logger.info("Using taxonomy from CLI: %s", args.taxonomy)
    else:
        # Load default taxonomy from settings
        taxonomy = get_active_taxonomy()
        logger.info("Using taxonomy from settings: %s (v%s)", taxonomy.name, taxonomy.version)

    # Apply naming style override from CLI if provided
    if getattr(args, "naming_style", None):
        app_settings.NAMING_STYLE = args.naming_style
        logger.info("Using naming style from CLI: %s", args.naming_style)
    else:
        logger.info("Using naming style from settings: %s", app_settings.NAMING_STYLE)

    logger.info("AI File Classifier started (verbosity: %s)", args.verbosity)
    logger.debug("Arguments: %s", vars(args))

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    try:
        # Initialize the AI client using factory function
        # CLI arguments (if provided) override environment-based AI configuration
        client: AIClient = create_ai_client(
            provider=getattr(args, "ai_provider", None),
            model=getattr(args, "ai_model", None),
        )

        # Create extraction config from CLI args (if provided) or env vars
        extraction_config = None
        if hasattr(args, "extraction_strategy") and args.extraction_strategy:
            extraction_config = ExtractionConfig(
                strategy=args.extraction_strategy  # type: ignore
            )
            logger.info(
                "Using extraction strategy from CLI: %s", args.extraction_strategy
            )
        else:
            # Will use default from environment variables
            extraction_config = ExtractionConfig.from_env()
            logger.debug(
                "Using extraction strategy from environment: %s",
                extraction_config.strategy,
            )

        # Process files based on mode (batch vs path)
        if args.batch:
            logger.info("Batch mode: reading file paths from stdin")
            results = process_stdin_batch(client, extraction_config)
        elif args.path:
            results = process_path(args.path, client, extraction_config)
        else:
            logger.error(
                "No path provided\n"
                "  → Use: python main.py <path> [options]\n"
                "  → Or use --batch to read from stdin\n"
                "  → Run with --help for usage"
            )
            sys.exit(2)  # Invalid arguments

        # Output results to stdout as JSON
        if not results:
            logger.warning("No results generated")
        else:
            logger.info("Generated %d path suggestion(s)", len(results))
            # Both single-file and batch mode: output JSON (one object per line)
            # This is JSON Lines format (newline-delimited JSON)
            for result in results:
                # Output JSON object with all metadata
                print(json.dumps(result))

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
