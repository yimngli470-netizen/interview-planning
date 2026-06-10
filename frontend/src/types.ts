export type Status = 'not-started' | 'in-progress' | 'done';

export type Level = '' | 'foundational' | 'intermediate' | 'advanced';

export interface Resource {
  title: string;
  url: string; // empty => link to a search for `query` instead
  kind: 'video' | 'course' | 'article' | 'docs' | 'book';
  query: string;
}

export interface Subtopic {
  id: number;
  topic_id: number;
  title: string;
  notes: string;
  explanation: string; // long-form markdown (KaTeX + mermaid); the "learn more" body
  resources: Resource[];
  status: Status;
  order: number;
  pinned: boolean;
  owner_id: number | null; // null = default/shared (read-only); set = user's own
}

export type QuestionKind = 'example' | 'common';

export interface Question {
  id: number;
  topic_id: number;
  kind: QuestionKind;
  prompt: string;
  order: number;
  owner_id: number | null; // null = default/shared (read-only); set = user's own
}

export interface Topic {
  id: number;
  domain_id: number;
  title: string;
  notes: string;
  status: Status;
  priority: number;
  path_order: number; // pedagogical sequence within domain (0 = unset)
  level: Level;
  effort_hours: number;
  pinned: boolean;
  owner_id: number | null; // null = default/shared (read-only); set = user's own
  subtopics: Subtopic[];
  questions: Question[];
}

export interface Domain {
  id: number;
  name: string;
  color: string;
  order: number;
}

export interface User {
  id: number;
  name: string;
}

export interface StudySession {
  id: number;
  user_id: number;
  started_at: string; // naive UTC ISO (no tz suffix)
  ended_at: string | null;
  date: string;
  duration_min: number;
  active: boolean;
}
