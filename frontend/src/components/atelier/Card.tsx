'use client';

import { useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';

type Props = {
  children: ReactNode;
  onClick?: () => void;
  active?: boolean;
  hover?: boolean;
  className?: string;
  style?: CSSProperties;
};

export function Card({ children, onClick, active = false, hover = true, className = '', style }: Props) {
  const [h, setH] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setH(true)}
      onMouseLeave={() => setH(false)}
      className={`rounded-[14px] bg-card transition-[transform,box-shadow,border-color] duration-200 ${
        h && hover ? 'shadow-hi -translate-y-0.5' : 'shadow-med'
      } ${onClick ? 'cursor-pointer' : 'cursor-default'} ${className}`}
      style={{
        border: `1px solid ${active ? '#1C1B17' : '#D8D0BE'}`,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
