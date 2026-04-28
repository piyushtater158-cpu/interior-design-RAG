import type { components } from './api.d';
import { useAppStore } from '@/store/app';
import { MOCK_SESSIONS, MOCK_NOTIFICATIONS, type MockSession, type MockNotification } from './mockLibrary';

export type TokenResponse = components['schemas']['TokenResponse'];
export type MeResponse = components['schemas']['MeResponse'];
export type UploadResponse = components['schemas']['UploadResponse'];
export type RetrieveResponse = components['schemas']['RetrieveResponse'];
export type ReferenceHit = components['schemas']['ReferenceHit'];
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
  return useAppStore.getState().jwt ?? localStorage.getItem('atelier:jwt');
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

  retrieveReferences: (args: { upload_id: string; room_type?: string; style_tag?: string; k?: number; prompt?: string }) =>
    request<RetrieveResponse>('/retrieve/references', {
      method: 'POST',
      body: JSON.stringify(args),
    }),

  generateDraft: (args: {
    upload_id: string;
    room_type?: string;
    style_tag?: string;
    reference_ids?: string[];
    session_id?: string;
    prompt?: string;
  }) =>
    request<GenerationResponse>('/generate/draft', {
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
