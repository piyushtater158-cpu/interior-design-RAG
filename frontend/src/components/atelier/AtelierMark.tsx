import { TOKENS } from '@/lib/tokens';

export function AtelierMark({ size = 28, color = TOKENS.ink }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" className="block">
      <g transform="translate(20,6)">
        <path d="M0 0 L14 8 L0 16 L-14 8 Z" fill={color} opacity="0.95" />
        <path d="M-14 8 L0 16 L0 32 L-14 24 Z" fill={color} opacity="0.7" />
        <path d="M14 8 L0 16 L0 32 L14 24 Z" fill={color} opacity="0.5" />
      </g>
    </svg>
  );
}
