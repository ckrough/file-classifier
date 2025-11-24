"""Unit tests for deterministic path builder module with GPO naming standards."""

import pytest
from src.path.builder import build_path, PathMetadata
from src.config import settings as app_settings

# For this test module, we assert compact_gpo behavior explicitly
app_settings.NAMING_STYLE = "compact_gpo"


@pytest.mark.unit
def test_build_path_standard():
    """Test standard path building with NIST-compliant concise format."""
    result = build_path(
        domain="financial",
        category="retail",
        doctype="receipt",
        vendor_name="acme_markets",
        subject="groceries",  # Subject ignored in new format
        date="20230923",
        file_extension=".pdf",
    )

    assert isinstance(result, PathMetadata)
    assert result.directory_path == "Financial/Retail/Receipts/"  # Plural folder
    assert result.filename == "acme_markets_20230923.pdf"  # Vendor + date only (lowercase)
    assert result.full_path == "Financial/Retail/Receipts/acme_markets_20230923.pdf"


@pytest.mark.unit
def test_build_path_banking_statement():
    """Test path building for banking statement (NIST-compliant)."""
    result = build_path(
        domain="financial",
        category="banking",
        doctype="statement",
        vendor_name="chase",
        subject="checking",  # Subject ignored
        date="20240115",
        file_extension=".pdf",
    )

    assert result.directory_path == "Financial/Banking/Statements/"  # Plural
    assert result.filename == "chase_20240115.pdf"  # Vendor + date only (lowercase)
    assert result.full_path == "Financial/Banking/Statements/chase_20240115.pdf"


@pytest.mark.unit
def test_build_path_no_date():
    """Test path building without date (NIST-compliant)."""
    result = build_path(
        domain="legal",
        category="contracts",
        doctype="agreement",
        vendor_name="acme_corp",
        subject="service",  # Subject ignored
        date="",
        file_extension=".pdf",
    )

    assert result.directory_path == "Legal/Contracts/Agreements/"  # Plural
    assert result.filename == "acme_corp.pdf"  # Vendor only (no date, lowercase)
    assert result.full_path == "Legal/Contracts/Agreements/acme_corp.pdf"


@pytest.mark.unit
def test_build_path_unknown_vendor_raises_error():
    """Test that unknown vendor raises ValueError."""
with pytest.raises(ValueError, match="Invalid vendor"):
        build_path(
            domain="financial",
            category="banking",
            doctype="statement",
            vendor_name="unknown",
            subject="checking",
            date="20230923",
            file_extension=".pdf",
        )


@pytest.mark.unit
def test_build_path_empty_vendor_raises_error():
    """Test that empty vendor raises ValueError."""
with pytest.raises(ValueError, match="Invalid vendor"):
        build_path(
            domain="financial",
            category="banking",
            doctype="statement",
            vendor_name="",
            subject="checking",
            date="20230923",
            file_extension=".pdf",
        )


@pytest.mark.unit
def test_build_path_na_vendor_raises_error():
    """Test that 'n/a' vendor gets normalized to 'na' and raises ValueError."""
    # After normalization, "n/a" becomes "na" which should still be rejected
with pytest.raises(ValueError, match="Invalid vendor"):
        build_path(
            domain="financial",
            category="banking",
            doctype="statement",
            vendor_name="n/a",  # Gets normalized to "na" (slash removed)
            subject="checking",
            date="20230923",
            file_extension=".pdf",
        )


@pytest.mark.unit
def test_build_path_generic_vendor_raises_error():
    """Test that 'generic' vendor raises ValueError."""
with pytest.raises(ValueError, match="Invalid vendor"):
        build_path(
            domain="financial",
            category="banking",
            doctype="statement",
            vendor_name="generic",
            subject="checking",
            date="20230923",
            file_extension=".pdf",
        )


