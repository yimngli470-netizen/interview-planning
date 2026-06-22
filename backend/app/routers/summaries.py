from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TopicSummary
from ..schemas import SummaryOut

router = APIRouter(prefix="/api/summaries", tags=["summaries"])


@router.get("/{summary_id}", response_model=SummaryOut)
def get_summary(summary_id: int, db: Session = Depends(get_db)):
    """Full distilled-HTML study-notes body for one topic summary, fetched on
    demand when the user opens the 'Study notes' panel (kept out of the topic
    feed so that listing stays small)."""
    s = db.get(TopicSummary, summary_id)
    if s is None:
        raise HTTPException(404, "summary not found")
    return SummaryOut.model_validate(s)
