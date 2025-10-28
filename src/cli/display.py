"""
User display and interaction.

This module handles displaying suggested file changes to the user
and getting approval for renaming or moving operations.
"""

import logging
import os
from typing import Optional

from src.files.operations import rename_files, move_files

__all__ = ["handle_suggested_changes"]

logger = logging.getLogger(__name__)


def handle_suggested_changes(
    changes: list[dict[str, str]],
    dry_run: bool,
    destination_root: Optional[str] = None,
    move_enabled: bool = False,
) -> None:
    """
    Handle user verification and approval of suggested changes.

    Supports two modes:
    - Rename mode: Renames files in-place (default)
    - Move mode: Moves files to archive directory structure (requires destination_root)

    Args:
        changes (list[dict[str, str]]): List of change dictionaries containing
            file_path, suggested_name, and destination_relative_path.
        dry_run (bool): If True, display changes but don't apply them.
        destination_root (Optional[str]): Root directory for archive structure.
            Required when move_enabled is True.
        move_enabled (bool): If True, move files to archive structure. If False,
            rename files in-place. Defaults to False.

    Returns:
        None
    """
    if not changes:
        msg = "No changes were suggested."
        logger.info(msg)
        return

    # Display changes based on mode
    if move_enabled and destination_root:
        mode_msg = "Move mode: Files will be moved to archive structure\n"
        logger.info(mode_msg)

        logger.info("Displaying %d suggested moves:", len(changes))
        for change in changes:
            source_basename = os.path.basename(change["file_path"])
            destination_relative = change.get("destination_relative_path", "")
            change_msg = f"{source_basename} → {destination_relative}\n"
            logger.info("  %s", change_msg)
    else:
        mode_msg = "Rename mode: Files will be renamed in current directory\n"
        logger.info(mode_msg)

        logger.info("Displaying %d suggested renames:", len(changes))
        for change in changes:
            file_path = change["file_path"]
            suggested_name = change["suggested_name"]

            current_basename = os.path.basename(file_path)
            # Note: suggested_name already includes extension from multi-agent pipeline
            change_msg = f"{current_basename} → {suggested_name}\n"
            logger.info("  %s", change_msg)

    if dry_run:
        dry_run_msg = "Dry-run mode enabled. No changes will be made."
        logger.info(dry_run_msg)
        return

    # Auto-execute (no confirmation prompt by default)
    user_confirmation = input("Approve changes? (yes/no): ").strip().lower()
    logger.info("User response to approval prompt: '%s'", user_confirmation)

    if user_confirmation != "yes":
        cancel_msg = "Operation canceled by user."
        logger.info(cancel_msg)
        return

    # Execute based on mode
    if move_enabled and destination_root:
        logger.info("Executing move operation for %d files...", len(changes))
        results = move_files(changes, destination_root, dry_run=False)
        _display_move_results(results)
    else:
        logger.info("Executing rename operation for %d files...", len(changes))
        rename_files(changes)
        success_msg = f"{len(changes)} file(s) have been renamed."
        logger.info(success_msg)


def _display_move_results(results: dict[str, list[str]]) -> None:
    """
    Display summary statistics for move operations.

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
        "\nMove operation complete: %d succeeded, %d skipped, %d failed (total: %d)",
        succeeded_count,
        skipped_count,
        failed_count,
        total_count,
    )
    logger.info("  ✓ Successfully moved: %d file(s)", succeeded_count)
    if skipped_count > 0:
        logger.info("  ⊘ Skipped (already exists): %d file(s)", skipped_count)
    if failed_count > 0:
        logger.info("  ✗ Failed: %d file(s)", failed_count)

    # Display details for skipped and failed files
    if skipped_count > 0:
        logger.info("\nSkipped files (already exist at destination):")
        for file_path in results["skipped"]:
            basename = os.path.basename(file_path)
            logger.info("  - %s", basename)

    if failed_count > 0:
        logger.info("\nFailed files (see logs for details):")
        for file_path in results["failed"]:
            basename = os.path.basename(file_path)
            logger.info("  - %s", basename)
