"""
Command-line argument parsing.

This module handles parsing and validation of command-line arguments
provided by the user.
"""

import argparse
import logging

__all__ = ["parse_arguments"]

logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments provided by the user.

    Returns:
        argparse.Namespace: The parsed command line arguments with:
            - path: File or directory to analyze (optional with --batch)
            - batch: Read file paths from stdin
            - format: Output format (json, csv, tsv)
            - full_extraction: Force full content extraction (overrides env var)
            - extraction_strategy: Extraction strategy override (optional)
            - verbosity: One of 'quiet', 'normal', 'verbose', 'debug'
    """
    parser = argparse.ArgumentParser(
        description="AI-powered file classification tool - Unix-style with JSON output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
output formats:
  json (default)  Newline-delimited JSON (one object per line)
  csv             Comma-separated values with header
  tsv             Tab-separated values with header

verbosity levels (logs go to stderr):
  (default)    Normal progress logging
  --quiet      Only errors to stderr
  --verbose    Detailed progress with timing
  --debug      Full technical logging

unix-style examples:
  %(prog)s document.pdf                          # Single file, JSON output
  %(prog)s document.pdf | jq -r '.suggested_name'  # Extract field with jq

  find . -name "*.pdf" | %(prog)s --batch        # Batch mode from stdin
  find . -type f | %(prog)s --batch --format=csv # CSV output

  # Generate move script
  find . -name "*.pdf" | %(prog)s --batch | \\
    jq -r '"mv \\"\\(.original)\\" \\"\\(.full_path)\\""' > moves.sh

  # Filter by domain
  find . -type f | %(prog)s --batch | \\
    jq -r 'select(.metadata.domain == "financial")'
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
    io_group.add_argument(
        "--format",
        type=str,
        choices=["json", "csv", "tsv"],
        default="json",
        help="Output format (default: json)",
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
