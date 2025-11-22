"""
Deterministic path builder for file classification.

This module provides simple, deterministic path construction from
normalized metadata.
No AI decisions needed - all metadata is already normalized by the
Standards Agent.

Implements GPO naming standards:
- Title_Case_With_Underscores for filenames
- Title Case for folder names
- Character restrictions (a-z, 0-9, _, -)
- Path length limit (255 chars)
- Hierarchy depth limit (8 levels)
"""

import re
from dataclasses import dataclass

from src.config.settings import (
    MAX_PATH_LENGTH,
    MAX_HIERARCHY_DEPTH,
    ALLOWED_CHARS_PATTERN,
    FILLER_WORDS,
)


def _to_title_case_with_underscores(text: str) -> str:
    """
    Convert lowercase_with_underscores to Title_Case_With_Underscores.

    Examples:
        >>> _to_title_case_with_underscores("bank_of_america")
        'Bank_Of_America'
        >>> _to_title_case_with_underscores("checking")
        'Checking'
    """
    if not text:
        return text
    words = text.split("_")
    return "_".join(word.capitalize() for word in words)


def _to_title_case(text: str) -> str:
    """
    Convert lowercase text to Title Case (for folder names).

    Examples:
        >>> _to_title_case("financial")
        'Financial'
        >>> _to_title_case("banking")
        'Banking'
    """
    if not text:
        return text
    # Handle underscores by replacing with spaces, title casing, then replacing back
    words = text.replace("_", " ").split()
    return " ".join(word.capitalize() for word in words).replace(" ", "_")


def _pluralize_doctype(doctype: str) -> str:
    """
    Pluralize document type for folder naming convention.

    Container folders should use plural forms per naming conventions.

    Examples:
        >>> _pluralize_doctype("receipt")
        'Receipts'
        >>> _pluralize_doctype("statement")
        'Statements'
        >>> _pluralize_doctype("invoice")
        'Invoices'
        >>> _pluralize_doctype("lab_results")
        'Lab_Results'
    """
    # Common irregular plurals
    irregular = {
        "policy": "Policies",
        "1099": "1099s",
        "1040": "1040s",
        "w2": "W2s",
    }

    doctype_lower = doctype.lower()
    if doctype_lower in irregular:
        return irregular[doctype_lower]

    # Apply Title Case first
    formatted = _to_title_case(doctype)

    # Check if already plural (ends with 's' but not ss, es, xs, zs)
    if formatted.endswith("s") and not formatted.endswith(("ss", "es", "xs", "zs")):
        # Already plural (e.g., Lab_Results, Accounts)
        return formatted

    # Simple pluralization rules
    if formatted.endswith("y") and len(formatted) > 1 and formatted[-2] not in "aeiou":
        # policy -> Policies, proxy -> Proxies
        return formatted[:-1] + "ies"
    if formatted.endswith(("s", "x", "z", "ch", "sh")):
        # business -> businesses, box -> boxes
        return formatted + "es"
    # Most cases: receipt -> receipts, statement -> statements
    return formatted + "s"


def _normalize_vendor_name(vendor: str) -> str:
    """
    Apply defensive normalization to vendor names.

    Handles cases where AI output may contain formatting that should be
    handled programmatically:
    - Removes domain extensions (.com, .net, .org, .edu, .gov, .co.uk, etc.)
    - Removes www prefix
    - Replaces spaces with underscores
    - Removes special characters (except underscores and hyphens)
    - Converts to lowercase

    Examples:
        >>> _normalize_vendor_name("Walmart.com")
        'walmart'
        >>> _normalize_vendor_name("www.amazon.com")
        'amazon'
        >>> _normalize_vendor_name("Bank & Trust Co.")
        'bank_trust_co'
        >>> _normalize_vendor_name("AT&T Wireless")
        'att_wireless'
    """
    if not vendor:
        return vendor

    # Remove www prefix (case insensitive)
    if vendor.lower().startswith("www."):
        vendor = vendor[4:]

    # Remove common domain extensions
    domain_extensions = [
        ".com",
        ".net",
        ".org",
        ".edu",
        ".gov",
        ".mil",
        ".co.uk",
        ".co",
        ".io",
        ".ai",
    ]
    vendor_lower = vendor.lower()
    for ext in domain_extensions:
        if vendor_lower.endswith(ext):
            vendor = vendor[: -len(ext)]
            break

    # Replace spaces with underscores
    vendor = vendor.replace(" ", "_")

    # Remove special characters (keep only alphanumeric, underscores, hyphens)
    # This handles &, commas, periods, etc.
    vendor = re.sub(r"[^a-z0-9_-]", "", vendor, flags=re.IGNORECASE)

    # Convert to lowercase
    vendor = vendor.lower()

    # Clean up multiple underscores
    vendor = re.sub(r"_+", "_", vendor)

    # Remove leading/trailing underscores
    vendor = vendor.strip("_")

    return vendor


