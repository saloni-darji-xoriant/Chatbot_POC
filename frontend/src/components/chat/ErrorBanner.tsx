export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md bg-danger-soft px-[15px] py-[11px]">
      <span className="font-body text-md text-danger">{message}</span>
      <div className="flex shrink-0 gap-3">
        {onRetry && (
          <button type="button" onClick={onRetry} className="font-body text-sm font-semibold text-danger underline">
            Try again
          </button>
        )}
        <a href="/help" className="font-body text-sm font-semibold text-danger underline">
          Open Help Center
        </a>
      </div>
    </div>
  );
}
