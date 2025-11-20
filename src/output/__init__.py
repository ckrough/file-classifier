"""
Output formatting module for Unix-style structured output.

This module provides formatters for outputting classification results
in various formats (JSON, CSV, TSV) suitable for Unix pipelines.
"""

from src.output.models import ClassificationResult, ClassificationMetadata
from src.output.formatter import OutputFormatter

__all__ = ["ClassificationResult", "ClassificationMetadata", "OutputFormatter"]
