import { useState, useEffect, useCallback, useRef } from 'react';
import {
  ArrowRight, RefreshCw, Loader, LogOut, UserPlus, X,
  BarChart3, BookOpen, CalendarDays,
} from 'lucide-react';
import type { Domain, Topic, StudySession, Subtopic, User } from './types';
import { api } from './lib/api';
import type { LoginResult } from './lib/api';
import { parseUTC, formatClock } from './lib/time';
import { Mark } from './lib/ui';
import { QUOTES } from './lib/quotes';
import Dashboard from './components/Dashboard';
import TopicsView from './components/TopicsView';
import SessionsView from './components/SessionsView';

type Tab = 'dashboard' | 'topics' | 'sessions';

const AUTH_KEY = 'prep-auth-v1';
const HEARTBEAT_MS = 30_000;
// No real input for this long ⇒ treat the user as away: the heartbeat reports
// "not present" so the server caps the session, and the on-screen timer freezes.
// This is what stops a tab left open on an awake machine from logging phantom
// hours — while still allowing brief glances at other windows without pausing.
const IDLE_MS = 15 * 60_000;
const ACTIVITY_EVENTS = ['pointermove', 'pointerdown', 'keydown', 'wheel', 'scroll', 'touchstart'] as const;

interface SavedAuth {
  userId: number;
  userName: string;
  sessionId: number;
}

// Pull the FastAPI `detail` message out of a `req` error string for a clean toast.
function errText(msg: string, fallback: string): string {
  const m = msg.match(/"detail":"([^"]+)"/);
  return m ? m[1] : (msg || fallback);
}

