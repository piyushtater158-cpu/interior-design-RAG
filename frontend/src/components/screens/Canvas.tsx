'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGate } from '@/components/shared/AuthGate';
import { MobStatusBar } from '@/components/mobile/MobStatusBar';
import { MobNav } from '@/components/mobile/MobNav';
import { MobSheet } from '@/components/mobile/MobSheet';
import { ShelfBtn } from '@/components/mobile/ShelfBtn';
import { RoomRender } from '@/components/atelier/RoomRender';
import { Btn } from '@/components/atelier/Btn';
import { Anno } from '@/components/atelier/Anno';
import { AtelierMark } from '@/components/atelier/AtelierMark';
import { CreditsPill } from '@/components/canvas/CreditsPill';
import { RevisionRail } from '@/components/canvas/RevisionRail';
import { ChatPanel } from '@/components/canvas/ChatPanel';
import { ReferenceStrip } from '@/components/canvas/ReferenceStrip';
import { Spinner } from '@/components/shared/Loader';
import { ErrorBanner } from '@/components/shared/ErrorBanner';
import { useSessionStore } from '@/store/session';
import { useAppStore } from '@/store/app';
import { useResponsive } from '@/hooks/useResponsive';
import { useHydrated } from '@/hooks/useHydrated';
import { api, ApiError, absoluteUrl } from '@/lib/api';
import { revLabel } from '@/lib/format';

type Sheet = 'chat' | 'refs' | 'commit' | null;

