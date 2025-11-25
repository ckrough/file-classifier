"""Unit tests for the central taxonomy module."""

import pytest

from src.taxonomy import (
    canonical_domain,
    canonical_category,
    canonical_doctype,
    CANONICAL_DOMAINS,
    CANONICAL_CATEGORIES,
    CANONICAL_DOCTYPES,
)


@pytest.mark.unit
def test_canonical_domain_direct_and_alias():
    """Domains should resolve directly or via simple aliases."""
    assert "financial" in CANONICAL_DOMAINS

    # Direct match, case/spacing/underscore insensitive
    assert canonical_domain("Financial") == "financial"
    assert canonical_domain(" financial ") == "financial"

    # Alias mapping
    assert canonical_domain("finances") == "financial"
    assert canonical_domain("finance") == "financial"

    # Domain sometimes emitted as "real_estate" should map to property
    assert canonical_domain("real estate") == "property"


@pytest.mark.unit
def test_canonical_category_within_domain_and_aliases():
    """Categories should resolve within a domain, including common aliases."""
    # Direct category
    assert canonical_category("financial", "banking") == "banking"

    # Normalization of spaces/hyphens/upper-case
    assert canonical_category("financial", "Banking") == "banking"

    # Alias: home_repairs -> home_improvement under property
    assert canonical_category("property", "home_repairs") == "home_improvement"
    assert canonical_category("property", "Remodeling") == "home_improvement"

    # Unknown category in a known domain returns None (taxonomy layer only)
    assert canonical_category("financial", "nonexistent_category") is None


@pytest.mark.unit
def test_canonical_doctype_and_aliases():
    """Doctypes should normalize synonyms into the canonical vocabulary."""
    # Direct canonical
    assert "statement" in CANONICAL_DOCTYPES
    assert canonical_doctype("statement") == "statement"
    assert canonical_doctype(" Statement ") == "statement"

    # Aliases
    assert canonical_doctype("bill") == "invoice"
    assert canonical_doctype("billing_statement") == "statement"
    assert canonical_doctype("Explanation of Benefits") == "eob"
    assert canonical_doctype("owners_manual") == "manual"
    assert canonical_doctype("user guide") == "guide"

    # Unknown doctype returns None at taxonomy level
    assert canonical_doctype("memo") is None


@pytest.mark.unit
def test_canonical_category_respects_domain_aliases():
    """Category normalization should still work when domain comes via alias form."""
    # "Finances" is an alias for the canonical "financial" domain
    assert canonical_category("Finances", "banking") == "banking"
    # Mixed case and spacing still normalize correctly
    assert canonical_category(" finances ", "Banking") == "banking"


@pytest.mark.unit
def test_unknown_domain_and_category_return_none():
    """Unknown domains or categories should return None at the taxonomy layer."""
    assert canonical_domain("unknown_domain") is None
    assert canonical_domain("") is None
    assert canonical_category("unknown_domain", "banking") is None
