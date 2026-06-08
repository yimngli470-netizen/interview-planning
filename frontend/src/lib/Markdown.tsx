import { Component, useEffect, useRef, useState } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import mermaid from 'mermaid';
import 'katex/dist/katex.min.css';

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

function CodeBlock({ className, children }: { className?: string; children?: React.ReactNode }) {
  const text = String(children ?? '');
  if (className && /\blanguage-mermaid\b/.test(className)) {
    return <Mermaid chart={text.replace(/\n$/, '')} />;
  }
  // A fenced block (has a language- class or contains newlines) vs inline code.
  if (className || text.includes('\n')) {
    return <pre className="md-pre"><code className={className}>{children}</code></pre>;
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

export default function Markdown({ children }: { children: string }) {
  return (
    <div className="md">
      <MdBoundary raw={children}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeKatex]}
          components={{
            code: CodeBlock as never,
            // react-markdown wraps fenced code in <pre>; our CodeBlock already
            // emits its own <pre>, so make the outer pre a passthrough.
            pre: ({ children }) => <>{children}</>,
          }}
        >
          {children}
        </ReactMarkdown>
      </MdBoundary>
    </div>
  );
}
