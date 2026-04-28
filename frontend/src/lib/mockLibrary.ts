import type { RoomType, StyleId, RoomTone } from '@/lib/tokens';

export type MockSession = {
  id: string;
  roomType: RoomType;
  styleTag: StyleId;
  tone: RoomTone;
  revCount: number;
  committed: boolean;
  favourite: boolean;
  createdAt: string;
  caption: string;
};

export type NotifType = 'low_balance' | 'feature' | 'commit' | 'storage';
export type NotifCtaScreen = 'topup' | 'library' | 'profile' | 'canvas';

export type MockNotification = {
  id: string;
  type: NotifType;
  read: boolean;
  time: string;
  title: string;
  body: string;
  cta?: string;
  ctaScreen?: NotifCtaScreen;
  sessionId?: string;
};

export const MOCK_SESSIONS: MockSession[] = [
  {
    id: 's1',
    roomType: 'bedroom',
    styleTag: 'scandinavian',
    tone: 'warm',
    revCount: 12,
    committed: true,
    favourite: true,
    createdAt: '2 days ago',
    caption: 'Primary bedroom',
  },
  {
    id: 's2',
    roomType: 'dining',
    styleTag: 'japandi',
    tone: 'warm',
    revCount: 7,
    committed: false,
    favourite: true,
    createdAt: '4 days ago',
    caption: 'Dining nook',
  },
  {
    id: 's3',
    roomType: 'kitchen',
    styleTag: 'midcentury',
    tone: 'cool',
    revCount: 4,
    committed: true,
    favourite: false,
    createdAt: '1 week ago',
    caption: 'Galley kitchen',
  },
  {
    id: 's4',
    roomType: 'mandir',
    styleTag: 'traditional',
    tone: 'moody',
    revCount: 9,
    committed: true,
    favourite: false,
    createdAt: '2 weeks ago',
    caption: 'Home shrine',
  },
  {
    id: 's5',
    roomType: 'bedroom',
    styleTag: 'boho',
    tone: 'warm',
    revCount: 3,
    committed: false,
    favourite: false,
    createdAt: '3 weeks ago',
    caption: 'Guest bedroom',
  },
  {
    id: 's6',
    roomType: 'dining',
    styleTag: 'industrial',
    tone: 'moody',
    revCount: 6,
    committed: false,
    favourite: false,
    createdAt: '1 month ago',
    caption: 'Loft dining',
  },
  {
    id: 's7',
    roomType: 'kitchen',
    styleTag: 'scandinavian',
    tone: 'cool',
    revCount: 11,
    committed: true,
    favourite: true,
    createdAt: '1 month ago',
    caption: 'Island kitchen',
  },
  {
    id: 's8',
    roomType: 'mandir',
    styleTag: 'japandi',
    tone: 'warm',
    revCount: 2,
    committed: false,
    favourite: false,
    createdAt: '2 months ago',
    caption: 'Meditation alcove',
  },
];

export const MOCK_NOTIFICATIONS: MockNotification[] = [
  {
    id: 'n1',
    type: 'low_balance',
    read: false,
    time: '2 min ago',
    title: 'Credits running low',
    body: 'You have 8 credits left. A commit costs 3 — top up to keep iterating.',
    cta: 'Top up now',
    ctaScreen: 'topup',
  },
  {
    id: 'n2',
    type: 'commit',
    read: false,
    time: '1 h ago',
    title: 'Commit complete',
    body: 'Primary bedroom · rev.12 rendered at high fidelity.',
    cta: 'Open canvas',
    ctaScreen: 'canvas',
    sessionId: 's1',
  },
  {
    id: 'n3',
    type: 'feature',
    read: true,
    time: 'yesterday',
    title: 'Gemini 3 Pro is live',
    body: 'Commits now use the higher-fidelity Pro model by default.',
  },
  {
    id: 'n4',
    type: 'storage',
    read: true,
    time: '3 days ago',
    title: 'Storage invoice',
    body: 'Monthly storage fee has been charged. Review your plan in Profile.',
    cta: 'Open profile',
    ctaScreen: 'profile',
  },
];

export const TOPUP_PRESETS_INR: number[] = [1000, 2000, 5000, 10000];
