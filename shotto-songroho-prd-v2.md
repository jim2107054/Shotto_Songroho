# Product Requirements Document
## Shotto Songroho (সত্য সংগ্রহ) — Agentic Fact-Verification & Tamper-Evident Archive for July Revolution Claims

**Version:** 2.0
**Date:** July 30, 2026
**Track:** July Hackathon 2026 — Track B (Spirit of July)
**Team size:** 2
**Sprint duration:** 72 hours

> ### What's new in v2.0
> - Added an **Archival Notarization Agent** — hash-chained, blockchain-anchored corpus so the archive is provably tamper-evident, directly answering the track's "archives that resist deletion" pillar.
> - Added a **Documented Incidents / Accountability Index** — cited-only surfacing of human rights org documentation, directly answering the "accountability tooling" pillar.
> - Added a **civic testimony intake** (moderated) directly answering "civic participation."
> - Promoted retrieval transparency (FR8) to P1 — it's cheap and it's your best "glass box, not black box" demo moment.
> - Added a Responsible AI & Neutrality section — important given how politically live this subject still is.
> - Added a scripted demo, a track-alignment table for judges, and a priority-ranked stretch list.

---

## 1. Executive Summary

Shotto Songroho is a web application that lets any user submit a claim, image, or social post link related to the July Revolution and receive a cited, evidence-backed verdict — **Verified**, **Disputed**, **Unverifiable**, or **False** — within seconds. The verdict is produced by a multi-agent pipeline (not a single LLM call) that extracts the claim, retrieves matching evidence from a curated corpus of verified events and testimony, cross-checks for contradictions, and (when an image is provided) checks whether it's a known reused/miscaptioned image from an unrelated event.

Beyond the fact-check itself, every verdict is written into a **hash-chained, publicly anchored archive** — so the product is not just a checker but a growing, citable, tamper-evident record of the revolution that survives independent of any single server or host. It also surfaces a cited **accountability index** of documented incidents, and accepts **citizen testimony** into a moderated intake queue — making it a single product that speaks to all three stated pillars of Track B: accountability, archives that resist deletion, and civic participation.

---

## 2. Problem Statement

False and recycled media routinely circulate as "proof" of specific July Revolution events — old images from unrelated conflicts or earlier protests get recaptioned with false dates and locations. Existing Bangla fact-check efforts (Rumor Scanner, BOOM Bangladesh) are manual, slow, and don't scale to the speed at which misinformation spreads on social media. There is no fast, self-serve tool that lets an ordinary citizen or journalist check a claim in real time, with sources they can verify themselves — and no existing tool guarantees that its own findings can't quietly be edited, disputed, or deleted later by whoever happens to control the hosting.

---

## 3. Goals & Non-Goals

### Goals
- Let a user verify a text claim against a curated evidence corpus in under 10 seconds
- Let a user check whether a submitted image is a known reused/miscaptioned image
- Always show cited sources — never a black-box verdict
- Support both Bangla and English input/output
- Be usable on a low-end device / slow connection (text-first UI, small payloads)
- **Produce a tamper-evident, publicly verifiable archive of findings that persists independent of any single host**
- **Support low-friction civic reporting so citizens can contribute testimony, not just consume verdicts**

### Non-Goals (for this sprint)
- Real-time social media crawling/monitoring (out of scope — this is a lookup tool, not a bot)
- User accounts, auth, or personalization
- Training a custom ML model from scratch (use existing embedding models + prompted LLM agents)
- Video verification (image + text only for MVP)
- Full offline/PWA support (deprioritized per team decision — assume some connectivity; see §21 for a cheaper substitute)
- **Adjudicating legal guilt, individual culpability, or contested political framing** — the tool verifies *what happened, where, when*, not *who is to blame* (see §19)

---

## 4. Target Users

| Persona | Need |
|---|---|
| **Citizen fact-checker** | Sees a viral claim/image, wants a fast sanity check before sharing |
| **Journalist / researcher** | Needs cited sources to back a story, not just a yes/no answer |
| **Fact-check org (e.g., Rumor Scanner)** | Could use this as a triage tool to speed up their manual review queue |
| **Archivist / human rights documenter** | Needs a record that can't be quietly altered later, with provable timestamps |

---

## 5. User Stories

