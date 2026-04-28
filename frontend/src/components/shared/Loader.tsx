import { TOKENS } from '@/lib/tokens';

export function Spinner({ size = 18, color = TOKENS.ink }: { size?: number; color?: string }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className="inline-block align-middle"
      style={{
        width: size,
        height: size,
        border: `2px solid ${color}`,
        borderTopColor: 'transparent',
        borderRadius: '50%',
        animation: 'spin 800ms linear infinite',
      }}
    />
  );
}

export function Shimmer({ className = '', style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <div
      className={`w-full h-full ${className}`}
      style={{
        background: `linear-gradient(90deg, ${TOKENS.bone} 0%, ${TOKENS.paper} 50%, ${TOKENS.bone} 100%)`,
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.6s linear infinite',
        ...style,
      }}
    />
  );
}
