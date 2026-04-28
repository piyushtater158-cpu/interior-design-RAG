'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { CREDIT_RATE_INR_DEFAULT, MIN_TOPUP_INR_DEFAULT, STORAGE_MONTHLY_INR_DEFAULT } from '@/lib/tokens';

export type NotifPrefKey = 'lowBalance' | 'commitDone' | 'features' | 'storage';
export type NotifPrefs = Record<NotifPrefKey, boolean>;

interface AppState {
  jwt: string | null;
  userId: string | null;
  email: string | null;
  mockCredits: number;
  abConfig: 'A' | 'B';
  creditRateInr: number;
  minTopUpInr: number;
  storageMonthlyInr: number;
  unreadNotifications: number;
  notifPrefs: NotifPrefs;
  favourites: string[];
  setAuth: (jwt: string, userId: string, email: string) => void;
  clearAuth: () => void;
  decrementCredits: (n: number) => void;
  setCredits: (n: number) => void;
  addCredits: (n: number) => void;
  setAbConfig: (c: 'A' | 'B') => void;
  setCreditRate: (rate: number) => void;
  setMinTopUp: (min: number) => void;
  setStorageMonthly: (amt: number) => void;
  setUnreadNotifications: (n: number) => void;
  markNotificationsRead: () => void;
  setNotifPref: (key: NotifPrefKey, value: boolean) => void;
  toggleFavourite: (id: string) => void;
  hydrated: boolean;
  _setHydrated: () => void;
}

const envNumber = (v: string | undefined, fallback: number) => {
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : fallback;
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      jwt: null,
      userId: null,
      email: null,
      mockCredits: 24,
      abConfig: 'A',
      creditRateInr: envNumber(process.env.NEXT_PUBLIC_CREDIT_RATE_INR, CREDIT_RATE_INR_DEFAULT),
      minTopUpInr: envNumber(process.env.NEXT_PUBLIC_MIN_TOPUP_INR, MIN_TOPUP_INR_DEFAULT),
      storageMonthlyInr: envNumber(
        process.env.NEXT_PUBLIC_STORAGE_MONTHLY_INR,
        STORAGE_MONTHLY_INR_DEFAULT,
      ),
      unreadNotifications: 0,
      notifPrefs: { lowBalance: true, commitDone: true, features: false, storage: true },
      favourites: [],
      hydrated: false,
      setAuth: (jwt, userId, email) => set({ jwt, userId, email }),
      clearAuth: () =>
        set({
          jwt: null,
          userId: null,
          email: null,
          favourites: [],
          unreadNotifications: 0,
        }),
      decrementCredits: (n) => set((s) => ({ mockCredits: Math.max(0, s.mockCredits - n) })),
      setCredits: (n) => set({ mockCredits: n }),
      addCredits: (n) => set((s) => ({ mockCredits: s.mockCredits + n })),
      setAbConfig: (c) => set({ abConfig: c }),
      setCreditRate: (rate) => set({ creditRateInr: rate }),
      setMinTopUp: (min) => set({ minTopUpInr: min }),
      setStorageMonthly: (amt) => set({ storageMonthlyInr: amt }),
      setUnreadNotifications: (n) => set({ unreadNotifications: Math.max(0, n) }),
      markNotificationsRead: () => set({ unreadNotifications: 0 }),
      setNotifPref: (key, value) =>
        set((s) => ({ notifPrefs: { ...s.notifPrefs, [key]: value } })),
      toggleFavourite: (id) =>
        set((s) => ({
          favourites: s.favourites.includes(id)
            ? s.favourites.filter((f) => f !== id)
            : [...s.favourites, id],
        })),
      _setHydrated: () => set({ hydrated: true }),
    }),
    {
      name: 'atelier:app',
      storage: createJSONStorage(() => (typeof window !== 'undefined' ? localStorage : undefined as never)),
      partialize: (s) => ({
        jwt: s.jwt,
        userId: s.userId,
        email: s.email,
        mockCredits: s.mockCredits,
        favourites: s.favourites,
        notifPrefs: s.notifPrefs,
      }),
      onRehydrateStorage: () => (state) => {
        state?._setHydrated();
      },
    },
  ),
);
