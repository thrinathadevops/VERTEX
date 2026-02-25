import Link from "next/link";
import type { ContentItem } from "@/lib/types";

export default function ContentCard({ item, blurred }: { item: ContentItem; blurred?: boolean }) {
  return (
    <Link href={`/blog/${(item as any).slug ?? item.id}`}>
      <article className="group rounded-2xl border border-slate-800 bg-slate-900/70 p-4 hover:border-sky-600/70 cursor-pointer">
        <h3 className="mb-1 text-sm font-semibold text-slate-100 line-clamp-2">
          {item.title}
        </h3>
        <p
          className={`text-xs text-slate-300 transition ${
            blurred ? "line-clamp-2 blur-sm group-hover:blur-none" : "line-clamp-3"
          }`}
        >
          {item.body}
        </p>
        {blurred && (
          <div className="mt-3 rounded-md border border-dashed border-sky-500/60 bg-sky-950/40 px-3 py-2 text-[11px] text-sky-100">
            Premium insight. Sign in with a premium account to see the full article.
          </div>
        )}
        {!blurred && (
          <p className="mt-3 text-[11px] text-sky-400 group-hover:text-sky-300">
            Read more →
          </p>
        )}
      </article>
    </Link>
  );
}