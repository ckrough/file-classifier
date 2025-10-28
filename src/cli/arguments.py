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
            - path: File or directory to analyze
            - destination: Archive root directory (optional)
            - move: Enable file moving (requires --destination)
            - dry_run: Preview mode (no actual changes)
            - verbosity: One of 'quiet', 'normal', 'verbose', 'debug'

    Raises:
        SystemExit: If --move is specified without --destination.
    """
    parser = argparse.ArgumentParser(
        description="AI-powered file classifier and archival tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
verbosity levels:
  (default)    Normal output with progress indicators
  --quiet      Only errors to stderr, no progress output
  --verbose    Detailed progress with timing for each operation
  --debug      Full technical logging for troubleshooting

examples:
  %(prog)s document.pdf                    # Analyze single file
  %(prog)s documents/ --verbose            # Analyze directory with details
  %(prog)s docs/ --move --destination=~/archive/  # Move files to archive
  %(prog)s docs/ --dry-run                 # Preview without changes
        """,
    )

    # Required arguments
    parser.add_argument(
        "path", type=str, help="Path to the file or directory to be analyzed"
    )

    # File operation modes
    operation_group = parser.add_argument_group("file operations")
    operation_group.add_argument(
        "--destination",
        type=str,
        help="Root directory for archive structure (files will be moved to "
        "Domain/Category/Vendor/ subdirectories under this root)",
    )
    operation_group.add_argument(
        "--move",
        action="store_true",
        help="Enable file moving to destination archive structure "
        "(requires --destination)",
    )
    operation_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing (works for both rename and move)",
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

    # Validate that --move requires --destination
    if args.move and not args.destination:
        parser.error("--move requires --destination to be specified")

    logger.debug("Parsed arguments: %s", vars(args))

    return args