def _normalize_subject(subject: str) -> str:
    """
    Apply defensive normalization to subject text.

    Handles cases where AI output may contain formatting that should be
    handled programmatically:
    - Removes filler words (a, and, of, the, to)
    - Replaces spaces with underscores
    - Removes special characters (except underscores and hyphens)
    - Converts to lowercase

    Examples:
        >>> _normalize_subject("explanation of benefits")
        'explanation_benefits'
        >>> _normalize_subject("bill of sale")
        'bill_sale'
        >>> _normalize_subject("Annual Report")
        'annual_report'
    """
    if not subject:
        return subject

    # Convert to lowercase first for easier processing
    subject = subject.lower()

    # Replace spaces with underscores for word splitting
    subject = subject.replace(" ", "_")

    # Remove special characters (keep only alphanumeric, underscores, hyphens)
    subject = re.sub(r"[^a-z0-9_-]", "", subject, flags=re.IGNORECASE)

    # Split by underscores to process words
    words = subject.split("_")

    # Remove filler words
    words = [word for word in words if word and word not in FILLER_WORDS]

    # Rejoin with underscores
    subject = "_".join(words)

    # Clean up multiple underscores
    subject = re.sub(r"_+", "_", subject)

    # Remove leading/trailing underscores
    subject = subject.strip("_")

    return subject


def _validate_characters(text: str, component_name: str) -> None:
    """
    Validate that text contains only allowed characters (a-z, 0-9, _, -).

    Args:
        text: Text to validate
        component_name: Name of component for error message

    Raises:
        ValueError: If text contains invalid characters
    """
    if not ALLOWED_CHARS_PATTERN.match(text):
        invalid_chars = set(
            c for c in text if not re.match(r"[a-z0-9_-]", c, re.IGNORECASE)
        )
        raise ValueError(
            f"Invalid characters in {component_name}: {invalid_chars}. "
            f"Only a-z, 0-9, underscores (_), and hyphens (-) are allowed "
            f"per GPO standards."
        )


def _validate_no_periods_in_folders(directory_path: str) -> None:
    """
    Validate that folder names do not contain periods.

    Args:
        directory_path: Directory path to validate

    Raises:
        ValueError: If any folder name contains a period
    """
    folders = directory_path.rstrip("/").split("/")
    for folder in folders:
        if "." in folder:
            raise ValueError(
                f"Folder name '{folder}' contains period. "
                f"Folder names must not contain periods per GPO standards."
            )


