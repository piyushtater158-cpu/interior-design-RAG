'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { useAppStore } from '@/store/app';
import { Spinner } from '@/components/shared/Loader';

export default function Callback() {
  const router = useRouter();
  const setAuth = useAppStore((s) => s.setAuth);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setAuth(session.access_token, session.user.id, session.user.email ?? '');
        router.replace('/app');
      } else {
        router.replace('/signin');
      }
    });
  }, [router, setAuth]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-bone-deep">
      <Spinner />
    </div>
  );
}
