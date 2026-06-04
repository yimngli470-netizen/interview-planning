# Interview Planning

A personal interview-prep planner + learning/note-taking platform for a senior
SDE / MLE loop. Track topics across domains (Coding, System Design, AI Infra,
AI/ML, Mock Interviews, Projects), break each topic into **learning points** with
their own notes, mark progress, and pin priorities.

## Stack

- **Backend:** FastAPI + SQLAlchemy 2.0 + Postgres
- **Frontend:** React + Vite + TypeScript + Tailwind
- **Dev:** Docker Compose (db + backend + frontend), all local

## Quick start

```bash
cp .env.example .env        # defaults work out of the box
docker compose up --build
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8001/docs
- Postgres: localhost:5434 (host port; 5432 inside the network)

> Host ports 8001/5434 are used (instead of 8000/5433) so this stack can run
> alongside the equity-research project without port clashes.

On first boot the DB is created and seeded with the default topic plan
(from the original `idea.ts` prototype). The seed is idempotent — it only runs
when the `domains` table is empty, so your edits are never clobbered.

## Layout

```
backend/app/
  main.py        FastAPI app + lifespan (create tables, seed)
  database.py    engine / session
  models.py      Domain, Topic, Subtopic (learning point), StudySession
  schemas.py     Pydantic request/response models
  seed.py        default plan, ported from idea.ts
  routers/       domains, topics, subtopics, sessions
frontend/src/
  App.tsx        state + data loading + mutations
  lib/api.ts     typed fetch client
  components/    Dashboard, TopicsView, TopicRow, SessionsView
```

## Phase 1 scope

- [x] Add / edit / delete topics within a domain
- [x] Learning points (subtopics) per topic, each with its own notes
- [x] Not Started / In Progress / Done on topics and learning points
- [x] Pin priorities to the top
- [x] Postgres-backed storage
- [x] Dashboard (progress by domain, streak, logged time) + session log

See `CLAUDE.md` for current state and next steps.
