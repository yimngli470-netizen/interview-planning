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
  notes: string;
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

  // AI auto-fill availability
  aiStatus: () => req<{ configured: boolean }>('/ai/status'),

  // Topics (user-scoped: defaults + that user's own; defaults are read-only)
  listTopics: (userId: number) => req<Topic[]>(`/topics?user_id=${userId}`),
  createTopic: (userId: number, t: Partial<Topic>, autofill = false) =>
    req<Topic>(`/topics?user_id=${userId}&autofill=${autofill ? 'true' : 'false'}`, {
      method: 'POST',
      body: JSON.stringify(t),
    }),
  updateTopic: (userId: number, id: number, t: Partial<Topic>) =>
    req<Topic>(`/topics/${id}?user_id=${userId}`, { method: 'PATCH', body: JSON.stringify(t) }),
  deleteTopic: (userId: number, id: number) =>
    req<void>(`/topics/${id}?user_id=${userId}`, { method: 'DELETE' }),

  // Subtopics (learning points)
  createSubtopic: (userId: number, topicId: number, s: Partial<Subtopic>) =>
    req<Subtopic>(`/topics/${topicId}/subtopics?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify(s),
    }),
  updateSubtopic: (userId: number, id: number, s: Partial<Subtopic>) =>
    req<Subtopic>(`/subtopics/${id}?user_id=${userId}`, { method: 'PATCH', body: JSON.stringify(s) }),
  deleteSubtopic: (userId: number, id: number) =>
    req<void>(`/subtopics/${id}?user_id=${userId}`, { method: 'DELETE' }),

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
  deleteSession: (id: number) =>
    req<void>(`/sessions/${id}`, { method: 'DELETE' }),

  // Question progress (per user)
  getProgress: (userId: number) =>
    req<QuestionProgress[]>(`/users/${userId}/question-progress`),
  setProgress: (
    userId: number,
    questionId: number,
    patch: { done?: boolean; notes?: string },
  ) =>
    req<QuestionProgress>(`/users/${userId}/question-progress`, {
      method: 'PUT',
      body: JSON.stringify({ question_id: questionId, ...patch }),
    }),
};
