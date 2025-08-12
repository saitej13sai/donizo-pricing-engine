📂 donizo-pricing-engine/
├── 📄 config.yaml — VAT, margin, region multipliers, unit normalization, confidence tiers
├── 📄 docker-compose.yml — Postgres + pgvector DB config
├── 📄 generate_dataset.py — creates materials.csv from synthetic generator
├── 📄 seed.py — loads dataset into DB (simulate or OpenAI mode)
├── 📂 app/
│ ├── 📄 main.py — FastAPI app entrypoint
│ ├── 📂 api/
│ │ └── 📄 routes.py — API endpoints (/material-price, /generate-proposal, /feedback, /healthz)
│ ├── 📂 services/
│ │ ├── 📄 search.py — semantic search (pgvector / simulate)
│ │ ├── 📄 proposal.py — task parsing, labor calc, margin & VAT logic
│ │ ├── 📄 feedback.py — records feedback & outputs adaptation plan
│ │ └── 📄 utils.py — helper functions
│ ├── 📂 models/
│ │ └── 📄 schemas.py — Pydantic models for request/response
│ └── 📂 db/
│ ├── 📄 session.py — DB connection setup
│ └── 📄 init.sql — schema & indexes (pgvector)
├── 📂 data/
│ └── 📄 materials.csv — generated dataset (seeded into DB)
├── 📂 tests/
│ └── 📄 test_endpoints.py — basic API tests
├── 📄 requirements.txt — Python dependencies
├── 📄 .env.example — sample environment vars (DATABASE_URL, OPENAI_API_KEY, EMBED_MODE)
├── 📄 README.md — project documentation & usage
└── 📄 .gitignore — ignores venv, data artifacts, cache

