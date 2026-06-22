"""Seed + enrich domains, topics, and learning points (fully idempotent).

`TOPICS` below is the base plan ported from the original idea.ts prototype
(carries priority/effort/pinned for fresh installs). `content.CONTENT_BY_DOMAIN`
adds the curated learning points, richer notes, and a few extra high-value
topics. `seed_or_enrich()` runs on every startup and:
  - creates any missing domains / base topics / extra topics,
  - adds any missing learning points (matched by title within a topic),
  - backfills a topic's notes only when currently empty.
So re-running never overwrites your edits, and it tops up new content on deploy.
"""

import json
import os
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Domain, Question, Subtopic, Topic, TopicSummary, User
from .security import EMPTY_PASSWORD_HASH
from .content import CONTENT_BY_DOMAIN, QUESTIONS

try:
    # Comprehensive LLM-authored points (each with markdown explanation + free
    # resources) / questions and a per-domain learning-path ORDER
    # (app/content_generated.py), merged additively on top of the curated content
    # above. Optional — module may not exist on a fresh checkout.
    from .content_generated import GENERATED, ORDER
except Exception:  # noqa: BLE001 — module may not exist yet
    GENERATED = {}
    ORDER = {}

try:
    # Hand-authored (Opus) rich content — same shape as GENERATED but written
    # directly rather than via the API. Merged AFTER (and so wins over) GENERATED.
    from .content_authored import AUTHORED, AUTHORED_ORDER
except Exception:  # noqa: BLE001
    AUTHORED = {}
    AUTHORED_ORDER = {}

try:
    # Canonical within-topic learning-point ordering (topic title -> point titles
    # in pedagogical, grouped order), produced by scripts/_order_points.py. Applied
    # to existing DEFAULT points so related points sit together. Optional.
    from .content_point_order import POINT_ORDER
except Exception:  # noqa: BLE001
    POINT_ORDER = {}

# Distilled HTML study-notes summaries: file in app/summaries/ -> exact topic
# title it summarizes. Drop a new <name>.html in that dir, add a line here, and
# restart; the seeder ingests it into topic_summaries (idempotent, by filename).
SUMMARY_DIR = os.path.join(os.path.dirname(__file__), "summaries")
SUMMARY_MAP: dict[str, str] = {
    # 九章算法 (basics, weeks 2-9)
    "week2-binary-search-distilled.html": "Binary Search (incl. on the answer)",
    "week3-binary-tree-distilled.html": "BFS / DFS on graphs and trees",
    "week4-bfs-distilled.html": "BFS / DFS on graphs and trees",
    "week5-dfs-distilled.html": "BFS / DFS on graphs and trees",
    "week6-linkedlist-array-distilled.html": "Linked lists & in-place pointer manipulation",
    "week7-two-pointers-distilled.html": "Arrays, Hashmaps, Two Pointers — foundation patterns",
    "week8-data-structure-distilled.html": "Design data structures (LRU/LFU, iterators, stream)",
    "week9-dp-distilled.html": "Dynamic Programming — 1D, 2D, knapsack patterns",
    # Advanced (senior algorithm, chapters 1-7)
    "adv1-sliding-window-distilled.html": "Sliding Window / Prefix Sum",
    "adv2-union-find-trie-distilled.html": "Trie / Union-Find",
    "adv3-heap-stack-distilled.html": "Heap / Priority Queue patterns",
    "adv4-binary-search-sweepline-distilled.html": "Binary Search (incl. on the answer)",
    "adv5-senior-dp-1-distilled.html": "Dynamic Programming — 1D, 2D, knapsack patterns",
    "adv6-senior-dp-2-distilled.html": "Dynamic Programming — 1D, 2D, knapsack patterns",
    "adv7-follow-up-problems-distilled.html": "Implementation-heavy problems w/ evolving requirements",
}
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)

# Flagship topics authored by hand (Opus) directly in content.py — skip the
# generated/Sonnet versions for these so they stay clean (no overlap).
SKIP_GENERATED = {
    "Transformer deep dive: MHA, KV cache, RoPE, MoE routing",
    "Post-training: SFT, RLHF, DPO, RLAIF, Constitutional AI",
    "Agentic systems: tool use, planning, MCP, multi-step reasoning",
    "AI safety: alignment, interpretability, red-teaming",
    "Inference optimization: KV cache, PagedAttention, continuous batching (vLLM)",
    "Distributed training: DDP, FSDP, ZeRO-1/2/3, TP, PP",
}


