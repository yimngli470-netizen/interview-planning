"""Anthropic (Claude) integration for auto-filling topic content.

Given a topic title + domain, generate learning points and practice/common
questions via a single forced tool-use call (reliable structured output).
Inert until ANTHROPIC_API_KEY is set — `ai_configured()` gates the feature.
"""

import logging
import os

log = logging.getLogger(__name__)

# Default to Sonnet for high-quality, comprehensive content; override with
# ANTHROPIC_MODEL (e.g. claude-haiku-4-5 for cheaper/faster, claude-opus-4-8 for
# the best). Note: MAX_TOKENS must be <= the chosen model's max output (Sonnet 4.6
# = 128k, Haiku 4.5 = 64k) — lower it if you switch to Haiku.
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
    return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())


def generate_topic_content(topic_title: str, domain_name: str) -> dict | None:
    """Return {learning_points: [{title, details}], example_questions: [...],
    common_questions: [...]} or None if AI is unconfigured or the call fails."""
    if not ai_configured():
        return None
    try:
        from anthropic import Anthropic  # imported lazily so the app boots without the dep configured
    except Exception:
        log.warning("anthropic SDK not installed; skipping AI autofill")
        return None

    user = (
        f"Domain: {domain_name}\nTopic: {topic_title}\n\n"
        "Produce study content for this exact topic:\n"
        "1) ALL the key learning points needed to fully cover the topic — as many as are "
        "genuinely important (do NOT cap the number). For EACH point give: a short title, 2-4 "
        "sentences of specific detail (the headline summary), a longer beginner-friendly markdown "
        "`explanation` (intro → intuition/analogy → formal, with KaTeX math and ```mermaid``` "
        "diagrams where helpful), and 1-3 free `resources`.\n"
        "2) example practice questions (see the tool's field description for the format per domain).\n"
        "3) common conceptual interview questions.\n"
        "Call the save_topic_content tool with your result."
    )
    try:
        client = Anthropic()  # reads ANTHROPIC_API_KEY from env
        # Stream: required once max_tokens is large (a non-streaming request would be
        # rejected for timeout risk). get_final_message() reassembles the tool_use block.
        with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,  # headroom for comprehensive, uncapped learning-point lists
            system=_SYSTEM,
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "save_topic_content"},
            messages=[{"role": "user", "content": user}],
        ) as stream:
            msg = stream.get_final_message()
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use" and block.name == "save_topic_content":
                return block.input  # type: ignore[return-value]
        log.warning("AI autofill: no tool_use block in response")
        return None
    except Exception:
        log.exception("AI autofill call failed")
        return None


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
    try:
        from anthropic import Anthropic
    except Exception:
        log.warning("anthropic SDK not installed; skipping explain")
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
    user = (
        f"Domain: {domain_name}\nTopic: {topic_title}\nLearning point: {point_title}\n\n{ask}"
    )
    try:
        client = Anthropic()
        with client.messages.stream(
            model=MODEL,
            max_tokens=4096,
            system=_EXPLAIN_SYSTEM,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            msg = stream.get_final_message()
        parts = [b.text for b in msg.content if getattr(b, "type", None) == "text"]
        text = "".join(parts).strip()
        return text or None
    except Exception:
        log.exception("explain_learning_point call failed")
        return None


# --- per-domain ordering pass (Issue 1: learning path + level for each topic) ---

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
    try:
        from anthropic import Anthropic
    except Exception:
        return None
    listing = "\n".join(f"- {t}" for t in titles)
    user = (
        f"Domain: {domain_name}\n\nHere are the study topics in this domain:\n{listing}\n\n"
        "Order them into a sensible LEARNING PATH for an engineer new to this domain — foundations "
        "and prerequisites first, advanced/specialized topics last — and tag each with a difficulty "
        "level (foundational / intermediate / advanced). Include every topic exactly once, with its "
        "title byte-identical to the input. Call save_learning_path."
    )
    try:
        client = Anthropic()
        with client.messages.stream(
            model=MODEL,
            max_tokens=8192,
            system="You design pedagogical learning sequences for technical interview prep.",
            tools=[_ORDER_TOOL],
            tool_choice={"type": "tool", "name": "save_learning_path"},
            messages=[{"role": "user", "content": user}],
        ) as stream:
            msg = stream.get_final_message()
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use" and block.name == "save_learning_path":
                return block.input.get("ordered_topics")  # type: ignore[union-attr]
        return None
    except Exception:
        log.exception("order_domain call failed")
        return None