1. *As a citizen*, I paste a claim I saw on Facebook and get a verdict with links to real sources, so I know whether to share it.
2. *As a citizen*, I upload a screenshot of a viral image and find out it's actually from a 2018 protest, not July 2024, so I don't spread misinformation.
3. *As a journalist*, I search the corpus directly for a date/location to see what's independently verified, so I can cite it in my reporting.
4. *As any user*, I switch the interface to Bangla so I can read and submit claims in my first language.
5. *As any user on a slow connection*, the page loads and returns a verdict without needing to download large assets.
6. *As an archivist*, I export the corpus's hash chain and independently verify against the public blockchain anchor that no entry has been silently altered.
7. *As a citizen with firsthand knowledge*, I submit my own account of an event into a moderation queue, so it can become part of the verified record if corroborated.

---

## 6. System Architecture

```
                    ┌─────────────────────────┐
                    │   User Input             │
                    │ (claim text / image /    │
                    │  social post link)        │
                    └───────────┬──────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │ 1. Claim Extraction Agent      │
                │  → {event, date, location,     │
                │     entities, claim_type}      │
                └───────────────┬────────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │ 2. Evidence Retrieval Agent    │
                │  → vector search over curated  │
                │     corpus (Chroma/FAISS)      │
                │  → top-k relevant documents    │
                └───────────────┬────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
    ┌───────────────────────────┐  ┌──────────────────────────┐
    │ 3a. Cross-Verification    │  │ 3b. Image Reuse Agent     │
    │   Agent                   │  │  (only if image present)  │
    │  → does evidence support, │  │  → perceptual hash match  │
    │    contradict, or not     │  │    vs known-reused-image  │
    │    cover the claim?       │  │    dataset                │
    └───────────────┬───────────┘  └─────────────┬──────────────┘
                    └───────────┬───────────────┘
                                ▼
                ┌───────────────────────────────┐
                │ 4. Verdict Agent               │
                │  → Verified / Disputed /       │
                │     Unverifiable / False       │
                │  → confidence score            │
                │  → cited source list           │
                │  → intermediate reasoning trace│
                └───────────────┬────────────────┘
                                ▼
                ┌───────────────────────────────┐
                │ 5. Archival Notarization Agent  │  ◄── NEW
                │  → hash verdict + evidence      │
                │    bundle (SHA-256)             │
                │  → append to hash chain         │
                │  → periodic public anchor       │
                │    (OpenTimestamps → Bitcoin)   │
                └───────────────┬────────────────┘
                                ▼
                        Verdict UI (bilingual, glass-box trace)
```

### 6.1 The Archival Notarization Agent (new)

This is the mechanism that turns "we say we verified this" into "anyone can prove this was verified, and prove it hasn't been altered since."

**How it works (cheap, ~half a day of engineering):**
1. Every corpus entry and every generated verdict is serialized to canonical JSON and SHA-256 hashed.
2. Each new hash is chained: `chain_hash_n = SHA256(chain_hash_(n-1) + entry_hash_n)`. This is the same core idea behind Merkle chains / blockchains — a single edited byte anywhere in history breaks every hash after it, so tampering is always detectable.
3. Periodically (e.g., every few hours, and definitely once on Day 1 and once before the demo), the current `chain_hash` is submitted to **OpenTimestamps** (`opentimestamps-client`, free, no infra), which anchors the hash into the Bitcoin blockchain. This produces a `.ots` proof file that anyone, anywhere, forever, can use to prove the chain existed in that exact state at that time — independent of whether Shotto Songroho's own servers are still running.
4. The chain log + `.ots` proofs are also committed to the public GitHub repo, so there are two independent, redundant tamper-evidence layers (git history + Bitcoin anchor) without running any blockchain infrastructure yourselves.

**Demo tip:** OpenTimestamps confirmations take a few hours (Bitcoin block time). Stamp your first hash the morning of Day 1 so you have a *confirmed* proof ready to show by Day 3, and keep the raw pending `.ots` for the "as of right now" version as backup narrative.

**Why multi-agent, not a single prompt:** each stage is independently testable and debuggable, failure is localized (e.g., if retrieval finds nothing, the Verdict Agent correctly returns "Unverifiable" instead of hallucinating), and it's a stronger, more defensible architecture to present to judges than a single RAG call.

---

