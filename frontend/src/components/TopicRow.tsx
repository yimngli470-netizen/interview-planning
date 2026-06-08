import { useState } from 'react';
import type { CSSProperties, MouseEvent } from 'react';
import {
  ChevronRight, ChevronDown, Pin, Trash2, Pencil, X, Plus, Check,
  BookOpen, Sparkles, Loader, Youtube, GraduationCap, FileText, Link2,
} from 'lucide-react';
import type { Domain, Topic, Subtopic, Question, Resource, Level } from '../types';
import { DomainChip, StatusButton, nextStatus } from '../lib/ui';
import { api } from '../lib/api';
import Markdown from '../lib/Markdown';

const LEVEL_META: Record<Exclude<Level, ''>, { label: string; bg: string; fg: string }> = {
  foundational: { label: 'Foundational', bg: 'oklch(0.93 0.06 155)', fg: 'oklch(0.42 0.10 155)' },
  intermediate: { label: 'Intermediate', bg: 'var(--warn-soft)', fg: 'oklch(0.50 0.12 66)' },
  advanced: { label: 'Advanced', bg: 'var(--accent-soft)', fg: 'var(--accent-strong)' },
};

function LevelChip({ level }: { level: Level }) {
  if (!level || !(level in LEVEL_META)) return null;
  const m = LEVEL_META[level as Exclude<Level, ''>];
  return (
    <span style={{ fontSize: 11, fontWeight: 600, padding: '1px 7px', borderRadius: 6, background: m.bg, color: m.fg }}>
      {m.label}
    </span>
  );
}

const RES_ICON = { video: Youtube, course: GraduationCap, article: FileText, docs: BookOpen, book: BookOpen } as const;

function resourceHref(r: Resource): string {
  if (r.url) return r.url;
  const q = encodeURIComponent(r.query || r.title);
  return r.kind === 'video'
    ? `https://www.youtube.com/results?search_query=${q}`
    : `https://www.google.com/search?q=${q}`;
}

function ResourceLinks({ resources }: { resources: Resource[] }) {
  if (!resources?.length) return null;
  return (
    <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 5 }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--faint)' }}>Free resources</div>
      {resources.map((r, i) => {
        const Icon = RES_ICON[r.kind] ?? Link2;
        return (
          <a key={i} href={resourceHref(r)} target="_blank" rel="noreferrer"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 13.5, color: 'var(--accent-strong)', textDecoration: 'none' }}>
            <Icon size={14} strokeWidth={2} style={{ flexShrink: 0, color: 'var(--faint)' }} />
            <span style={{ textDecoration: 'underline', textUnderlineOffset: 2 }}>{r.title}</span>
            {!r.url && <span className="faint" style={{ fontSize: 11 }}>(search)</span>}
          </a>
        );
      })}
    </div>
  );
}

const iconBtn: CSSProperties = {
  width: 32, height: 32, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
  border: 'none', background: 'transparent', color: 'var(--faint)', cursor: 'pointer',
  borderRadius: 8, transition: 'all .15s ease',
};

interface EditorCfg {
  label: string;
  title: string;
  titleEditable: boolean;
  notes: string;
  onSave: (v: { title: string; notes: string }) => void;
}

function NoteDisplay({ value }: { value: string }) {
  if (!value) return null;
  return (
    <div style={{ marginTop: 6, fontSize: 13.5, lineHeight: 1.55, color: 'var(--muted)', whiteSpace: 'pre-wrap' }}>
      {value}
    </div>
  );
}

