'use client';

type Props = {
  active: boolean;
  onToggle: () => void;
  size?: number;
  label?: string;
};

export function HeartBtn({ active, onToggle, size = 34, label = 'Favourite' }: Props) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={active}
      onClick={(e) => {
        e.stopPropagation();
        onToggle();
      }}
      className="flex items-center justify-center cursor-pointer p-0 transition-transform hover:scale-105"
      style={{
        width: size,
        height: size,
        borderRadius: '999px',
        background: 'rgba(251,248,242,0.94)',
        border: '1px solid #D8D0BE',
        boxShadow: '0 2px 6px rgba(28,27,23,0.08)',
      }}
    >
      <svg width={Math.round(size * 0.5)} height={Math.round(size * 0.5)} viewBox="0 0 20 20">
        <path
          d="M10 17 C 5 13.5 2 11 2 7.5 C 2 5 4 3.5 6 3.5 C 7.5 3.5 9 4.5 10 6 C 11 4.5 12.5 3.5 14 3.5 C 16 3.5 18 5 18 7.5 C 18 11 15 13.5 10 17 Z"
          fill={active ? '#B85C3A' : 'none'}
          stroke={active ? '#B85C3A' : '#1C1B17'}
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
      </svg>
    </button>
  );
}
