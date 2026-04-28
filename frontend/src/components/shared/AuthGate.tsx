'use client';

import { useEffect, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/store/app';
import { useHydrated } from '@/hooks/useHydrated';
import { Spinner } from './Loader';

export function AuthGate({ children }: { children: ReactNode }) {
  const hydrated = useHydrated();
  const jwt = useAppStore((s) => s.jwt);
  const router = useRouter();

  useEffect(() => {
    if (hydrated && !jwt) router.replace('/signin');
  }, [hydrated, jwt, router]);

  if (!hydrated || !jwt) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bone-deep">
        <Spinner />
      </div>
    );
  }
  return <>{children}</>;
}
