# Product Requirements Document
## Shotto Songroho (শত্য সংগ্রহ) — Agentic Fact-Verification for July Revolution Claims

**Version:** 1.0
**Date:** July 30, 2026
**Track:** July Hackathon 2026 — Track B (Spirit of July)
**Team size:** 2
**Sprint duration:** 72 hours

---

## 1. Executive Summary

Shotto Songroho is a web application that lets any user submit a claim, image, or social post link related to the July Revolution and receive a cited, evidence-backed verdict — **Verified**, **Disputed**, **Unverifiable**, or **False** — within seconds. The verdict is produced by a multi-agent pipeline (not a single LLM call) that extracts the claim, retrieves matching evidence from a curated corpus of verified events and testimony, cross-checks for contradictions, and (when an image is provided) checks whether it's a known reused/miscaptioned image from an unrelated event.

The product doubles as a growing, citable archive of verified July Revolution events, directly serving Track B's stated need for misinformation detection, fact-checking, and source verification.

---

## 2. Problem Statement

False and recycled media routinely circulate as "proof" of specific July Revolution events — old images from unrelated conflicts or earlier protests get recaptioned with false dates and locations. Existing Bangla fact-check efforts (Rumor Scanner, BOOM Bangladesh) are manual, slow, and don't scale to the speed at which misinformation spreads on social media. There is no fast, self-serve tool that lets an ordinary citizen or journalist check a claim in real time, with sources they can verify themselves.

---

## 3. Goals & Non-Goals

### Goals
- Let a user verify a text claim against a curated evidence corpus in under 10 seconds
- Let a user check whether a submitted image is a known reused/miscaptioned image
- Always show cited sources — never a black-box verdict
- Support both Bangla and English input/output
- Be usable on a low-end device / slow connection (text-first UI, small payloads)

### Non-Goals (for this sprint)
- Real-time social media crawling/monitoring (out of scope — this is a lookup tool, not a bot)
- User accounts, auth, or personalization
- Training a custom ML model from scratch (use existing embedding models + prompted LLM agents)
- Video verification (image + text only for MVP)
- Full offline/PWA support (deprioritized per team decision — assume some connectivity)

---

## 4. Target Users

| Persona | Need |
|---|---|
| **Citizen fact-checker** | Sees a viral claim/image, wants a fast sanity check before sharing |
| **Journalist / researcher** | Needs cited sources to back a story, not just a yes/no answer |
| **Fact-check org (e.g., Rumor Scanner)** | Could use this as a triage tool to speed up their manual review queue |

---

## 5. User Stories

1. *As a citizen*, I paste a claim I saw on Facebook and get a verdict with links to real sources, so I know whether to share it.
2. *As a citizen*, I upload a screenshot of a viral image and find out it's actually from a 2018 protest, not July 2024, so I don't spread misinformation.
3. *As a journalist*, I search the corpus directly for a date/location to see what's independently verified, so I can cite it in my reporting.
4. *As any user*, I switch the interface to Bangla so I can read and submit claims in my first language.
5. *As any user on a slow connection*, the page loads and returns a verdict without needing to download large assets.

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
                └───────────────┬────────────────┘
                                ▼
                        Verdict UI (bilingual)
