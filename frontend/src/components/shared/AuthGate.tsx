'use client';

import { useEffect, useState, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/store/app';
import { supabase } from '@/lib/supabase';
import { Spinner } from './Loader';

export function AuthGate({ children }: { children: ReactNode }) {
  const [sessionReady, setSessionReady] = useState(false);
  const jwt = useAppStore((s) => s.jwt);
  const setAuth = useAppStore((s) => s.setAuth);
  const clearAuth = useAppStore((s) => s.clearAuth);
  const router = useRouter();

  useEffect(() => {
    // Resolve current session (handles auto-refresh of Supabase tokens)
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setAuth(session.access_token, session.user.id, session.user.email ?? '');
      } else {
        clearAuth();
        router.replace('/signin');
      }
      setSessionReady(true);
    });

    // Keep store in sync with token refreshes and sign-outs
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setAuth(session.access_token, session.user.id, session.user.email ?? '');
      } else {
        clearAuth();
        router.replace('/signin');
      }
    });

    return () => subscription.unsubscribe();
  }, [setAuth, clearAuth, router]);

  if (!sessionReady || !jwt) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bone-deep">
        <Spinner />
      </div>
    );
  }
  return <>{children}</>;
}
