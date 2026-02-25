# VAREX Platform — Full Codebase Audit & Gap Register (Reverified)
> **Reviewed:** 2026-02-25 | **Author:** Antigravity code review (Re-verified after user modifications)
> **Scope:** Every Python + TypeScript file in `varex_backend/` and `varex_frontend/`

---

## 🛑 NEW CRITICAL ISSUES INTRODUCED FROM MODIFICATIONS

### [NEW CRITICAL] ❌ `package.json` Syntax Error
- **File:** `varex_frontend/package.json` line 18
- **Issue:** Missing comma after `"js-cookie": "3.0.5"`. The user added `"jwt-decode": "^4.0.0"` underneath it but forgot the preceding comma. This breaks `package.json` structurally. `npm install` and all frontend builds will fatally fail.
- **Fix:** Add a comma at the end of line 18.

### [STILL BROKEN CATASTROPHICALLY] ❌ `models/interview.py` vs `api/v1/interview.py` Duplication
- **File:** `varex_backend/app/models/interview.py` and `varex_backend/app/api/v1/interview.py`
- **Issue:** Instead of successfully separating the ORM models from the router, BOTH files now contain the exact same FastAPI router code. `models/interview.py` still imports from itself, causing a circular import crash. There are still zero SQLAlchemy ORM model definitions for the interview models.
- **Fix:** Delete `models/interview.py`. Create `models/interview_models.py` purely containing the SQLAlchemy mapper classes. Update `base.py` and `db.session` imports.

---

## 1. CRASH-LEVEL Bugs — Will crash on startup or first request
- **1.1** [✅ FIXED] `main.py` — Six `include_router()` calls BEFORE `app = FastAPI()`. Correctly moved to after application instantiation. 
- **1.2** [❌ STILL BROKEN] `models/interview.py` — Contains API router code, NOT ORM models. (See New Issues section above).
- **1.3** [⚠️ PARTIALLY FIXED] `varex_rbac.py` / `auth.py` — `UserRole.premium_user`. `auth.py` was fixed to use `UserRole.premium`. However, `varex_rbac.py` WAS NOT DELETED and still contains `premium_user`.
- **1.4** [❌ STILL BROKEN] `auth_b.py` — Was not deleted, duplicate auth module remains.
- **1.5** [✅ FIXED] `subscription_service.py` — References `PlanType.annual` which doesn't exist. Now maps to `PlanType.quarterly`.
- **1.6** [❌ STILL OPEN] `team.py` API — References `TeamMember.display_order` which doesn't exist.
- **1.7** [❌ STILL OPEN] `team.py` API — Writes to non-existent `member.avatar_url` attribute.
- **1.8** [❌ STILL OPEN] `analytics.py` — Wrong import path for `require_admin`.
- **1.9** [❌ STILL BROKEN] `interview.py` — Imports itself.
- **1.10** [❌ STILL BROKEN] `db/base.py` — Imports models that don't actually exist as ORM models.

## 2. Logic Bugs — Wrong behaviour at runtime
- **2.1** [❌ STILL OPEN] `subscriptions.py` — Wrong config attribute `RAZORPAY_SECRET`.
- **2.2** [✅ FIXED] `subscription_service.py` — Subscription idempotency issue.
- **2.3** [✅ FIXED] `subscription_service.py` — `enterprise` plan causing `TypeError`.
- **2.4** [❌ STILL OPEN] `auth_service.py` — Timing-safe password check bypassed.
- **2.5** [❌ STILL OPEN] `pricing/page.tsx` — Calls backend endpoint without Razorpay.
- **2.6** [❌ STILL BROKEN] `dashboard/page.tsx` — Role check uses wrong enum value `"premium_user"`.
- **2.7** [⚠️ PARTIALLY FIXED] `auth.ts` — `jwtDecode` dependency added, but broke `package.json` syntax.
- **2.8** [❌ STILL OPEN] `workshops.py` API — `seats_booked` never updated on registration.
- **2.9** [❌ STILL OPEN] `workshops.py` API — No seat limit check before registration.
- **2.10** [❌ STILL OPEN] `workshops.py` API — No duplicate registration check.
- **2.11 - 2.15** [❌ STILL OPEN] All other logic bugs remain.

## 3. Model / Schema Mismatches
- **3.1 - 3.19** [⚠️ PARTIALLY FIXED] You successfully generated `0002_align_models.py` using Alembic, which syncs the DB to the declarative base. However, the manual schema validations (e.g. `UserResponse` missing `updated_at`, `SubscriptionResponse` missing `razorpay_payment_id`) are likely still open within Pydantic models.

