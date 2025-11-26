"""Pipeline-level tests for taxonomy normalization and enforcement.

Taxonomy enforcement rules:
- Domain: STRICT - must exist in taxonomy (no new domains allowed)
- Category: FLEXIBLE - prefer existing, but new categories are allowed
- Doctype: FLEXIBLE - prefer existing, but new doctypes are allowed
"""

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
def test_pipeline_rejects_unknown_domain(mock_classify, mock_standardize):
    """Unknown domains should always cause pipeline failure (domains are strict)."""

    mock_classify.return_value = RawMetadata(
        domain="unknown_domain",
        category="some_category",
        doctype="statement",
        vendor_raw="Vendor",
        date_raw="2024-01-01",
        subject_raw="Subject",
        account_types=None,
    )

    mock_standardize.return_value = NormalizedMetadata(
        domain="unknown_domain",
        category="some_category",
        doctype="statement",
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
    assert "unknown domain" in msg


@pytest.mark.unit
@patch("src.agents.pipeline.standardize_metadata")
@patch("src.agents.pipeline.classify_document")
def test_pipeline_allows_new_doctypes(mock_classify, mock_standardize, monkeypatch):
    """New doctypes should be allowed (doctypes are flexible)."""

    monkeypatch.setattr(app_settings, "NAMING_STYLE", "descriptive_nara", raising=False)

    mock_classify.return_value = RawMetadata(
        domain="financial",
        category="banking",
        doctype="memo",  # New doctype not in taxonomy
        vendor_raw="Acme Bank",
        date_raw="2024-01-01",
        subject_raw="Account update",
        account_types=None,
    )

    mock_standardize.return_value = NormalizedMetadata(
        domain="financial",
        category="banking",
        doctype="memo",  # New doctype
        vendor_name="acme_bank",
        date="20240101",
        subject="account_update",
    )

    client = DummyAIClient()
    _, _, path = process_document_multi_agent(
        content="Sample content", filename="doc.pdf", ai_client=client
    )

    # New doctype should be accepted and used in the path
    assert "Financial/Banking/Memos/" in path.full_path
    assert "memo_" in path.filename


@pytest.mark.unit
@patch("src.agents.pipeline.standardize_metadata")
@patch("src.agents.pipeline.classify_document")
def test_pipeline_allows_new_categories(mock_classify, mock_standardize, monkeypatch):
    """New categories should be allowed (categories are flexible)."""

    monkeypatch.setattr(app_settings, "NAMING_STYLE", "descriptive_nara", raising=False)

    mock_classify.return_value = RawMetadata(
        domain="property",
        category="home_repairs_misc",  # New category not in taxonomy
        doctype="receipt",
        vendor_raw="Home Services LLC",
        date_raw="2024-02-02",
        subject_raw="Repairs",
        account_types=None,
    )

    mock_standardize.return_value = NormalizedMetadata(
        domain="property",
        category="home_repairs_misc",  # New category
        doctype="receipt",
        vendor_name="home_services_llc",
        date="20240202",
        subject="repairs",
    )

    client = DummyAIClient()
    _, _, path = process_document_multi_agent(
        content="Sample content", filename="repairs.pdf", ai_client=client
    )

    # New category should be accepted and used in the path
    # Path builder title-cases components
    assert "Property/Home_Repairs_Misc/" in path.full_path
    assert path.filename.endswith("_20240202.pdf")
