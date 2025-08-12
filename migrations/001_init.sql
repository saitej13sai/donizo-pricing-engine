CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS materials (
  id SERIAL PRIMARY KEY,
  material_name TEXT NOT NULL,
  description TEXT NOT NULL,
  unit_price NUMERIC NOT NULL,
  unit TEXT NOT NULL,
  region TEXT NOT NULL,
  vendor TEXT,
  vat_rate NUMERIC,
  quality_score INT,
  updated_at TIMESTAMPTZ NOT NULL,
  source TEXT NOT NULL,
  embedding vector(1536)
);

CREATE INDEX IF NOT EXISTS idx_materials_region ON materials(region);
CREATE INDEX IF NOT EXISTS idx_materials_unit ON materials(unit);
CREATE INDEX IF NOT EXISTS idx_materials_updated_at ON materials(updated_at);

-- ANN index (tune lists for scale)
CREATE INDEX IF NOT EXISTS idx_materials_embedding
ON materials USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
