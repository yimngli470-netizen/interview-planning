// Lazy, in-browser Python execution via Pyodide (CPython compiled to WASM).
// Nothing runs on the server — the ~6 MB runtime is fetched from the CDN the
// first time a user clicks "Run", then reused for every later run this session.
// No npm dependency: we inject the CDN <script> and call the global it defines.

const PYODIDE_VERSION = '0.26.4';
const CDN = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

declare global {
  interface Window {
    loadPyodide?: (opts: { indexURL: string }) => Promise<PyodideLike>;
  }
}

interface PyodideLike {
  runPythonAsync: (code: string) => Promise<unknown>;
  setStdout: (opts: { batched: (s: string) => void }) => void;
  setStderr: (opts: { batched: (s: string) => void }) => void;
  isPyProxy?: (x: unknown) => boolean;
}

let pyodidePromise: Promise<PyodideLike> | null = null;

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) return resolve();
    const s = document.createElement('script');
    s.src = src;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error('Failed to download the Python runtime.'));
    document.head.appendChild(s);
  });
}

// Singleton: at most one runtime is ever loaded, shared across every code block.
export function getPyodide(): Promise<PyodideLike> {
  if (!pyodidePromise) {
    pyodidePromise = (async () => {
      await loadScript(CDN + 'pyodide.js');
      if (!window.loadPyodide) throw new Error('Python runtime did not load.');
      return window.loadPyodide({ indexURL: CDN });
    })().catch((e) => {
      pyodidePromise = null; // allow a retry on the next click
      throw e;
    });
  }
  return pyodidePromise;
}

export interface RunResult {
  output: string;
  error: boolean;
}

// Run a snippet and collect everything the user would see in a terminal:
// stdout, stderr, then the value of the final expression (REPL-style).
export async function runPython(code: string): Promise<RunResult> {
  const pyodide = await getPyodide();
  const chunks: string[] = [];
  pyodide.setStdout({ batched: (s) => chunks.push(s) });
  pyodide.setStderr({ batched: (s) => chunks.push(s) });
  try {
    const result = await pyodide.runPythonAsync(code);
    let out = chunks.join('');
    if (result !== undefined && result !== null) {
      const repr = String(result);
      if (repr) out += (out && !out.endsWith('\n') ? '\n' : '') + repr;
    }
    if (pyodide.isPyProxy?.(result)) (result as { destroy: () => void }).destroy();
    return { output: out.trim() || '(ran with no output)', error: false };
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return { output: (chunks.join('') + msg).trim(), error: true };
  }
}
