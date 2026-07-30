"""
Shotto Songroho — Agent 3b: Image Reuse Checker
Detects reused/miscaptioned images by comparing perceptual hashes
against a database of known reused images.
"""

import io
import base64
import logging
from typing import Optional

from app.schemas.models import ImageCheckResult
from app.services.vector_store import get_image_hashes

logger = logging.getLogger(__name__)


def _compute_phash(image_bytes: bytes) -> Optional[str]:
    """Compute perceptual hash of an image."""
    try:
        import imagehash
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        phash = imagehash.phash(img)
        return str(phash)
    except ImportError:
        logger.error("imagehash or Pillow not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to compute image hash: {e}")
        return None


def _hash_distance(hash1: str, hash2: str) -> int:
    """
    Compute hamming distance between two hex hash strings.
    Lower distance = more similar.
    """
    try:
        import imagehash
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        return h1 - h2
    except Exception:
        # Manual hamming distance for hex strings
        if len(hash1) != len(hash2):
            return 999
        distance = 0
        for c1, c2 in zip(hash1, hash2):
            b1 = int(c1, 16)
            b2 = int(c2, 16)
            xor = b1 ^ b2
            distance += bin(xor).count('1')
        return distance


async def check_image_reuse(image_base64: str) -> ImageCheckResult:
    """
    Check if an uploaded image matches any known reused/miscaptioned images.
    
    Process:
    1. Decode base64 image
    2. Compute perceptual hash
    3. Compare against known reused image hash database
    4. If match found (hamming distance < threshold), flag as reused
    """
    try:
        # Decode the image
        # Remove data URL prefix if present
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        image_bytes = base64.b64decode(image_base64)

        # Compute perceptual hash
        phash = _compute_phash(image_bytes)
        if not phash:
            logger.warning("Could not compute image hash")
            return ImageCheckResult(matched=False)

        logger.info(f"Computed image pHash: {phash}")

        # Compare against known reused images
        known_hashes = get_image_hashes()
        best_match = None
        best_distance = float('inf')

        for known in known_hashes:
            known_phash = known.get("phash", "")
            if not known_phash:
                continue

            distance = _hash_distance(phash, known_phash)

            if distance < best_distance:
                best_distance = distance
                best_match = known

        # Threshold: hamming distance < 10 is a strong match
        MATCH_THRESHOLD = 10

        if best_match and best_distance < MATCH_THRESHOLD:
            logger.info(f"Image reuse detected! Distance: {best_distance}, Source: {best_match['original_source']}")
            return ImageCheckResult(
                matched=True,
                original_source=best_match.get("original_source"),
                original_date=best_match.get("original_date"),
                original_context=best_match.get("original_context"),
                hash_distance=best_distance,
            )
        else:
            logger.info(f"No image reuse detected (best distance: {best_distance})")
            return ImageCheckResult(
                matched=False,
                hash_distance=best_distance if best_distance != float('inf') else None,
            )

    except Exception as e:
        logger.error(f"Image reuse check failed: {e}")
        return ImageCheckResult(matched=False)
