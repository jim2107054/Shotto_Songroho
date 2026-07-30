"""
Shotto Songroho — Agent 4: Verdict Agent
Synthesizes all pipeline inputs to produce a final verdict with confidence and citations.
"""

import json
import logging
import re
from typing import List, Optional

import google.generativeai as genai

from app.config import settings
from app.schemas.models import (
    ExtractedClaim,
    RetrievedEvidence,
    CrossVerificationResult,
    ImageCheckResult,
    SourceCitation,
)

logger = logging.getLogger(__name__)


VERDICT_PROMPT = """You are the Verdict Agent for Shotto Songroho (শত্য সংগ্রহ), a fact-checking system for claims about the July 2024 Bangladesh Revolution.

You must produce a final verdict based on all the evidence and analysis below.

CRITICAL RULES:
1. NEVER say "Verified" or "False" if there is no supporting evidence — default to "Unverifiable"
2. A verdict with zero evidence MUST be "unverifiable"
3. If evidence contradicts the claim AND matches a known false claim, verdict is "false"
4. If evidence partially supports with some contradictions, verdict is "disputed"
5. Always cite specific sources — never give a black-box verdict

CLAIM:
{claim_text}

EVIDENCE RETRIEVED ({evidence_count} entries):
{evidence_text}

CROSS-VERIFICATION RESULT:
- Assessment: {cv_assessment}
- Reasoning: {cv_reasoning}
- Matches: {cv_matches}
- Contradictions: {cv_contradictions}

IMAGE CHECK: {image_check_text}

OUTPUT LANGUAGE: {output_lang}

Respond with a valid JSON object (no markdown formatting):
{{
  "verdict": "verified" | "disputed" | "unverifiable" | "false",
  "confidence": 0.0 to 1.0,
  "summary": "A clear, {output_lang_full} explanation of the verdict for a general audience. 2-3 sentences.",
  "sources": [
    {{
      "title": "Source title",
      "url": "source URL if available",
      "excerpt": "Relevant excerpt from the source",
      "source_org": "Organization name"
    }}
  ]
}}
"""


async def produce_verdict(
    claim: ExtractedClaim,
    evidence: List[RetrievedEvidence],
    cross_verification: CrossVerificationResult,
    image_check: Optional[ImageCheckResult],
    output_lang: str = "en",
) -> dict:
    """
    Produce the final verdict by synthesizing all pipeline inputs.
    Returns dict with verdict, confidence, summary, and sources.
    """
    # Enforce the rule: no evidence = unverifiable
    if not evidence:
        return _no_evidence_verdict(claim, output_lang)

    try:
        if not settings.GEMINI_API_KEY:
            logger.warning("No Gemini API key — using heuristic verdict")
            return _heuristic_verdict(claim, evidence, cross_verification, image_check, output_lang)

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Format evidence
        evidence_text = ""
        for i, e in enumerate(evidence[:6], 1):
            evidence_text += f"\n[{i}] {e.description}"
            evidence_text += f"\n    Date: {e.event_date}, Location: {e.location}"
            evidence_text += f"\n    Source: {e.source_org} ({e.source_url})"
            evidence_text += f"\n    Corpus Verdict: {e.verdict_label}"
            evidence_text += f"\n    Relevance: {e.relevance_score:.2f}\n"

        # Image check text
        image_check_text = "No image submitted"
        if image_check:
            if image_check.matched:
                image_check_text = (
                    f"⚠️ IMAGE REUSE DETECTED: This image matches a known reused image. "
                    f"Original source: {image_check.original_source} ({image_check.original_date}). "
                    f"Context: {image_check.original_context}"
                )
            else:
                image_check_text = "Image submitted but no reuse detected in known database."

        output_lang_full = "Bangla (বাংলা)" if output_lang == "bn" else "English"

        prompt = VERDICT_PROMPT.format(
            claim_text=claim.original_text[:500],
            evidence_count=len(evidence),
            evidence_text=evidence_text,
            cv_assessment=cross_verification.assessment,
            cv_reasoning=cross_verification.reasoning,
            cv_matches=", ".join(cross_verification.key_matches[:3]) or "None",
            cv_contradictions=", ".join(cross_verification.key_contradictions[:3]) or "None",
            image_check_text=image_check_text,
            output_lang=output_lang,
            output_lang_full=output_lang_full,
        )

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=2000,
            ),
        )

        response_text = response.text.strip()
        if response_text.startswith("```"):
            response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)

        data = json.loads(response_text)

        # Build sources
        sources = []
        for s in data.get("sources", []):
            sources.append(SourceCitation(
                title=s.get("title", ""),
                url=s.get("url"),
                excerpt=s.get("excerpt", ""),
                source_org=s.get("source_org"),
            ))

        # If no sources from LLM, use evidence sources
        if not sources:
            for e in evidence[:3]:
                sources.append(SourceCitation(
                    title=e.description[:100],
                    url=e.source_url,
                    excerpt=e.description,
                    source_org=e.source_org,
                ))

        verdict = data.get("verdict", "unverifiable")
        confidence = min(1.0, max(0.0, float(data.get("confidence", 0.5))))

        # Safety check: if verdict is verified/false but confidence is very low, downgrade
        if verdict in ("verified", "false") and confidence < 0.3:
            verdict = "disputed"

        # Safety check: if image reuse detected, cannot be "verified"
        if image_check and image_check.matched and verdict == "verified":
            verdict = "false"
            confidence = max(confidence, 0.8)

        result = {
            "verdict": verdict,
            "confidence": round(confidence, 2),
            "summary": data.get("summary", ""),
            "sources": sources,
        }

        logger.info(f"Verdict: {result['verdict']} (confidence: {result['confidence']})")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse verdict response: {e}")
        return _heuristic_verdict(claim, evidence, cross_verification, image_check, output_lang)
    except Exception as e:
        logger.error(f"Verdict generation failed: {e}")
        return _heuristic_verdict(claim, evidence, cross_verification, image_check, output_lang)


