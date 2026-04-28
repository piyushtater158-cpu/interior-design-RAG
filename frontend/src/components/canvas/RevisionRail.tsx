'use client';

import { useSessionStore, type Revision } from '@/store/session';
import { Anno } from '@/components/atelier/Anno';
import { revLabel, timestamp } from '@/lib/format';

export function RevisionRail({ className = '' }: { className?: string }) {
  const revisions = useSessionStore((s) => s.revisions);
  const current = useSessionStore((s) => s.currentGenerationId);
  const setCurrent = useSessionStore((s) => s.setCurrent);

  return (
    <aside
      className={`flex flex-col gap-3 overflow-y-auto ${className}`}
      style={{ background: '#FBF8F2', borderRight: '1px solid #D8D0BE' }}
    >
      <div className="px-4 pt-4 pb-2 sticky top-0 bg-paper z-10" style={{ borderBottom: '1px solid #D8D0BE' }}>
        <Anno className="block mb-1">revision stack</Anno>
        <div className="font-serif text-[18px]">{revisions.length} revisions</div>
      </div>
      <div className="px-3 pb-4 flex flex-col gap-2">
        {revisions.map((r, i) => (
          <Thumb key={r.generationId} rev={r} active={r.generationId === current} index={i} onClick={() => setCurrent(r.generationId)} />
        ))}
        {revisions.length === 0 && (
          <div className="px-2 py-6 text-center">
            <Anno>no revisions yet</Anno>
          </div>
        )}
      </div>
    </aside>
  );
}

function Thumb({ rev, active, index, onClick }: { rev: Revision; active: boolean; index: number; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col gap-1.5 rounded-lg p-2 bg-transparent cursor-pointer text-left"
      style={{
        border: active ? '1.5px solid #1C1B17' : '1px solid #D8D0BE',
        background: active ? '#FFFFFF' : '#FEFCF6',
      }}
    >
      <div className="aspect-[4/3] rounded overflow-hidden bg-bone">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={rev.outputUrl} alt={revLabel(index)} className="w-full h-full object-cover" />
      </div>
      <div className="flex items-center justify-between">
        <Anno color={active ? '#1C1B17' : undefined}>{revLabel(index)}</Anno>
        <span
          className="text-[10px] font-mono uppercase tracking-wider"
          style={{ color: rev.kind === 'commit' ? '#3D4A2A' : rev.kind === 'edit' ? '#B85C3A' : '#8B8676' }}
        >
          {rev.kind}
        </span>
      </div>
      <Anno>{timestamp(rev.createdAt)}</Anno>
    </button>
  );
}
