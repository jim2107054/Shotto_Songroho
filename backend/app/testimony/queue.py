"""
Moderated testimony queue storage.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

QUEUE_PATH = Path(__file__).parent / "queue.jsonl"


def enqueue_testimony(text: str, contact_optional: str | None, lang: str) -> Dict[str, Any]:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    item = {
        "id": str(uuid.uuid4()),
        "text": text,
        "contact_optional": contact_optional or "",
        "lang": lang,
        "status": "queued_for_review",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(QUEUE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return {"status": "queued_for_review", "id": item["id"]}
