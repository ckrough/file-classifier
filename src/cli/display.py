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
    changes: list[dict[str, str]], dry_run: bool, auto_rename: bool
) -> None:
    """
    Handle user verification and approval of suggested changes.

    Args:
        changes (list[dict[str, str]]): List of change dictionaries containing
            file_path and suggested_name.
        dry_run (bool): If True, display changes but don't apply them.
        auto_rename (bool): If True, automatically apply changes without asking.

    Returns:
        None
    """
    if not changes:
        print("No changes were suggested.")
        return

    for change in changes:
        file_path = change["file_path"]
        suggested_name = change["suggested_name"]

        # Extract extension from original file and append to suggested name for display
        _, ext = os.path.splitext(file_path)
        suggested_name_with_ext = f"{suggested_name}{ext}"

        # Display the current and suggested filenames
        current_basename = os.path.basename(file_path)
        print(f"{current_basename} → {suggested_name_with_ext}\n")

    if dry_run:
        print("Dry-run mode enabled. No changes will be made.")
        return

    if auto_rename:
        rename_files(changes)
        print("Files have been renamed.")
        return

    user_confirmation = input("Approve rename? (yes/no): ").strip().lower()
    if user_confirmation == "yes":
        rename_files(changes)
        print("Files have been renamed.")
    else:
        print("Renaming was canceled by the user.")
