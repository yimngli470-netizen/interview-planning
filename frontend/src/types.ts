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
}

export interface Domain {
  id: number;
  name: string;
  color: string;
  order: number;
}

export interface StudySession {
  id: number;
  topic_id: number | null;
  date: string;
  duration_min: number;
  summary: string;
  created_at: string;
}
