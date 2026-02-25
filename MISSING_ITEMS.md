# VAREX Platform — Full Codebase Audit & Gap Register (Active Issues Only)
> **Reviewed:** 2026-02-25 | **Author:** Antigravity code review
> **Scope:** Every Python + TypeScript file in `varex_backend/` and `varex_frontend/`
> **Note:** All previously marked `[✅ FIXED]` items have been removed from this list to give a clean overview of remaining tasks.

---

## 4. Connectivity Gaps — API to Frontend
- **4.x** [❌ STILL OPEN] The frontend UI needs to correctly wire the newly built Next.js `/api/email` (for forms/newsletters), `/api/s3/presign` (for avatars/resumes endpoints in UI components), and `/api/razorpay` (in any stray subscription paths) effectively. 
- **4.x** [❌ STILL OPEN] Backend `app/api/email/`, `app/api/s3/`, `app/api/webhook/`, `app/api/razorpay/` directories exist but are completely empty in the FastAPI backend. However, those responsibilities have now partially transitioned to the Next.js routes. They should probably be deleted from the FastAPI project to prevent confusion.

## 6. Missing Features & Stubs
- **6.1 - 6.13** [❌ ALL STILL OPEN] No actual LLM implementations applied (they are just stubs). E.g. `ats_service.py` returning hardcoded results, interview AI returning hardcoded results.

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
- **12.x** `next.config.js` missing or unoptimized.

---

### Immediate Next Steps (Your Call To Action)
1. **Empty Backend Dirs**: Clean up the unused dummy directories inside `varex_backend/app/api/` (email, s3, webhook, razorpay) since those responsibilities are now either Next.js specific routes or integrated tightly into other API spaces like `api/v1/auth.py` and `api/v1/subscriptions.py`.
2. **LLM Implementation**: Rebuild the hardcoded Logic in `app/services/ats_service.py` to actually call the Gemini api using `google-generativeai` (since it's installed in `requirements.txt`).
3. **Database Indexing**: Create an alembic revision that manually applies fast indexes to heavily queried fields (like user IDs on foreign keys, email fields, and active status fields).
4. **Testing Infrastructure**: Add basic pytest scaffolding manually inside a new `varex_backend/tests/` folder.
