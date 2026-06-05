import { useState, useEffect, type MouseEvent } from 'react';
import {
  Pin, Edit2, Trash2, Save, ChevronRight, ChevronDown, Plus, X,
} from 'lucide-react';
import type { Domain, Topic, Subtopic, Question } from '../types';
import { domainClasses, StatusButton, nextStatus } from '../lib/ui';

function QuestionItem({
  q,
  done,
  notes,
  canTrack,
  onToggle,
  onSaveNotes,
}: {
  q: Question;
  done: boolean;
  notes: string;
  canTrack: boolean;
  onToggle: (questionId: number, done: boolean) => void;
  onSaveNotes: (questionId: number, notes: string) => void;
}) {
  const [val, setVal] = useState(notes);
  // sync when the saved value arrives/changes (e.g. after login loads progress)
  useEffect(() => setVal(notes), [notes]);
  const dirty = val !== notes;
  return (
    <div className="py-1">
      <label
        className={`flex items-start gap-2 text-sm ${canTrack ? 'cursor-pointer' : ''}`}
        title={canTrack ? '' : 'Log in to track'}
      >
        <input
          type="checkbox"
          checked={done}
          disabled={!canTrack}
          onChange={(e) => onToggle(q.id, e.target.checked)}
          className="mt-1 accent-slate-900 disabled:opacity-40"
        />
        <span className={done ? 'line-through text-slate-400' : 'text-slate-700'}>{q.prompt}</span>
      </label>
      <textarea
        value={val}
        onChange={(e) => setVal(e.target.value)}
        onBlur={() => dirty && onSaveNotes(q.id, val)}
        disabled={!canTrack}
        placeholder="Your notes / answer…"
        rows={val ? 4 : 2}
        className="ml-6 mt-1 w-[calc(100%-1.5rem)] px-3 py-2 text-sm text-slate-700 border border-slate-200 rounded-md focus:outline-none focus:border-slate-400 resize-y bg-slate-50/50 disabled:bg-slate-50 min-h-[2.75rem]"
      />
      {dirty && <span className="ml-6 text-xs text-amber-600">unsaved — click away to save</span>}
    </div>
  );
}

interface Props {
  topic: Topic;
  domain: Domain | undefined;
  canTrack: boolean;
  doneQuestions: Set<number>;
  questionNotes: Map<number, string>;
  onToggleQuestion: (questionId: number, done: boolean) => void;
  onSaveQuestionNotes: (questionId: number, notes: string) => void;
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
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(sub.title);
  const dirty = notes !== sub.notes;

  const saveTitle = () => {
    const t = title.trim();
    if (t && t !== sub.title) onPatch(sub.id, { title: t });
    setEditing(false);
  };

  return (
    <div className="flex items-start gap-2 py-2 group/sub">
      <StatusButton
        status={sub.status}
        onClick={() => onPatch(sub.id, { status: nextStatus(sub.status) })}
        iconClass="w-4 h-4 mt-0.5"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          {editing ? (
            <input
              autoFocus
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={saveTitle}
              onKeyDown={(e) => {
                if (e.key === 'Enter') saveTitle();
                if (e.key === 'Escape') {
                  setTitle(sub.title);
                  setEditing(false);
                }
              }}
              className="flex-1 px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-slate-500"
            />
          ) : (
            <>
              <span
                onDoubleClick={() => {
                  setTitle(sub.title);
                  setEditing(true);
                }}
                title="Double-click to edit"
                className={`text-sm ${sub.status === 'done' ? 'line-through text-slate-400' : 'text-slate-800'}`}
              >
                {sub.title}
              </span>
              <button
                onClick={() => {
                  setTitle(sub.title);
                  setEditing(true);
                }}
                className="opacity-0 group-hover/sub:opacity-100 p-1 text-slate-300 hover:text-slate-700 transition"
                title="Edit learning point"
              >
                <Edit2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => onRemove(sub.id)}
                className="opacity-0 group-hover/sub:opacity-100 p-1 text-slate-300 hover:text-rose-600 transition"
                title="Delete learning point"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          onBlur={() => dirty && onPatch(sub.id, { notes })}
          placeholder="Notes for this learning point…"
          rows={notes ? 4 : 2}
          className="mt-1 w-full px-3 py-2 text-sm text-slate-700 border border-slate-200 rounded-md focus:outline-none focus:border-slate-400 resize-y bg-slate-50/50 min-h-[2.75rem]"
        />
        {dirty && <span className="text-xs text-amber-600">unsaved — click away to save</span>}
      </div>
    </div>
  );
}

export default function TopicRow({
  topic,
  domain,
  canTrack,
  doneQuestions,
  questionNotes,
  onToggleQuestion,
  onSaveQuestionNotes,
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
  const qDone = topic.questions.filter((q) => doneQuestions.has(q.id)).length;

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

  // The whole header row toggles expand; interactive controls stopPropagation.
  const stop = (fn: () => void) => (e: MouseEvent) => {
    e.stopPropagation();
    fn();
  };

  return (
    <div className="p-3 hover:bg-slate-50 group">
      <div
        className="flex items-start gap-3 cursor-pointer"
        onClick={() => setExpanded((v) => !v)}
        role="button"
        aria-expanded={expanded}
        title={expanded ? 'Collapse' : 'Show learning points'}
      >
        <StatusButton
          status={topic.status}
          onClick={stop(() => onPatchTopic(topic.id, { status: nextStatus(topic.status) }))}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="flex items-center text-slate-400">
              {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </span>
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
            {topic.questions.length > 0 && (
              <span className="text-xs text-slate-400">
                · {qDone}/{topic.questions.length} Qs
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
            onClick={stop(() => onPatchTopic(topic.id, { pinned: !topic.pinned }))}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded"
            title={topic.pinned ? 'Unpin' : 'Pin'}
          >
            <Pin className={`w-3.5 h-3.5 ${topic.pinned ? 'fill-current text-amber-500' : ''}`} />
          </button>
          <button onClick={stop(() => setEditing(true))} className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded opacity-0 group-hover:opacity-100 transition" title="Edit">
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button onClick={stop(() => onRemoveTopic(topic.id))} className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded opacity-0 group-hover:opacity-100 transition" title="Delete">
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

          {topic.questions.length > 0 && (
            <div className="mt-4">
              <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">
                Practice questions
              </div>
              {(['example', 'common'] as const).map((kind) => {
                const qs = topic.questions.filter((q) => q.kind === kind);
                if (qs.length === 0) return null;
                return (
                  <div key={kind} className="mb-2">
                    <div className="text-[11px] text-slate-400 mb-0.5">
                      {kind === 'example' ? 'Example problems' : 'Common questions'}
                    </div>
                    <div className="space-y-1">
                      {qs.map((q) => (
                        <QuestionItem
                          key={q.id}
                          q={q}
                          done={doneQuestions.has(q.id)}
                          notes={questionNotes.get(q.id) ?? ''}
                          canTrack={canTrack}
                          onToggle={onToggleQuestion}
                          onSaveNotes={onSaveQuestionNotes}
                        />
                      ))}
                    </div>
                  </div>
                );
              })}
              {!canTrack && (
                <p className="text-[11px] text-slate-400">Log in to check off questions as you solve them.</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
