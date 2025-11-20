"""Unit tests for output data models."""

import pytest
from pydantic import ValidationError

from src.output.models import ClassificationMetadata, ClassificationResult


@pytest.mark.unit
def test_classification_metadata_valid():
    """Test that ClassificationMetadata accepts valid data."""
    metadata = ClassificationMetadata(
        domain="financial",
        category="banking",
        vendor="chase",
        date="20240115",
        doctype="statement",
        subject="checking",
    )

    assert metadata.domain == "financial"
    assert metadata.category == "banking"
    assert metadata.vendor == "chase"
    assert metadata.date == "20240115"
    assert metadata.doctype == "statement"
    assert metadata.subject == "checking"


@pytest.mark.unit
def test_classification_metadata_serialization():
    """Test that ClassificationMetadata serializes to dict correctly."""
    metadata = ClassificationMetadata(
        domain="medical",
        category="insurance",
        vendor="blue_cross",
        date="20240201",
        doctype="eob",
        subject="claim_details",
    )

    data = metadata.model_dump()

    assert data == {
        "domain": "medical",
        "category": "insurance",
        "vendor": "blue_cross",
        "date": "20240201",
        "doctype": "eob",
        "subject": "claim_details",
    }


@pytest.mark.unit
def test_classification_result_valid():
    """Test that ClassificationResult accepts valid data."""
    result = ClassificationResult(
        original="document.pdf",
        suggested_path="financial/banking/chase",
        suggested_name="statement-chase-checking-20240115.pdf",
        full_path="financial/banking/chase/statement-chase-checking-20240115.pdf",
        metadata=ClassificationMetadata(
            domain="financial",
            category="banking",
            vendor="chase",
            date="20240115",
            doctype="statement",
            subject="checking",
        ),
    )

    assert result.original == "document.pdf"
    assert result.suggested_path == "financial/banking/chase"
    assert result.suggested_name == "statement-chase-checking-20240115.pdf"
    assert (
        result.full_path
        == "financial/banking/chase/statement-chase-checking-20240115.pdf"
    )
    assert result.metadata.domain == "financial"


@pytest.mark.unit
def test_classification_result_serialization():
    """Test that ClassificationResult serializes to nested dict correctly."""
    result = ClassificationResult(
        original="invoice.pdf",
        suggested_path="business/invoices/acme_corp",
        suggested_name="invoice-acme-services-20240115.pdf",
        full_path="business/invoices/acme_corp/invoice-acme-services-20240115.pdf",
        metadata=ClassificationMetadata(
            domain="business",
            category="invoices",
            vendor="acme_corp",
            date="20240115",
            doctype="invoice",
            subject="services",
        ),
    )

    data = result.model_dump()

    assert data["original"] == "invoice.pdf"
    assert data["suggested_path"] == "business/invoices/acme_corp"
    assert data["suggested_name"] == "invoice-acme-services-20240115.pdf"
    assert (
        data["full_path"]
        == "business/invoices/acme_corp/invoice-acme-services-20240115.pdf"
    )
    assert data["metadata"]["domain"] == "business"
    assert data["metadata"]["category"] == "invoices"
    assert data["metadata"]["vendor"] == "acme_corp"


@pytest.mark.unit
def test_classification_metadata_missing_fields():
    """Test that ClassificationMetadata requires all fields."""
    with pytest.raises(ValidationError):
        ClassificationMetadata(
            domain="financial",
            category="banking",
            # Missing required fields
        )


@pytest.mark.unit
def test_classification_result_missing_fields():
    """Test that ClassificationResult requires all fields."""
    with pytest.raises(ValidationError):
        ClassificationResult(
            original="document.pdf",
            suggested_path="financial/banking/chase",
            # Missing required fields
        )


@pytest.mark.unit
def test_classification_result_with_empty_strings():
    """Test that ClassificationResult accepts empty strings for optional-like fields."""
    result = ClassificationResult(
        original="unknown.pdf",
        suggested_path="",
        suggested_name="unknown.pdf",
        full_path="unknown.pdf",
        metadata=ClassificationMetadata(
            domain="uncategorized",
            category="",
            vendor="",
            date="",
            doctype="",
            subject="",
        ),
    )

    assert result.suggested_path == ""
    assert result.metadata.category == ""
    assert result.metadata.vendor == ""
