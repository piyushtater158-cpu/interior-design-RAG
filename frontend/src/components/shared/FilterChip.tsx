'use client';

type Props = {
  label: string;
  active: boolean;
  onClick: () => void;
  count?: number;
};

export function FilterChip({ label, active, onClick, count }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="font-sans text-[12px] tracking-[0.1px] rounded-full flex items-center gap-1.5 cursor-pointer transition-colors whitespace-nowrap"
      style={{
        padding: '6px 12px',
        background: active ? '#1C1B17' : '#FFFFFF',
        color: active ? '#FBF8F2' : '#1C1B17',
        border: `1px solid ${active ? '#1C1B17' : '#D8D0BE'}`,
        fontWeight: active ? 500 : 400,
      }}
    >
      {label}
      {typeof count === 'number' && (
        <span
          className="font-mono text-[10px]"
          style={{ color: active ? 'rgba(251,248,242,0.7)' : '#8B8676' }}
        >
          {count}
        </span>
      )}
    </button>
  );
}
