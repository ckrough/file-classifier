"""
Deterministic path builder for file classification.

This module provides simple, deterministic path construction from
normalized metadata.
No AI decisions needed - all metadata is already normalized by the
Standards Agent.
"""

from dataclasses import dataclass


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


def build_path(
    domain: str,
    category: str,
    doctype: str,
    vendor_name: str,
    subject: str,
    date: str,
    file_extension: str,
) -> PathMetadata:
    """
    Build file path deterministically from normalized metadata.

    Taxonomy: domain/category/doctype/
    Filename format: doctype-vendor-subject-YYYYMMDD.ext

    Example:
        >>> build_path("financial", "retail", "receipt", "acme_markets",
        ...           "grocery_shopping", "20230923", ".pdf")
        PathMetadata(
            directory_path="financial/retail/receipt/",
            filename="receipt-acme_markets-grocery_shopping-20230923.pdf",
            full_path="financial/retail/receipt/"
            "receipt-acme_markets-grocery_shopping-20230923.pdf"
        )

    Args:
        domain: Primary domain (financial, property, insurance,
            tax, legal, medical)
        category: Functional category within domain
            (banking, retail, etc.)
        doctype: Document type (statement, receipt, invoice, etc.)
        vendor_name: Normalized vendor name (must not be "unknown")
        subject: Brief description/subject (normalized)
        date: Date in YYYYMMDD format (empty string if no date)
        file_extension: File extension including dot
            (e.g., ".pdf", ".txt")

    Returns:
        PathMetadata: Complete path information

    Raises:
        ValueError: If vendor_name is unknown/empty
            (should be caught by Standards Agent)
        ValueError: If path exceeds filesystem limits even
            after truncation
    """
    # Defensive normalization (ensure lowercase, no extra whitespace)
    domain = domain.lower().strip()
    category = category.lower().strip()
    doctype = doctype.lower().strip()
    vendor_name = vendor_name.lower().strip() if vendor_name else ""
    subject = subject.lower().strip() if subject else "document"
    date = date.strip() if date else ""

    # Validate vendor (unknown vendors should error out)
    if not vendor_name or vendor_name in ["unknown", "n/a", "none", "generic"]:
        raise ValueError(
            f"Cannot build path with unknown vendor (got: '{vendor_name}'). "
            f"Standards Agent must determine specific vendor from document content."
        )

    # Build directory path: domain/category/doctype/
    directory_path = f"{domain}/{category}/{doctype}/"

    # Build filename: doctype-vendor-subject-YYYYMMDD.ext
    if date:
        filename = f"{doctype}-{vendor_name}-{subject}-{date}{file_extension}"
    else:
        filename = f"{doctype}-{vendor_name}-{subject}{file_extension}"

    full_path = f"{directory_path}{filename}"

    # Path length validation (filesystem limit ~255 chars, leave buffer)
    max_path_length = 250
    if len(full_path) > max_path_length:
        # Truncate subject to fit within limit
        # Preserve critical metadata: domain, category, doctype, vendor, date
        excess = len(full_path) - max_path_length
        max_subject_len = len(subject) - excess

        if max_subject_len < 3:
            raise ValueError(
                f"Path too long even after truncating subject: {len(full_path)} chars. "
                f"Consider using shorter domain/category/doctype/vendor values."
            )

        # Truncate subject intelligently
        subject = subject[:max_subject_len]

        # Rebuild filename with truncated subject
        if date:
            filename = f"{doctype}-{vendor_name}-{subject}-{date}{file_extension}"
        else:
            filename = f"{doctype}-{vendor_name}-{subject}{file_extension}"

        full_path = f"{directory_path}{filename}"

    return PathMetadata(
        directory_path=directory_path, filename=filename, full_path=full_path
    )
