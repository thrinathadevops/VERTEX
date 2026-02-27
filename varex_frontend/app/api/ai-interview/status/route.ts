import { NextResponse } from "next/server";

function resolveCandidateUrls(): string[] {
  const raw = [
    process.env.AI_INTERVIEW_APP_URL,
    process.env.NEXT_PUBLIC_AI_INTERVIEW_APP_URL,
    "http://localhost:3010",
  ].filter(Boolean) as string[];

  return [...new Set(raw.map((url) => url.trim().replace(/\/+$/, "")))];
}

async function checkHealth(baseUrl: string): Promise<boolean> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 3000);
  try {
    const res = await fetch(`${baseUrl}/health`, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
    });
    return res.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function GET() {
  const urls = resolveCandidateUrls();

  for (const url of urls) {
    const healthy = await checkHealth(url);
    if (healthy) {
      return NextResponse.json({ ok: true, launchUrl: url });
    }
  }

  return NextResponse.json(
    {
      ok: false,
      message: "AI Interview application is currently unavailable. Please try again shortly.",
    },
    { status: 503 }
  );
}
