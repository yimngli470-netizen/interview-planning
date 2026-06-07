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
                            "description": "2-4 sentences of specific, concrete detail (numbers, tradeoffs, examples) — not generic.",
                        },
                    },
                    "required": ["title", "details"],
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
        "genuinely important (do NOT cap the number), each a short title + 2-4 sentences of "
        "specific detail.\n"
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
