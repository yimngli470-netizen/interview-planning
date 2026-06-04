from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Topic
from ..schemas import STATUSES, TopicCreate, TopicOut, TopicUpdate

router = APIRouter(prefix="/api/topics", tags=["topics"])


def _validate_status(status: str | None):
    if status is not None and status not in STATUSES:
        raise HTTPException(422, f"status must be one of {sorted(STATUSES)}")


@router.get("", response_model=list[TopicOut])
def list_topics(domain_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Topic)
    if domain_id is not None:
        stmt = stmt.where(Topic.domain_id == domain_id)
    stmt = stmt.order_by(Topic.domain_id, Topic.priority, Topic.id)
    return db.scalars(stmt).all()


@router.post("", response_model=TopicOut, status_code=201)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)):
    _validate_status(payload.status)
    data = payload.model_dump()
    # default priority = append to end of its domain
    if not data.get("priority"):
        max_p = db.scalar(
            select(func.coalesce(func.max(Topic.priority), 0)).where(
                Topic.domain_id == data["domain_id"]
            )
        )
        data["priority"] = (max_p or 0) + 1
    topic = Topic(**data)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.patch("/{topic_id}", response_model=TopicOut)
def update_topic(topic_id: int, payload: TopicUpdate, db: Session = Depends(get_db)):
    _validate_status(payload.status)
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(topic, k, v)
    db.commit()
    db.refresh(topic)
    return topic


@router.delete("/{topic_id}", status_code=204)
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found")
    db.delete(topic)
    db.commit()
