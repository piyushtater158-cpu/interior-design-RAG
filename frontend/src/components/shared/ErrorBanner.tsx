import { Anno } from '@/components/atelier/Anno';

export function ErrorBanner({ message, onDismiss }: { message: string; onDismiss?: () => void }) {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-xl px-4 py-3"
      style={{
        background: 'rgba(184,92,58,0.08)',
        border: '1px solid rgba(184,92,58,0.35)',
      }}
    >
      <div className="flex-1 min-w-0">
        <Anno color="#B85C3A" className="block mb-1">error</Anno>
        <div className="text-sm text-ink-soft">{message}</div>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          aria-label="Dismiss"
          className="w-6 h-6 rounded-full flex items-center justify-center text-mute hover:text-ink bg-transparent border-0 cursor-pointer shrink-0"
        >
          <svg width="10" height="10" viewBox="0 0 10 10">
            <path d="M1 1 L9 9 M9 1 L1 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      )}
    </div>
  );
}
