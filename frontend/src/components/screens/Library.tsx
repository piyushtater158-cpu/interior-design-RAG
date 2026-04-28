'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGate } from '@/components/shared/AuthGate';
import { MobStatusBar } from '@/components/mobile/MobStatusBar';
import { MobNav } from '@/components/mobile/MobNav';
import { MobTabBar, type TabId } from '@/components/mobile/MobTabBar';
import { Card } from '@/components/atelier/Card';
import { Anno } from '@/components/atelier/Anno';
import { Btn } from '@/components/atelier/Btn';
import { RoomRender } from '@/components/atelier/RoomRender';
import { BlueprintBg } from '@/components/atelier/BlueprintBg';
import { FilterChip } from '@/components/shared/FilterChip';
import { HeartBtn } from '@/components/shared/HeartBtn';
import { Spinner } from '@/components/shared/Loader';
import { CreditsPill } from '@/components/canvas/CreditsPill';
import { useAppStore } from '@/store/app';
import { api } from '@/lib/api';
import { ROOM_TYPES, type RoomType } from '@/lib/tokens';
import type { MockSession } from '@/lib/mockLibrary';

type Filter = 'all' | RoomType | 'favourites';
type Sort = 'recent' | 'most_revised';

function LibraryInner() {
  const router = useRouter();
  const favourites = useAppStore((s) => s.favourites);
  const toggleFavourite = useAppStore((s) => s.toggleFavourite);
  const unreadNotifications = useAppStore((s) => s.unreadNotifications);

  const [sessions, setSessions] = useState<MockSession[] | null>(null);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<Filter>('all');
  const [sort, setSort] = useState<Sort>('recent');

  useEffect(() => {
    let alive = true;
    api
      .listUserSessions()
      .then((items) => {
        if (alive) setSessions(items);
      })
      .catch(() => {
        if (alive) setSessions([]);
      });
    return () => {
      alive = false;
    };
  }, []);

  const isFav = (s: MockSession) => favourites.includes(s.id) || s.favourite;

  const visible = useMemo(() => {
    if (!sessions) return [];
    const q = query.trim().toLowerCase();
    let out = sessions.filter((s) => {
      if (q) {
        const hay = `${s.caption} ${s.roomType} ${s.styleTag}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      if (filter === 'favourites') return isFav(s);
      if (filter !== 'all') return s.roomType === filter;
      return true;
    });
    out = [...out].sort((a, b) =>
      sort === 'most_revised' ? b.revCount - a.revCount : 0,
    );
    return out;
  }, [sessions, query, filter, sort, favourites]);

  const filterChips: { id: Filter; label: string; count?: number }[] = [
    { id: 'all', label: 'All', count: sessions?.length },
    ...ROOM_TYPES.map((r) => ({
      id: r.id as Filter,
      label: r.name,
      count: sessions?.filter((s) => s.roomType === r.id).length,
    })),
    {
      id: 'favourites',
      label: 'Favourites',
      count: sessions?.filter(isFav).length,
    },
  ];

  const goTab = (t: TabId) => {
    if (t === 'home') router.push('/app');
    else if (t === 'library') return;
    else if (t === 'profile') router.push('/app/profile');
    else if (t === 'canvas') router.push('/app');
  };

  return (
    <BlueprintBg className="min-h-screen pb-[90px] lg:pb-8">
      <div className="lg:hidden">
        <MobStatusBar />
      </div>

      <div className="lg:max-w-[1200px] lg:mx-auto">
        <MobNav
          title="Library"
          sub="past projects"
          trailing={<CreditsPill />}
        />

        <div className="px-5 pt-4 lg:px-10">
          <Anno className="block mb-2">02 · past work</Anno>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search sessions, rooms, styles…"
            className="w-full font-sans text-[14px] px-4 py-3 outline-none"
            style={{
              background: '#FFFFFF',
              border: '1px solid #D8D0BE',
              borderRadius: 12,
              color: '#1C1B17',
            }}
          />
        </div>

        <div className="px-5 pt-3 lg:px-10 flex items-center gap-2 overflow-x-auto no-scrollbar">
          {filterChips.map((c) => (
            <FilterChip
              key={c.id}
              label={c.label}
              active={filter === c.id}
              onClick={() => setFilter(c.id)}
              count={c.count}
            />
          ))}
        </div>

        <div className="px-5 pt-3 pb-4 lg:px-10 flex items-center justify-between">
          <Anno>{visible.length} {visible.length === 1 ? 'session' : 'sessions'}</Anno>
          <div className="flex items-center gap-2">
            <Anno>sort</Anno>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as Sort)}
              className="font-sans text-[12px] px-2 py-1 bg-card"
              style={{ border: '1px solid #D8D0BE', borderRadius: 8 }}
            >
              <option value="recent">Recent</option>
              <option value="most_revised">Most revised</option>
            </select>
          </div>
        </div>

        {sessions === null ? (
          <div className="flex items-center justify-center py-24">
            <Spinner />
          </div>
        ) : visible.length === 0 ? (
          <div className="px-5 lg:px-10 py-16 text-center flex flex-col items-center gap-4">
            <h2 className="font-serif text-[26px] leading-tight">Nothing here yet</h2>
            <p className="text-ink-soft text-sm max-w-sm">
              Start a new session and your committed projects will collect here.
            </p>
            <Btn onClick={() => router.push('/app')}>New session</Btn>
          </div>
        ) : (
          <div className="px-5 lg:px-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {visible.map((s) => (
              <Card
                key={s.id}
                onClick={() => router.push(`/app/session/${s.id}`)}
                className="p-0 overflow-hidden flex flex-col"
              >
                <div className="relative h-[200px]">
                  <RoomRender type={s.roomType} tone={s.tone} />
                  <div className="absolute top-3 right-3">
                    <HeartBtn active={isFav(s)} onToggle={() => toggleFavourite(s.id)} />
                  </div>
                  {s.committed && (
                    <div
                      className="absolute top-3 left-3 px-2 py-0.5 rounded-full"
                      style={{ background: '#1C1B17' }}
                    >
                      <Anno color="#FBF8F2">committed</Anno>
                    </div>
                  )}
                </div>
                <div className="p-4 flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <div className="font-serif text-[20px] leading-tight">{s.caption}</div>
                    <Anno>rev·{String(s.revCount).padStart(2, '0')}</Anno>
                  </div>
                  <Anno>
                    {s.roomType} · {s.styleTag}
                  </Anno>
                  <Anno className="mt-1">{s.createdAt}</Anno>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      <div className="lg:hidden">
        <MobTabBar tab="library" onTab={goTab} unreadCount={unreadNotifications} />
      </div>
    </BlueprintBg>
  );
}

export function Library() {
  return (
    <AuthGate>
      <LibraryInner />
    </AuthGate>
  );
}