## 7. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR1 | User can submit a text claim via input box | P0 |
| FR2 | User can upload an image alongside or instead of text | P0 |
| FR3 | System returns a verdict (Verified/Disputed/Unverifiable/False) with confidence | P0 |
| FR4 | System displays cited sources with links/excerpts for every verdict | P0 |
| FR5 | System supports Bangla and English input, with a language toggle for output | P0 |
| FR6 | Image reuse detection flags known miscaptioned/recycled images | P1 |
| FR7 | Corpus is searchable directly (browse verified events by date/location) | P1 |
| FR8 | System shows retrieval transparency — "why" a source was matched (agent trace) | **P1** ⬆ (was P2 — cheap, and your best glass-box demo moment) |
| FR10 | Corpus is hash-chained and periodically anchored to a public, independent timestamping service | **P1 (new)** |
| FR11 | System surfaces a cited "Documented Incidents" accountability index by date/location, drawn only from named human-rights-org citations already in the corpus | **P1 (new)** |
| FR12 | User can submit a social post URL and system extracts claim text from it | P2 (stretch) |
| FR13 | User can submit personal testimony/evidence into a moderated intake queue (not auto-published) | **P2 (new, stretch)** |
| FR14 | User can generate a shareable verdict card (image + QR to sources) for social sharing | **P2 (new, stretch)** |

---

## 8. Non-Functional Requirements

- **Latency:** verdict returned in under 10 seconds for text claims
- **Bandwidth:** initial page load under 1 MB; no unnecessary image/video assets
- **Reliability:** if the LLM API fails or times out, the system degrades to "Unverifiable — try again" rather than crashing
- **Explainability:** every verdict must show at least one cited source; a verdict with zero evidence is never shown as Verified or False
- **Bilingual:** all UI copy and verdict output available in Bangla and English
- **Integrity:** the corpus's tamper-evidence chain must be independently re-verifiable from a downloaded export, without trusting Shotto Songroho's own server

---

## 9. Data / Corpus Design

The corpus is the product's core asset and its biggest execution risk — prioritize building it first.

**Sources to compile (100–200 entries target):**
- Rumor Scanner Bangladesh and BOOM Bangladesh — known false claims (seed the "False" category)
- Ain o Salish Kendra (ASK) and Odhikar human rights documentation — verified event records
- Wikipedia's July Revolution timeline — structured backbone of dates/locations/events
- AFP Fact Check / Reuters Fact Check — reused-image cases (a common pattern: old Syria/Myanmar/2018 quota-movement images recaptioned as July 2024/2025)

**Schema (per corpus entry) — updated for multi-source + chain-of-custody:**
```json
{
  "id": "string",
  "event_date": "YYYY-MM-DD",
  "location": "string",
  "description_bn": "string",
  "description_en": "string",
  "verdict_label": "verified | disputed | false_claim",
  "sources": [
    { "url": "string", "org": "string", "excerpt": "string" }
  ],
  "entities": ["org/unit-level only — see §19 for what is and isn't allowed here"],
  "related_image_hashes": ["phash1", "phash2"],
  "entry_hash": "sha256 of the canonical entry",
  "prev_chain_hash": "sha256 of the chain state before this entry",
  "ots_proof_ref": "path or id of the OpenTimestamps proof covering this entry, once anchored"
}
```

**Rule:** an entry can only be labeled `verified` if it has **≥2 independent sources** in `sources[]`. Single-sourced entries cap out at `disputed` with a note. This is a cheap rule that meaningfully raises the credibility of your "Verified" badge in front of judges and in front of skeptical users.

---

## 10. Tech Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI (Python), Docker |
| Agent orchestration | Simple sequential pipeline (plain function calls with structured LLM outputs) |
| Vector store | Chroma or FAISS |
| Embeddings | Multilingual model with strong Bangla support — prefer `intfloat/multilingual-e5-base` or `BAAI/bge-m3` over generic MiniLM variants |
| LLM | API-based (Claude or equivalent) — declared per hackathon's AI-use disclosure rule |
| Image hashing | `imagehash` (Python) for perceptual hash comparison |
| **Tamper-evidence** | **`hashlib` (SHA-256 chain) + `opentimestamps-client` for free Bitcoin-anchored timestamping** |
| **Caching** | Simple in-memory LRU (or Redis if time allows) on repeat claims — keeps you inside the 10s budget and cuts LLM cost during demo/judging |
| Shareable card generation | `Pillow` + `qrcode` (server-side PNG/OG-image generation) |
| Eval harness | small `eval.py` — runs the 20 hand-labeled test claims against the live pipeline and prints accuracy; a visible, judge-friendly proof point |
| Frontend | React, bilingual UI toggle |
| Hosting | Vercel (frontend) + Railway/Render (backend); mirror export to GitHub Pages for redundancy (see §21) |

---

## 11. API Design (draft)

