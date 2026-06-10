# Forge — Interview Prep

A personal interview-prep planner + learning/note-taking platform for a senior
SDE / MLE loop. Track topics across domains (Coding, System Design, AI Infra,
AI/ML, Mock Interviews, Projects), break each into **learning points** and
**practice questions**, follow a curated learning path, and log your study time.

> A forge turns raw metal into something stronger through heat and repetition —
> same idea here: steady reps that temper your skills for the interview loop.

(The repo dir is still `interview-planning`; the product is "Forge".)

## Highlights

- **Curated default content** across the six domains — read-only and shared,
  with a per-domain **learning path** (what to study first) and Foundational /
  Intermediate / Advanced level chips.
- **Rich learning points** — each default point has a long-form markdown
  **"Learn more"** explanation (KaTeX math + Mermaid diagrams) and 1–3 free
  external resources. On-demand **"Explain simpler" / "Go deeper"** buttons
  generate (and permanently cache) extra explanations via Claude.
- **Make it yours** — add your own topics, learning points, and **common
  questions** on top of the shared content (your additions are private to you,
  even when attached to a default topic). Optional AI auto-fill writes the
  learning points + practice questions for a new topic.
- **Per-user accounts** — defaults are shared; your own items and progress are
  scoped to you.
- **Progress + time tracking** — Not Started / In Progress / Done on topics,
  points, and questions; auto-recorded study sessions (idle-aware); a dashboard
  with per-domain progress, streak, and logged time.

## Stack

- **Backend:** FastAPI + SQLAlchemy 2.0 + Postgres
- **Frontend:** React + Vite + TypeScript + Tailwind
- **AI:** Anthropic Claude (`claude-sonnet-4-6`) for auto-fill + explanations
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

On first boot the DB is created, migrated (lightweight additive `ALTER`s), and
seeded with the default topic plan. Seeding is idempotent and additive — your
own edits are never clobbered.

### Enabling AI

AI auto-fill and the explain buttons need an Anthropic API key. The recommended
way keeps the key out of the repo by reading it from the macOS Keychain:

```bash
# store once (you are prompted to paste the key; it is not echoed)
security add-generic-password -U -a "$USER" -s forge-anthropic-api-key -w

# then launch via the wrapper instead of `docker compose`
./scripts/run.sh up -d --build
```

Alternatively, set `ANTHROPIC_API_KEY` in `.env` (gitignored). Without a key the
app runs fine — AI features are simply disabled.

## Layout

```
backend/app/
  main.py            FastAPI app + lifespan (create tables, migrate, seed)
  database.py        engine / session
  models.py          Domain, Topic, Subtopic, Question, ExplainCache,
                     User, QuestionProgress, StudySession
  schemas.py         Pydantic request/response models
  llm.py             Claude calls (auto-fill, explain, domain ordering)
  seed.py            default plan + additive enrich/merge of curated content
  content*.py        curated / LLM-generated / hand-authored default content
  routers/           domains, topics, subtopics, questions, sessions,
                     progress, ai
backend/scripts/
  _enrich.py         one-off batch that LLM-enriches the default content
frontend/src/
  App.tsx            state + data loading + mutations + auth/session
  lib/api.ts         typed fetch client
  lib/Markdown.tsx   markdown renderer (KaTeX + Mermaid)
  components/        Dashboard, TopicsView, TopicRow, SessionsView
scripts/run.sh       launch with the API key pulled from the macOS Keychain
```

## Ownership model

Every Topic / Subtopic / Question carries an `owner_id`:

- `NULL` → **default/curated** content: shared and read-only (only your
  *progress* — status/pins — can change).
- set → **your own** item: only you see it, and only you can edit or delete it.

API endpoints take a `user_id` query param to scope listing (defaults + your
own) and authorize mutations.

See `CLAUDE.md` for the full current state, data model, and next steps.
