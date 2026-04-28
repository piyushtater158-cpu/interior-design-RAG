'use client';

type TabId = 'home' | 'canvas' | 'library' | 'profile';

const TABS: { id: TabId; label: string; icon: 'home' | 'frame' | 'stack' | 'me' }[] = [
  { id: 'home', label: 'Studio', icon: 'home' },
  { id: 'canvas', label: 'Canvas', icon: 'frame' },
  { id: 'library', label: 'Library', icon: 'stack' },
  { id: 'profile', label: 'Profile', icon: 'me' },
];

function renderIcon(kind: 'home' | 'frame' | 'stack' | 'me', active: boolean) {
  const c = active ? '#1C1B17' : '#8B8676';
  const p = { fill: 'none', stroke: c, strokeWidth: 1.6, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  switch (kind) {
    case 'home':
      return (
        <svg width="22" height="22" viewBox="0 0 22 22">
          <path d="M3 10 L11 3 L19 10 V19 H3 Z" {...p} />
          <path d="M8 19 V14 H14 V19" {...p} />
        </svg>
      );
    case 'frame':
      return (
        <svg width="22" height="22" viewBox="0 0 22 22">
          <rect x="3" y="4" width="16" height="14" rx="2" {...p} />
          <path d="M3 14 L8 9 L12 13 L16 10 L19 13" {...p} />
          <circle cx="8" cy="8" r="1.2" {...p} />
        </svg>
      );
    case 'stack':
      return (
        <svg width="22" height="22" viewBox="0 0 22 22">
          <rect x="3" y="7" width="16" height="12" rx="2" {...p} />
          <path d="M5 4 H17 M6 1 H16" {...p} />
        </svg>
      );
    case 'me':
      return (
        <svg width="22" height="22" viewBox="0 0 22 22">
          <circle cx="11" cy="8" r="4" {...p} />
          <path d="M3 20 C 3 15 7 13 11 13 S 19 15 19 20" {...p} />
        </svg>
      );
  }
}

type Props = {
  tab: TabId;
  onTab: (t: TabId) => void;
  unreadCount?: number;
  /** Which tab gets the unread dot. Defaults to 'profile'. */
  unreadOn?: TabId;
};

export function MobTabBar({ tab, onTab, unreadCount = 0, unreadOn = 'profile' }: Props) {
  return (
    <div
      className="absolute bottom-0 left-0 right-0 pb-[22px] pt-2 flex justify-around z-30"
      style={{
        background: 'rgba(251,248,242,0.92)',
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        borderTop: '0.5px solid #D8D0BE',
      }}
    >
      {TABS.map((t) => {
        const showDot = unreadCount > 0 && t.id === unreadOn;
        return (
          <button
            key={t.id}
            onClick={() => onTab(t.id)}
            className="relative flex flex-col items-center gap-[3px] px-3.5 py-1 cursor-pointer bg-transparent border-0"
          >
            <div className="relative">
              {renderIcon(t.icon, tab === t.id)}
              {showDot && (
                <span
                  aria-label={`${unreadCount} unread`}
                  className="absolute -top-0.5 -right-0.5 w-[8px] h-[8px] rounded-full"
                  style={{ background: '#B85C3A', border: '1.5px solid #FBF8F2' }}
                />
              )}
            </div>
            <span
              className="font-sans text-[10px] tracking-[0.1px]"
              style={{
                color: tab === t.id ? '#1C1B17' : '#8B8676',
                fontWeight: tab === t.id ? 500 : 400,
              }}
            >
              {t.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}

export type { TabId };
