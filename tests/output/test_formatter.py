"""Unit tests for output formatter."""

import json
from io import StringIO

import pytest

from src.output.formatter import OutputFormatter
from src.output.models import ClassificationMetadata, ClassificationResult


@pytest.fixture
def sample_result():
    """Create a sample ClassificationResult for testing."""
    return ClassificationResult(
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


@pytest.fixture
def sample_results():
    """Create a list of sample ClassificationResults for testing."""
    return [
        ClassificationResult(
            original="doc1.pdf",
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
        ),
        ClassificationResult(
            original="doc2.pdf",
            suggested_path="medical/insurance/blue_cross",
            suggested_name="eob-blue_cross-claim-20240201.pdf",
            full_path="medical/insurance/blue_cross/eob-blue_cross-claim-20240201.pdf",
            metadata=ClassificationMetadata(
                domain="medical",
                category="insurance",
                vendor="blue_cross",
                date="20240201",
                doctype="eob",
                subject="claim",
            ),
        ),
    ]


@pytest.mark.unit
def test_formatter_default_format():
    """Test that OutputFormatter defaults to JSON format."""
    formatter = OutputFormatter()
    assert formatter.format_type == "json"


@pytest.mark.unit
def test_formatter_json_format():
    """Test that OutputFormatter can be initialized with JSON format."""
    formatter = OutputFormatter(format_type="json")
    assert formatter.format_type == "json"


@pytest.mark.unit
def test_formatter_csv_format():
    """Test that OutputFormatter can be initialized with CSV format."""
    formatter = OutputFormatter(format_type="csv")
    assert formatter.format_type == "csv"


@pytest.mark.unit
def test_formatter_tsv_format():
    """Test that OutputFormatter can be initialized with TSV format."""
    formatter = OutputFormatter(format_type="tsv")
    assert formatter.format_type == "tsv"


@pytest.mark.unit
def test_to_json(sample_result):
    """Test JSON serialization of a single result."""
    formatter = OutputFormatter(format_type="json")
    output = formatter.to_json(sample_result)

    # Parse JSON to verify it's valid
    data = json.loads(output)

    assert data["original"] == "document.pdf"
    assert data["suggested_path"] == "financial/banking/chase"
    assert data["suggested_name"] == "statement-chase-checking-20240115.pdf"
    assert data["metadata"]["domain"] == "financial"
    assert data["metadata"]["category"] == "banking"


@pytest.mark.unit
def test_to_json_batch(sample_results):
    """Test newline-delimited JSON for multiple results."""
    formatter = OutputFormatter(format_type="json")
    output = formatter.to_json_batch(sample_results)

    lines = output.split("\n")
    assert len(lines) == 2

    # Verify each line is valid JSON
    data1 = json.loads(lines[0])
    data2 = json.loads(lines[1])

    assert data1["original"] == "doc1.pdf"
    assert data2["original"] == "doc2.pdf"


@pytest.mark.unit
def test_to_csv_with_header(sample_results):
    """Test CSV output with header row."""
    formatter = OutputFormatter(format_type="csv")
    output = formatter.to_csv(sample_results, include_header=True)

    lines = output.split("\n")
    assert len(lines) == 3  # Header + 2 data rows

    # Check header (strip any trailing \r for platform compatibility)
    assert lines[0].rstrip("\r") == (
        "original,suggested_path,suggested_name,full_path,"
        "domain,category,vendor,date,doctype,subject"
    )

    # Check first data row
    assert "doc1.pdf" in lines[1]
    assert "financial/banking/chase" in lines[1]
    assert "statement-chase-checking-20240115.pdf" in lines[1]


@pytest.mark.unit
def test_to_csv_without_header(sample_results):
    """Test CSV output without header row."""
    formatter = OutputFormatter(format_type="csv")
    output = formatter.to_csv(sample_results, include_header=False)

    lines = output.split("\n")
    assert len(lines) == 2  # Only 2 data rows, no header

    # First line should be data, not header
    assert "doc1.pdf" in lines[0]
    assert "original" not in lines[0]  # Header keyword should not appear


@pytest.mark.unit
def test_to_csv_empty_list():
    """Test CSV output with empty results list."""
    formatter = OutputFormatter(format_type="csv")
    output = formatter.to_csv([], include_header=True)

    assert output == ""


@pytest.mark.unit
def test_to_tsv_with_header(sample_results):
    """Test TSV output with header row."""
    formatter = OutputFormatter(format_type="tsv")
    output = formatter.to_tsv(sample_results, include_header=True)

    lines = output.split("\n")
    assert len(lines) == 3  # Header + 2 data rows

    # Check that tabs are used as delimiters
    assert "\t" in lines[0]
    assert "\t" in lines[1]

    # Check header fields
    header_fields = lines[0].split("\t")
    assert "original" in header_fields
    assert "suggested_path" in header_fields
    assert "domain" in header_fields


@pytest.mark.unit
def test_to_tsv_without_header(sample_results):
    """Test TSV output without header row."""
    formatter = OutputFormatter(format_type="tsv")
    output = formatter.to_tsv(sample_results, include_header=False)

    lines = output.split("\n")
    assert len(lines) == 2  # Only 2 data rows, no header

    # First line should be data, not header
    assert "doc1.pdf" in lines[0]
    assert "original" not in lines[0]


@pytest.mark.unit
def test_to_tsv_empty_list():
    """Test TSV output with empty results list."""
    formatter = OutputFormatter(format_type="tsv")
    output = formatter.to_tsv([], include_header=True)

    assert output == ""


@pytest.mark.unit
def test_format_single_json(sample_result):
    """Test format_single with JSON format."""
    formatter = OutputFormatter(format_type="json")
    output = formatter.format_single(sample_result)

    data = json.loads(output)
    assert data["original"] == "document.pdf"


@pytest.mark.unit
def test_format_single_csv(sample_result):
    """Test format_single with CSV format."""
    formatter = OutputFormatter(format_type="csv")
    output = formatter.format_single(sample_result)

    # Should be a single CSV row without header
    assert "document.pdf" in output
    assert "financial/banking/chase" in output


@pytest.mark.unit
def test_format_single_tsv(sample_result):
    """Test format_single with TSV format."""
    formatter = OutputFormatter(format_type="tsv")
    output = formatter.format_single(sample_result)

    # Should be a single TSV row without header
    assert "\t" in output
    assert "document.pdf" in output


@pytest.mark.unit
def test_format_batch_json(sample_results):
    """Test format_batch with JSON format."""
    formatter = OutputFormatter(format_type="json")
    output = formatter.format_batch(sample_results)

    lines = output.split("\n")
    assert len(lines) == 2


@pytest.mark.unit
def test_format_batch_csv(sample_results):
    """Test format_batch with CSV format."""
    formatter = OutputFormatter(format_type="csv")
    output = formatter.format_batch(sample_results, include_header=True)

    lines = output.split("\n")
    assert len(lines) == 3  # Header + 2 data rows


@pytest.mark.unit
def test_write_result_json(sample_result):
    """Test write_result with JSON format to StringIO."""
    formatter = OutputFormatter(format_type="json")
    output = StringIO()

    formatter.write_result(sample_result, file=output)

    content = output.getvalue()
    data = json.loads(content.strip())  # Strip to remove trailing newline
    assert data["original"] == "document.pdf"


@pytest.mark.unit
def test_write_batch_json(sample_results):
    """Test write_batch with JSON format to StringIO."""
    formatter = OutputFormatter(format_type="json")
    output = StringIO()

    formatter.write_batch(sample_results, file=output)

    content = output.getvalue()
    lines = content.strip().split("\n")
    assert len(lines) == 2

    # Each line should be valid JSON
    data1 = json.loads(lines[0])
    data2 = json.loads(lines[1])
    assert data1["original"] == "doc1.pdf"
    assert data2["original"] == "doc2.pdf"


@pytest.mark.unit
def test_write_batch_csv(sample_results):
    """Test write_batch with CSV format to StringIO."""
    formatter = OutputFormatter(format_type="csv")
    output = StringIO()

    formatter.write_batch(sample_results, file=output, include_header=True)

    content = output.getvalue()
    lines = content.strip().split("\n")
    assert len(lines) == 3  # Header + 2 data rows

    # Check header
    assert "original" in lines[0]
    assert "suggested_path" in lines[0]


@pytest.mark.unit
def test_write_batch_tsv(sample_results):
    """Test write_batch with TSV format to StringIO."""
    formatter = OutputFormatter(format_type="tsv")
    output = StringIO()

    formatter.write_batch(sample_results, file=output, include_header=True)

    content = output.getvalue()
    lines = content.strip().split("\n")
    assert len(lines) == 3  # Header + 2 data rows

    # Check that tabs are used
    assert "\t" in lines[0]
    assert "\t" in lines[1]


@pytest.mark.unit
def test_format_single_unsupported_format():
    """Test that format_single raises error for unsupported format."""
    formatter = OutputFormatter(format_type="json")
    formatter.format_type = "xml"  # Manually set to unsupported format

    sample = ClassificationResult(
        original="test.pdf",
        suggested_path="test",
        suggested_name="test.pdf",
        full_path="test/test.pdf",
        metadata=ClassificationMetadata(
            domain="test",
            category="test",
            vendor="test",
            date="20240101",
            doctype="test",
            subject="test",
        ),
    )

    with pytest.raises(ValueError, match="Unsupported format"):
        formatter.format_single(sample)


@pytest.mark.unit
def test_format_batch_unsupported_format():
    """Test that format_batch raises error for unsupported format."""
    formatter = OutputFormatter(format_type="json")
    formatter.format_type = "xml"  # Manually set to unsupported format

    with pytest.raises(ValueError, match="Unsupported format"):
        formatter.format_batch([])
