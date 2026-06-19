"""Anthropic (Claude) integration for auto-filling topic content.

Given a topic title + domain, generate learning points and practice/common
questions. Two interchangeable backends, selected by ``LLM_PROVIDER``:

* ``api`` (default, prod/servers) — the Anthropic Python SDK with a forced
  tool-use call for reliable structured output. Reads ``ANTHROPIC_API_KEY``;
  billed against API credits.
* ``subscription`` (local dev only) — shells out to the Claude Code CLI
  (``claude -p``) authenticated with ``CLAUDE_CODE_OAUTH_TOKEN`` (mint via
  ``claude setup-token``). Billed against your Claude Max/Pro plan, not credits.
  Headless ``claude -p`` can't force a custom tool, so the structured paths ask
  for schema-conforming JSON and parse it.

Inert until the selected provider is configured — ``ai_configured()`` gates the
feature, so the app boots fine with neither secret set.
"""

import json
import logging
import os
import shutil
import subprocess

log = logging.getLogger(__name__)

# api -> Anthropic API (credits); subscription -> Claude Code CLI (Max/Pro plan).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "api").strip().lower()

# Default to Sonnet for high-quality, comprehensive content; override with
# ANTHROPIC_MODEL (e.g. claude-haiku-4-5 for cheaper/faster, claude-opus-4-8 for
# the best). On the api path, MAX_TOKENS must be <= the model's max output
# (Sonnet 4.6 = 128k, Haiku 4.5 = 64k) — lower it if you switch to Haiku. The
# subscription path manages output length itself, so MAX_TOKENS is ignored there.
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "100000"))

_TOOL = {
    "name": "save_topic_content",
    "description": "Save the generated study content for the interview-prep topic.",
    "input_schema": {
        "type": "object",
        "properties": {
            "learning_points": {
                "type": "array",
                "description": (
                    "ALL the key learning points needed to fully cover this topic — as many as "
                    "are genuinely important. Do NOT cap the count: a narrow topic might need 4-5, "
                    "a broad one 15-20+. Include every important sub-concept, technique, tradeoff, "
                    "and gotcha rather than artificially summarizing into a fixed number."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Short name of the learning point"},
                        "details": {
                            "type": "string",
                            "description": "2-4 sentences of specific, concrete detail (numbers, tradeoffs, examples) — not generic. This is the terse HEADLINE summary.",
                        },
                        "explanation": {
                            "type": "string",
                            "description": (
                                "A longer, beginner-friendly MARKDOWN explanation of this point for an "
                                "engineer NOT already expert in this domain. Structure it: (1) a plain-English "
                                "intro of what it is and why it matters, (2) the intuition / a concrete analogy, "
                                "(3) the formal/technical details. Use markdown: headings, bullet lists, and "
                                "`inline code`. For math use KaTeX ($…$ inline, $$…$$ display) — e.g. "
                                "$\\text{softmax}(QK^\\top/\\sqrt{d_k})V$. For diagrams use a ```mermaid``` fenced "
                                "code block (flowchart/sequence/graph) — these render as real diagrams, so prefer "
                                "them over describing a picture. Do NOT embed images. Aim for 150-400 words."
                            ),
                        },
                        "resources": {
                            "type": "array",
                            "description": (
                                "1-3 high-quality FREE learning resources for this point. Only include a `url` "
                                "if you are confident it is a real, stable link (canonical sources like "
                                "3Blue1Brown, Andrej Karpathy, Stanford CS courses, official docs, well-known "
                                "blogs). If unsure, leave url empty and give a precise `query` to search instead "
                                "— never invent a URL."
                            ),
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "description": "Resource name, e.g. 'Karpathy — Let's build GPT'"},
                                    "url": {"type": "string", "description": "Direct URL ONLY if confidently real/stable; else empty."},
                                    "kind": {"type": "string", "enum": ["video", "course", "article", "docs", "book"]},
                                    "query": {"type": "string", "description": "Search query to find it (used when url is empty)."},
                                },
                                "required": ["title", "kind", "query"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["title", "details", "explanation", "resources"],
                    "additionalProperties": False,
                },
            },
            "example_questions": {
                "type": "array",
                "description": (
                    "Concrete practice questions. For Coding, list LeetCode problems as "
                    "'<Name> (LC <number>)'. For System Design, list real designs (e.g. "
                    "'Design Uber'). Otherwise, applied scenario questions."
                ),
                "items": {"type": "string"},
            },
            "common_questions": {
                "type": "array",
                "description": "Common conceptual interview questions on this topic.",
                "items": {"type": "string"},
            },
        },
        "required": ["learning_points", "example_questions", "common_questions"],
        "additionalProperties": False,
    },
}

