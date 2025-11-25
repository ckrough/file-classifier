"""Benchmark tests for AI prompt functions - caching behavior."""

import pytest

from src.ai.prompts import get_prompt_template, clear_prompt_cache
from src.taxonomy import reset_taxonomy


@pytest.fixture(autouse=True)
def reset_state():
    """Reset taxonomy and prompt cache before each test."""
    reset_taxonomy()
    clear_prompt_cache()
    yield
    reset_taxonomy()
    clear_prompt_cache()


@pytest.mark.benchmark
def test_prompt_template_generation_first_call(benchmark):
    """
    Benchmark first call to get_prompt_template (uncached).

    Note: This measures cache overhead on first call.
    """
    # Clear cache before benchmark
    clear_prompt_cache()

    result = benchmark(get_prompt_template, "classification-agent")

    # Validate correctness
    assert result is not None
    assert hasattr(result, "format_messages")


@pytest.mark.benchmark
def test_prompt_template_generation_cached(benchmark):
    """
    Benchmark cached calls to get_prompt_template.

    This measures the effectiveness of @lru_cache decorator.
    """
    # Warm up cache
    get_prompt_template("classification-agent")

    result = benchmark(get_prompt_template, "classification-agent")

    # Validate correctness
    assert result is not None
    assert hasattr(result, "format_messages")


@pytest.mark.benchmark
def test_prompt_template_repeated_calls(benchmark):
    """Benchmark repeated calls to test cache hit rate."""

    def repeated_calls():
        results = []
        for _ in range(100):
            results.append(get_prompt_template("classification-agent"))
        return results

    # Warm up cache
    get_prompt_template("classification-agent")

    results = benchmark(repeated_calls)

    # Validate correctness
    assert len(results) == 100
    # All should be the same cached object
    assert all(r is results[0] for r in results)