def _has_depth(gen: dict) -> bool:
    return any(
        (p.get("explanation") if isinstance(p, dict) else "") for p in gen.get("points", [])
    )


# Rich content sources, lowest→highest precedence (AUTHORED wins over GENERATED).
RICH_SOURCES = (GENERATED, AUTHORED)

# Topics whose depth-bearing set is the AUTHORITATIVE, comprehensive learning-point
# list → maps title to its canonical set of point titles. For these we DON'T also
# seed the curated content.py points, and we prune any default point NOT in this
# set — otherwise curated + older-generation points (whose titles drifted) pile up
# as redundant, no-"Learn more" duplicates. v1/no-depth topics (e.g. Coding, or
# topics that failed enrichment) keep the additive behaviour. A later source
# (AUTHORED) overrides an earlier one's canonical set for the same title.
AUTHORITATIVE_POINTS: dict[str, set[str]] = {}
for _src in RICH_SOURCES:
    for _title, _gen in _src.items():
        if _title in SKIP_GENERATED or not _has_depth(_gen):
            continue
        AUTHORITATIVE_POINTS[_title] = {
            (p.get("title") or "").strip()
            for p in _gen.get("points", [])
            if (p.get("title") or "").strip()
        }
AUTHORITATIVE = set(AUTHORITATIVE_POINTS)

DEFAULT_USERS = ["Zoey", "Xiaoming"]

DOMAINS = [
    ("Coding", "blue"),
    ("System Design", "violet"),
    ("AI Infra", "emerald"),
    ("AI/ML", "amber"),
    ("Mock Interviews", "rose"),
    ("Projects", "indigo"),
]

