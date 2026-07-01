from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import StudySession, User
from ..schemas import (
    HeartbeatOut, LoginIn, LoginOut, SessionOut, SignupIn, StartSessionIn, UserOut,
)
from ..security import hash_password, verify_password

router = APIRouter(prefix="/api", tags=["tracking"])

# No heartbeat at all for this long => the client dropped (laptop closed/slept).
STALE_SECONDS = 120
# Heartbeats arriving but the client reports the user idle/away for this long =>
# finalize the session. Counted time is always capped at the last ACTIVE beat, so
# this only controls when we close the block, never how much time is counted.
IDLE_GRACE_SECONDS = 120


def _is_stale(s: StudySession, now: datetime) -> bool:
    """Connection lost — no heartbeat (of any kind) for STALE_SECONDS."""
    return (now - s.last_heartbeat_at).total_seconds() > STALE_SECONDS


def _finalize(s: StudySession, end: datetime) -> None:
    s.ended_at = end
    s.duration_min = max(0, round((end - s.started_at).total_seconds() / 60))


def _close_if_open(s: StudySession, now: datetime) -> None:
    """Finalize an open session, always capping at the last real activity."""
    if s.ended_at is None:
        _finalize(s, s.last_active_at)


def _finalize_stale_for_user(db: Session, user_id: int, now: datetime) -> None:
    open_sessions = db.scalars(
        select(StudySession).where(
            StudySession.user_id == user_id, StudySession.ended_at.is_(None)
        )
    ).all()
    changed = False
    for s in open_sessions:
        if _is_stale(s, now):
            _finalize(s, s.last_active_at)
            changed = True
    if changed:
        db.commit()


def _to_out(s: StudySession, now: datetime) -> SessionOut:
    active = s.ended_at is None
    if active:
        # Counted time runs to the last ACTIVE beat — idle/away beats don't extend
        # it, so a tab left open (or a stale client) can't inflate the duration.
        duration = max(0, round((s.last_active_at - s.started_at).total_seconds() / 60))
    else:
        duration = s.duration_min
    return SessionOut(
        id=s.id,
        user_id=s.user_id,
        started_at=s.started_at,
        last_active_at=s.last_active_at,
        ended_at=s.ended_at,
        date=s.date,
        duration_min=duration,
        active=active,
    )


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.id)).all()


def _open_session(db: Session, user: User) -> tuple[StudySession, datetime]:
    """Close any open block for the user and start a fresh one."""
    now = datetime.utcnow()
    for s in db.scalars(
        select(StudySession).where(
            StudySession.user_id == user.id, StudySession.ended_at.is_(None)
        )
    ).all():
        _close_if_open(s, now)
    session = StudySession(
        user_id=user.id, started_at=now, last_heartbeat_at=now, last_active_at=now,
        date=now.date(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session, now


def _find_user_by_name(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.name) == username.strip().lower()))


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = _find_user_by_name(db, payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect username or password")
    session, now = _open_session(db, user)
    return LoginOut(user=user, session=_to_out(session, now))


@router.post("/signup", response_model=LoginOut, status_code=201)
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    username = payload.username.strip()
    if not username:
        raise HTTPException(422, "Username is required")
    if _find_user_by_name(db, username):
        raise HTTPException(409, "That username is already taken")
    user = User(name=username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    session, now = _open_session(db, user)
    return LoginOut(user=user, session=_to_out(session, now))


@router.post("/sessions/start", response_model=SessionOut)
def start_session(payload: StartSessionIn, db: Session = Depends(get_db)):
    """Open a new study block for an already-signed-in client (idle-resume) —
    no re-authentication, mirroring the existing browser-trust model."""
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(404, "User not found")
    session, now = _open_session(db, user)
    return _to_out(session, now)


@router.post("/logout", response_model=SessionOut)
def logout(payload: dict, db: Session = Depends(get_db)):
    session_id = payload.get("session_id")
    s = db.get(StudySession, session_id) if session_id else None
    if not s:
        raise HTTPException(404, "Session not found")
    now = datetime.utcnow()
    if s.ended_at is None:
        # Clicking sign-out is itself activity, unless the connection already went
        # stale — then cap at the last real activity.
        if not _is_stale(s, now):
            s.last_active_at = now
        _finalize(s, s.last_active_at)
        db.commit()
        db.refresh(s)
    return _to_out(s, now)


@router.post("/sessions/{session_id}/heartbeat", response_model=HeartbeatOut)
def heartbeat(
    session_id: int,
    payload: dict | None = Body(default=None),
    db: Session = Depends(get_db),
):
    s = db.get(StudySession, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    now = datetime.utcnow()
    if s.ended_at is not None:
        return HeartbeatOut(active=False, session=_to_out(s, now))

    # The client reports whether the user is actually present. A missing flag
    # (old/stale client) is treated as NOT present, so it can never accrue time.
    present = bool(payload.get("active", False)) if isinstance(payload, dict) else False

    # A long gap since the LAST beat means the client was dormant — laptop asleep/
    # closed, tab discarded, machine off. That whole gap is not study time. Finalize
    # the block at the last real activity and make the client open a fresh one. This
    # MUST run before advancing last_active_at: otherwise a single present beat after
    # a 26h sleep (e.g. the reload path sends active=true while the tab is visible)
    # would set last_active_at = now and retroactively count the entire gap.
    if _is_stale(s, now):
        _finalize(s, s.last_active_at)
        db.commit()
        db.refresh(s)
        return HeartbeatOut(active=False, session=_to_out(s, now))

    s.last_heartbeat_at = now  # connection liveness, regardless of presence
    if present:
        s.last_active_at = now

    # Finalize if the user has been idle/away too long. Caps at last_active_at,
    # so the idle stretch contributes nothing to the counted duration.
    if (now - s.last_active_at).total_seconds() > IDLE_GRACE_SECONDS:
        _finalize(s, s.last_active_at)
        db.commit()
        db.refresh(s)
        return HeartbeatOut(active=False, session=_to_out(s, now))

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


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    s = db.get(StudySession, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    db.delete(s)
    db.commit()