def _validate_hierarchy_depth(directory_path: str) -> None:
    """
    Validate that directory hierarchy does not exceed maximum depth.

    Args:
        directory_path: Directory path to validate

    Raises:
        ValueError: If hierarchy exceeds MAX_HIERARCHY_DEPTH
    """
    depth = len(directory_path.rstrip("/").split("/"))
    if depth > MAX_HIERARCHY_DEPTH:
        raise ValueError(
            f"Directory hierarchy depth ({depth}) exceeds maximum allowed "
            f"({MAX_HIERARCHY_DEPTH}). GPO standards require maximum 8 levels."
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


def build_path(  # pylint: disable=too-many-arguments,too-many-positional-arguments
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

    Applies GPO naming standards:
    - Title Case for folder names
    - Title_Case_With_Underscores for filenames
    - Underscores as separators (no hyphens in final output)
    - Character validation (a-z, 0-9, _, -)
    - Path length limit (255 chars)
    - Hierarchy depth limit (8 levels)

    Taxonomy: Domain/Category/Doctypes/ (plural folder)
    Filename format: Vendor_YYYYMMDD.ext (concise, NIST-compliant)

    NIST Principle: Files should be descriptive independent of folder location.
    - Folder hierarchy provides classification context (domain/category/doctype)
    - Filename provides instance identification (vendor + date)
    - No redundant information between folder and filename

    Example:
        >>> build_path("financial", "retail", "receipt", "acme_markets",
        ...           "groceries", "20230923", ".pdf")
        PathMetadata(
            directory_path="Financial/Retail/Receipts/",
            filename="Acme_Markets_20230923.pdf",
            full_path="Financial/Retail/Receipts/Acme_Markets_20230923.pdf"
        )

    Args:
        domain: Primary domain (financial, property, insurance,
            tax, legal, medical) - lowercase from Standards Agent
        category: Functional category within domain
            (banking, retail, etc.) - lowercase from Standards Agent
        doctype: Document type (statement, receipt, invoice, etc.)
            - lowercase from Standards Agent
        vendor_name: Normalized vendor name (must not be "unknown")
            - lowercase from Standards Agent
        subject: Brief description/subject (normalized) - lowercase from Standards Agent
        date: Date in YYYYMMDD format (empty string if no date)
        file_extension: File extension including dot
            (e.g., ".pdf", ".txt")

    Returns:
        PathMetadata: Complete path information with GPO formatting applied

    Raises:
        ValueError: If vendor_name is unknown/empty
        ValueError: If path contains invalid characters
        ValueError: If path exceeds filesystem limits
        ValueError: If hierarchy depth exceeds 8 levels
        ValueError: If folder names contain periods
    """
    # Defensive normalization:
    # Ensure lowercase, no extra whitespace, remove special chars
    domain = domain.lower().strip()
    category = category.lower().strip()
    doctype = doctype.lower().strip()
    date = date.strip() if date else ""

    # Apply specialized normalization for vendor and subject
    # Handles domain extensions, www prefix, filler words, special characters
    vendor_name = _normalize_vendor_name(vendor_name) if vendor_name else ""
    subject = _normalize_subject(subject) if subject else "document"

    # Validate vendor (unknown vendors should error out)
    # Note: After normalization, "n/a" becomes "na", so we check for both
    if not vendor_name or vendor_name in ["unknown", "n/a", "na", "none", "generic"]:
        raise ValueError(
            f"Cannot build path with unknown vendor (got: '{vendor_name}'). "
            f"Standards Agent must determine specific vendor from document content."
        )

    # Validate characters in input components (before case conversion)
    _validate_characters(domain, "domain")
    _validate_characters(category, "category")
    _validate_characters(doctype, "doctype")
    _validate_characters(vendor_name, "vendor_name")
    _validate_characters(subject, "subject")
    if date:
        _validate_characters(date, "date")

    # Apply GPO case conversion
    # Folders: Title Case
    domain_formatted = _to_title_case(domain)
    category_formatted = _to_title_case(category)
    doctype_formatted = _pluralize_doctype(doctype)  # Plural for container folders

    # Filename components: Title_Case_With_Underscores
    # Vendor only, no doctype/subject redundancy
    vendor_file = _to_title_case_with_underscores(vendor_name)

    # Build directory path: Domain/Category/Doctypes/ (plural)
    directory_path = f"{domain_formatted}/{category_formatted}/{doctype_formatted}/"

    # Validate directory structure
    _validate_no_periods_in_folders(directory_path)
    _validate_hierarchy_depth(directory_path)

    # Build filename: Vendor_YYYYMMDD.ext (NIST-compliant, concise)
    # No doctype or subject - folder hierarchy provides classification context
    # Filename provides instance identification only (vendor + date)
    if date:
        filename = f"{vendor_file}_{date}{file_extension}"
    else:
        filename = f"{vendor_file}{file_extension}"

    full_path = f"{directory_path}{filename}"

    # Path length validation (GPO standard: 255 chars max)
    # With concise filenames, this should rarely trigger
    if len(full_path) > MAX_PATH_LENGTH:
        raise ValueError(
            f"Path too long: {len(full_path)} chars. "
            f"Maximum allowed: {MAX_PATH_LENGTH} chars per GPO standards. "
            f"Path: {full_path}"
        )

    return PathMetadata(
        directory_path=directory_path, filename=filename, full_path=full_path
    )
