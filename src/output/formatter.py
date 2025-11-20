"""
Output formatting for Unix-style structured output.

Provides formatters for JSON, CSV, and TSV output formats suitable
for Unix pipelines and composability with standard tools.
"""

import csv
import json
import sys
from io import StringIO
from typing import Literal

from src.output.models import ClassificationResult

OutputFormat = Literal["json", "csv", "tsv"]


class OutputFormatter:
    """
    Formatter for classification results in various output formats.

    Supports JSON (newline-delimited), CSV, and TSV formats optimized
    for Unix tool composition and pipeline processing.
    """

    def __init__(self, format_type: OutputFormat = "json"):
        """
        Initialize formatter with specified format type.

        Args:
            format_type: Output format - 'json', 'csv', or 'tsv'
        """
        self.format_type = format_type

    def format_single(self, result: ClassificationResult) -> str:
        """
        Format a single classification result.

        Args:
            result: Classification result to format

        Returns:
            Formatted string for the result
        """
        if self.format_type == "json":
            return self.to_json(result)
        if self.format_type == "csv":
            return self.to_csv([result], include_header=False)
        if self.format_type == "tsv":
            return self.to_tsv([result], include_header=False)
        raise ValueError(f"Unsupported format: {self.format_type}")

    def format_batch(
        self, results: list[ClassificationResult], include_header: bool = True
    ) -> str:
        """
        Format multiple classification results.

        Args:
            results: List of classification results to format
            include_header: Include CSV/TSV header (ignored for JSON)

        Returns:
            Formatted string for all results
        """
        if self.format_type == "json":
            return self.to_json_batch(results)
        if self.format_type == "csv":
            return self.to_csv(results, include_header=include_header)
        if self.format_type == "tsv":
            return self.to_tsv(results, include_header=include_header)
        raise ValueError(f"Unsupported format: {self.format_type}")

    def to_json(self, result: ClassificationResult) -> str:
        """
        Convert single result to JSON.

        Args:
            result: Classification result

        Returns:
            JSON string (newline-terminated)
        """
        return json.dumps(result.model_dump(), ensure_ascii=False)

    def to_json_batch(self, results: list[ClassificationResult]) -> str:
        """
        Convert multiple results to newline-delimited JSON.

        Args:
            results: List of classification results

        Returns:
            Newline-delimited JSON string
        """
        return "\n".join(self.to_json(r) for r in results)

    def to_csv(
        self, results: list[ClassificationResult], include_header: bool = True
    ) -> str:
        """
        Convert results to CSV format.

        Args:
            results: List of classification results
            include_header: Include header row

        Returns:
            CSV-formatted string
        """
        if not results:
            return ""

        output = StringIO()
        fieldnames = [
            "original",
            "suggested_path",
            "suggested_name",
            "full_path",
            "domain",
            "category",
            "vendor",
            "date",
            "doctype",
            "subject",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)

        if include_header:
            writer.writeheader()

        for result in results:
            row = {
                "original": result.original,
                "suggested_path": result.suggested_path,
                "suggested_name": result.suggested_name,
                "full_path": result.full_path,
                "domain": result.metadata.domain,
                "category": result.metadata.category,
                "vendor": result.metadata.vendor,
                "date": result.metadata.date,
                "doctype": result.metadata.doctype,
                "subject": result.metadata.subject,
            }
            writer.writerow(row)

        return output.getvalue().rstrip("\r\n")

    def to_tsv(
        self, results: list[ClassificationResult], include_header: bool = True
    ) -> str:
        """
        Convert results to TSV format.

        Args:
            results: List of classification results
            include_header: Include header row

        Returns:
            TSV-formatted string
        """
        if not results:
            return ""

        output = StringIO()
        fieldnames = [
            "original",
            "suggested_path",
            "suggested_name",
            "full_path",
            "domain",
            "category",
            "vendor",
            "date",
            "doctype",
            "subject",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter="\t")

        if include_header:
            writer.writeheader()

        for result in results:
            row = {
                "original": result.original,
                "suggested_path": result.suggested_path,
                "suggested_name": result.suggested_name,
                "full_path": result.full_path,
                "domain": result.metadata.domain,
                "category": result.metadata.category,
                "vendor": result.metadata.vendor,
                "date": result.metadata.date,
                "doctype": result.metadata.doctype,
                "subject": result.metadata.subject,
            }
            writer.writerow(row)

        return output.getvalue().rstrip("\r\n")

    def write_result(self, result: ClassificationResult, file=None) -> None:
        """
        Write a single result to file (or stdout if None).

        Args:
            result: Classification result to write
            file: File object to write to (defaults to stdout)
        """
        if file is None:
            file = sys.stdout

        output = self.format_single(result)
        print(output, file=file)

    def write_batch(
        self,
        results: list[ClassificationResult],
        file=None,
        include_header: bool = True,
    ) -> None:
        """
        Write multiple results to file (or stdout if None).

        Args:
            results: List of classification results to write
            file: File object to write to (defaults to stdout)
            include_header: Include CSV/TSV header (ignored for JSON)
        """
        if file is None:
            file = sys.stdout

        if self.format_type == "json":
            # Write each JSON object on its own line for streaming
            for result in results:
                print(self.to_json(result), file=file)
        else:
            output = self.format_batch(results, include_header=include_header)
            print(output, file=file)
