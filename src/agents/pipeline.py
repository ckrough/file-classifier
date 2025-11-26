"""
Multi-Agent Pipeline Orchestrator.

Coordinates the 2-agent workflow for document processing:
1. Document Input
2. [Classification Agent] → Raw metadata
3. [Standards Agent] → Normalized metadata
4. [Deterministic Path Builder] → Assembled path + filename (no AI)
5. Output: Complete path + filename
"""

import logging
import os
import time

from src.ai.client import AIClient
from src.agents.classification import classify_document
from src.agents.standards import standardize_metadata
from src.path.builder import build_path, PathMetadata
from src.analysis.models import (
    RawMetadata,
    NormalizedMetadata,
)
from src.taxonomy import canonical_domain, canonical_category, canonical_doctype

__all__ = ["process_document_multi_agent"]
logger = logging.getLogger(__name__)


def _safe_lower(value: str | None) -> str:
    """Safely lowercase a string, returning empty string if None."""
    return (value or "").lower().strip()


def process_document_multi_agent(
    content: str,
    filename: str,
    ai_client: AIClient,
) -> tuple[RawMetadata, NormalizedMetadata, PathMetadata]:
    """
    Process a document through the multi-agent pipeline.

    This orchestrator coordinates the 2-agent workflow:
    1. Classification Agent extracts raw semantic metadata
    2. Standards Enforcement Agent applies naming conventions and validates vendor
    3. Deterministic path builder creates filesystem path (no AI)

    Args:
        content (str): Extracted text content of the document.
        filename (str): Original filename (for context).
        ai_client (AIClient): The AI client to use for AI agents.

    Returns:
        tuple[RawMetadata, NormalizedMetadata, PathMetadata]:
            Returns all metadata from the pipeline for downstream use.

    Raises:
        RuntimeError: If any agent in the pipeline fails.
        ValueError: If Standards Agent fails to determine vendor.
    """
    pipeline_start = time.perf_counter()

    try:
        logger.info("Starting 2-agent pipeline for: %s", filename)
        logger.debug("Document content length: %d characters", len(content))

        # Step 1: Classification Agent
        logger.info("Step 1/2: Classification Agent analyzing document: %s", filename)
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
        logger.info(
            "Step 2/2: Standards Enforcement Agent normalizing metadata: %s", filename
        )
        step_start = time.perf_counter()
        normalized: NormalizedMetadata = standardize_metadata(raw_metadata, ai_client)
        step_elapsed = time.perf_counter() - step_start

        logger.info(
            "   Standardization complete (%.2fs): vendor=%s, date=%s, subject=%s",
            step_elapsed,
            normalized.vendor_name,
            normalized.date,
            normalized.subject,
        )

        # Validate vendor before path construction
        # Standards Agent MUST determine a specific vendor
        if not normalized.vendor_name or normalized.vendor_name.lower() in [
            "unknown",
            "n/a",
            "none",
            "generic",
        ]:
            raise ValueError(
                f"Standards Agent failed to determine vendor for {filename}. "
                f"Got vendor_name: '{normalized.vendor_name}'. "
                f"Document may be unreadable, corrupted, or missing vendor information."
            )

        # Taxonomy normalization for domain/category/doctype
        # - Domain: STRICT - must exist in taxonomy (no new domains allowed)
        # - Category: FLEXIBLE - prefer existing, but allow new categories
        # - Doctype: FLEXIBLE - prefer existing, but allow new doctypes
        #
        # The classification agent attempts to match existing taxonomy values first.
        # Only when no close match exists should it create new categories/doctypes.

        raw_domain = normalized.domain
        raw_category = normalized.category
        raw_doctype = normalized.doctype

        canonical_dom = canonical_domain(raw_domain)
        if not canonical_dom:
            # Domain is the top-level partition; we do not allow
            # unknown domains to create new branches.
            raise ValueError(
                "Taxonomy validation failed: unknown domain "
                f"'{raw_domain}' for document '{filename}'"
            )

        canonical_cat = canonical_category(canonical_dom, raw_category)
        canonical_doc = canonical_doctype(raw_doctype)

        # Categories: allow new ones if not found in taxonomy
        if canonical_cat is None:
            canonical_cat = _safe_lower(raw_category)
            logger.info(
                "  → New category '%s' created under domain '%s'",
                canonical_cat,
                canonical_dom,
            )

        # Doctypes: allow new ones if not found in taxonomy
        if canonical_doc is None:
            canonical_doc = _safe_lower(raw_doctype)
            logger.info(
                "  → New doctype '%s' created",
                canonical_doc,
            )

        if (
            canonical_dom != raw_domain.lower()
            or canonical_cat != raw_category.lower()
            or canonical_doc != raw_doctype.lower()
        ):
            logger.info(
                "   Taxonomy canonicalization: %s/%s/%s  %s/%s/%s",
                raw_domain,
                raw_category,
                raw_doctype,
                canonical_dom,
                canonical_cat,
                canonical_doc,
            )

        # Deterministic path building (no AI, no API call)
        logger.info("Building filesystem path (deterministic, no AI)...")
        step_start = time.perf_counter()
        file_extension = os.path.splitext(filename)[1]

        path_metadata: PathMetadata = build_path(
            domain=canonical_dom,
            category=canonical_cat,
            doctype=canonical_doc,
            vendor_name=normalized.vendor_name,
            subject=normalized.subject,
            date=normalized.date,
            file_extension=file_extension,
            version=normalized.version,
        )
        step_elapsed = time.perf_counter() - step_start

        logger.info(
            "  → Path built (%.2fs): %s",
            step_elapsed,
            path_metadata.full_path,
        )

        pipeline_elapsed = time.perf_counter() - pipeline_start
        logger.info(
            "Pipeline complete for %s (%.2fs): %s",
            filename,
            pipeline_elapsed,
            path_metadata.full_path,
        )

        return raw_metadata, normalized, path_metadata

    except ValueError as e:
        # ValueError from vendor validation or path building
        pipeline_elapsed = time.perf_counter() - pipeline_start
        logger.error(
            "Pipeline validation failed for %s after %.2fs: %s",
            filename,
            pipeline_elapsed,
            str(e),
            exc_info=True,
        )
        raise RuntimeError(f"Document processing validation failed: {e}") from e

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
