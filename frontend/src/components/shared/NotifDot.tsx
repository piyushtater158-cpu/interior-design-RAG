import type { NotifType } from '@/lib/mockLibrary';

const COLORS: Record<NotifType, string> = {
  low_balance: '#D99B3A',
  feature: '#3D4A2A',
  commit: '#B85C3A',
  storage: '#A8B5B0',
};

export function NotifDot({ type, size = 10 }: { type: NotifType; size?: number }) {
  return (
    <span
      aria-hidden
      className="inline-block shrink-0 rounded-full"
      style={{
        width: size,
        height: size,
        background: COLORS[type],
        boxShadow: '0 0 0 3px rgba(28,27,23,0.04)',
      }}
    />
  );
}
