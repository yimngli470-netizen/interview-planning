import { useMemo, useState, type Dispatch, type SetStateAction } from 'react';
import { Search, Plus } from 'lucide-react';
import type { Domain, Topic, Subtopic } from '../types';
import TopicRow from './TopicRow';

interface Props {
  domains: Domain[];
  topics: Topic[];
  // Filters are owned by App so they persist when switching tabs.
  search: string;
  setSearch: Dispatch<SetStateAction<string>>;
  domainFilter: number | 'all';
  setDomainFilter: Dispatch<SetStateAction<number | 'all'>>;
  statusFilter: string;
  setStatusFilter: Dispatch<SetStateAction<string>>;
  onAddTopic: (domainId: number, title: string, effortHours: number) => void;
  onPatchTopic: (id: number, patch: Partial<Topic>) => void;
  onRemoveTopic: (id: number) => void;
  onAddSubtopic: (topicId: number, title: string) => void;
  onPatchSubtopic: (id: number, patch: Partial<Subtopic>) => void;
  onRemoveSubtopic: (id: number) => void;
}

export default function TopicsView({
  domains,
  topics,
  search,
  setSearch,
  domainFilter,
  setDomainFilter,
  statusFilter,
  setStatusFilter,
  onAddTopic,
  onPatchTopic,
  onRemoveTopic,
  onAddSubtopic,
  onPatchSubtopic,
  onRemoveSubtopic,
}: Props) {
  const [showAdd, setShowAdd] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDomain, setNewDomain] = useState<number | ''>('');
  const [newEffort, setNewEffort] = useState(4);

  const domainById = useMemo(
    () => Object.fromEntries(domains.map((d) => [d.id, d])),
    [domains],
  );
  const domainOrder = useMemo(
    () => Object.fromEntries(domains.map((d, i) => [d.id, i])),
    [domains],
  );

  const filtered = useMemo(() => {
    let list = topics;
    if (domainFilter !== 'all') list = list.filter((t) => t.domain_id === domainFilter);
    if (statusFilter !== 'all') list = list.filter((t) => t.status === statusFilter);
    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (t) =>
          t.title.toLowerCase().includes(q) ||
          t.notes.toLowerCase().includes(q) ||
          t.subtopics.some(
            (s) => s.title.toLowerCase().includes(q) || s.notes.toLowerCase().includes(q),
          ),
      );
    }
    // pinned first, then by domain order, then priority
    return [...list].sort((a, b) => {
      if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
      if (a.domain_id !== b.domain_id)
        return (domainOrder[a.domain_id] ?? 0) - (domainOrder[b.domain_id] ?? 0);
      return a.priority - b.priority;
    });
  }, [topics, domainFilter, statusFilter, search, domainOrder]);

  const submitAdd = () => {
    const domainId = newDomain === '' ? domains[0]?.id : newDomain;
    if (!newTitle.trim() || !domainId) return;
    onAddTopic(domainId, newTitle.trim(), Number(newEffort) || 4);
    setNewTitle('');
    setShowAdd(false);
  };

  return (
    <div className="space-y-4">
      <div className="bg-white border border-slate-200 rounded-lg p-3 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search topics, learning points, notes…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400"
          />
        </div>
        <select
          value={domainFilter}
          onChange={(e) => setDomainFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))}
          className="px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400 bg-white"
        >
          <option value="all">All domains</option>
          {domains.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400 bg-white"
        >
          <option value="all">All status</option>
          <option value="not-started">Not started</option>
          <option value="in-progress">In progress</option>
          <option value="done">Done</option>
        </select>
        <button
          onClick={() => {
            setShowAdd((v) => !v);
            if (newDomain === '') setNewDomain(domains[0]?.id ?? '');
          }}
          className="flex items-center gap-1 px-3 py-2 text-sm bg-slate-900 text-white rounded-md hover:bg-slate-800"
        >
          <Plus className="w-4 h-4" /> Add topic
        </button>
      </div>

      {showAdd && (
        <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-[1fr_180px_100px] gap-2">
            <input
              type="text"
              placeholder="Topic title…"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submitAdd()}
              className="px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400"
            />
            <select
              value={newDomain}
              onChange={(e) => setNewDomain(Number(e.target.value))}
              className="px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400 bg-white"
            >
              {domains.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
            <input
              type="number"
              placeholder="Hours"
              value={newEffort}
              onChange={(e) => setNewEffort(Number(e.target.value))}
              className="px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400"
            />
          </div>
          <div className="flex gap-2">
            <button onClick={submitAdd} className="px-3 py-1.5 text-sm bg-slate-900 text-white rounded-md hover:bg-slate-800">Add</button>
            <button onClick={() => setShowAdd(false)} className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-md">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        {filtered.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">No topics match your filters.</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {filtered.map((t) => (
              <TopicRow
                key={t.id}
                topic={t}
                domain={domainById[t.domain_id]}
                onPatchTopic={onPatchTopic}
                onRemoveTopic={onRemoveTopic}
                onAddSubtopic={onAddSubtopic}
                onPatchSubtopic={onPatchSubtopic}
                onRemoveSubtopic={onRemoveSubtopic}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