def _no_evidence_verdict(claim: ExtractedClaim, output_lang: str) -> dict:
    """Return an unverifiable verdict when no evidence is found."""
    if output_lang == "bn":
        summary = "এই দাবি যাচাই করার জন্য আমাদের তথ্যভান্ডারে পর্যাপ্ত প্রমাণ পাওয়া যায়নি। এটি সত্য বা মিথ্যা কোনোটিই নিশ্চিত করা সম্ভব নয়।"
    else:
        summary = "Insufficient evidence found in our corpus to verify this claim. We cannot confirm or deny its accuracy."

    return {
        "verdict": "unverifiable",
        "confidence": 0.0,
        "summary": summary,
        "sources": [],
    }


def _heuristic_verdict(
    claim: ExtractedClaim,
    evidence: List[RetrievedEvidence],
    cv: CrossVerificationResult,
    image_check: Optional[ImageCheckResult],
    output_lang: str,
) -> dict:
    """Fallback heuristic verdict without LLM."""
    sources = []
    for e in evidence[:3]:
        sources.append(SourceCitation(
            title=e.description[:100],
            url=e.source_url,
            excerpt=e.description,
            source_org=e.source_org,
        ))

    # Image reuse = false
    if image_check and image_check.matched:
        return {
            "verdict": "false",
            "confidence": 0.85,
            "summary": f"This image has been identified as a reused image. Original source: {image_check.original_source} ({image_check.original_date}).",
            "sources": sources,
        }

    # Map cross-verification to verdict
    verdict_map = {
        "supports": ("verified", 0.75),
        "contradicts": ("false", 0.7),
        "partially_supports": ("disputed", 0.5),
        "insufficient": ("unverifiable", 0.3),
    }

    verdict, confidence = verdict_map.get(cv.assessment, ("unverifiable", 0.3))

    # Adjust confidence based on evidence relevance
    if evidence:
        top_score = evidence[0].relevance_score
        confidence = min(1.0, confidence * (0.5 + top_score * 0.5))

    summary = cv.reasoning if cv.reasoning else "Based on available evidence in the corpus."

    return {
        "verdict": verdict,
        "confidence": round(confidence, 2),
        "summary": summary,
        "sources": sources,
    }
