'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGate } from '@/components/shared/AuthGate';
import { BlueprintBg } from '@/components/atelier/BlueprintBg';
import { MobStatusBar } from '@/components/mobile/MobStatusBar';
import { MobNav } from '@/components/mobile/MobNav';
import { RoomRender } from '@/components/atelier/RoomRender';
import { Btn } from '@/components/atelier/Btn';
import { Anno } from '@/components/atelier/Anno';
import { Card } from '@/components/atelier/Card';
import { Spinner } from '@/components/shared/Loader';
import { ErrorBanner } from '@/components/shared/ErrorBanner';
import { useSessionStore } from '@/store/session';
import { api, ApiError, absoluteUrl } from '@/lib/api';
import { revLabel } from '@/lib/format';

function ExportInner({ sessionId }: { sessionId: string }) {
  const router = useRouter();
  const revisions = useSessionStore((s) => s.revisions);
  const currentId = useSessionStore((s) => s.currentGenerationId);

  const current = useMemo(
    () => revisions.find((r) => r.generationId === currentId) ?? revisions[revisions.length - 1],
    [revisions, currentId],
  );
  const currentIndex = current ? revisions.findIndex((r) => r.generationId === current.generationId) : -1;

  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!current) {
      setLoading(false);
      return;
    }
    let alive = true;
    (async () => {
      try {
        const res = await api.exportGeneration(current.generationId);
        if (alive) setDownloadUrl(absoluteUrl(res.download_url));
      } catch (err) {
        if (alive) setError(err instanceof ApiError ? err.message : 'Export failed.');
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [current]);

  return (
    <BlueprintBg className="min-h-screen pb-10">
      <div className="lg:hidden">
        <MobStatusBar />
        <MobNav
          title="Export"
          sub={current ? `${revLabel(currentIndex)} · ${current.kind}` : 'no revision'}
          onBack={() => router.push(`/app/session/${sessionId}`)}
        />
      </div>
      <div className="hidden lg:flex items-center justify-between px-10 pt-8 pb-4">
        <div>
          <Anno>export · final render</Anno>
          <h1 className="font-serif text-[40px] leading-tight mt-1">
            {current ? `${revLabel(currentIndex)} · ${current.kind}` : 'Export'}
          </h1>
        </div>
        <Btn variant="ghost" onClick={() => router.push(`/app/session/${sessionId}`)}>← back to canvas</Btn>
      </div>

      <div className="px-5 lg:px-10 lg:max-w-[1100px] lg:mx-auto flex flex-col gap-5">
        <Card className="p-0 overflow-hidden aspect-[4/3] lg:aspect-[16/10]">
          <div className="w-full h-full">
            <RoomRender imageUrl={current?.outputUrl ?? null} tone={current?.tone ?? 'warm'} />
          </div>
        </Card>

        {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          <div className="flex flex-col">
            <Anno>file · PNG · full resolution</Anno>
            <span className="text-ink-soft text-sm">
              {current?.modelId ? `model · ${current.modelId}` : ''}
            </span>
          </div>
          <a
            href={downloadUrl ?? '#'}
            download
            aria-disabled={!downloadUrl}
            onClick={(e) => { if (!downloadUrl) e.preventDefault(); }}
            className="inline-block"
          >
            <Btn size="lg" variant="clay" disabled={loading || !downloadUrl}>
              {loading ? <Spinner size={14} color="#FBF8F2" /> : null}
              {loading ? 'Preparing…' : 'Download PNG ↓'}
            </Btn>
          </a>
        </div>
      </div>
    </BlueprintBg>
  );
}

export function Export({ sessionId }: { sessionId: string }) {
  return (
    <AuthGate>
      <ExportInner sessionId={sessionId} />
    </AuthGate>
  );
}
