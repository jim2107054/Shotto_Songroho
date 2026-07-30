"""
Corpus source normalization and verdict-label guardrails.
"""

from typing import Any, Dict, List

Source = Dict[str, str]


def normalize_sources(entry: Dict[str, Any]) -> List[Source]:
    """Return v2 sources[] from either new or legacy corpus entries."""
    raw_sources = entry.get("sources") or []
    sources: List[Source] = []

    for source in raw_sources:
        if not isinstance(source, dict):
            continue
        sources.append({
            "url": str(source.get("url") or ""),
            "org": str(source.get("org") or source.get("source_org") or ""),
            "excerpt": str(source.get("excerpt") or ""),
        })

    if not sources and (entry.get("source_url") or entry.get("source_org")):
        sources.append({
            "url": str(entry.get("source_url") or ""),
            "org": str(entry.get("source_org") or ""),
            "excerpt": str(entry.get("description_en") or entry.get("description_bn") or ""),
        })

    return sources


def independent_source_count(sources: List[Source]) -> int:
    """Count independent sources by organization, falling back to URL host."""
    keys = set()
    for source in sources:
        org = (source.get("org") or "").strip().lower()
        url = (source.get("url") or "").strip().lower()
        key = org or url
        if key:
            keys.add(key)
    return len(keys)


def enforce_verdict_label(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the v2 rule: verified requires at least two independent sources."""
    normalized = dict(entry)
    sources = normalize_sources(normalized)
    normalized["sources"] = sources

    if normalized.get("verdict_label") == "verified" and independent_source_count(sources) < 2:
        normalized["verdict_label"] = "disputed"

    normalized.pop("source_url", None)
    normalized.pop("source_org", None)
    return normalized


def source_title(source: Source) -> str:
    return source.get("org") or source.get("url") or "Source"
