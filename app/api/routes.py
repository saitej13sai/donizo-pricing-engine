from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.schemas import MaterialOut, ProposalIn, ProposalOut, FeedbackIn
from app.services.search import semantic_search
from app.services.proposal import generate_proposal
from app.services.feedback import record_feedback, adaptation_notes
from app.services.utils import rows_to_csv  # <-- add this import

router = APIRouter()

@router.get("/healthz")
def health():
    return {"status": "ok"}

@router.get("/material-price", response_model=list[MaterialOut])
def material_price(
    request: Request,
    query: str = Query(..., description="Fuzzy material query"),
    region: str | None = Query(None),
    unit: str | None = Query(None),
    vendor: str | None = Query(None),
    quality_score_min: int | None = Query(None, ge=0, le=5),
    limit: int = Query(5, ge=1, le=50),
    format: str = Query("json", pattern="^(json|csv)$", description="Response format"),
    db: Session = Depends(get_db),
):
    """
    Return material matches with similarity + confidence.
    - JSON (default) or CSV when format=csv or Accept: text/csv
    """
    results = semantic_search(db, query, region, unit, vendor, quality_score_min, limit)
    if not results:
        raise HTTPException(status_code=404, detail="No materials found")

    # normalize unit_price to float for consistent output
    for r in results:
        try:
            if isinstance(r.get("unit_price"), str):
                r["unit_price"] = float(r["unit_price"])
        except Exception:
            pass

    # Decide CSV vs JSON (query param wins; else Accept header)
    wants_csv = (
        format == "csv"
        or "text/csv" in (request.headers.get("accept") or "").lower()
    )

    if wants_csv:
        field_order = [
            "material_name",
            "description",
            "unit_price",
            "unit",
            "region",
            "vendor",
            "vat_rate",
            "quality_score",
            "updated_at",
            "source",
            "similarity_score",
            "confidence_tier",
        ]
        csv_text = rows_to_csv(results, field_order)
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="material_price.csv"'},
        )

    # default: JSON (FastAPI will validate against MaterialOut[])
    return results

@router.post("/generate-proposal", response_model=ProposalOut)
def generate(proposal: ProposalIn, db: Session = Depends(get_db)):
    out = generate_proposal(db, proposal.transcript, proposal.region, proposal.build_type)
    return out

@router.post("/feedback")
def feedback(payload: FeedbackIn, db: Session = Depends(get_db)):
    record_feedback(db, payload.model_dump())
    return {"status": "recorded", "adaptation_plan": adaptation_notes(payload.model_dump())}
