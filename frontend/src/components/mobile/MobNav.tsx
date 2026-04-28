import type { ReactNode } from 'react';
import { Anno } from '@/components/atelier/Anno';

type Props = {
  title: string;
  sub?: string;
  onBack?: () => void;
  trailing?: ReactNode;
  dark?: boolean;
};

export function MobNav({ title, sub, onBack, trailing, dark = false }: Props) {
  const fg = dark ? '#F4EFE6' : '#1C1B17';
  const muted = dark ? '#B8B2A1' : '#8B8676';
  return (
    <div
      className="flex items-center gap-3 px-5 pt-1.5 pb-3 min-h-[56px] box-border"
      style={{
        borderBottom: `0.5px solid ${dark ? 'rgba(255,255,255,0.1)' : '#D8D0BE'}`,
        background: dark ? 'transparent' : '#FBF8F2',
      }}
    >
      {onBack && (
        <button
          onClick={onBack}
          className="w-9 h-9 rounded-full flex items-center justify-center shrink-0 cursor-pointer p-0"
          style={{
            background: dark ? 'rgba(255,255,255,0.08)' : '#FFFFFF',
            border: `1px solid ${dark ? 'rgba(255,255,255,0.1)' : '#D8D0BE'}`,
          }}
          aria-label="Back"
        >
          <svg width="10" height="16" viewBox="0 0 10 16">
            <path d="M8 2 L2 8 L8 14" stroke={fg} strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      )}
      <div className="flex-1 min-w-0">
        {sub && (
          <Anno color={muted} className="block mb-0.5">
            {sub}
          </Anno>
        )}
        <div className="font-serif text-[22px] font-normal leading-[1.15]" style={{ color: fg }}>
          {title}
        </div>
      </div>
      {trailing}
    </div>
  );
}
