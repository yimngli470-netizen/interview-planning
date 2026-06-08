from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import llm
from ..database import get_db
from ..models import ExplainCache, Subtopic

router = APIRouter(prefix="/api/ai", tags=["ai"])

EXPLAIN_MODES = {"simpler", "deeper"}


@router.get("/status")
def ai_status():
    """Whether AI auto-fill is available (ANTHROPIC_API_KEY is set)."""
    return {"configured": llm.ai_configured()}


class ExplainIn(BaseModel):
    point_title: str
    topic_title: str = ""
    domain_name: str = ""
    mode: str = "simpler"  # 'simpler' | 'deeper'
    # When given, the result is cached (and re-served) per (subtopic, mode) — the
    # explanation is the same for every user, so we only ever generate it once.
    subtopic_id: int | None = None
    refresh: bool = False  # force regeneration, overwriting any cached copy


@router.post("/explain")
def explain(payload: ExplainIn, db: Session = Depends(get_db)):
    """On-demand markdown explanation of one learning point (simpler/deeper).
    Cache-first: a hit returns instantly with no LLM call."""
    mode = payload.mode if payload.mode in EXPLAIN_MODES else "simpler"

    cached = None
    if payload.subtopic_id is not None:
        # On-demand explanations are for shared DEFAULT content only. A user's own
        # learning point (owner_id set) must not trigger an LLM call.
        sub = db.get(Subtopic, payload.subtopic_id)
        if sub is not None and sub.owner_id is not None:
            raise HTTPException(403, "AI explanations are only available for default content")
        cached = db.scalar(
            select(ExplainCache).where(
                ExplainCache.subtopic_id == payload.subtopic_id,
                ExplainCache.mode == mode,
            )
        )
        if cached and not payload.refresh:
            return {"markdown": cached.markdown, "cached": True}

    if not llm.ai_configured():
        raise HTTPException(503, "AI is not configured (no API key)")
    md = llm.explain_learning_point(
        payload.point_title, payload.topic_title, payload.domain_name, mode
    )
    if not md:
        raise HTTPException(502, "Could not generate an explanation")

    if payload.subtopic_id is not None:
        try:
            if cached:  # refresh path — overwrite
                cached.markdown = md
            else:
                db.add(ExplainCache(subtopic_id=payload.subtopic_id, mode=mode, markdown=md))
            db.commit()
        except IntegrityError:
            # Another request cached it first (race on the unique constraint) — fine.
            db.rollback()
    return {"markdown": md, "cached": False}
