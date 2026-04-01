# VAREX Platform

**Virtual Architecture, Resilience & Execution**  
Full-stack SaaS platform for DevSecOps consulting, Cybersecurity, SAP SD, AI Hiring, premium learning content, and workshop delivery.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Prerequisites](#prerequisites)
3. [Quick Start — Local Development](#quick-start--local-development)
4. [Environment Variables](#environment-variables)
5. [Database — Schemas, Tables & Columns](#database--schemas-tables--columns)
6. [Running with Docker](#running-with-docker)
7. [Using a Local IP Instead of a Domain](#using-a-local-ip-instead-of-a-domain)
8. [Going Live — Switching to varextech.in](#going-live--switching-to-varextechin)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Platform Architecture](#platform-architecture)
11. [Features](#features)
12. [API Reference](#api-reference)
13. [Project Structure](#project-structure)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI (Python 3.12), SQLAlchemy (async), Alembic |
| Database | PostgreSQL 16 |
| Auth | JWT (access + refresh tokens), bcrypt |
| Payments | Razorpay |
| File Storage | AWS S3 + CloudFront CDN |
| Email | SendGrid |
| Reverse Proxy | Nginx |
| Containerisation | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Prerequisites

Install these before anything else:

| Tool | Version | Install |
|---|---|---|
| Node.js | 20+ | https://nodejs.org |
| Python | 3.12+ | https://python.org |
| PostgreSQL | 16+ | https://postgresql.org |
| Docker | 24+ | https://docker.com |
| Docker Compose | v2+ | bundled with Docker Desktop |
| Git | any | https://git-scm.com |

Optional but recommended:

- **pgAdmin 4** — GUI for PostgreSQL  
- **Postman** — API testing  
- **VS Code** with extensions: Pylance, ESLint, Tailwind CSS IntelliSense

---

## Quick Start — Local Development

### 1. Clone the repository

```bash
git clone https://github.com/your-org/varex.git
cd varex
```

### 2. Set up the Backend

```bash
cd varex-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill environment variables
cp .env.example .env
# Edit .env — minimum required: DATABASE_URL and SECRET_KEY

# Create the database
psql -U postgres -c "CREATE DATABASE varexdb;"
psql -U postgres -c "CREATE USER varex WITH PASSWORD 'varexpassword';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE varexdb TO varex;"

# Run migrations (creates all tables)
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

API is now live at: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

### 3. Set up the Frontend

```bash
cd varex-frontend

# Install dependencies
npm install

# Install integration packages
npm i razorpay @aws-sdk/client-s3 @aws-sdk/s3-request-presigner uuid
npm i @types/uuid tailwindcss-animate @tailwindcss/typography @tailwindcss/forms --save-dev

# Copy and fill environment variables
cp .env.local.example .env.local
# Edit .env.local — minimum required: NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Start the dev server
npm run dev
```

Frontend is now live at: http://localhost:3000

### 4. Create the first admin user

After the backend is running:

```bash
# Using the Swagger UI at http://localhost:8000/docs
# POST /api/v1/auth/register with:
{
  "name": "Admin",
  "email": "admin@varextech.in",
  "password": "yourpassword"
}

# Then manually promote to admin in psql:
psql -U varex -d varexdb -c "UPDATE users SET role='admin' WHERE email='admin@varextech.in';"
```

---

## Environment Variables

### varex-frontend/.env.local

```env
# Backend API
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000     # local dev
# NEXT_PUBLIC_API_BASE_URL=https://varextech.in    # production

# Razorpay
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx             # use rzp_test_ for dev
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_signing_secret
NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx

# AWS S3
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET=varex-assets
AWS_CLOUDFRONT_URL=https://dXXXXXXXXXX.cloudfront.net

# SendGrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxx

# Internal
INTERNAL_API_SECRET=any_random_32_char_string
```

### varex-backend/.env

```env
DATABASE_URL=postgresql+asyncpg://varex:varexpassword@localhost:5432/varexdb
SECRET_KEY=generate_with_openssl_rand_hex_32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000
RAZORPAY_WEBHOOK_SECRET=your_webhook_signing_secret
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=noreply@varextech.in
INTERNAL_API_SECRET=same_as_frontend_internal_secret
```

---

## Database — Schemas, Tables & Columns

All tables are created automatically by `alembic upgrade head`.  
Below is the complete reference.

### Table: `users`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, default uuid4 | Unique user ID |
| name | VARCHAR(255) | NOT NULL | Full name |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| hashed_password | TEXT | NOT NULL | bcrypt hash |
| role | ENUM | NOT NULL, default 'free_user' | free_user / premium / enterprise / admin |
| is_active | BOOLEAN | default true | Account status |
| avatar_url | TEXT | nullable | S3/CDN profile picture URL |
| company | VARCHAR(255) | nullable | Company name (enterprise users) |
| created_at | TIMESTAMP | default now() | Registration time |
| updated_at | TIMESTAMP | auto-update | Last modified |

**Role values:** `free_user` · `premium` · `enterprise` · `admin`

---

### Table: `subscriptions`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Subscription ID |
| user_id | UUID | FK → users.id | Owner |
| plan_type | VARCHAR(50) | NOT NULL | monthly / quarterly / enterprise |
| status | VARCHAR(50) | NOT NULL | pending / active / expired / cancelled |
| razorpay_order_id | VARCHAR(255) | nullable | Razorpay order reference |
| razorpay_payment_id | VARCHAR(255) | nullable | Razorpay payment reference |
| expiry_date | TIMESTAMP | nullable | When subscription ends |
| created_at | TIMESTAMP | default now() | |
| updated_at | TIMESTAMP | auto-update | |

---

### Table: `content`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Content ID |
| title | VARCHAR(500) | NOT NULL | Article/module title |
| slug | VARCHAR(500) | UNIQUE, NOT NULL | URL slug |
| body | TEXT | NOT NULL | HTML content |
| category | VARCHAR(100) | NOT NULL | devops / security / sap / architecture / ai_hiring |
| access_level | VARCHAR(50) | default 'free' | free / premium |
| is_published | BOOLEAN | default false | Published flag |
| author_id | UUID | FK → users.id | Author |
| created_at | TIMESTAMP | default now() | |
| updated_at | TIMESTAMP | auto-update | |

---

### Table: `leads`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Lead ID |
| name | VARCHAR(255) | NOT NULL | Contact name |
| email | VARCHAR(255) | NOT NULL | Contact email |
| company | VARCHAR(255) | nullable | Company name |
| phone | VARCHAR(20) | nullable | Phone number |
| service_interest | VARCHAR(255) | NOT NULL | Service they enquired about |
| message | TEXT | nullable | Additional message |
| status | VARCHAR(50) | default 'new' | new / contacted / qualified / converted / rejected |
| created_at | TIMESTAMP | default now() | |

---

### Table: `workshops`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Workshop ID |
| title | VARCHAR(500) | NOT NULL | Workshop title |
| slug | VARCHAR(500) | UNIQUE | URL slug |
| description | TEXT | nullable | Full description |
| mode | VARCHAR(50) | NOT NULL | online / offline / hybrid |
| price | NUMERIC(10,2) | default 0 | Price in INR |
| max_seats | INTEGER | NOT NULL | Seat capacity |
| seats_booked | INTEGER | default 0 | Booked seats count |
| status | ENUM | NOT NULL | upcoming / open / completed / cancelled |
| scheduled_date | TIMESTAMP | nullable | Workshop date |
| is_published | BOOLEAN | default false | |
| created_at | TIMESTAMP | default now() | |

### Table: `workshop_registrations`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Registration ID |
| workshop_id | UUID | FK → workshops.id | Workshop |
| user_id | UUID | FK → users.id | Registered user |
| created_at | TIMESTAMP | default now() | Registration time |

---

### Table: `portfolio`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Project ID |
| title | VARCHAR(500) | NOT NULL | Case study title |
| slug | VARCHAR(500) | UNIQUE | URL slug |
| summary | TEXT | nullable | Short description |
| body | TEXT | nullable | Full case study HTML |
| category | VARCHAR(100) | nullable | devops / security / sap / ai_hiring |
| tech_stack | ARRAY[TEXT] | nullable | Technologies used |
| client_name | VARCHAR(255) | nullable | Client (anonymised) |
| is_published | BOOLEAN | default false | |
| created_at | TIMESTAMP | default now() | |

---

### Table: `team_members`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Member ID |
| name | VARCHAR(255) | NOT NULL | Full name |
| slug | VARCHAR(255) | UNIQUE | URL slug |
| role | VARCHAR(255) | NOT NULL | Job title |
| bio | TEXT | nullable | Profile bio |
| avatar_url | TEXT | nullable | Profile picture URL |
| avatar_s3_key | TEXT | nullable | S3 key for avatar |
| linkedin_url | TEXT | nullable | LinkedIn profile |
| github_url | TEXT | nullable | GitHub profile |
| specialisations | ARRAY[TEXT] | nullable | Skills list |
| display_order | INTEGER | default 0 | Sort order on /team page |
| is_published | BOOLEAN | default false | |
| created_at | TIMESTAMP | default now() | |

---

### Table: `certifications`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Cert ID |
| title | VARCHAR(500) | NOT NULL | Certification name |
| issuer | VARCHAR(255) | NOT NULL | e.g. AWS, CNCF, SAP |
| issued_to | VARCHAR(255) | NOT NULL | Person/team name |
| issued_date | DATE | nullable | Issue date |
| expiry_date | DATE | nullable | Expiry date |
| credential_url | TEXT | nullable | Verification link |
| badge_url | TEXT | nullable | Badge image URL |
| badge_s3_key | TEXT | nullable | S3 key for badge |
| is_published | BOOLEAN | default false | |
| created_at | TIMESTAMP | default now() | |

---

### Table: `faqs`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | FAQ ID |
| question | TEXT | NOT NULL | Question text |
| answer | TEXT | NOT NULL | Answer text (HTML allowed) |
| category | VARCHAR(100) | nullable | pricing / workshops / consulting / general |
| display_order | INTEGER | default 0 | Sort order |
| is_published | BOOLEAN | default false | |
| created_at | TIMESTAMP | default now() | |

---

## Running with Docker

```bash
# Build and start all 4 services (db, backend, frontend, nginx)
docker compose up --build

# Run in background
docker compose up --build -d

# Run migrations inside the backend container
docker compose exec backend alembic upgrade head

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop everything
docker compose down

# Stop and delete volumes (WARNING: deletes all DB data)
docker compose down -v
```

Services after `docker compose up`:

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

---

## Using a Local IP Instead of a Domain

If you have not bought `varextech.in` yet and want to test on your local network
(e.g. from a mobile or another machine on the same Wi-Fi):

### Step 1 — Find your local IP

```bash
# macOS / Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr IPv4
# Example result: 192.168.1.105
```

### Step 2 — Update frontend env

```env
# varex-frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://192.168.1.105:8000
```

### Step 3 — Update backend CORS

```env
# varex-backend/.env
ALLOWED_ORIGINS=http://192.168.1.105:3000,http://localhost:3000
```

### Step 4 — Update Razorpay webhook (dev)

Use **ngrok** to expose localhost publicly for Razorpay webhook testing:

```bash
npm install -g ngrok
ngrok http 3000
# Copy the https://xxxx.ngrok.io URL
# Set Razorpay webhook URL to: https://xxxx.ngrok.io/api/webhook/razorpay
```

### Step 5 — Restart services

```bash
# If running manually
cd varex-backend  && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd varex-frontend && npm run dev -- --hostname 0.0.0.0

# If using Docker
docker compose down && docker compose up --build
```

Now access from any device on your network:  
`http://192.168.1.105:3000`

---

## Going Live — Switching to varextech.in

Once you purchase `varextech.in`, update these locations:

### 1. DNS — Point domain to your VPS

In your domain registrar (GoDaddy / Namecheap / Cloudflare):

```
Type  Name   Value              TTL
A     @      YOUR_VPS_IP        300
A     www    YOUR_VPS_IP        300
CNAME api    varextech.in       300   (optional)
```

### 2. SSL Certificate (free via Let's Encrypt)

```bash
# On your VPS
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d varextech.in -d www.varextech.in
# Certificates saved to /etc/letsencrypt/live/varextech.in/
```

Update `nginx/nginx.conf`:
```nginx
ssl_certificate     /etc/letsencrypt/live/varextech.in/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/varextech.in/privkey.pem;
```

### 3. Frontend env — update API URL

```env
# varex-frontend/.env.local  (or Vercel environment variables)
NEXT_PUBLIC_API_BASE_URL=https://varextech.in
```

### 4. Backend env — update CORS

```env
# varex-backend/.env
ALLOWED_ORIGINS=https://varextech.in,https://www.varextech.in
ENVIRONMENT=production
```

### 5. Update metadata base URL

```ts
// lib/metadata.ts — line 2
const BASE_URL = "https://varextech.in";   // already set correctly
```

### 6. Razorpay — switch to live keys

```env
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxx      # was rzp_test_
NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxx
```

Set webhook URL in Razorpay dashboard:  
`https://varextech.in/api/webhook/razorpay`

### 7. SendGrid — verify domain

1. Go to SendGrid → Settings → Sender Authentication  
2. Authenticate domain `varextech.in`  
3. Add the CNAME records they provide to your DNS

### 8. GitHub Secrets — add VPS details

```
DEPLOY_HOST      = your VPS IP or varextech.in
DEPLOY_USER      = ubuntu (or root)
DEPLOY_SSH_KEY   = contents of your private SSH key
```

### 9. Push to main — triggers auto-deploy

```bash
git push origin main
# GitHub Actions will: test → build → push Docker images → SSH deploy
```

---

## CI/CD Pipeline

```
git push origin main
        │
        ├─► Job 1: Backend Tests
        │     └─ pytest + alembic on test PostgreSQL DB
        │
        ├─► Job 2: Frontend Build
        │     └─ tsc --noEmit + eslint + next build
        │
        └─► (both pass + branch=main)
              │
              ├─► Job 3: Build & Push Docker Images
              │     └─ ghcr.io/your-org/varex-backend:latest
              │     └─ ghcr.io/your-org/varex-frontend:latest
              │
              └─► Job 4: Deploy to VPS
                    └─ SSH → docker compose pull → docker compose up -d
```

PRs only run Jobs 1 & 2 — never build or deploy.

---

## Platform Architecture

```
                        ┌─────────────────────────────────┐
                        │         varextech.in             │
                        │         Nginx (443/80)           │
                        │   HTTP → HTTPS redirect          │
                        └──────────┬──────────────┬────────┘
                                   │              │
                        /api/*     │              │  /*
                                   ▼              ▼
                        ┌──────────────┐  ┌──────────────┐
                        │   FastAPI    │  │   Next.js 15 │
                        │  :8000       │  │  :3000       │
                        │  Python 3.12 │  │  TypeScript  │
                        └──────┬───────┘  └──────┬───────┘
                               │                 │
                               ▼                 │
                        ┌──────────────┐         │
                        │  PostgreSQL  │         │
                        │  :5432       │         │
                        └──────────────┘         │
                                                 │
                        ┌────────────────────────▼──────┐
                        │      Next.js API Routes        │
                        │  /api/razorpay/create-order    │
                        │  /api/razorpay/verify          │
                        │  /api/webhook/razorpay         │
                        │  /api/s3/presign               │
                        │  /api/email/send               │
                        └───────────────────────────────┘
                                    │
              ┌─────────────────────┼──────────────────────┐
              ▼                     ▼                       ▼
      ┌──────────────┐    ┌──────────────────┐   ┌──────────────────┐
      │   Razorpay   │    │   AWS S3 +        │   │    SendGrid      │
      │   Payments   │    │   CloudFront CDN  │   │    Email         │
      └──────────────┘    └──────────────────┘   └──────────────────┘
```

### Role-Based Access Control

```
Guest (not logged in)
  └─ Public pages, blog, portfolio, workshops listing

free_user
  └─ All of above + dashboard, free content, workshop registration

premium
  └─ All of above + all premium modules, workshop recordings

enterprise
  └─ All of above + enterprise portal, dedicated account manager

admin
  └─ Everything + admin panel, user management, lead management, analytics
```

---

## Features

### Public Website
- **Homepage** — Hero, services strip (DevSecOps / Security / SAP / AI Hiring), testimonials, newsletter
- **Blog** — Category pages for DevOps, Cybersecurity, SAP SD, Architecture, AI Hiring; free + premium articles
- **Portfolio** — Case studies with tech stack, client industry, outcomes
- **Workshops** — Listing, individual pages, seat availability, registration
- **Team** — Member profiles with specialisations and social links
- **Certifications** — Issued certs with badge images and credential URLs
- **FAQ** — Categorised, searchable FAQ
- **Services** — Detail pages for DevSecOps / Cybersecurity / SAP SD / AI Hiring
- **Pricing** — Free / Premium (monthly + quarterly) / Enterprise
- **Contact** — Consultation form with lead capture
- **Hire** — AI Hiring landing page
- **Legal** — Privacy Policy, Terms of Service, Refund Policy

### Authentication
- Email + password registration and login
- JWT access tokens (60 min) + refresh tokens (7 days) stored in cookies
- Protected routes (client-side ProtectedRoute + server-side API guards)
- Change password from settings page
- Role-based access: free_user / premium / enterprise / admin

### Dashboards
| Dashboard | Accessible by | Features |
|---|---|---|
| Base | All logged-in users | Role card, quick links, subscription status |
| Premium | premium + admin | Content library, subscription days remaining, expiry warning |
| Enterprise | enterprise + admin | Company portal, workshops, consultation activity |
| Admin | admin only | 4 tabs: overview stats, user management, lead pipeline, content links |

### Settings Page
- Edit name and profile avatar (S3 upload with progress ring)
- Change password
- Subscription status + upgrade/billing CTA

### Payments (Razorpay)
- Monthly plan: ₹1,499 / Quarterly: ₹3,999
- HMAC signature verification on payment
- Server-side webhook handler for `payment.captured`
- Subscription auto-activated after payment verified

### File Uploads (AWS S3)
- Pre-signed PUT URLs (files go directly to S3, not through the server)
- Upload types: `avatar`, `resume`, `badge`, `diagram`
- Upload progress ring in UI
- CloudFront CDN delivery

### Email (SendGrid)
- 5 transactional templates: welcome, lead confirmation, workshop registration, subscription activated, expiry reminder
- Internal API route for server-side email triggering
- Domain-authenticated from `noreply@varextech.in`

### SEO
- `app/sitemap.ts` — dynamic sitemap including blog/portfolio/workshop slugs
- `app/robots.ts` — blocks `/dashboard/`, `/api/`, `/admin/`
- `lib/metadata.ts` — `buildMetadata()` + `PAGE_META` for all 12 static pages
- OpenGraph and Twitter Card tags on every page

### DevOps
- Multi-stage Docker builds (frontend: deps → builder → runner)
- `docker-compose.yml` — 4 services: PostgreSQL, FastAPI, Next.js, Nginx
- Nginx: HTTP → HTTPS redirect, gzip, security headers, reverse proxy
- GitHub Actions CI/CD: 4 jobs (test backend, test frontend, build images, deploy)
- Docker image caching via GitHub Actions cache
- SSH-based zero-downtime deploy on push to `main`

---

## API Reference

Base URL: `http://localhost:8000/api/v1`  
Full interactive docs: `http://localhost:8000/docs`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /auth/register | Public | Create account |
| POST | /auth/login | Public | Get JWT tokens |
| POST | /auth/refresh | Public | Refresh access token |
| POST | /auth/change-password | User | Change password |
| GET | /users/me | User | Get own profile |
| PATCH | /users/{id} | User/Admin | Update profile |
| GET | /users | Admin | List all users |
| PATCH | /users/{id} | Admin | Toggle active status |
| GET | /content/free | Public | Free articles |
| GET | /content/premium | Premium | Premium modules |
| POST | /content | Admin | Create content |
| GET | /subscriptions/me | User | Own subscription |
| POST | /subscriptions | User | Create subscription |
| PATCH | /subscriptions/activate | User | Activate after payment |
| GET | /leads | Admin | All leads |
| POST | /leads | Public | Submit contact form |
| PATCH | /leads/{id}/status | Admin | Update lead status |
| GET | /workshops | Public | Published workshops |
| GET | /workshops/{slug} | Public | Workshop detail |
| POST | /workshops | Admin | Create workshop |
| PATCH | /workshops/{id} | Admin | Update workshop |
| DELETE | /workshops/{id} | Admin | Delete workshop |
| POST | /workshops/{id}/register | User | Register for workshop |
| GET | /workshops/{id}/registrations | Admin | View registrations |
| GET | /portfolio | Public | Portfolio items |
| GET | /team | Public | Team members |
| PATCH | /team/{id}/avatar | Admin | Update avatar |
| GET | /certifications | Public | Certifications |
| GET | /faq | Public | FAQs |
| GET | /analytics | Admin | Platform analytics |
| POST | /webhooks/razorpay | Internal | Razorpay webhook |

---

## Project Structure

```
varex/
├── varex-backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── subscription.py
│   │   │   ├── content.py
│   │   │   ├── lead.py
│   │   │   ├── workshop.py
│   │   │   ├── portfolio.py
│   │   │   ├── team.py
│   │   │   ├── certification.py
│   │   │   └── faq.py
│   │   ├── schemas/          (Pydantic schemas for every model)
│   │   ├── api/v1/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── content.py
│   │   │   ├── subscriptions.py
│   │   │   ├── leads.py
│   │   │   ├── workshops.py
│   │   │   ├── portfolio.py
│   │   │   ├── team.py
│   │   │   ├── certifications.py
│   │   │   ├── faq.py
│   │   │   ├── analytics.py
│   │   │   └── webhooks.py
│   │   ├── dependencies/
│   │   │   └── auth.py
│   │   └── db/
│   │       └── session.py
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── varex-frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── loading.tsx
│   │   ├── not-found.tsx
│   │   ├── error.tsx
│   │   ├── sitemap.ts
│   │   ├── robots.ts
│   │   ├── login/
│   │   ├── register/
│   │   ├── blog/
│   │   │   ├── page.tsx
│   │   │   ├── [slug]/
│   │   │   ├── devops/
│   │   │   ├── security/
│   │   │   ├── sap/
│   │   │   ├── architecture/
│   │   │   └── ai_hiring/
│   │   ├── portfolio/
│   │   ├── workshops/
│   │   ├── team/
│   │   ├── certifications/
│   │   ├── faq/
│   │   ├── services/[slug]/
│   │   ├── pricing/
│   │   ├── hire/
│   │   ├── contact/
│   │   ├── learnings/
│   │   ├── privacy/
│   │   ├── terms/
│   │   ├── refund/
│   │   ├── dashboard/
│   │   │   ├── page.tsx
│   │   │   ├── admin/
│   │   │   ├── premium/
│   │   │   ├── enterprise/
│   │   │   └── settings/
│   │   └── api/
│   │       ├── razorpay/
│   │       ├── webhook/
│   │       ├── s3/
│   │       └── email/
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── Footer.tsx
│   │   ├── ProtectedRoute.tsx
│   │   ├── Testimonials.tsx
│   │   ├── NewsletterSignup.tsx
│   │   ├── AvatarUpload.tsx
│   │   └── CookieBanner.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   ├── types.ts
│   │   ├── razorpay.ts
│   │   ├── s3.ts
│   │   ├── email.ts
│   │   └── metadata.ts
│   ├── public/
│   │   ├── og-default.png
│   │   ├── og-home.png
│   │   ├── favicon.ico
│   │   └── logo.svg
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── Dockerfile
│   └── .env.local.example
│
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
└── .github/
    └── workflows/
        └── ci-cd.yml
```

---

*Built by VAREX Technologies · Bengaluru, India · varextech.in*


GitHub-Based Blog Content Integration — Walkthrough
What Was Built
The VAREX blog now dynamically fetches 161 AWS Interview Prep markdown posts from the GitHub repository at https://github.com/thrinathadevops/VERTEX/tree/main/aws-interview-prep.

Architecture
/api/content/github
List files
Fetch raw .md
5-min cache
ContentItem[]
Browser
GitHub API Route
GitHub Contents API
raw.githubusercontent.com
In-Memory Cache
The frontend fetches from 3 content sources in parallel:

Local Markdown (/api/content/local) — files in content/blog/
Backend Database (/api/v1/content/free) — PostgreSQL via FastAPI
GitHub Repository (/api/content/github) — NEW ← fetches from GitHub
Files Changed
File	Action	Purpose
route.ts
NEW	GitHub content API with caching
aws_interview/page.tsx
NEW	AWS Interview category page
api.ts
Modified	Added GitHub as 3rd content source
blog/page.tsx
Modified	Added AWS Interview category
local/route.ts
Modified	Added aws_interview category
.env.local.example
Modified	Added GitHub config vars