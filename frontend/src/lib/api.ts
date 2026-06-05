import type { Domain, Topic, Subtopic, StudySession, User } from '../types';

export interface LoginResult {
  user: User;
  session: StudySession;
}
export interface HeartbeatResult {
  active: boolean;
  session: StudySession | null;
}
export interface QuestionProgress {
  question_id: number;
  done: boolean;
}

// Talk to the backend on the SAME host that served this page, port 8001.
// This makes it work both locally (localhost:5173 -> localhost:8001) and from
// another device on the LAN (10.0.0.24:5173 -> 10.0.0.24:8001) without baking
// in an address. An explicit VITE_API_BASE still overrides if you set one.
const BASE =
  import.meta.env.VITE_API_BASE?.trim() ||
  `${window.location.protocol}//${window.location.hostname}:8001`;

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  // Domains
  listDomains: () => req<Domain[]>('/domains'),
  createDomain: (d: Partial<Domain>) =>
    req<Domain>('/domains', { method: 'POST', body: JSON.stringify(d) }),
  updateDomain: (id: number, d: Partial<Domain>) =>
    req<Domain>(`/domains/${id}`, { method: 'PATCH', body: JSON.stringify(d) }),
  deleteDomain: (id: number) =>
    req<void>(`/domains/${id}`, { method: 'DELETE' }),

  // Topics
  listTopics: () => req<Topic[]>('/topics'),
  createTopic: (t: Partial<Topic>) =>
    req<Topic>('/topics', { method: 'POST', body: JSON.stringify(t) }),
  updateTopic: (id: number, t: Partial<Topic>) =>
    req<Topic>(`/topics/${id}`, { method: 'PATCH', body: JSON.stringify(t) }),
  deleteTopic: (id: number) =>
    req<void>(`/topics/${id}`, { method: 'DELETE' }),

  // Subtopics (learning points)
  createSubtopic: (topicId: number, s: Partial<Subtopic>) =>
    req<Subtopic>(`/topics/${topicId}/subtopics`, {
      method: 'POST',
      body: JSON.stringify(s),
    }),
  updateSubtopic: (id: number, s: Partial<Subtopic>) =>
    req<Subtopic>(`/subtopics/${id}`, { method: 'PATCH', body: JSON.stringify(s) }),
  deleteSubtopic: (id: number) =>
    req<void>(`/subtopics/${id}`, { method: 'DELETE' }),

  // Users / auth
  listUsers: () => req<User[]>('/users'),
  login: (userId: number) =>
    req<LoginResult>('/login', { method: 'POST', body: JSON.stringify({ user_id: userId }) }),
  logout: (sessionId: number) =>
    req<StudySession>('/logout', { method: 'POST', body: JSON.stringify({ session_id: sessionId }) }),
  heartbeat: (sessionId: number) =>
    req<HeartbeatResult>(`/sessions/${sessionId}/heartbeat`, { method: 'POST' }),

  // Study sessions (auto, per user)
  listSessions: (userId: number) =>
    req<StudySession[]>(`/sessions?user_id=${userId}`),

  // Question progress (per user)
  getProgress: (userId: number) =>
    req<QuestionProgress[]>(`/users/${userId}/question-progress`),
  setProgress: (userId: number, questionId: number, done: boolean) =>
    req<QuestionProgress>(`/users/${userId}/question-progress`, {
      method: 'PUT',
      body: JSON.stringify({ question_id: questionId, done }),
    }),
};
