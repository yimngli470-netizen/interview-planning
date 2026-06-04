from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Subtopic, Topic
from ..schemas import STATUSES, SubtopicCreate, SubtopicOut, SubtopicUpdate

router = APIRouter(prefix="/api", tags=["subtopics"])


def _validate_status(status: str | None):
    if status is not None and status not in STATUSES:
        raise HTTPException(422, f"status must be one of {sorted(STATUSES)}")


@router.get("/topics/{topic_id}/subtopics", response_model=list[SubtopicOut])
def list_subtopics(topic_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(Subtopic)
        .where(Subtopic.topic_id == topic_id)
        .order_by(Subtopic.order, Subtopic.id)
    ).all()


@router.post(
    "/topics/{topic_id}/subtopics", response_model=SubtopicOut, status_code=201
)
def create_subtopic(
    topic_id: int, payload: SubtopicCreate, db: Session = Depends(get_db)
):
    _validate_status(payload.status)
    if not db.get(Topic, topic_id):
        raise HTTPException(404, "Topic not found")
    data = payload.model_dump()
    if not data.get("order"):
        max_o = db.scalar(
            select(func.coalesce(func.max(Subtopic.order), 0)).where(
                Subtopic.topic_id == topic_id
            )
        )
        data["order"] = (max_o or 0) + 1
    sub = Subtopic(topic_id=topic_id, **data)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.patch("/subtopics/{subtopic_id}", response_model=SubtopicOut)
def update_subtopic(
    subtopic_id: int, payload: SubtopicUpdate, db: Session = Depends(get_db)
):
    _validate_status(payload.status)
    sub = db.get(Subtopic, subtopic_id)
    if not sub:
        raise HTTPException(404, "Subtopic not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(sub, k, v)
    db.commit()
    db.refresh(sub)
    return sub


@router.delete("/subtopics/{subtopic_id}", status_code=204)
def delete_subtopic(subtopic_id: int, db: Session = Depends(get_db)):
    sub = db.get(Subtopic, subtopic_id)
    if not sub:
        raise HTTPException(404, "Subtopic not found")
    db.delete(sub)
    db.commit()
