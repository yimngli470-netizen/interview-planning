from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Question, QuestionProgress, User
from ..schemas import QuestionProgressIn, QuestionProgressOut

router = APIRouter(prefix="/api/users", tags=["progress"])


@router.get("/{user_id}/question-progress", response_model=list[QuestionProgressOut])
def get_progress(user_id: int, db: Session = Depends(get_db)):
    if not db.get(User, user_id):
        raise HTTPException(404, "User not found")
    # all rows (done and/or with notes) so the client has both flags + notes
    return db.scalars(
        select(QuestionProgress).where(QuestionProgress.user_id == user_id)
    ).all()


@router.put("/{user_id}/question-progress", response_model=QuestionProgressOut)
def set_progress(
    user_id: int, payload: QuestionProgressIn, db: Session = Depends(get_db)
):
    if not db.get(User, user_id):
        raise HTTPException(404, "User not found")
    if not db.get(Question, payload.question_id):
        raise HTTPException(404, "Question not found")
    row = db.scalar(
        select(QuestionProgress).where(
            QuestionProgress.user_id == user_id,
            QuestionProgress.question_id == payload.question_id,
        )
    )
    if row is None:
        row = QuestionProgress(user_id=user_id, question_id=payload.question_id)
        db.add(row)
    if payload.done is not None:
        row.done = payload.done
    if payload.notes is not None:
        row.notes = payload.notes
    db.commit()
    db.refresh(row)
    return row
