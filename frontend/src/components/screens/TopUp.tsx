'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGate } from '@/components/shared/AuthGate';
import { MobStatusBar } from '@/components/mobile/MobStatusBar';
import { MobNav } from '@/components/mobile/MobNav';
import { Card } from '@/components/atelier/Card';
import { Anno } from '@/components/atelier/Anno';
import { Btn } from '@/components/atelier/Btn';
import { BlueprintBg } from '@/components/atelier/BlueprintBg';
import { Spinner } from '@/components/shared/Loader';
import { ErrorBanner } from '@/components/shared/ErrorBanner';
import { FilterChip } from '@/components/shared/FilterChip';
import { useAppStore } from '@/store/app';
import { api, ApiError } from '@/lib/api';
import { creditsFor, inrFor, formatInr } from '@/lib/format';
import { TOPUP_PRESETS_INR } from '@/lib/mockLibrary';

function TopUpInner() {
  const router = useRouter();
  const mockCredits = useAppStore((s) => s.mockCredits);
  const creditRateInr = useAppStore((s) => s.creditRateInr);
  const minTopUpInr = useAppStore((s) => s.minTopUpInr);
  const storageMonthlyInr = useAppStore((s) => s.storageMonthlyInr);
  const addCredits = useAppStore((s) => s.addCredits);

  const [amount, setAmount] = useState<number>(TOPUP_PRESETS_INR[0]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const credits = useMemo(() => creditsFor(amount, creditRateInr), [amount, creditRateInr]);
  const balanceInr = inrFor(mockCredits, creditRateInr);
  const belowMin = amount < minTopUpInr;

  const confirm = async () => {
    if (belowMin || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await api.topUpCredits({ amountInr: amount });
      addCredits(res.credits);
      setToast(`Added ${res.credits} credits`);
      setTimeout(() => setToast(null), 2400);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Top-up failed. Try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <BlueprintBg className="min-h-screen pb-16">
      <div className="lg:hidden">
        <MobStatusBar />
      </div>

      <div className="lg:max-w-[720px] lg:mx-auto">
        <MobNav title="Top up" sub="buy credits" onBack={() => router.back()} />

        <div className="px-5 pt-4 lg:px-10 flex flex-col gap-4">
          <Card className="p-5 flex flex-col gap-1">
            <Anno>current balance</Anno>
            <div className="flex items-baseline gap-3 mt-1">
              <span className="font-serif text-[40px] leading-none">{mockCredits}</span>
              <span className="font-sans text-sm text-mute">credits</span>
              <span className="font-sans text-sm text-mute ml-auto">≈ {formatInr(balanceInr)}</span>
            </div>
            <Anno className="mt-1">₹{creditRateInr} per credit</Anno>
          </Card>

          <div className="flex flex-col gap-2">
            <Anno>preset amounts</Anno>
            <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
              {TOPUP_PRESETS_INR.map((p) => (
                <FilterChip
                  key={p}
                  label={formatInr(p)}
                  active={amount === p}
                  onClick={() => setAmount(p)}
                />
              ))}
            </div>
          </div>

          <Card className="p-5 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <Anno>custom amount</Anno>
              <Anno>min · {formatInr(minTopUpInr)}</Anno>
            </div>
            <div
              className="flex items-center gap-2 px-3 py-2"
              style={{ background: '#FEFCF6', border: '1px solid #D8D0BE', borderRadius: 10 }}
            >
              <span className="font-serif text-[22px] text-ink-soft">₹</span>
              <input
                type="number"
                inputMode="numeric"
                min={minTopUpInr}
                step={100}
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value) || 0)}
                className="flex-1 font-serif text-[22px] bg-transparent outline-none text-ink"
              />
            </div>
            <div className="flex items-center justify-between">
              <Anno>you get</Anno>
              <div className="flex items-baseline gap-2">
                <span className="font-serif text-[24px] leading-none">{credits}</span>
                <span className="font-sans text-sm text-mute">credits</span>
              </div>
            </div>
            {belowMin && (
              <div className="font-sans text-[12px]" style={{ color: '#B85C3A' }}>
                Minimum top-up is {formatInr(minTopUpInr)}.
              </div>
            )}
          </Card>

          {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

          <Btn variant="clay" size="lg" onClick={confirm} disabled={belowMin || submitting}>
            {submitting ? <Spinner size={14} color="#FBF8F2" /> : null}
            {submitting ? 'Processing…' : `Confirm · ${formatInr(amount)}`}
          </Btn>

          <Card className="p-4 flex flex-col gap-2" hover={false}>
            <Anno>rate card</Anno>
            <ul className="flex flex-col gap-1.5 font-sans text-[13px] text-ink-soft">
              <li>· ₹{creditRateInr} per credit</li>
              <li>· Storage {formatInr(storageMonthlyInr)}/month</li>
              <li>· Credits never expire</li>
              <li>· Draft 2 · Edit 1 · Commit 3 credits</li>
            </ul>
          </Card>
        </div>
      </div>

      {toast && (
        <div
          className="fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-2.5 rounded-full z-40"
          style={{
            background: '#1C1B17',
            color: '#FBF8F2',
            boxShadow: '0 10px 24px rgba(28,27,23,0.3)',
          }}
        >
          <span className="font-sans text-[13px]">{toast}</span>
        </div>
      )}
    </BlueprintBg>
  );
}

export function TopUp() {
  return (
    <AuthGate>
      <TopUpInner />
    </AuthGate>
  );
}
