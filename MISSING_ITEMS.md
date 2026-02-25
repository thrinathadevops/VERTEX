# VAREX Platform — Full Codebase Audit & Gap Register (Active Issues Only)
> **Reviewed:** 2026-02-25 | **Author:** Antigravity code review
> **Scope:** Every Python + TypeScript file in `varex_backend/` and `varex_frontend/`
> **Note:** All previously marked `[✅ FIXED]` items have been removed from this list to give a clean overview of remaining tasks.

---

## 2. Logic Bugs — Wrong behaviour at runtime
- **2.5** [❌ STILL OPEN] `pricing/page.tsx` — Calls backend endpoint directly from frontend, potentially leaving Razorpay integrations incomplete.
- **2.7** [⚠️ PARTIALLY FIXED] `auth.ts` — `jwtDecode` dependency added and package syntax fixed, but frontend `auth.ts` might still not correctly process the `jti` logic fully if backend is missing it.
- **2.11 - 2.15** [❌ STILL OPEN] All other logic bugs from the original audit remain.

## 3. Model / Schema Mismatches
- **3.1 - 3.19** [❌ STILL OPEN] Manual schema validations (e.g. `UserResponse` missing `updated_at`, `SubscriptionResponse` missing `razorpay_payment_id`) are likely still open within Pydantic models. Need to match all Pydantic schemas in `app/schemas/` to explicitly mirror their `app/models/` SQLAlchemy definitions.

## 4. Connectivity Gaps — API to Frontend
- **4.1** [❌ STILL BROKEN] `razorpay.ts` calls `/api/razorpay/create-order` — Next.js route DOES NOT EXIST. The `varex_frontend/app/api/` folder is missing the `razorpay` implementation.
- **4.2** [❌ STILL BROKEN] `s3.ts` calls `/api/s3/presign` — Next.js route DOES NOT EXIST.
- **4.3** [❌ STILL BROKEN] `email.ts` — Exposes `SENDGRID_API_KEY` to the client side. This needs to be moved to a Next.js server-side backend API route.
- **4.4** [❌ STILL OPEN] Backend `app/api/email/`, `app/api/s3/`, `app/api/webhook/`, `app/api/razorpay/` directories exist but are completely empty. They require FastAPI router implementations.
- **4.6 - 4.9** [❌ STILL OPEN] Missing corresponding endpoints referenced inside frontend `api.ts`.

## 5. Security Gaps
- **5.1 - 5.10** [❌ ALL STILL OPEN] JWT missing `jti` for explicit token invalidation on logout.
- **5.x** Cookies lacking `httpOnly` secure flags. 
- **5.x** Timing attacks pending on auth routes.
- **5.x** CORS whitelist is incomplete or too permissive (e.g., allow `*`).

## 6. Missing Features & Stubs
- **6.1 - 6.13** [❌ ALL STILL OPEN] No actual LLM implementations applied (they are just stubs).
- **6.x** No explicit logout endpoint logic implemented effectively.
- **6.x** Password reset functionality completely missing.
- **6.x** Missing pagination on major collection endpoints (list queries return unbounded datasets).

## 7. Database / Migration Issues
- **7.4, 7.5** [❌ STILL OPEN] Missing specific database indexes. Foreign keys generally don't automatically create indexes in PostgreSQL. Heavy read querying foreign keys without indexes will cause slowness.

## 8. Infrastructure & Docker Gaps
- **8.3 - 8.8** [❌ STILL OPEN] Backend Dockerfile optimizations (multi-stage builds, non-root user).
- **8.x** Certbot SSL implementation missing.
- **8.x** Redis caching layer needs to be fully utilized inside the backend codebase (e.g., blacklisting tokens).
- **8.x** `.dockerignore` creation still missing for node_modules, venv, etc.

## 9. CI/CD Gaps
- **9.1** [❌ STILL OPEN] Github workflows still utilize hyphens where underscores are needed.
- **9.2** [❌ STILL OPEN] No `tests/` directory inside `varex_backend/`. Pytest execution will fail.
- **9.5, 9.6** [❌ STILL OPEN] Frontend tests in CI. Latest Docker tags implementation.

## 10. Best Practice Violations
- **10.4 - 10.11** [❌ STILL OPEN] Missing structured logging, hardcoded strings scattered around, unhandled error cases.

## 12. Frontend Specific Issues
- **12.1 - 12.10** [❌ STILL OPEN] Missing standard static pages (Terms of Service, Privacy Policy).
- **12.x** Missing `Forgot password?` workflow pages.
- **12.x** Role caching still relies on UI-editable tokens/cookies which causes client-side security risks.
- **12.x** `next.config.js` missing or unoptimized.

---

### Immediate Next Steps (Your Call To Action)
1. **Frontend Secure Routes**: Resolve **[4.3]** by building the `app/api/email/route.ts` API route in the frontend to hide `SENDGRID_API_KEY`. Apply the same logic for Razorpay and S3 endpoints **[4.1]** **[4.2]**.
2. **Backend Services**: Implement the logic for the empty directories in `varex_backend/app/api/` (Razorpay, S3, Email).
3. **Pydantic Schemas**: Verify and update schemas in `app/schemas/` to strictly align with their SQLAlchemy equivalents.
4. **Security Fixes**: Enhance JWT handling to include `jti` and set `httpOnly` cookies for sessions.
