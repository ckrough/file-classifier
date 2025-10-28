"""
Data models for file analysis.

Defines Pydantic models for the multi-agent document processing pipeline:
- RawMetadata: Classification Agent output
- NormalizedMetadata: Standards Enforcement Agent output
- PathMetadata: Path Construction Agent output
- ResolvedMetadata: Conflict Resolution Agent output
- Analysis: DEPRECATED - Legacy model kept for backward compatibility only
"""

from typing import Optional

from pydantic import BaseModel, Field

__all__ = [
    "Analysis",
    "RawMetadata",
    "NormalizedMetadata",
    "PathMetadata",
    "ResolvedMetadata",
]


class Analysis(BaseModel):
    """
    DEPRECATED: Legacy model for backward compatibility only.

    This model is deprecated and kept only for backward compatibility with
    existing tests. The multi-agent pipeline now uses:
    - RawMetadata (Classification Agent output)
    - NormalizedMetadata (Standards Enforcement Agent output)
    - PathMetadata (Path Construction Agent output)
    - ResolvedMetadata (Conflict Resolution Agent output)

    Do not use this model for new code.
    """

    category: str = Field(
        ..., description="The file's category (e.g., invoice, receipt)."
    )
    vendor: str = Field(..., description="The vendor or source of the file.")
    description: str = Field(
        ..., description="A brief description of the file content."
    )
    date: Optional[str] = Field(
        None, description="The date associated with the file (e.g., 'YYYY-MM-DD')."
    )


class RawMetadata(BaseModel):
    """
    Raw metadata extracted by the Document Classification Agent.

    Contains unprocessed semantic information from document analysis before
    standardization and normalization.
    """

    domain: str = Field(
        ...,
        description="Primary domain: Financial, Property, Insurance, Tax, "
        "Legal, Medical",
    )
    category: str = Field(
        ...,
        description="Functional category within domain "
        "(e.g., Banking, Real_Estate, Health)",
    )
    doctype: str = Field(
        ...,
        description="Document type: statement, receipt, invoice, policy, "
        "deed, title, etc.",
    )
    vendor_raw: str = Field(
        ...,
        description="Raw vendor name as found in document " "(e.g., 'Bank of America')",
    )
    date_raw: str = Field(
        ...,
        description="Most relevant date in document "
        "(invoice date preferred over transaction date)",
    )
    subject_raw: str = Field(
        ..., description="Raw subject matter or purpose (e.g., 'wire transfer')"
    )
    account_types: Optional[list[str]] = Field(
        None, description="Account types mentioned (e.g., 'checking', 'IRA')"
    )


class NormalizedMetadata(BaseModel):
    """
    Normalized metadata from the Standards Enforcement Agent.

    All fields follow the document archival system naming conventions:
    - Lowercase with underscores for multi-word values
    - Standardized vendor names (e.g., 'bank_of_america', 'smith_john_md')
    - ISO 8601 dates (YYYYMMDD)
    - Concise subjects (1-3 words)
    """

    domain: str = Field(..., description="Normalized domain name (unchanged from raw)")
    category: str = Field(
        ..., description="Normalized category name (unchanged from raw)"
    )
    doctype: str = Field(..., description="Standardized document type vocabulary")
    vendor_name: str = Field(
        ...,
        description="Standardized vendor name "
        "(e.g., 'bank_of_america', 'smith_john_md')",
    )
    date: str = Field(
        ...,
        description="Selected and formatted date in YYYYMMDD format (e.g., '20250131')",
    )
    subject: str = Field(
        ...,
        description="Normalized subject (1-3 words, lowercase, underscores)",
    )


class PathMetadata(BaseModel):
    """
    Path and filename constructed by the Path Construction Agent.

    Follows the document archival system directory taxonomy:
    - directory_path: Domain/Category/Vendor/
      (with special cases like Tax/Federal/2024/)
    - filename: doctype-vendor-subject-YYYYMMDD.ext
    - full_path: Complete path combining directory and filename
    """

    directory_path: str = Field(
        ...,
        description="Directory path following taxonomy: " "Domain/Category/Vendor/",
    )
    filename: str = Field(
        ...,
        description="Standardized filename: doctype-vendor-subject-YYYYMMDD",
    )
    full_path: str = Field(..., description="Complete path: directory_path + filename")


class ResolvedMetadata(BaseModel):
    """
    Final resolved metadata from the Conflict Resolution Agent.

    Handles edge cases, ambiguities, and multi-purpose document placement.
    Provides the final decision on file location with optional alternatives.
    """

    final_path: str = Field(
        ..., description="Final resolved full path for the document"
    )
    alternative_paths: Optional[list[str]] = Field(
        None,
        description="Alternative placement options if document serves "
        "multiple purposes",
    )
    resolution_notes: Optional[str] = Field(
        None,
        description="Explanation of resolution logic for edge cases",
    )