function CanvasInner({ sessionId }: { sessionId: string }) {
  const router = useRouter();
  const bp = useResponsive();
  const hydrated = useHydrated();

  const revisions = useSessionStore((s) => s.revisions);
  const currentId = useSessionStore((s) => s.currentGenerationId);
  const storedSessionId = useSessionStore((s) => s.sessionId);
  const setRevisions = useSessionStore((s) => s.setRevisions);
  const setCurrent = useSessionStore((s) => s.setCurrent);
  const appendRevision = useSessionStore((s) => s.appendRevision);
  const roomType = useSessionStore((s) => s.roomType);
  const decrementCredits = useAppStore((s) => s.decrementCredits);

  const [sheet, setSheet] = useState<Sheet>(null);
  const [committing, setCommitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const current = useMemo(
    () => revisions.find((r) => r.generationId === currentId) ?? revisions[revisions.length - 1],
    [revisions, currentId],
  );
  const currentIndex = current ? revisions.findIndex((r) => r.generationId === current.generationId) : -1;

  // Rehydrate on refresh if the store is empty but this session exists on the backend.
  useEffect(() => {
    if (!hydrated) return;
    if (revisions.length > 0) return;
    if (storedSessionId !== sessionId) return;
    let alive = true;
    (async () => {
      try {
        const items = await api.listSessionGenerations(sessionId);
        if (!alive || items.length === 0) return;
        setRevisions(
          items.map((it) => ({
            generationId: it.generation_id,
            kind: it.kind as 'draft' | 'edit' | 'commit',
            outputUrl: absoluteUrl(it.output_url ?? ''),
            parentId: it.parent_generation_id ?? null,
            createdAt: Date.parse(it.created_at),
            modelId: it.model_id ?? undefined,
          })),
        );
        const last = items[items.length - 1].generation_id;
        if (last) setCurrent(last);
      } catch {
        /* ignore */
      }
    })();
    return () => { alive = false; };
  }, [hydrated, revisions.length, storedSessionId, sessionId, setRevisions, setCurrent]);

  async function commit() {
    if (!currentId) return;
    setCommitting(true);
    setError(null);
    try {
      const res = await api.generateCommit({ generation_id: currentId, session_id: sessionId });
      appendRevision({
        generationId: res.generation_id,
        kind: 'commit',
        outputUrl: absoluteUrl(res.output_url),
        parentId: currentId,
        createdAt: Date.now(),
        modelId: res.model_id,
        backendId: res.backend_id,
      });
      decrementCredits(3);
      setSheet(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Commit failed.');
    } finally {
      setCommitting(false);
    }
  }

  const isDesktop = bp === 'desktop';
  const isIpad = bp === 'ipad';

  const canvasNode = (
    <div className="relative w-full h-full">
      <RoomRender
        type={(roomType ?? 'bedroom') as 'bedroom' | 'dining' | 'kitchen' | 'mandir'}
        tone={current?.tone ?? 'warm'}
        imageUrl={current?.outputUrl ?? null}
        label={current ? `${revLabel(currentIndex)} · ${current.kind}` : undefined}
        anno={current?.modelId ? `model · ${current.modelId}` : undefined}
      />
      {!current && (
        <div className="absolute inset-0 flex items-center justify-center bg-bone/60">
          <Spinner />
        </div>
      )}
    </div>
  );

  // Desktop — three-rail layout
  if (isDesktop) {
    return (
      <div className="min-h-screen flex flex-col bg-bone-deep">
        <div className="flex items-center justify-between px-8 py-3" style={{ borderBottom: '1px solid #D8D0BE', background: '#FBF8F2' }}>
          <div className="flex items-center gap-3">
            <button onClick={() => router.push('/app')} className="bg-transparent border-0 cursor-pointer p-0 flex items-center gap-2">
              <AtelierMark size={22} />
              <span className="font-serif text-[18px]">Atelier</span>
            </button>
            <Anno className="ml-4">session · {sessionId.slice(0, 8)}</Anno>
          </div>
          <div className="flex items-center gap-3">
            <Btn size="sm" variant="ghost" onClick={() => router.push(`/app/session/${sessionId}/export`)} disabled={!current}>
              Export →
            </Btn>
            <CreditsPill />
          </div>
        </div>
        <div className="flex-1 grid" style={{ gridTemplateColumns: '20% 1fr 25%', minHeight: 0 }}>
          <RevisionRail className="h-full" />
          <div className="relative">{canvasNode}</div>
          <aside className="flex flex-col h-full" style={{ background: '#FBF8F2', borderLeft: '1px solid #D8D0BE' }}>
            <div className="border-b" style={{ borderColor: '#D8D0BE' }}>
              <ReferenceStrip />
            </div>
            <div className="flex-1 min-h-0 flex flex-col">
              <ChatPanel />
            </div>
            <div className="border-t p-3 flex gap-2" style={{ borderColor: '#D8D0BE' }}>
              <Btn variant="clay" className="flex-1" onClick={commit} disabled={committing || !current}>
                {committing ? <Spinner size={14} color="#FBF8F2" /> : null}
                Commit · 3cr
              </Btn>
            </div>
          </aside>
        </div>
        {error && <div className="fixed bottom-4 right-4 max-w-sm"><ErrorBanner message={error} onDismiss={() => setError(null)} /></div>}
      </div>
    );
  }

  // Mobile + iPad share the shelf UI; iPad just gets a wider canvas
  return (
    <div
      className="min-h-screen relative flex flex-col"
      style={{ background: '#1C1B17' }}
    >
      <div className="shrink-0">
        <MobStatusBar dark />
        <MobNav
          title={current ? `${revLabel(currentIndex)} · ${current.kind}` : 'Loading…'}
          sub={`session · ${sessionId.slice(0, 8)}`}
          onBack={() => router.push('/app')}
          dark
          trailing={<CreditsPill />}
        />
      </div>

      <div className={`relative flex-1 ${isIpad ? 'px-8 py-4' : ''}`}>
        <div className={`w-full h-full ${isIpad ? 'max-w-[900px] mx-auto rounded-2xl overflow-hidden shadow-hi' : ''}`}>
          {canvasNode}
        </div>
      </div>

      <div
        className="shrink-0 flex gap-2 px-4 pt-3 pb-5"
        style={{ background: 'rgba(28,27,23,0.96)', borderTop: '1px solid rgba(255,255,255,0.08)' }}
      >
        <ShelfBtn
          label="Edit"
          count={revisions.filter((r) => r.kind === 'edit').length}
          onClick={() => setSheet('chat')}
          icon={<Icon kind="edit" />}
          primary
          disabled={!current}
        />
        <ShelfBtn
          label="Refs"
          count={useSessionStore.getState().references.length}
          onClick={() => setSheet('refs')}
          icon={<Icon kind="refs" />}
        />
        <ShelfBtn
          label="Commit"
          onClick={() => setSheet('commit')}
          icon={<Icon kind="commit" />}
          disabled={!current}
        />
        <ShelfBtn
          label="Export"
          onClick={() => router.push(`/app/session/${sessionId}/export`)}
          icon={<Icon kind="export" />}
          disabled={!current}
        />
      </div>

      {sheet === 'chat' && (
        <MobSheet title="Edit" sub="describe a change" onClose={() => setSheet(null)}>
          <div className="h-[50vh]"><ChatPanel onAction={() => {}} /></div>
        </MobSheet>
      )}
      {sheet === 'refs' && (
        <MobSheet title="References" sub="retrieved matches" onClose={() => setSheet(null)}>
          <ReferenceStrip orientation="grid" />
        </MobSheet>
      )}
      {sheet === 'commit' && (
        <MobSheet title="Commit" sub="higher-fidelity re-render" onClose={() => setSheet(null)}>
          <div className="flex flex-col gap-4 pt-2">
            <p className="text-ink-soft text-sm">
              Commit re-renders the current revision at higher fidelity. Costs 3 credits and cannot be undone.
            </p>
            {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
            <Btn variant="clay" size="lg" onClick={commit} disabled={committing || !current}>
              {committing ? <Spinner size={14} color="#FBF8F2" /> : null}
              {committing ? 'Committing…' : 'Commit revision'}
            </Btn>
          </div>
        </MobSheet>
      )}
    </div>
  );
}

function Icon({ kind }: { kind: 'edit' | 'refs' | 'commit' | 'export' }) {
  const p = { fill: 'none', stroke: '#FBF8F2', strokeWidth: 1.6, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  switch (kind) {
    case 'edit':
      return (
        <svg width="20" height="20" viewBox="0 0 20 20">
          <path d="M3 17 L7 16 L17 6 L14 3 L4 13 Z" {...p} />
        </svg>
      );
    case 'refs':
      return (
        <svg width="20" height="20" viewBox="0 0 20 20">
          <rect x="3" y="4" width="14" height="12" rx="2" {...p} />
          <path d="M3 13 L7 9 L11 12 L14 10 L17 13" {...p} />
        </svg>
      );
    case 'commit':
      return (
        <svg width="20" height="20" viewBox="0 0 20 20">
          <circle cx="10" cy="10" r="3" {...p} />
          <path d="M10 2 V7 M10 13 V18" {...p} />
        </svg>
      );
    case 'export':
      return (
        <svg width="20" height="20" viewBox="0 0 20 20">
          <path d="M10 13 V3 M6 7 L10 3 L14 7" {...p} />
          <path d="M4 13 V16 H16 V13" {...p} />
        </svg>
      );
  }
}

export function Canvas({ sessionId }: { sessionId: string }) {
  return (
    <AuthGate>
      <CanvasInner sessionId={sessionId} />
    </AuthGate>
  );
}
