'use client';

import { useAppStore } from '@/store/app';
import { Anno } from '@/components/atelier/Anno';

export function CreditsPill() {
  const credits = useAppStore((s) => s.mockCredits);
  return (
    <div
      className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-card"
      style={{ border: '1px solid #D8D0BE' }}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-olive" />
      <Anno>credits</Anno>
      <span className="font-mono text-[12px] text-ink">{credits.toString().padStart(2, '0')}</span>
    </div>
  );
}
