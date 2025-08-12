from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.schemas import MaterialOut, ProposalIn, ProposalOut, FeedbackIn
from app.services.search import semantic_search
from app.services.proposal import generate_proposal
from app.services.feedback import record_feedback, adaptation_notes

router = APIRouter()

@router.get("/healthz")
def health():
    return {"status": "ok"}

@router.get("/material-price", response_model=list[MaterialOut])
def material_price(
    query: str,
    region: str | None = None,
    unit: str | None = None,
    vendor: str | None = None,
    quality_score_min: int | None = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    results = semantic_search(db, query, region, unit, vendor, quality_score_min, limit)
    if not results:
        raise HTTPException(status_code=404, detail="No materials found")
    return results

@router.post("/generate-proposal", response_model=ProposalOut)
def generate(proposal: ProposalIn, db: Session = Depends(get_db)):
    out = generate_proposal(db, proposal.transcript, proposal.region, proposal.build_type)
    return out

@router.post("/feedback")
def feedback(payload: FeedbackIn, db: Session = Depends(get_db)):
    record_feedback(db, payload.model_dump())
    return {"status": "recorded", "adaptation_plan": adaptation_notes(payload.model_dump())}
