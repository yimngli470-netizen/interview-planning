import json
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

STATUSES = {"not-started", "in-progress", "done"}
LEVELS = {"", "foundational", "intermediate", "advanced"}


# ---------- Learning resource (free external material) ----------
class ResourceOut(BaseModel):
    title: str = ""
    # Direct link when known-good (canonical sources); otherwise empty and the
    # client links to a search for `query` so it can never be a dead link.
    url: str = ""
    kind: str = "article"  # video | course | article | docs | book
    query: str = ""


# ---------- Subtopic (learning point) ----------
class SubtopicBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    notes: str = ""
    explanation: str = ""
    status: str = "not-started"
    order: int = 0
    pinned: bool = False


class SubtopicCreate(SubtopicBase):
    pass


class SubtopicUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    explanation: str | None = None
    resources: list[ResourceOut] | None = None
    status: str | None = None
    order: int | None = None
    pinned: bool | None = None


class SubtopicOut(SubtopicBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    topic_id: int
    owner_id: int | None = None
    resources: list[ResourceOut] = []


def to_subtopic_out(s) -> "SubtopicOut":
    """Serialize a Subtopic ORM row, parsing its JSON resources blob."""
    out = SubtopicOut.model_validate(s)
    raw = getattr(s, "resources_json", "") or ""
    if raw:
        try:
            out.resources = [ResourceOut(**r) for r in json.loads(raw)]
        except Exception:
            out.resources = []
    return out


# ---------- Topic ----------
class TopicBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    notes: str = ""
    status: str = "not-started"
    priority: int = 0
    path_order: int = 0
    level: str = ""
    effort_hours: int = 4
    pinned: bool = False


class TopicCreate(TopicBase):
    domain_id: int


class TopicUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    status: str | None = None
    priority: int | None = None
    path_order: int | None = None
    level: str | None = None
    effort_hours: int | None = None
    pinned: bool | None = None
    domain_id: int | None = None


# ---------- Question (practice / interview question) ----------
class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    topic_id: int
    kind: str
    prompt: str
    order: int


class TopicOut(TopicBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    domain_id: int
    owner_id: int | None = None
    subtopics: list[SubtopicOut] = []
    questions: list[QuestionOut] = []


# ---------- Domain ----------
class DomainBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    color: str = "slate"
    order: int = 0


class DomainCreate(DomainBase):
    pass


class DomainUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    color: str | None = None
    order: int | None = None


class DomainOut(DomainBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- User / auth ----------
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class LoginIn(BaseModel):
    user_id: int


# ---------- Study session (auto time tracking) ----------
class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    started_at: datetime
    ended_at: datetime | None
    date: date
    duration_min: int  # computed/finalized minutes
    active: bool


class LoginOut(BaseModel):
    user: UserOut
    session: SessionOut


class HeartbeatOut(BaseModel):
    active: bool
    session: SessionOut | None = None


# ---------- Question progress (per user) ----------
class QuestionProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    question_id: int
    done: bool
    notes: str


class QuestionProgressIn(BaseModel):
    question_id: int
    done: bool | None = None
    notes: str | None = None
