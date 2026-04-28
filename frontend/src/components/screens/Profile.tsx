'use client';

import { useRouter } from 'next/navigation';
import { AuthGate } from '@/components/shared/AuthGate';
import { MobStatusBar } from '@/components/mobile/MobStatusBar';
import { MobNav } from '@/components/mobile/MobNav';
import { MobTabBar, type TabId } from '@/components/mobile/MobTabBar';
import { Card } from '@/components/atelier/Card';
import { Anno } from '@/components/atelier/Anno';
import { Btn } from '@/components/atelier/Btn';
import { BlueprintBg } from '@/components/atelier/BlueprintBg';
import { useAppStore, type NotifPrefKey } from '@/store/app';
import { useSessionStore } from '@/store/session';
import { inrFor, formatInr } from '@/lib/format';

const NOTIF_ROWS: { key: NotifPrefKey; title: string; sub: string }[] = [
  { key: 'lowBalance', title: 'Low balance alerts', sub: 'Ping me when credits drop below a commit.' },
  { key: 'commitDone', title: 'Commit complete', sub: 'High-fidelity render finished.' },
  { key: 'features', title: 'Product updates', sub: 'New models and capabilities.' },
  { key: 'storage', title: 'Storage invoices', sub: 'Monthly storage charges.' },
];

function Row({
  title,
  sub,
  checked,
  onChange,
}: {
  title: string;
  sub: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label
      className="flex items-start justify-between gap-4 py-3 cursor-pointer"
      style={{ borderBottom: '1px solid #EAE2D4' }}
    >
      <div className="flex-1 min-w-0">
        <div className="font-sans text-[14px] text-ink">{title}</div>
        <div className="font-sans text-[12px] text-mute mt-0.5">{sub}</div>
      </div>
      <span
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className="shrink-0 relative inline-block cursor-pointer transition-colors"
        style={{
          width: 40,
          height: 24,
          borderRadius: 999,
          background: checked ? '#3D4A2A' : '#D8D0BE',
        }}
      >
        <span
          className="absolute top-[2px] transition-all"
          style={{
            left: checked ? 18 : 2,
            width: 20,
            height: 20,
            borderRadius: 999,
            background: '#FBF8F2',
            boxShadow: '0 1px 2px rgba(0,0,0,0.15)',
          }}
        />
      </span>
      <input type="checkbox" className="sr-only" checked={checked} onChange={() => onChange(!checked)} />
    </label>
  );
}

function ProfileInner() {
  const router = useRouter();
  const email = useAppStore((s) => s.email);
  const mockCredits = useAppStore((s) => s.mockCredits);
  const creditRateInr = useAppStore((s) => s.creditRateInr);
  const storageMonthlyInr = useAppStore((s) => s.storageMonthlyInr);
  const notifPrefs = useAppStore((s) => s.notifPrefs);
  const unreadNotifications = useAppStore((s) => s.unreadNotifications);
  const setNotifPref = useAppStore((s) => s.setNotifPref);
  const clearAuth = useAppStore((s) => s.clearAuth);
  const resetSession = useSessionStore((s) => s.reset);

  const initial = (email ?? 'A').trim().charAt(0).toUpperCase();
  const balanceInr = inrFor(mockCredits, creditRateInr);

  const signOut = () => {
    clearAuth();
    resetSession();
    if (typeof window !== 'undefined') {
      localStorage.removeItem('atelier:jwt');
      localStorage.removeItem('atelier:user');
    }
    router.push('/');
  };

  const goTab = (t: TabId) => {
    if (t === 'home') router.push('/app');
    else if (t === 'library') router.push('/app/library');
    else if (t === 'profile') return;
    else if (t === 'canvas') router.push('/app');
  };

  return (
    <BlueprintBg className="min-h-screen pb-[90px] lg:pb-8">
      <div className="lg:hidden">
        <MobStatusBar />
      </div>

      <div className="lg:max-w-[880px] lg:mx-auto">
        <MobNav
          title="Profile"
          sub={email ?? 'signed in'}
          trailing={
            <button
              onClick={() => router.push('/app/notifications')}
              className="relative w-9 h-9 rounded-full flex items-center justify-center cursor-pointer bg-card p-0"
              style={{ border: '1px solid #D8D0BE' }}
              aria-label="Notifications"
            >
              <svg width="16" height="16" viewBox="0 0 20 20">
                <path
                  d="M4 14 C 5 12 5 10 5 8 C 5 5 7 3 10 3 C 13 3 15 5 15 8 C 15 10 15 12 16 14 Z M8 16 C 8 17 9 18 10 18 C 11 18 12 17 12 16"
                  stroke="#1C1B17"
                  strokeWidth="1.6"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              {unreadNotifications > 0 && (
                <span
                  className="absolute top-1 right-1 w-[8px] h-[8px] rounded-full"
                  style={{ background: '#B85C3A', border: '1.5px solid #FBF8F2' }}
                />
              )}
            </button>
          }
        />

        <div className="px-5 pt-4 lg:px-10 flex flex-col gap-4">
          <Card className="p-5 flex items-center gap-4">
            <div
              className="shrink-0 w-14 h-14 rounded-full flex items-center justify-center"
              style={{ background: '#EAE2D4', border: '1px solid #D8D0BE' }}
            >
              <span className="font-serif text-[22px] text-ink">{initial}</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-serif text-[22px] leading-tight truncate">{email ?? 'Designer'}</div>
              <Anno className="block mt-1">member · atelier studio</Anno>
            </div>
          </Card>

          <Card className="p-5 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <Anno>wallet</Anno>
              <Anno>₹{creditRateInr} per credit</Anno>
            </div>
            <div className="flex items-baseline gap-3">
              <span className="font-serif text-[40px] leading-none">{mockCredits}</span>
              <span className="font-sans text-sm text-mute">credits</span>
              <span className="font-sans text-sm text-mute ml-auto">≈ {formatInr(balanceInr)}</span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <Btn variant="primary" className="flex-1" onClick={() => router.push('/app/topup')}>
                Top up
              </Btn>
              <Btn variant="secondary" onClick={() => router.push('/app/notifications')}>
                Activity
              </Btn>
            </div>
            <Anno className="mt-1">storage · {formatInr(storageMonthlyInr)}/month · credits never expire</Anno>
          </Card>

          <Card className="p-5 flex flex-col gap-2">
            <Anno>usage</Anno>
            <div className="grid grid-cols-3 gap-3 mt-1">
              <Stat label="Drafts" value="14" />
              <Stat label="Edits" value="42" />
              <Stat label="Commits" value="6" />
            </div>
          </Card>

          <Card className="p-5">
            <Anno className="block mb-2">notifications</Anno>
            {NOTIF_ROWS.map((r) => (
              <Row
                key={r.key}
                title={r.title}
                sub={r.sub}
                checked={notifPrefs[r.key]}
                onChange={(v) => setNotifPref(r.key, v)}
              />
            ))}
          </Card>

          <Card className="p-5 flex flex-col gap-2">
            <Anno>account</Anno>
            <Btn variant="ghost" onClick={signOut} className="justify-start w-full">
              Sign out
            </Btn>
          </Card>
        </div>
      </div>

      <div className="lg:hidden">
        <MobTabBar tab="profile" onTab={goTab} unreadCount={unreadNotifications} />
      </div>
    </BlueprintBg>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="font-serif text-[22px] leading-none">{value}</span>
      <Anno>{label}</Anno>
    </div>
  );
}

export function Profile() {
  return (
    <AuthGate>
      <ProfileInner />
    </AuthGate>
  );
}
