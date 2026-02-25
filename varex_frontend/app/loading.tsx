// PATH: varex-frontend/app/loading.tsx
// Global loading skeleton — shown by Next.js during page transitions

export default function Loading() {
  return (
    <div className="space-y-6 animate-pulse max-w-5xl mx-auto">
      {/* Page header skeleton */}
      <div className="space-y-2">
        <div className="h-7 w-48 rounded-lg bg-slate-800" />
        <div className="h-4 w-72 rounded-md bg-slate-800/70" />
      </div>

      {/* Cards skeleton */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
            <div className="h-4 w-3/4 rounded-md bg-slate-800" />
            <div className="h-3 w-full rounded-md bg-slate-800/70" />
            <div className="h-3 w-5/6 rounded-md bg-slate-800/70" />
            <div className="h-3 w-2/3 rounded-md bg-slate-800/70" />
          </div>
        ))}
      </div>
    </div>
  );
}
