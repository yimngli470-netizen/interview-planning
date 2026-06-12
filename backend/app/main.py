from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from .database import Base, engine, SessionLocal
from .routers import domains, topics, subtopics, questions, sessions, progress, ai
from .seed import seed_or_enrich


def _drop_legacy_sessions() -> None:
    """The old manual `sessions` table was replaced by `study_sessions`.
    Drop it if present and empty (no Alembic yet). Safe: never drops data."""
    insp = inspect(engine)
    if "sessions" in insp.get_table_names():
        with engine.begin() as conn:
            count = conn.execute(text("SELECT count(*) FROM sessions")).scalar()
            if not count:
                conn.execute(text("DROP TABLE sessions"))


def _ensure_columns(insp, tables, table: str, col_to_ddl: dict[str, str]) -> None:
    """Add each missing column on `table` via its DDL. Idempotent."""
    if table not in tables:
        return
    cols = {c["name"] for c in insp.get_columns(table)}
    for col, ddl in col_to_ddl.items():
        if col not in cols:
            with engine.begin() as conn:
                conn.execute(text(ddl))


def _add_missing_columns() -> None:
    """Lightweight, additive 'migrations' (no Alembic yet). Each is idempotent
    and non-destructive — only adds a column when it's missing."""
    insp = inspect(engine)
    tables = insp.get_table_names()
    # question_progress.notes (per-user answer/notes on a practice question)
    if "question_progress" in tables:
        cols = {c["name"] for c in insp.get_columns("question_progress")}
        if "notes" not in cols:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE question_progress ADD COLUMN notes TEXT NOT NULL DEFAULT ''")
                )
    # owner_id on topics + subtopics + questions (NULL = default/shared content)
    for tbl in ("topics", "subtopics", "questions"):
        if tbl in tables:
            cols = {c["name"] for c in insp.get_columns(tbl)}
            if "owner_id" not in cols:
                with engine.begin() as conn:
                    conn.execute(
                        text(f"ALTER TABLE {tbl} ADD COLUMN owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE")
                    )
    # users.password_hash (existing accounts get the empty-password hash so they
    # can sign in with a blank password)
    if "users" in tables:
        cols = {c["name"] for c in insp.get_columns("users")}
        if "password_hash" not in cols:
            from .security import EMPTY_PASSWORD_HASH
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(64) NOT NULL DEFAULT ''")
                )
                conn.execute(
                    text("UPDATE users SET password_hash = :h WHERE password_hash = ''"),
                    {"h": EMPTY_PASSWORD_HASH},
                )
    # learning-path ordering + level on topics; rich depth on subtopics
    _ensure_columns(insp, tables, "topics", {
        "path_order": "ALTER TABLE topics ADD COLUMN path_order INTEGER NOT NULL DEFAULT 0",
        "level": "ALTER TABLE topics ADD COLUMN level VARCHAR(20) NOT NULL DEFAULT ''",
    })
    _ensure_columns(insp, tables, "subtopics", {
        "explanation": "ALTER TABLE subtopics ADD COLUMN explanation TEXT NOT NULL DEFAULT ''",
        "resources_json": "ALTER TABLE subtopics ADD COLUMN resources_json TEXT NOT NULL DEFAULT ''",
    })
    # study_sessions.last_active_at (counted-time boundary; backfill from last_heartbeat_at)
    if "study_sessions" in tables:
        cols = {c["name"] for c in insp.get_columns("study_sessions")}
        if "last_active_at" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE study_sessions ADD COLUMN last_active_at TIMESTAMP"))
                conn.execute(text("UPDATE study_sessions SET last_active_at = last_heartbeat_at WHERE last_active_at IS NULL"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase 1: create tables directly. Swap for Alembic once the schema settles.
    _drop_legacy_sessions()
    Base.metadata.create_all(bind=engine)
    _add_missing_columns()
    db = SessionLocal()
    try:
        seed_or_enrich(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Interview Planning API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # Personal, local-network app: allow the Vite dev origin from any host
    # (localhost, 127.0.0.1, or a LAN IP like http://10.0.0.24:5173) on port
    # 5173. No cookies/credentials are used, so this is safe for LAN dev.
    allow_origin_regex=r"http://[^/]+:5173",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(domains.router)
app.include_router(topics.router)
app.include_router(subtopics.router)
app.include_router(questions.router)
app.include_router(sessions.router)
app.include_router(progress.router)
app.include_router(ai.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
