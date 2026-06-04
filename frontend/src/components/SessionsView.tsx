import { useMemo, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import type { Domain, Topic, StudySession } from '../types';
import { domainClasses } from '../lib/ui';

interface Props {
  domains: Domain[];
  topics: Topic[];
  sessions: StudySession[];
  onAddSession: (s: Partial<StudySession>) => void;
  onRemoveSession: (id: number) => void;
}

const today = () => new Date().toISOString().slice(0, 10);

export default function SessionsView({
  domains,
  topics,
  sessions,
  onAddSession,
  onRemoveSession,
}: Props) {
  const [show, setShow] = useState(false);
  const [date, setDate] = useState(today());
  const [duration, setDuration] = useState(60);
  const [topicId, setTopicId] = useState<number | ''>('');
  const [summary, setSummary] = useState('');

  const domainById = useMemo(
    () => Object.fromEntries(domains.map((d) => [d.id, d])),
    [domains],
  );
  const topicById = useMemo(
    () => Object.fromEntries(topics.map((t) => [t.id, t])),
    [topics],
  );

  const save = () => {
    if (!topicId) return;
    onAddSession({
      topic_id: Number(topicId),
      date,
      duration_min: Number(duration) || 0,
      summary,
    });
    setDate(today());
    setDuration(60);
    setTopicId('');
    setSummary('');
    setShow(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-semibold">Session log</h2>
          <p className="text-sm text-slate-500">Track what you studied and for how long.</p>
        </div>
        <button
          onClick={() => setShow((v) => !v)}
          className="flex items-center gap-1 px-3 py-2 text-sm bg-slate-900 text-white rounded-md hover:bg-slate-800"
        >
          <Plus className="w-4 h-4" /> Log session
        </button>
      </div>

      {show && (
        <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-[150px_120px_1fr] gap-2">
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="px-3 py-2 text-sm border border-slate-200 rounded-md"
            />
            <input
              type="number"
              placeholder="Minutes"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="px-3 py-2 text-sm border border-slate-200 rounded-md"
            />
            <select
              value={topicId}
              onChange={(e) => setTopicId(e.target.value === '' ? '' : Number(e.target.value))}
              className="px-3 py-2 text-sm border border-slate-200 rounded-md bg-white"
            >
              <option value="">Select topic…</option>
              {domains.map((d) => (
                <optgroup key={d.id} label={d.name}>
                  {topics
                    .filter((t) => t.domain_id === d.id)
                    .map((t) => (
                      <option key={t.id} value={t.id}>{t.title}</option>
                    ))}
                </optgroup>
              ))}
            </select>
          </div>
          <textarea
            placeholder="What did you cover? Key insights, blockers…"
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            rows={2}
            className="w-full px-3 py-2 text-sm border border-slate-200 rounded-md resize-y"
          />
          <div className="flex gap-2">
            <button onClick={save} className="px-3 py-1.5 text-sm bg-slate-900 text-white rounded-md hover:bg-slate-800">Save session</button>
            <button onClick={() => setShow(false)} className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-md">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        {sessions.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">No sessions logged yet.</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {sessions.map((s) => {
              const t = s.topic_id != null ? topicById[s.topic_id] : undefined;
              const d = t ? domainById[t.domain_id] : undefined;
              return (
                <div key={s.id} className="p-3 hover:bg-slate-50 group">
                  <div className="flex items-start gap-3">
                    <div className="text-xs text-slate-500 w-24 pt-0.5">{s.date}</div>
                    <div className="text-xs text-slate-600 w-16 pt-0.5">{s.duration_min} min</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {d && <span className={`text-xs px-2 py-0.5 rounded border ${domainClasses(d.color)}`}>{d.name}</span>}
                        <span className="text-sm">{t ? t.title : '(deleted topic)'}</span>
                      </div>
                      {s.summary && <div className="text-xs text-slate-500 mt-1 whitespace-pre-wrap">{s.summary}</div>}
                    </div>
                    <button
                      onClick={() => onRemoveSession(s.id)}
                      className="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
