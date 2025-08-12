import os, httpx, functools, hashlib
import numpy as np
from app.core.config import CONFIG

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = CONFIG["embedding"]["model"]
DIM = int(CONFIG["embedding"]["dimensions"])
EMBED_MODE = os.getenv("EMBED_MODE", "openai").lower()  # "openai" | "simulate"

def _simulate_vec(text: str) -> list[float]:
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    seed = int(h[:8], 16)
    rng = np.random.RandomState(seed)
    v = rng.normal(0, 1, size=DIM).astype(np.float32)
    n = np.linalg.norm(v)
    if n > 0:
        v = v / n
    return v.tolist()

@functools.lru_cache(maxsize=4096)
def _embed_text_cached(text: str) -> list[float]:
    if EMBED_MODE == "simulate":
        return _simulate_vec(text)

    url = "https://api.openai.com/v1/embeddings"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {"model": MODEL, "input": [text]}
    with httpx.Client(timeout=30) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]

def embed_texts(texts: list[str]) -> list[list[float]]:
    return [_embed_text_cached(t) for t in texts]