```
POST /api/verify
  body: { text?: string, image?: base64, url?: string, lang: "bn"|"en" }
  returns: {
    verdict: "verified"|"disputed"|"unverifiable"|"false",
    confidence: 0-1,
    sources: [{ title, url, excerpt }],
    image_match?: { matched: bool, original_source?, original_date? },
    reasoning_trace: [{ agent, output }],   // powers FR8 glass-box view
    chain_receipt?: { entry_hash, chain_hash, ots_proof_ref }
  }

GET /api/corpus?query=&date_from=&date_to=&location=
  returns: [ corpus entries matching filters ]

GET /api/accountability-index?date_from=&date_to=&location=
  returns: [ { entity, incidents: [{ date, location, sources }] } ]   // FR11, cited-only, no generated claims

POST /api/testimony
  body: { text, contact_optional?, lang }
  returns: { status: "queued_for_review" }   // FR13, never auto-published

GET /api/chain/verify
  returns: { valid: bool, chain_length, latest_ots_proof }   // lets anyone independently re-verify integrity
```

---

## 12. UI Requirements

- **Home screen:** single input box (text/image/link), language toggle, submit button
- **Verdict screen:** large color-coded verdict badge (green/yellow/red/gray), confidence %, cited sources list with excerpts, **expandable "how this was checked" agent trace (glass-box view, FR8)**, **"Share this verdict" card button (FR14)**
- **Corpus browser (P1):** simple searchable/filterable list of verified entries
- **Accountability index view (P1, new):** filterable list of documented incidents by date/location, each line fully cited
- **Integrity page (new, cheap):** a single static page showing the current chain hash, latest OpenTimestamps proof, and a "how to verify this yourself" explainer — this is a small page but it's disproportionately persuasive to judges
- **Testimony intake form (P2, new):** short form, explicit "this will be reviewed before publication, not published automatically" copy
- Design should be readable on a low-end phone screen at minimum

---

## 13. Success Metrics (for demo/judging, not production KPIs)

- Verdict accuracy on a held-out test set of ~20 hand-labeled claims (aim for correct verdict on 80%+), measured by the `eval.py` harness
- Demo reliability: 0 crashes during the live 3-minute presentation
- Corpus size: 100+ verified entries by submission
- At least one **confirmed** OpenTimestamps proof by demo time

---

## 14. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Corpus too small/thin by deadline | Build corpus on Day 1 before writing pipeline code; cap scope at 100 entries minimum |
| LLM hallucinates a verdict with no real evidence | Verdict Agent must refuse to say Verified/False if retrieval returns 0 relevant docs — forced "Unverifiable" |
| Image reuse detection has few matches to demo | Deliberately seed 10–15 known reused-image cases into the demo dataset so the feature has something to catch |
| Bilingual support adds scope creep | Ship English-first, add Bangla output as a translation pass on top of the same pipeline, not a separate pipeline |
| Running out of time for polish | Cut P2 stretch items first (§21, ranked by ROI); core verdict flow (FR1–FR5) must work end-to-end by Day 2 evening |
| **OpenTimestamps confirmation is slow (hours)** | **Stamp the first hash Day 1 morning; have a confirmed proof ready by Day 3; show the pending proof as the "live" fallback narrative** |
| **Perceived political bias, given the subject matter** | **Strict multi-source rule for "Verified"; never generate individual-culpability claims; explicit Responsible AI section (§19) in README and pitch** |

---

## 15. Execution Timeline (72 hours, 2 people)

**Day 1**
- Person A: build and structure the corpus (JSON), embed into vector store
- Person B: scaffold FastAPI backend, agent pipeline skeleton, React frontend shell
- Evening: wire Claim Extraction → Retrieval Agent, test on 10 sample claims; **stamp the first corpus hash to OpenTimestamps so it has time to confirm**

**Day 2**
- Person A: Cross-Verification + Verdict Agent, prompt tuning, citation formatting, **accountability index endpoint**
- Person B: Image Reuse Agent (imagehash matching) + frontend polish, Bangla/English toggle, **agent trace UI (FR8)**
- Evening: integration testing, seed edge-case claims, **implement hash chain + notarization agent**

**Day 3**
- Morning: bug fixes, deploy, test on slow connection, **verify OpenTimestamps proof has confirmed; run eval.py and record the accuracy number for the pitch**
- Afternoon: record demo video (script in §20), build slide deck, finalize README/problem statement; **if time remains, pick ONE item from §21, not all of them**
- Evening: submit early

---

## 16. Judging-Criteria Alignment Checklist

- [ ] Commit history shows incremental progress from Hour 1
- [ ] Public repo with MIT/Apache 2.0 license from day 1
- [ ] README with clear setup/run instructions
- [ ] Demo video scripted around a false-claim-correctly-flagged moment
- [ ] AI-tool usage disclosed per hackathon rules
- [ ] Submitted well before the deadline, not at 23:59
- [ ] **At least one confirmed OpenTimestamps proof referenced in the README**
- [ ] **`eval.py` output (accuracy number) included in README or slide deck**

