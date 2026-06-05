import { useState, useEffect, useCallback } from 'react';
import { BarChart3, BookOpen, Calendar, Loader2, AlertTriangle } from 'lucide-react';
import type { Domain, Topic, StudySession, Status, Subtopic } from './types';
import { api } from './lib/api';
import Dashboard from './components/Dashboard';
import TopicsView from './components/TopicsView';
import SessionsView from './components/SessionsView';

type Tab = 'dashboard' | 'topics' | 'sessions';

export default function App() {
  const [tab, setTab] = useState<Tab>('dashboard');
  const [domains, setDomains] = useState<Domain[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [sessions, setSessions] = useState<StudySession[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Topics-tab filters live here (not in TopicsView) so they persist across
  // tab switches instead of resetting when the view unmounts.
  const [topicSearch, setTopicSearch] = useState('');
  const [topicDomainFilter, setTopicDomainFilter] = useState<number | 'all'>('all');
  const [topicStatusFilter, setTopicStatusFilter] = useState<string>('all');

  const reloadTopics = useCallback(async () => {
    setTopics(await api.listTopics());
  }, []);
  const reloadSessions = useCallback(async () => {
    setSessions(await api.listSessions());
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const [d, t, s] = await Promise.all([
          api.listDomains(),
          api.listTopics(),
          api.listSessions(),
        ]);
        setDomains(d);
        setTopics(t);
        setSessions(s);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load data');
      } finally {
        setLoaded(true);
      }
    })();
  }, []);

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
  const cycleTopicStatus = (t: Topic, next: Status) => patchTopic(t.id, { status: next });

  // --- subtopic (learning point) mutations ---
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

  // --- session mutations ---
  const addSession = async (s: Partial<StudySession>) => {
    await api.createSession(s);
    await reloadSessions();
  };
  const removeSession = async (id: number) => {
    await api.deleteSession(id);
    await reloadSessions();
  };

  if (!loaded) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="mb-4">
            <h1 className="text-xl font-semibold">SWE / MLE Interview Prep</h1>
            <p className="text-sm text-slate-500">Senior SDE / MLE @ frontier AI labs</p>
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
            onCycleStatus={cycleTopicStatus}
          />
        )}

        {tab === 'topics' && (
          <TopicsView
            domains={domains}
            topics={topics}
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
            domains={domains}
            topics={topics}
            sessions={sessions}
            onAddSession={addSession}
            onRemoveSession={removeSession}
          />
        )}
      </main>
    </div>
  );
}
