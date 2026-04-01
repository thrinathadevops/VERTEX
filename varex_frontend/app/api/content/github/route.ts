import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import matter from "gray-matter";
import { marked } from "marked";

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// AWS Interview Content API Route
//
// Strategy: LOCAL FILESYSTEM FIRST → GitHub API FALLBACK
//
// 1. Locally (dev/Docker): reads directly from the aws-interview-prep
//    folder on disk. ZERO API calls. No rate limits.
// 2. Production (separate repo): if local folder doesn't exist,
//    falls back to GitHub Contents API with optional GITHUB_TOKEN
//    (5,000 req/hr with token + 5-min cache = unlimited practical use).
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const GITHUB_REPO = process.env.GITHUB_REPO || "varextech/interview-preparation";
const GITHUB_CONTENT_PATH = process.env.GITHUB_CONTENT_PATH || ".";
const GITHUB_BRANCH = process.env.GITHUB_BRANCH || "main";
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

// Local filesystem path (relative to project root)
const LOCAL_CONTENT_DIR = GITHUB_CONTENT_PATH === "."
  ? path.join(process.cwd(), "..", "interview-preparation")
  : path.join(process.cwd(), "..", GITHUB_CONTENT_PATH);

const contentSuffix = GITHUB_CONTENT_PATH === "." ? "" : `/${GITHUB_CONTENT_PATH}`;
const GITHUB_API_BASE = `https://api.github.com/repos/${GITHUB_REPO}/contents${contentSuffix}`;
const RAW_BASE = `https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}${contentSuffix}`;

// ── In-memory cache (10 min TTL) ───────────────────────────────
interface CacheEntry {
  data: any[];
  timestamp: number;
}

let cache: CacheEntry | null = null;
const CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes

function getCachedData(): any[] | null {
  if (cache && Date.now() - cache.timestamp < CACHE_TTL_MS) {
    return cache.data;
  }
  return null;
}

function setCachedData(data: any[]) {
  cache = { data, timestamp: Date.now() };
}

// ── Title helper ────────────────────────────────────────────────
function titleFromFilename(filename: string): string {
  return filename
    .replace(/\.md$/, "")
    .replace(/^\d+_/, "")
    .replace(/^aws_interview_/i, "")
    .replace(/^aws_/i, "AWS ")
    .replace(/_quick_referance$/i, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// OPTION 1: Read from LOCAL FILESYSTEM (zero API calls)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async function readFromLocalFilesystem(): Promise<any[] | null> {
  if (!fs.existsSync(LOCAL_CONTENT_DIR)) {
    console.log(`Local folder not found at ${LOCAL_CONTENT_DIR}, falling back to GitHub API`);
    return null;
  }

  const files = fs.readdirSync(LOCAL_CONTENT_DIR).filter((f) => f.endsWith(".md"));
  const allPosts: any[] = [];

  for (const filename of files) {
    try {
      const rawContent = fs.readFileSync(path.join(LOCAL_CONTENT_DIR, filename), "utf-8");
      const { data, content } = matter(rawContent);

      allPosts.push({
        id: `github-aws-${filename}`,
        title: data.title || titleFromFilename(filename),
        slug: filename.replace(/\.md$/, ""),
        body: await marked.parse(content),
        category: data.category || "aws_interview",
        access_level: data.access_level || "free",
        is_published: true,
        author_id: data.author || "system",
        created_at: data.date || new Date().toISOString(),
        source: "local_filesystem",
        github_url: `https://github.com/${GITHUB_REPO}/blob/${GITHUB_BRANCH}/${GITHUB_CONTENT_PATH}/${filename}`,
      });
    } catch (err) {
      console.warn(`Failed to parse local file ${filename}:`, err);
    }
  }

  return allPosts;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// OPTION 2: Fetch from GITHUB API (fallback for production)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

async function readFromGitHubAPI(): Promise<any[]> {
  // List files
  const res = await fetch(GITHUB_API_BASE, { headers: githubHeaders() });
  if (!res.ok) {
    throw new Error(`GitHub API returned ${res.status}`);
  }

  const items: Array<{ name: string; type: string }> = await res.json();
  const mdFiles = items.filter((i) => i.type === "file" && i.name.endsWith(".md"));

  // Fetch and parse in batches of 10
  const BATCH_SIZE = 10;
  const allPosts: any[] = [];

  for (let i = 0; i < mdFiles.length; i += BATCH_SIZE) {
    const batch = mdFiles.slice(i, i + BATCH_SIZE);
    const results = await Promise.allSettled(
      batch.map(async ({ name: filename }) => {
        const url = `${RAW_BASE}/${encodeURIComponent(filename)}`;
        const rawRes = await fetch(url, {
          headers: { "User-Agent": "VAREX-Blog-Fetcher", ...(GITHUB_TOKEN ? { Authorization: `Bearer ${GITHUB_TOKEN}` } : {}) },
        });
        if (!rawRes.ok) throw new Error(`Failed to fetch ${filename}`);
        const raw = await rawRes.text();
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
          source: "github_api",
          github_url: `https://github.com/${GITHUB_REPO}/blob/${GITHUB_BRANCH}/${GITHUB_CONTENT_PATH}/${filename}`,
        };
      })
    );

    for (const r of results) {
      if (r.status === "fulfilled") allPosts.push(r.value);
      else console.warn("GitHub fetch failed:", r.reason);
    }
  }

  return allPosts;
}

// ── Main GET handler ────────────────────────────────────────────
export async function GET() {
  try {
    // 1. Check cache
    const cached = getCachedData();
    if (cached) {
      return NextResponse.json(cached, {
        status: 200,
        headers: { "X-Cache": "HIT", "X-Source": "cache" },
      });
    }

    // 2. Try local filesystem first (ZERO API calls)
    let posts = await readFromLocalFilesystem();
    let source = "local_filesystem";

    // 3. Fallback to GitHub API only if local folder missing
    if (!posts) {
      posts = await readFromGitHubAPI();
      source = "github_api";
    }

    // 4. Sort by date descending
    posts.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    // 5. Cache and return
    setCachedData(posts);

    return NextResponse.json(posts, {
      status: 200,
      headers: { "X-Cache": "MISS", "X-Source": source, "X-Count": String(posts.length) },
    });
  } catch (error) {
    console.error("Content Fetch Error:", error);
    return NextResponse.json(
      { error: "Failed to fetch content" },
      { status: 500 }
    );
  }
}
