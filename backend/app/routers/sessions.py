from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import StudySession, User
from ..schemas import HeartbeatOut, LoginIn, LoginOut, SessionOut, UserOut

router = APIRouter(prefix="/api", tags=["tracking"])

# If we haven't heard a heartbeat in this long, the session is considered
# abandoned (laptop closed/slept) and is finalized at its last heartbeat.
STALE_SECONDS = 120


def _is_stale(s: StudySession, now: datetime) -> bool:
    return (now - s.last_heartbeat_at).total_seconds() > STALE_SECONDS


def _finalize(s: StudySession, end: datetime) -> None:
    s.ended_at = end
    s.duration_min = max(0, round((end - s.started_at).total_seconds() / 60))


def _close_if_open(s: StudySession, now: datetime) -> None:
    """Finalize an open session: at `now` if still live, else at last heartbeat."""
    if s.ended_at is None:
        _finalize(s, s.last_heartbeat_at if _is_stale(s, now) else now)


def _finalize_stale_for_user(db: Session, user_id: int, now: datetime) -> None:
    open_sessions = db.scalars(
        select(StudySession).where(
            StudySession.user_id == user_id, StudySession.ended_at.is_(None)
        )
    ).all()
    changed = False
    for s in open_sessions:
        if _is_stale(s, now):
            _finalize(s, s.last_heartbeat_at)
            changed = True
    if changed:
        db.commit()


def _to_out(s: StudySession, now: datetime) -> SessionOut:
    active = s.ended_at is None
    if active:
        # live elapsed (capped at last heartbeat if it has gone stale)
        end = s.last_heartbeat_at if _is_stale(s, now) else now
        duration = max(0, round((end - s.started_at).total_seconds() / 60))
    else:
        duration = s.duration_min
    return SessionOut(
        id=s.id,
        user_id=s.user_id,
        started_at=s.started_at,
        ended_at=s.ended_at,
        date=s.date,
        duration_min=duration,
        active=active,
    )


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.id)).all()


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(404, "User not found")
    now = datetime.utcnow()
    # close any previously-open sessions so only one is active at a time
    for s in db.scalars(
        select(StudySession).where(
            StudySession.user_id == user.id, StudySession.ended_at.is_(None)
        )
    ).all():
        _close_if_open(s, now)
    session = StudySession(
        user_id=user.id, started_at=now, last_heartbeat_at=now, date=now.date()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return LoginOut(user=user, session=_to_out(session, now))


@router.post("/logout", response_model=SessionOut)
def logout(payload: dict, db: Session = Depends(get_db)):
    session_id = payload.get("session_id")
    s = db.get(StudySession, session_id) if session_id else None
    if not s:
        raise HTTPException(404, "Session not found")
    now = datetime.utcnow()
    if s.ended_at is None:
        _finalize(s, now if not _is_stale(s, now) else s.last_heartbeat_at)
        db.commit()
        db.refresh(s)
    return _to_out(s, now)


@router.post("/sessions/{session_id}/heartbeat", response_model=HeartbeatOut)
def heartbeat(session_id: int, db: Session = Depends(get_db)):
    s = db.get(StudySession, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    now = datetime.utcnow()
    if s.ended_at is not None:
        return HeartbeatOut(active=False, session=_to_out(s, now))
    if _is_stale(s, now):
        # laptop slept/closed since last beat — finalize, tell client to restart
        _finalize(s, s.last_heartbeat_at)
        db.commit()
        db.refresh(s)
        return HeartbeatOut(active=False, session=_to_out(s, now))
    s.last_heartbeat_at = now
    db.commit()
    db.refresh(s)
    return HeartbeatOut(active=True, session=_to_out(s, now))


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(user_id: int, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    _finalize_stale_for_user(db, user_id, now)
    sessions = db.scalars(
        select(StudySession)
        .where(StudySession.user_id == user_id)
        .order_by(StudySession.started_at.desc())
    ).all()
    return [_to_out(s, now) for s in sessions]
