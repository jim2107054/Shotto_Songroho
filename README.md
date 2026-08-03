# Shotto Songroho

Agentic Fact-Verification for July Revolution Claims

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Track: Spirit of July](https://img.shields.io/badge/Track-Spirit%20of%20July-blue)]()
[![Hackathon: July 2026](https://img.shields.io/badge/Hackathon-July%202026-green)]()

## What is this?

Shotto Songroho lets any user submit a claim, image, or social post link related to the July Revolution and receive a **cited, evidence-backed verdict** — Verified, Disputed, Unverifiable, or False — within seconds.

The verdict is produced by a **multi-agent pipeline** (not a single LLM call) that:
1. **Extracts** the claim into structured data
2. **Retrieves** matching evidence from a curated corpus
3. **Cross-verifies** for consistency and contradictions
4. **Checks images** against known reused/miscaptioned images
5. **Produces a verdict** with cited sources

## Key Features

- 🔍 **Multi-agent verification pipeline** — 5 specialized AI agents working in sequence
- 📚 **Curated corpus** — 65+ verified events and known false claims
- 🖼️ **Image reuse detection** — Catches recycled/miscaptioned images from unrelated events
- 🌐 **Bilingual** — Full Bangla (বাংলা) and English support
- 📱 **Mobile-first** — Works on low-end devices with small payloads
- 🔗 **Cited sources** — Every verdict shows verifiable sources
- 🔬 **Pipeline transparency** — See exactly how each claim was verified

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11) |
| Agent Pipeline | Sequential multi-agent with Gemini LLM |
| Vector Store | ChromaDB with cosine similarity |
| Embeddings | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) |
| Image Hashing | imagehash (perceptual hashing) |
| Frontend | React 18 + Vite 5 |
| Styling | Vanilla CSS with glassmorphism dark theme |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Gemini API key (get one at [ai.google.dev](https://ai.google.dev))

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the server
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Open http://localhost:5173 in your browser.

### Docker (Alternative)

```bash
# From project root
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/verify` | Verify a claim (text/image/URL) |
| GET | `/api/corpus` | Search/browse the corpus |
| GET | `/api/health` | Health check |

### Example: Verify a claim

```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"text": "Students were shot at Dhaka University on July 19, 2024", "lang": "en"}'
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings
│   │   ├── api/routes.py        # API endpoints
│   │   ├── agents/              # Multi-agent pipeline
│   │   │   ├── claim_extractor.py
│   │   │   ├── evidence_retriever.py
│   │   │   ├── cross_verifier.py
│   │   │   ├── image_checker.py
│   │   │   ├── verdict_agent.py
│   │   │   └── pipeline.py
│   │   ├── corpus/              # Seed data
│   │   └── services/            # ChromaDB service
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/          # React components
│   │   ├── i18n/                # Bangla + English translations
│   │   └── hooks/               # Custom hooks
│   └── package.json
└── docker-compose.yml
```

## AI Usage Disclosure

This project uses:
- **Google Gemini** (API-based) for claim extraction, cross-verification, and verdict generation
- **sentence-transformers** (paraphrase-multilingual-MiniLM-L12-v2) for multilingual embedding generation
- **imagehash** for perceptual image hashing

The AI assists in analysis but every verdict is backed by evidence from the curated corpus. The system never produces a "Verified" or "False" verdict without supporting evidence.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Team

Built for the July Hackathon 2026 — Track B (Spirit of July)