# (domain, title, priority, effort_hours, pinned, notes)
TOPICS = [
    ("Coding", "Arrays, Hashmaps, Two Pointers — foundation patterns", 1, 8, False, ""),
    ("Coding", "BFS / DFS on graphs and trees", 2, 10, False, ""),
    ("Coding", "Dynamic Programming — 1D, 2D, knapsack patterns", 3, 15, False, ""),
    ("Coding", "Binary Search (incl. on the answer)", 4, 6, False, ""),
    ("Coding", "Implementation-heavy problems w/ evolving requirements", 5, 12, True,
     "Anthropic-style: rewards code that stays clean as constraints are added mid-interview."),
    ("Coding", "Heap / Priority Queue patterns", 6, 6, False, ""),
    ("Coding", "Sliding Window / Prefix Sum", 7, 6, False, ""),
    ("Coding", "Concurrency primitives (locks, async, threads)", 8, 8, False, ""),
    ("Coding", "Backtracking", 9, 8, False, ""),
    ("Coding", "Trie / Union-Find", 10, 6, False, ""),

    ("System Design", "Fundamentals: load balancing, caching, sharding, replication, consistency", 1, 12, True, ""),
    ("System Design", "Design LLM inference serving system (batching, KV cache, autoscaling)", 2, 10, True, ""),
    ("System Design", "Design distributed training cluster (DP/MP/PP, fault tolerance)", 3, 10, False, ""),
    ("System Design", "Design RAG pipeline w/ vector search + eval", 4, 8, False, ""),
    ("System Design", "Design agent orchestration / tool-use system", 5, 6, False, ""),
    ("System Design", "Design model evaluation / observability platform", 6, 6, False, ""),
    ("System Design", "Design rate limiter / distributed counter", 7, 4, False, ""),
    ("System Design", "Design distributed KV store / metadata service", 8, 6, False, ""),
    ("System Design", "Design streaming chat / news feed / notification system", 9, 6, False, ""),
    ("System Design", "Design URL shortener / pastebin (warmup)", 10, 4, False, ""),

    ("AI Infra", "GPU architecture: SMs, memory hierarchy, Tensor Cores, NVLink", 1, 10, True, ""),
    ("AI Infra", "Distributed training: DDP, FSDP, ZeRO-1/2/3, TP, PP", 2, 12, True, ""),
    ("AI Infra", "Inference optimization: KV cache, PagedAttention, continuous batching (vLLM)", 3, 10, True, ""),
    ("AI Infra", "CUDA programming basics: kernels, shared memory, occupancy", 4, 15, False, ""),
    ("AI Infra", "Quantization (INT8, FP8, FP4) & speculative decoding", 5, 8, False, ""),
    ("AI Infra", "FlashAttention & memory-efficient attention variants", 6, 6, False, ""),
    ("AI Infra", "NCCL collectives & communication patterns", 7, 6, False, ""),
    ("AI Infra", "Serving frameworks: Triton, TensorRT-LLM, SGLang", 8, 8, False, ""),
    ("AI Infra", "Checkpointing, fault tolerance, large-cluster observability", 9, 6, False, ""),
    ("AI Infra", "Kubernetes / SLURM for ML workloads", 10, 6, False, ""),

    ("AI/ML", "Transformer deep dive: MHA, KV cache, RoPE, MoE routing", 1, 12, True, ""),
    ("AI/ML", "Pretraining: scaling laws, data mixing, tokenization", 2, 8, False, ""),
    ("AI/ML", "Post-training: SFT, RLHF, DPO, RLAIF, Constitutional AI", 3, 10, True, ""),
    ("AI/ML", "Evaluation: benchmarks, human eval, hallucination detection", 4, 6, False, ""),
    ("AI/ML", "Agentic systems: tool use, planning, MCP, multi-step reasoning", 5, 8, True, ""),
    ("AI/ML", "AI safety: alignment, interpretability, red-teaming", 6, 8, True,
     "Critical for Anthropic — values/ethics round."),
    ("AI/ML", "RAG architectures vs fine-tuning tradeoffs", 7, 6, False, ""),
    ("AI/ML", "Probability/stats fundamentals (Bayes, MLE, distributions)", 8, 6, False, ""),
    ("AI/ML", "Classical ML refresher: regression, trees, gradient boosting", 9, 6, False, ""),
    ("AI/ML", "Diffusion models & multimodal architectures", 10, 6, False, ""),

    ("Mock Interviews", "Write 6 STAR stories (impact, ambiguity, conflict, failure, leadership, ethics)", 1, 6, True, ""),
    ("Mock Interviews", "Project deep-dive prep (20-min present + 40-min Q&A)", 2, 8, True,
     "Defend every architectural decision as if facing a skeptical senior engineer."),
    ("Mock Interviews", "5 coding mocks (45-min, no AI tools — Anthropic prohibits them)", 3, 8, True, ""),
    ("Mock Interviews", "3 system design mocks (AI-flavored: inference, RAG, training)", 4, 8, False, ""),
    ("Mock Interviews", "2 ML system design mocks (recommender / RAG / fine-tuning)", 5, 6, False, ""),
    ("Mock Interviews", "Anthropic values/ethics scenario practice", 6, 4, False, ""),
    ("Mock Interviews", "Schedule recurring mocks (Pramp / Exponent / Interviewing.io)", 7, 2, False, ""),
    ("Mock Interviews", "Record yourself & review playback", 8, 3, False, ""),

    ("Projects", "Build mini LLM inference server (continuous batching + KV cache)", 1, 30, True, ""),
    ("Projects", "Implement attention from scratch (MHA, RoPE, KV cache, masking)", 2, 15, True, ""),
    ("Projects", "Build a RAG app w/ eval harness (retrieval + groundedness metrics)", 3, 20, False, ""),
    ("Projects", "Build an agent with tool-use (MCP-style) + eval", 4, 20, False, ""),
    ("Projects", "Fine-tune a small model w/ LoRA, measure quality delta", 5, 15, False, ""),
    ("Projects", "Write a CUDA kernel (e.g., fused softmax or matmul)", 6, 25, False, ""),
    ("Projects", "Distributed training toy: DDP/FSDP on multi-GPU", 7, 20, False, ""),
    ("Projects", "Contribute to open-source ML repo (PR merged)", 8, 25, False, ""),
]


