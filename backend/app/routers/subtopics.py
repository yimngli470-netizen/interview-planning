from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Subtopic, Topic
from ..schemas import STATUSES, SubtopicCreate, SubtopicOut, SubtopicUpdate

router = APIRouter(prefix="/api", tags=["subtopics"])

# On a DEFAULT (owner_id IS NULL) learning point, only progress is editable.
DEFAULT_SUBTOPIC_EDITABLE = {"status"}


def _validate_status(status: str | None):
    if status is not None and status not in STATUSES:
        raise HTTPException(422, f"status must be one of {sorted(STATUSES)}")


@router.get("/topics/{topic_id}/subtopics", response_model=list[SubtopicOut])
def list_subtopics(
    topic_id: int, user_id: int | None = None, db: Session = Depends(get_db)
):
    stmt = select(Subtopic).where(Subtopic.topic_id == topic_id)
    if user_id is None:
        stmt = stmt.where(Subtopic.owner_id.is_(None))
    else:
        stmt = stmt.where(or_(Subtopic.owner_id.is_(None), Subtopic.owner_id == user_id))
    return db.scalars(stmt.order_by(Subtopic.order, Subtopic.id)).all()


@router.post(
    "/topics/{topic_id}/subtopics", response_model=SubtopicOut, status_code=201
)
def create_subtopic(
    topic_id: int,
    payload: SubtopicCreate,
    user_id: int | None = None,
    db: Session = Depends(get_db),
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
    sub = Subtopic(topic_id=topic_id, owner_id=user_id, **data)  # user-owned point
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.patch("/subtopics/{subtopic_id}", response_model=SubtopicOut)
def update_subtopic(
    subtopic_id: int,
    payload: SubtopicUpdate,
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    _validate_status(payload.status)
    sub = db.get(Subtopic, subtopic_id)
    if not sub:
        raise HTTPException(404, "Subtopic not found")
    fields = payload.model_dump(exclude_unset=True)
    if sub.owner_id is None:
        bad = set(fields) - DEFAULT_SUBTOPIC_EDITABLE
        if bad:
            raise HTTPException(403, f"Default learning point is read-only (can't change {sorted(bad)})")
    elif sub.owner_id != user_id:
        raise HTTPException(403, "You can only edit your own learning points")
    for k, v in fields.items():
        setattr(sub, k, v)
    db.commit()
    db.refresh(sub)
    return sub


@router.delete("/subtopics/{subtopic_id}", status_code=204)
def delete_subtopic(
    subtopic_id: int, user_id: int | None = None, db: Session = Depends(get_db)
):
    sub = db.get(Subtopic, subtopic_id)
    if not sub:
        raise HTTPException(404, "Subtopic not found")
    if sub.owner_id is None:
        raise HTTPException(403, "Default learning point can't be deleted")
    if sub.owner_id != user_id:
        raise HTTPException(403, "You can only delete your own learning points")
    db.delete(sub)
    db.commit()
