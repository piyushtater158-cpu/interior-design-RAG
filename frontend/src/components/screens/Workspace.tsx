'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGate } from '@/components/shared/AuthGate';
import { MobStatusBar } from '@/components/mobile/MobStatusBar';
import { MobNav } from '@/components/mobile/MobNav';
import { MobTabBar, type TabId } from '@/components/mobile/MobTabBar';
import { Card } from '@/components/atelier/Card';
import { Anno } from '@/components/atelier/Anno';
import { IsoRoom } from '@/components/atelier/IsoRoom';
import { AtelierMark } from '@/components/atelier/AtelierMark';
import { CreditsPill } from '@/components/canvas/CreditsPill';
import { BlueprintBg } from '@/components/atelier/BlueprintBg';
import { ROOM_TYPES } from '@/lib/tokens';
import { useAppStore } from '@/store/app';
import { api } from '@/lib/api';

const TONES = ['warm', 'cool', 'moody', 'warm'] as const;

function WorkspaceInner() {
  const router = useRouter();
  const email = useAppStore((s) => s.email);
  const unreadNotifications = useAppStore((s) => s.unreadNotifications);

  // Best-effort A/B config fetch — admin-only, silent on 403.
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL ?? 'https://n8n.srv1649259.hstgr.cloud/webhook'}/admin/ab-config`,
        );
        if (!alive || !r.ok) return;
        const body: { config?: 'A' | 'B' } = await r.json();
        if (body.config) useAppStore.getState().setAbConfig(body.config);
      } catch {
        /* ignore */
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  // Seed unread notification count (stub — returns mock).
  useEffect(() => {
    let alive = true;
    api
      .listNotifications()
      .then((xs) => {
        if (!alive) return;
        useAppStore.getState().setUnreadNotifications(xs.filter((n) => !n.read).length);
      })
      .catch(() => {
        /* ignore */
      });
    return () => {
      alive = false;
    };
  }, []);

  const goTab = (t: TabId) => {
    if (t === 'home') return;
    if (t === 'library') router.push('/app/library');
    else if (t === 'profile') router.push('/app/profile');
    else if (t === 'canvas') router.push('/app');
  };

  return (
    <BlueprintBg className="min-h-screen pb-[90px] lg:pb-8">
      <div className="lg:hidden">
        <MobStatusBar />
      </div>

      <div className="lg:max-w-[1200px] lg:mx-auto">
        <div className="hidden lg:flex items-center justify-between px-10 pt-8 pb-4">
          <div className="flex items-center gap-3">
            <AtelierMark size={28} />
            <span className="font-serif text-[22px]">Atelier</span>
            <Anno className="ml-3">studio workspace</Anno>
          </div>
          <CreditsPill />
        </div>

        <div className="lg:hidden">
          <MobNav
            title="Studio"
            sub={email ? `signed in · ${email}` : 'signed in'}
            trailing={<CreditsPill />}
          />
        </div>

        <div className="px-5 pt-4 lg:px-10 lg:pt-2">
          <Anno className="block mb-2">01 · choose a room</Anno>
          <h1 className="font-serif text-[28px] lg:text-[40px] leading-tight">
            What are we designing today?
          </h1>
          <p className="text-ink-soft mt-2 text-sm lg:text-base max-w-xl">
            Pick a room. Each room opens with its own retrieval index and prompt pack.
          </p>
        </div>

        <div className="px-5 py-5 lg:px-10 lg:py-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {ROOM_TYPES.map((r, i) => (
            <Card
              key={r.id}
              onClick={() => router.push(`/app/new?type=${r.id}`)}
              className="p-5 flex flex-col gap-3"
            >
              <div className="flex items-center justify-between">
                <Anno>0{i + 1}</Anno>
                <svg width="14" height="14" viewBox="0 0 14 14">
                  <path d="M3 7 L11 7 M7 3 L11 7 L7 11" stroke="#1C1B17" strokeWidth="1.5" fill="none" strokeLinecap="round" />
                </svg>
              </div>
              <div className="flex items-center justify-center py-3">
                <IsoRoom type={r.iso as 'bedroom' | 'dining' | 'kitchen' | 'mandir'} size={160} tone={TONES[i]} />
              </div>
              <div>
                <div className="font-serif text-[22px] leading-tight">{r.name}</div>
                <Anno className="block mt-1">{r.sub}</Anno>
              </div>
            </Card>
          ))}
        </div>
      </div>

      <div className="lg:hidden">
        <MobTabBar tab="home" onTab={goTab} unreadCount={unreadNotifications} />
      </div>
    </BlueprintBg>
  );
}

export function Workspace() {
  return (
    <AuthGate>
      <WorkspaceInner />
    </AuthGate>
  );
}
