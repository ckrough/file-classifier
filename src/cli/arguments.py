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
    """
    parser = argparse.ArgumentParser(description="File Analyzer Application")
    parser.add_argument(
        "path", type=str, help="Path to the file or directory to be analyzed"
    )
    parser.add_argument(
        "--auto-rename", action="store_true", help="Always rename the file[s]"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute a dry run without renaming files",
    )
    return parser.parse_args()
