"""
Anchor the current Shotto Songroho corpus chain with OpenTimestamps.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.chain.service import (  # noqa: E402
    ANCHOR_INPUT_PATH,
    PROOFS_DIR,
    compute_chain,
    save_anchor_manifest,
    update_corpus_chain_fields,
    write_anchor_input,
    ots_command,
)
from app.corpus.loader import load_seed_data  # noqa: E402


def main() -> int:
    update_result = update_corpus_chain_fields()
    chain_hash = update_result["chain_hash"]
    input_path = write_anchor_input(chain_hash)
    PROOFS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("ots_compat.py")), "stamp", str(input_path)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except FileNotFoundError:
        save_anchor_manifest(chain_hash, None, "client_missing", "Install opentimestamps-client to create .ots proofs.")
        print("OpenTimestamps client not found. Install opentimestamps-client and rerun.", file=sys.stderr)
        return 2

    generated = Path(str(input_path) + ".ots")
    proof_path = None
    if generated.exists():
        proof_path = PROOFS_DIR / f"chain-{chain_hash[:16]}.ots"
        shutil.move(str(generated), proof_path)
        update_corpus_chain_fields(str(proof_path).replace("\\", "/"))

    status = "stamped" if result.returncode == 0 and proof_path else "stamp_failed"
    detail = (result.stdout + result.stderr).strip()
    manifest = save_anchor_manifest(chain_hash, proof_path, status, detail[-1000:])

    verification = compute_chain(load_seed_data())
    print({
        "chain_hash": chain_hash,
        "chain_length": verification["chain_length"],
        "proof_path": manifest["proof_path"],
        "status": manifest["status"],
    })
    return 0 if status == "stamped" else 1


if __name__ == "__main__":
    raise SystemExit(main())
