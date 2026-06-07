import type { MouseEvent } from 'react';
import { Circle, Contrast, CircleCheckBig, Flame } from 'lucide-react';
import type { Status, Domain } from '../types';

// Warm-compatible domain chip tints keyed by the domain's stored hue name.
const DOMAIN_COLORS: Record<string, { bg: string; fg: string; bd: string }> = {
  indigo: { bg: 'oklch(0.945 0.040 280)', fg: 'oklch(0.470 0.120 280)', bd: 'oklch(0.880 0.050 280)' },
  blue: { bg: 'oklch(0.948 0.040 240)', fg: 'oklch(0.480 0.115 245)', bd: 'oklch(0.882 0.050 240)' },
  violet: { bg: 'oklch(0.948 0.040 305)', fg: 'oklch(0.480 0.120 305)', bd: 'oklch(0.884 0.050 305)' },
  amber: { bg: 'oklch(0.950 0.055 75)', fg: 'oklch(0.520 0.110 58)', bd: 'oklch(0.885 0.065 70)' },
  emerald: { bg: 'oklch(0.948 0.045 158)', fg: 'oklch(0.470 0.100 160)', bd: 'oklch(0.880 0.055 158)' },
  rose: { bg: 'oklch(0.950 0.040 18)', fg: 'oklch(0.520 0.130 22)', bd: 'oklch(0.886 0.050 18)' },
};

export function nextStatus(s: Status): Status {
  return s === 'not-started' ? 'in-progress' : s === 'in-progress' ? 'done' : 'not-started';
}

export function StatusButton({
  status,
  onClick,
  size = 22,
}: {
  status: Status;
  onClick: (e: MouseEvent<HTMLButtonElement>) => void;
  size?: number;
}) {
  const cfg = {
    'not-started': { Icon: Circle, color: 'var(--faint)', sw: 1.8, title: 'Not started' },
    'in-progress': { Icon: Contrast, color: 'var(--warn)', sw: 2.2, title: 'In progress' },
    done: { Icon: CircleCheckBig, color: 'var(--ok)', sw: 2.2, title: 'Done' },
  }[status];
  const { Icon } = cfg;
  return (
    <button
      onClick={onClick}
      title={cfg.title}
      className="shrink-0"
      style={{
        background: 'transparent', border: 'none', padding: 4, margin: -4, cursor: 'pointer',
        color: cfg.color, display: 'inline-flex', borderRadius: 8,
      }}
    >
      <Icon size={size} strokeWidth={cfg.sw} />
    </button>
  );
}

export function DomainChip({ domain, small }: { domain?: Domain; small?: boolean }) {
  if (!domain) return null;
  const c = DOMAIN_COLORS[domain.color] ?? DOMAIN_COLORS.amber;
  return (
    <span
      className="chip"
      style={{ background: c.bg, color: c.fg, borderColor: c.bd, fontSize: small ? 11.5 : 12 }}
    >
      {domain.name}
    </span>
  );
}

export function Mark({ size = 40, radius }: { size?: number; radius?: number }) {
  return (
    <span className="mark" style={{ width: size, height: size, borderRadius: radius ?? size * 0.32 }}>
      <Flame size={size * 0.52} strokeWidth={2} fill="rgba(255,255,255,0.18)" />
    </span>
  );
}
