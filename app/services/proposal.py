import re, math, datetime
from sqlalchemy.orm import Session
from app.core.config import CONFIG
from app.services.search import semantic_search

def detect_region(transcript: str, region_hint: str|None) -> str:
    if region_hint:
        return region_hint
    for rg in CONFIG["regions"].keys():
        if rg.lower() in transcript.lower():
            return rg
    return CONFIG["defaults"]["default_region"]

def detect_build_type(transcript: str, build_type: str|None) -> str:
    if build_type:
        return build_type
    if re.search(r"\bnew build|nouvelle construction\b", transcript, re.I):
        return "new"
    return "renovation"

def pick_tasks(transcript: str):
    tasks = []
    lex = CONFIG["proposal"]["task_lexicon"]
    t = transcript.lower()
    if any(k in t for k in ["tile","carrelage","tiles","60x60","60 by 60"]): tasks.append(lex["tile"])
    if any(k in t for k in ["glue","adhesive","colle"]): tasks.append(lex["glue"])
    if any(k in t for k in ["cement","ciment","outdoor"]): tasks.append(lex["cement"])
    if not tasks: tasks.append({"label":"General renovation task","base_labor_hours":6})
    return tasks

def compute_vat(build_type: str) -> float:
    return CONFIG["defaults"]["default_vat_new"] if build_type == "new" else CONFIG["defaults"]["default_vat_reno"]

def region_multiplier(region: str) -> float:
    return CONFIG["regions"].get(region, 1.0)

def contractor_margin() -> float:
    return CONFIG["defaults"]["contractor_margin"]

def estimate_task(db: Session, transcript: str, region: str, task: dict):
    mats = semantic_search(db=db, query=transcript, region=region, unit=None, vendor=None, qmin=None, limit=3)

    fallback_used = False
    if not mats:
        # try any region
        mats_any = semantic_search(db=db, query=transcript, region=None, unit=None, vendor=None, qmin=None, limit=1)
        if mats_any:
            m = mats_any[0]
            m["vendor"] = CONFIG["proposal"]["fallback_vendor"]
            m["source"] = m["source"] + "  # fallback-other-region"
            m["confidence_tier"] = "LOW"
            mats = [m]
            fallback_used = True
        else:
            # synthesize a generic fallback material
            mats = [{
                "material_name": "Generic material (simulated)",
                "description": CONFIG["proposal"]["fallback_note"],
                "unit_price": 20.0,
                "unit": "€/unit",
                "region": region,
                "vendor": CONFIG["proposal"]["fallback_vendor"],
                "vat_rate": None,
                "quality_score": 3,
                "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
                "source": "https://donizo.example/fallback",
                "similarity_score": 0.5,
                "confidence_tier": "LOW"
            }]
            fallback_used = True

    labor_hours = task["base_labor_hours"]
    labor_rate = CONFIG["proposal"]["labor_rate_per_hour"]
    labor_cost = labor_hours * labor_rate

    rm = region_multiplier(region)
    material_cost = 0.0
    top_mats = mats[:2]
    for m in top_mats:
        material_cost += float(m["unit_price"]) * rm

    conf = sum(m["similarity_score"] for m in top_mats) / max(1, len(top_mats))
    build_type = detect_build_type(transcript, None)
    subtotal = labor_cost + material_cost
    margin = subtotal * contractor_margin()
    vat = (subtotal + margin) * compute_vat(build_type)
    final = subtotal + margin + vat

    label = task["label"] + (" (fallback)" if fallback_used else "")
    return {
        "label": label,
        "materials": top_mats,
        "estimated_duration": f"{math.ceil(labor_hours/8)} day",
        "margin_protected_price": round(final,2),
        "confidence_score": round(conf,4)
    }

def generate_proposal(db: Session, transcript: str, region_hint: str|None, build_type_hint: str|None):
    region = detect_region(transcript, region_hint)
    tasks = pick_tasks(transcript)
    outs = [estimate_task(db, transcript, region, t) for t in tasks]
    total = round(sum(t["margin_protected_price"] for t in outs), 2)
    return {"tasks": outs, "total_estimate": total}
