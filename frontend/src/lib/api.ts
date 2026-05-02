import type { components } from './api.d';
import { useAppStore } from '@/store/app';
import { MOCK_SESSIONS, MOCK_NOTIFICATIONS, type MockSession, type MockNotification } from './mockLibrary';

export type TokenResponse = components['schemas']['TokenResponse'];
export type MeResponse = components['schemas']['MeResponse'];
export type UploadResponse = components['schemas']['UploadResponse'];
export type GenerationResponse = components['schemas']['GenerationResponse'];
export type HistoryItem = components['schemas']['HistoryItem'];
export type ExportResponse = components['schemas']['ExportResponse'];
export type ABConfigResponse = components['schemas']['ABConfigResponse'];

const BACKEND_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:5678/webhook').replace(/\/$/, '');

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(message: string, status: number, code: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

function readToken(): string | null {
  if (typeof window === 'undefined') return null;

  // 1. Try the live Zustand store first (works after hydration)
  const fromStore = useAppStore.getState().jwt;
  if (fromStore) return fromStore;

  // 2. Fallback: read directly from the persisted store object (key: 'atelier:app')
  try {
    const raw = localStorage.getItem('atelier:app');
    if (raw) {
      const parsed = JSON.parse(raw);
      return parsed?.state?.jwt ?? null;
    }
  } catch {
    // localStorage blocked or JSON malformed
  }
  return null;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...((init.headers as Record<string, string>) ?? {}),
  };
  const token = readToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (init.body && !(init.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  const r = await fetch(`${BACKEND_URL}${path}`, { ...init, headers });
  if (!r.ok) {
    let body: { error?: string; code?: string; detail?: unknown } = {};
    try {
      body = await r.json();
    } catch {
      /* non-json error */
    }
    const message =
      body.error ??
      (typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? r.statusText));
    if (r.status === 401 && typeof window !== 'undefined') {
      useAppStore.getState().clearAuth();
      window.location.replace('/signin');
    }
    throw new ApiError(message, r.status, body.code ?? `http_${r.status}`);
  }
  if (r.status === 204) return undefined as T;
  return (await r.json()) as T;
}

/** Convert a backend-relative URL (e.g. `/data/outputs/...`) to an absolute URL. Leaves absolute URLs alone. */
export function absoluteUrl(url: string): string {
  if (/^https?:\/\//i.test(url)) return url;
  return `${BACKEND_URL}${url.startsWith('/') ? '' : '/'}${url}`;
}

export const api = {
  authMagicLink: (email: string) =>
    request<TokenResponse>('/auth/magic-link', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  authMe: () => request<MeResponse>('/auth/me'),

  uploadRoomPhoto: (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    return request<UploadResponse>('/uploads/room-photo', {
      method: 'POST',
      body: fd,
    });
  },

  generateOrchestrated: (args: {
    upload_id: string;
    brief: string;
    style_tag?: string;
    room_type?: string;
    session_id?: string;
  }) =>
    request<GenerationResponse>('/generate/orchestrated', {
      method: 'POST',
      body: JSON.stringify(args),
    }),

  generateEdit: (args: { generation_id: string; instruction: string; session_id?: string }) =>
    request<GenerationResponse>('/generate/edit', {
      method: 'POST',
      body: JSON.stringify(args),
    }),

  generateCommit: (args: { generation_id: string; session_id?: string }) =>
    request<GenerationResponse>('/generate/commit', {
      method: 'POST',
      body: JSON.stringify(args),
    }),

  listSessionGenerations: (session_id: string) =>
    request<HistoryItem[]>(`/generations/session/${encodeURIComponent(session_id)}`),

  exportGeneration: (generation_id: string) =>
    request<ExportResponse>(`/generations/${encodeURIComponent(generation_id)}/export`, {
      method: 'POST',
    }),

  /** Stub — backend endpoint not yet available. Returns mock sessions. */
  listUserSessions: async (): Promise<MockSession[]> => {
    await new Promise((r) => setTimeout(r, 120));
    return MOCK_SESSIONS;
  },

  /** Stub — backend endpoint not yet available. Returns mock notifications. */
  listNotifications: async (): Promise<MockNotification[]> => {
    await new Promise((r) => setTimeout(r, 120));
    return MOCK_NOTIFICATIONS;
  },

  /** Stub — local-only for MVP. Real payment integration deferred to v1.5. */
  topUpCredits: async (args: { amountInr: number }): Promise<{ credits: number; amountInr: number }> => {
    const rate = useAppStore.getState().creditRateInr;
    await new Promise((r) => setTimeout(r, 350));
    return { amountInr: args.amountInr, credits: Math.floor(args.amountInr / rate) };
  },
};
