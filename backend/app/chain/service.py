"""
Tamper-evident SHA-256 hash chain utilities.
"""

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.corpus.loader import SEED_DATA_PATH, load_seed_data

CHAIN_FIELDS = {"entry_hash", "prev_chain_hash", "ots_proof_ref"}
ZERO_HASH = "0" * 64
CHAIN_DIR = Path(__file__).parent
PROOFS_DIR = CHAIN_DIR / "proofs"
ANCHOR_INPUT_PATH = CHAIN_DIR / "current_chain_hash.txt"
ANCHOR_MANIFEST_PATH = CHAIN_DIR / "anchor_manifest.json"
OTS_COMPAT_PATH = CHAIN_DIR.parents[1] / "scripts" / "ots_compat.py"


def ots_command() -> str:
    path_match = shutil.which("ots")
    if path_match:
        return path_match

    try:
        import site
        candidate = Path(site.getusersitepackages()).parent / "Scripts" / "ots.exe"
        if candidate.exists():
            return str(candidate)
    except Exception:
        pass

    return "ots"


def canonical_entry(entry: Dict[str, Any]) -> str:
    payload = {key: value for key, value in entry.items() if key not in CHAIN_FIELDS}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_entry_hash(entry: Dict[str, Any]) -> str:
    return sha256_hex(canonical_entry(entry))


def next_chain_hash(prev_chain_hash: str, entry_hash: str) -> str:
    return hashlib.sha256((prev_chain_hash + entry_hash).encode("utf-8")).hexdigest()


def compute_chain(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    chain_hash = ZERO_HASH
    computed = []
    valid = True
    errors = []

    for index, entry in enumerate(entries):
        entry_hash = compute_entry_hash(entry)
        expected_prev = chain_hash
        stored_entry_hash = entry.get("entry_hash")
        stored_prev = entry.get("prev_chain_hash")

        if stored_entry_hash and stored_entry_hash != entry_hash:
            valid = False
            errors.append(f"{entry.get('id', index)} entry_hash mismatch")
        if stored_prev and stored_prev != expected_prev:
            valid = False
            errors.append(f"{entry.get('id', index)} prev_chain_hash mismatch")

        chain_hash = next_chain_hash(chain_hash, entry_hash)
        computed.append({
            "id": entry.get("id", str(index)),
            "entry_hash": entry_hash,
            "prev_chain_hash": expected_prev,
            "chain_hash": chain_hash,
        })

    return {
        "valid": valid,
        "errors": errors,
        "chain_hash": chain_hash,
        "chain_length": len(entries),
        "entries": computed,
    }


def update_corpus_chain_fields(proof_ref: Optional[str] = None) -> Dict[str, Any]:
    with open(SEED_DATA_PATH, "r", encoding="utf-8") as f:
        entries = json.load(f)

    chain_hash = ZERO_HASH
    for entry in entries:
        entry_hash = compute_entry_hash(entry)
        entry["entry_hash"] = entry_hash
        entry["prev_chain_hash"] = chain_hash
        if proof_ref is not None:
            entry["ots_proof_ref"] = proof_ref
        elif "ots_proof_ref" not in entry:
            entry["ots_proof_ref"] = None
        chain_hash = next_chain_hash(chain_hash, entry_hash)

    with open(SEED_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return {"chain_hash": chain_hash, "chain_length": len(entries)}


def latest_proof() -> Optional[Path]:
    if not PROOFS_DIR.exists():
        return None
    proofs = sorted(PROOFS_DIR.glob("*.ots"), key=lambda path: path.stat().st_mtime, reverse=True)
    return proofs[0] if proofs else None


def load_anchor_manifest() -> Dict[str, Any]:
    if not ANCHOR_MANIFEST_PATH.exists():
        return {}
    with open(ANCHOR_MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def proof_status(proof_path: Optional[Path] = None, check_remote: bool = False) -> Dict[str, Any]:
    proof_path = proof_path or latest_proof()
    if not proof_path:
        return {"status": "missing", "proof_path": None, "detail": "No proof file found."}

    manifest = load_anchor_manifest()
    if not check_remote:
        manifest_status = manifest.get("status", "proof_file_present")
        status = "pending" if manifest_status == "stamped" else manifest_status
        return {
            "status": status,
            "proof_path": str(proof_path),
            "detail": manifest.get("detail", "OpenTimestamps proof file exists; remote confirmation check not run."),
        }

    status = "proof_file_present"
    detail = "OpenTimestamps proof file exists; run ots verify to check confirmation."
    try:
        result = subprocess.run(
            ([sys.executable, str(OTS_COMPAT_PATH), "verify", "-f", str(ANCHOR_INPUT_PATH), str(proof_path)] if OTS_COMPAT_PATH.exists() else [ots_command(), "verify", "-f", str(ANCHOR_INPUT_PATH), str(proof_path)]),
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        output = (result.stdout + result.stderr).strip()
        detail = output[-1000:] if output else detail
        if result.returncode == 0:
            status = "verified"
        elif "Pending" in output or "pending" in output or "No connection" in output or "refused" in output:
            status = "pending"
        else:
            status = "unverified"
    except FileNotFoundError:
        status = "client_missing"
    except Exception as exc:
        status = "check_failed"
        detail = str(exc)

    return {"status": status, "proof_path": str(proof_path), "detail": detail}


def verify_stored_chain() -> Dict[str, Any]:
    entries = load_seed_data()
    result = compute_chain(entries)
    manifest = load_anchor_manifest()
    result["latest_ots_proof"] = proof_status()
    result["anchor_manifest"] = manifest
    return result


def write_anchor_input(chain_hash: str) -> Path:
    CHAIN_DIR.mkdir(parents=True, exist_ok=True)
    ANCHOR_INPUT_PATH.write_text(chain_hash + "\n", encoding="utf-8")
    return ANCHOR_INPUT_PATH


def save_anchor_manifest(chain_hash: str, proof_path: Optional[Path], status: str, detail: str = "") -> Dict[str, Any]:
    manifest = {
        "chain_hash": chain_hash,
        "anchored_at": datetime.now(timezone.utc).isoformat(),
        "proof_path": str(proof_path) if proof_path else None,
        "status": status,
        "detail": detail,
    }
    ANCHOR_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
