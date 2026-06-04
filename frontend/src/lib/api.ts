import type { Domain, Topic, Subtopic, StudySession } from '../types';

const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

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

  // Sessions
  listSessions: () => req<StudySession[]>('/sessions'),
  createSession: (s: Partial<StudySession>) =>
    req<StudySession>('/sessions', { method: 'POST', body: JSON.stringify(s) }),
  deleteSession: (id: number) =>
    req<void>(`/sessions/${id}`, { method: 'DELETE' }),
};
