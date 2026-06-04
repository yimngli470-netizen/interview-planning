import { useMemo } from 'react';
import { Target, Loader2, Clock, Flame, Pin } from 'lucide-react';
import type { Domain, Topic, StudySession, Status } from '../types';
import { domainClasses, StatusButton, nextStatus } from '../lib/ui';

interface Props {
  domains: Domain[];
  topics: Topic[];
  sessions: StudySession[];
  onCycleStatus: (t: Topic, next: Status) => void;
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

export default function Dashboard({ domains, topics, sessions, onCycleStatus }: Props) {
  const stats = useMemo(() => {
    const byDomain: Record<number, { total: number; done: number; totalHours: number; doneHours: number; pct: number }> = {};
    for (const d of domains) {
      const items = topics.filter((t) => t.domain_id === d.id);
      const done = items.filter((t) => t.status === 'done');
      const totalHours = items.reduce((s, t) => s + (t.effort_hours || 0), 0);
      const doneHours = done.reduce((s, t) => s + (t.effort_hours || 0), 0);
      byDomain[d.id] = {
        total: items.length,
        done: done.length,
        totalHours,
        doneHours,
        pct: items.length ? Math.round((done.length / items.length) * 100) : 0,
      };
    }
    const totalDone = topics.filter((t) => t.status === 'done').length;
    const totalInProg = topics.filter((t) => t.status === 'in-progress').length;
    const totalSessionMin = sessions.reduce((s, x) => s + (x.duration_min || 0), 0);

    // streak: consecutive days from today with >=1 session
    const dates = new Set(sessions.map((s) => s.date));
    let streak = 0;
    const cur = new Date();
    while (dates.has(cur.toISOString().slice(0, 10))) {
      streak++;
      cur.setDate(cur.getDate() - 1);
    }
    return { byDomain, totalDone, totalInProg, total: topics.length, totalSessionMin, streak };
  }, [domains, topics, sessions]);

  const domainById = useMemo(
    () => Object.fromEntries(domains.map((d) => [d.id, d])),
    [domains],
  );
  const pinned = topics.filter((t) => t.pinned);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          Icon={Target}
          label="Completed"
          value={`${stats.totalDone} / ${stats.total}`}
          sub={stats.total ? `${Math.round((stats.totalDone / stats.total) * 100)}% of plan` : 'no topics'}
        />
        <StatCard Icon={Loader2} label="In Progress" value={stats.totalInProg} sub="active topics" />
        <StatCard
          Icon={Clock}
          label="Logged Time"
          value={`${Math.round(stats.totalSessionMin / 60)}h`}
          sub={`${sessions.length} sessions`}
        />
        <StatCard
          Icon={Flame}
          label="Day Streak"
          value={stats.streak}
          sub={stats.streak > 0 ? 'keep going' : 'log today'}
        />
      </div>

      <section className="bg-white border border-slate-200 rounded-lg p-5">
        <h2 className="font-semibold mb-4">Progress by domain</h2>
        <div className="space-y-3">
          {domains.map((d) => {
            const s = stats.byDomain[d.id];
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
        <h2 className="font-semibold mb-3 flex items-center gap-2">
          <Pin className="w-4 h-4" /> Pinned priorities
        </h2>
        <div className="space-y-2">
          {pinned.length === 0 && (
            <p className="text-sm text-slate-500">No pinned items. Pin your top priorities in the Topics tab.</p>
          )}
          {pinned.map((t) => {
            const d = domainById[t.domain_id];
            return (
              <div key={t.id} className="flex items-center gap-3 p-2 rounded hover:bg-slate-50">
                <StatusButton status={t.status} onClick={() => onCycleStatus(t, nextStatus(t.status))} />
                {d && <span className={`text-xs px-2 py-0.5 rounded border ${domainClasses(d.color)}`}>{d.name}</span>}
                <span className={`text-sm flex-1 ${t.status === 'done' ? 'line-through text-slate-400' : ''}`}>{t.title}</span>
                <span className="text-xs text-slate-500">{t.effort_hours}h</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="bg-white border border-slate-200 rounded-lg p-5">
        <h2 className="font-semibold mb-3">Recent sessions</h2>
        {sessions.length === 0 ? (
          <p className="text-sm text-slate-500">No sessions logged yet. Log your first study block in the Sessions tab.</p>
        ) : (
          <div className="space-y-2">
            {sessions.slice(0, 5).map((s) => {
              const t = topics.find((x) => x.id === s.topic_id);
              const d = t ? domainById[t.domain_id] : undefined;
              return (
                <div key={s.id} className="flex items-center gap-3 p-2 rounded hover:bg-slate-50 text-sm">
                  <span className="text-slate-500 w-24">{s.date}</span>
                  <span className="text-slate-600 w-16">{s.duration_min}min</span>
                  {d && <span className={`text-xs px-2 py-0.5 rounded border ${domainClasses(d.color)}`}>{d.name}</span>}
                  <span className="text-slate-700 flex-1 truncate">{t ? t.title : '(deleted topic)'}</span>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
