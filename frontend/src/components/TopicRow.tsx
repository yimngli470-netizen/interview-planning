import { useState } from 'react';
import {
  Pin, Edit2, Trash2, Save, ChevronRight, ChevronDown, Plus, X,
} from 'lucide-react';
import type { Domain, Topic, Subtopic } from '../types';
import { domainClasses, StatusButton, nextStatus } from '../lib/ui';

interface Props {
  topic: Topic;
  domain: Domain | undefined;
  onPatchTopic: (id: number, patch: Partial<Topic>) => void;
  onRemoveTopic: (id: number) => void;
  onAddSubtopic: (topicId: number, title: string) => void;
  onPatchSubtopic: (id: number, patch: Partial<Subtopic>) => void;
  onRemoveSubtopic: (id: number) => void;
}

function SubtopicRow({
  sub,
  onPatch,
  onRemove,
}: {
  sub: Subtopic;
  onPatch: (id: number, patch: Partial<Subtopic>) => void;
  onRemove: (id: number) => void;
}) {
  const [notes, setNotes] = useState(sub.notes);
  const dirty = notes !== sub.notes;
  return (
    <div className="flex items-start gap-2 py-2 group/sub">
      <StatusButton
        status={sub.status}
        onClick={() => onPatch(sub.id, { status: nextStatus(sub.status) })}
        iconClass="w-4 h-4 mt-0.5"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`text-sm ${sub.status === 'done' ? 'line-through text-slate-400' : 'text-slate-800'}`}>
            {sub.title}
          </span>
          <button
            onClick={() => onRemove(sub.id)}
            className="opacity-0 group-hover/sub:opacity-100 p-1 text-slate-300 hover:text-rose-600 transition"
            title="Delete learning point"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          onBlur={() => dirty && onPatch(sub.id, { notes })}
          placeholder="Notes for this learning point…"
          rows={notes ? 3 : 1}
          className="mt-1 w-full px-2 py-1 text-xs text-slate-600 border border-slate-200 rounded focus:outline-none focus:border-slate-400 resize-y bg-slate-50/50"
        />
        {dirty && <span className="text-[10px] text-amber-600">unsaved — click away to save</span>}
      </div>
    </div>
  );
}

export default function TopicRow({
  topic,
  domain,
  onPatchTopic,
  onRemoveTopic,
  onAddSubtopic,
  onPatchSubtopic,
  onRemoveSubtopic,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(topic.title);
  const [editNotes, setEditNotes] = useState(topic.notes);
  const [editEffort, setEditEffort] = useState(topic.effort_hours);
  const [newSub, setNewSub] = useState('');

  const subDone = topic.subtopics.filter((s) => s.status === 'done').length;

  const saveEdit = () => {
    onPatchTopic(topic.id, {
      title: editTitle,
      notes: editNotes,
      effort_hours: Number(editEffort) || 0,
    });
    setEditing(false);
  };

  const addSub = () => {
    if (!newSub.trim()) return;
    onAddSubtopic(topic.id, newSub.trim());
    setNewSub('');
  };

  if (editing) {
    return (
      <div className="p-3 space-y-2">
        <input
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:border-slate-500"
        />
        <textarea
          value={editNotes}
          onChange={(e) => setEditNotes(e.target.value)}
          placeholder="Notes, links, key insights…"
          rows={3}
          className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:border-slate-500 resize-y"
        />
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-500">Hours:</label>
          <input
            type="number"
            value={editEffort}
            onChange={(e) => setEditEffort(Number(e.target.value))}
            className="w-20 px-2 py-1 text-sm border border-slate-300 rounded-md"
          />
          <button onClick={saveEdit} className="ml-auto flex items-center gap-1 px-3 py-1.5 text-sm bg-slate-900 text-white rounded-md hover:bg-slate-800">
            <Save className="w-3.5 h-3.5" /> Save
          </button>
          <button onClick={() => setEditing(false)} className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-md">
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 hover:bg-slate-50 group">
      <div className="flex items-start gap-3">
        <StatusButton
          status={topic.status}
          onClick={() => onPatchTopic(topic.id, { status: nextStatus(topic.status) })}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setExpanded((v) => !v)}
              className="flex items-center gap-1 text-slate-400 hover:text-slate-700"
              title="Show learning points"
            >
              {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </button>
            {domain && (
              <span className={`text-xs px-2 py-0.5 rounded border ${domainClasses(domain.color)}`}>{domain.name}</span>
            )}
            <span className="text-xs text-slate-400">#{topic.priority}</span>
            <span className={`text-sm ${topic.status === 'done' ? 'line-through text-slate-400' : ''}`}>
              {topic.title}
            </span>
            {topic.subtopics.length > 0 && (
              <span className="text-xs text-slate-400">
                · {subDone}/{topic.subtopics.length} points
              </span>
            )}
          </div>
          {topic.notes && !expanded && (
            <div className="text-xs text-slate-500 mt-1 whitespace-pre-wrap">{topic.notes}</div>
          )}
        </div>
        <div className="flex items-center gap-1">
          <span className="text-xs text-slate-500 mr-1">{topic.effort_hours}h</span>
          <button
            onClick={() => onPatchTopic(topic.id, { pinned: !topic.pinned })}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded"
            title={topic.pinned ? 'Unpin' : 'Pin'}
          >
            <Pin className={`w-3.5 h-3.5 ${topic.pinned ? 'fill-current text-amber-500' : ''}`} />
          </button>
          <button onClick={() => setEditing(true)} className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded opacity-0 group-hover:opacity-100 transition">
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button onClick={() => onRemoveTopic(topic.id)} className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded opacity-0 group-hover:opacity-100 transition">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {expanded && (
        <div className="ml-8 mt-2 pl-3 border-l-2 border-slate-100">
          {topic.notes && (
            <div className="text-xs text-slate-500 mb-2 whitespace-pre-wrap">{topic.notes}</div>
          )}
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">
            Learning points
          </div>
          {topic.subtopics.length === 0 && (
            <p className="text-xs text-slate-400 py-1">No learning points yet — break this topic into the key things to learn.</p>
          )}
          <div className="divide-y divide-slate-100">
            {topic.subtopics.map((s) => (
              <SubtopicRow key={s.id} sub={s} onPatch={onPatchSubtopic} onRemove={onRemoveSubtopic} />
            ))}
          </div>
          <div className="flex items-center gap-2 mt-2">
            <input
              value={newSub}
              onChange={(e) => setNewSub(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addSub()}
              placeholder="Add a learning point…"
              className="flex-1 px-2 py-1.5 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400"
            />
            <button onClick={addSub} className="flex items-center gap-1 px-2.5 py-1.5 text-xs bg-slate-900 text-white rounded-md hover:bg-slate-800">
              <Plus className="w-3.5 h-3.5" /> Add
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