def seed_or_enrich(db: Session) -> None:
    """Idempotently ensure domains, topics, and learning points exist."""
    # --- domains ---
    domains = {d.name: d for d in db.scalars(select(Domain)).all()}
    for order, (name, color) in enumerate(DOMAINS):
        if name not in domains:
            d = Domain(name=name, color=color, order=order)
            db.add(d)
            domains[name] = d
    db.flush()

    # --- base topics (the original 56, with curated priority/effort/pinned) ---
    topics = {(t.domain_id, t.title): t for t in db.scalars(select(Topic)).all()}
    for domain_name, title, priority, effort, pinned, notes in TOPICS:
        dom = domains[domain_name]
        if (dom.id, title) not in topics:
            t = Topic(
                domain_id=dom.id,
                title=title,
                priority=priority,
                effort_hours=effort,
                pinned=pinned,
                notes=notes,
                status="not-started",
            )
            db.add(t)
    db.flush()
    topics = {(t.domain_id, t.title): t for t in db.scalars(select(Topic)).all()}

    # --- content: extra topics, note backfill, and learning points ---
    for domain_name, specs in CONTENT_BY_DOMAIN.items():
        dom = domains[domain_name]
        for spec in specs:
            title = spec["title"]
            topic = topics.get((dom.id, title))
            if topic is None:
                # a topic defined only in content.py (the extra high-value ones)
                next_priority = (
                    max(
                        (t.priority for k, t in topics.items() if k[0] == dom.id),
                        default=0,
                    )
                    + 1
                )
                topic = Topic(
                    domain_id=dom.id,
                    title=title,
                    priority=spec.get("priority") or next_priority,
                    effort_hours=spec.get("effort", 4),
                    pinned=spec.get("pinned", False),
                    notes=spec.get("notes", ""),
                    status="not-started",
                )
                db.add(topic)
                db.flush()
                topics[(dom.id, title)] = topic
            elif not topic.notes and spec.get("notes"):
                topic.notes = spec["notes"]  # backfill only when empty

            # learning points — add any that don't already exist on this topic.
            # Skipped for AUTHORITATIVE topics: the generated set owns their points
            # (prevents curated points piling up alongside the comprehensive list).
            if title not in AUTHORITATIVE:
                existing = {s.title for s in topic.subtopics}
                next_order = max((s.order for s in topic.subtopics), default=0)
                for pt_title, pt_notes in spec.get("points", []):
                    if pt_title not in existing:
                        next_order += 1
                        db.add(
                            Subtopic(
                                topic_id=topic.id,
                                title=pt_title,
                                notes=pt_notes,
                                order=next_order,
                                status="not-started",
                            )
                        )
                        existing.add(pt_title)

            # practice / interview questions (idempotent by prompt)
            qspec = QUESTIONS.get(title)
            if qspec:
                have = {q.prompt for q in topic.questions}
                q_order = max((q.order for q in topic.questions), default=0)
                # examples first, then common — order field drives display order
                for kind in ("example", "common"):
                    for prompt in qspec.get(kind, []):
                        if prompt not in have:
                            q_order += 1
                            db.add(
                                Question(
                                    topic_id=topic.id,
                                    kind=kind,
                                    prompt=prompt,
                                    order=q_order,
                                )
                            )
                            have.add(prompt)

    # --- merge rich content (GENERATED then AUTHORED; additive, default topics) ---
    by_title = {k[1]: t for k, t in topics.items() if t.owner_id is None}
    for source in RICH_SOURCES:
        for title, gen in source.items():
            if title in SKIP_GENERATED:
                continue
            topic = by_title.get(title)
            if topic is None:
                continue
            # Re-query each pass (autoflush) so a later source sees the earlier
            # source's just-added points and never double-adds.
            existing = {s.title: s for s in db.scalars(
                select(Subtopic).where(Subtopic.topic_id == topic.id)
            ).all()}
            next_order = max((s.order for s in existing.values()), default=0)
            for p in gen.get("points", []):
                pt_title = (p.get("title") or "").strip()
                if not pt_title:
                    continue
                explanation = p.get("explanation", "") or ""
                resources = p.get("resources") or []
                res_json = json.dumps(resources) if resources else ""
                if pt_title in existing:
                    # backfill depth onto an existing point only when empty, so
                    # user/hand edits are never overwritten.
                    s = existing[pt_title]
                    if explanation and not s.explanation:
                        s.explanation = explanation
                    if res_json and not (s.resources_json or ""):
                        s.resources_json = res_json
                else:
                    next_order += 1
                    ns = Subtopic(
                        topic_id=topic.id, title=pt_title, notes=p.get("notes", "") or "",
                        explanation=explanation, resources_json=res_json,
                        order=next_order, status="not-started",
                    )
                    db.add(ns)
                    existing[pt_title] = ns
            questions = db.scalars(select(Question).where(Question.topic_id == topic.id)).all()
            have = {q.prompt for q in questions}
            q_order = max((q.order for q in questions), default=0)
            for kind in ("example", "common"):
                for prompt in gen.get(kind, []):
                    if prompt and prompt not in have:
                        q_order += 1
                        db.add(Question(topic_id=topic.id, kind=kind, prompt=prompt, order=q_order))
                        have.add(prompt)

    # prune stale/duplicate default points on authoritative topics — anything not
    # in the canonical set (curated + drifted older-generation points). User-owned
    # points are never touched. Idempotent: once converged, nothing deletes.
    if AUTHORITATIVE_POINTS:
        db.flush()
        for title, keep_titles in AUTHORITATIVE_POINTS.items():
            topic = by_title.get(title)
            if topic is None or not keep_titles:
                continue
            for s in db.scalars(
                select(Subtopic).where(
                    Subtopic.topic_id == topic.id,
                    Subtopic.owner_id.is_(None),
                    Subtopic.title.notin_(keep_titles),
                )
            ).all():
                db.delete(s)

    # --- apply learning-path ordering + level (default topics) ---
    def _apply_order(order_map: dict, override: bool) -> None:
        for domain_name, items in order_map.items():
            dom = domains.get(domain_name)
            if dom is None:
                continue
            for i, it in enumerate(items, start=1):
                topic = topics.get((dom.id, it["title"]))
                if topic is None or topic.owner_id is not None:
                    continue
                if override or not topic.path_order:
                    topic.path_order = i
                if override or not topic.level:
                    topic.level = it.get("level", "") or ""

    _apply_order(ORDER, override=False)        # generated ordering: fill gaps only
    _apply_order(AUTHORED_ORDER, override=True)  # hand-authored ordering wins

    # --- apply within-topic learning-point ordering (default points) ---
    # Re-assign Subtopic.order so related points sit together (e.g. all DFS, then
    # all BFS). Only default points (owner_id IS NULL) are touched, matched by
    # exact title; titles not in the canonical list keep their relative order and
    # follow the listed ones. Fully idempotent. User-owned points are untouched.
    if POINT_ORDER:
        db.flush()
        for topic_title, ordered_titles in POINT_ORDER.items():
            topic = by_title.get(topic_title)
            if topic is None:
                continue
            subs = db.scalars(
                select(Subtopic).where(
                    Subtopic.topic_id == topic.id, Subtopic.owner_id.is_(None)
                )
            ).all()
            rank = {t: i for i, t in enumerate(ordered_titles)}
            tail = len(ordered_titles)
            # listed points by canonical rank; any unlisted point keeps its old
            # order but sorts after every listed one (stable on current order).
            for new_order, s in enumerate(
                sorted(subs, key=lambda s: (rank.get(s.title, tail), s.order)), start=1
            ):
                if s.order != new_order:
                    s.order = new_order

    # --- ingest distilled HTML study-notes summaries (idempotent, keyed by source) ---
    # Files live in app/summaries/ and ship in the image; SUMMARY_MAP attaches each
    # to its topic. Re-ingests on change (edit the HTML + restart to update).
    for fname, topic_title in SUMMARY_MAP.items():
        path = os.path.join(SUMMARY_DIR, fname)
        topic = by_title.get(topic_title)
        if topic is None or not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        m = _TITLE_RE.search(html)
        disp = (m.group(1).strip() if m else "") or topic_title
        existing = db.scalars(
            select(TopicSummary).where(TopicSummary.source == fname)
        ).first()
        if existing is None:
            db.add(TopicSummary(topic_id=topic.id, source=fname, title=disp, html=html))
        elif (existing.html, existing.topic_id, existing.title) != (html, topic.id, disp):
            existing.html, existing.topic_id, existing.title = html, topic.id, disp

    # --- users ---
    existing_users = {u.name for u in db.scalars(select(User)).all()}
    for name in DEFAULT_USERS:
        if name not in existing_users:
            db.add(User(name=name, password_hash=EMPTY_PASSWORD_HASH))  # blank password

    db.commit()
