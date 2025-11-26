"""
Deterministic path builder.

This module constructs folder paths and filenames from canonical, style-neutral
metadata using a pluggable NamingStyle.

Central validations enforced here:
- No periods in folder names
- Single period in filename (extension separator)
- Path length limited by configuration
- Hierarchy depth limited by configuration
"""

from dataclasses import dataclass

from src.config import settings
from src.naming.registry import get_style
from src.analysis.models import NormalizedMetadata


def _validate_no_periods_in_folders(directory_path: str) -> None:
    """Ensure folder names do not contain periods."""
    folders = directory_path.rstrip("/").split("/")
    for folder in folders:
        if "." in folder:
            raise ValueError(
                f"Folder name '{folder}' contains period. Folder names must not contain periods."
            )


def _validate_hierarchy_depth(directory_path: str) -> None:
    """Validate that directory hierarchy does not exceed configured maximum depth."""
    depth = len(directory_path.rstrip("/").split("/"))
    if depth > settings.MAX_HIERARCHY_DEPTH:
        raise ValueError(
            f"Directory hierarchy depth ({depth}) exceeds configured maximum ({settings.MAX_HIERARCHY_DEPTH})."
        )


@dataclass
class PathMetadata:
    """
    Simple path metadata structure.

    Attributes:
        directory_path: Directory path relative to archive root
            (e.g., "financial/retail/receipt/")
        filename: Just the filename with extension
            (e.g., "receipt-acme_markets-grocery-20230923.pdf")
        full_path: Complete path (directory_path + filename)
    """

    directory_path: str
    filename: str
    full_path: str


from typing import Optional


def build_path(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    domain: str,
    category: str,
    doctype: str,
    vendor_name: str,
    subject: str,
    date: str,
    file_extension: str,
    version: Optional[str] = None,
) -> PathMetadata:
    """
    Build file path deterministically from canonical metadata using the active
    NamingStyle.

    Args:
        domain: canonical domain (lowercase slug).
        category: canonical category (lowercase slug).
        doctype: canonical doctype (lowercase slug).
        vendor_name: canonical vendor (lowercase slug; must be specific).
        subject: canonical subject (lowercase slug; may be empty).
        date: canonical date in YYYY, YYYYMM, or YYYYMMDD (may be empty).
        file_extension: file extension including a leading dot (e.g., ".pdf").
        version: optional version token ("vNN", "final", or "draft").

    Returns:
        PathMetadata with directory_path, filename, and full_path.
    """
    normalized = NormalizedMetadata(
        domain=domain.strip().lower(),
        category=category.strip().lower(),
        doctype=doctype.strip().lower(),
        vendor_name=(vendor_name or "").strip().lower(),
        subject=(subject or "").strip().lower(),
        date=(date or "").strip(),
        version=(version or None),
    )

    # Resolve style
    style = get_style(settings.NAMING_STYLE)

    # Folders
    folders = style.folder_components(normalized)
    directory_path = "/".join(folders) + "/"

    # Validate directory structure
    _validate_no_periods_in_folders(directory_path)
    _validate_hierarchy_depth(directory_path)

    # Filename
    filename = style.filename(normalized, file_extension)

    # Single period rule (ensure exactly one dot)
    if filename.count(".") != 1:
        raise ValueError(
            "Filename must contain exactly one period (extension separator)."
        )

    full_path = f"{directory_path}{filename}"

    # Path length validation (configured budget)
    if len(full_path) > settings.MAX_PATH_LENGTH:
        raise ValueError(
            f"Path too long: {len(full_path)} chars. Maximum allowed: {settings.MAX_PATH_LENGTH}."
        )

    return PathMetadata(
        directory_path=directory_path, filename=filename, full_path=full_path
    )
