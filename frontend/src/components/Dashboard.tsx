import { useMemo } from 'react';
import { Target, Contrast, Clock, Flame, Trash2, ChevronRight } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { Domain, Topic, StudySession, User } from '../types';
import { DomainChip } from '../lib/ui';
import { parseUTC, localDateKey, formatHM } from '../lib/time';

interface Props {
  domains: Domain[];
  topics: Topic[];
  sessions: StudySession[];
  currentUser: User | null;
  nowTs: number;
  onRemoveSession: (id: number) => void;
  onSelectDomain: (domainId: number) => void;
}

function sessionMinutes(s: StudySession, nowTs: number): number {
  if (s.active) return (nowTs - parseUTC(s.started_at).getTime()) / 60000;
  return s.duration_min;
}

function StatTile({
  Icon, label, value, sub, accent,
}: {
  Icon: LucideIcon;
  label: string;
  value: string | number;
  sub: string;
  accent?: boolean;
}) {
  return (
    <div className="card" style={{ padding: '18px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, color: 'var(--muted)', fontSize: 12.5, fontWeight: 600, letterSpacing: '0.02em', textTransform: 'uppercase' }}>
        <Icon size={15} strokeWidth={2} style={{ color: accent ? 'var(--accent)' : 'var(--faint)' }} />
        {label}
      </div>
      <div className="display tnum" style={{ fontSize: 38, marginTop: 8, color: 'var(--text)' }}>{value}</div>
      <div className="faint" style={{ fontSize: 13, marginTop: 2 }}>{sub}</div>
    </div>
  );
}

export default function Dashboard({ domains, topics, sessions, currentUser, nowTs, onRemoveSession, onSelectDomain }: Props) {
  const byDomain = useMemo(() => {
    const m: Record<number, { total: number; done: number; totalHours: number; doneHours: number; pct: number }> = {};
    for (const d of domains) {
      const items = topics.filter((t) => t.domain_id === d.id);
      const done = items.filter((t) => t.status === 'done');
      const totalHours = items.reduce((s, t) => s + (t.effort_hours || 0), 0);
      const doneHours = done.reduce((s, t) => s + (t.effort_hours || 0), 0);
      m[d.id] = { total: items.length, done: done.length, totalHours, doneHours, pct: items.length ? Math.round((done.length / items.length) * 100) : 0 };
    }
    return m;
  }, [domains, topics]);

  const totalDone = topics.filter((t) => t.status === 'done').length;
  const totalInProg = topics.filter((t) => t.status === 'in-progress').length;
  const totalMin = useMemo(() => sessions.reduce((s, x) => s + sessionMinutes(x, nowTs), 0), [sessions, nowTs]);
  const streak = useMemo(() => {
    const dates = new Set(sessions.map((s) => localDateKey(parseUTC(s.started_at))));
    let n = 0; const cur = new Date();
    while (dates.has(localDateKey(cur))) { n++; cur.setDate(cur.getDate() - 1); }
    return n;
  }, [sessions]);
  const overallPct = topics.length ? Math.round((totalDone / topics.length) * 100) : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
        <StatTile Icon={Target} label="Completed" value={`${totalDone}/${topics.length}`} sub={topics.length ? `${overallPct}% of plan` : 'no topics'} accent />
        <StatTile Icon={Contrast} label="In progress" value={totalInProg} sub="active topics" />
        <StatTile Icon={Clock} label="Logged time" value={formatHM(totalMin)} sub={currentUser ? `${sessions.length} sessions` : 'log in to track'} />
        <StatTile Icon={Flame} label="Day streak" value={streak} sub={streak > 0 ? 'keep the heat on' : 'study today'} accent />
      </div>

      <section className="card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 18 }}>
          <h2 className="display" style={{ fontSize: 21, margin: 0 }}>Progress by domain</h2>
          <span className="faint" style={{ fontSize: 13 }}>{overallPct}% overall</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          {domains.map((d) => {
            const s = byDomain[d.id];
            return (
              <button key={d.id} type="button" onClick={() => onSelectDomain(d.id)}
                className="row-hover domain-row" title={`View ${d.name} topics`}
                style={{ display: 'block', width: '100%', textAlign: 'left', border: 'none', background: 'transparent', cursor: 'pointer', padding: '8px 10px', margin: '0 -10px', borderRadius: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 9 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
                    <DomainChip domain={d} />
                    <span className="muted" style={{ fontSize: 14 }}>{s.done} / {s.total} topics</span>
                  </div>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <span className="faint tnum" style={{ fontSize: 13.5 }}>{s.doneHours} / {s.totalHours}h</span>
                    <ChevronRight className="domain-row-arrow" size={16} strokeWidth={2.2} style={{ color: 'var(--faint)' }} />
                  </span>
                </div>
                <div className="track"><i style={{ width: `${s.pct}%` }} /></div>
              </button>
            );
          })}
        </div>
      </section>

      <section className="card" style={{ padding: 24 }}>
        <h2 className="display" style={{ fontSize: 21, margin: '0 0 14px' }}>Recent study sessions</h2>
        {!currentUser ? (
          <p className="muted" style={{ fontSize: 14 }}>Log in to automatically track your study time.</p>
        ) : sessions.length === 0 ? (
          <p className="muted" style={{ fontSize: 14 }}>No sessions yet — they're recorded automatically while you're logged in.</p>
        ) : (
          <div className="divide" style={{ marginTop: -6 }}>
            {sessions.slice(0, 6).map((s) => {
              const start = parseUTC(s.started_at);
              const end = s.ended_at ? parseUTC(s.ended_at) : null;
              const removeWithConfirm = () => {
                if (window.confirm(`Delete this study session?\n\n${start.toLocaleDateString()}  ·  ${formatHM(sessionMinutes(s, nowTs))}\n\nThis can't be undone.`)) onRemoveSession(s.id);
              };
              return (
                <div key={s.id} className="row-hover" style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '11px 0', fontSize: 14 }}>
                  <span className="tnum" style={{ width: 104, color: 'var(--muted)', fontWeight: 600 }}>{start.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>
                  <span className="muted tnum" style={{ flex: 1 }}>
                    {start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} – {end ? end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'now'}
                  </span>
                  {s.active && <span className="badge" style={{ background: 'var(--ok-soft)', color: 'var(--ok)' }}><span style={{ width: 6, height: 6, borderRadius: 999, background: 'var(--ok)' }} /> active</span>}
                  <span className="tnum" style={{ width: 72, textAlign: 'right', fontWeight: 600 }}>{formatHM(sessionMinutes(s, nowTs))}</span>
                  {s.active ? <span style={{ width: 30 }} /> : (
                    <button className="reveal" onClick={removeWithConfirm} title="Delete session"
                      style={{ width: 30, height: 30, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', border: 'none', background: 'transparent', color: 'var(--faint)', cursor: 'pointer', borderRadius: 8 }}>
                      <Trash2 size={16} strokeWidth={2} />
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
