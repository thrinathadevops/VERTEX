// PATH: app/not-found.tsx
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-5 px-4">
      <p className="text-7xl font-black text-slate-700 leading-none">404</p>
      <div className="space-y-1">
        <h1 className="text-xl font-bold text-slate-100">Page not found</h1>
        <p className="text-sm text-slate-400 max-w-xs">
          The page you are looking for does not exist or has been moved.
        </p>
      </div>
      <div className="flex flex-wrap gap-3 justify-center pt-2">
        <Link href="/"
          className="rounded-lg bg-sky-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-sky-400 transition">
          Go home
        </Link>
        <Link href="/blog"
          className="rounded-lg border border-slate-700 px-5 py-2.5 text-sm text-slate-200 hover:border-sky-500/60 transition">
          Read the blog
        </Link>
        <Link href="/contact"
          className="rounded-lg border border-slate-700 px-5 py-2.5 text-sm text-slate-200 hover:border-sky-500/60 transition">
          Contact us
        </Link>
      </div>
      <p className="text-xs text-slate-500">
        Error code: 404 · varextech.in
      </p>
    </div>
  );
}
