import { NextResponse } from "next/server";
import matter from "gray-matter";
import { marked } from "marked";

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// GitHub Content API Route
// Fetches markdown blog posts from a GitHub repository.
// Supports both public repos (unauthenticated) and private repos
// (via GITHUB_TOKEN env var).
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const GITHUB_REPO = process.env.GITHUB_REPO || "thrinathadevops/VERTEX";
const GITHUB_CONTENT_PATH = process.env.GITHUB_CONTENT_PATH || "aws-interview-prep";
const GITHUB_BRANCH = process.env.GITHUB_BRANCH || "main";
const GITHUB_TOKEN = process.env.GITHUB_TOKEN; // optional — for private repos

const GITHUB_API_BASE = `https://api.github.com/repos/${GITHUB_REPO}/contents/${GITHUB_CONTENT_PATH}`;
const RAW_BASE = `https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}/${GITHUB_CONTENT_PATH}`;

// ── In-memory cache (5 min TTL) ────────────────────────────────
interface CacheEntry {
  data: any[];
  timestamp: number;
}

let cache: CacheEntry | null = null;
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

function getCachedData(): any[] | null {
  if (cache && Date.now() - cache.timestamp < CACHE_TTL_MS) {
    return cache.data;
  }
  return null;
}

function setCachedData(data: any[]) {
  cache = { data, timestamp: Date.now() };
}

// ── GitHub fetch helpers ────────────────────────────────────────
function githubHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/vnd.github.v3+json",
    "User-Agent": "VAREX-Blog-Fetcher",
  };
  if (GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${GITHUB_TOKEN}`;
  }
  return headers;
}

async function listMarkdownFiles(): Promise<string[]> {
  const res = await fetch(GITHUB_API_BASE, { headers: githubHeaders() });

  if (!res.ok) {
    const errText = await res.text();
    console.error(`GitHub API error (${res.status}):`, errText);
    throw new Error(`GitHub API returned ${res.status}`);
  }

  const items: Array<{ name: string; type: string }> = await res.json();

  return items
    .filter((item) => item.type === "file" && item.name.endsWith(".md"))
    .map((item) => item.name);
}

async function fetchRawMarkdown(filename: string): Promise<string> {
  const url = `${RAW_BASE}/${encodeURIComponent(filename)}`;
  const headers: Record<string, string> = {
    "User-Agent": "VAREX-Blog-Fetcher",
  };
  if (GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${GITHUB_TOKEN}`;
  }

  const res = await fetch(url, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch ${filename}: ${res.status}`);
  }
  return res.text();
}

// ── Derive a human-readable title from the filename ─────────────
function titleFromFilename(filename: string): string {
  return filename
    .replace(/\.md$/, "")
    .replace(/^\d+_/, "")              // strip leading number prefix
    .replace(/^aws_interview_/i, "")   // strip common prefix
    .replace(/^aws_/i, "AWS ")         // restore "AWS" prefix
    .replace(/_quick_referance$/i, "") // strip suffix
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase()); // Title Case
}

// ── Main GET handler ────────────────────────────────────────────
export async function GET() {
  try {
    // 1. Check cache first
    const cached = getCachedData();
    if (cached) {
      return NextResponse.json(cached, {
        status: 200,
        headers: { "X-Cache": "HIT" },
      });
    }

    // 2. List all .md files from GitHub
    const filenames = await listMarkdownFiles();

    // 3. Fetch and parse each file (batch in parallel, max 10 concurrent)
    const BATCH_SIZE = 10;
    const allPosts: any[] = [];

    for (let i = 0; i < filenames.length; i += BATCH_SIZE) {
      const batch = filenames.slice(i, i + BATCH_SIZE);
      const results = await Promise.allSettled(
        batch.map(async (filename) => {
          const raw = await fetchRawMarkdown(filename);
          const { data, content } = matter(raw);

          return {
            id: `github-aws-${filename}`,
            title: data.title || titleFromFilename(filename),
            slug: filename.replace(/\.md$/, ""),
            body: await marked.parse(content),
            category: data.category || "aws_interview",
            access_level: data.access_level || "free",
            is_published: true,
            author_id: data.author || "system",
            created_at: data.date || new Date().toISOString(),
            source: "github",
            github_url: `https://github.com/${GITHUB_REPO}/blob/${GITHUB_BRANCH}/${GITHUB_CONTENT_PATH}/${filename}`,
          };
        })
      );

      for (const result of results) {
        if (result.status === "fulfilled") {
          allPosts.push(result.value);
        } else {
          console.warn("Failed to process a GitHub post:", result.reason);
        }
      }
    }

    // 4. Sort by date descending
    allPosts.sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    // 5. Cache and return
    setCachedData(allPosts);

    return NextResponse.json(allPosts, {
      status: 200,
      headers: { "X-Cache": "MISS" },
    });
  } catch (error) {
    console.error("GitHub Content Fetch Error:", error);
    return NextResponse.json(
      { error: "Failed to fetch content from GitHub" },
      { status: 500 }
    );
  }
}
