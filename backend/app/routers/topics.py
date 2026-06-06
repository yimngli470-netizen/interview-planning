from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Subtopic, Topic
from ..schemas import STATUSES, SubtopicOut, TopicCreate, TopicOut, TopicUpdate

router = APIRouter(prefix="/api/topics", tags=["topics"])

# Fields a user may change on DEFAULT (owner_id IS NULL) content — progress /
# preference only. Everything else on a default is read-only.
DEFAULT_TOPIC_EDITABLE = {"status", "pinned"}


def _validate_status(status: str | None):
    if status is not None and status not in STATUSES:
        raise HTTPException(422, f"status must be one of {sorted(STATUSES)}")


def _visible_subtopics(topic: Topic, user_id: int | None) -> list[Subtopic]:
    return [
        s for s in topic.subtopics if s.owner_id is None or s.owner_id == user_id
    ]


def _serialize(topic: Topic, user_id: int | None) -> TopicOut:
    out = TopicOut.model_validate(topic)
    out.subtopics = [SubtopicOut.model_validate(s) for s in _visible_subtopics(topic, user_id)]
    return out


@router.get("", response_model=list[TopicOut])
def list_topics(
    user_id: int | None = None,
    domain_id: int | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Topic)
    if domain_id is not None:
        stmt = stmt.where(Topic.domain_id == domain_id)
    # default topics (owner NULL) + this user's own topics
    if user_id is None:
        stmt = stmt.where(Topic.owner_id.is_(None))
    else:
        stmt = stmt.where(or_(Topic.owner_id.is_(None), Topic.owner_id == user_id))
    stmt = stmt.order_by(Topic.domain_id, Topic.priority, Topic.id)
    return [_serialize(t, user_id) for t in db.scalars(stmt).all()]


@router.post("", response_model=TopicOut, status_code=201)
def create_topic(
    payload: TopicCreate, user_id: int | None = None, db: Session = Depends(get_db)
):
    _validate_status(payload.status)
    data = payload.model_dump()
    if not data.get("priority"):
        max_p = db.scalar(
            select(func.coalesce(func.max(Topic.priority), 0)).where(
                Topic.domain_id == data["domain_id"]
            )
        )
        data["priority"] = (max_p or 0) + 1
    topic = Topic(**data, owner_id=user_id)  # user-created topic
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return _serialize(topic, user_id)


@router.patch("/{topic_id}", response_model=TopicOut)
def update_topic(
    topic_id: int,
    payload: TopicUpdate,
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    _validate_status(payload.status)
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found")
    fields = payload.model_dump(exclude_unset=True)
    if topic.owner_id is None:
        # default/curated topic — only progress/preference fields are editable
        bad = set(fields) - DEFAULT_TOPIC_EDITABLE
        if bad:
            raise HTTPException(403, f"Default content is read-only (can't change {sorted(bad)})")
    elif topic.owner_id != user_id:
        raise HTTPException(403, "You can only edit your own topics")
    for k, v in fields.items():
        setattr(topic, k, v)
    db.commit()
    db.refresh(topic)
    return _serialize(topic, user_id)


@router.delete("/{topic_id}", status_code=204)
def delete_topic(
    topic_id: int, user_id: int | None = None, db: Session = Depends(get_db)
):
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found")
    if topic.owner_id is None:
        raise HTTPException(403, "Default content can't be deleted")
    if topic.owner_id != user_id:
        raise HTTPException(403, "You can only delete your own topics")
    db.delete(topic)
    db.commit()
