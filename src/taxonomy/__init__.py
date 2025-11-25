"""Central taxonomy for domains, categories, and doctypes.

This module defines the canonical vocabulary for the directory hierarchy used by
this application, along with helpers to normalize raw values into that
vocabulary.

The intent is that:
- Classification and Standards Enforcement agents *aim* to emit values from
  this vocabulary.
- Code is the final gatekeeper and will canonicalize via aliases or, in strict
  mode, reject unknown values.

The initial seed is homeowner-focused, but the sets are intended to be
maintainable and extensible over time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Set, Tuple

from src.config import settings

# ---------------------------------------------------------------------------
# Canonical vocabulary (seeded with homeowner-focused taxonomy)
# ---------------------------------------------------------------------------

CANONICAL_DOMAINS: Set[str] = {
    "financial",
    "property",
    "insurance",
    "legal",
    "medical",
    "employment",
    "utilities",
    "education",
}

# Per-domain allowed categories
CANONICAL_CATEGORIES: Dict[str, Set[str]] = {
    "financial": {
        "banking",
        "credit",
        "investment",
        "retirement",
        "loans",
        "mortgage",
        "tax",
    },
    "property": {
        "real_estate",
        "vehicles",
        "major_assets",
        "household",
        "home_improvement",
    },
    "insurance": {
        "health",
        "property_casualty",
        "life_disability",
        "other",
    },
    "legal": {
        "identity",
        "estate",
        "agreements",
        "compliance",
    },
    "medical": {
        "records",
        "expenses",
        "providers",
    },
    "employment": {
        "compensation",
        "benefits",
        "employment_docs",
    },
    "utilities": {
        "energy",
        "communications",
        "water_waste",
        "security",
    },
    "education": {
        "tuition",
        "transcripts",
        "student_loans",
    },
}

CANONICAL_DOCTYPES: Set[str] = {
    "statement",
    "receipt",
    "invoice",
    "policy",
    "contract",
    "deed",
    "title",
    "return",
    "notice",
    "report",
    "certificate",
    "form",
    "letter",
    "agreement",
    "confirmation",
    "eob",
    "record",
    "warranty",
    "manual",
    "guide",
}

# ---------------------------------------------------------------------------
# Aliases (synonyms and common variants)
# ---------------------------------------------------------------------------

# Domain aliases collapse near-duplicates to canonical domain slugs.
DOMAIN_ALIASES: Dict[str, str] = {
    "finances": "financial",
    "finance": "financial",
    "real_estate": "property",  # occasionally used as a domain
    "tax": "financial",  # when emitted as a domain
}

# Category aliases are keyed by (domain, raw_category).
CATEGORY_ALIASES: Dict[Tuple[str, str], str] = {
    ("property", "home_repairs"): "home_improvement",
    ("property", "repairs"): "home_improvement",
    ("property", "remodeling"): "home_improvement",
    ("property", "renovation"): "home_improvement",
    ("property", "renovations"): "home_improvement",
    ("property", "contractors"): "home_improvement",
    ("property", "hoa_docs"): "compliance",
    ("property", "homeowners_association"): "compliance",
    ("utilities", "cable_tv"): "communications",
    ("utilities", "internet"): "communications",
    ("utilities", "phone"): "communications",
    ("financial", "checking_accounts"): "banking",
    ("financial", "savings_accounts"): "banking",
    ("financial", "credit_cards"): "credit",
    ("financial", "investment_accounts"): "investment",
    ("financial", "retirement_accounts"): "retirement",
}

# Doctype aliases collapse various phrases into canonical doctypes.
DOCTYPE_ALIASES: Dict[str, str] = {
    "bill": "invoice",
    "billing_statement": "statement",
    "billing": "invoice",
    "eob": "eob",  # already canonical but often uppercase
    "explanation_of_benefits": "eob",
    "policy_document": "policy",
    "insurance_policy": "policy",
    "user_guide": "guide",
    "owner_guide": "guide",
    "owners_manual": "manual",
    "owner_manual": "manual",
    "training_manual": "manual",
    "home_warranty_card": "warranty",
    "service_contract": "contract",
    "service_agreement": "agreement",
    "appointment_letter": "letter",
    "tax_return": "return",
}


# ---------------------------------------------------------------------------
# Optional configuration override (JSON/YAML)
# ---------------------------------------------------------------------------

@dataclass
class TaxonomyConfig:
    """Container for taxonomy data.

    This exists mainly to make it easier to load/override from external
    configuration in the future. For now we simply wrap module-level
    constants.
    """

    domains: Set[str]
    categories: Dict[str, Set[str]]
    doctypes: Set[str]


def _load_config_from_file() -> Optional[TaxonomyConfig]:
    """Optionally load taxonomy configuration from a JSON/YAML file.

    If settings.TAXONOMY_CONFIG_PATH is not set or the file cannot be loaded,
    this returns None and the built-in constants are used.

    This is intentionally conservative: failures fall back to code defaults
    rather than failing the application.
    """

    path = getattr(settings, "TAXONOMY_CONFIG_PATH", None)
    if not path:
        return None

    import json
    from pathlib import Path

    config_path = Path(path)
    if not config_path.is_file():
        return None

    try:
        text = config_path.read_text(encoding="utf-8")
        if config_path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore[import]
            except Exception:  # pragma: no cover - optional dependency
                return None
            data = yaml.safe_load(text)
        else:
            data = json.loads(text)
    except Exception:  # pragma: no cover - defensive
        return None

    domains = set(str(d).strip().lower() for d in data.get("domains", []))
    categories: Dict[str, Set[str]] = {}
    for domain, cats in data.get("categories", {}).items():
        d = str(domain).strip().lower()
        categories[d] = {str(c).strip().lower() for c in cats}
    doctypes = {str(t).strip().lower() for t in data.get("doctypes", [])}

    return TaxonomyConfig(domains=domains, categories=categories, doctypes=doctypes)


_CONFIG_OVERRIDE: Optional[TaxonomyConfig] = _load_config_from_file()


def _active_domains() -> Set[str]:
    return _CONFIG_OVERRIDE.domains if _CONFIG_OVERRIDE else CANONICAL_DOMAINS


def _active_categories() -> Dict[str, Set[str]]:
    return _CONFIG_OVERRIDE.categories if _CONFIG_OVERRIDE else CANONICAL_CATEGORIES


def _active_doctypes() -> Set[str]:
    return _CONFIG_OVERRIDE.doctypes if _CONFIG_OVERRIDE else CANONICAL_DOCTYPES


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def _normalize_token(value: str) -> str:
    """Normalize a taxonomy token for lookup.

    - Strips whitespace
    - Lowercases
    - Replaces spaces and hyphens with underscores
    """

    value = (value or "").strip().lower()
    if not value:
        return ""
    value = value.replace("-", "_").replace(" ", "_")
    return value


def canonical_domain(raw: str) -> Optional[str]:
    """Resolve a raw domain string to a canonical domain slug.

    Returns None if no suitable canonical value can be found.
    """

    token = _normalize_token(raw)
    if not token:
        return None

    domains = _active_domains()

    if token in domains:
        return token

    alias = DOMAIN_ALIASES.get(token)
    if alias and alias in domains:
        return alias

    return None


def canonical_category(domain: str, raw: str) -> Optional[str]:
    """Resolve a raw category string to a canonical category for the domain.

    Returns None if no suitable canonical value can be found.
    """

    dom = canonical_domain(domain) or _normalize_token(domain)
    if not dom:
        return None

    token = _normalize_token(raw)
    if not token:
        return None

    categories = _active_categories().get(dom, set())

    if token in categories:
        return token

    alias = CATEGORY_ALIASES.get((dom, token))
    if alias and alias in categories:
        return alias

    return None


def canonical_doctype(raw: str) -> Optional[str]:
    """Resolve a raw doctype string to a canonical doctype slug.

    Returns None if no suitable canonical value can be found.
    """

    token = _normalize_token(raw)
    if not token:
        return None

    doctypes = _active_doctypes()

    if token in doctypes:
        return token

    alias = DOCTYPE_ALIASES.get(token)
    if alias and alias in doctypes:
        return alias

    return None


__all__ = [
    "CANONICAL_DOMAINS",
    "CANONICAL_CATEGORIES",
    "CANONICAL_DOCTYPES",
    "DOMAIN_ALIASES",
    "CATEGORY_ALIASES",
    "DOCTYPE_ALIASES",
    "canonical_domain",
    "canonical_category",
    "canonical_doctype",
]
