from sqlalchemy import text
from sqlalchemy.orm import Session

def record_feedback(db: Session, payload: dict):
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            task_id TEXT,
            quote_id TEXT,
            user_type TEXT,
            verdict TEXT,
            comment TEXT,
            target_component TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    db.execute(text("""
        INSERT INTO feedback (task_id, quote_id, user_type, verdict, comment, target_component)
        VALUES (:task_id, :quote_id, :user_type, :verdict, :comment, :target_component)
    """), payload)

def adaptation_notes(payload: dict) -> list[str]:
    notes = []
    v = (payload.get("verdict") or "").lower()
    target = (payload.get("target_component") or "").lower()
    if "overpriced" in v or target == "materials":
        notes.append("Decrease regional price multiplier slightly for similar materials in this city (learning rate 0.02).")
    if target == "labor":
        notes.append("Recalibrate labor hours for this task label based on moving average of accepted quotes.")
    if target == "vat":
        notes.append("Verify VAT inference (renovation vs new build) next time.")
    if (payload.get("user_type") or "").lower() == "contractor":
        notes.append("Weight contractor feedback higher and lower confidence if repeated rejections occur.")
    return notes
