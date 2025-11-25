"""
Command-line argument parsing.

This module handles parsing and validation of command-line arguments
provided by the user.
"""

import argparse
import logging

from src.ai.client import AIProvider

__all__ = ["parse_arguments"]

logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments provided by the user.

    Returns:
        argparse.Namespace: The parsed command line arguments with:
            - path: File to analyze (optional with --batch)
            - batch: Read file paths from stdin
            - full_extraction: Force full content extraction (overrides env var)
            - extraction_strategy: Extraction strategy override (optional)
            - verbosity: One of 'quiet', 'normal', 'verbose', 'debug'
    """
    parser = argparse.ArgumentParser(
        description="AI-powered file classification tool - outputs JSON metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
output format (JSON Lines):
  Both modes output JSON with metadata fields:
    original, suggested_path, domain, category, doctype, vendor, date, subject

  Batch mode outputs one JSON object per line (newline-delimited JSON)

verbosity levels (logs go to stderr):
  (default)    Normal progress logging
  --quiet      Only errors to stderr
  --verbose    Detailed progress with timing
  --debug      Full technical logging

jq examples (jq required: brew install jq):
  # Extract just the suggested path
  %(prog)s document.pdf | jq -r .suggested_path

  # Move file to suggested path
  mv doc.pdf "$(%(prog)s document.pdf | jq -r .suggested_path)"

  # Batch process and generate move commands
  find . -name "*.pdf" | %(prog)s --batch | \\
    jq -r '"mkdir -p \\(.suggested_path | dirname) && " +
           "mv \\(.original) \\(.suggested_path)"' | bash

  # Filter by domain
  find . -type f | %(prog)s --batch | jq 'select(.domain == "financial")'

  # Extract vendor list
  find . -type f | %(prog)s --batch | jq -r .vendor | sort -u
        """,
    )

    # Positional arguments
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        help="Path to file to analyze (required unless --batch)",
    )

    # Input/output modes
    io_group = parser.add_argument_group("input/output")
    io_group.add_argument(
        "--batch",
        action="store_true",
        help="Batch mode: read file paths from stdin (one per line)",
    )

    # Naming style
    naming_group = parser.add_argument_group(
        "naming",
        description=(
            "Configure naming conventions. Overrides NAMING_STYLE env var for this run."
        ),
    )
    naming_group.add_argument(
        "--naming-style",
        type=str,
        choices=["compact_gpo", "descriptive_nara"],
        help=(
            "Select naming style: 'compact_gpo' (default) or 'descriptive_nara'. "
            "If omitted, uses NAMING_STYLE env var or defaults to compact_gpo."
        ),
    )

    # AI configuration
    ai_group = parser.add_argument_group(
        "AI configuration",
        description=(
            "Configure AI provider and model. Overrides AI_PROVIDER/AI_MODEL/OLLAMA_MODEL "
            "environment variables for this run."
        ),
    )
    ai_group.add_argument(
        "--ai-provider",
        type=str,
        choices=[p.value for p in AIProvider],
        help=(
            "Select AI provider (overrides AI_PROVIDER env var). "
            "Supported providers: "
            + ", ".join(sorted(p.value for p in AIProvider))
        ),
    )
    ai_group.add_argument(
        "--ai-model",
        type=str,
        help=(
            "Override AI model for the selected provider "
            "(overrides AI_MODEL or OLLAMA_MODEL env vars)."
        ),
    )

    # Performance tuning
    performance_group = parser.add_argument_group(
        "performance tuning",
        description="Control content extraction to optimize API costs and speed",
    )
    performance_group.add_argument(
        "--full-extraction",
        action="store_true",
        help=(
            "Extract full document content "
            "(highest accuracy, slower, more expensive). "
            "Overrides CLASSIFICATION_STRATEGY environment variable."
        ),
    )
    performance_group.add_argument(
        "--extraction-strategy",
        type=str,
        choices=["full", "first_n_pages", "char_limit", "adaptive"],
        help=(
            "Override extraction strategy "
            "(default: from CLASSIFICATION_STRATEGY env var or 'adaptive'). "
            "'adaptive' uses smart sampling based on document size."
        ),
    )

    # Verbosity control (mutually exclusive)
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const="quiet",
        dest="verbosity",
        help="Suppress all output except errors (sent to stderr)",
    )
    verbosity_group.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="verbose",
        dest="verbosity",
        help="Show detailed progress and timing for each operation",
    )
    verbosity_group.add_argument(
        "--debug",
        action="store_const",
        const="debug",
        dest="verbosity",
        help="Show full technical logging for troubleshooting",
    )

    # Set default verbosity if no flag specified
    parser.set_defaults(verbosity="normal")

    args = parser.parse_args()

    # Validation: --batch mode doesn't require path, but non-batch does
    if not args.batch and not args.path:
        parser.error("path argument is required unless using --batch mode")

    # Validation: can't specify both path and --batch
    if args.batch and args.path:
        parser.error("cannot specify path argument with --batch mode")

    # Handle --full-extraction flag (overrides --extraction-strategy)
    if args.full_extraction:
        if args.extraction_strategy and args.extraction_strategy != "full":
            logger.warning(
                "--full-extraction overrides --extraction-strategy=%s (using 'full')",
                args.extraction_strategy,
            )
        args.extraction_strategy = "full"

    logger.debug("Parsed arguments: %s", vars(args))

    return args
