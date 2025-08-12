import os
import random
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.services.embedding import embed_texts
from app.core.config import CONFIG

EMBED_MODE = os.getenv("EMBED_MODE", "openai").lower()  # "simulate" | "openai"

def _normalize_unit(u: str | None) -> str | None:
    if not u:
        return None
    norm = CONFIG["filters"]["units_normalization"]
    return norm.get(u, u)

def cosine_sim_to_conf(sim: float):
    tiers = CONFIG["defaults"]["confidence_tiers"]
    if sim >= tiers["HIGH"]:
        return sim, "HIGH"
    if sim >= tiers["MEDIUM"]:
        return sim, "MEDIUM"
    return sim, "LOW"

def _simulate_search(db: Session, region: str | None, unit: str | None, vendor: str | None,
                     qmin: int | None, limit: int):
    """
    Simulation path: no pgvector ops. Pull recent rows that match filters and
    synthesize a plausible similarity score.
    """
    unit = _normalize_unit(unit)
    top_k = limit or CONFIG["search"]["top_k"]

    base = (
        "SELECT material_name, description, unit_price, unit, region, vendor, "
        "vat_rate, quality_score, updated_at, source "
        "FROM materials WHERE 1=1"
    )
    params = {}
    if region:
        base += " AND region = :region"
        params["region"] = region
    if unit:
        base += " AND unit = :unit"
        params["unit"] = unit
    if vendor:
        base += " AND vendor = :vendor"
        params["vendor"] = vendor
    if qmin is not None:
        base += " AND quality_score >= :qmin"
        params["qmin"] = qmin

    # Order by freshness; in real mode we sort by vector distance.
    base += " ORDER BY updated_at DESC LIMIT :top_k"
    params["top_k"] = top_k

    rows = db.execute(text(base), params).mappings().all()

    results = []
    for r in rows:
        # Synthesize a believable similarity for demo purposes
        sim = round(random.uniform(0.82, 0.97), 4)
        score, tier = cosine_sim_to_conf(sim)
        results.append({**dict(r), "similarity_score": score, "confidence_tier": tier})
    return results

def semantic_search(db: Session, query: str, region: str | None, unit: str | None,
                    vendor: str | None, qmin: int | None, limit: int):
    """
    Dual-path search:
      - simulate: SQL filter + synthetic similarity
      - openai:   pgvector ANN using <=> with explicit ::vector cast
    """
    if EMBED_MODE == "simulate":
        return _simulate_search(db, region, unit, vendor, qmin, limit)

    # --- Real vector search path (OpenAI embeddings) ---
    vec = embed_texts([query])[0]
    top_k = limit or CONFIG["search"]["top_k"]
    min_score = CONFIG["search"]["min_score"]

    unit = _normalize_unit(unit)

    # Use explicit ::vector cast on the parameter to avoid "vector <=> numeric[]" errors
    base = (
        "SELECT material_name, description, unit_price, unit, region, vendor, vat_rate, quality_score, "
        "updated_at, source, 1 - (embedding <=> (:qvec)::vector) as similarity_score "
        "FROM materials WHERE 1=1"
    )
    params = {"qvec": vec, "top_k": top_k}
    if region:
        base += " AND region = :region"
        params["region"] = region
    if unit:
        base += " AND unit = :unit"
        params["unit"] = unit
    if vendor:
        base += " AND vendor = :vendor"
        params["vendor"] = vendor
    if qmin is not None:
        base += " AND quality_score >= :qmin"
        params["qmin"] = qmin

    base += " ORDER BY embedding <=> (:qvec)::vector ASC LIMIT :top_k"

    rows = db.execute(text(base), params).mappings().all()

    results = []
    for r in rows:
        sim = float(r["similarity_score"])
        score, tier = cosine_sim_to_conf(sim)
        results.append({**dict(r), "similarity_score": round(score, 4), "confidence_tier": tier})

    if not results:
        return []

    # graceful degradation if below minimum similarity
    if results[0]["similarity_score"] < min_score:
        results[0]["confidence_tier"] = "LOW"
    return results

