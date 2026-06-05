from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, SessionLocal
from .routers import domains, topics, subtopics, sessions
from .seed import seed_or_enrich


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase 1: create tables directly. Swap for Alembic once the schema settles.
    Base.metadata.create_all(bind=engine)
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
app.include_router(sessions.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
