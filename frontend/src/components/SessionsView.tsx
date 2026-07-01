import { useMemo } from 'react';
import { Clock } from 'lucide-react';
import type { StudySession, User } from '../types';
import { parseUTC, localDateKey, formatHM, sessionMinutes } from '../lib/time';

interface Props {
  sessions: StudySession[];
  currentUser: User | null;
  nowTs: number;
}

export default function SessionsView({ sessions, currentUser, nowTs }: Props) {
  const byDay = useMemo(() => {
    const groups: { key: string; label: string; total: number; items: StudySession[] }[] = [];
    const index: Record<string, number> = {};
    for (const s of sessions) {
      const d = parseUTC(s.started_at);
      const key = localDateKey(d);
      if (!(key in index)) {
        index[key] = groups.length;
        groups.push({ key, label: d.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' }), total: 0, items: [] });
      }
      const g = groups[index[key]];
      g.items.push(s);
      g.total += sessionMinutes(s, nowTs);
    }
    return groups;
  }, [sessions, nowTs]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      <div>
        <h2 className="display" style={{ fontSize: 24, margin: '0 0 6px' }}>Session log</h2>
        <p className="muted" style={{ fontSize: 14.5, margin: 0, lineHeight: 1.55, maxWidth: 640 }}>
          Study time is recorded automatically while you're logged in — it starts when you log in and stops when you sign out.
        </p>
      </div>

      {!currentUser ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}><span className="muted">Log in to start tracking your study time.</span></div>
      ) : sessions.length === 0 ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}><span className="muted">No sessions yet — your current session will appear here as you study.</span></div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {byDay.map((g) => (
            <div key={g.key} className="card" style={{ overflow: 'hidden', padding: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '13px 20px', background: 'var(--surface-2)', borderBottom: '1px solid var(--border)' }}>
                <span className="display" style={{ fontSize: 16 }}>{g.label}</span>
                <span className="muted tnum" style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 13.5, fontWeight: 600 }}>
                  <Clock size={15} strokeWidth={2} /> {formatHM(g.total)}
                </span>
              </div>
              <div className="divide">
                {g.items.map((s) => {
                  const start = parseUTC(s.started_at);
                  const end = s.ended_at ? parseUTC(s.ended_at) : null;
                  return (
                    <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '13px 20px', fontSize: 14.5 }}>
                      <Clock size={15} strokeWidth={2} style={{ color: 'var(--faint)' }} />
                      <span className="tnum" style={{ fontWeight: 600 }}>{start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} – {end ? end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'now'}</span>
                      {s.active && <span className="badge" style={{ background: 'var(--ok-soft)', color: 'var(--ok)' }}><span style={{ width: 6, height: 6, borderRadius: 999, background: 'var(--ok)' }} /> active</span>}
                      <span className="muted tnum" style={{ marginLeft: 'auto', fontWeight: 600 }}>{formatHM(sessionMinutes(s, nowTs))}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
