export function MobStatusBar({ dark = false }: { dark?: boolean }) {
  const fg = dark ? '#F4EFE6' : '#1C1B17';
  return (
    <div className="flex items-center justify-between px-6 pt-3 pb-1 h-[44px] shrink-0 text-xs font-medium" style={{ color: fg }}>
      <span className="font-sans">9:41</span>
      <div className="flex items-center gap-1.5">
        <svg width="16" height="10" viewBox="0 0 16 10" fill="none">
          <path d="M1 7 a1 1 0 0 1 1-1 h1 v3 h-1 a1 1 0 0 1-1-1 z M5 5 a1 1 0 0 1 1-1 h1 v5 h-1 a1 1 0 0 1-1-1 z M9 3 a1 1 0 0 1 1-1 h1 v7 h-1 a1 1 0 0 1-1-1 z M13 1 a1 1 0 0 1 1-1 h1 v9 h-1 a1 1 0 0 1-1-1 z" fill={fg} />
        </svg>
        <svg width="14" height="10" viewBox="0 0 14 10" fill="none">
          <path d="M7 2 C4 2 2 3 0 5 L7 10 L14 5 C12 3 10 2 7 2 z" fill={fg} opacity="0.9" />
        </svg>
        <svg width="22" height="10" viewBox="0 0 22 10" fill="none">
          <rect x="0.5" y="0.5" width="18" height="9" rx="2" stroke={fg} opacity="0.4" />
          <rect x="2" y="2" width="15" height="6" rx="1" fill={fg} />
          <rect x="19" y="3" width="1.5" height="4" rx="0.5" fill={fg} opacity="0.4" />
        </svg>
      </div>
    </div>
  );
}
