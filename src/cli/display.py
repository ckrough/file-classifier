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
        print("No changes were suggested.")
        return

    # Display changes based on mode
    if move_enabled and destination_root:
        print("Move mode: Files will be moved to archive structure\n")
        for change in changes:
            source_basename = os.path.basename(change["file_path"])
            destination_relative = change.get("destination_relative_path", "")
            print(f"{source_basename} → {destination_relative}\n")
    else:
        print("Rename mode: Files will be renamed in current directory\n")
        for change in changes:
            file_path = change["file_path"]
            suggested_name = change["suggested_name"]

            # Extract extension from original file and append for display
            _, ext = os.path.splitext(file_path)
            suggested_name_with_ext = f"{suggested_name}{ext}"

            current_basename = os.path.basename(file_path)
            print(f"{current_basename} → {suggested_name_with_ext}\n")

    if dry_run:
        print("Dry-run mode enabled. No changes will be made.")
        return

    # Auto-execute (no confirmation prompt by default)
    user_confirmation = input("Approve changes? (yes/no): ").strip().lower()
    if user_confirmation != "yes":
        print("Operation canceled by user.")
        return

    # Execute based on mode
    if move_enabled and destination_root:
        results = move_files(changes, destination_root, dry_run=False)
        _display_move_results(results)
    else:
        rename_files(changes)
        print(f"{len(changes)} file(s) have been renamed.")


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

    print("\nMove operation complete:")
    print(f"  ✓ Successfully moved: {succeeded_count} file(s)")
    if skipped_count > 0:
        print(f"  ⊘ Skipped (already exists): {skipped_count} file(s)")
    if failed_count > 0:
        print(f"  ✗ Failed: {failed_count} file(s)")

    # Display details for skipped and failed files
    if skipped_count > 0:
        print("\nSkipped files (already exist at destination):")
        for file_path in results["skipped"]:
            print(f"  - {os.path.basename(file_path)}")

    if failed_count > 0:
        print("\nFailed files (see logs for details):")
        for file_path in results["failed"]:
            print(f"  - {os.path.basename(file_path)}")
