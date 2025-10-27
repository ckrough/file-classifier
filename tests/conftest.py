"""Configuration for pytest fixtures used across all test modules."""

import pytest


@pytest.fixture(autouse=True)
def mock_openai_api_key(monkeypatch):
    """Mock the OPENAI_API_KEY environment variable for all tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")


"""Pytest configuration for Claude Code optimization."""


def pytest_configure(config):
    """Configure pytest for optimal Claude Code output."""
    config.option.verbose = 1
    config.option.tbstyle = "short"
    config.option.showcapture = "no"


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add structured summary for LLM processing."""
    print("\n" + "=" * 60)
    print("TEST EXECUTION SUMMARY")
    print("=" * 60)

    # Stats
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))
    errors = len(terminalreporter.stats.get("error", []))

    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print(f"SKIPPED: {skipped}")
    print(f"ERRORS: {errors}")
    print(f"EXIT_CODE: {exitstatus}")
    print("=" * 60)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Format test results for clear LLM parsing."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        if report.failed:
            print(f"\n{'='*60}")
            print(f"FAILED: {item.nodeid}")
            print(f"{'='*60}")
            if report.longrepr:
                print(str(report.longrepr))