## 4. Connectivity Gaps — API to Frontend
- **4.1** [❌ STILL BROKEN] `razorpay.ts` calls `/api/razorpay/create-order` — Next.js route DOES NOT EXIST. The `varex_frontend/app/api/` folder is completely missing.
- **4.2** [❌ STILL BROKEN] `s3.ts` calls `/api/s3/presign` — Next.js route DOES NOT EXIST.
- **4.3** [❌ STILL BROKEN] `email.ts` — Exposes `SENDGRID_API_KEY` to the client side.
- **4.4** [❌ STILL OPEN] Backend `app/api/email/`, `app/api/s3/`, `app/api/webhook/`, `app/api/razorpay/` directories exist but are empty.
- **4.5** [✅ FIXED] Analytics router never registered. (Successfully added to `main.py`).
- **4.6 - 4.9** [❌ STILL OPEN] Missing endpoints in `api.ts`.

## 5. Security Gaps
- **5.1 - 5.10** [❌ ALL STILL OPEN] JWT missing `jti`, cookies lacking `httpOnly`, timing attacks pending, CORS whitelist incomplete, etc.

## 6. Missing Features & Stubs
- **6.1 - 6.13** [❌ ALL STILL OPEN] No actual LLM implementations (just stubs), no logout endpoints, no password reset functionality, lacking pagination, etc. 

## 7. Database / Migration Issues
- **7.1** [✅ FIXED] Alembic `0002_align_models.py` running aligns existing schemas.
- **7.2** [❌ STILL BROKEN] Interview models lack migrations because they aren't even defined successfully.
- **7.3** [✅ FIXED] `alembic.ini` and `env.py` configured correctly with `os.getenv("DATABASE_URL")`.
- **7.4, 7.5** [❌ STILL OPEN] Missing specific database indexes.
- **7.6** [✅ FIXED] `Base.metadata.create_all` successfully removed from production lifespan.

## 8. Infrastructure & Docker Gaps
- **8.1** [✅ FIXED] `docker-compose.yml` hyphen/underscore paths corrected (`varex_backend`, `varex_frontend`).
- **8.2** [✅ FIXED] `varex_frontend/Dockerfile` has been successfully created.
- **8.3 - 8.8** [❌ STILL OPEN] Backend Dockerfile optimizations, Certbot implementation, `redis` addition to compose, and `.dockerignore` creation still missing.

## 9. CI/CD Gaps
- **9.1** [❌ STILL OPEN] Github workflows still utilize hyphens where underscores are needed.
- **9.2** [❌ STILL OPEN] No `tests/` directory inside `varex_backend/`. Pytest execution will fail.
- **9.3, 9.4** [✅ FIXED] Packages `python-dotenv`, `boto3`, `slowapi`, `pdfminer.six` successfully added to backend `requirements.txt`.
- **9.5, 9.6** [❌ STILL OPEN] Frontend tests in CI, Latest Docker tags.

## 10. Best Practice Violations
- **10.1** [✅ FIXED] `main.py` `create_all` removed.
- **10.3** [❌ STILL OPEN] `auth.py`, `auth_b.py`, and `varex_rbac.py` exist concurrently leading to ambiguity. Delete the latter two.
- **10.4 - 10.11** [❌ STILL OPEN] All other best practices pending.

## 11. Dead Code & Housekeeping
- **11.1 - 11.8** [❌ ALMOST ALL STILL BROKEN] You have not deleted `user_old.py`, `subscription_old.py`, `auth_b.py`, `varex_rbac.py`, nor resolved the `app/models/interview.py` issue. 

## 12. Frontend Specific Issues
- **12.1 - 12.10** [❌ STILL OPEN] Missing standard static pages, missing `Forgot password?` workflows, role caching still relies on UI-editable tokens, `next.config.js` missing, etc.

---

### Immediate Re-Action Required (The "Must Fix Now" list)
1. **Fix `varex_frontend/package.json` line 18**: Insert a comma at the end of `"js-cookie": "3.0.5"`.
2. **Fix `interview.py`**: Stop copying the router into the `models` folder. The ORM models need to just be SQLAlchemy models.
3. **Delete Dead Auth Files**: Completely delete `varex_rbac.py` and `auth_b.py` and point all imports to `auth.py`. Update your dashboard route to strictly match `UserRole.premium`.
4. **Create `/api` directories in Next.js**: Create the Next.js API routing structure.