function QuestionItem({
  q, done, notes, onToggle, onSaveNotes, onExpand,
}: {
  q: Question;
  done: boolean;
  notes: string;
  onToggle: (questionId: number, done: boolean) => void;
  onSaveNotes: (questionId: number, notes: string) => void;
  onExpand: (cfg: EditorCfg) => void;
}) {
  const openNotes = () =>
    onExpand({
      label: 'Practice question',
      title: q.prompt,
      titleEditable: false,
      notes,
      onSave: ({ notes: nn }) => onSaveNotes(q.id, nn),
    });

  return (
    <div className="row-hover" style={{ padding: '7px 0' }}>
      <label style={{ display: 'flex', alignItems: 'flex-start', gap: 10, cursor: 'pointer' }}>
        <button
          type="button"
          onClick={() => onToggle(q.id, !done)}
          style={{
            marginTop: 1, width: 20, height: 20, flexShrink: 0, borderRadius: 6, cursor: 'pointer',
            border: `1.8px solid ${done ? 'var(--accent)' : 'var(--border-strong)'}`,
            background: done ? 'var(--accent)' : 'var(--surface)', color: '#fff',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', transition: 'all .15s ease',
          }}
        >{done && <Check size={13} strokeWidth={3} />}</button>
        <span style={{ flex: 1, fontSize: 14.5, lineHeight: 1.45, color: done ? 'var(--faint)' : 'var(--text)', textDecoration: done ? 'line-through' : 'none' }}>{q.prompt}</span>
        <button className="reveal" onClick={(e) => { e.preventDefault(); openNotes(); }} title="Edit answer"
          style={{ border: 'none', background: 'transparent', color: 'var(--faint)', cursor: 'pointer', padding: 2, display: 'inline-flex', flexShrink: 0 }}>
          <Pencil size={14} strokeWidth={2.2} />
        </button>
      </label>
      <div style={{ marginLeft: 30 }}><NoteDisplay value={notes} /></div>
    </div>
  );
}