---

## 17. Post-Hackathon Roadmap (not in scope for the sprint, for context only)

- Expand corpus via partnership with Rumor Scanner / BOOM Bangladesh
- Add browser extension for inline verification on social feeds
- Add video verification support
- Community-contributed corpus entries with moderation queue (MVP version already in-scope as FR13)
- Third-party legal/human-rights review of the accountability index methodology before wider release

---

## 18. Track Alignment Mapping (why this wins)

Most Track B submissions will address *one* pillar convincingly. Judges will notice a product that maps to all three with real, working mechanisms rather than a slide bullet — lead your pitch with this table.

| Track B pillar | Shotto Songroho mechanism |
|---|---|
| **Accountability** | Documented Incidents / Accountability Index (§7 FR11) — cited-only, structured surfacing of already-public ASK/Odhikar documentation; the Verdict Agent is itself accountable to its own evidence (forced "Unverifiable" default) |
| **Archives that resist deletion** | Hash-chained corpus, periodically anchored into the Bitcoin blockchain via OpenTimestamps (§6.1); redundant git history; static mirror export (§21) |
| **Access to information** | Bilingual, sub-1MB, <10s verdicts; open `/api/corpus` and `/api/chain/verify` endpoints; downloadable corpus |
| **Civic participation** | Testimony intake with moderation queue (FR13); shareable verdict cards drive organic reach (FR14) |
| **Memory of what happened** | A permanent-by-design, growing, citable public record — not just a one-off checker |

---

## 19. Responsible AI & Neutrality Guardrails

The July Revolution remains a politically live subject. This section should go in your README verbatim — it materially reduces the risk of the tool being read as partisan, and it protects real people.

- The tool adjudicates **provenance and factual claims** ("did event X happen at location Y on date Z," "is this image really from that event") — it does **not** adjudicate legal guilt, moral culpability, or contested political framing.
- **"Verified" requires ≥2 independent named sources.** Single-sourced claims cap at "Disputed."
- The system **never generates** casualty figures, named-individual attributions, or characterizations that are not explicitly present in a cited source. The accountability index only surfaces text and citations that are *already public* in the named human rights reports — the LLM is not permitted to infer or extend beyond what's cited.
- `entities` in the corpus schema (§9) should stay at the organizational/unit level as documented by cited sources — the product should not become a vehicle for doxxing private individuals.
- Ambiguous LLM output always resolves to **"Unverifiable,"** never to "False" or "Verified" — the failure mode is always "we don't know," never a confident wrong answer.
- A visible **"Report an error / dispute this verdict"** link feeds into a public corrections log — this is a governance signal judges respond well to, and it's cheap to build (a form + a queue).

---

## 20. Demo Script (3-Minute Judge Narrative)

| Time | Beat |
|---|---|
| 0:00–0:30 | Hook: show a real example of a viral claim/recaptioned image that circulated with a false date or location |
| 0:30–1:15 | Submit it live. Walk through the glass-box agent trace as it runs. Land on "False — reused image, originally from [X]," with cited sources visible |
| 1:15–1:45 | Open the **Integrity page**: show the hash chain and the confirmed OpenTimestamps proof. Line: *"Even if our server disappeared tomorrow, this finding is provable, forever, independent of us."* |
| 1:45–2:15 | Open the **Accountability Index / corpus browser**: filter by date/location, show cited documented incidents |
| 2:15–2:45 | Flip the language toggle live to Bangla |
| 2:45–3:00 | Close on the track-alignment table (§18) and the eval.py accuracy number |

---

## 21. Stretch "Wow" Features (priority-ordered by effort vs. payoff — pick from the top, don't try all)

1. **Shareable verdict card** (FR14) — server-side PNG/OG-image with a QR code back to sources. Cheap (Pillow + qrcode), and it's the one feature that makes the *tool itself* spread civically, not just the demo.
2. **Static mirror export** — a single command that snapshots the corpus + verdicts to static HTML for GitHub Pages / IPFS pinning. Cheap, and it's a concrete, demoable answer to "what if this gets taken down" that pairs perfectly with the hash-chain narrative.
3. **"Report an error" corrections log** — small form + queue; strengthens the governance/trust story from §19 for very little engineering cost.
4. **Browser extension teaser** — even a static mockup (no working extension needed) showing inline verification on a social feed is pure demo eye-candy; only do this if the above three are already done.

---