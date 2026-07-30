"""
Shotto Songroho - Corpus Loader (UTF-8)
Loads seed data and image hashes into ChromaDB on startup.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from app.corpus.sources import enforce_verdict_label

logger = logging.getLogger(__name__)

CORPUS_DIR = Path(__file__).parent
SEED_DATA_PATH = CORPUS_DIR / "seed_data.json"
IMAGE_HASHES_PATH = CORPUS_DIR / "image_hashes.json"


def load_seed_data() -> List[Dict[str, Any]]:
    """Load corpus entries from seed_data.json."""
    if not SEED_DATA_PATH.exists():
        logger.warning(f"Seed data file not found: {SEED_DATA_PATH}")
        return []

    with open(SEED_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    data = [enforce_verdict_label(entry) for entry in data]

    logger.info(f"Loaded {len(data)} corpus entries from seed data")
    return data


def load_image_hashes() -> List[Dict[str, Any]]:
    """Load known reused image hashes from image_hashes.json."""
    if not IMAGE_HASHES_PATH.exists():
        logger.warning(f"Image hashes file not found: {IMAGE_HASHES_PATH}")
        return []

    with open(IMAGE_HASHES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} image hash entries")
    return data


def prepare_documents_for_embedding(entries: List[Dict[str, Any]]) -> dict:
    """
    Prepare corpus entries for ChromaDB ingestion.
    Returns dict with ids, documents, and metadatas ready for collection.add().
    
    Strategy: embed both Bangla and English descriptions as separate documents
    pointing to the same entry, maximizing multilingual retrieval.
    """
    ids = []
    documents = []
    metadatas = []

    for entry in entries:
        entry_id = entry["id"]

        # English document
        en_text = entry.get("description_en", "")
        if en_text:
            ids.append(f"{entry_id}_en")
            documents.append(en_text)
            metadatas.append({
                "entry_id": entry_id,
                "lang": "en",
                "event_date": entry.get("event_date", ""),
                "location": entry.get("location", ""),
                "verdict_label": entry.get("verdict_label", ""),
                "sources": entry.get("sources", []),
                "description_en": en_text,
                "description_bn": entry.get("description_bn", ""),
            })

        # Bangla document
        bn_text = entry.get("description_bn", "")
        if bn_text:
            ids.append(f"{entry_id}_bn")
            documents.append(bn_text)
            metadatas.append({
                "entry_id": entry_id,
                "lang": "bn",
                "event_date": entry.get("event_date", ""),
                "location": entry.get("location", ""),
                "verdict_label": entry.get("verdict_label", ""),
                "sources": entry.get("sources", []),
                "description_en": entry.get("description_en", ""),
                "description_bn": bn_text,
            })

    logger.info(f"Prepared {len(ids)} documents for embedding ({len(entries)} entries x 2 languages)")
    return {
        "ids": ids,
        "documents": documents,
        "metadatas": metadatas,
    }



