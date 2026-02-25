import { MetadataRoute } from "next";

const BASE_URL = "https://varextech.in";

const STATIC_ROUTES = [
  { url: "/",              priority: 1.0,  changeFrequency: "weekly"  },
  { url: "/blog",          priority: 0.9,  changeFrequency: "daily"   },
  { url: "/portfolio",     priority: 0.9,  changeFrequency: "weekly"  },
  { url: "/workshops",     priority: 0.8,  changeFrequency: "daily"   },
  { url: "/learnings",     priority: 0.8,  changeFrequency: "weekly"  },
  { url: "/team",          priority: 0.7,  changeFrequency: "monthly" },
  { url: "/certifications",priority: 0.6,  changeFrequency: "monthly" },
  { url: "/pricing",       priority: 0.8,  changeFrequency: "monthly" },
  { url: "/services",      priority: 0.8,  changeFrequency: "monthly" },
  { url: "/hire",          priority: 0.8,  changeFrequency: "monthly" },
  { url: "/contact",       priority: 0.7,  changeFrequency: "monthly" },
  { url: "/faq",           priority: 0.6,  changeFrequency: "monthly" },
  { url: "/privacy",       priority: 0.3,  changeFrequency: "yearly"  },
  { url: "/terms",         priority: 0.3,  changeFrequency: "yearly"  },
  { url: "/refund",        priority: 0.3,  changeFrequency: "yearly"  },
] as const;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const now = new Date();

  // Static routes
  const staticEntries: MetadataRoute.Sitemap = STATIC_ROUTES.map((r) => ({
    url:              `${BASE_URL}${r.url}`,
    lastModified:     now,
    changeFrequency:  r.changeFrequency as MetadataRoute.Sitemap[number]["changeFrequency"],
    priority:         r.priority,
  }));

  // Dynamic blog slugs
  let blogEntries: MetadataRoute.Sitemap = [];
  let portfolioEntries: MetadataRoute.Sitemap = [];
  let workshopEntries: MetadataRoute.Sitemap = [];

  try {
    const [contentRes, portfolioRes, workshopRes] = await Promise.all([
      fetch(`${API}/api/v1/content/free`),
      fetch(`${API}/api/v1/portfolio`),
      fetch(`${API}/api/v1/workshops`),
    ]);

    if (contentRes.ok) {
      const content = await contentRes.json() as { slug: string; created_at: string }[];
      blogEntries = content.map((c) => ({
        url:             `${BASE_URL}/blog/${c.slug}`,
        lastModified:    new Date(c.created_at),
        changeFrequency: "weekly" as const,
        priority:        0.7,
      }));
    }

    if (portfolioRes.ok) {
      const projects = await portfolioRes.json() as { slug: string; created_at: string }[];
      portfolioEntries = projects.map((p) => ({
        url:             `${BASE_URL}/portfolio/${p.slug}`,
        lastModified:    new Date(p.created_at),
        changeFrequency: "monthly" as const,
        priority:        0.7,
      }));
    }

    if (workshopRes.ok) {
      const workshops = await workshopRes.json() as { slug: string }[];
      workshopEntries = workshops.map((w) => ({
        url:             `${BASE_URL}/workshops/${w.slug}`,
        lastModified:    now,
        changeFrequency: "weekly" as const,
        priority:        0.7,
      }));
    }
  } catch {
    // silently skip if API is unavailable at build time
  }

  return [...staticEntries, ...blogEntries, ...portfolioEntries, ...workshopEntries];
}
