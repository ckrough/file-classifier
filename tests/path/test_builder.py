"""Unit tests for deterministic path builder module."""

import pytest
from src.path.builder import build_path, PathMetadata


@pytest.mark.unit
def test_build_path_standard():
    """Test standard path building with all fields provided."""
    result = build_path(
        domain="financial",
        category="retail",
        doctype="receipt",
        vendor_name="acme_markets",
        subject="grocery_shopping",
        date="20230923",
        file_extension=".pdf",
    )

    assert isinstance(result, PathMetadata)
    assert result.directory_path == "financial/retail/receipt/"
    assert (
        result.filename == "receipt-acme_markets-grocery_shopping-20230923.pdf"
    )
    assert (
        result.full_path
        == "financial/retail/receipt/receipt-acme_markets-grocery_shopping-20230923.pdf"
    )


@pytest.mark.unit
def test_build_path_banking_statement():
    """Test path building for banking statement."""
    result = build_path(
        domain="financial",
        category="banking",
        doctype="statement",
        vendor_name="chase",
        subject="checking",
        date="20240115",
        file_extension=".pdf",
    )

    assert result.directory_path == "financial/banking/statement/"
    assert result.filename == "statement-chase-checking-20240115.pdf"
    assert (
        result.full_path
        == "financial/banking/statement/statement-chase-checking-20240115.pdf"
    )


@pytest.mark.unit
def test_build_path_no_date():
    """Test path building without date (empty string)."""
    result = build_path(
        domain="legal",
        category="contracts",
        doctype="agreement",
        vendor_name="acme_corp",
        subject="service_agreement",
        date="",
        file_extension=".pdf",
    )

    assert result.directory_path == "legal/contracts/agreement/"
    assert result.filename == "agreement-acme_corp-service_agreement.pdf"
    assert (
        result.full_path
        == "legal/contracts/agreement/agreement-acme_corp-service_agreement.pdf"
    )


@pytest.mark.unit
def test_build_path_unknown_vendor_raises_error():
    """Test that unknown vendor raises ValueError."""
    with pytest.raises(ValueError, match="unknown vendor"):
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
    with pytest.raises(ValueError, match="unknown vendor"):
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
    """Test that 'n/a' vendor raises ValueError."""
    with pytest.raises(ValueError, match="unknown vendor"):
        build_path(
            domain="financial",
            category="banking",
            doctype="statement",
            vendor_name="n/a",
            subject="checking",
            date="20230923",
            file_extension=".pdf",
        )


@pytest.mark.unit
def test_build_path_generic_vendor_raises_error():
    """Test that 'generic' vendor raises ValueError."""
    with pytest.raises(ValueError, match="unknown vendor"):
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
def test_build_path_truncates_long_subject():
    """Test that overly long paths truncate subject to fit filesystem limits."""
    long_subject = "a" * 300  # Very long subject

    result = build_path(
        domain="financial",
        category="banking",
        doctype="statement",
        vendor_name="chase",
        subject=long_subject,
        date="20230923",
        file_extension=".pdf",
    )

    # Path should be truncated to <= 250 chars
    assert len(result.full_path) <= 250

    # Critical metadata should be preserved
    assert "financial/banking/statement/" in result.full_path
    assert "chase" in result.filename
    assert "20230923" in result.filename

    # Subject should be truncated
    assert len(result.filename) < len(f"statement-chase-{long_subject}-20230923.pdf")


@pytest.mark.unit
def test_build_path_normalizes_uppercase():
    """Test that uppercase inputs are normalized to lowercase."""
    result = build_path(
        domain="FINANCIAL",
        category="BANKING",
        doctype="STATEMENT",
        vendor_name="CHASE",
        subject="CHECKING",
        date="20230923",
        file_extension=".PDF",
    )

    assert result.directory_path == "financial/banking/statement/"
    assert result.filename == "statement-chase-checking-20230923.PDF"


@pytest.mark.unit
def test_build_path_strips_whitespace():
    """Test that whitespace is stripped from inputs."""
    result = build_path(
        domain="  financial  ",
        category=" banking ",
        doctype=" statement ",
        vendor_name=" chase ",
        subject=" checking ",
        date=" 20230923 ",
        file_extension=".pdf",
    )

    assert result.directory_path == "financial/banking/statement/"
    assert result.filename == "statement-chase-checking-20230923.pdf"


@pytest.mark.unit
def test_build_path_txt_file():
    """Test path building for .txt file."""
    result = build_path(
        domain="legal",
        category="correspondence",
        doctype="letter",
        vendor_name="acme_corp",
        subject="contract_negotiation",
        date="20240301",
        file_extension=".txt",
    )

    assert result.full_path.endswith(".txt")
    assert result.filename == "letter-acme_corp-contract_negotiation-20240301.txt"


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
    """Test path building for tax document under financial domain."""
    result = build_path(
        domain="financial",
        category="tax",
        doctype="1040",
        vendor_name="irs",
        subject="federal_return",
        date="20240415",
        file_extension=".pdf",
    )

    assert result.directory_path == "financial/tax/1040/"
    assert result.filename == "1040-irs-federal_return-20240415.pdf"
    assert result.full_path == "financial/tax/1040/1040-irs-federal_return-20240415.pdf"


@pytest.mark.unit
def test_build_path_medical_document():
    """Test path building for medical document."""
    result = build_path(
        domain="medical",
        category="records",
        doctype="lab_results",
        vendor_name="quest_diagnostics",
        subject="blood_work",
        date="20240201",
        file_extension=".pdf",
    )

    assert result.directory_path == "medical/records/lab_results/"
    assert result.filename == "lab_results-quest_diagnostics-blood_work-20240201.pdf"


@pytest.mark.unit
def test_build_path_underscore_subject():
    """Test that underscores in subject are preserved."""
    result = build_path(
        domain="financial",
        category="retail",
        doctype="receipt",
        vendor_name="home_depot",
        subject="home_improvement_supplies",
        date="20230615",
        file_extension=".pdf",
    )

    assert "home_improvement_supplies" in result.filename
    assert (
        result.filename
        == "receipt-home_depot-home_improvement_supplies-20230615.pdf"
    )
