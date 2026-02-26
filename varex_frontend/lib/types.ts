// PATH: varex_frontend/lib/types.ts
// FIX: UserRole — "premium_user" -> "premium", added "enterprise" (Bug 3.13)
// FIX: ContentItem now includes slug and category (Bug 3.15)
// FIX: SubscriptionResponse includes razorpay_payment_id, price_paid (Bug 3.14)

export type UserRole = "guest" | "free_user" | "premium" | "enterprise" | "admin";
//                                              ^^^^^^^^^ was "premium_user" — FIXED

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  avatar_url?: string;
  company?: string;
  created_at: string;
  updated_at?: string;
}

export interface Subscription {
  id: string;
  user_id: string;
  plan_type: "monthly" | "quarterly" | "enterprise";
  status: "pending" | "active" | "expired" | "cancelled";
  start_date?: string;
  expiry_date?: string;
  razorpay_order_id?: string;
  razorpay_payment_id?: string;   // ADDED (Bug 3.14)
  price_paid?: number;   // ADDED (Bug 3.14)
  created_at: string;
}

export interface ContentItem {
  id: string;
  title: string;
  slug: string;            // ADDED (Bug 3.15)
  body: string;
  category: string;            // ADDED (Bug 3.15)
  access_level: "free" | "premium";
  is_published: boolean;
  author_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface Lead {
  id: string;
  name: string;
  email: string;
  company?: string;
  phone?: string;
  service_interest: string;
  message?: string;
  status: "new" | "contacted" | "qualified" | "converted" | "rejected";
  created_at: string;
}

export interface Workshop {
  id: string;
  title: string;
  slug: string;
  description?: string;
  mode: "online" | "offline" | "hybrid";
  price: number;
  max_seats: number;
  seats_booked: number;
  status: "upcoming" | "open" | "full" | "completed" | "cancelled";
  scheduled_date?: string;
  duration_hours?: number;
  price_inr?: number;
  curriculum?: string;
  is_published: boolean;
  created_at: string;
}

export interface TeamMember {
  id: string;
  name: string;
  slug: string;
  role: string;
  bio?: string;
  avatar_url?: string;
  linkedin_url?: string;
  github_url?: string;           // ADDED (Bug 3.17)
  specialisations?: string[];
  specializations?: string[];
  enterprise_projects?: string[];         // ADDED (Bug 3.17)
  title?: string;
  years_experience?: number;
  tools?: string[];
  pricing?: Record<string, number>;
  available_for?: string[];
  available_from?: string;
  display_order: number;
  is_published: boolean;
  created_at: string;
}

export interface PortfolioProject {
  id: string;
  title: string;
  slug: string;
  summary?: string;
  body?: string;
  description?: string;
  category?: string;
  tech_stack?: string[];
  outcomes?: string[];
  client_name?: string;
  diagram_s3_key?: string;    // ADDED (Bug 3.16)
  case_study_url?: string;    // ADDED (Bug 3.16)
  github_url?: string;
  is_featured?: boolean;
  is_published: boolean;
  created_at: string;
}

export interface Certification {
  id: string;
  title: string;
  issuer: string;
  issued_to: string;
  issued_date?: string;
  expiry_date?: string;
  credential_url?: string;
  badge_url?: string;
  is_published: boolean;
  created_at: string;
  domain: string;
  issuing_body?: string;
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  metric?: string;
}

export interface FAQ {
  id: string;
  question: string;
  answer: string;
  category?: string;
  display_order: number;
  is_published: boolean;
  created_at: string;
}

export interface Analytics {
  users: {
    total: number;
    new_30d: number;
    premium: number;
    enterprise: number;
  };
  leads: {
    total: number;
    new_30d: number;
    converted: number;
    conversion_rate: number;
  };
  subscriptions: { active: number };
  workshops: { total_registrations: number };
}

export type Project = PortfolioProject;
export type ProjectCategory = string;
