// lib/metadata.ts — reusable metadata generator for all pages
import type { Metadata } from "next";

const BASE_URL   = "https://varextech.in";
const SITE_NAME  = "VAREX Technologies";
const OG_DEFAULT = `${BASE_URL}/og-default.png`;

export interface PageMetaInput {
  title:        string;
  description:  string;
  path:         string;
  ogImage?:     string;
  noIndex?:     boolean;
}

export function buildMetadata({
  title,
  description,
  path,
  ogImage,
  noIndex = false,
}: PageMetaInput): Metadata {
  const url      = `${BASE_URL}${path}`;
  const imageUrl = ogImage ?? OG_DEFAULT;

  return {
    title:       `${title} | ${SITE_NAME}`,
    description,
    metadataBase: new URL(BASE_URL),
    alternates:  { canonical: url },
    robots:      noIndex ? { index: false, follow: false } : { index: true, follow: true },
    openGraph: {
      title,
      description,
      url,
      siteName:  SITE_NAME,
      locale:    "en_IN",
      type:      "website",
      images: [{
        url:    imageUrl,
        width:  1200,
        height: 630,
        alt:    title,
      }],
    },
    twitter: {
      card:        "summary_large_image",
      title,
      description,
      images:     [imageUrl],
      site:       "@varextech",
    },
  };
}

// ── Pre-built metadata for every page ────────────────────────────
export const PAGE_META = {
  home: buildMetadata({
    title:       "DevSecOps, Cybersecurity & SAP SD Consulting",
    description: "VAREX builds high-performance engineering teams and delivers DevSecOps, Security, SAP SD, and AI Hiring solutions for Indian enterprises.",
    path:        "/",
    ogImage:     `${BASE_URL}/og-home.png`,
  }),
  blog: buildMetadata({
    title:       "Blog — DevOps, Security & Architecture",
    description: "Expert articles on DevSecOps, Kubernetes, Cybersecurity, SAP SD, and Cloud Architecture from the VAREX team.",
    path:        "/blog",
  }),
  portfolio: buildMetadata({
    title:       "Portfolio — Case Studies",
    description: "Real-world engineering case studies across DevSecOps, Cloud Architecture, SAP SD, and AI Hiring.",
    path:        "/portfolio",
  }),
  workshops: buildMetadata({
    title:       "Workshops & Training",
    description: "Hands-on workshops on DevSecOps, Kubernetes, Cloud Architecture, and SAP SD. Online and offline.",
    path:        "/workshops",
  }),
  learnings: buildMetadata({
    title:       "Premium Learning Paths",
    description: "Architecture deep dives, AI interview modules, and execution playbooks for senior engineers.",
    path:        "/learnings",
    noIndex:     true,
  }),
  pricing: buildMetadata({
    title:       "Pricing — Plans & Subscriptions",
    description: "Free, Premium, and Enterprise plans for VAREX learning content and consulting services.",
    path:        "/pricing",
  }),
  team: buildMetadata({
    title:       "Our Team",
    description: "Meet the VAREX engineers — certified DevSecOps, SAP SD, and Cybersecurity specialists.",
    path:        "/team",
  }),
  contact: buildMetadata({
    title:       "Contact — Book a Free Consultation",
    description: "Talk to a VAREX architect. Book a free 30-minute consultation for DevSecOps, SAP SD, or hiring advisory.",
    path:        "/contact",
  }),
  hire: buildMetadata({
    title:       "Hire in 7 Days — AI-Powered Talent",
    description: "Hire pre-vetted DevSecOps, SAP SD, and Cybersecurity engineers in 7 days using VAREX AI hiring system.",
    path:        "/hire",
  }),
  privacy: buildMetadata({
    title:       "Privacy Policy",
    description: "VAREX Technologies privacy policy — how we collect, use, and protect your data.",
    path:        "/privacy",
    noIndex:     true,
  }),
  terms: buildMetadata({
    title:       "Terms of Service",
    description: "VAREX Technologies terms of service.",
    path:        "/terms",
    noIndex:     true,
  }),
  refund: buildMetadata({
    title:       "Refund Policy",
    description: "VAREX Technologies refund policy for subscriptions and workshops.",
    path:        "/refund",
    noIndex:     true,
  }),
};
