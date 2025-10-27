"""Benchmark tests for filename generation functions."""

import pytest

from src.analysis.filename import generate_filename
from src.analysis.models import Analysis


@pytest.mark.benchmark
def test_generate_filename_with_date(benchmark, sample_analysis_simple):
    """Benchmark generate_filename with date field present."""
    result = benchmark(generate_filename, sample_analysis_simple)

    # Validate correctness
    assert isinstance(result, str)
    assert result.count("-") >= 3  # vendor-category-description-date
    assert "2024-01-15" in result


@pytest.mark.benchmark
def test_generate_filename_without_date(benchmark):
    """Benchmark generate_filename without date field."""
    analysis = Analysis(
        category="invoice",
        vendor="acme",
        description="services",
        date="",  # No date
    )

    result = benchmark(generate_filename, analysis)

    # Validate correctness
    assert isinstance(result, str)
    assert result == "acme-invoice-services"


@pytest.mark.benchmark
def test_generate_filename_complex(benchmark, sample_analysis_complex):
    """Benchmark generate_filename with long strings."""
    result = benchmark(generate_filename, sample_analysis_complex)

    # Validate correctness
    assert isinstance(result, str)
    assert len(result) > 50  # Complex strings should produce longer filename


@pytest.mark.benchmark
def test_generate_filename_batch(benchmark, sample_analysis_batch):
    """Benchmark generate_filename across a batch of 100 items."""

    def generate_batch(batch):
        return [generate_filename(item) for item in batch]

    results = benchmark(generate_batch, sample_analysis_batch)

    # Validate correctness
    assert len(results) == 100
    assert all(isinstance(r, str) for r in results)
    assert all("-" in r for r in results)