function SubtopicRow({
  sub, owned, aiConfigured, topicTitle, domainName, onPatch, onRemove, onExpand,
}: {
  sub: Subtopic;
  owned: boolean;
  aiConfigured: boolean;
  topicTitle: string;
  domainName: string;
  onPatch: (id: number, patch: Partial<Subtopic>) => void;
  onRemove: (id: number) => void;
  onExpand: (cfg: EditorCfg) => void;
}) {
  const [open, setOpen] = useState(false);
  // On-demand "simpler/deeper" explanations (session-cached, client-side only —
  // default content is read-only so we never persist these).
  const [extra, setExtra] = useState<{ simpler?: string; deeper?: string }>({});
  const [loading, setLoading] = useState<'simpler' | 'deeper' | null>(null);
  const [err, setErr] = useState('');

  const openEdit = () =>
    onExpand({
      label: 'Learning point',
      title: sub.title,
      titleEditable: true,
      notes: sub.notes,
      onSave: ({ title: nt, notes: nn }) => {
        const t = (nt || '').trim();
        const patch: Partial<Subtopic> = {};
        if (t && t !== sub.title) patch.title = t;
        if (nn !== sub.notes) patch.notes = nn;
        if (Object.keys(patch).length) onPatch(sub.id, patch);
      },
    });

  const closeExtra = (mode: 'simpler' | 'deeper') =>
    setExtra((e) => { const n = { ...e }; delete n[mode]; return n; });

  const ask = async (mode: 'simpler' | 'deeper') => {
    if (loading) return;
    if (extra[mode]) { closeExtra(mode); return; }  // toggle off if already shown
    setLoading(mode); setErr('');
    try {
      const { markdown } = await api.explain({ point_title: sub.title, topic_title: topicTitle, domain_name: domainName, mode, subtopic_id: sub.id });
      setExtra((e) => ({ ...e, [mode]: markdown }));
    } catch (e) {
      // Surface the real reason (status + body) so it's debuggable, not a silent spinner.
      const msg = e instanceof Error ? e.message : String(e);
      setErr(/Failed to fetch|NetworkError/i.test(msg)
        ? 'Network/timeout — the AI may be busy generating bulk content right now. Try again shortly.'
        : `Couldn't generate: ${msg}`);
      console.error('explain failed:', e);
    } finally {
      setLoading(null);
    }
  };

  const hasDepth = Boolean(sub.explanation) || sub.resources?.length > 0;
  const canExplain = aiConfigured;

  return (
    <div className="row-hover" style={{ display: 'flex', alignItems: 'flex-start', gap: 11, padding: '11px 0' }}>
      <StatusButton status={sub.status} size={19} onClick={() => onPatch(sub.id, { status: nextStatus(sub.status) })} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 14.5, color: sub.status === 'done' ? 'var(--faint)' : 'var(--text)', textDecoration: sub.status === 'done' ? 'line-through' : 'none' }}>{sub.title}</span>
          {!owned && <span className="faint" style={{ fontSize: 11, padding: '1px 6px', borderRadius: 6, background: 'var(--surface-2)', border: '1px solid var(--border)' }}>default</span>}
          {owned && (
            <>
              <button className="reveal" onClick={openEdit} title="Edit learning point"
                style={{ border: 'none', background: 'transparent', color: 'var(--faint)', cursor: 'pointer', padding: 2, display: 'inline-flex' }}>
                <Pencil size={13.5} strokeWidth={2.2} />
              </button>
              <button className="reveal" onClick={() => onRemove(sub.id)} title="Delete learning point"
                style={{ border: 'none', background: 'transparent', color: 'var(--faint)', cursor: 'pointer', padding: 2, display: 'inline-flex' }}>
                <X size={14} strokeWidth={2.4} />
              </button>
            </>
          )}
        </div>
        <NoteDisplay value={sub.notes} />

        {/* Disclosure controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 7, flexWrap: 'wrap' }}>
          {hasDepth && (
            <button type="button" onClick={() => setOpen((v) => !v)}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 4, border: 'none', background: 'transparent', color: 'var(--accent-strong)', cursor: 'pointer', fontSize: 12.5, fontWeight: 600, padding: 0 }}>
              {open ? <ChevronDown size={14} strokeWidth={2.4} /> : <ChevronRight size={14} strokeWidth={2.4} />}
              {open ? 'Hide explanation' : 'Learn more'}
            </button>
          )}
          {canExplain && (
            <>
              <button type="button" onClick={() => ask('simpler')} disabled={loading !== null}
                title="Plain-English explanation for someone new to this domain"
                style={{ display: 'inline-flex', alignItems: 'center', gap: 4, border: 'none', background: 'transparent', color: extra.simpler ? 'var(--accent-strong)' : 'var(--faint)', cursor: 'pointer', fontSize: 12.5, fontWeight: 600, padding: 0 }}>
                {loading === 'simpler' ? <Loader size={13} className="spin" strokeWidth={2.4} /> : <Sparkles size={13} strokeWidth={2} />}
                {extra.simpler ? 'Hide simpler' : 'Explain simpler'}
              </button>
              <button type="button" onClick={() => ask('deeper')} disabled={loading !== null}
                title="Advanced, in-depth explanation"
                style={{ display: 'inline-flex', alignItems: 'center', gap: 4, border: 'none', background: 'transparent', color: extra.deeper ? 'var(--accent-strong)' : 'var(--faint)', cursor: 'pointer', fontSize: 12.5, fontWeight: 600, padding: 0 }}>
                {loading === 'deeper' ? <Loader size={13} className="spin" strokeWidth={2.4} /> : <Sparkles size={13} strokeWidth={2} />}
                {extra.deeper ? 'Hide deeper' : 'Go deeper'}
              </button>
            </>
          )}
        </div>
        {err && <div style={{ marginTop: 6, fontSize: 12.5, color: 'var(--accent)' }}>{err}</div>}

        {/* Expanded depth */}
        {open && (
          <div style={{ marginTop: 10, padding: '12px 14px', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 2 }}>
              <button type="button" onClick={() => setOpen(false)} title="Close"
                style={{ border: 'none', background: 'transparent', color: 'var(--faint)', cursor: 'pointer', padding: 2, display: 'inline-flex' }}>
                <X size={15} strokeWidth={2.4} />
              </button>
            </div>
            {sub.explanation && <Markdown>{sub.explanation}</Markdown>}
            <ResourceLinks resources={sub.resources} />
          </div>
        )}
        {extra.simpler && (
          <ExtraBlock label="Simpler explanation" md={extra.simpler} onClose={() => closeExtra('simpler')} />
        )}
        {extra.deeper && (
          <ExtraBlock label="Deeper dive" md={extra.deeper} onClose={() => closeExtra('deeper')} />
        )}
      </div>
    </div>
  );
}

function ExtraBlock({ label, md, onClose }: { label: string; md: string; onClose: () => void }) {
  return (
    <div style={{ marginTop: 10, padding: '12px 14px', background: 'var(--accent-softer)', border: '1px solid var(--accent-line)', borderRadius: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 6 }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--accent-strong)' }}>
          <Sparkles size={12} strokeWidth={2} /> {label}
        </div>
        <button type="button" onClick={onClose} title="Close"
          style={{ border: 'none', background: 'transparent', color: 'var(--faint)', cursor: 'pointer', padding: 2, display: 'inline-flex', flexShrink: 0 }}>
          <X size={15} strokeWidth={2.4} />
        </button>
      </div>
      <Markdown>{md}</Markdown>
    </div>
  );
}

