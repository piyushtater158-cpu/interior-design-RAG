import type { CSSProperties, ReactNode } from 'react';
import { TOKENS } from '@/lib/tokens';

type Props = {
  children?: ReactNode;
  size?: number;
  className?: string;
  style?: CSSProperties;
};

export function BlueprintBg({ children, size = 24, className = '', style }: Props) {
  return (
    <div
      className={`relative ${className}`}
      style={{
        backgroundColor: TOKENS.bone,
        backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(28,27,23,0.08) 1px, transparent 0)',
        backgroundSize: `${size}px ${size}px`,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
