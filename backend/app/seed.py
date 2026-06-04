"""Seed default domains + topics on first run (idempotent).

Ported from the original idea.ts prototype. Only runs when the domains table
is empty, so it never clobbers data you've added.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Domain, Topic

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


def seed(db: Session) -> None:
    if db.scalar(select(Domain).limit(1)):
        return  # already seeded

    domain_by_name: dict[str, Domain] = {}
    for order, (name, color) in enumerate(DOMAINS):
        d = Domain(name=name, color=color, order=order)
        db.add(d)
        domain_by_name[name] = d
    db.flush()  # assign ids

    for domain_name, title, priority, effort, pinned, notes in TOPICS:
        db.add(
            Topic(
                domain_id=domain_by_name[domain_name].id,
                title=title,
                priority=priority,
                effort_hours=effort,
                pinned=pinned,
                notes=notes,
                status="not-started",
            )
        )
    db.commit()
