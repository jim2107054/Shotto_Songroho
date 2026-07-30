"""
Shotto Songroho — API Routes
FastAPI router with verify, corpus, and health endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse

from app.schemas.models import (
    VerifyRequest,
    ShareCardRequest,
    TestimonyRequest,
    TestimonyResponse,
    VerifyResponse,
    CorpusSearchResponse,
    CorpusEntryResponse,
    HealthResponse,
    SourceCitation,
    ChainVerifyResponse,
    ChainProofStatus,
    AccountabilityIncident,
    AccountabilityIndexEntry,
    AccountabilityIndexResponse,
)
from app.agents.pipeline import run_verification_pipeline
from app.services.vector_store import get_all_corpus_entries, get_corpus_count
from app.services.share_card import render_verdict_card
from app.testimony.queue import enqueue_testimony
from app.chain.service import latest_proof, verify_stored_chain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

HUMAN_RIGHTS_ORGS = ("amnesty", "odhikar", "ain o salish", "ask", "human rights")


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


@router.post("/testimony", response_model=TestimonyResponse)
async def submit_testimony(request: TestimonyRequest):
    """Store civic testimony in a moderation queue; never auto-publish."""
    result = enqueue_testimony(
        text=request.text,
        contact_optional=request.contact_optional,
        lang=request.lang,
    )
    return TestimonyResponse(**result)


@router.post("/share-card")
async def share_card(request: ShareCardRequest):
    """Generate a shareable verdict PNG with a QR code to the first cited source."""
    png = render_verdict_card(
        verdict=request.verdict,
        confidence=request.confidence,
        summary=request.summary,
        sources=request.sources,
    )
    return Response(content=png, media_type="image/png")


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
                entry_hash=entry.get("entry_hash"),
                prev_chain_hash=entry.get("prev_chain_hash"),
                ots_proof_ref=entry.get("ots_proof_ref"),
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


@router.get("/accountability-index", response_model=AccountabilityIndexResponse)
async def accountability_index(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    location: Optional[str] = Query(None, description="Location filter"),
):
    """Aggregate documented incidents by existing org/unit-level corpus entities."""
    entries = get_all_corpus_entries(
        date_from=date_from,
        date_to=date_to,
        location=location,
        limit=200,
    )
    grouped = {}
    for entry in entries:
        sources = entry.get("sources", [])
        source_blob = " ".join(str(source.get("org", "")) for source in sources if isinstance(source, dict)).lower()
        if not any(org in source_blob for org in HUMAN_RIGHTS_ORGS):
            continue

        citations = [
            SourceCitation(
                title=source.get("org") or source.get("url") or "Source",
                url=source.get("url"),
                excerpt=source.get("excerpt", ""),
                source_org=source.get("org"),
            )
            for source in sources
            if isinstance(source, dict)
        ]
        for entity in entry.get("entities", []):
            if not entity or not isinstance(entity, str):
                continue
            grouped.setdefault(entity, []).append(AccountabilityIncident(
                id=entry.get("id", ""),
                date=entry.get("event_date"),
                location=entry.get("location"),
                description=entry.get("description_en", ""),
                sources=citations,
            ))

    results = [
        AccountabilityIndexEntry(entity=entity, incidents=incidents)
        for entity, incidents in sorted(grouped.items())
    ]
    return AccountabilityIndexResponse(results=results, total_entities=len(results))


@router.get("/chain/verify", response_model=ChainVerifyResponse)
async def verify_chain():
    """Recompute the stored corpus hash chain and report latest OTS proof status."""
    result = verify_stored_chain()
    proof = result.get("latest_ots_proof", {})
    return ChainVerifyResponse(
        valid=result.get("valid", False),
        chain_length=result.get("chain_length", 0),
        chain_hash=result.get("chain_hash", ""),
        errors=result.get("errors", []),
        latest_ots_proof=ChainProofStatus(
            status=proof.get("status", "missing"),
            proof_path=proof.get("proof_path"),
            detail=proof.get("detail", ""),
        ),
    )


@router.get("/chain/proof/latest")
async def latest_chain_proof():
    """Download the latest OpenTimestamps proof file."""
    proof = latest_proof()
    if not proof:
        raise HTTPException(status_code=404, detail="No OpenTimestamps proof found.")
    return FileResponse(path=proof, filename=proof.name, media_type="application/octet-stream")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        corpus_size=get_corpus_count(),
        version="1.0.0",
    )
