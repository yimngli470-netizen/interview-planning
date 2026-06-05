import { useMemo } from 'react';
import { Target, Loader2, Clock, Flame, Trash2 } from 'lucide-react';
import type { Domain, Topic, StudySession, User } from '../types';
import { domainClasses } from '../lib/ui';
import { parseUTC, localDateKey, formatHM } from '../lib/time';

interface Props {
  domains: Domain[];
  topics: Topic[];
  sessions: StudySession[];
  currentUser: User | null;
  nowTs: number;
  onRemoveSession: (id: number) => void;
}

function StatCard({
  Icon,
  label,
  value,
  sub,
}: {
  Icon: typeof Target;
  label: string;
  value: string | number;
  sub: string;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
        <Icon className="w-3.5 h-3.5" />
        {label}
      </div>
      <div className="text-2xl font-semibold">{value}</div>
      <div className="text-xs text-slate-500 mt-1">{sub}</div>
    </div>
  );
}

// minutes for a session: live elapsed if active, else its finalized duration
function sessionMinutes(s: StudySession, nowTs: number): number {
  if (s.active) return (nowTs - parseUTC(s.started_at).getTime()) / 60000;
  return s.duration_min;
}

export default function Dashboard({
  domains,
  topics,
  sessions,
  currentUser,
  nowTs,
  onRemoveSession,
}: Props) {
  const byDomain = useMemo(() => {
    const m: Record<number, { total: number; done: number; totalHours: number; doneHours: number; pct: number }> = {};
    for (const d of domains) {
      const items = topics.filter((t) => t.domain_id === d.id);
      const done = items.filter((t) => t.status === 'done');
      const totalHours = items.reduce((s, t) => s + (t.effort_hours || 0), 0);
      const doneHours = done.reduce((s, t) => s + (t.effort_hours || 0), 0);
      m[d.id] = {
        total: items.length,
        done: done.length,
        totalHours,
        doneHours,
        pct: items.length ? Math.round((done.length / items.length) * 100) : 0,
      };
    }
    return m;
  }, [domains, topics]);

  const totalDone = topics.filter((t) => t.status === 'done').length;
  const totalInProg = topics.filter((t) => t.status === 'in-progress').length;

  const totalMin = useMemo(
    () => sessions.reduce((sum, s) => sum + sessionMinutes(s, nowTs), 0),
    [sessions, nowTs],
  );

  const streak = useMemo(() => {
    const dates = new Set(sessions.map((s) => localDateKey(parseUTC(s.started_at))));
    let n = 0;
    const cur = new Date();
    while (dates.has(localDateKey(cur))) {
      n++;
      cur.setDate(cur.getDate() - 1);
    }
    return n;
  }, [sessions]);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          Icon={Target}
          label="Completed"
          value={`${totalDone} / ${topics.length}`}
          sub={topics.length ? `${Math.round((totalDone / topics.length) * 100)}% of plan` : 'no topics'}
        />
        <StatCard Icon={Loader2} label="In Progress" value={totalInProg} sub="active topics" />
        <StatCard
          Icon={Clock}
          label="Logged Time"
          value={formatHM(totalMin)}
          sub={currentUser ? `${sessions.length} sessions` : 'log in to track'}
        />
        <StatCard
          Icon={Flame}
          label="Day Streak"
          value={streak}
          sub={streak > 0 ? 'keep going' : currentUser ? 'study today' : 'log in to track'}
        />
      </div>

      <section className="bg-white border border-slate-200 rounded-lg p-5">
        <h2 className="font-semibold mb-4">Progress by domain</h2>
        <div className="space-y-3">
          {domains.map((d) => {
            const s = byDomain[d.id];
            return (
              <div key={d.id}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded border ${domainClasses(d.color)}`}>{d.name}</span>
                    <span className="text-sm text-slate-600">{s.done} / {s.total} topics</span>
                  </div>
                  <span className="text-sm text-slate-500">{s.doneHours} / {s.totalHours}h</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-slate-900 rounded-full transition-all" style={{ width: `${s.pct}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="bg-white border border-slate-200 rounded-lg p-5">
        <h2 className="font-semibold mb-3">Recent study sessions</h2>
        {!currentUser ? (
          <p className="text-sm text-slate-500">Log in to automatically track your study time.</p>
        ) : sessions.length === 0 ? (
          <p className="text-sm text-slate-500">No sessions yet — they're recorded automatically while you're logged in.</p>
        ) : (
          <div className="space-y-1">
            {sessions.slice(0, 6).map((s) => {
              const start = parseUTC(s.started_at);
              const end = s.ended_at ? parseUTC(s.ended_at) : null;
              const removeWithConfirm = () => {
                if (
                  window.confirm(
                    `Delete this study session?\n\n${start.toLocaleDateString()}  ·  ${formatHM(sessionMinutes(s, nowTs))}\n\nThis can't be undone.`,
                  )
                ) {
                  onRemoveSession(s.id);
                }
              };
              return (
                <div key={s.id} className="flex items-center gap-3 p-2 rounded hover:bg-slate-50 text-sm">
                  <span className="text-slate-500 w-28">{start.toLocaleDateString()}</span>
                  <span className="text-slate-600 flex-1">
                    {start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    {' – '}
                    {end ? end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'now'}
                  </span>
                  {s.active && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">active</span>
                  )}
                  <span className="text-slate-700 w-20 text-right">{formatHM(sessionMinutes(s, nowTs))}</span>
                  {s.active ? (
                    <span className="w-7" />
                  ) : (
                    <button
                      onClick={removeWithConfirm}
                      title="Delete session"
                      className="w-7 flex justify-center p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
