"""
Shotto Songroho — Agent 2: Evidence Retrieval
Searches the corpus vector store for relevant evidence matching the extracted claim.
"""

import logging
from typing import List

from app.schemas.models import ExtractedClaim, RetrievedEvidence
from app.services.vector_store import search_corpus

logger = logging.getLogger(__name__)


async def retrieve_evidence(claim: ExtractedClaim, top_k: int = 8) -> List[RetrievedEvidence]:
    """
    Retrieve relevant evidence from the corpus using vector similarity search.
    
    Strategy:
    1. Search using the full event description
    2. If date/location available, also search with those as context
    3. Merge and deduplicate results
    """
    all_results = []
    seen_ids = set()

    # Primary search: use the event description
    query = claim.event
    if claim.original_text and len(claim.original_text) > len(claim.event):
        query = claim.original_text[:500]  # Use more context if available

    primary_results = search_corpus(
        query=query,
        n_results=top_k,
        date_from=None,
        date_to=None,
        location=None,
    )

    for r in primary_results:
        if r["id"] not in seen_ids:
            seen_ids.add(r["id"])
            all_results.append(r)

    # Secondary search: narrower with date/location if available
    if claim.date or claim.location:
        secondary_query = claim.event
        if claim.date:
            secondary_query += f" {claim.date}"
        if claim.location:
            secondary_query += f" {claim.location}"

        secondary_results = search_corpus(
            query=secondary_query,
            n_results=top_k // 2,
            location=claim.location if claim.location else None,
        )

        for r in secondary_results:
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                all_results.append(r)

    # Sort by relevance score
    all_results.sort(key=lambda x: x["relevance_score"], reverse=True)

    # Convert to RetrievedEvidence models
    evidence_list = []
    for r in all_results[:top_k]:
        evidence_list.append(RetrievedEvidence(
            id=r["id"],
            description=r.get("description_en", r.get("description", "")),
            event_date=r.get("event_date"),
            location=r.get("location"),
            source_url=r.get("source_url"),
            source_org=r.get("source_org"),
            verdict_label=r.get("verdict_label"),
            relevance_score=r.get("relevance_score", 0.0),
        ))

    logger.info(f"Retrieved {len(evidence_list)} evidence entries for claim: '{claim.event[:60]}...'")

    # Log top match
    if evidence_list:
        top = evidence_list[0]
        logger.info(f"Top match: '{top.description[:60]}...' (score: {top.relevance_score:.4f})")

    return evidence_list
