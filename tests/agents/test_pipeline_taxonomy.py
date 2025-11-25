"""Pipeline-level tests for taxonomy normalization and enforcement."""

from unittest.mock import Mock, patch

import pytest

from src.agents.pipeline import process_document_multi_agent
from src.analysis.models import RawMetadata, NormalizedMetadata
from src.path.builder import PathMetadata
from src.config import settings as app_settings


class DummyAIClient(Mock):
    """Lightweight stand-in for AIClient to satisfy type hints."""


@pytest.mark.unit
@patch("src.agents.pipeline.standardize_metadata")
@patch("src.agents.pipeline.classify_document")
def test_pipeline_applies_taxonomy_canonicalization(
    mock_classify, mock_standardize, monkeypatch
):
    """Non-canonical domain/category/doctype should be canonicalized before path build."""

    # Use monkeypatch so global settings are restored after the test, avoiding
    # cross-test interference with naming/path builder tests.
    monkeypatch.setattr(app_settings, "TAXONOMY_STRICT_MODE", True, raising=False)
    monkeypatch.setattr(app_settings, "NAMING_STYLE", "descriptive_nara", raising=False)

    mock_classify.return_value = RawMetadata(
        domain="Finances",
        category="Banking",
        doctype="Billing_Statement",
        vendor_raw="Acme Bank",
        date_raw="2023-10-01",
        subject_raw="Checking",
        account_types=["checking"],
    )

    mock_standardize.return_value = NormalizedMetadata(
        domain="Finances",  # non-canonical
        category="Banking",  # non-canonical casing
        doctype="billing_statement",  # alias for "statement"
        vendor_name="acme_bank",
        date="20231001",
        subject="checking",
    )

    # Run pipeline
    client = DummyAIClient()
    raw, normalized, path = process_document_multi_agent(
        content="Sample content", filename="doc.pdf", ai_client=client
    )

    # Raw/normalized reflect what agents returned
    assert raw.domain == "Finances"
    assert normalized.domain == "Finances"

    # Path should be built using canonical taxonomy values
    # Domain should resolve to "financial", doctype alias to "statement".
    assert "Financial/Banking/Statements/" in path.full_path
    # With descriptive_nara style, filename encodes doctype, vendor, subject, and date.
    assert path.filename == "statement_acme_bank_checking_20231001.pdf"


@pytest.mark.unit
@patch("src.agents.pipeline.standardize_metadata")
@patch("src.agents.pipeline.classify_document")
def test_pipeline_strict_mode_rejects_unknown_taxonomy(
    mock_classify, mock_standardize, monkeypatch
):
    """In strict mode, unknown categories/doctypes should cause pipeline failure."""

    monkeypatch.setattr(app_settings, "TAXONOMY_STRICT_MODE", True, raising=False)

    mock_classify.return_value = RawMetadata(
        domain="financial",
        category="unknown_category",
        doctype="memo",
        vendor_raw="Vendor",
        date_raw="2024-01-01",
        subject_raw="Subject",
        account_types=None,
    )

    mock_standardize.return_value = NormalizedMetadata(
        domain="financial",
        category="unknown_category",
        doctype="memo",
        vendor_name="vendor",
        date="20240101",
        subject="subject",
    )

    client = DummyAIClient()

    with pytest.raises(RuntimeError) as exc_info:
        process_document_multi_agent(
            content="Sample content", filename="doc.pdf", ai_client=client
        )

    msg = str(exc_info.value)
    assert "Taxonomy validation failed" in msg


@pytest.mark.unit
@patch("src.agents.pipeline.standardize_metadata")
@patch("src.agents.pipeline.classify_document")
def test_pipeline_fallback_maps_unknown_to_other(
    mock_classify, mock_standardize, monkeypatch
):
    """In fallback mode, unknown category/doctype map to 'other' while domain must be known."""

    monkeypatch.setattr(app_settings, "TAXONOMY_STRICT_MODE", False, raising=False)

    mock_classify.return_value = RawMetadata(
        domain="property",
        category="home_repairs_misc",
        doctype="memo",
        vendor_raw="Home Services LLC",
        date_raw="2024-02-02",
        subject_raw="Repairs",
        account_types=None,
    )

    mock_standardize.return_value = NormalizedMetadata(
        domain="property",
        category="home_repairs_misc",
        doctype="memo",
        vendor_name="home_services_llc",
        date="20240202",
        subject="repairs",
    )

    client = DummyAIClient()
    _, _, path = process_document_multi_agent(
        content="Sample content", filename="repairs.pdf", ai_client=client
    )

    # Category/doctype should fall back to 'other', which will appear as
    # "Other/Others" in the directory path when Title-Cased and pluralized.
    assert "Property/Other/" in path.directory_path or "Property/Other/" in path.full_path
    assert "Others/" in path.directory_path
    assert path.filename.endswith("_20240202.pdf")
