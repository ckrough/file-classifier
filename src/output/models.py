"""
Output data models for structured classification results.

These models define the JSON schema for outputting classification results
in a Unix-friendly format suitable for piping to other tools.
"""

from pydantic import BaseModel, Field


class ClassificationMetadata(BaseModel):
    """
    Metadata extracted from document classification.

    Contains structured information about the document's classification
    including domain, category, vendor, date, document type, and subject.
    """

    domain: str = Field(description="Top-level domain (e.g., 'financial', 'medical')")
    category: str = Field(
        description="Category within domain (e.g., 'banking', 'insurance')"
    )
    vendor: str = Field(description="Vendor/organization name (normalized)")
    date: str = Field(description="Document date in YYYYMMDD format")
    doctype: str = Field(description="Document type (e.g., 'statement', 'invoice')")
    subject: str = Field(description="Brief subject description")


class ClassificationResult(BaseModel):
    """
    Complete classification result for a single document.

    This is the primary output model containing the original file path,
    suggested new path and filename, and detailed metadata.
    """

    original: str = Field(description="Original file path")
    suggested_path: str = Field(description="Suggested directory path (relative)")
    suggested_name: str = Field(description="Suggested filename with extension")
    full_path: str = Field(description="Complete suggested path (path/filename)")
    metadata: ClassificationMetadata = Field(
        description="Detailed classification metadata"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "original": "document.pdf",
                "suggested_path": "financial/banking/chase",
                "suggested_name": "statement-chase-checking-20240115.pdf",
                "full_path": (
                    "financial/banking/chase/" "statement-chase-checking-20240115.pdf"
                ),
                "metadata": {
                    "domain": "financial",
                    "category": "banking",
                    "vendor": "chase",
                    "date": "20240115",
                    "doctype": "statement",
                    "subject": "checking",
                },
            }
        }
