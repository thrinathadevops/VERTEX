"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getContentBySlug } from "@/lib/api";

import type { ContentItem } from "@/lib/types";

export default function BlogPostPage() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const [post, setPost] = useState<ContentItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const bodyRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!slug) return;
    getContentBySlug(slug)
      .then(setPost)
      .catch((err) => {
        const status = err?.response?.status;
        if (status === 403) {
          setError("premium");
        } else if (status === 404) {
          setError("notfound");
        } else {
          setError("unknown");
        }
      })
      .finally(() => setLoading(false));
  }, [slug]);

  // ── Mermaid diagram rendering ────────────────────────────────
  useEffect(() => {
    if (!post || !bodyRef.current) return;

    /**
     * Sanitize raw Mermaid graph definitions from the markdown files.
     * Many GitHub posts use emojis, <br/>, and parentheses inside node
     * labels without quoting them, which causes Mermaid parse errors.
     */
    function sanitizeMermaid(raw: string): string {
      const lines = raw.split("\n");
      const result: string[] = [];

      for (const line of lines) {
        let out = line;

        // Skip style/classDef/click lines — they don't have node labels
        const trimmed = out.trim();
        if (
          trimmed.startsWith("style ") ||
          trimmed.startsWith("classDef ") ||
          trimmed.startsWith("click ") ||
          trimmed.startsWith("%%") ||
          trimmed === ""
        ) {
          result.push(out);
          continue;
        }

        // Fix square bracket labels: ID[...content...] → ID["...content..."]
        // Only if content has special chars and isn't already quoted
        out = out.replace(
          /(\w+)\[([^\]"]+)\]/g,
          (_match, id, content) => {
            // Check if the content needs quoting (has emojis, <br/>, parens, etc)
            const needsQuoting =
              /[^\x20-\x7E]/.test(content) || // non-ASCII (emojis)
              /<br\s*\/?>/.test(content) ||     // HTML br tags
              /[(){}]/.test(content);            // parentheses/braces
            if (needsQuoting) {
              const cleaned = content
                .replace(/<br\s*\/?>/gi, "<br/>") // normalize br tags
                .replace(/[^\x20-\x7E<>/\-:.'&,;!?@#$%^*+=~`|\\]/g, "") // strip emojis
                .trim();
              return `${id}["${cleaned}"]`;
            }
            return `${id}[${content}]`;
          }
        );

        // Fix double-paren labels (circle nodes): ID((content)) → ID(("content"))
        out = out.replace(
          /(\w+)\(\(([^)"]+)\)\)/g,
          (_match, id, content) => {
            const hasSpecial = /[^\x20-\x7E]/.test(content);
            if (hasSpecial) {
              const cleaned = content.replace(/[^\x20-\x7E]/g, "").trim();
              return `${id}(("${cleaned}"))`;
            }
            return `${id}(("${content}"))`;
          }
        );

        // Fix cylinder labels: ID[(content)] → ID[("content")]
        out = out.replace(
          /(\w+)\[\(([^)"]+)\)\]/g,
          (_match, id, content) => {
            const cleaned = content.replace(/[^\x20-\x7E]/g, "").trim();
            return `${id}[("${cleaned}")]`;
          }
        );

        // Fix round-paren labels (stadium): ID([content]) → ID(["content"])
        out = out.replace(
          /(\w+)\(\[([^\]"]+)\]\)/g,
          (_match, id, content) => {
            const cleaned = content.replace(/[^\x20-\x7E]/g, "").trim();
            return `${id}(["${cleaned}"])`;
          }
        );

        // Fix diamond/rhombus labels: ID{content} → ID{"content"}
        out = out.replace(
          /(\w+)\{([^}"]+)\}/g,
          (_match, id, content) => {
            const hasSpecial =
              /[^\x20-\x7E]/.test(content) || /<br\s*\/?>/.test(content);
            if (hasSpecial) {
              const cleaned = content
                .replace(/<br\s*\/?>/gi, "<br/>")
                .replace(/[^\x20-\x7E<>/\-:.'&,;!?@#$%^*+=~`|\\]/g, "")
                .trim();
              return `${id}{"${cleaned}"}`;
            }
            return _match;
          }
        );

        // Fix subgraph names with parentheses: subgraph "Name (stuff)"
        // Mermaid chokes on parens inside quoted subgraph names sometimes
        out = out.replace(
          /^(\s*subgraph\s+)"([^"]+)"/,
          (_match, prefix, name) => {
            const cleaned = name.replace(/\(/g, "- ").replace(/\)/g, "");
            return `${prefix}"${cleaned}"`;
          }
        );

        // Fix edge labels with special characters in pipe syntax: |label|
        out = out.replace(
          /\|([^|"]+)\|/g,
          (_match, content) => {
            const hasSpecial = /[^\x20-\x7E]/.test(content);
            if (hasSpecial) {
              const cleaned = content.replace(/[^\x20-\x7E]/g, "").trim();
              return `|"${cleaned}"|`;
            }
            return `|"${content}"|`;
          }
        );

        result.push(out);
      }

      return result.join("\n");
    }

    const renderMermaid = async () => {
      const mermaid = (await import("mermaid")).default;
      mermaid.initialize({
        startOnLoad: false,
        theme: "dark",
        themeVariables: {
          darkMode: true,
          background: "#0f172a",
          primaryColor: "#38bdf8",
          primaryTextColor: "#f1f5f9",
          primaryBorderColor: "#475569",
          lineColor: "#64748b",
          secondaryColor: "#1e293b",
          tertiaryColor: "#1e293b",
        },
        flowchart: { curve: "basis", htmlLabels: true },
        securityLevel: "loose",
      });

      const el = bodyRef.current;
      if (!el) return;

      // Find all mermaid code blocks (marked wraps them in <pre><code class="language-mermaid">)
      const codeBlocks = el.querySelectorAll("code.language-mermaid");

      for (let i = 0; i < codeBlocks.length; i++) {
        const codeEl = codeBlocks[i] as HTMLElement;
        const rawDef = codeEl.textContent || "";
        const preEl = codeEl.parentElement; // the <pre> wrapper

        if (!preEl || !rawDef.trim()) continue;

        try {
          // Sanitize the Mermaid syntax before rendering
          const graphDef = sanitizeMermaid(rawDef.trim());
          const id = `mermaid-diagram-${i}-${Date.now()}`;
          const { svg } = await mermaid.render(id, graphDef);

          // Create a styled wrapper and replace the <pre> block
          const wrapper = document.createElement("div");
          wrapper.className = "mermaid-wrapper my-6 flex justify-center overflow-x-auto rounded-lg border border-slate-700 bg-slate-900/60 p-4";
          wrapper.innerHTML = svg;
          preEl.replaceWith(wrapper);
        } catch (err) {
          console.warn("Mermaid render failed for block", i, err);
          // Keep the raw code block visible as fallback
        }
      }
    };

    // Small delay to ensure the DOM has been painted
    const timer = setTimeout(renderMermaid, 100);
    return () => clearTimeout(timer);
  }, [post]);

  if (loading) return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <div className="h-6 w-6 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
    </div>
  );

  // ── 404 ───────────────────────────────────────────────────────
  if (error === "notfound") return (
    <div className="max-w-xl mx-auto text-center py-20 space-y-3">
      <p className="text-4xl">📄</p>
      <h1 className="text-xl font-semibold">Post not found</h1>
      <p className="text-sm text-slate-400">This article may have been moved or deleted.</p>
      <Link href="/blog" className="inline-block text-xs text-sky-400 hover:text-sky-300 mt-2">
        ← Back to Blog
      </Link>
    </div>
  );

  // ── Premium gate ──────────────────────────────────────────────
  if (error === "premium") return (
    <div className="max-w-xl mx-auto text-center py-20 space-y-4">
      <p className="text-4xl">🔒</p>
      <h1 className="text-xl font-semibold">Premium content</h1>
      <p className="text-sm text-slate-300">
        This article is available to Premium and Enterprise subscribers.
      </p>
      <div className="flex items-center justify-center gap-3 mt-2">
        <Link href="/pricing"
          className="rounded-md bg-sky-500 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-400">
          Upgrade plan
        </Link>
        <Link href="/blog" className="text-xs text-slate-400 hover:text-slate-200">
          ← Back to Blog
        </Link>
      </div>
    </div>
  );

  if (!post) return null;

  const readingMins = Math.ceil((post.body?.split(" ").length ?? 0) / 200);
  const categoryColors: Record<string, string> = {
    devops: "bg-sky-500/20 text-sky-300",
    security: "bg-red-500/20 text-red-300",
    sap: "bg-amber-500/20 text-amber-300",
    architecture: "bg-purple-500/20 text-purple-300",
    aws_interview: "bg-teal-500/20 text-teal-300",
    ai_hiring: "bg-emerald-500/20 text-emerald-300",
    azure_interview: "bg-blue-500/20 text-blue-300",
    linux_interview: "bg-emerald-500/20 text-emerald-300",
    kubernetes_interview: "bg-indigo-500/20 text-indigo-300",
  };
  const category = (post as any).category ?? "devops";

  return (
    <article className="max-w-5xl mx-auto space-y-6">
      {/* ── Breadcrumb ──────────────────────────────────────────── */}
      <nav className="flex items-center gap-1 text-[11px] text-slate-400">
        <Link href="/blog" className="hover:text-sky-300">Blog</Link>
        <span>/</span>
        <Link href={`/blog/${category}`} className="hover:text-sky-300 capitalize">{category}</Link>
        <span>/</span>
        <span className="text-slate-300 truncate max-w-[160px]">{post.title}</span>
      </nav>

      {/* ── Header ──────────────────────────────────────────────── */}
      <header className="space-y-3">
        <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${categoryColors[category] ?? "bg-slate-700 text-slate-300"}`}>
          {category}
        </span>
        <h1 className="text-2xl font-bold leading-snug">{post.title}</h1>
        <div className="flex items-center gap-4 text-[11px] text-slate-400">
          <span>📅 {new Date(post.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}</span>
          <span>⏱ {readingMins} min read</span>
          {post.access_level === "premium" && (
            <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-amber-300">Premium</span>
          )}
        </div>
      </header>

      {/* ── Divider ─────────────────────────────────────────────── */}
      <hr className="border-slate-800" />

      {/* ── Body ────────────────────────────────────────────────── */}
      <section
        ref={bodyRef}
        className="prose prose-invert prose-sm max-w-none
          prose-headings:font-semibold prose-headings:text-slate-100
          prose-p:text-slate-300 prose-p:leading-relaxed
          prose-a:text-sky-400 prose-a:no-underline hover:prose-a:underline
          prose-code:bg-slate-800 prose-code:px-1 prose-code:rounded
          prose-pre:bg-slate-900 prose-pre:border prose-pre:border-slate-700
          prose-blockquote:border-sky-500 prose-blockquote:text-slate-300
          prose-li:text-slate-300"
        dangerouslySetInnerHTML={{ __html: post.body }}
      />

      {/* ── Footer actions ──────────────────────────────────────── */}
      <div className="border-t border-slate-800 pt-5 flex items-center justify-between">
        <Link href="/blog"
          className="text-xs text-slate-400 hover:text-sky-300 flex items-center gap-1">
          ← Back to Blog
        </Link>
        <div className="flex items-center gap-3 text-xs">
          <Link href="/contact" className="text-slate-400 hover:text-sky-300">
            Get free consultation →
          </Link>
        </div>
      </div>
    </article>
  );
}
