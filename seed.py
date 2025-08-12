import os, csv, yaml, time, math, random, hashlib
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import httpx
import numpy as np

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
CONFIG_PATH = os.getenv("CONFIG_PATH", "./config.yaml")
config = yaml.safe_load(open(CONFIG_PATH, "r", encoding="utf-8"))

EMBED_MODE = os.getenv("EMBED_MODE", "openai").lower()  # "openai" | "simulate"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = config["embedding"]["model"]
DIM = int(config["embedding"]["dimensions"])

# Tunables (can be overridden via env)
BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "16"))
SLEEP_BETWEEN = float(os.getenv("EMBED_SLEEP_SECONDS", "1.0"))
MAX_RETRIES = int(os.getenv("EMBED_MAX_RETRIES", "8"))

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def _deterministic_vec(text: str, dim: int) -> list[float]:
    # Deterministic seed from text (md5 -> int)
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    seed = int(h[:8], 16)
    rng = np.random.RandomState(seed)
    v = rng.normal(0, 1, size=dim).astype(np.float32)
    # L2 normalize
    norm = np.linalg.norm(v)
    if norm > 0:
        v = v / norm
    return v.tolist()

def backoff_sleep(attempt: int, retry_after: float | None):
    if retry_after and retry_after > 0:
        time.sleep(retry_after)
        return
    base = min(2 ** attempt, 30)
    jitter = random.uniform(0, 0.5)
    time.sleep(base + jitter)

def get_embedding_batch(texts):
    if EMBED_MODE == "simulate":
        return [_deterministic_vec(t, DIM) for t in texts]

    # else: openai
    url = "https://api.openai.com/v1/embeddings"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {"model": EMBED_MODEL, "input": texts}

    for attempt in range(MAX_RETRIES):
        try:
            limits = httpx.Limits(max_keepalive_connections=1, max_connections=2)
            with httpx.Client(timeout=60, limits=limits) as client:
                r = client.post(url, headers=headers, json=payload)
                if r.status_code == 429:
                    ra = r.headers.get("Retry-After")
                    retry_after = float(ra) if ra and ra.isdigit() else None
                    print(f"[rate-limit] 429 received. attempt={attempt+1}/{MAX_RETRIES} retry_after={retry_after}")
                    backoff_sleep(attempt+1, retry_after)
                    continue
                r.raise_for_status()
                data = r.json()["data"]
                return [d["embedding"] for d in data]
        except httpx.HTTPStatusError as e:
            if 500 <= e.response.status_code < 600:
                print(f"[server] {e.response.status_code} attempt={attempt+1}/{MAX_RETRIES}")
                backoff_sleep(attempt+1, None)
                continue
            raise
        except (httpx.TimeoutException, httpx.TransportError) as e:
            print(f"[network] {type(e).__name__} attempt={attempt+1}/{MAX_RETRIES}")
            backoff_sleep(attempt+1, None)
            continue
    raise RuntimeError("Failed to obtain embeddings after retries")

def upsert(conn, row, emb):
    conn.execute(text("""
        INSERT INTO materials (material_name, description, unit_price, unit, region, vendor, vat_rate, quality_score, updated_at, source, embedding)
        VALUES (:material_name, :description, :unit_price, :unit, :region, :vendor, :vat_rate, :quality_score, :updated_at, :source, :embedding)
    """), {
        "material_name": row["material_name"],
        "description": row["description"],
        "unit_price": float(row["unit_price"]),
        "unit": row["unit"],
        "region": row["region"],
        "vendor": row.get("vendor") or None,
        "vat_rate": float(row["vat_rate"]) if row.get("vat_rate") not in ("", None) else None,
        "quality_score": int(row["quality_score"]) if row.get("quality_score") not in ("", None) else None,
        "updated_at": row["updated_at"],
        "source": row["source"],
        "embedding": emb
    })

def main():
    mode = EMBED_MODE
    with engine.begin() as conn:
        ddl = open("./migrations/001_init.sql","r",encoding="utf-8").read()
        conn.execute(text(ddl))
        conn.execute(text("DELETE FROM materials"))
    rows = list(csv.DictReader(open("./data/materials.csv","r",encoding="utf-8")))
    total = len(rows)
    print(f"Seeding {total} rows with mode={mode} model={EMBED_MODEL} dim={DIM} batch={BATCH_SIZE}")

    for i in range(0, total, BATCH_SIZE):
        chunk = rows[i:i+BATCH_SIZE]
        inputs = [f"{r['material_name']} || {r['description']}" for r in chunk]
        embs = get_embedding_batch(inputs)
        with engine.begin() as conn:
            for r, e in zip(chunk, embs):
                upsert(conn, r, e)
        print(f"Inserted {i+len(chunk)}/{total}")
        if SLEEP_BETWEEN > 0 and mode == "openai":
            time.sleep(SLEEP_BETWEEN)
    print("Done")

if __name__ == "__main__":
    main()

