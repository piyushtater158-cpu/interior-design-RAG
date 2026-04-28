export const TOKENS = {
  bone: '#F4EFE6',
  boneDeep: '#EAE2D4',
  paper: '#FBF8F2',
  ink: '#1C1B17',
  inkSoft: '#3A382F',
  mute: '#8B8676',
  muteLite: '#B8B2A1',
  line: '#D8D0BE',
  olive: '#3D4A2A',
  oliveDeep: '#2A3420',
  clay: '#B85C3A',
  sand: '#D9C9A8',
  sky: '#A8B5B0',
  card: '#FFFFFF',
  cardSoft: '#FEFCF6',
} as const;

export const ROOM_TYPES = [
  { id: 'bedroom', name: 'Bedroom', sub: 'calm / personal / low light', iso: 'bedroom' },
  { id: 'dining', name: 'Dining', sub: 'gathering / warm / focal', iso: 'dining' },
  { id: 'kitchen', name: 'Kitchen', sub: 'utility / surfaces / flow', iso: 'kitchen' },
  { id: 'mandir', name: 'Mandir', sub: 'sacred / still / intimate', iso: 'mandir' },
] as const;

export const STYLES = [
  { id: 'scandinavian', name: 'Scandinavian', desc: 'pale wood · airy · restrained' },
  { id: 'japandi', name: 'Japandi', desc: 'quiet · textural · warm minimal' },
  { id: 'midcentury', name: 'Mid-century', desc: 'teak · tapered · bold color' },
  { id: 'traditional', name: 'Traditional', desc: 'carved · layered · rich tones' },
  { id: 'industrial', name: 'Industrial', desc: 'steel · concrete · patina' },
  { id: 'boho', name: 'Boho', desc: 'rattan · weave · sun-faded' },
] as const;

export type RoomType = (typeof ROOM_TYPES)[number]['id'];
export type StyleId = (typeof STYLES)[number]['id'];
export type RoomTone = 'warm' | 'cool' | 'moody';

export const CREDIT_RATE_INR_DEFAULT = 5;
export const MIN_TOPUP_INR_DEFAULT = 1000;
export const STORAGE_MONTHLY_INR_DEFAULT = 149;
