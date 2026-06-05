import type { MouseEvent } from 'react';
import { Circle, Loader2, Check } from 'lucide-react';
import type { Status } from '../types';

export function domainClasses(color: string): string {
  // color is a tailwind hue name stored on the domain (blue, violet, ...)
  return `bg-${color}-100 text-${color}-700 border-${color}-200`;
}

export function nextStatus(s: Status): Status {
  return s === 'not-started' ? 'in-progress' : s === 'in-progress' ? 'done' : 'not-started';
}

export function StatusButton({
  status,
  onClick,
  iconClass = 'w-5 h-5',
}: {
  status: Status;
  onClick: (e: MouseEvent<HTMLButtonElement>) => void;
  iconClass?: string;
}) {
  const cfg = {
    'not-started': { Icon: Circle, cls: 'text-slate-300 hover:text-slate-500' },
    'in-progress': { Icon: Loader2, cls: 'text-amber-500' },
    done: { Icon: Check, cls: 'text-emerald-600' },
  }[status];
  const { Icon } = cfg;
  return (
    <button onClick={onClick} className={`shrink-0 transition ${cfg.cls}`} title={status}>
      <Icon className={iconClass} />
    </button>
  );
}
