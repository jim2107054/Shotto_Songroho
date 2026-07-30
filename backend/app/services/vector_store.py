"""
Shotto Songroho — Vector Store Service
ChromaDB wrapper for corpus embedding, retrieval, and search.
"""

import logging
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.utils import embedding_functions

from app.config import settings
from app.corpus.loader import load_seed_data, load_image_hashes, prepare_documents_for_embedding

logger = logging.getLogger(__name__)

# Module-level state
_client: Optional[chromadb.ClientAPI] = None
_collection: Optional[chromadb.Collection] = None
_corpus_entries: List[Dict[str, Any]] = []
_image_hashes: List[Dict[str, Any]] = []


def get_embedding_function():
    """Create the sentence-transformer embedding function for multilingual support."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=settings.EMBEDDING_MODEL,
    )


def initialize_vector_store():
    """Initialize ChromaDB and load corpus on startup."""
    global _client, _collection, _corpus_entries, _image_hashes

    logger.info("Initializing vector store...")

    # Create persistent client
    _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_PATH)

    # Create embedding function
    ef = get_embedding_function()

    # Get or create the collection
    _collection = _client.get_or_create_collection(
        name="july_revolution_corpus",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    # Load corpus
    _corpus_entries = load_seed_data()
    _image_hashes = load_image_hashes()

    # Check if corpus is already loaded
    existing_count = _collection.count()
    expected_count = len(_corpus_entries) * 2  # EN + BN per entry

    if existing_count < expected_count:
        logger.info(f"Loading corpus into ChromaDB ({existing_count} existing, {expected_count} expected)...")
        # Clear and reload
        if existing_count > 0:
            # Get all existing IDs and delete them
            existing = _collection.get()
            if existing["ids"]:
                _collection.delete(ids=existing["ids"])

        # Prepare and add documents
        docs = prepare_documents_for_embedding(_corpus_entries)
        if docs["ids"]:
            # Add in batches to avoid memory issues
            batch_size = 50
            for i in range(0, len(docs["ids"]), batch_size):
                _collection.add(
                    ids=docs["ids"][i:i + batch_size],
                    documents=docs["documents"][i:i + batch_size],
                    metadatas=docs["metadatas"][i:i + batch_size],
                )
            logger.info(f"Successfully loaded {len(docs['ids'])} documents into ChromaDB")
    else:
        logger.info(f"Corpus already loaded ({existing_count} documents)")


def search_corpus(
    query: str,
    n_results: int = 10,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    location: Optional[str] = None,
    verdict_label: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search the corpus using vector similarity with optional metadata filters.
    Returns list of matched entries with relevance scores.
    """
    if _collection is None:
        logger.error("Vector store not initialized")
        return []

    # Build where clause for metadata filtering
    where_clauses = []
    if location:
        where_clauses.append({"location": {"$contains": location}})
    if verdict_label:
        where_clauses.append({"verdict_label": verdict_label})

    where = None
    if len(where_clauses) == 1:
        where = where_clauses[0]
    elif len(where_clauses) > 1:
        where = {"$and": where_clauses}

    try:
        results = _collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )
    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}")
        # Retry without filters if filter caused the error
        try:
            results = _collection.query(
                query_texts=[query],
                n_results=n_results,
            )
        except Exception as e2:
            logger.error(f"ChromaDB query retry failed: {e2}")
            return []

    # Parse results
    entries = []
    if results and results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 1.0

            # Convert cosine distance to similarity score (0-1)
            relevance_score = max(0.0, 1.0 - distance)

            # Apply date filtering in post-processing (ChromaDB string comparison is limited)
            event_date = metadata.get("event_date", "")
            if date_from and event_date and event_date < date_from:
                continue
            if date_to and event_date and event_date > date_to:
                continue

            entries.append({
                "id": metadata.get("entry_id", doc_id),
                "description": results["documents"][0][i] if results["documents"] else "",
                "description_en": metadata.get("description_en", ""),
                "description_bn": metadata.get("description_bn", ""),
                "event_date": event_date,
                "location": metadata.get("location", ""),
                "verdict_label": metadata.get("verdict_label", ""),
                "source_url": metadata.get("source_url", ""),
                "source_org": metadata.get("source_org", ""),
                "relevance_score": round(relevance_score, 4),
                "lang": metadata.get("lang", "en"),
            })

    # Deduplicate by entry_id (keep highest scoring)
    seen = {}
    for entry in entries:
        eid = entry["id"]
        if eid not in seen or entry["relevance_score"] > seen[eid]["relevance_score"]:
            seen[eid] = entry

    return sorted(seen.values(), key=lambda x: x["relevance_score"], reverse=True)


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

    # No query — return filtered raw entries
    results = []
    for entry in _corpus_entries:
        # Apply filters
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
