🛠️ Donizo Smart Semantic Pricing Engine (Simulate Mode)
📌 Overview
The Donizo Pricing Engine is a FastAPI-based service for material price lookup and automatic proposal generation using semantic search.
For this submission, EMBED_MODE=simulate is enabled to bypass OpenAI API rate limits, so the system works fully offline with realistic similarity scores.

🚀 Features
Material Search (/material-price) — Find top-matching materials with similarity scores.

Proposal Generation (/generate-proposal) — Parse transcript into tasks, match materials, calculate VAT, margin, and total price.

Feedback Recording (/feedback) — Capture user verdicts and propose adaptation plans.

Simulate Mode — No external API calls, instant results with random but realistic similarity values.

📂 Project Structure
📂 donizo-pricing-engine/
├── 📄 config.yaml — VAT, margin, region multipliers, unit normalization, confidence tiers
├── 📄 docker-compose.yml — Postgres + pgvector DB config
├── 📄 generate_dataset.py — creates materials.csv from synthetic generator
├── 📄 seed.py — loads dataset into DB (simulate or OpenAI mode)
├── 📂 app/
│   ├── 📄 main.py — FastAPI app entrypoint
│   ├── 📂 api/
│   │   └── 📄 routes.py — API endpoints (/material-price, /generate-proposal, /feedback, /healthz)
│   ├── 📂 services/
│   │   ├── 📄 search.py — semantic search (pgvector / simulate)
│   │   ├── 📄 proposal.py — task parsing, labor calc, margin & VAT logic
│   │   ├── 📄 feedback.py — records feedback & outputs adaptation plan
│   │   └── 📄 utils.py — helper functions
│   ├── 📂 models/
│   │   └── 📄 schemas.py — Pydantic models for request/response
│   └── 📂 db/
│       ├── 📄 session.py — DB connection setup
│       └── 📄 init.sql — schema & indexes (pgvector)
├── 📂 data/
│   └── 📄 materials.csv — generated dataset (seeded into DB)
├── 📂 tests/
│   └── 📄 test_endpoints.py — basic API tests
├── 📄 requirements.txt — Python dependencies
├── 📄 .env.example — sample environment vars (DATABASE_URL, OPENAI_API_KEY, EMBED_MODE)
├── 📄 README.md — project documentation & usage
└── 📄 .gitignore — ignores venv, data artifacts, cache

⚙️ Setup & Run
1️⃣ Clone Repo & Setup Environment
git clone https://github.com/YOUR_USERNAME/donizo-pricing-engine.git
cd donizo-pricing-engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
2️⃣ Start Database
docker compose up -d db
export DATABASE_URL=postgresql+psycopg2://donizo:donizo@localhost:5432/pricing
3️⃣ Generate Dataset & Seed (Simulate Mode)
export EMBED_MODE=simulate
python generate_dataset.py
python seed.py
4️⃣ Run the API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
📡 API Usage
Material Search
curl -s "http://127.0.0.1:8000/material-price?query=colle%20carrelage%20salle%20de%20bain%20PACA&region=PACA&limit=3"
Proposal Generation
curl -s -X POST http://127.0.0.1:8000/generate-proposal \
  -H "Content-Type: application/json" \
  -d '{"transcript":"Need waterproof glue and 60x60cm matte white wall tiles, better quality this time. For bathroom walls in Paris"}'
Feedback
curl -s -X POST http://127.0.0.1:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"task_id":"abc123","quote_id":"q456","user_type":"contractor","verdict":"overpriced","comment":"Tile price high for this city","target_component":"materials"}'
🧪 Test Endpoint
curl -s http://127.0.0.1:8000/healthz
Expected:
{"status":"ok"}
📝 Notes
Simulate Mode allows running without OpenAI key or internet calls.
The database schema supports pgvector for real semantic search.
For real embeddings, set:
export EMBED_MODE=openai
export OPENAI_API_KEY=sk-...
and re-run python seed.py.




