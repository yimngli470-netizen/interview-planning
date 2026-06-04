import { useState, useEffect, useMemo } from 'react';
import { Search, Pin, PinOff, Plus, Trash2, Copy, Check, Circle, Loader2, Clock, BarChart3, FileText, Calendar, BookOpen, Filter, X, ChevronDown, Target, Flame, Edit2, Save } from 'lucide-react';

const DOMAINS = ['Coding', 'System Design', 'AI Infra', 'AI/ML', 'Mock Interviews', 'Projects'];

const DOMAIN_COLORS = {
  'Coding': 'bg-blue-100 text-blue-700 border-blue-200',
  'System Design': 'bg-violet-100 text-violet-700 border-violet-200',
  'AI Infra': 'bg-emerald-100 text-emerald-700 border-emerald-200',
  'AI/ML': 'bg-amber-100 text-amber-700 border-amber-200',
  'Mock Interviews': 'bg-rose-100 text-rose-700 border-rose-200',
  'Projects': 'bg-indigo-100 text-indigo-700 border-indigo-200',
};

const DEFAULT_TOPICS = [
  // Coding
  { id: 'c1', domain: 'Coding', title: 'Arrays, Hashmaps, Two Pointers — foundation patterns', priority: 1, effortHours: 8, status: 'not-started', pinned: false, notes: '' },
  { id: 'c2', domain: 'Coding', title: 'BFS / DFS on graphs and trees', priority: 2, effortHours: 10, status: 'not-started', pinned: false, notes: '' },
  { id: 'c3', domain: 'Coding', title: 'Dynamic Programming — 1D, 2D, knapsack patterns', priority: 3, effortHours: 15, status: 'not-started', pinned: false, notes: '' },
  { id: 'c4', domain: 'Coding', title: 'Binary Search (incl. on the answer)', priority: 4, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'c5', domain: 'Coding', title: 'Implementation-heavy problems w/ evolving requirements', priority: 5, effortHours: 12, status: 'not-started', pinned: true, notes: 'Anthropic-style: rewards code that stays clean as constraints are added mid-interview.' },
  { id: 'c6', domain: 'Coding', title: 'Heap / Priority Queue patterns', priority: 6, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'c7', domain: 'Coding', title: 'Sliding Window / Prefix Sum', priority: 7, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'c8', domain: 'Coding', title: 'Concurrency primitives (locks, async, threads)', priority: 8, effortHours: 8, status: 'not-started', pinned: false, notes: '' },
  { id: 'c9', domain: 'Coding', title: 'Backtracking', priority: 9, effortHours: 8, status: 'not-started', pinned: false, notes: '' },
  { id: 'c10', domain: 'Coding', title: 'Trie / Union-Find', priority: 10, effortHours: 6, status: 'not-started', pinned: false, notes: '' },

  // System Design
  { id: 'sd1', domain: 'System Design', title: 'Fundamentals: load balancing, caching, sharding, replication, consistency', priority: 1, effortHours: 12, status: 'not-started', pinned: true, notes: '' },
  { id: 'sd2', domain: 'System Design', title: 'Design LLM inference serving system (batching, KV cache, autoscaling)', priority: 2, effortHours: 10, status: 'not-started', pinned: true, notes: '' },
  { id: 'sd3', domain: 'System Design', title: 'Design distributed training cluster (DP/MP/PP, fault tolerance)', priority: 3, effortHours: 10, status: 'not-started', pinned: false, notes: '' },
  { id: 'sd4', domain: 'System Design', title: 'Design RAG pipeline w/ vector search + eval', priority: 4, effortHours: 8, status: 'not-started', pinned: false, notes: '' },
  { id: 'sd5', domain: 'System Design', title: 'Design agent orchestration / tool-use system', priority: 5, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'sd6', domain: 'System Design', title: 'Design model evaluation / observability platform', priority: 6, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'sd7', domain: 'System Design', title: 'Design rate limiter / distributed counter', priority: 7, effortHours: 4, status: 'not-started', pinned: false, notes: '' },
  { id: 'sd8', domain: 'System Design', title: 'Design distributed KV store / metadata service', priority: 8, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'sd9', domain: 'System Design', title: 'Design streaming chat / news feed / notification system', priority: 9, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'sd10', domain: 'System Design', title: 'Design URL shortener / pastebin (warmup)', priority: 10, effortHours: 4, status: 'not-started', pinned: false, notes: '' },

  // AI Infra
  { id: 'inf1', domain: 'AI Infra', title: 'GPU architecture: SMs, memory hierarchy, Tensor Cores, NVLink', priority: 1, effortHours: 10, status: 'not-started', pinned: true, notes: '' },
  { id: 'inf2', domain: 'AI Infra', title: 'Distributed training: DDP, FSDP, ZeRO-1/2/3, TP, PP', priority: 2, effortHours: 12, status: 'not-started', pinned: true, notes: '' },
  { id: 'inf3', domain: 'AI Infra', title: 'Inference optimization: KV cache, PagedAttention, continuous batching (vLLM)', priority: 3, effortHours: 10, status: 'not-started', pinned: true, notes: '' },
  { id: 'inf4', domain: 'AI Infra', title: 'CUDA programming basics: kernels, shared memory, occupancy', priority: 4, effortHours: 15, status: 'not-started', pinned: false, notes: '' },
  { id: 'inf5', domain: 'AI Infra', title: 'Quantization (INT8, FP8, FP4) & speculative decoding', priority: 5, effortHours: 8, status: 'not-started', pinned: false, notes: '' },
  { id: 'inf6', domain: 'AI Infra', title: 'FlashAttention & memory-efficient attention variants', priority: 6, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'inf7', domain: 'AI Infra', title: 'NCCL collectives & communication patterns', priority: 7, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'inf8', domain: 'AI Infra', title: 'Serving frameworks: Triton, TensorRT-LLM, SGLang', priority: 8, effortHours: 8, status: 'not-started', pinned: false, notes: '' },
  { id: 'inf9', domain: 'AI Infra', title: 'Checkpointing, fault tolerance, large-cluster observability', priority: 9, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'inf10', domain: 'AI Infra', title: 'Kubernetes / SLURM for ML workloads', priority: 10, effortHours: 6, status: 'not-started', pinned: false, notes: '' },

  // AI/ML
  { id: 'ml1', domain: 'AI/ML', title: 'Transformer deep dive: MHA, KV cache, RoPE, MoE routing', priority: 1, effortHours: 12, status: 'not-started', pinned: true, notes: '' },
  { id: 'ml2', domain: 'AI/ML', title: 'Pretraining: scaling laws, data mixing, tokenization', priority: 2, effortHours: 8, status: 'not-started', pinned: false, notes: '' },
  { id: 'ml3', domain: 'AI/ML', title: 'Post-training: SFT, RLHF, DPO, RLAIF, Constitutional AI', priority: 3, effortHours: 10, status: 'not-started', pinned: true, notes: '' },
  { id: 'ml4', domain: 'AI/ML', title: 'Evaluation: benchmarks, human eval, hallucination detection', priority: 4, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'ml5', domain: 'AI/ML', title: 'Agentic systems: tool use, planning, MCP, multi-step reasoning', priority: 5, effortHours: 8, status: 'not-started', pinned: true, notes: '' },
  { id: 'ml6', domain: 'AI/ML', title: 'AI safety: alignment, interpretability, red-teaming', priority: 6, effortHours: 8, status: 'not-started', pinned: true, notes: 'Critical for Anthropic — values/ethics round.' },
  { id: 'ml7', domain: 'AI/ML', title: 'RAG architectures vs fine-tuning tradeoffs', priority: 7, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'ml8', domain: 'AI/ML', title: 'Probability/stats fundamentals (Bayes, MLE, distributions)', priority: 8, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'ml9', domain: 'AI/ML', title: 'Classical ML refresher: regression, trees, gradient boosting', priority: 9, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'ml10', domain: 'AI/ML', title: 'Diffusion models & multimodal architectures', priority: 10, effortHours: 6, status: 'not-started', pinned: false, notes: '' },

  // Mock Interviews
  { id: 'mk1', domain: 'Mock Interviews', title: 'Write 6 STAR stories (impact, ambiguity, conflict, failure, leadership, ethics)', priority: 1, effortHours: 6, status: 'not-started', pinned: true, notes: '' },
  { id: 'mk2', domain: 'Mock Interviews', title: 'Project deep-dive prep (20-min present + 40-min Q&A)', priority: 2, effortHours: 8, status: 'not-started', pinned: true, notes: 'Defend every architectural decision as if facing a skeptical senior engineer.' },
  { id: 'mk3', domain: 'Mock Interviews', title: '5 coding mocks (45-min, no AI tools — Anthropic prohibits them)', priority: 3, effortHours: 8, status: 'not-started', pinned: true, notes: '' },
  { id: 'mk4', domain: 'Mock Interviews', title: '3 system design mocks (AI-flavored: inference, RAG, training)', priority: 4, effortHours: 8, status: 'not-started', pinned: false, notes: '' },
  { id: 'mk5', domain: 'Mock Interviews', title: '2 ML system design mocks (recommender / RAG / fine-tuning)', priority: 5, effortHours: 6, status: 'not-started', pinned: false, notes: '' },
  { id: 'mk6', domain: 'Mock Interviews', title: 'Anthropic values/ethics scenario practice', priority: 6, effortHours: 4, status: 'not-started', pinned: false, notes: '' },
  { id: 'mk7', domain: 'Mock Interviews', title: 'Schedule recurring mocks (Pramp / Exponent / Interviewing.io)', priority: 7, effortHours: 2, status: 'not-started', pinned: false, notes: '' },
  { id: 'mk8', domain: 'Mock Interviews', title: 'Record yourself & review playback', priority: 8, effortHours: 3, status: 'not-started', pinned: false, notes: '' },

  // Projects
  { id: 'p1', domain: 'Projects', title: 'Build mini LLM inference server (continuous batching + KV cache)', priority: 1, effortHours: 30, status: 'not-started', pinned: true, notes: '' },
  { id: 'p2', domain: 'Projects', title: 'Implement attention from scratch (MHA, RoPE, KV cache, masking)', priority: 2, effortHours: 15, status: 'not-started', pinned: true, notes: '' },
  { id: 'p3', domain: 'Projects', title: 'Build a RAG app w/ eval harness (retrieval + groundedness metrics)', priority: 3, effortHours: 20, status: 'not-started', pinned: false, notes: '' },
  { id: 'p4', domain: 'Projects', title: 'Build an agent with tool-use (MCP-style) + eval', priority: 4, effortHours: 20, status: 'not-started', pinned: false, notes: '' },
  { id: 'p5', domain: 'Projects', title: 'Fine-tune a small model w/ LoRA, measure quality delta', priority: 5, effortHours: 15, status: 'not-started', pinned: false, notes: '' },
  { id: 'p6', domain: 'Projects', title: 'Write a CUDA kernel (e.g., fused softmax or matmul)', priority: 6, effortHours: 25, status: 'not-started', pinned: false, notes: '' },
  { id: 'p7', domain: 'Projects', title: 'Distributed training toy: DDP/FSDP on multi-GPU', priority: 7, effortHours: 20, status: 'not-started', pinned: false, notes: '' },
  { id: 'p8', domain: 'Projects', title: 'Contribute to open-source ML repo (PR merged)', priority: 8, effortHours: 25, status: 'not-started', pinned: false, notes: '' },
];

