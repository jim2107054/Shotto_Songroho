"""
Shotto Songroho — Agent 3a: Cross-Verification
Compares the extracted claim against retrieved evidence to determine
whether evidence supports, contradicts, or is insufficient.
"""

import json
import logging
import re

import google.generativeai as genai

from app.config import settings
from app.schemas.models import ExtractedClaim, RetrievedEvidence, CrossVerificationResult
from typing import List

logger = logging.getLogger(__name__)


CROSS_VERIFY_PROMPT = """You are a cross-verification agent for fact-checking claims about the July 2024 Bangladesh Revolution.

You are given:
1. A CLAIM that someone is making
2. A set of EVIDENCE entries from a curated, verified corpus

Your job is to determine whether the evidence SUPPORTS, CONTRADICTS, PARTIALLY SUPPORTS, or is INSUFFICIENT to verify the claim.

CLAIM:
- Event: {event}
- Date: {date}
- Location: {location}
- Full text: {original_text}

EVIDENCE:
{evidence_text}

Analyze carefully:
- Does the evidence confirm the specific details (date, location, numbers, actors)?
- Are there contradictions between the claim and evidence?
- Is the evidence relevant but insufficient to fully verify/deny?
- If the claim includes exaggerated numbers or manipulated details, flag that.

Respond with a valid JSON object (no markdown):
{{
  "assessment": "supports" | "contradicts" | "insufficient" | "partially_supports",
  "reasoning": "Detailed explanation of your assessment",
  "key_matches": ["List of specific facts that match between claim and evidence"],
  "key_contradictions": ["List of specific contradictions or exaggerations found"]
}}
"""


async def cross_verify(
    claim: ExtractedClaim,
    evidence: List[RetrievedEvidence],
) -> CrossVerificationResult:
    """
    Cross-verify the claim against retrieved evidence using LLM analysis.
    """
    if not evidence:
        logger.info("No evidence available — returning insufficient")
        return CrossVerificationResult(
            assessment="insufficient",
            reasoning="No relevant evidence was found in the corpus to verify or deny this claim.",
            key_matches=[],
            key_contradictions=[],
        )

    try:
        if not settings.GEMINI_API_KEY:
            logger.warning("No Gemini API key — using heuristic cross-verification")
            return _heuristic_cross_verify(claim, evidence)

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Format evidence for the prompt
        evidence_text = ""
        for i, e in enumerate(evidence[:6], 1):  # Limit to top 6 for prompt length
            evidence_text += f"\n[{i}] (Relevance: {e.relevance_score:.2f})\n"
            evidence_text += f"  Date: {e.event_date or 'unknown'}\n"
            evidence_text += f"  Location: {e.location or 'unknown'}\n"
            source_orgs = ", ".join(s.source_org or s.title for s in e.sources) or "unknown"
            evidence_text += f"  Sources: {source_orgs}\n"
            evidence_text += f"  Verdict: {e.verdict_label or 'unknown'}\n"
            evidence_text += f"  Description: {e.description}\n"

        prompt = CROSS_VERIFY_PROMPT.format(
            event=claim.event,
            date=claim.date or "not specified",
            location=claim.location or "not specified",
            original_text=claim.original_text[:500],
            evidence_text=evidence_text,
        )

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=1500,
            ),
        )

        response_text = response.text.strip()
        if response_text.startswith("```"):
            response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)

        data = json.loads(response_text)

        result = CrossVerificationResult(
            assessment=data.get("assessment", "insufficient"),
            reasoning=data.get("reasoning", ""),
            key_matches=data.get("key_matches", []),
            key_contradictions=data.get("key_contradictions", []),
        )

        logger.info(f"Cross-verification result: {result.assessment}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse cross-verification response: {e}")
        return _heuristic_cross_verify(claim, evidence)
    except Exception as e:
        logger.error(f"Cross-verification failed: {e}")
        return _heuristic_cross_verify(claim, evidence)


def _heuristic_cross_verify(
    claim: ExtractedClaim,
    evidence: List[RetrievedEvidence],
) -> CrossVerificationResult:
    """Fallback heuristic cross-verification without LLM."""
    if not evidence:
        return CrossVerificationResult(
            assessment="insufficient",
            reasoning="No relevant evidence found.",
        )

    top_score = evidence[0].relevance_score
    has_false_claim_match = any(e.verdict_label == "false_claim" for e in evidence[:3])
    has_verified_match = any(e.verdict_label == "verified" for e in evidence[:3])

    if has_false_claim_match and top_score > 0.7:
        return CrossVerificationResult(
            assessment="contradicts",
            reasoning=f"Matched a known false claim in the corpus with high relevance ({top_score:.2f}).",
            key_contradictions=[e.description for e in evidence[:3] if e.verdict_label == "false_claim"],
        )
    elif has_verified_match and top_score > 0.7:
        return CrossVerificationResult(
            assessment="supports",
            reasoning=f"Matched verified events in the corpus with high relevance ({top_score:.2f}).",
            key_matches=[e.description for e in evidence[:3] if e.verdict_label == "verified"],
        )
    elif top_score > 0.5:
        return CrossVerificationResult(
            assessment="partially_supports",
            reasoning=f"Some relevant evidence found but not a strong match ({top_score:.2f}).",
            key_matches=[e.description for e in evidence[:2]],
        )
    else:
        return CrossVerificationResult(
            assessment="insufficient",
            reasoning=f"Evidence relevance too low ({top_score:.2f}) to make a determination.",
        )
