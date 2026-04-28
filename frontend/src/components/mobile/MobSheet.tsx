'use client';

import type { ReactNode } from 'react';
import { Anno } from '@/components/atelier/Anno';

type Props = {
  children: ReactNode;
  title: string;
  sub?: string;
  onClose: () => void;
};

export function MobSheet({ children, title, sub, onClose }: Props) {
  return (
    <>
      <div
        onClick={onClose}
        className="absolute inset-0 bg-black/40 z-[50]"
        style={{ animation: 'fadeIn 200ms ease' }}
      />
      <div
        className="absolute bottom-0 left-0 right-0 z-[51] max-h-[72%] flex flex-col bg-paper text-ink"
        style={{
          borderRadius: '20px 20px 0 0',
          animation: 'slideUp 260ms cubic-bezier(0.2, 0.9, 0.3, 1)',
          boxShadow: '0 -20px 50px rgba(0,0,0,0.3)',
        }}
      >
        <div className="pt-2.5 flex justify-center">
          <div className="w-10 h-1 rounded bg-line" />
        </div>
        <div className="pt-3 pb-2 px-5 flex items-start gap-3">
          <div className="flex-1">
            {sub && <Anno className="block mb-0.5">{sub}</Anno>}
            <div className="font-serif text-[22px] font-normal">{title}</div>
          </div>
          <button
            onClick={onClose}
            className="w-[30px] h-[30px] rounded-full flex items-center justify-center bg-bone border-0 cursor-pointer"
            aria-label="Close"
          >
            <svg width="12" height="12" viewBox="0 0 12 12">
              <path d="M2 2 L10 10 M10 2 L2 10" stroke="#1C1B17" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto pt-2 pb-8 px-5">{children}</div>
      </div>
    </>
  );
}
