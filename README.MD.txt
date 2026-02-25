Backend

Project Structure

varex_backend/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── app/
    ├── main.py                        ← FastAPI app, CORS, middleware, routers
    ├── core/
    │   ├── config.py                  ← Pydantic Settings (env-driven)
    │   └── security.py                ← bcrypt hashing + JWT encode/decode
    ├── models/
    │   ├── user.py                    ← User + UserRole enum
    │   ├── subscription.py            ← Subscription + PlanType/Status enums
    │   └── content.py                 ← Content + AccessLevel enum
    ├── schemas/
    │   ├── auth.py / user.py / ...    ← Pydantic v2 I/O schemas
    ├── api/v1/
    │   ├── auth.py                    ← /register /login /refresh
    │   ├── users.py                   ← /me  /admin/all
    │   ├── content.py                 ← /free /premium /{id}
    │   └── subscription.py            ← /me  POST /
    ├── services/
    │   ├── user_service.py
    │   ├── auth_service.py
    │   └── subscription_service.py
    ├── dependencies/
    │   └── auth.py                    ← get_current_user, require_roles(), require_premium
    ├── middleware/
    │   └── auth_middleware.py         ← Request logging middleware
    └── db/
        ├── base.py                    ← DeclarativeBase + model imports
        └── session.py                 ← Async engine + get_db() dependency


Key Design Decisions
Auth Flow
JWT access tokens (60 min) + refresh tokens (7 days) are issued at /api/v1/auth/login . The decode_token() function in security.py validates both token type and expiry . Refresh tokens cannot be used as access tokens — the type field is strictly checked.

RBAC System
The require_roles(*roles) dependency factory in app/dependencies/auth.py lets you gate any route to specific roles with a single line :

Depends(require_roles(UserRole.admin))          # Admin only
Depends(require_premium)                         # premium_user or admin
Depends(get_current_active_user)                 # any authenticated user


User Roles (4 tiers)

| Role         | Access                                                     |
| ------------ | ---------------------------------------------------------- |
| guest        | No login required (free content public endpoints)          |
| free_user    | Default on register; protected routes, no premium content  |
| premium_user | All content, subscription features                         |
| admin        | Full access including user management and content creation |

Database Layer
Uses SQLAlchemy 2.0 async with asyncpg driver for non-blocking PostgreSQL queries . Tables are auto-created on startup via Base.metadata.create_all — swap for Alembic migrations in production .

Subscription Logic
Plan durations are defined in subscription_service.py: monthly = 30 days, annual = 365 days, free = no expiry . Razorpay fields (razorpay_order_id, razorpay_payment_id) are stored on the Subscription model as placeholders ready for wiring up .

Quick Start

# 1. Clone & configure
cp .env.example .env
# Edit .env with your real SECRET_KEY and DATABASE_URL

# 2. Run with Docker Compose
docker compose up --build

# 3. API docs available at:
# http://localhost:8000/api/docs   ← Swagger UI
# http://localhost:8000/api/redoc  ← ReDoc


Next Steps to Wire Up
Alembic – replace create_all with proper migrations (alembic init alembic)

Razorpay – verify razorpay_payment_id in POST /api/v1/subscriptions/ before activating plan

Role upgrade – add a DB update in subscription_service to set user.role = premium_user on successful payment

AI Interview module – add app/api/v1/interview.py as a placeholder router (scaffolded and ready)

Redis – add token blacklisting for logout/revoke using a Redis dependency

Froentend

Project structure

app/
  layout.tsx           // Root layout with Navbar + Footer
  globals.css          // Tailwind + base styles
  page.tsx             // Public home page
  login/page.tsx       // Login screen
  register/page.tsx    // Register screen
  dashboard/page.tsx   // Auth-required dashboard
  blog/page.tsx        // Free + premium posts (blurred if not premium)
  learnings/page.tsx   // Subscription / upgrade UI

components/
  Navbar.tsx           // Top navigation with role badge, login/logout
  Footer.tsx           // Global footer
  ProtectedRoute.tsx   // Client-side auth guard wrapper
  ContentCard.tsx      // Card with optional premium blur banner

lib/
  api.ts               // Axios client, JWT refresh flow, API helpers
  auth.ts              // Token + user cookie helpers
  types.ts             // Shared TS interfaces (User, Subscription, ContentItem, Tokens)
  jwt-decode.d.ts      // Minimal typing for jwt-decode


Key implementation details
Tailwind + layout
Tailwind is wired through globals.css, tailwind.config.ts, and postcss.config.mjs.

layout.tsx applies a subtle gradient background, uses Navbar and Footer, and constrains content to max-w-6xl for a focused SaaS feel.