interface Props {
  topic: Topic;
  domain: Domain | undefined;
  currentUserId: number;
  aiConfigured: boolean;
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

export default function TopicRow({
  topic, domain, currentUserId, aiConfigured, doneQuestions, questionNotes,
  onToggleQuestion, onSaveQuestionNotes,
  onPatchTopic, onRemoveTopic, onAddSubtopic, onPatchSubtopic, onRemoveSubtopic,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const [newSub, setNewSub] = useState('');
  const [editor, setEditor] = useState<EditorCfg | null>(null);
  const [editorTitle, setEditorTitle] = useState('');
  const [editorText, setEditorText] = useState('');

  const ownedTopic = topic.owner_id === currentUserId;
  const subDone = topic.subtopics.filter((s) => s.status === 'done').length;
  const qDone = topic.questions.filter((q) => doneQuestions.has(q.id)).length;
  const stop = (fn: () => void) => (e: MouseEvent) => { e.stopPropagation(); fn(); };

  const openEditor = (cfg: EditorCfg) => { setEditorTitle(cfg.title || ''); setEditorText(cfg.notes || ''); setEditor(cfg); };
  const closeEditor = () => { if (editor) editor.onSave({ title: editorTitle, notes: editorText }); setEditor(null); };

  const addSub = () => { if (newSub.trim()) { onAddSubtopic(topic.id, newSub.trim()); setNewSub(''); } };

  return (
    <div className="row-hover topic-row" style={{ padding: '15px 20px', transition: 'background .15s ease' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 13, cursor: 'pointer' }} onClick={() => setExpanded((v) => !v)}>
        <div style={{ marginTop: 1 }}>
          <StatusButton status={topic.status} size={22} onClick={stop(() => onPatchTopic(topic.id, { status: nextStatus(topic.status) }))} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 9, flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--faint)', display: 'inline-flex', transition: 'transform .2s ease', transform: expanded ? 'rotate(90deg)' : 'none' }}>
              <ChevronRight size={17} strokeWidth={2.4} />
            </span>
            {topic.pinned && <Pin size={14} strokeWidth={2} fill="var(--warn)" style={{ color: 'var(--warn)' }} />}
            <DomainChip domain={domain} small />
            <LevelChip level={topic.level} />
            <span className="display" style={{ fontSize: 17, color: topic.status === 'done' ? 'var(--faint)' : 'var(--text)', textDecoration: topic.status === 'done' ? 'line-through' : 'none' }}>{topic.title}</span>
            <span style={{ display: 'inline-flex', gap: 8 }}>
              {topic.subtopics.length > 0 && <span className="faint" style={{ fontSize: 12.5 }}>{subDone}/{topic.subtopics.length} points</span>}
              {topic.questions.length > 0 && <span className="faint" style={{ fontSize: 12.5 }}>· {qDone}/{topic.questions.length} Qs</span>}
            </span>
          </div>
          {topic.notes && !expanded && <div className="muted" style={{ fontSize: 13.5, marginTop: 6, lineHeight: 1.5, paddingLeft: 26 }}>{topic.notes}</div>}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span className="faint tnum" style={{ fontSize: 13, marginRight: 4, fontWeight: 600 }}>{topic.effort_hours}h</span>
          <button onClick={stop(() => onPatchTopic(topic.id, { pinned: !topic.pinned }))} title={topic.pinned ? 'Unpin' : 'Pin'}
            style={{ ...iconBtn, color: topic.pinned ? 'var(--warn)' : 'var(--faint)' }}>
            <Pin size={16} strokeWidth={2} fill={topic.pinned ? 'var(--warn)' : 'none'} />
          </button>
          {ownedTopic && (
            <button className="reveal" onClick={stop(() => onRemoveTopic(topic.id))} title="Delete" style={iconBtn}>
              <Trash2 size={16} strokeWidth={2} />
            </button>
          )}
        </div>
      </div>

      {expanded && (
        <div style={{ marginLeft: 35, marginTop: 12, paddingLeft: 16, borderLeft: '2px solid var(--accent-line)' }}>
          {topic.notes && <div className="muted" style={{ fontSize: 13.5, marginBottom: 14, lineHeight: 1.55 }}>{topic.notes}</div>}
          <div style={{ fontSize: 11.5, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--faint)', marginBottom: 4 }}>Learning points</div>
          {topic.subtopics.length === 0 && <p className="faint" style={{ fontSize: 13, padding: '4px 0' }}>No learning points yet — add your own below.</p>}
          <div className="divide">
            {topic.subtopics.map((s) => (
              <SubtopicRow key={s.id} sub={s} owned={s.owner_id === currentUserId}
                aiConfigured={aiConfigured} topicTitle={topic.title} domainName={domain?.name ?? ''}
                onPatch={onPatchSubtopic} onRemove={onRemoveSubtopic} onExpand={openEditor} />
            ))}
          </div>
          <div style={{ display: 'flex', gap: 9, marginTop: 12 }}>
            <input className="field" value={newSub} onChange={(e) => setNewSub(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && addSub()} placeholder="Add your own learning point…" />
            <button className="btn btn-soft btn-sm" onClick={addSub}><Plus size={15} strokeWidth={2.4} /> Add</button>
          </div>

          {topic.questions.length > 0 && (
            <div style={{ marginTop: 22 }}>
              <div style={{ fontSize: 11.5, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--faint)', marginBottom: 6 }}>Practice questions</div>
              {(['example', 'common'] as const).map((kind) => {
                const qs = topic.questions.filter((q) => q.kind === kind);
                if (qs.length === 0) return null;
                return (
                  <div key={kind} style={{ marginBottom: 10 }}>
                    <div className="faint" style={{ fontSize: 12, marginBottom: 2 }}>{kind === 'example' ? 'Example problems' : 'Common questions'}</div>
                    <div>{qs.map((q) => (
                      <QuestionItem key={q.id} q={q} done={doneQuestions.has(q.id)} notes={questionNotes.get(q.id) ?? ''} onToggle={onToggleQuestion} onSaveNotes={onSaveQuestionNotes} onExpand={openEditor} />
                    ))}</div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {editor && (
        <div onClick={closeEditor} style={{ position: 'fixed', inset: 0, zIndex: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, background: 'oklch(0.2 0.02 60 / 0.42)', backdropFilter: 'blur(3px)' }}>
          <div onClick={(e) => e.stopPropagation()} className="card" style={{ width: '100%', maxWidth: 760, height: '82vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 24px 60px -12px rgba(0,0,0,0.35)' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, padding: '16px 22px', borderBottom: '1px solid var(--border)' }}>
              <div style={{ minWidth: 0 }}>
                <div className="faint" style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{editor.label}</div>
                {!editor.titleEditable && <div className="display" style={{ fontSize: 18, marginTop: 3 }}>{editor.title}</div>}
              </div>
              <button onClick={closeEditor} title="Done (saves)" style={{ ...iconBtn, flexShrink: 0 }}><X size={20} strokeWidth={2.2} /></button>
            </div>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              {editor.titleEditable && (
                <div style={{ padding: '18px 22px 0' }}>
                  <label className="faint" style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Name</label>
                  <input className="field" autoFocus value={editorTitle} onChange={(e) => setEditorTitle(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Escape') closeEditor(); }} placeholder="Learning point name…"
                    style={{ marginTop: 6, fontSize: 16, fontWeight: 600 }} />
                  <label className="faint" style={{ display: 'block', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', marginTop: 16 }}>Details</label>
                </div>
              )}
              <textarea
                autoFocus={!editor.titleEditable} value={editorText}
                onChange={(e) => setEditorText(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Escape') closeEditor(); if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') closeEditor(); }}
                placeholder="Write your notes / answer…"
                style={{ flex: 1, width: '100%', border: 'none', outline: 'none', resize: 'none', padding: editor.titleEditable ? '8px 22px 22px' : '22px', fontFamily: 'var(--font-ui)', fontSize: 16, lineHeight: 1.65, color: 'var(--text)', background: 'var(--surface)' }}
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 22px', borderTop: '1px solid var(--border)' }}>
              <span className="faint tnum" style={{ fontSize: 12.5 }}>{editorText.length} chars · Esc or ⌘/Ctrl+Enter to save</span>
              <button className="btn btn-primary btn-sm" onClick={closeEditor}>Done</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