const STORAGE_KEY = 'prep-state-v1';

export default function App() {
  const [tab, setTab] = useState('dashboard');
  const [topics, setTopics] = useState(DEFAULT_TOPICS);
  const [sessions, setSessions] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [domainFilter, setDomainFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [editEffort, setEditEffort] = useState(0);
  const [showAdd, setShowAdd] = useState(false);
  const [newItem, setNewItem] = useState({ domain: 'Coding', title: '', effortHours: 4 });
  const [showSession, setShowSession] = useState(false);
  const [newSession, setNewSession] = useState({ date: new Date().toISOString().slice(0, 10), durationMin: 60, topicId: '', summary: '' });
  const [copied, setCopied] = useState(false);

  // Load state
  useEffect(() => {
    (async () => {
      try {
        const r = await window.storage.get(STORAGE_KEY);
        if (r && r.value) {
          const d = JSON.parse(r.value);
          if (d.topics) setTopics(d.topics);
          if (d.sessions) setSessions(d.sessions);
        }
      } catch (e) {
        // first run
      }
      setLoaded(true);
    })();
  }, []);

  // Persist
  useEffect(() => {
    if (!loaded) return;
    (async () => {
      try {
        await window.storage.set(STORAGE_KEY, JSON.stringify({ topics, sessions }));
      } catch (e) {
        console.error('save failed', e);
      }
    })();
  }, [topics, sessions, loaded]);

  const stats = useMemo(() => {
    const byDomain = {};
    DOMAINS.forEach(d => {
      const items = topics.filter(t => t.domain === d);
      const done = items.filter(t => t.status === 'done').length;
      const inProg = items.filter(t => t.status === 'in-progress').length;
      const totalHours = items.reduce((s, t) => s + (t.effortHours || 0), 0);
      const doneHours = items.filter(t => t.status === 'done').reduce((s, t) => s + (t.effortHours || 0), 0);
      byDomain[d] = { total: items.length, done, inProg, totalHours, doneHours, pct: items.length ? Math.round((done / items.length) * 100) : 0 };
    });
    const totalDone = topics.filter(t => t.status === 'done').length;
    const totalInProg = topics.filter(t => t.status === 'in-progress').length;
    const totalSessionMin = sessions.reduce((s, x) => s + (x.durationMin || 0), 0);

    // streak: consecutive days from today with at least 1 session
    const dates = new Set(sessions.map(s => s.date));
    let streak = 0;
    let cur = new Date();
    while (true) {
      const d = cur.toISOString().slice(0, 10);
      if (dates.has(d)) {
        streak++;
        cur.setDate(cur.getDate() - 1);
      } else {
        break;
      }
    }

    return { byDomain, totalDone, totalInProg, total: topics.length, totalSessionMin, streak };
  }, [topics, sessions]);

  const filteredTopics = useMemo(() => {
    let list = topics;
    if (domainFilter !== 'All') list = list.filter(t => t.domain === domainFilter);
    if (statusFilter !== 'All') list = list.filter(t => t.status === statusFilter);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(t => t.title.toLowerCase().includes(q) || (t.notes || '').toLowerCase().includes(q) || t.domain.toLowerCase().includes(q));
    }
    // sort: pinned first, then by domain, then priority
    return [...list].sort((a, b) => {
      if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
      if (a.domain !== b.domain) return DOMAINS.indexOf(a.domain) - DOMAINS.indexOf(b.domain);
      return a.priority - b.priority;
    });
  }, [topics, domainFilter, statusFilter, search]);

  const cycleStatus = (id) => {
    setTopics(ts => ts.map(t => {
      if (t.id !== id) return t;
      const next = t.status === 'not-started' ? 'in-progress' : t.status === 'in-progress' ? 'done' : 'not-started';
      return { ...t, status: next };
    }));
  };

  const togglePin = (id) => {
    setTopics(ts => ts.map(t => t.id === id ? { ...t, pinned: !t.pinned } : t));
  };

  const deleteTopic = (id) => {
    setTopics(ts => ts.filter(t => t.id !== id));
  };

  const startEdit = (t) => {
    setEditingId(t.id);
    setEditTitle(t.title);
    setEditNotes(t.notes || '');
    setEditEffort(t.effortHours);
  };

  const saveEdit = () => {
    setTopics(ts => ts.map(t => t.id === editingId ? { ...t, title: editTitle, notes: editNotes, effortHours: Number(editEffort) || 0 } : t));
    setEditingId(null);
  };

  const addTopic = () => {
    if (!newItem.title.trim()) return;
    const id = 'u' + Date.now();
    const domainItems = topics.filter(t => t.domain === newItem.domain);
    const maxP = domainItems.reduce((m, t) => Math.max(m, t.priority), 0);
    setTopics(ts => [...ts, { id, domain: newItem.domain, title: newItem.title.trim(), priority: maxP + 1, effortHours: Number(newItem.effortHours) || 4, status: 'not-started', pinned: false, notes: '' }]);
    setNewItem({ domain: newItem.domain, title: '', effortHours: 4 });
    setShowAdd(false);
  };

  const logSession = () => {
    if (!newSession.topicId) return;
    const id = 's' + Date.now();
    setSessions(ss => [{ id, ...newSession, durationMin: Number(newSession.durationMin) || 0 }, ...ss]);
    setNewSession({ date: new Date().toISOString().slice(0, 10), durationMin: 60, topicId: '', summary: '' });
    setShowSession(false);
  };

  const deleteSession = (id) => setSessions(ss => ss.filter(s => s.id !== id));

  const exportSummary = async () => {
    let md = `# SWE Interview Prep — Progress Summary\n\n`;
    md += `**Overall:** ${stats.totalDone}/${stats.total} topics complete • ${Math.round(stats.totalSessionMin / 60)} hours logged • ${stats.streak}-day streak\n\n`;
    md += `## By Domain\n\n`;
    DOMAINS.forEach(d => {
      const s = stats.byDomain[d];
      md += `- **${d}**: ${s.done}/${s.total} done (${s.pct}%) — ${s.doneHours}/${s.totalHours}h\n`;
    });
    md += `\n## In Progress\n\n`;
    topics.filter(t => t.status === 'in-progress').forEach(t => {
      md += `- [${t.domain}] ${t.title} (${t.effortHours}h)\n`;
    });
    md += `\n## Pinned Priorities\n\n`;
    topics.filter(t => t.pinned && t.status !== 'done').forEach(t => {
      md += `- [${t.domain}] ${t.title} — ${t.status}\n`;
    });
    try {
      await navigator.clipboard.writeText(md);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      alert('Copy failed — try again');
    }
  };

  const topicById = (id) => topics.find(t => t.id === id);

  if (!loaded) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-xl font-semibold text-slate-900">SWE Interview Prep</h1>
              <p className="text-sm text-slate-500">Senior SDE / MLE @ frontier AI labs</p>
            </div>
            <button
              onClick={exportSummary}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-slate-900 text-white rounded-md hover:bg-slate-800 transition"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied!' : 'Share summary'}
            </button>
          </div>
          <div className="flex gap-1">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
              { id: 'topics', label: 'Topics', icon: BookOpen },
              { id: 'sessions', label: 'Sessions', icon: Calendar },
            ].map(t => {
              const Icon = t.icon;
              return (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`flex items-center gap-2 px-3 py-2 text-sm rounded-md transition ${tab === t.id ? 'bg-slate-100 text-slate-900 font-medium' : 'text-slate-600 hover:bg-slate-50'}`}
                >
                  <Icon className="w-4 h-4" />
                  {t.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Dashboard */}
        {tab === 'dashboard' && (
          <div className="space-y-6">
            {/* Top stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard icon={Target} label="Completed" value={`${stats.totalDone} / ${stats.total}`} sub={`${Math.round((stats.totalDone / stats.total) * 100)}% of plan`} />
              <StatCard icon={Loader2} label="In Progress" value={stats.totalInProg} sub="active topics" />
              <StatCard icon={Clock} label="Logged Time" value={`${Math.round(stats.totalSessionMin / 60)}h`} sub={`${sessions.length} sessions`} />
              <StatCard icon={Flame} label="Day Streak" value={stats.streak} sub={stats.streak > 0 ? 'keep going' : 'log today'} />
            </div>

            {/* Domain progress */}
            <div className="bg-white border border-slate-200 rounded-lg p-5">
              <h2 className="font-semibold text-slate-900 mb-4">Progress by domain</h2>
              <div className="space-y-3">
                {DOMAINS.map(d => {
                  const s = stats.byDomain[d];
                  return (
                    <div key={d}>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-0.5 rounded border ${DOMAIN_COLORS[d]}`}>{d}</span>
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
            </div>

            {/* Pinned */}
            <div className="bg-white border border-slate-200 rounded-lg p-5">
              <h2 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <Pin className="w-4 h-4" />
                Pinned priorities
              </h2>
              <div className="space-y-2">
                {topics.filter(t => t.pinned).length === 0 && (
                  <p className="text-sm text-slate-500">No pinned items. Pin your top priorities in the Topics tab.</p>
                )}
                {topics.filter(t => t.pinned).map(t => (
                  <div key={t.id} className="flex items-center gap-3 p-2 rounded hover:bg-slate-50">
                    <StatusButton status={t.status} onClick={() => cycleStatus(t.id)} />
                    <span className={`text-xs px-2 py-0.5 rounded border ${DOMAIN_COLORS[t.domain]}`}>{t.domain}</span>
                    <span className={`text-sm flex-1 ${t.status === 'done' ? 'line-through text-slate-400' : 'text-slate-900'}`}>{t.title}</span>
                    <span className="text-xs text-slate-500">{t.effortHours}h</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent sessions */}
            <div className="bg-white border border-slate-200 rounded-lg p-5">
              <h2 className="font-semibold text-slate-900 mb-3">Recent sessions</h2>
              {sessions.length === 0 ? (
                <p className="text-sm text-slate-500">No sessions logged yet. Go to Sessions tab to log your first study block.</p>
              ) : (
                <div className="space-y-2">
                  {sessions.slice(0, 5).map(s => {
                    const t = topicById(s.topicId);
                    return (
                      <div key={s.id} className="flex items-center gap-3 p-2 rounded hover:bg-slate-50 text-sm">
                        <span className="text-slate-500 w-20">{s.date}</span>
                        <span className="text-slate-600 w-16">{s.durationMin}min</span>
                        {t && <span className={`text-xs px-2 py-0.5 rounded border ${DOMAIN_COLORS[t.domain]}`}>{t.domain}</span>}
                        <span className="text-slate-700 flex-1 truncate">{t ? t.title : '(deleted topic)'}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Topics */}
        {tab === 'topics' && (
          <div className="space-y-4">
            {/* Toolbar */}
            <div className="bg-white border border-slate-200 rounded-lg p-3 flex flex-wrap items-center gap-2">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search topics and notes..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400"
                />
              </div>
              <select
                value={domainFilter}
                onChange={e => setDomainFilter(e.target.value)}
                className="px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400 bg-white"
              >
                <option>All</option>
                {DOMAINS.map(d => <option key={d}>{d}</option>)}
              </select>
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                className="px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400 bg-white"
              >
                <option value="All">All status</option>
                <option value="not-started">Not started</option>
                <option value="in-progress">In progress</option>
                <option value="done">Done</option>
              </select>
              <button
                onClick={() => setShowAdd(!showAdd)}
                className="flex items-center gap-1 px-3 py-2 text-sm bg-slate-900 text-white rounded-md hover:bg-slate-800"
              >
                <Plus className="w-4 h-4" /> Add topic
              </button>
            </div>

            {/* Add form */}
            {showAdd && (
              <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-[1fr_180px_100px] gap-2">
                  <input
                    type="text"
                    placeholder="Topic title..."
                    value={newItem.title}
                    onChange={e => setNewItem({ ...newItem, title: e.target.value })}
                    className="px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400"
                  />
                  <select
                    value={newItem.domain}
                    onChange={e => setNewItem({ ...newItem, domain: e.target.value })}
                    className="px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400 bg-white"
                  >
                    {DOMAINS.map(d => <option key={d}>{d}</option>)}
                  </select>
                  <input
                    type="number"
                    placeholder="Hours"
                    value={newItem.effortHours}
                    onChange={e => setNewItem({ ...newItem, effortHours: e.target.value })}
                    className="px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:border-slate-400"
                  />
                </div>
                <div className="flex gap-2">
                  <button onClick={addTopic} className="px-3 py-1.5 text-sm bg-slate-900 text-white rounded-md hover:bg-slate-800">Add</button>
                  <button onClick={() => setShowAdd(false)} className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-md">Cancel</button>
                </div>
              </div>
            )}

            {/* Topics list */}
            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
              {filteredTopics.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-sm">No topics match your filters.</div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {filteredTopics.map(t => (
                    <div key={t.id} className="p-3 hover:bg-slate-50 group">
                      {editingId === t.id ? (
                        <div className="space-y-2">
                          <input
                            value={editTitle}
                            onChange={e => setEditTitle(e.target.value)}
                            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:border-slate-500"
                          />
                          <textarea
                            value={editNotes}
                            onChange={e => setEditNotes(e.target.value)}
                            placeholder="Notes, links, key insights..."
                            rows={3}
                            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:border-slate-500 resize-y"
                          />
                          <div className="flex items-center gap-2">
                            <label className="text-xs text-slate-500">Hours:</label>
                            <input
                              type="number"
                              value={editEffort}
                              onChange={e => setEditEffort(e.target.value)}
                              className="w-20 px-2 py-1 text-sm border border-slate-300 rounded-md"
                            />
                            <button onClick={saveEdit} className="ml-auto flex items-center gap-1 px-3 py-1.5 text-sm bg-slate-900 text-white rounded-md hover:bg-slate-800">
                              <Save className="w-3.5 h-3.5" /> Save
                            </button>
                            <button onClick={() => setEditingId(null)} className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-md">Cancel</button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-start gap-3">
                          <StatusButton status={t.status} onClick={() => cycleStatus(t.id)} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className={`text-xs px-2 py-0.5 rounded border ${DOMAIN_COLORS[t.domain]}`}>{t.domain}</span>
                              <span className="text-xs text-slate-400">#{t.priority}</span>
                              <span className={`text-sm ${t.status === 'done' ? 'line-through text-slate-400' : 'text-slate-900'}`}>{t.title}</span>
                            </div>
                            {t.notes && (
                              <div className="text-xs text-slate-500 mt-1 whitespace-pre-wrap">{t.notes}</div>
                            )}
                          </div>
                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
                            <span className="text-xs text-slate-500 mr-2">{t.effortHours}h</span>
                            <button onClick={() => togglePin(t.id)} className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded">
                              {t.pinned ? <Pin className="w-3.5 h-3.5 fill-current text-amber-500" /> : <Pin className="w-3.5 h-3.5" />}
                            </button>
                            <button onClick={() => startEdit(t)} className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded">
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>
                            <button onClick={() => deleteTopic(t.id)} className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded">
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                          {t.pinned && (
                            <div className="opacity-100 group-hover:opacity-0 transition absolute right-3">
                              <Pin className="w-3.5 h-3.5 fill-current text-amber-500" />
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Sessions */}
        {tab === 'sessions' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-slate-900">Session log</h2>
                <p className="text-sm text-slate-500">Track what you studied and for how long.</p>
              </div>
              <button
                onClick={() => setShowSession(!showSession)}
                className="flex items-center gap-1 px-3 py-2 text-sm bg-slate-900 text-white rounded-md hover:bg-slate-800"
              >
                <Plus className="w-4 h-4" /> Log session
              </button>
            </div>

            {showSession && (
              <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-[140px_120px_1fr] gap-2">
                  <input
                    type="date"
                    value={newSession.date}
                    onChange={e => setNewSession({ ...newSession, date: e.target.value })}
                    className="px-3 py-2 text-sm border border-slate-200 rounded-md"
                  />
                  <input
                    type="number"
                    placeholder="Minutes"
                    value={newSession.durationMin}
                    onChange={e => setNewSession({ ...newSession, durationMin: e.target.value })}
                    className="px-3 py-2 text-sm border border-slate-200 rounded-md"
                  />
                  <select
                    value={newSession.topicId}
                    onChange={e => setNewSession({ ...newSession, topicId: e.target.value })}
                    className="px-3 py-2 text-sm border border-slate-200 rounded-md bg-white"
                  >
                    <option value="">Select topic...</option>
                    {DOMAINS.map(d => (
                      <optgroup key={d} label={d}>
                        {topics.filter(t => t.domain === d).map(t => (
                          <option key={t.id} value={t.id}>{t.title}</option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>
                <textarea
                  placeholder="What did you cover? Key insights, blockers..."
                  value={newSession.summary}
                  onChange={e => setNewSession({ ...newSession, summary: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-md resize-y"
                />
                <div className="flex gap-2">
                  <button onClick={logSession} className="px-3 py-1.5 text-sm bg-slate-900 text-white rounded-md hover:bg-slate-800">Save session</button>
                  <button onClick={() => setShowSession(false)} className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-md">Cancel</button>
                </div>
              </div>
            )}

            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
              {sessions.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-sm">No sessions logged yet.</div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {sessions.map(s => {
                    const t = topicById(s.topicId);
                    return (
                      <div key={s.id} className="p-3 hover:bg-slate-50 group">
                        <div className="flex items-start gap-3">
                          <div className="text-xs text-slate-500 w-20 pt-0.5">{s.date}</div>
                          <div className="text-xs text-slate-600 w-16 pt-0.5">{s.durationMin} min</div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              {t && <span className={`text-xs px-2 py-0.5 rounded border ${DOMAIN_COLORS[t.domain]}`}>{t.domain}</span>}
                              <span className="text-sm text-slate-900">{t ? t.title : '(deleted topic)'}</span>
                            </div>
                            {s.summary && <div className="text-xs text-slate-500 mt-1 whitespace-pre-wrap">{s.summary}</div>}
                          </div>
                          <button onClick={() => deleteSession(s.id)} className="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition">
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
        )}
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, sub }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
        <Icon className="w-3.5 h-3.5" />
        {label}
      </div>
      <div className="text-2xl font-semibold text-slate-900">{value}</div>
      <div className="text-xs text-slate-500 mt-1">{sub}</div>
    </div>
  );
}

function StatusButton({ status, onClick }) {
  const cfg = {
    'not-started': { icon: Circle, cls: 'text-slate-300 hover:text-slate-500' },
    'in-progress': { icon: Loader2, cls: 'text-amber-500' },
    'done': { icon: Check, cls: 'text-emerald-600' },
  }[status];
  const Icon = cfg.icon;
  return (
    <button onClick={onClick} className={`mt-0.5 ${cfg.cls} transition`} title={status}>
      <Icon className="w-5 h-5" />
    </button>
  );
}
