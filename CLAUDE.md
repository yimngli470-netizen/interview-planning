# Interview Planning — project state

Personal interview-prep planner + learning/note-taking platform for a senior
SDE/MLE loop. Phase 1 = personal use, fully local in Docker.

## Stack & how to run

- Backend: FastAPI + SQLAlchemy 2.0 + Postgres (`backend/`)
- Frontend: React + Vite + TS + Tailwind (`frontend/`)
- `docker compose up --build` → frontend :5173, API :8000 (`/docs`), Postgres host :5433.
- `cp .env.example .env` first (defaults work).

## Data model

`Domain` 1—* `Topic` 1—* `Subtopic` (a "learning point", carries its own notes).
`StudySession` references a topic (nullable, SET NULL on delete).
Status is a string on Topic and Subtopic: `not-started | in-progress | done`,
validated at the API layer (`schemas.STATUSES`).

## Content

- `backend/app/content.py` = single source of truth for the curated prep
  content: 62 topics, ~347 learning points with detailed notes (numbers,
  tradeoffs, worked examples). Deep on System Design / AI Infra / AI/ML
  (~6-8 points each); crisper on Coding / Mock / Projects (~4-6).
- To add/edit content, edit `content.py` and restart the backend — the enricher
  tops up the DB on the next start. Topic titles for the original 56 must stay
  byte-identical so they match existing rows.

## Conventions

- Tables are created via `Base.metadata.create_all` in the FastAPI lifespan
  (Phase 1). **No Alembic yet** — add migrations once the schema settles.
- `backend/app/seed.py::seed_or_enrich()` runs on EVERY startup and is fully
  idempotent: creates missing domains/topics/learning points, backfills a
  topic's notes only when empty, never overwrites edits. `TOPICS` holds the base
  56 (priority/effort/pinned for fresh installs); `content.py` adds points +
  extra topics.
- Frontend: **always `import type` for interfaces** (Vite/`verbatimModuleSyntax`
  otherwise throws a runtime SyntaxError).
- Domain colors are Tailwind hue names stored on the row (`blue`, `violet`, …);
  applied via `domainClasses()` and safelisted in `tailwind.config.js`.
- All topic/subtopic mutations refetch topics (`reloadTopics`) — simple and
  correct for single-user Phase 1; optimize later if needed.

## Phase 1 status: COMPLETE (initial build + content)

Topics CRUD, learning points (subtopics) with per-point notes + status,
status cycling, pinning, dashboard (domain progress / streak / logged hours),
session log. DB seeded + enriched from `content.py` (62 topics / ~347 points).

## Next / backlog

- AI-generated learning points: given a topic + weekly goal, auto-list the key
  points to learn (user's stated vision). Will need the Claude API.
- Track-pad-friendly drawing board for diagrams (explicitly **out of Phase 1**).
- Drag-to-reorder topics & learning points (currently order via priority/order int).
- Markdown rendering for notes.
- Alembic migrations once schema stabilizes.
- Export/share progress summary (existed in idea.ts prototype; not yet ported).
