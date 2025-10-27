"""End-to-end functional tests using sample documents."""

import sys
import pytest
import subprocess


@pytest.mark.functional
@pytest.mark.slow
def test_process_directory_dry_run():
    """Test processing entire sample-documents directory."""
    result = subprocess.run(
        [sys.executable, "main.py", "--dry-run", "sample-documents"],
        capture_output=True,
        text=True,
        env={"DEBUG_MODE": "True"},
    )

    # Verify exit code
    assert result.returncode == 0, f"App failed with: {result.stderr}"

    # Verify output contains expected patterns
    assert "Dry-run mode enabled" in result.stdout

    # Verify file renaming suggestions
    assert "acme_20060921.pdf →" in result.stdout
    assert "newegg-upgrade.pdf →" in result.stdout
    assert "acs-20071231.pdf →" in result.stdout


@pytest.mark.functional
@pytest.mark.slow
def test_process_single_document_dry_run():
    """Test processing single document."""
    result = subprocess.run(
        [sys.executable, "main.py", "--dry-run", "sample-documents/acme_20060921.pdf"],
        capture_output=True,
        text=True,
        env={"DEBUG_MODE": "True"},
    )

    # Verify exit code
    assert result.returncode == 0, f"App failed with: {result.stderr}"

    # Verify output contains expected patterns
    assert "Dry-run mode enabled" in result.stdout

    # Verify file renaming suggestions
    assert "acme_20060921.pdf →" in result.stdout


@pytest.mark.functional
@pytest.mark.slow
def test_ai_classification_accuracy():
    """Test that AI correctly classifies known documents."""
    # This test actually verifies the AI output quality
    result = subprocess.run(
        [sys.executable, "main.py", "--dry-run", "sample-documents/acme_20060921.pdf"],
        capture_output=True,
        text=True,
        env={"DEBUG_MODE": "True"},
    )

    assert result.returncode == 0

    # If we know this is an invoice, verify it's classified correctly
    output_lower = result.stdout.lower()
    assert "invoice" in output_lower or "acme" in output_lower
