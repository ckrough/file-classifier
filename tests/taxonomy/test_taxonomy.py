"""Unit tests for the central taxonomy module."""

import pytest

from src.taxonomy import (
    canonical_domain,
    canonical_category,
    canonical_doctype,
    get_active_taxonomy,
    reset_taxonomy,
    list_available_taxonomies,
    generate_taxonomy_xml,
)


@pytest.fixture(autouse=True)
def reset_taxonomy_state():
    """Reset taxonomy state before each test to ensure clean slate."""
    reset_taxonomy()
    yield
    reset_taxonomy()


@pytest.mark.unit
def test_load_household_taxonomy():
    """The household taxonomy should load and contain expected domains."""
    taxonomy = get_active_taxonomy()
    assert taxonomy.name == "household"
    assert "financial" in taxonomy.domain_names
    assert "property" in taxonomy.domain_names
    assert "medical" in taxonomy.domain_names


@pytest.mark.unit
def test_list_available_taxonomies():
    """Should list available taxonomy files."""
    taxonomies = list_available_taxonomies()
    assert "household" in taxonomies


@pytest.mark.unit
def test_canonical_domain_direct_and_alias():
    """Domains should resolve directly or via simple aliases."""
    taxonomy = get_active_taxonomy()
    assert "financial" in taxonomy.domain_names

    # Direct match, case/spacing/underscore insensitive
    assert canonical_domain("Financial") == "financial"
    assert canonical_domain(" financial ") == "financial"

    # Alias mapping
    assert canonical_domain("finances") == "financial"
    assert canonical_domain("finance") == "financial"

    # Domain sometimes emitted as "real_estate" should map to property
    assert canonical_domain("real estate") == "property"

    # Scientific/academic aliases should map to reference
    assert canonical_domain("scientific/academic") == "reference"
    assert canonical_domain("scientific") == "reference"
    assert canonical_domain("academic") == "reference"


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

    # Grocery shopping aliases
    assert canonical_category("financial", "grocery_shopping") == "banking"
    assert canonical_category("financial", "groceries") == "banking"

    # Medical health information -> records
    assert canonical_category("medical", "health_information") == "records"

    # Unknown category in a known domain returns None (taxonomy layer only)
    assert canonical_category("financial", "nonexistent_category") is None


@pytest.mark.unit
def test_canonical_doctype_and_aliases():
    """Doctypes should normalize synonyms into the canonical vocabulary."""
    taxonomy = get_active_taxonomy()
    # Direct canonical
    assert "statement" in taxonomy.doctype_names
    assert canonical_doctype("statement") == "statement"
    assert canonical_doctype(" Statement ") == "statement"

    # Aliases
    assert canonical_doctype("bill") == "invoice"
    assert canonical_doctype("billing_statement") == "statement"
    assert canonical_doctype("Explanation of Benefits") == "eob"
    assert canonical_doctype("owners_manual") == "manual"
    assert canonical_doctype("user guide") == "guide"
    assert canonical_doctype("article") == "report"
    assert canonical_doctype("research_paper") == "report"

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


@pytest.mark.unit
def test_generate_taxonomy_xml():
    """Generated XML should contain domains and doctypes."""
    xml = generate_taxonomy_xml()
    assert "<taxonomy>" in xml
    assert "<domains>" in xml
    assert "<doctypes>" in xml
    assert 'name="financial"' in xml
    assert 'name="statement"' in xml


@pytest.mark.unit
def test_taxonomy_categories_loaded():
    """Categories should be loaded correctly per domain."""
    taxonomy = get_active_taxonomy()

    # Financial domain should have banking, credit, etc.
    assert "banking" in taxonomy.category_names.get("financial", set())
    assert "credit" in taxonomy.category_names.get("financial", set())
    assert "taxes" in taxonomy.category_names.get("financial", set())

    # Medical domain should have records, billing, etc.
    assert "records" in taxonomy.category_names.get("medical", set())
    assert "billing" in taxonomy.category_names.get("medical", set())