function RotatingQuote() {
  const [i, setI] = useState(() => Math.floor(Math.random() * QUOTES.length));
  const [shown, setShown] = useState(true);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const fadeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const advance = useCallback(() => {
    setShown(false);
    setI((prev) => {
      let n = prev;
      while (n === prev && QUOTES.length > 1) n = Math.floor(Math.random() * QUOTES.length);
      return n;
    });
    if (fadeTimer.current) clearTimeout(fadeTimer.current);
    fadeTimer.current = setTimeout(() => setShown(true), 40);
  }, []);

  const startTimer = useCallback(() => {
    if (timer.current) clearInterval(timer.current);
    timer.current = setInterval(advance, 8500);
  }, [advance]);

  useEffect(() => {
    startTimer();
    return () => {
      if (timer.current) clearInterval(timer.current);
      if (fadeTimer.current) clearTimeout(fadeTimer.current);
    };
  }, [startTimer]);

  const q = QUOTES[i];
  return (
    <div style={{ maxWidth: 460 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 26 }}>
        <span style={{ width: 26, height: 2, background: 'var(--accent-line)', borderRadius: 2 }} />
        <span style={{ fontSize: 12, fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase', color: 'var(--accent)' }}>
          A thought before you begin
        </span>
      </div>
      <div style={{ opacity: shown ? 1 : 0, transform: shown ? 'none' : 'translateY(8px)', transition: 'opacity .55s ease, transform .55s cubic-bezier(.2,.7,.2,1)' }}>
        <blockquote className="display" style={{ margin: 0, fontSize: 34, lineHeight: 1.18, color: 'var(--text)' }}>
          <span style={{ color: 'var(--accent)', fontSize: 44, lineHeight: 0, position: 'relative', top: 10, marginRight: 2 }}>“</span>
          {q.text}
        </blockquote>
        <div style={{ marginTop: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ width: 18, height: 1.5, background: 'var(--faint)' }} />
          <cite style={{ fontStyle: 'normal', fontSize: 14.5, fontWeight: 600, color: 'var(--muted)' }}>{q.author}</cite>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 40 }}>
        <button className="btn btn-soft btn-sm" onClick={() => { advance(); startTimer(); }} title="Show another">
          <RefreshCw size={15} strokeWidth={2.2} /> Another
        </button>
        <div style={{ display: 'flex', gap: 6 }}>
          {QUOTES.slice(0, 6).map((_, k) => (
            <span key={k} style={{ width: 6, height: 6, borderRadius: 999, background: i % 6 === k ? 'var(--accent)' : 'var(--accent-line)', transition: 'background .3s ease' }} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState<Tab>('dashboard');
  const [domains, setDomains] = useState<Domain[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiConfigured, setAiConfigured] = useState(false);

  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [activeSession, setActiveSession] = useState<StudySession | null>(null);
  const [sessions, setSessions] = useState<StudySession[]>([]);
  const [doneQ, setDoneQ] = useState<Set<number>>(new Set());
  const [qNotes, setQNotes] = useState<Map<number, string>>(new Map());
  const [nowTs, setNowTs] = useState(Date.now());
  const [idle, setIdle] = useState(false);
  const lastActivityRef = useRef(Date.now());

  // Auth form state
  const [authUser, setAuthUser] = useState('');
  const [authPass, setAuthPass] = useState('');
  const [authBusy, setAuthBusy] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [suUser, setSuUser] = useState('');
  const [suPass, setSuPass] = useState('');

  const [topicSearch, setTopicSearch] = useState('');
  const [topicDomainFilter, setTopicDomainFilter] = useState<number | 'all'>('all');
  const [topicStatusFilter, setTopicStatusFilter] = useState<string>('all');

  const reloadTopics = useCallback(async (userId: number) => {
    setTopics(await api.listTopics(userId));
  }, []);

  const loadUserData = useCallback(async (userId: number) => {
    const [t, s, p] = await Promise.all([
      api.listTopics(userId),
      api.listSessions(userId),
      api.getProgress(userId),
    ]);
    setTopics(t);
    setSessions(s);
    setDoneQ(new Set(p.filter((x) => x.done).map((x) => x.question_id)));
    setQNotes(new Map(p.filter((x) => x.notes).map((x) => [x.question_id, x.notes])));
  }, []);

  const clearAuth = useCallback(() => {
    localStorage.removeItem(AUTH_KEY);
    setCurrentUser(null);
    setActiveSession(null);
    setSessions([]);
    setTopics([]);
    setDoneQ(new Set());
    setQNotes(new Map());
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const [d, ai] = await Promise.all([api.listDomains(), api.aiStatus()]);
        setDomains(d);
        setAiConfigured(ai.configured);
        const raw = localStorage.getItem(AUTH_KEY);
        if (raw) {
          const saved: SavedAuth = JSON.parse(raw);
          try {
            const hb = await api.heartbeat(saved.sessionId, !document.hidden);
            if (hb.active && hb.session) {
              setCurrentUser({ id: saved.userId, name: saved.userName });
              setActiveSession(hb.session);
              await loadUserData(saved.userId);
            } else {
              localStorage.removeItem(AUTH_KEY);
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

  // "Away" = no real interaction with the page for IDLE_MS (15 min). Simply
  // looking at another window/tab does NOT pause the session — only genuine
  // inactivity does. (A backgrounded tab fires no input events, so it still
  // idles out naturally after 15 min; returning to the tab counts as activity.)
  const isAway = () => Date.now() - lastActivityRef.current > IDLE_MS;

  // Track real presence: any input — or the tab/window regaining focus — is "here".
  useEffect(() => {
    if (!activeSession) return;
    lastActivityRef.current = Date.now();
    const mark = () => { lastActivityRef.current = Date.now(); };
    const onVisible = () => { if (!document.hidden) mark(); };
    for (const ev of ACTIVITY_EVENTS) window.addEventListener(ev, mark, { passive: true });
    window.addEventListener('focus', mark);
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      for (const ev of ACTIVITY_EVENTS) window.removeEventListener(ev, mark);
      window.removeEventListener('focus', mark);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [activeSession]);

  useEffect(() => {
    if (!activeSession) return;
    const tick = () => {
      setNowTs(Date.now());
      setIdle(isAway());
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [activeSession]);

  const clearAuthRef = useRef(clearAuth);
  clearAuthRef.current = clearAuth;
  const currentUserRef = useRef(currentUser);
  currentUserRef.current = currentUser;
  useEffect(() => {
    if (!activeSession) return;
    const id = setInterval(async () => {
      // Always beat, but tell the server whether the user is actually present.
      // The server only counts time up to the last "present" beat, so an idle/
      // away tab (or a stale client) can't accrue phantom minutes.
      const present = !isAway();
      try {
        const hb = await api.heartbeat(activeSession.id, present);
        if (!hb.active && present) {
          // The server finalized the block (idle/stale) but the user is active
          // again — start a fresh session instead of logging out. If not present,
          // leave it finalized; we'll start a new block when activity resumes.
          const u = currentUserRef.current;
          if (!u) { clearAuthRef.current(); return; }
          const session = await api.startSession(u.id);
          setActiveSession(session);
          lastActivityRef.current = Date.now();
          localStorage.setItem(AUTH_KEY, JSON.stringify({ userId: u.id, userName: u.name, sessionId: session.id }));
        }
      } catch {
        /* transient */
      }
    }, HEARTBEAT_MS);
    return () => clearInterval(id);
  }, [activeSession]);

  const applyAuth = useCallback(async (res: LoginResult) => {
    setCurrentUser(res.user);
    setActiveSession(res.session);
    localStorage.setItem(AUTH_KEY, JSON.stringify({ userId: res.user.id, userName: res.user.name, sessionId: res.session.id }));
    await loadUserData(res.user.id);
  }, [loadUserData]);

  const submitLogin = async () => {
    if (authBusy || !authUser.trim()) return;
    setAuthBusy(true); setError(null);
    try {
      await applyAuth(await api.login(authUser.trim(), authPass));
    } catch (e) {
      setError(e instanceof Error ? errText(e.message, 'Login failed') : 'Login failed');
    } finally {
      setAuthBusy(false);
    }
  };

  const submitSignup = async () => {
    if (authBusy || !suUser.trim()) return;
    setAuthBusy(true); setError(null);
    try {
      await applyAuth(await api.signup(suUser.trim(), suPass));
      setShowSignup(false);
    } catch (e) {
      setError(e instanceof Error ? errText(e.message, 'Sign up failed') : 'Sign up failed');
    } finally {
      setAuthBusy(false);
    }
  };
  const logout = async () => {
    if (activeSession) {
      try { await api.logout(activeSession.id); } catch { /* ignore */ }
    }
    clearAuth();
  };

  // topic mutations (user-scoped; default content is rejected server-side)
  const addTopic = async (domainId: number, title: string, effortHours: number, autofill: boolean) => {
    if (!currentUser) return;
    await api.createTopic(currentUser.id, { domain_id: domainId, title, effort_hours: effortHours }, autofill);
    await reloadTopics(currentUser.id);
  };
  const patchTopic = async (id: number, patch: Partial<Topic>) => {
    if (!currentUser) return;
    await api.updateTopic(currentUser.id, id, patch);
    await reloadTopics(currentUser.id);
  };
  const removeTopic = async (id: number) => {
    if (!currentUser) return;
    await api.deleteTopic(currentUser.id, id);
    await reloadTopics(currentUser.id);
  };

  const addSubtopic = async (topicId: number, title: string) => {
    if (!currentUser) return;
    await api.createSubtopic(currentUser.id, topicId, { title });
    await reloadTopics(currentUser.id);
  };
  const patchSubtopic = async (id: number, patch: Partial<Subtopic>) => {
    if (!currentUser) return;
    await api.updateSubtopic(currentUser.id, id, patch);
    await reloadTopics(currentUser.id);
  };
  const removeSubtopic = async (id: number) => {
    if (!currentUser) return;
    await api.deleteSubtopic(currentUser.id, id);
    await reloadTopics(currentUser.id);
  };

  const addQuestion = async (topicId: number, prompt: string, kind: 'example' | 'common') => {
    if (!currentUser) return;
    await api.createQuestion(currentUser.id, topicId, { prompt, kind });
    await reloadTopics(currentUser.id);
  };
  const editQuestion = async (id: number, prompt: string) => {
    if (!currentUser) return;
    await api.updateQuestion(currentUser.id, id, { prompt });
    await reloadTopics(currentUser.id);
  };
  const removeQuestion = async (id: number) => {
    if (!currentUser) return;
    await api.deleteQuestion(currentUser.id, id);
    await reloadTopics(currentUser.id);
  };

  const removeSession = async (id: number) => {
    setSessions((prev) => prev.filter((s) => s.id !== id));
    try {
      await api.deleteSession(id);
    } catch {
      if (currentUser) setSessions(await api.listSessions(currentUser.id));
    }
  };

  const toggleQuestion = async (questionId: number, done: boolean) => {
    if (!currentUser) return;
    setDoneQ((prev) => { const n = new Set(prev); done ? n.add(questionId) : n.delete(questionId); return n; });
    try {
      await api.setProgress(currentUser.id, questionId, { done });
    } catch {
      setDoneQ((prev) => { const n = new Set(prev); done ? n.delete(questionId) : n.add(questionId); return n; });
    }
  };
  const saveQuestionNotes = async (questionId: number, notes: string) => {
    if (!currentUser) return;
    setQNotes((prev) => { const n = new Map(prev); notes ? n.set(questionId, notes) : n.delete(questionId); return n; });
    try { await api.setProgress(currentUser.id, questionId, { notes }); } catch { /* keep optimistic */ }
  };

  if (!loaded) {
    return (
      <div className="app-shell" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Loader size={26} className="spin" style={{ color: 'var(--faint)' }} />
      </div>
    );
  }

  // ---------- Login gate ----------
  if (!currentUser) {
    return (
      <div className="app-shell">
        <div style={{ minHeight: '100vh', display: 'grid', gridTemplateColumns: 'minmax(0,1.15fr) minmax(0,0.85fr)' }}>
          {/* Left — inspiration */}
          <div style={{
            position: 'relative', display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
            padding: 'clamp(40px, 6vw, 80px)',
            background:
              'radial-gradient(130% 90% at 0% 0%, var(--accent-softer) 0%, transparent 50%),' +
              'radial-gradient(120% 80% at 100% 100%, var(--bg-tint) 0%, transparent 55%),' +
              'var(--bg)',
            borderRight: '1px solid var(--border)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 13 }}>
              <Mark size={46} />
              <div>
                <div className="display" style={{ fontSize: 25 }}>Forge</div>
                <div className="faint" style={{ fontSize: 12.5, fontWeight: 600, letterSpacing: '0.04em' }}>SENIOR SDE / MLE PREP</div>
              </div>
            </div>
            <RotatingQuote />
            <div className="faint" style={{ fontSize: 13, lineHeight: 1.6, maxWidth: 440 }}>
              Steady, focused reps that temper your skills for the loop. Show up, log the
              time, and let the streak do the convincing.
            </div>
          </div>

          {/* Right — sign in */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'clamp(28px, 4vw, 56px)', background: 'var(--surface)' }}>
            <div style={{ width: '100%', maxWidth: 340 }}>
              <h1 className="display" style={{ fontSize: 30, margin: '0 0 6px' }}>Welcome back</h1>
              <p className="muted" style={{ fontSize: 15, margin: '0 0 30px', lineHeight: 1.5 }}>
                Sign in to start the clock. Your session begins the moment you sign in.
              </p>
              {error && (
                <div className="card-flat" style={{ background: 'var(--danger-soft)', color: 'var(--danger)', padding: '11px 14px', fontSize: 13.5, marginBottom: 18 }}>{error}</div>
              )}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label className="faint" style={{ display: 'block', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 6 }}>Username</label>
                  <input className="field" autoFocus value={authUser} onChange={(e) => setAuthUser(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && submitLogin()} placeholder="Your username" autoComplete="username" />
                </div>
                <div>
                  <label className="faint" style={{ display: 'block', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 6 }}>Password</label>
                  <input className="field" type="password" value={authPass} onChange={(e) => setAuthPass(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && submitLogin()} placeholder="Your password" autoComplete="current-password" />
                </div>
                <button className="btn btn-primary btn-lg btn-block" style={{ justifyContent: 'center', marginTop: 4 }}
                  disabled={authBusy || !authUser.trim()} onClick={submitLogin}>
                  {authBusy && !showSignup ? <Loader size={18} className="spin" strokeWidth={2.4} /> : <>Sign in <ArrowRight size={18} strokeWidth={2.4} /></>}
                </button>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '24px 0' }}>
                <span style={{ flex: 1, height: 1, background: 'var(--border)' }} />
                <span className="faint" style={{ fontSize: 12, fontWeight: 600 }}>new here?</span>
                <span style={{ flex: 1, height: 1, background: 'var(--border)' }} />
              </div>
              <button className="btn btn-soft btn-block" style={{ justifyContent: 'center' }}
                onClick={() => { setError(null); setSuUser(''); setSuPass(''); setShowSignup(true); }}>
                <UserPlus size={17} strokeWidth={2.2} /> Create an account
              </button>
            </div>
          </div>
        </div>

        {showSignup && (
          <div onClick={() => !authBusy && setShowSignup(false)}
            style={{ position: 'fixed', inset: 0, zIndex: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, background: 'oklch(0.2 0.02 60 / 0.42)', backdropFilter: 'blur(3px)' }}>
            <div onClick={(e) => e.stopPropagation()} className="card" style={{ width: '100%', maxWidth: 400, padding: 26, boxShadow: '0 24px 60px -12px rgba(0,0,0,0.35)' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 4 }}>
                <h2 className="display" style={{ fontSize: 22, margin: 0 }}>Create an account</h2>
                <button onClick={() => setShowSignup(false)} title="Close"
                  style={{ border: 'none', background: 'transparent', color: 'var(--faint)', cursor: 'pointer', padding: 2, display: 'inline-flex' }}>
                  <X size={20} strokeWidth={2.2} />
                </button>
              </div>
              <p className="muted" style={{ fontSize: 13.5, margin: '0 0 20px', lineHeight: 1.5 }}>
                Pick a username. A password is optional — leave it blank if you like.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label className="faint" style={{ display: 'block', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 6 }}>Username</label>
                  <input className="field" autoFocus value={suUser} onChange={(e) => setSuUser(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && submitSignup()} placeholder="Choose a username" autoComplete="off" />
                </div>
                <div>
                  <label className="faint" style={{ display: 'block', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 6 }}>Password <span style={{ textTransform: 'none', fontWeight: 600 }}>(optional)</span></label>
                  <input className="field" type="password" value={suPass} onChange={(e) => setSuPass(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && submitSignup()} placeholder="Optional" autoComplete="new-password" />
                </div>
                {error && (
                  <div className="card-flat" style={{ background: 'var(--danger-soft)', color: 'var(--danger)', padding: '10px 13px', fontSize: 13 }}>{error}</div>
                )}
                <button className="btn btn-primary btn-lg btn-block" style={{ justifyContent: 'center', marginTop: 4 }}
                  disabled={authBusy || !suUser.trim()} onClick={submitSignup}>
                  {authBusy ? <Loader size={18} className="spin" strokeWidth={2.4} /> : <>Create account & sign in <ArrowRight size={18} strokeWidth={2.4} /></>}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // When idle, freeze the clock at the last real activity (the server caps the
  // recorded session there too), so the pill doesn't tick up while you're away.
  const liveEnd = idle ? Math.min(nowTs, lastActivityRef.current) : nowTs;
  const elapsedSec = activeSession ? (liveEnd - parseUTC(activeSession.started_at).getTime()) / 1000 : 0;
  const tabs = [
    { id: 'dashboard' as const, label: 'Dashboard', Icon: BarChart3 },
    { id: 'topics' as const, label: 'Topics', Icon: BookOpen },
    { id: 'sessions' as const, label: 'Sessions', Icon: CalendarDays },
  ];

  return (
    <div className="app-shell">
      <header style={{ background: 'var(--surface)', borderBottom: '1px solid var(--border)', position: 'sticky', top: 0, zIndex: 20, backdropFilter: 'blur(8px)' }}>
        <div style={{ maxWidth: 1080, margin: '0 auto', padding: '16px 28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Mark size={40} />
              <div>
                <div className="display" style={{ fontSize: 20, lineHeight: 1 }}>Forge</div>
                <div className="faint" style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.03em', marginTop: 3 }}>Senior SDE / MLE prep</div>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div className="tnum" title={idle ? 'Paused — no activity detected. Time resumes when you interact.' : undefined} style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '8px 13px', borderRadius: 999, background: idle ? 'var(--muted-soft, color-mix(in oklch, var(--ok) 8%, transparent))' : 'var(--ok-soft)', color: idle ? 'var(--muted)' : 'var(--ok)', fontSize: 14.5, fontWeight: 700, transition: 'background .3s, color .3s' }}>
                <span style={{ width: 7, height: 7, borderRadius: 999, background: idle ? 'var(--muted)' : 'var(--ok)', boxShadow: idle ? 'none' : '0 0 0 4px color-mix(in oklch, var(--ok) 22%, transparent)' }} />
                {formatClock(elapsedSec)}{idle ? ' · paused' : ''}
              </div>
              <span className="muted" style={{ fontSize: 14, fontWeight: 600 }}>{currentUser.name}</span>
              <button className="btn btn-ghost btn-sm" onClick={logout}><LogOut size={16} strokeWidth={2} /> Sign out</button>
            </div>
          </div>
          <nav style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
            {tabs.map((t) => (
              <button key={t.id} onClick={() => setTab(t.id)} className={`navbtn ${tab === t.id ? 'on' : ''}`}>
                <t.Icon size={17} strokeWidth={2} /> {t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main style={{ maxWidth: 1080, margin: '0 auto', padding: 28 }}>
        {error && (
          <div className="card-flat" style={{ background: 'var(--danger-soft)', color: 'var(--danger)', padding: '12px 16px', fontSize: 14, marginBottom: 16 }}>{error}</div>
        )}
        {tab === 'dashboard' && (
          <Dashboard domains={domains} topics={topics} sessions={sessions} currentUser={currentUser} nowTs={nowTs}
            onRemoveSession={removeSession}
            onSelectDomain={(domainId) => { setTopicDomainFilter(domainId); setTopicStatusFilter('all'); setTab('topics'); }} />
        )}
        {tab === 'topics' && (
          <TopicsView
            domains={domains} topics={topics}
            currentUserId={currentUser.id}
            aiConfigured={aiConfigured}
            doneQuestions={doneQ} questionNotes={qNotes}
            onToggleQuestion={toggleQuestion} onSaveQuestionNotes={saveQuestionNotes}
            search={topicSearch} setSearch={setTopicSearch}
            domainFilter={topicDomainFilter} setDomainFilter={setTopicDomainFilter}
            statusFilter={topicStatusFilter} setStatusFilter={setTopicStatusFilter}
            onAddTopic={addTopic} onPatchTopic={patchTopic} onRemoveTopic={removeTopic}
            onAddSubtopic={addSubtopic} onPatchSubtopic={patchSubtopic} onRemoveSubtopic={removeSubtopic}
            onAddQuestion={addQuestion} onEditQuestion={editQuestion} onRemoveQuestion={removeQuestion}
          />
        )}
        {tab === 'sessions' && <SessionsView sessions={sessions} currentUser={currentUser} nowTs={nowTs} />}
      </main>
    </div>
  );
}
