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
) -> ResolvedMetadata:
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
        ResolvedMetadata: Final resolved metadata with complete path.

    Raises:
        RuntimeError: If any agent in the pipeline fails.
    """
    try:
        logger.info("Starting multi-agent pipeline for: %s", filename)

        # Step 1: Classification Agent
        logger.debug("Step 1: Invoking Classification Agent")
        raw_metadata: RawMetadata = classify_document(content, filename, ai_client)
        logger.info(
            "Classification: domain=%s, category=%s, doctype=%s",
            raw_metadata.domain,
            raw_metadata.category,
            raw_metadata.doctype,
        )

        # Step 2: Standards Enforcement Agent
        logger.debug("Step 2: Invoking Standards Enforcement Agent")
        normalized: NormalizedMetadata = standardize_metadata(raw_metadata, ai_client)
        logger.info(
            "Standardized: vendor=%s, date=%s, subject=%s",
            normalized.vendor_name,
            normalized.date,
            normalized.subject,
        )

        # Step 3: Path Construction Agent
        logger.debug("Step 3: Invoking Path Construction Agent")
        file_extension = os.path.splitext(filename)[1]
        path_metadata: PathMetadata = construct_path(
            normalized, ai_client, file_extension
        )
        logger.info(
            "Path constructed: %s",
            path_metadata.full_path,
        )

        # Step 4: Conflict Resolution Agent (check for conflicts)
        logger.debug("Step 4: Invoking Conflict Resolution Agent")
        conflict_flags: Optional[list[str]] = _detect_conflicts(
            raw_metadata, normalized
        )

        resolved: ResolvedMetadata = resolve_conflicts(
            path_metadata, raw_metadata, ai_client, conflict_flags
        )

        logger.info(
            "Pipeline complete: final_path=%s",
            resolved.final_path,
        )

        return resolved

    except Exception as e:
        logger.error(
            "Multi-agent pipeline failed for %s: %s",
            filename,
            e,
            exc_info=True,
        )
        raise RuntimeError("Multi-agent pipeline failed") from e


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
    if raw.domain in ["Medical", "Property"] and "receipt" in normalized.doctype:
        conflicts.append("potential_multi_purpose")

    return conflicts if conflicts else None
