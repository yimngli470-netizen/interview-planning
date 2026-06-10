from datetime import datetime, date

from sqlalchemy import (
    String, Integer, Boolean, Text, ForeignKey, Date, DateTime, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

# status is a free string constrained at the API layer: not-started | in-progress | done


class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(60), default="slate")
    order: Mapped[int] = mapped_column(Integer, default=0)

    topics: Mapped[list["Topic"]] = relationship(
        back_populates="domain",
        cascade="all, delete-orphan",
        order_by="Topic.priority",
    )


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(
        ForeignKey("domains.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="not-started")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    # pedagogical sequence within a domain (1,2,3…; 0 = unset). Drives the
    # "Learning path" sort so a newcomer knows what to study first.
    path_order: Mapped[int] = mapped_column(Integer, default=0)
    # difficulty tier for the curve at a glance: foundational|intermediate|advanced|""
    level: Mapped[str] = mapped_column(String(20), default="")
    effort_hours: Mapped[int] = mapped_column(Integer, default=4)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    # NULL = default/curated content (shared, read-only). Set = a user's own
    # topic (only they see it; only they can edit/delete it).
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    domain: Mapped["Domain"] = relationship(back_populates="topics")
    subtopics: Mapped[list["Subtopic"]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan",
        order_by="Subtopic.order",
    )
    questions: Mapped[list["Question"]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan",
        order_by="Question.order",
    )


class Subtopic(Base):
    """A key learning point within a topic — each carries its own notes."""

    __tablename__ = "subtopics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    # long-form markdown explanation (intro → intuition → formal), may contain
    # KaTeX math ($…$) and ```mermaid``` diagrams. The terse `notes` stays the
    # headline; this is the expandable "learn more" body.
    explanation: Mapped[str] = mapped_column(Text, default="")
    # JSON array of {title, url, kind, query} curated free learning resources.
    resources_json: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="not-started")
    order: Mapped[int] = mapped_column(Integer, default=0)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    # NULL = default/curated learning point (shared, read-only). Set = a user's
    # own learning point (only they see + edit + delete it).
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    topic: Mapped["Topic"] = relationship(back_populates="subtopics")


class Question(Base):
    """A practice / interview question attached to a topic (shared content).

    kind: 'example' (a concrete problem — LeetCode #, 'Design Uber') or
          'common' (a conceptual interview question).
    """

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(20), default="example")
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    # NULL = default/curated question (shared, read-only). Set = a user's own
    # question (only they see + edit + delete it) — they can attach their own
    # common questions even onto a shared default topic.
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    topic: Mapped["Topic"] = relationship(back_populates="questions")


class ExplainCache(Base):
    """Persistent cache of on-demand 'explain simpler / go deeper' results, keyed
    by (subtopic, mode). The explanation of a learning point is the same for every
    user, so the first request generates it and all later ones (any user, any
    session) are served from here — no repeat LLM call."""

    __tablename__ = "explain_cache"
    __table_args__ = (UniqueConstraint("subtopic_id", "mode"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subtopic_id: Mapped[int] = mapped_column(
        ForeignKey("subtopics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False)  # simpler | deeper
    markdown: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class QuestionProgress(Base):
    """Per-user completion of a practice question."""

    __tablename__ = "question_progress"
    __table_args__ = (UniqueConstraint("user_id", "question_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")  # user's answer/notes


class StudySession(Base):
    """Auto-recorded study time block: created on login, kept alive by
    heartbeats, finalized on logout (or when heartbeats go stale)."""

    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # connection liveness — advances on EVERY heartbeat (detects a dropped client)
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # last beat where the client reported the user actually present. Counted time
    # runs started_at -> last_active_at, so idle beats (or a stale client that
    # sends no presence flag) can never accrue phantom minutes.
    last_active_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    # minutes; populated when the session is finalized
    duration_min: Mapped[int] = mapped_column(Integer, default=0)
