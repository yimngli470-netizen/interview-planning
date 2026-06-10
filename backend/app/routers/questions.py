from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Question, Topic
from ..schemas import QUESTION_KINDS, QuestionCreate, QuestionOut, QuestionUpdate

router = APIRouter(prefix="/api", tags=["questions"])


def _validate_kind(kind: str) -> str:
    if kind not in QUESTION_KINDS:
        raise HTTPException(422, f"kind must be one of {sorted(QUESTION_KINDS)}")
    return kind


@router.post(
    "/topics/{topic_id}/questions", response_model=QuestionOut, status_code=201
)
def create_question(
    topic_id: int,
    payload: QuestionCreate,
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Add a user-owned practice question (default: a 'common' interview question)
    to a topic. The question is private to the user, even on a shared default topic."""
    if user_id is None:
        raise HTTPException(401, "Sign in to add your own questions")
    if not db.get(Topic, topic_id):
        raise HTTPException(404, "Topic not found")
    kind = _validate_kind(payload.kind)
    order = payload.order
    if not order:
        max_o = db.scalar(
            select(func.coalesce(func.max(Question.order), 0)).where(
                Question.topic_id == topic_id
            )
        )
        order = (max_o or 0) + 1
    q = Question(
        topic_id=topic_id, owner_id=user_id, kind=kind,
        prompt=payload.prompt.strip()[:1000], order=order,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.patch("/questions/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    payload: QuestionUpdate,
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.get(Question, question_id)
    if not q:
        raise HTTPException(404, "Question not found")
    if q.owner_id is None:
        raise HTTPException(403, "Default question is read-only")
    if q.owner_id != user_id:
        raise HTTPException(403, "You can only edit your own questions")
    fields = payload.model_dump(exclude_unset=True)
    if "prompt" in fields and fields["prompt"] is not None:
        fields["prompt"] = fields["prompt"].strip()[:1000]
    for k, v in fields.items():
        setattr(q, k, v)
    db.commit()
    db.refresh(q)
    return q


@router.delete("/questions/{question_id}", status_code=204)
def delete_question(
    question_id: int, user_id: int | None = None, db: Session = Depends(get_db)
):
    q = db.get(Question, question_id)
    if not q:
        raise HTTPException(404, "Question not found")
    if q.owner_id is None:
        raise HTTPException(403, "Default question can't be deleted")
    if q.owner_id != user_id:
        raise HTTPException(403, "You can only delete your own questions")
    db.delete(q)
    db.commit()
