"""
Shotto Songroho - Vector Store Service
Numpy-based vector store for corpus embedding, retrieval, and search.
Uses sentence-transformers for multilingual embeddings and numpy cosine similarity.
"""

import logging
import numpy as np
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.corpus.loader import load_seed_data, load_image_hashes, prepare_documents_for_embedding

logger = logging.getLogger(__name__)

# Module-level state
_model: Optional[SentenceTransformer] = None
_embeddings: Optional[np.ndarray] = None
_documents: List[str] = []
_metadatas: List[Dict[str, Any]] = []
_doc_ids: List[str] = []
_corpus_entries: List[Dict[str, Any]] = []
_image_hashes: List[Dict[str, Any]] = []


def initialize_vector_store():
    """Initialize the embedding model and load corpus."""
    global _model, _embeddings, _documents, _metadatas, _doc_ids, _corpus_entries, _image_hashes

    logger.info("Initializing vector store...")

    # Load the multilingual embedding model
    logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
    _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    logger.info("Embedding model loaded successfully")

    # Load corpus data
    _corpus_entries = load_seed_data()
    _image_hashes = load_image_hashes()

    # Prepare documents
    docs = prepare_documents_for_embedding(_corpus_entries)
    _doc_ids = docs["ids"]
    _documents = docs["documents"]
    _metadatas = docs["metadatas"]

    if _documents:
        # Generate embeddings for all documents
        logger.info(f"Generating embeddings for {len(_documents)} documents...")
        _embeddings = _model.encode(_documents, show_progress_bar=True, convert_to_numpy=True)
        # Normalize for cosine similarity
        norms = np.linalg.norm(_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # avoid division by zero
        _embeddings = _embeddings / norms
        logger.info(f"Embeddings shape: {_embeddings.shape}")
    else:
        _embeddings = np.array([])
        logger.warning("No documents to embed")

    logger.info(f"Vector store initialized with {len(_documents)} documents from {len(_corpus_entries)} corpus entries")


def search_corpus(
    query: str,
    n_results: int = 10,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    location: Optional[str] = None,
    verdict_label: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search the corpus using cosine similarity.
    Returns list of matched entries with relevance scores.
    """
    if _model is None or _embeddings is None or len(_embeddings) == 0:
        logger.error("Vector store not initialized")
        return []

    # Encode query
    query_embedding = _model.encode([query], convert_to_numpy=True)
    query_norm = np.linalg.norm(query_embedding)
    if query_norm > 0:
        query_embedding = query_embedding / query_norm

    # Compute cosine similarities
    similarities = np.dot(_embeddings, query_embedding.T).flatten()

    # Get top-k indices sorted by similarity
    top_indices = np.argsort(similarities)[::-1]

    # Filter and build results
    entries = []
    seen_ids = set()

    for idx in top_indices:
        if len(entries) >= n_results:
            break

        metadata = _metadatas[idx]
        entry_id = metadata.get("entry_id", _doc_ids[idx])
        relevance_score = float(similarities[idx])

        # Skip low relevance
        if relevance_score < 0.05:
            continue

        # Apply metadata filters
        event_date = metadata.get("event_date", "")
        if date_from and event_date and event_date < date_from:
            continue
        if date_to and event_date and event_date > date_to:
            continue
        if location and location.lower() not in metadata.get("location", "").lower():
            continue
        if verdict_label and metadata.get("verdict_label", "") != verdict_label:
            continue

        # Deduplicate by entry_id (keep highest score)
        if entry_id in seen_ids:
            continue
        seen_ids.add(entry_id)

        entries.append({
            "id": entry_id,
            "description": _documents[idx],
            "description_en": metadata.get("description_en", ""),
            "description_bn": metadata.get("description_bn", ""),
            "event_date": event_date,
            "location": metadata.get("location", ""),
            "verdict_label": metadata.get("verdict_label", ""),
            "sources": metadata.get("sources", []),
            "relevance_score": round(relevance_score, 4),
            "lang": metadata.get("lang", "en"),
        })

    return entries


def get_all_corpus_entries(
    query: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    location: Optional[str] = None,
    verdict_label: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Get corpus entries with optional text search and filters.
    If query is provided, uses vector search. Otherwise returns filtered entries directly.
    """
    if query:
        return search_corpus(
            query=query,
            n_results=limit,
            date_from=date_from,
            date_to=date_to,
            location=location,
            verdict_label=verdict_label,
        )

    # No query - return filtered raw entries
    results = []
    for entry in _corpus_entries:
        if date_from and entry.get("event_date", "") < date_from:
            continue
        if date_to and entry.get("event_date", "") > date_to:
            continue
        if location and location.lower() not in entry.get("location", "").lower():
            continue
        if verdict_label and entry.get("verdict_label", "") != verdict_label:
            continue

        results.append(entry)
        if len(results) >= limit:
            break

    return results


def get_corpus_count() -> int:
    """Get the total number of corpus entries."""
    return len(_corpus_entries)


def get_image_hashes() -> List[Dict[str, Any]]:
    """Get all known reused image hashes."""
    return _image_hashes


