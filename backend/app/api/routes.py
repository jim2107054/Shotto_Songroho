"""
Shotto Songroho — API Routes
FastAPI router with verify, corpus, and health endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.models import (
    VerifyRequest,
    VerifyResponse,
    CorpusSearchResponse,
    CorpusEntryResponse,
    HealthResponse,
    SourceCitation,
)
from app.agents.pipeline import run_verification_pipeline
from app.services.vector_store import get_all_corpus_entries, get_corpus_count

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.post("/verify", response_model=VerifyResponse)
async def verify_claim(request: VerifyRequest):
    """
    Verify a claim about the July Revolution.
    
    Accepts text, image (base64), or URL input.
    Returns a verdict with confidence, cited sources, and pipeline transparency.
    """
    # Validate that at least some input is provided
    if not request.text and not request.image_base64 and not request.url:
        raise HTTPException(
            status_code=400,
            detail="At least one of text, image, or URL must be provided.",
        )

    logger.info(f"Verify request: text={bool(request.text)}, image={bool(request.image_base64)}, url={bool(request.url)}, lang={request.lang}")

    try:
        result = await run_verification_pipeline(request)
        return result
    except Exception as e:
        logger.error(f"Verification pipeline error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}",
        )


@router.get("/corpus", response_model=CorpusSearchResponse)
async def search_corpus(
    query: Optional[str] = Query(None, description="Search text"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    location: Optional[str] = Query(None, description="Location filter"),
    verdict_label: Optional[str] = Query(None, description="Filter by verdict: verified or false_claim"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
):
    """
    Search and browse the curated corpus of verified July Revolution events.
    Supports text search (vector similarity) and metadata filters.
    """
    try:
        entries = get_all_corpus_entries(
            query=query,
            date_from=date_from,
            date_to=date_to,
            location=location,
            verdict_label=verdict_label,
            limit=limit,
        )

        results = []
        for entry in entries:
            results.append(CorpusEntryResponse(
                id=entry.get("id", ""),
                event_date=entry.get("event_date"),
                location=entry.get("location"),
                description_bn=entry.get("description_bn", ""),
                description_en=entry.get("description_en", ""),
                verdict_label=entry.get("verdict_label", ""),
                sources=[
                    SourceCitation(
                        title=source.get("org") or source.get("url") or "Source",
                        url=source.get("url"),
                        excerpt=source.get("excerpt", ""),
                        source_org=source.get("org"),
                    )
                    for source in entry.get("sources", [])
                    if isinstance(source, dict)
                ],
                entities=entry.get("entities", []),
                related_image_hashes=entry.get("related_image_hashes", []),
            ))

        return CorpusSearchResponse(
            results=results,
            total=len(results),
        )
    except Exception as e:
        logger.error(f"Corpus search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Corpus search failed: {str(e)}",
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        corpus_size=get_corpus_count(),
        version="1.0.0",
    )
