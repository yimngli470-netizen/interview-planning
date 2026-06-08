import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from .. import llm
from ..database import get_db
from ..models import Domain, Question, Subtopic, Topic
from ..schemas import STATUSES, TopicCreate, TopicOut, TopicUpdate, to_subtopic_out

log = logging.getLogger(__name__)

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
    out.subtopics = [to_subtopic_out(s) for s in _visible_subtopics(topic, user_id)]
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


def _autofill_topic(db: Session, topic: Topic, user_id: int) -> None:
    """Best-effort: ask Claude for learning points + questions and attach them
    to this (user-owned) topic. Any failure leaves the topic without AI content."""
    dom = db.get(Domain, topic.domain_id)
    content = llm.generate_topic_content(topic.title, dom.name if dom else "")
    if not content:
        return
    try:
        order = 0
        for lp in content.get("learning_points", []):
            title = (lp.get("title") or "").strip()
            if not title:
                continue
            order += 1
            resources = lp.get("resources") or []
            db.add(Subtopic(
                topic_id=topic.id, owner_id=user_id, title=title[:500],
                notes=lp.get("details", "") or "",
                explanation=lp.get("explanation", "") or "",
                resources_json=json.dumps(resources) if resources else "",
                order=order, status="not-started",
            ))
        q_order = 0
        for kind, key in (("example", "example_questions"), ("common", "common_questions")):
            for prompt in content.get(key, []):
                p = (prompt or "").strip()
                if not p:
                    continue
                q_order += 1
                db.add(Question(topic_id=topic.id, kind=kind, prompt=p[:1000], order=q_order))
        db.commit()
    except Exception:
        log.exception("AI autofill: failed to persist content for topic %s", topic.id)
        db.rollback()


@router.post("", response_model=TopicOut, status_code=201)
def create_topic(
    payload: TopicCreate,
    user_id: int | None = None,
    autofill: bool = False,
    db: Session = Depends(get_db),
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
    if autofill and user_id is not None and llm.ai_configured():
        _autofill_topic(db, topic, user_id)
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
