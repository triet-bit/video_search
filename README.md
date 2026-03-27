# HCMAI Video Retrieval System (Renovate)

> A Video Retrieval System rebuilt and significantly improved from the original submission for the HCMAI Competition.

---

## Project Context

This project is a major renovation of our original video search product built for the HCMAI competition. In the initial version, we utilized FAISS for vector storage and explored models like BEiT-3 (which is fundamentally geared towards facial emotion recognition rather than pure retrieval tasks).

To achieve superior search accuracy and handle complex, multi-event queries, the entire pipeline has been re-architected. We migrated from FAISS to **Qdrant** for robust vector management, replaced the embedding engine with **SigLIP**, introduced **BLIP-2** for visual reranking, and integrated **Gemini 2.5 Flash** for intelligent query chunking.

---

## System Architecture

The system exposes a single FastAPI backend that routes each query to one of **three search pipelines** depending on the search type selected by the user. All pipelines share the same SigLIP encoder and Qdrant vector store; they differ in how the query is prepared and how results are ranked.

```
Browser (React / Vite)
       │  HTTP
       ▼
  FastAPI Server
       │
       ├─── [Type 1] Vector Search
       ├─── [Type 2] Trake Search (DANTE DP)
       └─── [Type 3] Enhanced Search (Gemini)
       │
       ├── Qdrant      ← semantic vector store
       └── MongoDB     ← frame metadata
```

---

## Search Pipelines

### Type 1 — Vector Search

Standard single-query semantic search. Best for short, focused queries.

```
User query
    │
    ▼
SigLIP encoder          ← converts text to embedding vector
    │
    ▼
Qdrant (cosine search)  ← finds nearest keyframe vectors
    │
    ▼
Top-K keyframes         ← ranked by similarity score
```

**When to use:** Simple queries like *"a dog running on the beach"* or *"aerial view of a city at night"*.

---

### Type 2 — Trake Search (DANTE DP)

Multi-event temporal search. Finds a sequence of events occurring in order within the same video. Uses the **DANTE Dynamic Programming** algorithm to select the optimal chain of keyframes while penalizing unnatural time gaps (λ penalty).

```
Multi-event query  (e.g. "man picks up bag → walks through door → enters car")
    │
    ▼
SigLIP encoder          ← each event clause encoded independently
    │
    ▼
Qdrant search           ← candidate keyframes retrieved per event
    │
    ▼
DANTE DP algorithm      ← finds optimal sequence with λ time penalty
    │
    ▼
Ordered keyframe chain  ← time-consistent sequence within one video
```

**When to use:** Queries describing a narrative or sequence of actions, e.g. *"person enters a room, sits down, opens a laptop"*.

---

### Type 3 — Enhanced Search with Gemini

LLM-assisted search for long, descriptive, or ambiguous queries. **Gemini 2.5 Flash** decomposes the query into independent visual chunks (subject, action, environment), each chunk is encoded and searched separately, and results are merged and deduplicated.

```
Long / complex query
    │
    ▼
Gemini 2.5 Flash        ← splits query into N visual sub-queries
    │
    ├── chunk 1 ──► SigLIP ──► Qdrant ──► results 1
    ├── chunk 2 ──► SigLIP ──► Qdrant ──► results 2
    └── chunk N ──► SigLIP ──► Qdrant ──► results N
                                              │
                                              ▼
                                     Merge & deduplicate
                                              │
                                              ▼
                                    Top-K keyframes (aggregated)
```

**When to use:** Queries like *"a news anchor in a studio with a city skyline in the background, discussing weather, while a graphic appears on screen"*.

---

## Local Development

### Prerequisites

- Python 3.12+
- Node.js & npm
- Qdrant (local or Docker)
- MongoDB (local or Docker)
- `GOOGLE_API_KEY` set in `.env` (for Gemini)

### Start the Backend (FastAPI)

```bash
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Start the Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

### Start with Docker

```bash
docker compose up --build
```

---

## Project Structure

```
.
├── configs/                # Environment configs and model settings
├── data/                   # Vector index and metadata storage
├── documents/              # Reference papers and assets
├── docker-compose.yaml
├── Makefile
├── requirements.txt
├── scripts/                # Utility scripts (init DB, convert index, etc.)
├── src/
│   ├── api/                # FastAPI app, routers, schemas
│   ├── db/                 # Qdrant & MongoDB clients
│   ├── models/             # SigLIP, BLIP-2, Gemini, reranker
│   ├── search/             # Vector search & DANTE DP (track_search)
│   └── utils/              # Helpers and logger
├── frontend/               # React + Vite UI
└── tests/                  # API and pipeline tests
```

---

## Model Overview

| Component | Model | Role |
|---|---|---|
| Embedding | SigLIP | Text & image → vector |
| LLM | Gemini 2.5 Flash | Query decomposition (Type 3) |
| Reranker | BLIP-2 | High-precision visual reranking |
| Vector DB | Qdrant | Cosine similarity search |
| Metadata DB | MongoDB | Frame and video metadata |
