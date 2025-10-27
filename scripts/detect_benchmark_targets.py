#!/usr/bin/env python3
"""
Detect which benchmark tests should run based on staged git changes.

Uses naming convention: src/analysis/analyzer.py → test_bench_analyzer
Returns pytest -k filter pattern to match benchmark tests by convention.
"""

import subprocess
import sys
from pathlib import Path


def get_staged_files() -> list[str]:
    """
    Get list of staged Python files from git.

    Returns:
        list[str]: List of staged file paths.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip().endswith(".py")
        ]
        return files
    except subprocess.CalledProcessError as e:
        print(f"Error getting staged files: {e}", file=sys.stderr)
        return []


def extract_benchmark_patterns(changed_files: list[str]) -> set[str]:
    """
    Extract benchmark test patterns from changed source files.

    Uses naming convention: src/analysis/analyzer.py → bench_analyzer

    Args:
        changed_files (list[str]): List of changed source file paths.

    Returns:
        set[str]: Set of pytest -k patterns to match benchmark tests.
    """
    patterns = set()

    for changed_file in changed_files:
        if not changed_file.startswith("src/"):
            continue

        # Extract module name from file path
        # src/analysis/analyzer.py -> analyzer
        file_path = Path(changed_file)
        module_name = file_path.stem  # filename without extension

        # Skip __init__ files
        if module_name == "__init__":
            continue

        # Create pytest -k pattern: bench_<module>
        # This matches test_bench_analyzer, test_bench_filename, etc.
        pattern = f"bench_{module_name}"
        patterns.add(pattern)

    return patterns


def main() -> None:
    """Main entry point for benchmark target detection."""
    # Get staged files
    changed_files = get_staged_files()

    if not changed_files:
        print("", end="")  # No output if no files changed
        return

    # Filter for files in src/
    src_files = [f for f in changed_files if f.startswith("src/")]

    if not src_files:
        print("", end="")  # No output if no src files changed
        return

    # Extract benchmark patterns using naming convention
    patterns = extract_benchmark_patterns(src_files)

    if not patterns:
        print("", end="")  # No patterns if only __init__ files changed
        return

    # Output pytest -k compatible pattern string
    # Multiple patterns joined with "or": bench_analyzer or bench_filename
    print(" or ".join(sorted(patterns)))


if __name__ == "__main__":
    main()
