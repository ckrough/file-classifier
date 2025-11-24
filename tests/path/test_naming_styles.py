import os
import importlib
import pytest

from src.path.builder import build_path, PathMetadata
from src.config import settings


@pytest.mark.unit
def test_descriptive_nara_is_default(monkeypatch):
    # Ensure style is descriptive_nara for this test (guard against prior mutations)
    monkeypatch.setattr(settings, "NAMING_STYLE", "descriptive_nara", raising=False)
    result = build_path(
        domain="financial",
        category="banking",
        doctype="statement",
        vendor_name="chase",
        subject="checking",
        date="20250131",
        file_extension=".pdf",
        version=None,
    )
    assert isinstance(result, PathMetadata)
    # Folders Title Case with pluralized doctype
    assert result.directory_path == "Financial/Banking/Statements/"
    # Filename per descriptive NARA: doctype_vendor_subject_date.ext
    assert result.filename == "statement_chase_checking_20250131.pdf"


@pytest.mark.unit
def test_descriptive_nara_with_version(monkeypatch):
    monkeypatch.setattr(settings, "NAMING_STYLE", "descriptive_nara", raising=False)
    res = build_path(
        domain="legal",
        category="agreements",
        doctype="contract",
        vendor_name="acme_corp",
        subject="msa",
        date="20241001",
        file_extension=".pdf",
        version="v02",
    )
    assert res.directory_path == "Legal/Agreements/Contracts/"
    assert res.filename == "contract_acme_corp_msa_20241001_v02.pdf"


@pytest.mark.unit
def test_compact_gpo_when_selected(monkeypatch):
    # Switch to compact_gpo explicitly
    monkeypatch.setattr(settings, "NAMING_STYLE", "compact_gpo", raising=False)
    res = build_path(
        domain="insurance",
        category="health",
        doctype="policy",
        vendor_name="bcbs",
        subject="premium",  # ignored in compact_gpo filename
        date="20250401",
        file_extension=".pdf",
    )
    assert res.directory_path == "Insurance/Health/Policies/"
    assert res.filename == "bcbs_20250401.pdf"