@pytest.mark.unit
def test_build_path_concise_filenames():
    """Test that concise NIST-compliant filenames prevent path length issues."""
    # Even with very long vendor name, should stay under limit
    long_vendor = "very_long_vendor_name_that_would_cause_issues"

    result = build_path(
        domain="financial",
        category="banking",
        doctype="statement",
        vendor_name=long_vendor,
        subject="ignored",  # Subject no longer in filename
        date="20230923",
        file_extension=".pdf",
    )

    # Path should be under configured budget (200)
    assert len(result.full_path) <= 200
    assert "Financial/Banking/Statements/" in result.full_path
    assert "20230923" in result.filename
    # Subject should NOT appear in filename
    assert "ignored" not in result.filename.lower()


@pytest.mark.unit
def test_build_path_normalizes_uppercase():
    """Test that uppercase inputs are normalized then converted to Title_Case format."""
    result = build_path(
        domain="FINANCIAL",
        category="BANKING",
        doctype="STATEMENT",
        vendor_name="CHASE",
        subject="CHECKING",  # Ignored
        date="20230923",
        file_extension=".PDF",
    )

    assert result.directory_path == "Financial/Banking/Statements/"  # Plural
    assert result.filename == "chase_20230923.PDF"  # Vendor + date only (lowercase base, ext preserved)


@pytest.mark.unit
def test_build_path_strips_whitespace():
    """Test that whitespace is stripped from inputs."""
    result = build_path(
        domain="  financial  ",
        category=" banking ",
        doctype=" statement ",
        vendor_name=" chase ",
        subject=" checking ",  # Ignored
        date=" 20230923 ",
        file_extension=".pdf",
    )

    assert result.directory_path == "Financial/Banking/Statements/"  # Plural
    assert result.filename == "chase_20230923.pdf"  # Vendor + date only (lowercase)


@pytest.mark.unit
def test_build_path_txt_file():
    """Test path building for .txt file (NIST-compliant)."""
    result = build_path(
        domain="legal",
        category="correspondence",
        doctype="letter",
        vendor_name="acme_corp",
        subject="contract",  # Ignored
        date="20240301",
        file_extension=".txt",
    )

    assert result.full_path.endswith(".txt")
    assert result.filename == "acme_corp_20240301.txt"  # Vendor + date only (lowercase)
    assert result.directory_path == "Legal/Correspondence/Letters/"  # Plural


@pytest.mark.unit
def test_build_path_extremely_long_raises_error():
    """Test that paths too long even after truncation raise ValueError."""
    # Create extremely long base path that can't be truncated enough
    very_long_domain = "a" * 100
    very_long_category = "b" * 100
    very_long_doctype = "c" * 100
    very_long_vendor = "d" * 100

    with pytest.raises(ValueError, match="Path too long"):
        build_path(
            domain=very_long_domain,
            category=very_long_category,
            doctype=very_long_doctype,
            vendor_name=very_long_vendor,
            subject="subject",
            date="20230923",
            file_extension=".pdf",
        )


@pytest.mark.unit
def test_build_path_tax_document():
    """Test path building for tax document with irregular plural (NIST-compliant)."""
    result = build_path(
        domain="financial",
        category="tax",
        doctype="1040",
        vendor_name="irs",
        subject="return",  # Ignored
        date="20240415",
        file_extension=".pdf",
    )

    assert result.directory_path == "Financial/Tax/1040s/"  # Irregular plural
    assert result.filename == "irs_20240415.pdf"  # Vendor + date only (lowercase)
    assert result.full_path == "Financial/Tax/1040s/irs_20240415.pdf"


@pytest.mark.unit
def test_build_path_medical_document():
    """Test path building for medical document (NIST-compliant)."""
    result = build_path(
        domain="medical",
        category="records",
        doctype="lab_results",
        vendor_name="quest_diagnostics",
        subject="blood_work",  # Ignored
        date="20240201",
        file_extension=".pdf",
    )

    assert result.directory_path == "Medical/Records/Lab_Results/"  # Already plural
    assert result.filename == "quest_diagnostics_20240201.pdf"  # Vendor + date only (lowercase)