```

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
| FR8 | System shows retrieval transparency — "why" a source was matched | P2 (stretch) |
| FR9 | User can submit a social post URL and system extracts claim text from it | P2 (stretch) |

---

## 8. Non-Functional Requirements

- **Latency:** verdict returned in under 10 seconds for text claims
- **Bandwidth:** initial page load under 1 MB; no unnecessary image/video assets
- **Reliability:** if the LLM API fails or times out, the system degrades to "Unverifiable — try again" rather than crashing
- **Explainability:** every verdict must show at least one cited source; a verdict with zero evidence is never shown as Verified or False
- **Bilingual:** all UI copy and verdict output available in Bangla and English

---

## 9. Data / Corpus Design

The corpus is the product's core asset and its biggest execution risk — prioritize building it first.

**Sources to compile (100–200 entries target):**
- Rumor Scanner Bangladesh and BOOM Bangladesh — known false claims (seed the "False" category)
- Ain o Salish Kendra (ASK) and Odhikar human rights documentation — verified event records
- Wikipedia's July Revolution timeline — structured backbone of dates/locations/events
- AFP Fact Check / Reuters Fact Check — reused-image cases (a common pattern: old Syria/Myanmar/2018 quota-movement images recaptioned as July 2024/2025)

**Schema (per corpus entry):**
```json
{
  "id": "string",
  "event_date": "YYYY-MM-DD",
  "location": "string",
  "description_bn": "string",
  "description_en": "string",
  "verdict_label": "verified | false_claim",
  "source_url": "string",
  "source_org": "string",
  "related_image_hashes": ["phash1", "phash2"]
}
```

---

## 10. Tech Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI (Python), Docker |
| Agent orchestration | Simple sequential pipeline (no heavy framework needed — plain function calls with structured LLM outputs) |
| Vector store | Chroma or FAISS |
| Embeddings | sentence-transformers (multilingual model for Bangla/English) |
| LLM | API-based (Claude or equivalent) — declared per hackathon's AI-use disclosure rule |
| Image hashing | `imagehash` (Python) for perceptual hash comparison |
| Frontend | React, bilingual UI toggle |
| Hosting | Vercel (frontend) + Railway/Render (backend) |

---

## 11. API Design (draft)

```
POST /api/verify
  body: { text?: string, image?: base64, url?: string, lang: "bn"|"en" }
  returns: {
    verdict: "verified"|"disputed"|"unverifiable"|"false",
    confidence: 0-1,
    sources: [{ title, url, excerpt }],
    image_match?: { matched: bool, original_source?, original_date? }
  }

GET /api/corpus?query=&date_from=&date_to=&location=
  returns: [ corpus entries matching filters ]
```

---

## 12. UI Requirements

- **Home screen:** single input box (text/image/link), language toggle, submit button
- **Verdict screen:** large color-coded verdict badge (green/yellow/red/gray), confidence %, cited sources list with excerpts, "how this was checked" expandable detail
- **Corpus browser (P1):** simple searchable/filterable list of verified entries
- Design should be readable on a low-end phone screen at minimum

---

## 13. Success Metrics (for demo/judging, not production KPIs)

- Verdict accuracy on a held-out test set of ~20 hand-labeled claims (aim for correct verdict on 80%+)
- Demo reliability: 0 crashes during the live 3-minute presentation
- Corpus size: 100+ verified entries by submission

---

## 14. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Corpus too small/thin by deadline | Build corpus on Day 1 before writing pipeline code; cap scope at 100 entries minimum |
| LLM hallucinates a verdict with no real evidence | Verdict Agent must refuse to say Verified/False if retrieval returns 0 relevant docs — forced "Unverifiable" |
| Image reuse detection has few matches to demo | Deliberately seed 10–15 known reused-image cases into the demo dataset so the feature has something to catch |
| Bilingual support adds scope creep | Ship English-first, add Bangla output as a translation pass on top of the same pipeline, not a separate pipeline |
| Running out of time for polish | Cut FR8/FR9 (stretch) first; core verdict flow (FR1–FR5) must work end-to-end by Day 2 evening |

---

## 15. Execution Timeline (72 hours, 2 people)

**Day 1**
- Person A: build and structure the corpus (JSON), embed into vector store
- Person B: scaffold FastAPI backend, agent pipeline skeleton, React frontend shell
- Evening: wire Claim Extraction → Retrieval Agent, test on 10 sample claims

**Day 2**
- Person A: Cross-Verification + Verdict Agent, prompt tuning, citation formatting
- Person B: Image Reuse Agent (imagehash matching) + frontend polish, Bangla/English toggle
- Evening: integration testing, seed edge-case claims

**Day 3**
- Morning: bug fixes, deploy, test on slow connection
- Afternoon: record demo video, build slide deck, finalize README/problem statement
- Evening: submit early

---

## 16. Judging-Criteria Alignment Checklist

- [ ] Commit history shows incremental progress from Hour 1
- [ ] Public repo with MIT/Apache 2.0 license from day 1
- [ ] README with clear setup/run instructions
- [ ] Demo video scripted around a false-claim-correctly-flagged moment
- [ ] AI-tool usage disclosed per Section 5 rules
- [ ] Submitted well before the deadline, not at 23:59

---

## 17. Post-Hackathon Roadmap (not in scope for the sprint, for context only)

- Expand corpus via partnership with Rumor Scanner / BOOM Bangladesh
- Add browser extension for inline verification on social feeds
- Add video verification support
- Community-contributed corpus entries with moderation queue
