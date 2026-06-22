import { Component, memo, useEffect, useRef, useState } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkBreaks from 'remark-breaks';
import rehypeKatex from 'rehype-katex';
import mermaid from 'mermaid';
import 'katex/dist/katex.min.css';
import { runPython } from './pyodide';

// Initialize mermaid once. `neutral` reads well on the warm paper background.
let mermaidReady = false;
function ensureMermaid() {
  if (mermaidReady) return;
  mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'strict', fontFamily: 'var(--font-ui)' });
  mermaidReady = true;
}

let mermaidSeq = 0;

// Off-screen sandbox so mermaid's temporary measurement node never appends to
// document.body and shifts the page (the "jump back and forth" while opening).
let _sandbox: HTMLElement | null = null;
function sandbox(): HTMLElement {
  if (!_sandbox) {
    _sandbox = document.createElement('div');
    _sandbox.style.cssText =
      'position:fixed;left:-10000px;top:0;width:0;height:0;overflow:hidden;visibility:hidden;contain:strict';
    document.body.appendChild(_sandbox);
  }
  return _sandbox;
}

function Mermaid({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    let alive = true;
    ensureMermaid();
    const id = `mmd-${mermaidSeq++}`;
    mermaid
      .render(id, chart, sandbox())
      .then(({ svg }) => { if (alive && ref.current) { ref.current.innerHTML = svg; setErr(false); } })
      .catch(() => { if (alive) setErr(true); });
    return () => { alive = false; };
  }, [chart]);

  if (err) {
    // Invalid diagram — fall back to showing the source rather than breaking.
    return <pre className="md-pre"><code>{chart}</code></pre>;
  }
  return <div ref={ref} className="md-mermaid" style={{ textAlign: 'center', margin: '12px 0' }} />;
}

const PYTHON_RE = /\blanguage-(python|py)\b/;

// A fenced code block. Python blocks (```python) get a "Run" button that
// executes the snippet in-browser via Pyodide and shows the output inline.
function RunnableCode({ className, code }: { className?: string; code: string }) {
  const runnable = !!className && PYTHON_RE.test(className);
  const [out, setOut] = useState<string | null>(null);
  const [err, setErr] = useState(false);
  const [running, setRunning] = useState(false);

  const run = async () => {
    setRunning(true);
    setOut(null);
    try {
      const { output, error } = await runPython(code);
      setOut(output);
      setErr(error);
    } catch (e) {
      setOut(e instanceof Error ? e.message : String(e));
      setErr(true);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="md-code-block">
      <pre className="md-pre"><code className={className}>{code}</code></pre>
      {runnable && (
        <div className="md-run">
          <button type="button" className="md-run-btn" onClick={run} disabled={running}>
            {running ? 'Running…' : '▶ Run'}
          </button>
          {out !== null && (
            <button type="button" className="md-run-clear" onClick={() => setOut(null)}>Clear</button>
          )}
        </div>
      )}
      {out !== null && (
        <pre className={'md-out' + (err ? ' md-out-err' : '')}>{out}</pre>
      )}
    </div>
  );
}

function CodeBlock({ className, children }: { className?: string; children?: React.ReactNode }) {
  const text = String(children ?? '');
  if (className && /\blanguage-mermaid\b/.test(className)) {
    return <Mermaid chart={text.replace(/\n$/, '')} />;
  }
  // A fenced block (has a language- class or contains newlines) vs inline code.
  if (className || text.includes('\n')) {
    return <RunnableCode className={className} code={text.replace(/\n$/, '')} />;
  }
  return <code className="md-code">{children}</code>;
}

// A render crash in markdown/katex must not blank the panel — fall back to the
// raw source and log to the console so it's debuggable.
class MdBoundary extends Component<{ raw: string; children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(err: Error, info: ErrorInfo) { console.error('Markdown render failed:', err, info); }
  render() {
    if (this.state.failed) {
      return <pre className="md-pre" style={{ whiteSpace: 'pre-wrap' }}>{this.props.raw}</pre>;
    }
    return this.props.children;
  }
}

// All of these MUST be stable (module-level) identities. If they were recreated
// per render, react-markdown would see new component/plugin references on every
// parent re-render (the app ticks every 1s) and remount the whole markdown
// subtree — which made Mermaid diagrams flicker out/in and the page jump.
const PresPassthrough = ({ children }: { children?: ReactNode }) => <>{children}</>;
const MD_COMPONENTS = { code: CodeBlock as never, pre: PresPassthrough };
const REMARK_PLUGINS = [remarkGfm, remarkMath, remarkBreaks];
const REHYPE_PLUGINS = [rehypeKatex];

function MarkdownInner({ children }: { children: string }) {
  return (
    <div className="md">
      <MdBoundary raw={children}>
        <ReactMarkdown remarkPlugins={REMARK_PLUGINS} rehypePlugins={REHYPE_PLUGINS} components={MD_COMPONENTS}>
          {children}
        </ReactMarkdown>
      </MdBoundary>
    </div>
  );
}

// memo: only re-parse/re-render when the markdown text itself changes, so the
// app's per-second re-render never touches an already-rendered explanation.
export default memo(MarkdownInner);
