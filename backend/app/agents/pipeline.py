"""
Shotto Songroho — Pipeline Orchestrator
Runs the multi-agent pipeline sequentially with error handling and step tracking.
"""

import time
import logging
from typing import Optional

from app.schemas.models import (
    VerifyRequest,
    VerifyResponse,
    ExtractedClaim,
    ImageCheckResult,
    PipelineStep,
    SourceCitation,
    ChainReceipt,
)
from app.agents.claim_extractor import extract_claim
from app.agents.evidence_retriever import retrieve_evidence
from app.agents.cross_verifier import cross_verify
from app.agents.image_checker import check_image_reuse
from app.agents.verdict_agent import produce_verdict
from app.chain.service import compute_entry_hash, next_chain_hash, verify_stored_chain

logger = logging.getLogger(__name__)


async def run_verification_pipeline(request: VerifyRequest) -> VerifyResponse:
    """
    Run the full multi-agent verification pipeline.
    
    Pipeline:
    1. Claim Extraction Agent — parse input into structured claim
    2. Evidence Retrieval Agent — vector search for relevant evidence
    3a. Cross-Verification Agent — compare claim vs evidence
    3b. Image Reuse Agent — check for known reused images (if image present)
    4. Verdict Agent — synthesize everything into final verdict
    
    Each step is tracked for transparency. Failures degrade gracefully.
    """
    steps = []
    claim = None
    image_check_result = None

    # Determine input text
    input_text = request.text or ""
    if request.url and not input_text:
        input_text = f"Social media post: {request.url}"
    if not input_text and request.image_base64:
        input_text = "Image submitted for verification"

    if not input_text:
        return VerifyResponse(
            verdict="unverifiable",
            confidence=0.0,
            summary="No input provided. Please submit a text claim, image, or URL.",
            sources=[],
            pipeline_steps=[],
        )

    # ─── Step 1: Claim Extraction ─────────────────────────────────
    t0 = time.time()
    try:
        has_image = bool(request.image_base64)
        claim = await extract_claim(input_text, has_image=has_image)
        duration = int((time.time() - t0) * 1000)
        steps.append(PipelineStep(
            agent="Claim Extraction",
            status="completed",
            summary=f"Extracted: {claim.event[:100]}",
            duration_ms=duration,
        ))
        logger.info(f"Step 1 complete ({duration}ms): Claim extracted")
    except Exception as e:
        duration = int((time.time() - t0) * 1000)
        logger.error(f"Step 1 failed: {e}")
        steps.append(PipelineStep(
            agent="Claim Extraction",
            status="failed",
            summary=f"Failed: {str(e)[:100]}",
            duration_ms=duration,
        ))
        # Create a basic claim to continue
        claim = ExtractedClaim(
            event=input_text[:500],
            original_text=input_text,
        )

    # ─── Step 2: Evidence Retrieval ───────────────────────────────
    t0 = time.time()
    evidence = []
    try:
        evidence = await retrieve_evidence(claim)
        duration = int((time.time() - t0) * 1000)
        steps.append(PipelineStep(
            agent="Evidence Retrieval",
            status="completed",
            summary=f"Found {len(evidence)} relevant entries (top score: {evidence[0].relevance_score:.2f})" if evidence else "No relevant evidence found",
            duration_ms=duration,
        ))
        logger.info(f"Step 2 complete ({duration}ms): {len(evidence)} evidence entries")
    except Exception as e:
        duration = int((time.time() - t0) * 1000)
        logger.error(f"Step 2 failed: {e}")
        steps.append(PipelineStep(
            agent="Evidence Retrieval",
            status="failed",
            summary=f"Failed: {str(e)[:100]}",
            duration_ms=duration,
        ))

    # ─── Step 3a: Cross-Verification ─────────────────────────────
    t0 = time.time()
    try:
        cv_result = await cross_verify(claim, evidence)
        duration = int((time.time() - t0) * 1000)
        steps.append(PipelineStep(
            agent="Cross-Verification",
            status="completed",
            summary=f"Assessment: {cv_result.assessment} — {cv_result.reasoning[:100]}",
            duration_ms=duration,
        ))
        logger.info(f"Step 3a complete ({duration}ms): {cv_result.assessment}")
    except Exception as e:
        duration = int((time.time() - t0) * 1000)
        logger.error(f"Step 3a failed: {e}")
        steps.append(PipelineStep(
            agent="Cross-Verification",
            status="failed",
            summary=f"Failed: {str(e)[:100]}",
            duration_ms=duration,
        ))
        from app.schemas.models import CrossVerificationResult
        cv_result = CrossVerificationResult(
            assessment="insufficient",
            reasoning="Cross-verification could not be completed.",
        )

    # ─── Step 3b: Image Reuse Check ──────────────────────────────
    if request.image_base64:
        t0 = time.time()
        try:
            image_check_result = await check_image_reuse(request.image_base64)
            duration = int((time.time() - t0) * 1000)
            if image_check_result.matched:
                summary = f"⚠️ REUSE DETECTED: {image_check_result.original_source} ({image_check_result.original_date})"
            else:
                summary = "No reuse detected in known image database"
            steps.append(PipelineStep(
                agent="Image Reuse Check",
                status="completed",
                summary=summary,
                duration_ms=duration,
            ))
            logger.info(f"Step 3b complete ({duration}ms): matched={image_check_result.matched}")
        except Exception as e:
            duration = int((time.time() - t0) * 1000)
            logger.error(f"Step 3b failed: {e}")
            steps.append(PipelineStep(
                agent="Image Reuse Check",
                status="failed",
                summary=f"Failed: {str(e)[:100]}",
                duration_ms=duration,
            ))
    else:
        steps.append(PipelineStep(
            agent="Image Reuse Check",
            status="skipped",
            summary="No image submitted",
        ))

    # ─── Step 4: Verdict ──────────────────────────────────────────
    t0 = time.time()
    try:
        verdict_data = await produce_verdict(
            claim=claim,
            evidence=evidence,
            cross_verification=cv_result,
            image_check=image_check_result,
            output_lang=request.lang,
        )
        duration = int((time.time() - t0) * 1000)
        steps.append(PipelineStep(
            agent="Verdict Generation",
            status="completed",
            summary=f"Verdict: {verdict_data['verdict'].upper()} (confidence: {verdict_data['confidence']:.0%})",
            duration_ms=duration,
        ))
        logger.info(f"Step 4 complete ({duration}ms): {verdict_data['verdict']}")
    except Exception as e:
        duration = int((time.time() - t0) * 1000)
        logger.error(f"Step 4 failed: {e}")
        steps.append(PipelineStep(
            agent="Verdict Generation",
            status="failed",
            summary=f"Failed: {str(e)[:100]}",
            duration_ms=duration,
        ))
        verdict_data = {
            "verdict": "unverifiable",
            "confidence": 0.0,
            "summary": "An error occurred during verification. Please try again.",
            "sources": [],
        }

    chain_receipt = None
    try:
        stored_chain = verify_stored_chain()
        verdict_bundle = {
            "type": "generated_verdict",
            "claim": claim.model_dump() if claim else {},
            "verdict": verdict_data.get("verdict"),
            "confidence": verdict_data.get("confidence"),
            "summary": verdict_data.get("summary", ""),
            "sources": [source.model_dump() for source in verdict_data.get("sources", [])],
            "image_match": image_check_result.model_dump() if image_check_result else None,
        }
        entry_hash = compute_entry_hash(verdict_bundle)
        prev_chain_hash = stored_chain.get("chain_hash", "")
        chain_hash = next_chain_hash(prev_chain_hash, entry_hash)
        chain_receipt = ChainReceipt(
            entry_hash=entry_hash,
            prev_chain_hash=prev_chain_hash,
            chain_hash=chain_hash,
            ots_proof_ref=stored_chain.get("latest_ots_proof", {}).get("proof_path"),
        )
        steps.append(PipelineStep(
            agent="Archival Notarization",
            status="completed",
            summary=f"Verdict bundle hashed into chain receipt {entry_hash[:12]}...",
        ))
    except Exception as e:
        logger.error(f"Archival receipt failed: {e}")
        steps.append(PipelineStep(
            agent="Archival Notarization",
            status="failed",
            summary="Could not create chain receipt for this verdict.",
        ))

    # Build Response
    return VerifyResponse(
        verdict=verdict_data["verdict"],
        confidence=verdict_data["confidence"],
        summary=verdict_data["summary"],
        sources=verdict_data["sources"],
        image_match=image_check_result,
        pipeline_steps=steps,
        claim_extracted=claim,
        chain_receipt=chain_receipt,
    )


