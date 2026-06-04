from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

STATUSES = {"not-started", "in-progress", "done"}


# ---------- Subtopic (learning point) ----------
class SubtopicBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    notes: str = ""
    status: str = "not-started"
    order: int = 0
    pinned: bool = False


class SubtopicCreate(SubtopicBase):
    pass


class SubtopicUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    status: str | None = None
    order: int | None = None
    pinned: bool | None = None


class SubtopicOut(SubtopicBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    topic_id: int


# ---------- Topic ----------
class TopicBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    notes: str = ""
    status: str = "not-started"
    priority: int = 0
    effort_hours: int = 4
    pinned: bool = False


class TopicCreate(TopicBase):
    domain_id: int


class TopicUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    status: str | None = None
    priority: int | None = None
    effort_hours: int | None = None
    pinned: bool | None = None
    domain_id: int | None = None


class TopicOut(TopicBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    domain_id: int
    subtopics: list[SubtopicOut] = []


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


# ---------- Session ----------
class SessionBase(BaseModel):
    topic_id: int | None = None
    date: date
    duration_min: int = 0
    summary: str = ""


class SessionCreate(SessionBase):
    pass


class SessionOut(SessionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
