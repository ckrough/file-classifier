"""
Conflict Resolution Agent.

Expertise: Edge case handling and business logic decisions.
This requires judgment and context. It references the "Common Scenarios"
rules and makes final decisions when other agents flag ambiguity.
This is the "orchestrator" for complex cases.

Responsibilities:
- Multi-purpose document placement (medical receipt that's also a
  tax deduction)
- Vendor name change handling (TD_Ameritrade vs Schwab)
- Unknown vendor scenarios (garage sales, informal contractors)
- Missing metadata decisions
"""

import logging
from typing import Optional
from src.ai.client import AIClient
from src.ai.prompts import get_prompt_template
from src.analysis.models import RawMetadata, PathMetadata, ResolvedMetadata

__all__ = ["resolve_conflicts"]

logger = logging.getLogger(__name__)


def resolve_conflicts(
    path: PathMetadata,
    raw: RawMetadata,
    ai_client: AIClient,
    conflict_flags: Optional[list[str]] = None,
) -> ResolvedMetadata:
    """
    Handle edge cases and resolve ambiguous document placements.

    This agent makes final decisions for complex scenarios:
    - Documents that could belong to multiple categories
    - Vendor name changes/mergers
    - Unknown or informal vendors
    - Missing critical metadata

    If no conflicts are detected, the agent returns the path as-is.

    Args:
        path (PathMetadata): Proposed path from Path Construction Agent.
        raw (RawMetadata): Original raw metadata for context.
        ai_client (AIClient): The AI client to use for conflict resolution.
        conflict_flags (list[str], optional): Specific conflicts to resolve.

    Returns:
        ResolvedMetadata: Final resolved path with optional alternatives
                          and resolution notes.

    Raises:
        RuntimeError: If conflict resolution fails or AI client errors.
    """
    try:
        # If no conflicts flagged, accept path as-is
        if not conflict_flags:
            logger.debug(
                "Conflict Resolution Agent: No conflicts detected, "
                "accepting path: %s",
                path.full_path,
            )
            return ResolvedMetadata(
                final_path=path.full_path,
                alternative_paths=None,
                resolution_notes="No conflicts detected",
            )

        # Get the conflict resolution prompt template
        prompt_template = get_prompt_template("conflict-resolution-agent")

        # Prepare prompt values
        prompt_values = {
            "proposed_path": path.full_path,
            "domain": raw.domain,
            "category": raw.category,
            "doctype": raw.doctype,
            "vendor_raw": raw.vendor_raw,
            "conflict_flags": ", ".join(conflict_flags),
        }

        logger.debug(
            "Conflict Resolution Agent resolving conflicts: %s",
            conflict_flags,
        )

        # Invoke AI client with structured output
        resolved: ResolvedMetadata = ai_client.analyze_content(
            prompt_template=prompt_template,
            prompt_values=prompt_values,
            schema=ResolvedMetadata,
        )

        logger.debug(
            "Conflict Resolution Agent resolved path: %s (alternatives: %s)",
            resolved.final_path,
            resolved.alternative_paths,
        )

        return resolved

    except Exception as e:
        logger.error("Conflict Resolution Agent failed: %s", e, exc_info=True)
        raise RuntimeError("Conflict resolution failed") from e