_SYSTEM = (
    "You generate high-quality study content for a SENIOR-level SDE/MLE interview-prep "
    "app (frontier AI labs). Be specific and technical: include numbers, tradeoffs, and "
    "concrete worked examples. No fluff, no filler. Be COMPREHENSIVE: cover the entire "
    "topic with as many learning points as it genuinely warrants — never cap or pad to a "
    "fixed number. It is better to have 20 well-chosen points than to omit important ones."
)


def ai_configured() -> bool:
    """True if the selected provider is usable.

    api          -> ANTHROPIC_API_KEY set.
    subscription -> CLAUDE_CODE_OAUTH_TOKEN set AND the `claude` CLI is on PATH.
    """
    if LLM_PROVIDER == "subscription":
        return bool(os.getenv("CLAUDE_CODE_OAUTH_TOKEN", "").strip()) and shutil.which("claude") is not None
    return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())


# --- transport: api (Anthropic SDK) -----------------------------------------

def _api_tool_call(system: str, user: str, tool: dict, tool_name: str, max_tokens: int) -> dict | None:
    """Forced tool-use call → the tool's input dict (guaranteed structured)."""
    try:
        from anthropic import Anthropic  # lazy: app boots without the dep
    except Exception:
        log.warning("anthropic SDK not installed; skipping AI call")
        return None
    try:
        client = Anthropic()  # reads ANTHROPIC_API_KEY from env
        # Stream: required once max_tokens is large (a non-streaming request would
        # be rejected for timeout risk). get_final_message() reassembles the blocks.
        with client.messages.stream(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool_name},
            messages=[{"role": "user", "content": user}],
        ) as stream:
            msg = stream.get_final_message()
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use" and block.name == tool_name:
                return block.input  # type: ignore[return-value]
        log.warning("api call: no %s tool_use block in response", tool_name)
        return None
    except Exception:
        log.exception("api tool call failed")
        return None


