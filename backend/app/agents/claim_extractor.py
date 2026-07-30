"""
Shotto Songroho — Agent 1: Claim Extraction
Extracts structured claim data from raw text input using LLM.
"""

import json
import logging
import re
from typing import Optional

import google.generativeai as genai

from app.config import settings
from app.schemas.models import ExtractedClaim

logger = logging.getLogger(__name__)


EXTRACTION_PROMPT = """You are a claim extraction agent for fact-checking claims related to the July 2024 Bangladesh Revolution (also known as the July Revolution, quota reform movement, or গণঅভ্যুত্থান).

Your job is to extract structured information from the user's input. The input may be in Bangla or English.

Extract the following fields:
- event: A concise description of what is being claimed
- date: The date of the claimed event (YYYY-MM-DD format if possible, or approximate)
- location: Where the event allegedly occurred
- entities: List of people, organizations, or institutions mentioned
- claim_type: "factual" (text claim), "image" (image-based), or "mixed"
- original_text: The original input text
- language_detected: "bn" for Bangla, "en" for English

If a field cannot be determined, use null or empty.

Respond ONLY with a valid JSON object, no markdown formatting, no extra text.

User input: {input_text}
"""


async def extract_claim(text: str, has_image: bool = False) -> ExtractedClaim:
    """
    Extract structured claim from raw text input.
    Uses Gemini to parse and structure the claim.
    """
    try:
        if not settings.GEMINI_API_KEY:
            logger.warning("No Gemini API key configured, using basic extraction")
            return _basic_extraction(text, has_image)

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = EXTRACTION_PROMPT.format(input_text=text)

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=1000,
            ),
        )

        # Parse JSON response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)

        data = json.loads(response_text)

        claim = ExtractedClaim(
            event=data.get("event", text[:200]),
            date=data.get("date"),
            location=data.get("location"),
            entities=data.get("entities", []),
            claim_type="mixed" if has_image else data.get("claim_type", "factual"),
            original_text=text,
            language_detected=data.get("language_detected", _detect_language(text)),
        )

        logger.info(f"Extracted claim: event='{claim.event[:80]}...', date={claim.date}, location={claim.location}")
        return claim

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return _basic_extraction(text, has_image)
    except Exception as e:
        logger.error(f"Claim extraction failed: {e}")
        return _basic_extraction(text, has_image)


def _basic_extraction(text: str, has_image: bool = False) -> ExtractedClaim:
    """Fallback extraction without LLM — basic heuristic parsing."""
    return ExtractedClaim(
        event=text[:500],
        date=_extract_date(text),
        location=_extract_location(text),
        entities=[],
        claim_type="mixed" if has_image else "factual",
        original_text=text,
        language_detected=_detect_language(text),
    )


def _detect_language(text: str) -> str:
    """Simple language detection based on character ranges."""
    bangla_chars = sum(1 for c in text if '\u0980' <= c <= '\u09FF')
    total_alpha = sum(1 for c in text if c.isalpha())
    if total_alpha == 0:
        return "en"
    return "bn" if bangla_chars / total_alpha > 0.3 else "en"


def _extract_date(text: str) -> Optional[str]:
    """Try to extract a date from text using regex."""
    # YYYY-MM-DD
    match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if match:
        return match.group(1)
    # Month DD, YYYY
    match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', text, re.IGNORECASE)
    if match:
        months = {"january": "01", "february": "02", "march": "03", "april": "04",
                  "may": "05", "june": "06", "july": "07", "august": "08",
                  "september": "09", "october": "10", "november": "11", "december": "12"}
        m = months[match.group(1).lower()]
        d = match.group(2).zfill(2)
        y = match.group(3)
        return f"{y}-{m}-{d}"
    return None


def _extract_location(text: str) -> Optional[str]:
    """Try to extract a location from text using known place names."""
    locations = [
        "Dhaka", "Chittagong", "Rajshahi", "Khulna", "Sylhet", "Rangpur",
        "Barisal", "Comilla", "Narayanganj", "Gazipur", "Mirpur", "Uttara",
        "Dhanmondi", "Gulshan", "Banani", "Mohammadpur", "Savar", "Jatrabari",
        "Shahbag", "Farmgate", "BUET", "Dhaka University", "Ashulia",
        "ঢাকা", "চট্টগ্রাম", "রাজশাহী", "খুলনা", "সিলেট", "রংপুর",
        "মিরপুর", "উত্তরা", "ধানমন্ডি", "শাহবাগ", "মোহাম্মদপুর",
    ]
    for loc in locations:
        if loc.lower() in text.lower():
            return loc
    return None
