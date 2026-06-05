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

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Domain, Question, Subtopic, Topic, User
from .content import CONTENT_BY_DOMAIN, QUESTIONS

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

            # learning points — add any that don't already exist on this topic
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

    # --- users ---
    existing_users = {u.name for u in db.scalars(select(User)).all()}
    for name in DEFAULT_USERS:
        if name not in existing_users:
            db.add(User(name=name))

    db.commit()
