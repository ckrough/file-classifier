"""Benchmark tests for file operations - string manipulation only."""

import pytest


@pytest.mark.benchmark
def test_path_construction_simple(benchmark):
    """Benchmark simple path string construction pattern."""
    import os

    def construct_paths():
        base_dir = "/some/directory/path"
        filename = "document-name"
        ext = ".pdf"
        return os.path.join(base_dir, f"{filename}{ext}")

    result = benchmark(construct_paths)

    # Validate correctness
    assert isinstance(result, str)
    assert result.endswith(".pdf")


@pytest.mark.benchmark
def test_path_construction_batch(benchmark):
    """Benchmark path construction for batch of files."""
    import os

    def construct_batch_paths():
        base_dir = "/some/directory/path"
        filenames = [f"document-{i}" for i in range(100)]
        ext = ".pdf"
        return [os.path.join(base_dir, f"{name}{ext}") for name in filenames]

    results = benchmark(construct_batch_paths)

    # Validate correctness
    assert len(results) == 100
    assert all(isinstance(r, str) for r in results)


@pytest.mark.benchmark
def test_extension_extraction(benchmark):
    """Benchmark file extension extraction pattern."""
    import os

    def extract_extensions():
        file_paths = [
            "/path/to/document.pdf",
            "/path/to/image.png",
            "/path/to/text.txt",
        ] * 33  # 99 files

        return [os.path.splitext(fp) for fp in file_paths]

    results = benchmark(extract_extensions)

    # Validate correctness
    assert len(results) == 99
    assert all(isinstance(r, tuple) for r in results)
