Donizo – Smart Semantic Pricing Engine v0
FastAPI microservice for semantic material pricing and quote generation with confidence scoring, VAT rules, contractor margin, regional multipliers, and feedback learning hooks.

Tech: FastAPI, Postgres + pgvector, OpenAI embeddings (swap-ready), YAML config, Docker Compose.

1) What this service does (requirements ✓)
Data ingestion for ≥1,000 materials (shipped dataset: 1,200 rows).

Embedding + Vector DB: name+description embedded and stored with metadata in Postgres + pgvector.

/material-price: multilingual fuzzy search with filters, similarity score, confidence tier, updated_at, source (metadata).

/generate-proposal: infers tasks from transcript, finds materials, computes labor, region multiplier, contractor margin (+25%), VAT (10% renovation, 20% new build), and returns confidence score.

/feedback: stores user verdicts and returns an adaptation plan (how the engine will adjust).

Graceful degradation + region fallback when perfect match or local stock is missing.

YAML config for units normalization, confidence tiers, multipliers, labor rates, fallback vendor note.

Latency: sub-500ms for 1–5k rows in simulate or with pgvector IVFFLAT.

2) Project structure
3) 2) Project structure
bash
Copy
Edit
donizo-pricing-engine/
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
├─ .env.example
├─ README.md
├─ config.yaml
├─ generate_dataset.py         # 1,200 rows
├─ seed.py                     # embeddings + load to DB (simulate or OpenAI)
├─ migrations/
│  └─ 001_init.sql             # schema + pgvector IVFFLAT (1536-D)
└─ app/
   ├─ main.py
   ├─ api/routes.py            # /material-price, /generate-proposal, /feedback
   ├─ core/config.py
   ├─ db/session.py
   ├─ models/schemas.py        # Pydantic I/O (JSON Schema)
   └─ services/
      ├─ embedding.py          # simulate|openai switch
      ├─ search.py             # simulate: SQL filter; openai: pgvector ANN
      ├─ proposal.py           # VAT, margin, region, labor, fallback
      └─ feedback.py           # persist + adaptation notes
3) Configuration
config.yaml (key parts)

Embedding model: text-embedding-3-small (1536-D) → pgvector limit-friendly.

Confidence tiers: HIGH ≥ 0.85, MEDIUM ≥ 0.70, LOW ≥ 0.50.

VAT: 10% renovation (default), 20% new build.

Contractor margin: 25%.

Region multipliers: e.g., Île-de-France 1.10, PACA 1.05.

Units normalization: €/sqm|€/m2|€/m^2 → €/m², etc.

Proposal: labor lexicon + hourly rate (45 €/h), fallback vendor/note.

4) Install & run
Prerequisites
Python 3.11

Docker Desktop

Optional: OpenAI API key (for real embeddings)

Environment
bash
Copy
Edit
cp .env.example .env
# set your OPENAI_API_KEY if you’ll use real embeddings later
Start database
bash
Copy
Edit
docker compose up -d db
Setup venv and deps
bash
Copy
Edit
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://donizo:donizo@localhost:5432/pricing
Generate dataset & seed (default: simulate, no API calls)
bash
Copy
Edit
export EMBED_MODE=simulate
python generate_dataset.py
python seed.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
Open http://127.0.0.1:8000/docs.

Swap to OpenAI embeddings (optional, when you have quota)
bash
Copy
Edit
export EMBED_MODE=openai
export OPENAI_API_KEY=sk-...
export EMBED_BATCH_SIZE=8
export EMBED_SLEEP_SECONDS=1.5
docker compose down -v && docker compose up -d db
python generate_dataset.py
python seed.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
5) Database & schema (pgvector)
Extension: CREATE EXTENSION IF NOT EXISTS vector;

Table: materials(..., embedding vector(1536))

Indexes: region, unit, updated_at, IVFFLAT on embedding with lists=100.

Rationale: pgvector co-locates vectors + metadata; IVFFLAT supports ANN for low-latency top-k search.

6) API endpoints (with examples)
GET /material-price
Semantic search with optional filters.

Params:

query (str, required)

region, unit, vendor (optional filters)

quality_score_min (int)

limit (int, default 5)

Example:

perl
Copy
Edit
GET /material-price?query=colle%20carrelage%20salle%20de%20bain%20PACA&region=PACA&limit=3
Response (excerpt):

json
Copy
Edit
[
  {
    "material_name": "HydroFix Waterproof Adhesive",
    "description": "High-bond waterproof tile adhesive...",
    "unit_price": 2.2,
    "unit": "€/kg",
    "region": "Île-de-France",
    "similarity_score": 0.91,
    "confidence_tier": "HIGH",
    "updated_at": "2025-08-03T14:30:00Z",
    "source": "https://www.leroymerlin.fr/produit/hydrofix-adhesive"
  }
]
Behavior:

Simulate mode: uses SQL filters + synthetic similarity (stable output, no OpenAI).

OpenAI mode: ANN via embedding <=> (:qvec)::vector cosine distance.

Degradation:

If top similarity < min_score (0.50), still returns best item with LOW tier.

POST /generate-proposal
Derives tasks, computes labor, materials, margin, VAT, multipliers, confidence.

Body:

json
Copy
Edit
{
  "transcript": "Need waterproof glue and 60x60cm matte white wall tiles, better quality this time. For bathroom walls in Paris",
  "region": null,
  "build_type": "renovation"    // optional; defaults to renovation
}
Response (excerpt):

json
Copy
Edit
{
  "tasks": [
    {
      "label": "Tile bathroom walls",
      "materials": [...top matches...],
      "estimated_duration": "1 day",
      "margin_protected_price": 460.0,
      "confidence_score": 0.84
    }
  ],
  "total_estimate": 460.0
}
Rules:

VAT: 10% (renovation) or 20% (new build).

Margin: +25% on subtotal (labor + materials).

Region multiplier: applies to material costs.

Fallback: if no regional matches → try any region; if still none → synthesize a generic material with LOW tier and fallback note.

POST /feedback
Stores verdicts and returns adaptation plan.

Body:

json
Copy
Edit
{
  "task_id": "abc123",
  "quote_id": "q456",
  "user_type": "contractor",
  "verdict": "overpriced",
  "comment": "Material was fine, tile price seems high for this city",
  "target_component": "materials"
}
Response (excerpt):

json
Copy
Edit
{
  "status": "recorded",
  "adaptation_plan": [
    "Decrease regional price multiplier slightly for similar materials in this city (learning rate 0.02).",
    "Weight contractor feedback higher and lower confidence if repeated rejections occur."
  ]
}
7) Confidence scoring strategy
Compute cosine similarity (OpenAI mode) or synthetic similarity (simulate mode) → map to tiers:

HIGH ≥ 0.85

MEDIUM ≥ 0.70

LOW ≥ 0.50

If lowest tier, either return best guess with LOW or suggest clarifying constraints (filters).

Confidence in proposal = mean(top materials’ similarities) for that task.

8) Pricing, VAT, and margin logic
Labor: derived from task lexicon (e.g., tiling 8h, glue 2h) × 45 €/h.

Materials: sum top matches’ unit_price × region multiplier (e.g., Île-de-France 1.10).

Margin: +25% on subtotal (labor + materials).

VAT: 10% renovation; 20% new build (applied after margin).

Output: margin_protected_price per task and total_estimate across tasks.

9) Units normalization
Requests like €/sqm, €/m2, €/m^2 are normalized to €/m² via YAML.

Ensures consistent filtering and display.

10) Fallback & graceful degradation
Region fallback: if no match for requested region → search across regions and mark vendor as fallback with LOW tier.

Synthetic fallback: if still no match → synthesize a generic material with neutral price and explicit fallback note.

Degradation: return results even when similarity is low; tiers communicate uncertainty.

11) Performance & latency
Simulate mode: no external calls; SQL filters + metadata sort → fast (<200ms typical).

OpenAI mode:

pgvector IVFFLAT with lists=100 (tune ~√N).

top_k=5 and restricted filters (region/unit/vendor/quality) reduce candidate set.

Embedding cache (LRU) for repeated queries.

Batch & backoff logic in seed.py (429-safe) when embedding rows.

12) Scaling & second-order system design (answers)
What breaks at 1M+ products / 10K daily queries? How to fix?

ANN recall/latency: shard by region/country, tune IVFFLAT lists, use read replicas, and Redis for query result caching.

Write amplification (scrapes/API): async ingestion workers, idempotent upserts, change-data-capture for only re-embedding updated rows.

Hot partitions: partition materials by region/vendor; per-partition indexes.

Tradeoffs between accuracy, latency, confidence

ANN (IVFFLAT) vs exact: IVFFLAT chosen for latency; gated by confidence tiers.

cap top_k=5, log tier distribution to calibrate min_score; fall back gracefully.

Learning from usage

Feedback reduces regional multipliers (EMA with lr=0.02) when “overpriced” recurs; adjusts labor priors; lowers confidence score for materials repeatedly rejected by contractors.

Integrate real-time supplier APIs/scrapers

Pull via workers (Celery/RQ), normalize schema, upsert by (vendor, source URL, SKU), mark updated_at, and re-embed only changed rows.

If a quote gets rejected, log 3 core signals

Similarity and tier at quote time.

Regional price residual vs accepted median for similar tasks.

Vendor/quality attributes of chosen materials.
Use to detect drift and over/under-pricing by region/vendor.

13) Testing (curl)
bash
Copy
Edit
# health
curl -s http://127.0.0.1:8000/healthz

# semantic search (French + region)
curl -s "http://127.0.0.1:8000/material-price?query=colle%20carrelage%20salle%20de%20bain%20PACA&region=PACA&limit=3"

# proposal
curl -s -X POST http://127.0.0.1:8000/generate-proposal \
  -H "Content-Type: application/json" \
  -d '{"transcript":"Need waterproof glue and 60x60cm matte white wall tiles, better quality this time. For bathroom walls in Paris"}'

# feedback
curl -s -X POST http://127.0.0.1:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"task_id":"abc123","quote_id":"q456","user_type":"contractor","verdict":"overpriced","comment":"Tile price high for this city","target_component":"materials"}'
14) Notes for reviewers
This repo runs fully offline in simulate mode (no OpenAI calls).

Switching to real embeddings is a one-command change (EMBED_MODE=openai) and reseed.

The service returns all required fields, including updated_at and source, and implements tiered confidence, VAT/margin rules, fallback, and feedback-led adaptation.

