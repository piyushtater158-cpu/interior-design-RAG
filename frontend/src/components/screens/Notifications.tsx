'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGate } from '@/components/shared/AuthGate';
import { MobStatusBar } from '@/components/mobile/MobStatusBar';
import { MobNav } from '@/components/mobile/MobNav';
import { Card } from '@/components/atelier/Card';
import { Anno } from '@/components/atelier/Anno';
import { Btn } from '@/components/atelier/Btn';
import { BlueprintBg } from '@/components/atelier/BlueprintBg';
import { NotifDot } from '@/components/shared/NotifDot';
import { Spinner } from '@/components/shared/Loader';
import { api } from '@/lib/api';
import { useAppStore } from '@/store/app';
import type { MockNotification, NotifCtaScreen } from '@/lib/mockLibrary';

function ctaHref(screen: NotifCtaScreen, sessionId?: string): string {
  switch (screen) {
    case 'topup':
      return '/app/topup';
    case 'library':
      return '/app/library';
    case 'profile':
      return '/app/profile';
    case 'canvas':
      return sessionId ? `/app/session/${sessionId}` : '/app';
  }
}

function Row({
  n,
  onCta,
}: {
  n: MockNotification;
  onCta: (n: MockNotification) => void;
}) {
  return (
    <Card className="p-4 flex gap-3" hover={false}>
      <div className="pt-1.5">
        <NotifDot type={n.type} />
      </div>
      <div className="flex-1 min-w-0 flex flex-col gap-1">
        <div className="flex items-start justify-between gap-2">
          <div className="font-serif text-[16px] leading-tight text-ink">{n.title}</div>
          <Anno>{n.time}</Anno>
        </div>
        <p className="font-sans text-[13px] text-ink-soft leading-relaxed">{n.body}</p>
        {n.cta && n.ctaScreen && (
          <div className="mt-1">
            <Btn size="sm" variant="secondary" onClick={() => onCta(n)}>
              {n.cta}
            </Btn>
          </div>
        )}
      </div>
    </Card>
  );
}

function NotificationsInner() {
  const router = useRouter();
  const setUnread = useAppStore((s) => s.setUnreadNotifications);
  const markRead = useAppStore((s) => s.markNotificationsRead);

  const [items, setItems] = useState<MockNotification[] | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .listNotifications()
      .then((xs) => {
        if (!alive) return;
        setItems(xs);
        setUnread(xs.filter((x) => !x.read).length);
      })
      .catch(() => {
        if (alive) setItems([]);
      });
    return () => {
      alive = false;
    };
  }, [setUnread]);

  const { unread, earlier } = useMemo(() => {
    const list = items ?? [];
    return {
      unread: list.filter((n) => !n.read),
      earlier: list.filter((n) => n.read),
    };
  }, [items]);

  const handleCta = (n: MockNotification) => {
    router.push(ctaHref(n.ctaScreen!, n.sessionId));
  };

  const handleMarkAll = () => {
    if (!items) return;
    setItems(items.map((n) => ({ ...n, read: true })));
    markRead();
  };

  return (
    <BlueprintBg className="min-h-screen pb-12 lg:pb-8">
      <div className="lg:hidden">
        <MobStatusBar />
      </div>

      <div className="lg:max-w-[880px] lg:mx-auto">
        <MobNav
          title="Notifications"
          sub={unread.length > 0 ? `${unread.length} unread` : 'all caught up'}
          onBack={() => router.back()}
          trailing={
            unread.length > 0 ? (
              <Btn size="sm" variant="ghost" onClick={handleMarkAll}>
                Mark all read
              </Btn>
            ) : undefined
          }
        />

        <div className="px-5 pt-4 lg:px-10 flex flex-col gap-5">
          {items === null ? (
            <div className="flex items-center justify-center py-16">
              <Spinner />
            </div>
          ) : items.length === 0 ? (
            <div className="py-16 text-center flex flex-col items-center gap-3">
              <h2 className="font-serif text-[24px]">You&apos;re all caught up</h2>
              <p className="text-ink-soft text-sm">
                We&apos;ll ping you when credits run low or a commit finishes.
              </p>
            </div>
          ) : (
            <>
              {unread.length > 0 && (
                <section className="flex flex-col gap-3">
                  <Anno>new</Anno>
                  {unread.map((n) => (
                    <Row key={n.id} n={n} onCta={handleCta} />
                  ))}
                </section>
              )}
              {earlier.length > 0 && (
                <section className="flex flex-col gap-3">
                  <Anno>earlier</Anno>
                  {earlier.map((n) => (
                    <Row key={n.id} n={n} onCta={handleCta} />
                  ))}
                </section>
              )}
            </>
          )}
        </div>
      </div>
    </BlueprintBg>
  );
}

export function Notifications() {
  return (
    <AuthGate>
      <NotificationsInner />
    </AuthGate>
  );
}
