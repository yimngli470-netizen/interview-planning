import { useState, useEffect, useCallback, useRef } from 'react';
import {
  BarChart3, BookOpen, Calendar, Loader2, AlertTriangle, LogIn, LogOut, Clock, Flame,
} from 'lucide-react';
import type { Domain, Topic, StudySession, Subtopic, User } from './types';
import { api } from './lib/api';
import { parseUTC, formatClock } from './lib/time';
import Dashboard from './components/Dashboard';
import TopicsView from './components/TopicsView';
import SessionsView from './components/SessionsView';

type Tab = 'dashboard' | 'topics' | 'sessions';

const AUTH_KEY = 'prep-auth-v1';
const HEARTBEAT_MS = 30_000;

interface SavedAuth {
  userId: number;
  userName: string;
  sessionId: number;
}

export default function App() {
  const [tab, setTab] = useState<Tab>('dashboard');
  const [domains, setDomains] = useState<Domain[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // auth / time tracking
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [activeSession, setActiveSession] = useState<StudySession | null>(null);
  const [sessions, setSessions] = useState<StudySession[]>([]);
  const [doneQ, setDoneQ] = useState<Set<number>>(new Set());
  const [qNotes, setQNotes] = useState<Map<number, string>>(new Map());
  const [nowTs, setNowTs] = useState(Date.now());

  // Topics-tab filters live here so they persist across tab switches.
  const [topicSearch, setTopicSearch] = useState('');
  const [topicDomainFilter, setTopicDomainFilter] = useState<number | 'all'>('all');
  const [topicStatusFilter, setTopicStatusFilter] = useState<string>('all');

  const reloadTopics = useCallback(async () => {
    setTopics(await api.listTopics());
  }, []);

  const loadUserData = useCallback(async (userId: number) => {
    const [s, p] = await Promise.all([api.listSessions(userId), api.getProgress(userId)]);
    setSessions(s);
    setDoneQ(new Set(p.filter((x) => x.done).map((x) => x.question_id)));
    setQNotes(new Map(p.filter((x) => x.notes).map((x) => [x.question_id, x.notes])));
  }, []);

  const removeSession = async (id: number) => {
    setSessions((prev) => prev.filter((s) => s.id !== id));
    try {
      await api.deleteSession(id);
    } catch {
      if (currentUser) setSessions(await api.listSessions(currentUser.id));
    }
  };

  const clearAuth = useCallback(() => {
    localStorage.removeItem(AUTH_KEY);
    setCurrentUser(null);
    setActiveSession(null);
    setSessions([]);
    setDoneQ(new Set());
    setQNotes(new Map());
  }, []);

  // --- initial load + resume a saved login ---
  useEffect(() => {
    (async () => {
      try {
        const [d, t, u] = await Promise.all([
          api.listDomains(),
          api.listTopics(),
          api.listUsers(),
        ]);
        setDomains(d);
        setTopics(t);
        setUsers(u);

        const raw = localStorage.getItem(AUTH_KEY);
        if (raw) {
          const saved: SavedAuth = JSON.parse(raw);
          try {
            const hb = await api.heartbeat(saved.sessionId);
            if (hb.active && hb.session) {
              setCurrentUser({ id: saved.userId, name: saved.userName });
              setActiveSession(hb.session);
              await loadUserData(saved.userId);
            } else {
              localStorage.removeItem(AUTH_KEY); // session ended while away
            }
          } catch {
            localStorage.removeItem(AUTH_KEY);
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load data');
      } finally {
        setLoaded(true);
      }
    })();
  }, [loadUserData]);

  // --- live clock tick while a session is active ---
  useEffect(() => {
    if (!activeSession) return;
    setNowTs(Date.now());
    const id = setInterval(() => setNowTs(Date.now()), 1000);
    return () => clearInterval(id);
  }, [activeSession]);

  // --- heartbeat while a session is active ---
  const clearAuthRef = useRef(clearAuth);
  clearAuthRef.current = clearAuth;
  useEffect(() => {
    if (!activeSession) return;
    const id = setInterval(async () => {
      try {
        const hb = await api.heartbeat(activeSession.id);
        if (!hb.active) clearAuthRef.current(); // laptop slept / went stale
      } catch {
        /* transient network error — keep trying */
      }
    }, HEARTBEAT_MS);
    return () => clearInterval(id);
  }, [activeSession]);

  // --- auth handlers ---
  const login = async (user: User) => {
    const res = await api.login(user.id);
    setCurrentUser(res.user);
    setActiveSession(res.session);
    localStorage.setItem(
      AUTH_KEY,
      JSON.stringify({ userId: res.user.id, userName: res.user.name, sessionId: res.session.id }),
    );
    await loadUserData(res.user.id);
  };
  const logout = async () => {
    if (activeSession) {
      try {
        await api.logout(activeSession.id);
      } catch {
        /* ignore */
      }
    }
    clearAuth();
  };

  // --- topic mutations ---
  const addTopic = async (domainId: number, title: string, effortHours: number) => {
    await api.createTopic({ domain_id: domainId, title, effort_hours: effortHours });
    await reloadTopics();
  };
  const patchTopic = async (id: number, patch: Partial<Topic>) => {
    await api.updateTopic(id, patch);
    await reloadTopics();
  };
  const removeTopic = async (id: number) => {
    await api.deleteTopic(id);
    await reloadTopics();
  };

  // --- subtopic mutations ---
  const addSubtopic = async (topicId: number, title: string) => {
    await api.createSubtopic(topicId, { title });
    await reloadTopics();
  };
  const patchSubtopic = async (id: number, patch: Partial<Subtopic>) => {
    await api.updateSubtopic(id, patch);
    await reloadTopics();
  };
  const removeSubtopic = async (id: number) => {
    await api.deleteSubtopic(id);
    await reloadTopics();
  };

  // --- question completion (per user) ---
  const toggleQuestion = async (questionId: number, done: boolean) => {
    if (!currentUser) return;
    setDoneQ((prev) => {
      const next = new Set(prev);
      if (done) next.add(questionId);
      else next.delete(questionId);
      return next;
    });
    try {
      await api.setProgress(currentUser.id, questionId, { done });
    } catch {
      setDoneQ((prev) => {
        const next = new Set(prev);
        if (done) next.delete(questionId);
        else next.add(questionId);
        return next;
      });
    }
  };

  const saveQuestionNotes = async (questionId: number, notes: string) => {
    if (!currentUser) return;
    setQNotes((prev) => {
      const next = new Map(prev);
      if (notes) next.set(questionId, notes);
      else next.delete(questionId);
      return next;
    });
    try {
      await api.setProgress(currentUser.id, questionId, { notes });
    } catch {
      /* keep optimistic value; will reconcile on next load */
    }
  };

  if (!loaded) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
      </div>
    );
  }

  // Login gate: content is only accessible to a logged-in user.
  if (!currentUser) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-6">
        <div className="w-full max-w-sm bg-white border border-slate-200 rounded-xl p-8 text-center shadow-sm">
          <div className="flex justify-center mb-3">
            <span className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-rose-600 text-white shadow-sm">
              <Flame className="w-6 h-6" />
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Forge</h1>
          <p className="text-sm text-slate-500 mt-1 mb-6">Senior SDE / MLE interview prep</p>
          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 text-left">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
          <div className="space-y-2">
            {users.map((u) => (
              <button
                key={u.id}
                onClick={() =>
                  login(u).catch((e) =>
                    setError(e instanceof Error ? e.message : 'Login failed'),
                  )
                }
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm bg-slate-900 text-white rounded-md hover:bg-slate-800"
              >
                <LogIn className="w-4 h-4" /> Log in as {u.name}
              </button>
            ))}
            {users.length === 0 && !error && (
              <p className="text-sm text-slate-500">No users found.</p>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-6">
            Logging in starts your study timer — your time is tracked automatically
            until you sign out or close your laptop.
          </p>
        </div>
      </div>
    );
  }

  const elapsedSec = activeSession
    ? (nowTs - parseUTC(activeSession.started_at).getTime()) / 1000
    : 0;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <span className="flex items-center justify-center w-9 h-9 rounded-lg bg-gradient-to-br from-orange-500 to-rose-600 text-white shadow-sm">
                <Flame className="w-5 h-5" />
              </span>
              <div>
                <h1 className="text-xl font-semibold leading-tight">Forge</h1>
                <p className="text-sm text-slate-500">Senior SDE / MLE interview prep</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-emerald-50 text-emerald-700 text-sm font-mono tabular-nums">
                <Clock className="w-4 h-4" />
                {formatClock(elapsedSec)}
              </div>
              <span className="text-sm text-slate-600">{currentUser.name}</span>
              <button
                onClick={logout}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-slate-200 rounded-md hover:bg-slate-50"
              >
                <LogOut className="w-4 h-4" /> Sign out
              </button>
            </div>
          </div>
          <nav className="flex gap-1">
            {([
              { id: 'dashboard', label: 'Dashboard', Icon: BarChart3 },
              { id: 'topics', label: 'Topics', Icon: BookOpen },
              { id: 'sessions', label: 'Sessions', Icon: Calendar },
            ] as const).map(({ id, label, Icon }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`flex items-center gap-2 px-3 py-2 text-sm rounded-md transition ${
                  tab === id
                    ? 'bg-slate-100 text-slate-900 font-medium'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6">
        {error && (
          <div className="mb-4 flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {tab === 'dashboard' && (
          <Dashboard
            domains={domains}
            topics={topics}
            sessions={sessions}
            currentUser={currentUser}
            nowTs={nowTs}
            onRemoveSession={removeSession}
          />
        )}

        {tab === 'topics' && (
          <TopicsView
            domains={domains}
            topics={topics}
            canTrack={!!currentUser}
            doneQuestions={doneQ}
            questionNotes={qNotes}
            onToggleQuestion={toggleQuestion}
            onSaveQuestionNotes={saveQuestionNotes}
            search={topicSearch}
            setSearch={setTopicSearch}
            domainFilter={topicDomainFilter}
            setDomainFilter={setTopicDomainFilter}
            statusFilter={topicStatusFilter}
            setStatusFilter={setTopicStatusFilter}
            onAddTopic={addTopic}
            onPatchTopic={patchTopic}
            onRemoveTopic={removeTopic}
            onAddSubtopic={addSubtopic}
            onPatchSubtopic={patchSubtopic}
            onRemoveSubtopic={removeSubtopic}
          />
        )}

        {tab === 'sessions' && (
          <SessionsView
            sessions={sessions}
            currentUser={currentUser}
            nowTs={nowTs}
          />
        )}
      </main>
    </div>
  );
}
