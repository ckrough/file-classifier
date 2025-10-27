"""Benchmark tests for MIME detection optimizations."""

import tempfile
from pathlib import Path

import pytest

from src.files.operations import is_supported_filetype, _get_mime_detector


@pytest.mark.benchmark
def test_mime_detector_singleton_initialization(benchmark):
    """
    Benchmark singleton Magic instance initialization.

    This measures the cost of the one-time initialization vs the old approach
    of creating a new instance every call.
    """
    # Clear any existing singleton for accurate measurement
    from src.files import operations

    operations._MIME_DETECTOR = None

    result = benchmark(_get_mime_detector)

    # Validate correctness
    assert result is not None
    assert hasattr(result, "from_file")


@pytest.mark.benchmark
def test_mime_detection_with_singleton(benchmark):
    """
    Benchmark MIME type detection using the singleton pattern.

    This measures the performance with the optimization applied - should be
    significantly faster than the old approach of creating Magic instances.
    """
    # Create a temporary text file for testing
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test content")
        temp_file = f.name

    try:
        result = benchmark(is_supported_filetype, temp_file)

        # Validate correctness
        assert result is True  # .txt files are supported
    finally:
        Path(temp_file).unlink(missing_ok=True)


@pytest.mark.benchmark
def test_mime_detection_batch_performance(benchmark):
    """
    Benchmark MIME detection across multiple files (simulates directory scan).

    This measures the cumulative performance improvement when processing many
    files - the primary use case where singleton pattern provides major gains.
    """
    # Create multiple temporary files
    temp_files = []
    for i in range(10):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"Test content {i}")
            temp_files.append(f.name)

    def check_all_files():
        return [is_supported_filetype(f) for f in temp_files]

    try:
        results = benchmark(check_all_files)

        # Validate correctness
        assert len(results) == 10
        assert all(results)  # All .txt files should be supported
    finally:
        for temp_file in temp_files:
            Path(temp_file).unlink(missing_ok=True)
