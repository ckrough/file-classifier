"""
Data models for file analysis.

Defines Pydantic models for the multi-agent document processing pipeline:
- RawMetadata: Classification Agent output
- NormalizedMetadata: Standards Enforcement Agent output
- PathMetadata: Moved to src.path.builder (deterministic, non-Pydantic dataclass)
- Analysis: DEPRECATED - Legacy model kept for backward compatibility only

Note: PathMetadata is now a simple dataclass in src.path.builder since path construction
is deterministic and doesn't require Pydantic validation.
"""

from typing import Optional

from pydantic import BaseModel, Field

__all__ = [
    "Analysis",
    "RawMetadata",
    "NormalizedMetadata",
]


class Analysis(BaseModel):
    """
    DEPRECATED: Legacy model for backward compatibility only.

    This model is deprecated and kept only for backward compatibility with
    existing tests. The multi-agent pipeline now uses:
    - RawMetadata (Classification Agent output)
    - NormalizedMetadata (Standards Enforcement Agent output)
    - PathMetadata (Deterministic path builder - in src.path.builder)

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
        description=(
            "Primary domain: Financial, Property, Insurance, Tax, Legal, Medical"
        ),
    )
    category: str = Field(
        ...,
        description=(
            "Functional category within domain (e.g., Banking, Real_Estate, Health)"
        ),
    )
    doctype: str = Field(
        ...,
        description=(
            "Document type: statement, receipt, invoice, policy, deed, title, etc."
        ),
    )
    vendor_raw: str = Field(
        ...,
        description=(
            "Raw vendor name as found in document (e.g., 'Bank of America')"
        ),
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

    Canonical, style-neutral fields used by naming styles. Do not include
    style-specific separators or casing decisions here.

    Domain, category, and doctype are expected to be drawn from a bounded,
    canonical taxonomy (or explicit "other" buckets), not arbitrary strings.

    CRITICAL: vendor_name must NEVER be "unknown", "n/a", "none", or empty.
    Standards Agent must determine a specific vendor or use generic descriptors
    (e.g., "gas_station", "grocery_store", "personal").
    """

    domain: str = Field(
        ...,
        description=(
            "Canonical domain name from taxonomy (lowercase slug, e.g., 'financial')."
        ),
    )
    category: str = Field(
        ...,
        description=(
            "Canonical category within domain (lowercase slug, e.g., 'banking')."
        ),
    )
    doctype: str = Field(
        ...,
        description=(
            "Canonical document type slug from taxonomy (e.g., 'statement', 'receipt')."
        ),
    )
    vendor_name: str = Field(
        ...,
        description=(
            "Standardized vendor name (canonical slug; lowercase with underscores)."
        ),
    )
    date: str = Field(
        ...,
        description=(
            "Selected date in YYYY, YYYYMM, or YYYYMMDD per canonical policy"
        ),
    )
    subject: str = Field(
        ...,
        description=(
            "Canonical subject (1-3 words, lowercase, underscores; WHAT not HOW)"
        ),
    )
    version: Optional[str] = Field(
        None,
        description="Optional version when explicit: vNN, final, or draft",
    )
