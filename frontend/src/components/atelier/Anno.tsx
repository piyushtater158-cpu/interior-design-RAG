import type { CSSProperties, ReactNode } from 'react';

type Props = {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  color?: string;
};

export function Anno({ children, className = '', style, color }: Props) {
  return (
    <span
      className={`font-mono text-[10px] tracking-[0.8px] uppercase ${className}`}
      style={{ color: color ?? '#8B8676', ...style }}
    >
      {children}
    </span>
  );
}
