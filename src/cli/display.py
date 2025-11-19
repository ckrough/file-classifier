"""
User display and interaction.

This module handles displaying suggested file changes to the user
and getting approval for renaming operations.
"""

import logging
import os

from src.files.operations import rename_files

__all__ = ["handle_suggested_changes"]

logger = logging.getLogger(__name__)


def handle_suggested_changes(
    changes: list[dict[str, str]],
    dry_run: bool,
) -> None:
    """
    Handle user verification and approval of suggested changes.

    Renames files in-place based on AI classification.

    Args:
        changes (list[dict[str, str]]): List of change dictionaries containing
            file_path and suggested_name.
        dry_run (bool): If True, display changes but don't apply them.

    Returns:
        None
    """
    if not changes:
        logger.info("No changes were suggested.")
        return

    # Display changes
    _display_rename_mode(changes)

    if dry_run:
        logger.info("Dry-run mode enabled. No changes will be made.")
        return

    # Get user approval
    if not _get_user_approval():
        logger.info("Operation canceled by user.")
        return

    # Execute rename operation
    _execute_rename_operation(changes)


def _display_rename_mode(changes: list[dict[str, str]]) -> None:
    """Display suggested changes."""
    logger.info("Files will be renamed in current directory\n")
    logger.info("Displaying %d suggested renames:", len(changes))
    for change in changes:
        current_basename = os.path.basename(change["file_path"])
        suggested_name = change["suggested_name"]
        # Note: suggested_name already includes extension from multi-agent pipeline
        logger.info("  %s → %s\n", current_basename, suggested_name)


def _get_user_approval() -> bool:
    """
    Get user approval for applying changes.

    Returns:
        bool: True if user approves, False otherwise.
    """
    user_confirmation = input("Approve changes? (yes/no): ").strip().lower()
    logger.info("User response to approval prompt: '%s'", user_confirmation)
    return user_confirmation == "yes"


def _execute_rename_operation(changes: list[dict[str, str]]) -> None:
    """Execute rename operation for all changes."""
    logger.info("Executing rename operation for %d files...", len(changes))
    results = rename_files(changes)
    _display_rename_results(results)


def _display_rename_results(results: dict[str, list[str]]) -> None:
    """
    Display summary statistics for rename operations.

    Args:
        results (dict[str, list[str]]): Results dictionary with keys
            'succeeded', 'skipped', 'failed'.

    Returns:
        None
    """
    succeeded_count = len(results["succeeded"])
    skipped_count = len(results["skipped"])
    failed_count = len(results["failed"])
    total_count = succeeded_count + skipped_count + failed_count

    # Log summary statistics with user-friendly formatting
    logger.info(
        "\nRename operation complete: %d succeeded, %d skipped, %d failed (total: %d)",
        succeeded_count,
        skipped_count,
        failed_count,
        total_count,
    )
    logger.info("  ✓ Successfully renamed: %d file(s)", succeeded_count)
    if skipped_count > 0:
        logger.info("  ⊘ Skipped (already exists): %d file(s)", skipped_count)
    if failed_count > 0:
        logger.info("  ✗ Failed: %d file(s)", failed_count)

    # Display details for skipped and failed files
    if skipped_count > 0:
        logger.info("\nSkipped files (destination already exists):")
        for file_path in results["skipped"]:
            basename = os.path.basename(file_path)
            logger.info("  - %s", basename)

    if failed_count > 0:
        logger.info("\nFailed files (see logs for details):")
        for file_path in results["failed"]:
            basename = os.path.basename(file_path)
            logger.info("  - %s", basename)