Auth + JWT handling
lib/api.ts configures an Axios instance pointing to your FastAPI backend at NEXT_PUBLIC_API_BASE_URL (default http://localhost:8000).

Access token from login is attached as Authorization: Bearer <token> on all requests, and a 401 triggers a refresh call to /api/v1/auth/refresh using the refresh token.

lib/auth.ts stores tokens in cookies (access_token, refresh_token) and provides helpers to clear them and read a cached user for role-based UI. This matches your requirement conceptually (HTTP-only would be done via backend Set-Cookie headers; here we simulate via js-cookie on the client).

Role-based UI + premium lock
User shape and roles (guest, free_user, premium_user, admin) are centralized in lib/types.ts.

Navbar shows the current user email and a small role pill, plus “Sign out” that clears tokens and returns to /.

ProtectedRoute wraps pages such as Dashboard and Learnings, redirecting unauthenticated users to /login?next=/requested-path.

Blog uses ContentCard with a blurred flag. Premium posts are rendered with a blur and a “Premium insight” banner when the user is not premium; if role is premium_user or admin, full text is visible.

Pages wired to FastAPI backend
Login / Register call /auth/login and /auth/register via lib/api.ts, then store tokens and route to /dashboard.

Dashboard calls /users/me and /subscriptions/me to show role, current plan, and premium status; non‑premium users see an upgrade CTA linking to /learnings.

Blog calls /content/free and /content/premium, matching your FastAPI endpoints, and applies the premium blur logic.

Learnings acts as a subscription/upgrade page, calling POST /subscriptions with plan_type of monthly or annual and showing the result message. (Payment UI is mocked; you can later wire Razorpay around createSubscription.)

How to run
Unzip:

unzip varex_next_frontend.zip
cd varex-frontend   # or the folder name you choose

Configure env:

cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_BASE_URL to your FastAPI URL (e.g., http://localhost:8000)

Install + dev:

npm install
npm run dev
# App at http://localhost:3000

Architecture overview
The system has two levels of access control — route-level via FastAPI Depends(), and object-level via a helper you call inside the route body.

Role hierarchy
The roles are assigned integer ranks so higher roles automatically inherit access to everything below them :

ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.guest:        0,
    UserRole.free_user:    1,
    UserRole.premium_user: 2,
    UserRole.admin:        3,   # ← passes every gate
}

The 7 building blocks
1. get_current_user — JWT decoder & DB loader

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:

Decodes the JWT with python-jose, validates payload["type"] == "access" (so refresh tokens are rejected), then loads the user from PostgreSQL. Raises HTTP 401 on any failure.

2. require_roles() — exact whitelist factory

def require_roles(*allowed_roles: UserRole) -> Callable:

Returns a FastAPI dependency that only allows users whose role is exactly in the whitelist. Good for admin-only endpoints where you don't want premium users slipping through.

3. require_minimum_role() — hierarchy-aware factory

def require_minimum_role(minimum_role: UserRole) -> Callable:

Returns a dependency that allows the specified role and every role ranked above it. Admin always passes every gate.

4. Pre-built convenience dependencies
These cover the three VAREX content tiers and are ready to use directly in Depends() :

| Dependency              | Who passes                     |
| ----------------------- | ------------------------------ |
| require_free            | free_user, premium_user, admin |
| require_premium         | premium_user, admin            |
| require_admin           | admin only                     |
| get_current_active_user | any authenticated active user  |

5. check_content_access() — per-object runtime gate

def check_content_access(content_access_level: str, user: User) -> None:

Call this inside a route after fetching a content object to enforce object-level access. Raises HTTP 403 if the content is "premium" and the user is not premium or admin.

Usage at a glance

from app.dependencies.auth import (
    get_current_active_user,
    require_admin,
    require_premium,
    require_free,
    require_roles,
    check_content_access,
)

# ── Any logged-in user ────────────────────────────────────────────────
@router.get("/profile")
async def profile(user: User = Depends(get_current_active_user)):
    return user

# ── Free content: free_user + premium_user + admin ────────────────────
@router.get("/content/free")
async def free_content(user: User = Depends(require_free)):
    ...

# ── Premium content: premium_user + admin ────────────────────────────
@router.get("/content/premium")
async def premium_content(user: User = Depends(require_premium)):
    ...

# ── Admin-only route ──────────────────────────────────────────────────
@router.delete("/users/{id}")
async def delete_user(user: User = Depends(require_admin)):
    ...

# ── Per-object gate (content fetched from DB first) ───────────────────
@router.get("/content/{id}")
async def get_content(id: UUID, user: User = Depends(get_current_active_user), db=Depends(get_db)):
    content = await fetch_content(db, id)
    check_content_access(content.access_level, user)   # 403 if needed
    return content

Error responses

| Situation                           | HTTP code | Detail message                             |
| ----------------------------------- | --------- | ------------------------------------------ |
| Missing / expired / malformed token | 401       | "Could not validate credentials."          |
| Refresh token used as access token  | 401       | Same                                       |
| User not found or inactive          | 401       | Same                                       |
| Role not in whitelist               | 403       | Lists required roles + user's current role |
| Content access level too high       | 403       | "Premium subscription required…"           |

Files generated
File	Purpose
app/models/interview.py	DB models: JobDescription, CandidateProfile, InterviewSession, InterviewTurn, ScoreReport
app/schemas/interview.py	Pydantic v2 request/response schemas
app/services/ats_service.py	ATS resume screening pipeline
app/services/interview_service.py	30-min AI session state machine
app/api/v1/interview.py	All FastAPI route endpoints
System architecture
The module has two sequential stages before a candidate reaches a human panel:

text
Resume Upload → ATS Screening → AI Interview (30 min) → Score Report
                                                       └→ Video Recording (Premium)
Stage 1 — ATS Screening
Data models
python
class JobDescription(Base):
    description      # Full JD text
    required_skills  # ["Python", "FastAPI", "Redis"]
    screening_prompt # Team-lead custom instruction:
                     # "Focus on async patterns and system design depth"

class CandidateProfile(Base):
    resume_text      # Extracted from uploaded PDF
    ats_score        # 0–100 computed score
    ats_report       # {matched_skills, missing_skills, summary, recommendation}
    screening_status # pending → screened → shortlisted / rejected
ATS pipeline (ats_service.py)
The run_ats_scan() function runs in 3 steps:

Keyword match — scans resume text for each required skill from the JD

LLM evaluation — passes JD + resume + team-lead's screening_prompt to the AI model with a recruiter system prompt. Replace the _call_llm_ats() stub with OpenAI/Gemini

Auto-status — persists shortlisted if score ≥ 70, rejected if < 40, screened otherwise

ATS endpoints
text
POST /api/v1/interview/candidates              → Register candidate
POST /api/v1/interview/candidates/{id}/upload-resume  → Upload PDF (parsed server-side)
POST /api/v1/interview/screen                 → Run ATS scan → returns score + matched/missing skills
Stage 2 — AI Interview (30 min)
Session state machine (interview_service.py)
text
scheduled → in_progress → completed
The session runs 8 turns (~4 min each = 30 min total). Each turn:

AI generates a contextual question based on JD + resume + conversation history

Candidate submits answer via API

AI scores the answer 0–10 and returns a polite acknowledgement reply

Next question is queued automatically

After turn 8 → session ends → ScoreReport is generated and persisted

Score Report dimensions
python
class ScoreReport(Base):
    overall_score         # 0–100
    communication_score   # 0–10
    technical_score       # 0–10
    problem_solving_score # 0–10
    confidence_score      # 0–10
    strengths             # ["Good async knowledge", ...]
    areas_to_improve      # ["Depth on distributed systems", ...]
    recommendation        # "Shortlist" | "Review" | "Reject"
    ai_summary            # Full narrative paragraph
Interview endpoints
text
POST   /api/v1/interview/sessions                         → Create session
POST   /api/v1/interview/sessions/{id}/start              → AI asks Q1
GET    /api/v1/interview/sessions/{id}/current-question   → Fetch pending question
POST   /api/v1/interview/sessions/{id}/turns/{tid}/answer → Submit answer + get AI reply
GET    /api/v1/interview/sessions/{id}/turns              → Full Q&A transcript
GET    /api/v1/interview/sessions/{id}/report             → Score report
GET    /api/v1/interview/sessions/{id}/recording          → 🔒 Premium: S3 video URL
Video recording (Premium gate)
Video recording is gated at two levels :

At session creation: video_recording_enabled=True raises HTTP 403 if user is not premium_user or admin

At recording retrieval: require_premium dependency blocks free users from accessing the S3 URL

The video_s3_key column stores the S3 path. Replace the stub in /recording with boto3.generate_presigned_url() to return a time-limited secure URL.

Wire it into main.py
Add this to your existing app/main.py:

python
from app.api.v1 import interview  # add this import

app.include_router(
    interview.router,
    prefix="/api/v1/interview",
    tags=["Interview"]
)
And add to app/db/base.py:


from app.models.interview import (   # noqa
    JobDescription, CandidateProfile,
    InterviewSession, InterviewTurn, ScoreReport
)
LLM integration (production swap)
Replace the three stubs in interview_service.py and ats_service.py with real API calls :

python
import openai

async def _call_llm_question(jd_text, resume_text, history, turn_number):
    response = await openai.ChatCompletion.acreate(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a senior technical interviewer..."},
            {"role": "user", "content": f"JD: {jd_text}\nHistory: {history}\nAsk question #{turn_number}"}
        ]
    )
    return response.choices[0].message.content
	
	