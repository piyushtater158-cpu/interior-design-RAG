'use client';

import { useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost' | 'clay';
type Size = 'sm' | 'md' | 'lg';

const TIERS: Record<Variant, { bg: string; bgHover: string; fg: string; border: string }> = {
  primary: { bg: '#3D4A2A', bgHover: '#2A3420', fg: '#FBF8F2', border: '#2A3420' },
  secondary: { bg: '#FFFFFF', bgHover: '#F4EFE6', fg: '#1C1B17', border: '#D8D0BE' },
  ghost: { bg: 'transparent', bgHover: 'rgba(28,27,23,0.05)', fg: '#1C1B17', border: 'transparent' },
  clay: { bg: '#B85C3A', bgHover: '#A24E2E', fg: '#FBF8F2', border: '#A24E2E' },
};

const SIZES: Record<Size, { pad: string; fs: number; h: number }> = {
  sm: { pad: '6px 12px', fs: 12, h: 28 },
  md: { pad: '10px 18px', fs: 13, h: 40 },
  lg: { pad: '14px 24px', fs: 14, h: 48 },
};

type Props = {
  children: ReactNode;
  variant?: Variant;
  size?: Size;
  onClick?: () => void;
  disabled?: boolean;
  icon?: ReactNode;
  className?: string;
  style?: CSSProperties;
  type?: 'button' | 'submit';
};

export function Btn({
  children,
  variant = 'primary',
  size = 'md',
  onClick,
  disabled,
  icon,
  className = '',
  style,
  type = 'button',
}: Props) {
  const [h, setH] = useState(false);
  const t = TIERS[variant];
  const s = SIZES[size];

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={() => setH(true)}
      onMouseLeave={() => setH(false)}
      className={`font-sans font-medium rounded-full inline-flex items-center gap-2 transition-[background,transform] duration-150 ${className}`}
      style={{
        fontSize: s.fs,
        letterSpacing: 0.2,
        background: h && !disabled ? t.bgHover : t.bg,
        color: t.fg,
        border: `1px solid ${t.border}`,
        padding: s.pad,
        height: s.h,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        boxShadow:
          variant === 'primary'
            ? '0 1px 0 rgba(255,255,255,0.1) inset, 0 2px 8px rgba(61,74,42,0.2)'
            : variant === 'clay'
            ? '0 4px 12px rgba(184,92,58,0.3)'
            : 'none',
        ...style,
      }}
    >
      {icon}
      {children}
    </button>
  );
}
