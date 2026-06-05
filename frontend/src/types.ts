export type Status = 'not-started' | 'in-progress' | 'done';

export interface Subtopic {
  id: number;
  topic_id: number;
  title: string;
  notes: string;
  status: Status;
  order: number;
  pinned: boolean;
}

export type QuestionKind = 'example' | 'common';

export interface Question {
  id: number;
  topic_id: number;
  kind: QuestionKind;
  prompt: string;
  order: number;
}

export interface Topic {
  id: number;
  domain_id: number;
  title: string;
  notes: string;
  status: Status;
  priority: number;
  effort_hours: number;
  pinned: boolean;
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
