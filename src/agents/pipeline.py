"""
Multi-Agent Pipeline Orchestrator.

Coordinates the 4-agent workflow for document processing:
1. Document Input
2. [Classification Agent] → Raw metadata
3. [Standards Agent] → Normalized metadata
4. [Path Construction Agent] → Assembled path + filename
5. [Conflict Resolution Agent] → Final resolved path (if conflicts exist)
6. Output: Complete path + filename
"""

import logging
import os
import time
from typing import Optional

from src.ai.client import AIClient
from src.agents.classification import classify_document
from src.agents.standards import standardize_metadata
from src.agents.path_construction import construct_path
from src.agents.conflict_resolution import resolve_conflicts
from src.analysis.models import (
    RawMetadata,
    NormalizedMetadata,
    PathMetadata,
    ResolvedMetadata,
)

__all__ = ["process_document_multi_agent"]

logger = logging.getLogger(__name__)


def process_document_multi_agent(
    content: str,
    filename: str,
    ai_client: AIClient,
) -> tuple[RawMetadata, NormalizedMetadata, ResolvedMetadata]:
    """
    Process a document through the multi-agent pipeline.

    This orchestrator coordinates the 4-agent workflow:
    1. Classification Agent extracts raw semantic metadata
    2. Standards Enforcement Agent applies naming conventions
    3. Path Construction Agent assembles directory path and filename
    4. Conflict Resolution Agent handles edge cases (if needed)

    Args:
        content (str): Extracted text content of the document.
        filename (str): Original filename (for context).
        ai_client (AIClient): The AI client to use for all agents.

    Returns:
        tuple[RawMetadata, NormalizedMetadata, ResolvedMetadata]:
            Returns all metadata from the pipeline for downstream use.

    Raises:
        RuntimeError: If any agent in the pipeline fails.
    """
    pipeline_start = time.perf_counter()

    try:
        logger.info("Starting multi-agent pipeline for: %s", filename)
        logger.debug("Document content length: %d characters", len(content))

        # Step 1: Classification Agent
        logger.info("Step 1/4: Classification Agent analyzing document...")
        step_start = time.perf_counter()
        raw_metadata: RawMetadata = classify_document(content, filename, ai_client)
        step_elapsed = time.perf_counter() - step_start

        logger.info(
            "  → Classification complete (%.2fs): %s/%s/%s",
            step_elapsed,
            raw_metadata.domain,
            raw_metadata.category,
            raw_metadata.doctype,
        )
        logger.debug(
            "  → Vendor: %s, Date: %s", raw_metadata.vendor_raw, raw_metadata.date_raw
        )

        # Step 2: Standards Enforcement Agent
        logger.info("Step 2/4: Standards Enforcement Agent normalizing metadata...")
        step_start = time.perf_counter()
        normalized: NormalizedMetadata = standardize_metadata(raw_metadata, ai_client)
        step_elapsed = time.perf_counter() - step_start

        logger.info(
            "  → Standardization complete (%.2fs): vendor=%s, date=%s, subject=%s",
            step_elapsed,
            normalized.vendor_name,
            normalized.date,
            normalized.subject,
        )

        # Step 3: Path Construction Agent
        logger.info("Step 3/4: Path Construction Agent building path...")
        step_start = time.perf_counter()
        file_extension = os.path.splitext(filename)[1]
        path_metadata: PathMetadata = construct_path(
            normalized, ai_client, file_extension
        )
        step_elapsed = time.perf_counter() - step_start

        logger.info(
            "  → Path constructed (%.2fs): %s",
            step_elapsed,
            path_metadata.full_path,
        )

        # Step 4: Conflict Resolution Agent (check for conflicts)
        logger.info("Step 4/4: Conflict Resolution Agent checking for conflicts...")
        step_start = time.perf_counter()
        conflict_flags: Optional[list[str]] = _detect_conflicts(
            raw_metadata, normalized
        )

        if conflict_flags:
            logger.info("  → Conflicts detected: %s", ", ".join(conflict_flags))
        else:
            logger.debug("  → No conflicts detected")

        resolved: ResolvedMetadata = resolve_conflicts(
            path_metadata, raw_metadata, ai_client, conflict_flags
        )
        step_elapsed = time.perf_counter() - step_start

        logger.info("  → Resolution complete (%.2fs)", step_elapsed)

        if resolved.alternative_paths:
            logger.info(
                "  → Alternative paths: %s", ", ".join(resolved.alternative_paths)
            )
        if resolved.resolution_notes and conflict_flags:
            logger.info("  → Notes: %s", resolved.resolution_notes)

        pipeline_elapsed = time.perf_counter() - pipeline_start
        logger.info(
            "Pipeline complete for %s (%.2fs): %s",
            filename,
            pipeline_elapsed,
            resolved.final_path,
        )

        return raw_metadata, normalized, resolved

    except Exception as e:
        pipeline_elapsed = time.perf_counter() - pipeline_start
        logger.error(
            "Multi-agent pipeline failed for %s after %.2fs: %s",
            filename,
            pipeline_elapsed,
            type(e).__name__,
            exc_info=True,
        )
        error_msg = (
            f"Document processing pipeline failed for {filename}\n"
            f"  → Check that the document contains readable text\n"
            f"  → Verify AI provider is configured correctly\n"
            f"  → See logs for detailed error information"
        )
        raise RuntimeError(error_msg) from e


def _detect_conflicts(
    raw: RawMetadata, normalized: NormalizedMetadata
) -> Optional[list[str]]:
    """
    Detect potential conflicts in the processed metadata.

    This helper function flags scenarios that may require conflict
    resolution, such as:
    - Multiple dates with ambiguous selection
    - Unknown or informal vendors
    - Multi-purpose documents (e.g., medical receipt + tax deduction)

    Args:
        raw (RawMetadata): Raw metadata from Classification Agent.
        normalized (NormalizedMetadata): Normalized metadata from Standards Agent.

    Returns:
        Optional[list[str]]: List of conflict flags, or None if no conflicts.
    """
    conflicts = []

    # Check for unknown vendor (generic or informal)
    if normalized.vendor_name in ["unknown", "informal", "generic"]:
        conflicts.append("unknown_vendor")

    # Check for multi-purpose documents
    # (e.g., Medical + Tax, or Property + Insurance)
    if raw.domain in ["medical", "property"] and "receipt" in normalized.doctype:
        conflicts.append("potential_multi_purpose")

    return conflicts if conflicts else None
