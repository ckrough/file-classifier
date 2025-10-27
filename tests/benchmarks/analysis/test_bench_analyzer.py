"""Benchmark tests for analysis module functions."""

import pytest

from src.analysis.analyzer import standardize_analysis
from src.analysis.models import Analysis


@pytest.mark.benchmark
def test_standardize_analysis_simple(benchmark, sample_analysis_simple):
    """Benchmark standardize_analysis with simple strings."""
    result = benchmark(standardize_analysis, sample_analysis_simple)

    # Validate correctness
    assert isinstance(result, Analysis)
    assert result.category == "invoice"
    assert result.vendor == "acme"


@pytest.mark.benchmark
def test_standardize_analysis_complex(benchmark, sample_analysis_complex):
    """Benchmark standardize_analysis with complex multi-word strings."""
    result = benchmark(standardize_analysis, sample_analysis_complex)

    # Validate correctness
    assert isinstance(result, Analysis)
    assert " " not in result.category
    assert " " not in result.vendor
    assert " " not in result.description
    assert "-" in result.category  # Spaces should be replaced with hyphens


@pytest.mark.benchmark
def test_standardize_analysis_with_spaces(benchmark, sample_analysis_with_spaces):
    """Benchmark standardize_analysis with strings containing multiple consecutive spaces."""
    result = benchmark(standardize_analysis, sample_analysis_with_spaces)

    # Validate correctness
    assert isinstance(result, Analysis)
    assert "   " not in result.category  # Multiple spaces should be replaced


@pytest.mark.benchmark
def test_standardize_analysis_batch(benchmark, sample_analysis_batch):
    """Benchmark standardize_analysis across a batch of 100 items."""

    def standardize_batch(batch):
        return [standardize_analysis(item) for item in batch]

    results = benchmark(standardize_batch, sample_analysis_batch)

    # Validate correctness
    assert len(results) == 100
    assert all(isinstance(r, Analysis) for r in results)
