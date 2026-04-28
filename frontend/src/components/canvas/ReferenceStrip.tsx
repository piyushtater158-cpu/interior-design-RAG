'use client';

import { useSessionStore } from '@/store/session';
import { Anno } from '@/components/atelier/Anno';

export function ReferenceStrip({ orientation = 'grid' }: { orientation?: 'grid' | 'row' }) {
  const refs = useSessionStore((s) => s.references);
  if (refs.length === 0) {
    return (
      <div className="p-4">
        <Anno>no references retrieved</Anno>
      </div>
    );
  }
  return (
    <div className="p-3">
      <Anno className="block mb-2 px-1">retrieved references · {refs.length}</Anno>
      <div
        className={
          orientation === 'row'
            ? 'flex gap-2 overflow-x-auto pb-1'
            : 'grid grid-cols-2 gap-2'
        }
      >
        {refs.map((r) => (
          <div
            key={r.id}
            className="rounded-lg overflow-hidden bg-card relative shrink-0"
            style={{ border: '1px solid #D8D0BE', width: orientation === 'row' ? 120 : undefined }}
          >
            <div className="aspect-[4/3] bg-bone">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={r.url} alt="" className="w-full h-full object-cover" />
            </div>
            <div className="absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded bg-black/55 text-paper text-[10px] font-mono">
              {Math.round(r.similarity * 100)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
