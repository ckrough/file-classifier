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


def _configure_taxonomy_and_naming(args: object, logger: logging.Logger) -> None:
    """Apply taxonomy and naming-style overrides from CLI arguments."""
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
        logger.info(
            "Using taxonomy from settings: %s (v%s)",
            taxonomy.name,
            taxonomy.version,
        )

    if getattr(args, "naming_style", None):
        app_settings.NAMING_STYLE = args.naming_style
        logger.info("Using naming style from CLI: %s", args.naming_style)
    else:
        logger.info(
            "Using naming style from settings: %s", app_settings.NAMING_STYLE
        )


def _create_ai_client_from_args(args: object) -> AIClient:
    """Create the AI client using CLI overrides when provided."""
    return create_ai_client(
        provider=getattr(args, "ai_provider", None),
        model=getattr(args, "ai_model", None),
    )


def _create_extraction_config_from_args(
    args: object, logger: logging.Logger
) -> ExtractionConfig:
    """Build ExtractionConfig from CLI arguments or environment variables."""
    if getattr(args, "extraction_strategy", None):
        extraction_config = ExtractionConfig(
            strategy=args.extraction_strategy  # type: ignore[attr-defined]
        )
        logger.info(
            "Using extraction strategy from CLI: %s", args.extraction_strategy
        )
        return extraction_config

    extraction_config = ExtractionConfig.from_env()
    logger.debug(
        "Using extraction strategy from environment: %s",
        extraction_config.strategy,
    )
    return extraction_config


def _run_processing(
    args: object,
    client: AIClient,
    extraction_config: ExtractionConfig,
    logger: logging.Logger,
):
    """Run the core processing for either batch or single-path mode."""
    if getattr(args, "batch", False):
        logger.info("Batch mode: reading file paths from stdin")
        return process_stdin_batch(client, extraction_config)

    path = getattr(args, "path", None)
    if path:
        return process_path(path, client, extraction_config)

    logger.error(
        "No path provided\n"
        "  \u2192 Use: python main.py <path> [options]\n"
        "  \u2192 Or use --batch to read from stdin\n"
        "  \u2192 Run with --help for usage",
    )
    raise ValueError("path argument is required unless using --batch mode")


def _handle_success(
    results: list[dict] | None,
    logger: logging.Logger,
    start_time: float,
) -> None:
    """Log summary and emit JSON results to stdout."""
    if not results:
        logger.warning("No results generated")
    else:
        logger.info("Generated %d path suggestion(s)", len(results))
        for result in results:
            print(json.dumps(result))

    elapsed = time.perf_counter() - start_time
    logger.info("Application completed successfully (%.2fs)", elapsed)


def _handle_error(
    exc: Exception,
    logger: logging.Logger,
    start_time: float,
) -> int:
    """Log structured error messages and return an appropriate exit code."""
    elapsed = time.perf_counter() - start_time

    if isinstance(exc, FileNotFoundError):
        logger.error(
            "File or directory not found: %s\n"
            "  \u2192 Check that the path exists\n"
            "  \u2192 Verify spelling and permissions",
            exc,
            exc_info=True,
        )
        return 1

    if isinstance(exc, PermissionError):
        logger.error(
            "Permission denied: %s\n"
            "  \u2192 Check file/directory permissions\n"
            "  \u2192 Try running with appropriate access rights",
            exc,
            exc_info=True,
        )
        return 1

    if isinstance(exc, ValueError):
        logger.error(
            "Invalid value or configuration: %s\n"
            "  \u2192 Check command-line arguments\n"
            "  \u2192 Verify .env file configuration\n"
            "  \u2192 See --help for valid options",
            exc,
            exc_info=True,
        )
        return 1

    if isinstance(exc, (OSError, RuntimeError)):
        logger.error(
            "Application error after %.2fs: %s\n"
            "  \u2192 Check logs for details\n"
            "  \u2192 See error message above for guidance",
            elapsed,
            exc,
            exc_info=True,
        )
        return 1

    logger.error("Unexpected error after %.2fs: %s", elapsed, exc, exc_info=True)
    return 1


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

    # Apply taxonomy and naming overrides
    _configure_taxonomy_and_naming(args, logger)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    try:
        client = _create_ai_client_from_args(args)
        extraction_config = _create_extraction_config_from_args(args, logger)
        results = _run_processing(args, client, extraction_config, logger)
        _handle_success(results, logger, start_time)
    except KeyboardInterrupt:
        elapsed = time.perf_counter() - start_time
        logger.info("Application interrupted by user (ran for %.2fs)", elapsed)
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as exc:  # noqa: BLE001
        exit_code = _handle_error(exc, logger, start_time)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
