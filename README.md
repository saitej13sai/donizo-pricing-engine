🛠️ Donizo Smart Semantic Pricing Engine (Simulate Mode)
Smart semantic pricing engine for renovation materials.
Handles fuzzy, multilingual queries; returns high-confidence material matches; generates structured proposals with VAT, margin logic, and confidence scoring — per Donizo Founding Data Engineer Test Case 3.
## 📂 Project Structure
```plaintext
/donizo-pricing-engine/
├── config.yaml                   # VAT, margin, region multipliers, unit normalization, confidence tiers
├── docker-compose.yml             # Postgres + pgvector DB config
├── generate_dataset.py            # creates materials.csv from synthetic generator
├── seed.py                        # loads dataset into DB (simulate or OpenAI mode)
├── app/
│   ├── main.py                    # FastAPI app entrypoint
│   ├── api/
│   │   └── routes.py              # API endpoints (/material-price, /generate-proposal, /feedback, /healthz)
│   ├── services/
│   │   ├── search.py              # semantic search (pgvector / simulate)
│   │   ├── proposal.py            # task parsing, labor calc, margin & VAT logic
│   │   ├── feedback.py            # records feedback & outputs adaptation plan
│   │   └── utils.py               # helper functions
│   ├── models/
│   │   └── schemas.py             # Pydantic models for request/response
│   └── db/
│       ├── session.py              # DB connection setup
│       └── init.sql                # schema & indexes (pgvector)
├── data/
│   └── materials.csv               # generated dataset (seeded into DB)
├── tests/
│   └── test_endpoints.py            # basic API tests
├── requirements.txt                 # Python dependencies
├── .env.example                     # sample env vars (DATABASE_URL, OPENAI_API_KEY, EMBED_MODE)
├── README.md                        # project documentation & usage
└── .gitignore                       # ignores venv, data artifacts, cache

#🚀 1) How to Run

Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

✅ Start database
docker compose up -d db
export DATABASE_URL=postgresql+psycopg2://donizo:donizo@localhost:5432/pricing

✅ Generate dataset & seed (Simulate Mode)
export EMBED_MODE=simulate
python generate_dataset.py
python seed.py

✅ Run API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

✅ You can now test:

✅Material Search
curl -s "http://127.0.0.1:8000/material-price?query=colle%20carrelage%20salle%20de%20bain%20PACA&region=PACA&limit=3"
✅Proposal Generation
curl -s -X POST http://127.0.0.1:8000/generate-proposal \
  -H "Content-Type: application/json" \
  -d '{"transcript":"Need waterproof glue and 60x60cm matte white wall tiles, better quality this time. For bathroom walls in Paris"}'
✅Feedback
curl -s -X POST http://127.0.0.1:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"task_id":"abc123","quote_id":"q456","user_type":"contractor","verdict":"overpriced","comment":"Tile price high for this city","target_component":"materials"}'

📄 2) Output JSON (material search example)
{
    "material_name": "Grout Anti-Mold White",
    "description": "Tile grout with anti-mold additive; white; bathroom and kitchen use",
    "unit_price": 20.55,
    "unit": "€/unit",
    "region": "Auvergne-Rhône-Alpes",
    "vendor": "PointP",
    "vat_rate": 10,
    "quality_score": 5,
    "updated_at": "2025-08-03T14:30:00Z",
    "source": "https://www.bricodepot.fr/produit/grout-anti-mold-white"
  }

⚙️ 3) Pricing & Margin Logic

✅ Materials: Unit prices from data/materials.csv
✅ Labor: Estimated duration × hourly rate × region multiplier
✅ Margin:
Base 25%
+5% for plumbing tasks
-5% if confidence > 0.9
Clamped between 15–35%
✅ VAT (France simplified):
10% if renovation & dwelling > 2 years
20% otherwise
✅ Confidence:
Derived from similarity score → HIGH / MEDIUM / LOW tiers

📌 4) Assumptions & Edge Cases

EMBED_MODE=simulate bypasses actual vector math and uses random realistic similarity scores.
If no region match is found, returns top matches across all regions.
Multilingual query handling supported.
Fallback margin logic if missing price data.

🧠 5) Bonus Features Implemented

✅ Simulate Mode (offline, no API key required)
✅ Region filters
✅ Confidence tiers for margin protection
✅ Feedback loop adjusting regional multipliers
✅ Docker-ready with pgvector schema

🔮 6) Future Improvements

Real embeddings via OpenAI or local embedding models
Live supplier price API integration
Per-task labor productivity adjustment
Multilingual embeddings for EN/FR/ES

🧪 7) Run Tests
pytest tests/


