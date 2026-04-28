'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { RoomType, StyleId, RoomTone } from '@/lib/tokens';

export type Revision = {
  generationId: string;
  kind: 'draft' | 'edit' | 'commit';
  outputUrl: string;
  parentId: string | null;
  createdAt: number;
  tone?: RoomTone;
  caption?: string;
  modelId?: string;
  backendId?: string;
};

export type ReferenceThumb = {
  id: string;
  url: string;
  similarity: number;
  styleTags: string[];
};

export type ChatMessage = { role: 'user' | 'system'; text: string };

interface SessionState {
  sessionId: string | null;
  roomType: RoomType | null;
  styleTag: StyleId | null;
  uploadId: string | null;
  uploadPreviewUrl: string | null;
  references: ReferenceThumb[];
  revisions: Revision[];
  currentGenerationId: string | null;
  chat: ChatMessage[];
  isGenerating: boolean;
  error: string | null;

  newSession: (args: { sessionId: string; roomType: RoomType; styleTag: StyleId }) => void;
  setUpload: (id: string, url: string) => void;
  setReferences: (r: ReferenceThumb[]) => void;
  appendRevision: (r: Revision) => void;
  setRevisions: (r: Revision[]) => void;
  setCurrent: (id: string) => void;
  appendChat: (m: ChatMessage) => void;
  setGenerating: (b: boolean) => void;
  setError: (e: string | null) => void;
  reset: () => void;
}

const ROTATE_TONE: RoomTone[] = ['warm', 'cool', 'moody'];

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      sessionId: null,
      roomType: null,
      styleTag: null,
      uploadId: null,
      uploadPreviewUrl: null,
      references: [],
      revisions: [],
      currentGenerationId: null,
      chat: [],
      isGenerating: false,
      error: null,

      newSession: ({ sessionId, roomType, styleTag }) =>
        set({
          sessionId,
          roomType,
          styleTag,
          uploadId: null,
          uploadPreviewUrl: null,
          references: [],
          revisions: [],
          currentGenerationId: null,
          chat: [],
          isGenerating: false,
          error: null,
        }),

      setUpload: (id, url) => set({ uploadId: id, uploadPreviewUrl: url }),
      setReferences: (r) => set({ references: r }),
      appendRevision: (r) => {
        const { revisions } = get();
        const tone = r.tone ?? ROTATE_TONE[revisions.length % 3];
        set({
          revisions: [...revisions, { ...r, tone }],
          currentGenerationId: r.generationId,
        });
      },
      setRevisions: (r) => set({ revisions: r }),
      setCurrent: (id) => set({ currentGenerationId: id }),
      appendChat: (m) => set((s) => ({ chat: [...s.chat, m] })),
      setGenerating: (b) => set({ isGenerating: b }),
      setError: (e) => set({ error: e }),
      reset: () =>
        set({
          sessionId: null,
          roomType: null,
          styleTag: null,
          uploadId: null,
          uploadPreviewUrl: null,
          references: [],
          revisions: [],
          currentGenerationId: null,
          chat: [],
          isGenerating: false,
          error: null,
        }),
    }),
    {
      name: 'atelier:session',
      storage: createJSONStorage(() => (typeof window !== 'undefined' ? localStorage : undefined as never)),
    },
  ),
);
