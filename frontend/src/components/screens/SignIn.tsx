'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { AtelierMark } from '@/components/atelier/AtelierMark';
import { BlueprintBg } from '@/components/atelier/BlueprintBg';
import { Btn } from '@/components/atelier/Btn';
import { Anno } from '@/components/atelier/Anno';
import { ErrorBanner } from '@/components/shared/ErrorBanner';
import { Spinner } from '@/components/shared/Loader';
import { api, ApiError } from '@/lib/api';
import { useAppStore } from '@/store/app';

export function SignIn() {
  const router = useRouter();
  const setAuth = useAppStore((s) => s.setAuth);

  const [email, setEmail] = useState('demo@example.com');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.authMagicLink(email.trim());
      setAuth(res.token, res.user_id, email.trim());
      if (typeof window !== 'undefined') {
        localStorage.setItem('atelier:jwt', res.token);
      }
      router.push('/app');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Sign-in failed. Try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <BlueprintBg className="min-h-screen flex items-center justify-center px-6">
      <form
        onSubmit={submit}
        className="w-full max-w-sm flex flex-col gap-5 bg-card rounded-[14px] p-7 shadow-med"
        style={{ border: '1px solid #D8D0BE' }}
      >
        <div className="flex items-center gap-3">
          <AtelierMark size={28} />
          <div className="font-serif text-[22px]">Atelier</div>
        </div>
        <div>
          <Anno className="block mb-2">sign in · mock magic link</Anno>
          <h2 className="font-serif text-[26px] leading-tight">Enter your studio email</h2>
        </div>

        <label className="flex flex-col gap-1.5 text-sm">
          <span className="text-ink-soft">Email</span>
          <input
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@studio.com"
            className="rounded-lg px-3.5 h-11 bg-paper text-ink outline-none"
            style={{ border: '1px solid #D8D0BE' }}
          />
        </label>

        {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

        <Btn type="submit" size="lg" disabled={loading || !email.trim()}>
          {loading ? <Spinner size={14} color="#FBF8F2" /> : null}
          {loading ? 'Signing in…' : 'Sign in'}
        </Btn>

        <Anno className="block text-center">mvp · jwt stored in localStorage</Anno>
      </form>
    </BlueprintBg>
  );
}
