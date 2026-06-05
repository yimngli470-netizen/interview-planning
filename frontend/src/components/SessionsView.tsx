import { useMemo } from 'react';
import { Clock } from 'lucide-react';
import type { StudySession, User } from '../types';
import { parseUTC, localDateKey, formatHM } from '../lib/time';

interface Props {
  sessions: StudySession[];
  currentUser: User | null;
  nowTs: number;
}

function sessionMinutes(s: StudySession, nowTs: number): number {
  if (s.active) return (nowTs - parseUTC(s.started_at).getTime()) / 60000;
  return s.duration_min;
}

export default function SessionsView({ sessions, currentUser, nowTs }: Props) {
  // group by local day, newest first
  const byDay = useMemo(() => {
    const groups: { key: string; label: string; total: number; items: StudySession[] }[] = [];
    const index: Record<string, number> = {};
    for (const s of sessions) {
      const d = parseUTC(s.started_at);
      const key = localDateKey(d);
      if (!(key in index)) {
        index[key] = groups.length;
        groups.push({ key, label: d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }), total: 0, items: [] });
      }
      const g = groups[index[key]];
      g.items.push(s);
      g.total += sessionMinutes(s, nowTs);
    }
    return groups;
  }, [sessions, nowTs]);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-semibold">Session log</h2>
        <p className="text-sm text-slate-500">
          Study time is recorded automatically while you're logged in — it starts when
          you log in and stops when you sign out (or close your laptop).
        </p>
      </div>

      {!currentUser ? (
        <div className="bg-white border border-slate-200 rounded-lg p-8 text-center text-sm text-slate-500">
          Log in to start tracking your study time.
        </div>
      ) : sessions.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-lg p-8 text-center text-sm text-slate-500">
          No sessions yet — your current session will appear here as you study.
        </div>
      ) : (
        <div className="space-y-4">
          {byDay.map((g) => (
            <div key={g.key} className="bg-white border border-slate-200 rounded-lg overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2 bg-slate-50 border-b border-slate-100">
                <span className="text-sm font-medium text-slate-700">{g.label}</span>
                <span className="flex items-center gap-1.5 text-sm text-slate-500">
                  <Clock className="w-3.5 h-3.5" /> {formatHM(g.total)}
                </span>
              </div>
              <div className="divide-y divide-slate-100">
                {g.items.map((s) => {
                  const start = parseUTC(s.started_at);
                  const end = s.ended_at ? parseUTC(s.ended_at) : null;
                  return (
                    <div key={s.id} className="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-slate-50">
                      <span className="text-slate-700">
                        {start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        {' – '}
                        {end ? end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'now'}
                      </span>
                      {s.active && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">active</span>
                      )}
                      <span className="ml-auto text-slate-500">{formatHM(sessionMinutes(s, nowTs))}</span>
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