@pytest.mark.unit
def test_build_path_multi_word_vendor():
    """Test that underscores in vendor names are preserved and Title_Case applied."""
    result = build_path(
        domain="financial",
        category="retail",
        doctype="receipt",
        vendor_name="home_depot",
        subject="supplies",  # Ignored
        date="20230615",
        file_extension=".pdf",
    )

    # Vendor with underscores remains lowercase with underscores in compact_gpo
    assert result.filename == "home_depot_20230615.pdf"
    assert result.directory_path == "Financial/Retail/Receipts/"  # Plural


# GPO-Specific Validation Tests


@pytest.mark.unit
def test_build_path_plural_folders():
    """Test that doctype folders are pluralized per naming conventions."""
    # Test regular pluralization
    result1 = build_path(
        domain="financial",
        category="banking",
        doctype="receipt",
        vendor_name="vendor",
        subject="test",
        date="20240101",
        file_extension=".pdf",
    )
    assert result1.directory_path == "Financial/Banking/Receipts/"

    # Test irregular plural
    result2 = build_path(
        domain="insurance",
        category="health",
        doctype="policy",
        vendor_name="vendor",
        subject="test",
        date="20240101",
        file_extension=".pdf",
    )
    assert result2.directory_path == "Insurance/Health/Policies/"

    # Test already plural
    result3 = build_path(
        domain="medical",
        category="records",
        doctype="lab_results",
        vendor_name="vendor",
        subject="test",
        date="20240101",
        file_extension=".pdf",
    )
    assert result3.directory_path == "Medical/Records/Lab_Results/"


@pytest.mark.unit
def test_build_path_rejects_invalid_characters():
    """Invalid characters in vendor should be rejected (no auto-normalization)."""
    # @ symbol should be removed by normalization
    with pytest.raises(ValueError):
        build_path(
            domain="financial",
            category="banking",
            doctype="statement",
            vendor_name="chase@bank",  # invalid
            subject="checking",
            date="20230923",
            file_extension=".pdf",
        )


@pytest.mark.unit
def test_build_path_rejects_special_characters():
    """Special characters like & should be rejected (no auto-normalization)."""
    # & symbol should be removed by normalization
    with pytest.raises(ValueError):
        build_path(
            domain="financial",
            category="banking",
            doctype="statement",
            vendor_name="bank&trust",  # invalid
            subject="checking",
            date="20230923",
            file_extension=".pdf",
        )


@pytest.mark.unit
def test_build_path_enforces_title_case_for_folders():
    """Test that folder names use Title Case per GPO standards (NIST-compliant)."""
    result = build_path(
        domain="financial",
        category="banking",
        doctype="statement",
        vendor_name="chase",
        subject="checking",  # Ignored
        date="20240115",
        file_extension=".pdf",
    )

    # Verify Title Case in directory path with plural folder
    assert result.directory_path == "Financial/Banking/Statements/"
    assert "financial" not in result.directory_path  # lowercase should not appear


@pytest.mark.unit
def test_filename_lowercase_with_underscores_compact_gpo():
    """Filename should be lowercase_with_underscores in compact_gpo style."""
    result = build_path(
        domain="medical",
        category="records",
        doctype="lab_results",
        vendor_name="quest_diagnostics",
        subject="blood_work",  # Ignored
        date="20240201",
        file_extension=".pdf",
    )

    # Verify lowercase_with_underscores for vendor in filename
    assert result.filename == "quest_diagnostics_20240201.pdf"
    # Verify underscores preserved
    assert "_" in result.filename
    # Verify no hyphens as separators
    assert result.filename.count("-") == 0  # Only underscores


@pytest.mark.unit
def test_build_path_uses_underscores_not_hyphens():
    """Test that GPO format uses underscores as separators, not hyphens."""
    result = build_path(
        domain="financial",
        category="banking",
        doctype="statement",
        vendor_name="bank_of_america",
        subject="checking",  # Ignored
        date="20240115",
        file_extension=".pdf",
    )

    # Count separators (should only use underscores between components)
    assert "_" in result.filename
    # Hyphens should not appear as separators
    components = result.filename.replace(".pdf", "").split("_")
    assert len(components) == 4  # bank, of, america, 20240115
    assert result.filename == "bank_of_america_20240115.pdf"
