'use client';

import { useEffect, useState } from 'react';

export type Breakpoint = 'mobile' | 'ipad' | 'desktop';

function currentBreakpoint(width: number): Breakpoint {
  if (width >= 1024) return 'desktop';
  if (width >= 768) return 'ipad';
  return 'mobile';
}

export function useResponsive(): Breakpoint {
  const [bp, setBp] = useState<Breakpoint>('mobile');

  useEffect(() => {
    const update = () => setBp(currentBreakpoint(window.innerWidth));
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  return bp;
}