def _api_text_call(system: str, user: str, max_tokens: int) -> str | None:
    try:
        from anthropic import Anthropic
    except Exception:
        log.warning("anthropic SDK not installed; skipping AI call")
        return None
    try:
        client = Anthropic()
        with client.messages.stream(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            msg = stream.get_final_message()
        text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text").strip()
        return text or None
    except Exception:
        log.exception("api text call failed")
        return None


# --- transport: subscription (Claude Code CLI, billed to Max/Pro plan) -------

def _claude_cli(prompt: str, *, timeout: int = 600) -> str | None:
    """One-shot headless `claude -p` call; returns the assistant text or None.

    Auth is the CLAUDE_CODE_OAUTH_TOKEN already in the process env (the CLI reads
    it), so this bills against the Claude Code subscription, not API credits.
    """
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--model", MODEL]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        log.warning("`claude` CLI not found on PATH; cannot run subscription call")
        return None
    except subprocess.TimeoutExpired:
        log.warning("claude CLI timed out after %ss", timeout)
        return None
    except Exception:
        log.exception("claude CLI invocation failed")
        return None
    if r.returncode != 0:
        log.warning("claude CLI exited %s: %s", r.returncode, (r.stderr or "")[-500:])
        return None
    # `--output-format json` emits a single result envelope: {is_error, result, ...}
    try:
        env = json.loads(r.stdout)
    except Exception:
        log.warning("claude CLI: stdout was not JSON")
        return None
    if env.get("is_error"):
        log.warning("claude CLI reported error: %s", str(env.get("result"))[:300])
        return None
    result = env.get("result")
    return result if isinstance(result, str) else None


def _extract_json(text: str | None) -> dict | None:
    """Pull the JSON object out of model text, tolerating a wrapping ```json fence
    and stray prose. Uses raw_decode from the first '{' so it parses ONE JSON value
    and ignores anything after it (e.g. a trailing ``` fence) — and, being a real
    parser, it isn't fooled by braces or ``` fences INSIDE string values (our
    `explanation` fields legitimately contain KaTeX `{...}` and ```mermaid``` blocks)."""
    if not text:
        return None
    start = text.find("{")
    if start < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _subscription_structured(system: str, user: str, schema: dict) -> dict | None:
    """Ask the CLI for schema-conforming JSON and parse it (the dev-path stand-in
    for the api path's forced tool-use)."""
    prompt = (
        f"{system}\n\n{user}\n\n"
        "Answer directly; do not use any tools. Return ONLY a single JSON object "
        "conforming to this JSON Schema — no prose, no explanation, no markdown "
        "code fences, just the raw JSON:\n"
        f"{json.dumps(schema)}"
    )
    data = _extract_json(_claude_cli(prompt))
    if data is None:
        log.warning("subscription call returned no parseable JSON object")
    return data


def _subscription_text(system: str, user: str) -> str | None:
    text = _claude_cli(f"{system}\n\n{user}\n\nAnswer directly in Markdown; do not use any tools.")
    return (text or "").strip() or None


# --- public API --------------------------------------------------------------

def generate_topic_content(topic_title: str, domain_name: str) -> dict | None:
    """Return {learning_points: [{title, details, explanation, resources}],
    example_questions: [...], common_questions: [...]} or None if AI is
    unconfigured or the call fails."""
    if not ai_configured():
        return None
    user = (
        f"Domain: {domain_name}\nTopic: {topic_title}\n\n"
        "Produce study content for this exact topic:\n"
        "1) ALL the key learning points needed to fully cover the topic — as many as are "
        "genuinely important (do NOT cap the number). For EACH point give: a short title, 2-4 "
        "sentences of specific detail (the headline summary), a longer beginner-friendly markdown "
        "`explanation` (intro → intuition/analogy → formal, with KaTeX math and ```mermaid``` "
        "diagrams where helpful), and 1-3 free `resources`.\n"
        "2) example practice questions (see the field descriptions for the format per domain).\n"
        "3) common conceptual interview questions."
    )
    if LLM_PROVIDER == "subscription":
        return _subscription_structured(_SYSTEM, user, _TOOL["input_schema"])
    return _api_tool_call(_SYSTEM, user, _TOOL, "save_topic_content", MAX_TOKENS)


# --- on-demand "explain this" (B4: a simpler or deeper take, per learning point) ---

_EXPLAIN_SYSTEM = (
    "You are a patient expert tutor for an interview-prep app. Explain the requested "
    "learning point in clear MARKDOWN. Use headings, bullet lists, and `inline code` where "
    "useful. For math use KaTeX ($…$ inline, $$…$$ display). For diagrams use a ```mermaid``` "
    "fenced code block (they render as real diagrams) — never embed images. Be concrete: real "
    "numbers, tradeoffs, worked examples. No filler."
)


def explain_learning_point(
    point_title: str, topic_title: str, domain_name: str, mode: str = "simpler"
) -> str | None:
    """Generate an on-demand markdown explanation of one learning point.
    mode='simpler' → for someone new to the domain; 'deeper' → advanced detail.
    Returns markdown text, or None if AI is unconfigured / the call fails."""
    if not ai_configured():
        return None
    if mode == "deeper":
        ask = (
            "Give an ADVANCED, in-depth explanation: edge cases, the underlying math/derivation, "
            "implementation details, performance tradeoffs, and how it connects to related ideas."
        )
    else:
        ask = (
            "Explain this so an engineer with NO background in this domain can understand it: start "
            "with plain-English intuition and a concrete analogy before any formalism, and define jargon."
        )
    user = f"Domain: {domain_name}\nTopic: {topic_title}\nLearning point: {point_title}\n\n{ask}"
    if LLM_PROVIDER == "subscription":
        return _subscription_text(_EXPLAIN_SYSTEM, user)
    return _api_text_call(_EXPLAIN_SYSTEM, user, 4096)


# --- per-domain ordering pass (Issue 1: learning path + level for each topic) ---

_ORDER_SYSTEM = "You design pedagogical learning sequences for technical interview prep."

_ORDER_TOOL = {
    "name": "save_learning_path",
    "description": "Save the pedagogical learning-path ordering + difficulty level for the domain's topics.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ordered_topics": {
                "type": "array",
                "description": (
                    "EVERY input topic, reordered into the sequence a newcomer to the domain should "
                    "study them (prerequisites/foundations first, advanced last). Include each title "
                    "EXACTLY as given."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "The topic title, byte-identical to the input."},
                        "level": {
                            "type": "string",
                            "enum": ["foundational", "intermediate", "advanced"],
                            "description": "Difficulty tier on the learning curve.",
                        },
                    },
                    "required": ["title", "level"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["ordered_topics"],
        "additionalProperties": False,
    },
}


def order_domain(domain_name: str, titles: list[str]) -> list[dict] | None:
    """Return [{title, level}] in pedagogical order, or None on failure."""
    if not ai_configured() or not titles:
        return None
    listing = "\n".join(f"- {t}" for t in titles)
    user = (
        f"Domain: {domain_name}\n\nHere are the study topics in this domain:\n{listing}\n\n"
        "Order them into a sensible LEARNING PATH for an engineer new to this domain — foundations "
        "and prerequisites first, advanced/specialized topics last — and tag each with a difficulty "
        "level (foundational / intermediate / advanced). Include every topic exactly once, with its "
        "title byte-identical to the input."
    )
    if LLM_PROVIDER == "subscription":
        data = _subscription_structured(_ORDER_SYSTEM, user, _ORDER_TOOL["input_schema"])
        return data.get("ordered_topics") if data else None
    out = _api_tool_call(_ORDER_SYSTEM, user, _ORDER_TOOL, "save_learning_path", 8192)
    return out.get("ordered_topics") if out else None
