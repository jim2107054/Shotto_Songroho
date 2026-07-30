"""
Export a static mirror of the corpus and integrity metadata.
"""

import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.chain.service import latest_proof, verify_stored_chain  # noqa: E402
from app.corpus.loader import load_seed_data  # noqa: E402

OUT_DIR = PROJECT_ROOT / "static_mirror"


def page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{html.escape(title)} - Shotto Songroho Mirror</title>
  <style>
    body {{ margin: 0; font-family: Nunito, Segoe UI, sans-serif; background: #F9FAFB; color: #212B36; }}
    header {{ background: #092C4C; color: #fff; padding: 24px; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
    a {{ color: #0D6EFD; }}
    .card {{ background: #fff; border: 1px solid #E6EAED; border-radius: 8px; padding: 20px; margin: 16px 0; }}
    .badge {{ display: inline-block; padding: 4px 8px; border-radius: 12px; background: #FE9F43; color: #fff; font-size: 12px; font-weight: 700; }}
    code {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <header><h1>Shotto Songroho Static Mirror</h1><p>Tamper-evident corpus snapshot.</p></header>
  <main>{body}</main>
</body>
</html>
"""


def render_index(entries, chain) -> str:
    body = f"""
    <div class=\"card\">
      <h2>Snapshot</h2>
      <p><strong>Corpus entries:</strong> {len(entries)}</p>
      <p><strong>Chain valid:</strong> {chain['valid']}</p>
      <p><strong>Chain hash:</strong> <code>{chain['chain_hash']}</code></p>
      <p><a href=\"corpus.html\">Browse corpus</a> | <a href=\"integrity.json\">Download integrity JSON</a></p>
    </div>
    """
    return page("Snapshot", body)


def render_corpus(entries) -> str:
    cards = []
    for entry in entries:
        sources = entry.get("sources", [])
        source_links = "".join(
            f"<li><a href='{html.escape(source.get('url', '#'))}'>{html.escape(source.get('org') or source.get('url') or 'Source')}</a></li>"
            for source in sources
            if isinstance(source, dict)
        )
        cards.append(f"""
        <article class=\"card\">
          <span class=\"badge\">{html.escape(entry.get('verdict_label', ''))}</span>
          <h2>{html.escape(entry.get('event_date') or '')} - {html.escape(entry.get('location') or '')}</h2>
          <p>{html.escape(entry.get('description_en') or '')}</p>
          <p><strong>Entry hash:</strong> <code>{html.escape(entry.get('entry_hash') or '')}</code></p>
          <ul>{source_links}</ul>
        </article>
        """)
    return page("Corpus", "\n".join(cards))


def main() -> int:
    entries = load_seed_data()
    chain = verify_stored_chain()
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    (OUT_DIR / "index.html").write_text(render_index(entries, chain), encoding="utf-8")
    (OUT_DIR / "corpus.html").write_text(render_corpus(entries), encoding="utf-8")
    (OUT_DIR / "corpus.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "integrity.json").write_text(json.dumps(chain, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

    proof = latest_proof()
    if proof:
        proofs_dir = OUT_DIR / "proofs"
        proofs_dir.mkdir()
        shutil.copy2(proof, proofs_dir / proof.name)

    print(f"Static mirror exported to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
