'use client';

import { useMemo, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { AuthGate } from '@/components/shared/AuthGate';
import { MobStatusBar } from '@/components/mobile/MobStatusBar';
import { MobNav } from '@/components/mobile/MobNav';
import { Card } from '@/components/atelier/Card';
import { Btn } from '@/components/atelier/Btn';
import { Anno } from '@/components/atelier/Anno';
import { BlueprintBg } from '@/components/atelier/BlueprintBg';
import { CreditsPill } from '@/components/canvas/CreditsPill';
import { ErrorBanner } from '@/components/shared/ErrorBanner';
import { Spinner } from '@/components/shared/Loader';
import { ROOM_TYPES, STYLES, type RoomType, type StyleId } from '@/lib/tokens';
import { api, ApiError, absoluteUrl } from '@/lib/api';
import { useSessionStore } from '@/store/session';
import { useAppStore } from '@/store/app';

type Step = 1 | 2;

function NewSessionInner() {
  const router = useRouter();
  const params = useSearchParams();
  const sessionStore = useSessionStore();
  const decrementCredits = useAppStore((s) => s.decrementCredits);

  const roomType = (params.get('type') as RoomType | null) ?? 'bedroom';
  const roomMeta = useMemo(() => ROOM_TYPES.find((r) => r.id === roomType) ?? ROOM_TYPES[0], [roomType]);

  const [step, setStep] = useState<Step>(1);
  const [styleId, setStyleId] = useState<StyleId | null>(null);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [prompt, setPrompt] = useState('');
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await api.uploadRoomPhoto(file);
      setUploadId(res.upload_id);
      setPreviewUrl(absoluteUrl(res.preview_url));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Upload failed.');
    } finally {
      setUploading(false);
    }
  }

  async function generate() {
    if (!uploadId || !prompt.trim()) return;
    setGenerating(true);
    setError(null);
    try {
      const sessionId =
        typeof crypto !== 'undefined' && 'randomUUID' in crypto
          ? crypto.randomUUID()
          : `sess-${Date.now()}`;

      sessionStore.newSession({ sessionId, roomType, styleTag: styleId });
      sessionStore.setUpload(uploadId, previewUrl ?? '');

      const result = await api.generateOrchestrated({
        upload_id: uploadId,
        brief: prompt.trim(),
        style_tag: styleId ?? undefined,
        room_type: roomType,
        session_id: sessionId,
      });
      sessionStore.appendRevision({
        generationId: result.generation_id,
        kind: 'orchestrated',
        outputUrl: absoluteUrl(result.output_url),
        parentId: null,
        createdAt: Date.now(),
        modelId: result.model_id,
        backendId: result.backend_id,
      });
      decrementCredits(2);

      router.push(`/app/session/${sessionId}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Generation failed.');
      setGenerating(false);
    }
  }

  const canAdvance = !!uploadId && !uploading;
  const canGenerate = !!prompt.trim() && !generating;

  // ── Step dots ──────────────────────────────────────────────────────────────
  const StepDots = () => (
    <div className="flex gap-1.5">
      {([1, 2] as Step[]).map((s) => (
        <div
          key={s}
          className="h-1 rounded-full transition-all duration-200"
          style={{
            width: s === step ? 22 : 10,
            background: s <= step ? '#1C1B17' : '#D8D0BE',
          }}
        />
      ))}
    </div>
  );

  return (
    <BlueprintBg className="min-h-screen flex flex-col">
      <div className="lg:hidden">
        <MobStatusBar />
      </div>

      <div className="lg:max-w-[1100px] lg:mx-auto w-full flex flex-col flex-1">
        {/* Nav */}
        <div className="lg:hidden">
          <MobNav
            title={step === 1 ? 'Show us the room' : 'Write a brief'}
            sub={`${roomMeta.id} · step 0${step} of 02`}
            onBack={step === 1 ? () => router.push('/app') : () => setStep(1)}
            trailing={<StepDots />}
          />
        </div>

        <div className="hidden lg:flex items-center justify-between px-10 pt-8 pb-4">
          <div>
            <Anno>new session · {roomMeta.sub} · step 0{step} of 02</Anno>
            <h1 className="font-serif text-[40px] leading-tight mt-1">{roomMeta.name}</h1>
          </div>
          <div className="flex items-center gap-4">
            <StepDots />
            <CreditsPill />
          </div>
        </div>

        {/* ── STEP 1: Upload ─────────────────────────────────────────────────── */}
        {step === 1 && (
          <div className="flex-1 px-5 lg:px-10 pt-4 pb-36 lg:pb-20">
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png"
              className="hidden"
              onChange={onFile}
            />

            <div
              onClick={() => !uploadId && fileRef.current?.click()}
              className="rounded-2xl overflow-hidden border relative"
              style={{
                aspectRatio: '4 / 3',
                borderStyle: uploadId ? 'solid' : 'dashed',
                borderColor: uploadId ? '#D8D0BE' : '#B8B2A1',
                borderWidth: '1.5px',
                background: uploadId ? '#FFFFFF' : '#FEFCF6',
                cursor: uploadId ? 'default' : 'pointer',
              }}
            >
              {uploadId && previewUrl ? (
                <>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={previewUrl} alt="room preview" className="w-full h-full object-cover" />
                  <div className="absolute bottom-3 left-3 right-3 flex justify-between items-end">
                    <Anno className="bg-white/80 rounded px-1.5 py-0.5">uploaded</Anno>
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-full gap-3 p-6 text-center">
                  {uploading ? (
                    <Spinner />
                  ) : (
                    <svg width="48" height="48" viewBox="0 0 40 40">
                      <rect x="6" y="8" width="28" height="22" rx="3" fill="none" stroke="#8B8676" strokeWidth="1.5" />
                      <circle cx="14" cy="16" r="2" fill="#8B8676" />
                      <path d="M 6 26 L 16 18 L 22 24 L 28 19 L 34 25" fill="none" stroke="#8B8676" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                  <div className="font-serif text-[20px]">
                    {uploading ? 'Uploading…' : 'Tap to upload'}
                  </div>
                  <Anno>{uploading ? '' : 'camera or photo library · JPG/PNG · ≤10MB'}</Anno>
                </div>
              )}
            </div>

            {uploadId && (
              <div className="mt-3 flex items-center gap-3 flex-wrap">
                {['landscape ok', 'night ok', 'any angle'].map((t) => (
                  <span
                    key={t}
                    className="px-2.5 py-1 rounded-full border text-xs"
                    style={{ borderColor: '#D8D0BE', background: '#FFFFFF' }}
                  >
                    <Anno>✓ {t}</Anno>
                  </span>
                ))}
                <button
                  type="button"
                  onClick={() => { setUploadId(null); setPreviewUrl(null); }}
                  className="text-xs"
                  style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8B8676', textTransform: 'uppercase', letterSpacing: '0.08em', background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  × replace
                </button>
              </div>
            )}

            <div className="mt-6">
              <Anno className="block mb-2">◆ what we keep</Anno>
              <p className="text-sm leading-relaxed" style={{ color: '#3A382F', maxWidth: 420 }}>
                Windows, proportions, and architecture stay. Everything else — furniture, finishes, light, greenery — is up for redesign.
              </p>
            </div>
          </div>
        )}

        {/* ── STEP 2: Brief + Style ─────────────────────────────────────────── */}
        {step === 2 && (
          <div className="flex-1 px-5 lg:px-10 pt-4 pb-36 lg:pb-20">
            <Anno className="block mb-2">◆ describe what you want · required</Anno>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder={`"soft light, lived-in, brass touches, plants that outgrow their pots"`}
              rows={4}
              className="w-full rounded-xl px-4 py-3 text-sm leading-relaxed resize-none outline-none border transition-colors"
              style={{
                fontFamily: 'Inter, sans-serif',
                background: '#FEFCF6',
                color: '#1C1B17',
                borderColor: prompt ? '#1C1B17' : '#D8D0BE',
              }}
            />
            <Anno className="block mt-1.5">
              your brief drives the 3-agent pipeline · reference selection is automatic
            </Anno>

            <div className="mt-6">
              <Anno className="block mb-3">◆ style tag · optional</Anno>
              <div className="grid grid-cols-2 gap-3">
                {STYLES.map((s) => (
                  <Card
                    key={s.id}
                    active={styleId === s.id}
                    onClick={() => setStyleId(styleId === s.id ? null : s.id)}
                    className="p-4"
                  >
                    <div className="flex items-center gap-2 mb-1.5">
                      <div
                        className="w-2 h-2 rounded-full transition-colors"
                        style={{ background: styleId === s.id ? '#3D4A2A' : '#D8D0BE' }}
                      />
                      <div className="font-serif text-[17px] leading-tight">{s.name}</div>
                    </div>
                    <Anno className="block">{s.desc}</Anno>
                  </Card>
                ))}
              </div>
              <Anno className="block mt-2">tap to select · tap again to deselect · agent infers style if none chosen</Anno>
            </div>
          </div>
        )}

        {/* ── Error ──────────────────────────────────────────────────────────── */}
        {error && (
          <div className="px-5 lg:px-10 pb-4">
            <ErrorBanner message={error} onDismiss={() => setError(null)} />
          </div>
        )}
      </div>

      {/* ── Sticky CTA ─────────────────────────────────────────────────────── */}
      <div
        className="fixed bottom-0 left-0 right-0 px-5 lg:px-0 pb-8 pt-4 z-30"
        style={{
          background: 'rgba(251,248,242,0.92)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderTop: '0.5px solid #D8D0BE',
        }}
      >
        <div className="lg:max-w-[1100px] lg:mx-auto">
          {step === 1 ? (
            <div className="flex items-center justify-between gap-3">
              <Anno>step 01 · upload your room</Anno>
              <Btn size="lg" onClick={() => setStep(2)} disabled={!canAdvance}>
                {uploading ? <Spinner size={14} color="#FBF8F2" /> : null}
                {uploading ? 'Uploading…' : 'Next — write a brief →'}
              </Btn>
            </div>
          ) : (
            <div className="flex items-center justify-between gap-3">
              <Anno>cost · 2 credits</Anno>
              <Btn size="lg" onClick={generate} disabled={!canGenerate}>
                {generating ? <Spinner size={14} color="#FBF8F2" /> : null}
                {generating ? 'Generating…' : prompt.trim() ? 'Generate first draft →' : 'Write a brief to continue'}
              </Btn>
            </div>
          )}
        </div>
      </div>
    </BlueprintBg>
  );
}

export function NewSession() {
  return (
    <AuthGate>
      <NewSessionInner />
    </AuthGate>
  );
}
