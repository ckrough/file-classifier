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
        argparse.Namespace: The parsed command line arguments.

    Raises:
        SystemExit: If --move is specified without --destination.
    """
    parser = argparse.ArgumentParser(
        description="AI-powered file classifier and archival tool"
    )
    parser.add_argument(
        "path", type=str, help="Path to the file or directory to be analyzed"
    )
    parser.add_argument(
        "--destination",
        type=str,
        help="Root directory for archive structure (files will be moved to "
        "Domain/Category/Vendor/ subdirectories under this root)",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Enable file moving to destination archive structure "
        "(requires --destination)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing (works for both rename and move)",
    )

    args = parser.parse_args()

    # Validate that --move requires --destination
    if args.move and not args.destination:
        parser.error("--move requires --destination to be specified")

    return args
