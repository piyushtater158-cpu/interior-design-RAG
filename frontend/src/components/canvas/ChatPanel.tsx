'use client';

import { useState, type FormEvent } from 'react';
import { useSessionStore } from '@/store/session';
import { useAppStore } from '@/store/app';
import { api, ApiError, absoluteUrl } from '@/lib/api';
import { Btn } from '@/components/atelier/Btn';
import { Anno } from '@/components/atelier/Anno';
import { Spinner } from '@/components/shared/Loader';
import { ErrorBanner } from '@/components/shared/ErrorBanner';

export function ChatPanel({ onAction }: { onAction?: () => void }) {
  const sessionId = useSessionStore((s) => s.sessionId);
  const currentId = useSessionStore((s) => s.currentGenerationId);
  const chat = useSessionStore((s) => s.chat);
  const appendChat = useSessionStore((s) => s.appendChat);
  const appendRevision = useSessionStore((s) => s.appendRevision);
  const decrementCredits = useAppStore((s) => s.decrementCredits);

  const [instruction, setInstruction] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!currentId || !instruction.trim()) return;
    setBusy(true);
    setError(null);
    const text = instruction.trim();
    appendChat({ role: 'user', text });
    setInstruction('');
    try {
      const res = await api.generateEdit({
        generation_id: currentId,
        instruction: text,
        session_id: sessionId ?? undefined,
      });
      appendRevision({
        generationId: res.generation_id,
        kind: 'edit',
        outputUrl: absoluteUrl(res.output_url),
        parentId: currentId,
        createdAt: Date.now(),
        modelId: res.model_id,
        backendId: res.backend_id,
        caption: text,
      });
      appendChat({ role: 'system', text: `applied · ${res.latency_ms}ms` });
      decrementCredits(1);
      onAction?.();
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Edit failed.';
      setError(msg);
      appendChat({ role: 'system', text: `error · ${msg}` });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-2">
        <Anno className="block mb-1">edit thread</Anno>
        {chat.length === 0 && (
          <div className="text-ink-soft text-sm">
            Describe a change — e.g. &quot;swap the rug for natural jute&quot; or &quot;warmer evening light&quot;.
          </div>
        )}
        {chat.map((m, i) => (
          <div
            key={i}
            className="rounded-lg px-3 py-2 text-sm max-w-[85%]"
            style={{
              alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
              background: m.role === 'user' ? '#1C1B17' : '#F4EFE6',
              color: m.role === 'user' ? '#FBF8F2' : '#1C1B17',
              border: m.role === 'user' ? 'none' : '1px solid #D8D0BE',
            }}
          >
            {m.text}
          </div>
        ))}
      </div>
      {error && <div className="px-3 pb-2"><ErrorBanner message={error} onDismiss={() => setError(null)} /></div>}
      <form onSubmit={submit} className="border-t p-3 flex gap-2" style={{ borderColor: '#D8D0BE' }}>
        <input
          type="text"
          value={instruction}
          disabled={busy || !currentId}
          onChange={(e) => setInstruction(e.target.value)}
          placeholder="describe an edit…"
          className="flex-1 rounded-lg px-3 h-11 bg-paper text-ink outline-none text-sm"
          style={{ border: '1px solid #D8D0BE' }}
        />
        <Btn type="submit" disabled={busy || !currentId || !instruction.trim()}>
          {busy ? <Spinner size={14} color="#FBF8F2" /> : 'Send'}
        </Btn>
      </form>
    </div>
  );
}
