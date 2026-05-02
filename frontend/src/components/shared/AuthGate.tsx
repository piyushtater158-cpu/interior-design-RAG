'use client';

import { useEffect, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/store/app';
import { useHydrated } from '@/hooks/useHydrated';
import { Spinner } from './Loader';

function jwtIsExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    return typeof payload.exp === 'number' && payload.exp < Date.now() / 1000;
  } catch {
    return true;
  }
}

export function AuthGate({ children }: { children: ReactNode }) {
  const hydrated = useHydrated();
  const jwt = useAppStore((s) => s.jwt);
  const clearAuth = useAppStore((s) => s.clearAuth);
  const router = useRouter();

  useEffect(() => {
    if (hydrated && (!jwt || jwtIsExpired(jwt))) {
      clearAuth();
      router.replace('/signin');
    }
  }, [hydrated, jwt, clearAuth, router]);

  if (!hydrated || !jwt || jwtIsExpired(jwt)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bone-deep">
        <Spinner />
      </div>
    );
  }
  return <>{children}</>;
}
