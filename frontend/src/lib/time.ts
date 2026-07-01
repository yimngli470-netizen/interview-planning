// The backend sends naive UTC timestamps (no 'Z'). JS would parse those as
// LOCAL time, so we append 'Z' to force UTC before converting to the user's
// local timezone.
export function parseUTC(s: string): Date {
  return new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : s + 'Z');
}

// Live-counted minutes for a study session. A finalized session reports its
// server-capped `duration_min` verbatim. An ACTIVE session ticks live to `nowTs`
// only while activity is recent; once the last present beat is older than the
// idle grace (laptop closed, tab dormant), it freezes at `last_active_at` — the
// same boundary the server counts to. This prevents a still-open session that
// spanned a long dormant gap from displaying its full wall-clock span.
const SESSION_IDLE_GRACE_MS = 120_000; // matches server IDLE_GRACE_SECONDS/STALE_SECONDS
export function sessionMinutes(
  s: { active: boolean; started_at: string; last_active_at: string; duration_min: number },
  nowTs: number,
): number {
  if (!s.active) return s.duration_min;
  const start = parseUTC(s.started_at).getTime();
  const lastActive = parseUTC(s.last_active_at).getTime();
  const end = nowTs - lastActive < SESSION_IDLE_GRACE_MS ? nowTs : lastActive;
  return Math.max(0, (end - start) / 60000);
}

export function localDateKey(d: Date): string {
  // YYYY-MM-DD in the user's local timezone
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// "1h 23m" / "45m" / "0m"
export function formatHM(totalMinutes: number): string {
  const m = Math.max(0, Math.round(totalMinutes));
  const h = Math.floor(m / 60);
  const rem = m % 60;
  return h > 0 ? `${h}h ${rem}m` : `${rem}m`;
}

// "01:23:45" live clock from a number of seconds
export function formatClock(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  const hh = String(Math.floor(s / 3600)).padStart(2, '0');
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, '0');
  const ss = String(s % 60).padStart(2, '0');
  return `${hh}:${mm}:${ss}`;
}
