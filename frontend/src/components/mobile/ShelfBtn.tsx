'use client';

import type { ReactNode } from 'react';

type Props = {
  label: string;
  count?: string | number;
  onClick?: () => void;
  icon: ReactNode;
  primary?: boolean;
  disabled?: boolean;
};

export function ShelfBtn({ label, count, onClick, icon, primary, disabled }: Props) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="flex-1 py-2.5 px-2 rounded-[14px] flex flex-col items-center gap-1 text-paper"
      style={{
        background: primary
          ? disabled
            ? 'rgba(184,92,58,0.3)'
            : '#B85C3A'
          : 'rgba(255,255,255,0.06)',
        border: `1px solid ${primary ? (disabled ? 'transparent' : '#B85C3A') : 'rgba(255,255,255,0.1)'}`,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.55 : 1,
      }}
    >
      {icon}
      <div className="font-sans text-[11px] font-medium">
        {label}
        {count !== undefined && !primary && (
          <span className="opacity-60 ml-1 font-mono text-[10px]">{count}</span>
        )}
      </div>
    </button>
  );
}
