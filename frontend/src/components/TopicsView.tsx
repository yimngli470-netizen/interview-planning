import { useMemo, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { Search, Plus } from 'lucide-react';
import type { Domain, Topic, Subtopic } from '../types';
import TopicRow from './TopicRow';

interface Props {
  domains: Domain[];
  topics: Topic[];
  currentUserId: number;
  doneQuestions: Set<number>;
  questionNotes: Map<number, string>;
  onToggleQuestion: (questionId: number, done: boolean) => void;
  onSaveQuestionNotes: (questionId: number, notes: string) => void;
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

export default function TopicsView(props: Props) {
  const {
    domains, topics, search, setSearch, domainFilter, setDomainFilter,
    statusFilter, setStatusFilter, onAddTopic,
  } = props;
  const [showAdd, setShowAdd] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDomain, setNewDomain] = useState<number | ''>(domains[0]?.id ?? '');
  const [newEffort, setNewEffort] = useState(4);

  const domainById = useMemo(() => Object.fromEntries(domains.map((d) => [d.id, d])), [domains]);
  const domainOrder = useMemo(() => Object.fromEntries(domains.map((d, i) => [d.id, i])), [domains]);

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
          t.subtopics.some((s) => s.title.toLowerCase().includes(q) || s.notes.toLowerCase().includes(q)),
      );
    }
    return [...list].sort((a, b) => {
      if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
      if (a.domain_id !== b.domain_id) return (domainOrder[a.domain_id] ?? 0) - (domainOrder[b.domain_id] ?? 0);
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="card" style={{ padding: 14, display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 11 }}>
        <div style={{ position: 'relative', flex: 1, minWidth: 220 }}>
          <span style={{ position: 'absolute', left: 13, top: '50%', transform: 'translateY(-50%)', color: 'var(--faint)', display: 'inline-flex' }}><Search size={17} strokeWidth={2} /></span>
          <input className="field" style={{ paddingLeft: 38 }} placeholder="Search topics, learning points, notes…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <select className="field" style={{ width: 'auto' }} value={domainFilter} onChange={(e) => setDomainFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))}>
          <option value="all">All domains</option>
          {domains.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <select className="field" style={{ width: 'auto' }} value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All status</option>
          <option value="not-started">Not started</option>
          <option value="in-progress">In progress</option>
          <option value="done">Done</option>
        </select>
        <button className="btn btn-primary" onClick={() => { setShowAdd((v) => !v); if (newDomain === '') setNewDomain(domains[0]?.id ?? ''); }}>
          <Plus size={17} strokeWidth={2.4} /> Add topic
        </button>
      </div>

      {showAdd && (
        <div className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 190px 110px', gap: 10 }}>
            <input className="field" placeholder="Topic title…" value={newTitle} autoFocus onChange={(e) => setNewTitle(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && submitAdd()} />
            <select className="field" value={newDomain} onChange={(e) => setNewDomain(Number(e.target.value))}>
              {domains.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
            <input className="field" type="number" placeholder="Hours" value={newEffort} onChange={(e) => setNewEffort(Number(e.target.value))} />
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary btn-sm" onClick={submitAdd}>Add topic</button>
            <button className="btn btn-ghost btn-sm" onClick={() => setShowAdd(false)}>Cancel</button>
          </div>
        </div>
      )}

      <div className="card" style={{ overflow: 'hidden', padding: 0 }}>
        {filtered.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center' }} className="muted">No topics match your filters.</div>
        ) : (
          <div className="divide">
            {filtered.map((t) => (
              <TopicRow
                key={t.id}
                topic={t}
                domain={domainById[t.domain_id]}
                currentUserId={props.currentUserId}
                doneQuestions={props.doneQuestions}
                questionNotes={props.questionNotes}
                onToggleQuestion={props.onToggleQuestion}
                onSaveQuestionNotes={props.onSaveQuestionNotes}
                onPatchTopic={props.onPatchTopic}
                onRemoveTopic={props.onRemoveTopic}
                onAddSubtopic={props.onAddSubtopic}
                onPatchSubtopic={props.onPatchSubtopic}
                onRemoveSubtopic={props.onRemoveSubtopic}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
