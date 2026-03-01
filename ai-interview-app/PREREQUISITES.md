# 🛠️ VAREX AI Interview Platform — Prerequisites & Setup Guide

> **Complete reference for all dependencies, API key creation, pricing, and free testing strategies.**

---

## 📑 Table of Contents

1. [System Prerequisites](#1-system-prerequisites)
2. [AI Provider API Keys — Overview](#2-ai-provider-api-keys--overview)
3. [Option A: Google Gemini (Recommended for Free Testing)](#3-option-a-google-gemini-recommended-for-free-testing)
4. [Option B: OpenAI (Recommended for Production)](#4-option-b-openai-recommended-for-production)
5. [Option C: Ollama (100% Free, Self-Hosted)](#5-option-c-ollama-100-free-self-hosted)
6. [Cost Comparison Summary](#6-cost-comparison-summary)
7. [JWT Secret Key](#7-jwt-secret-key)
8. [Database (PostgreSQL)](#8-database-postgresql)
9. [Frontend Dependencies](#9-frontend-dependencies)
10. [Backend Dependencies](#10-backend-dependencies)
11. [Environment Variable Reference](#11-environment-variable-reference)
12. [Free Testing Strategy — Zero Cost Setup](#12-free-testing-strategy--zero-cost-setup)
13. [Deployment Checklist](#13-deployment-checklist)

---

## 1. System Prerequisites

### 1.1 Required Software

| Prerequisite           | Minimum Version  | Purpose                              | Install Link                                         |
|------------------------|------------------|--------------------------------------|------------------------------------------------------|
| **Docker**             | 20.10+           | Containerized deployment             | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |
| **Docker Compose**     | 2.0+             | Multi-container orchestration        | Bundled with Docker Desktop                          |
| **Git**                | 2.30+            | Version control                      | [git-scm.com](https://git-scm.com/)                 |

### 1.2 Optional (Local Development Only)

| Prerequisite           | Minimum Version  | Purpose                              | Install Link                                         |
|------------------------|------------------|--------------------------------------|------------------------------------------------------|
| **Node.js**            | 20.x LTS         | Frontend build (Next.js 14)          | [nodejs.org](https://nodejs.org/)                    |
| **Python**             | 3.12+            | Backend runtime (FastAPI)            | [python.org](https://python.org/)                    |
| **PostgreSQL Client**  | 16+              | Direct DB access (debugging)         | [postgresql.org](https://www.postgresql.org/)        |

### 1.3 Auto-Provisioned by Docker (No Manual Install Needed)

| Component             | Image                | Purpose                     |
|-----------------------|----------------------|-----------------------------|
| PostgreSQL            | `postgres:16-alpine` | Application database        |
| Nginx                 | `nginx:alpine`       | Reverse proxy & load balancer |
| Python 3.12           | `python:3.12-slim`   | Backend container runtime   |
| Node.js 20            | `node:20-alpine`     | Frontend container runtime  |

> **💡 Key Point:** If you deploy via `docker compose up`, you only need **Docker** and **Docker Compose** installed on your machine. Everything else (PostgreSQL, Nginx, Node.js, Python) runs inside containers automatically.

### 1.4 Verification Commands

```powershell
# ── Verify Docker ──
docker --version                # Expected: Docker version 20.10+
docker compose version          # Expected: Docker Compose version v2.x+

# ── Verify Git ──
git --version                   # Expected: git version 2.30+

# ── Verify Node.js (optional, for local frontend dev) ──
node --version                  # Expected: v20.x.x
npm --version                   # Expected: 10.x.x

# ── Verify Python (optional, for local backend dev) ──
python --version                # Expected: Python 3.12.x
```

---

## 2. AI Provider API Keys — Overview

The VAREX AI Interview Platform uses a **Large Language Model (LLM)** to power the entire interview experience:

| Feature                        | LLM Usage                                           |
|-------------------------------|------------------------------------------------------|
| 🎤 AI Interviewer Introduction | Generates a personalized opening for each candidate  |
| ❓ Question Generation         | Creates contextual questions across 7 interview phases |
| 📊 Answer Evaluation           | Multi-criteria scoring (technical, communication, etc.) |
| 📝 Final Report                | Comprehensive assessment with recommendation         |
| 📄 Resume Analysis             | Extracts skills and experience for personalized questions |

### Provider Comparison at a Glance

| Provider          | API Key? | Free Tier?              | Quality      | Speed        | Default Model       |
|-------------------|----------|--------------------------|--------------|--------------|---------------------|
| **Google Gemini** | ✅ Yes   | ✅ Generous free tier     | ⭐⭐⭐⭐      | ⚡ Very Fast  | `gemini-2.0-flash`  |
| **OpenAI**        | ✅ Yes   | ❌ Pay-as-you-go only    | ⭐⭐⭐⭐⭐    | ⚡ Fast       | `gpt-4o`            |
| **Ollama**        | ❌ No    | ✅ Completely free        | ⭐⭐⭐–⭐⭐⭐⭐ | 🐢 Varies    | `llama3.1`          |

> **You only need ONE provider configured.** Set `AI_PROVIDER` in your `.env` file to choose.

---

## 3. Option A: Google Gemini (Recommended for Free Testing)

### 3.1 How to Create a Gemini API Key

#### Step 1 — Open Google AI Studio
- Navigate to: **https://aistudio.google.com/apikey**
- Sign in with any Google account (personal Gmail works)
- **No credit card required**

#### Step 2 — Create the Key
- Click the **"Create API key"** button
- Select an existing Google Cloud project OR let it auto-create one
- A project will be created with a name like `Generative Language Client`

#### Step 3 — Copy and Save the Key
- Your key will look like: `AIzaSyD-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Copy it immediately** — you can regenerate later, but save it now
- The key is tied to your Google account and the selected project

#### Step 4 — Configure in Your `.env`
```env
AI_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyD-your-actual-key-here
GEMINI_MODEL=gemini-2.0-flash
```

**⏱️ Total Time: ~2 minutes**

### 3.2 Gemini Pricing

#### Free Tier (No Credit Card Required)

| Limit              | Value                  |
|--------------------|------------------------|
| Requests per minute | 15 RPM                |
| Tokens per day      | 1,000,000             |
| Requests per day    | 1,500                 |
| Cost                | **$0.00**              |

#### Pay-as-You-Go (Gemini Flash)

| Item            | Cost                     |
|-----------------|--------------------------|
| Input tokens    | $0.075 per 1M tokens     |
| Output tokens   | $0.30 per 1M tokens      |
| Rate limit      | 2,000 RPM               |

#### Token Usage Estimation per Interview

| Interview Component       | Input Tokens | Output Tokens |
|--------------------------|-------------|---------------|
| Introduction generation   | ~800        | ~300          |
| Per question generation   | ~2,000      | ~500          |
| Per answer evaluation     | ~3,000      | ~800          |
| Final report generation   | ~4,000      | ~1,500        |

| Interview Type     | Total Tokens (approx.) | Free Tier Interviews/Day |
|--------------------|------------------------|--------------------------|
| 5-question (mock free)    | ~30,000         | **~33 interviews/day**  |
| 8-question (mock paid)    | ~50,000         | **~20 interviews/day**  |
| 12-question (enterprise)  | ~80,000         | **~12 interviews/day**  |

> **✅ The free tier is more than sufficient for development and testing.**

### 3.3 Available Gemini Models

| Model                  | Speed         | Quality       | Free Tier? | Recommended For           |
|------------------------|---------------|---------------|------------|---------------------------|
| `gemini-2.0-flash`     | ⚡ Very Fast  | ⭐⭐⭐⭐      | ✅ Yes     | **Default — best balance** |
| `gemini-2.0-flash-lite`| ⚡⚡ Fastest  | ⭐⭐⭐        | ✅ Yes     | High volume, lower quality |
| `gemini-2.5-pro`       | 🐢 Slower    | ⭐⭐⭐⭐⭐    | ⚠️ Limited | Maximum quality            |

### 3.4 Gemini API Key Management

```
📍 View all keys:    https://aistudio.google.com/apikey
📍 Delete a key:     Click the trash icon next to the key
📍 Regenerate:       Delete old key → Create new key
📍 Usage dashboard:  https://console.cloud.google.com/apis/dashboard
📍 Quota settings:   https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
```

---

## 4. Option B: OpenAI (Recommended for Production)

### 4.1 How to Create an OpenAI API Key

#### Step 1 — Create an OpenAI Account
- Navigate to: **https://platform.openai.com/signup**
- Sign up with Google, Microsoft, Apple, or email
- Verify your email and phone number

#### Step 2 — Add a Payment Method
- Navigate to: **https://platform.openai.com/account/billing**
- Click **"Add payment method"**
- Enter your credit/debit card details
- Set a **monthly usage limit** (recommended: **$10/month** to start)
- Optionally enable **auto-recharge** with a threshold

> **⚠️ Important:** OpenAI API does NOT have a permanent free tier. However, new accounts may receive **$5–$18** in free credits that expire in ~3 months.

#### Step 3 — Check for Free Credits
- Navigate to: **https://platform.openai.com/settings/organization/billing/overview**
- Look for a **"Credit Balance"** or **"Free Trial"** section
- If credits exist, you can test without paying

#### Step 4 — Create an API Key
- Navigate to: **https://platform.openai.com/api-keys**
- Click **"+ Create new secret key"**
- Set a name: `varex-ai-interview`
- Set permissions:
  - **All** (simplest for testing)
  - Or restrict to **Chat Completions** only (more secure)
- Click **"Create secret key"**

#### Step 5 — Copy and Save the Key
- The key looks like: `sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **⚠️ COPY IT NOW — You will NEVER see this key again**
- Store it in a password manager or secure note

#### Step 6 — Configure in Your `.env`
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_MODEL=gpt-4o
```

**⏱️ Total Time: ~5 minutes**

### 4.2 OpenAI Pricing

#### Model Pricing (as of March 2026)

| Model           | Input Cost (per 1M tokens) | Output Cost (per 1M tokens) | Quality       | Speed        |
|-----------------|----------------------------|-----------------------------|---------------|--------------|
| `gpt-4o`        | $2.50                      | $10.00                      | ⭐⭐⭐⭐⭐    | ⚡ Fast       |
| `gpt-4o-mini`   | $0.15                      | $0.60                       | ⭐⭐⭐⭐      | ⚡⚡ Very Fast |
| `gpt-4.1`       | $2.00                      | $8.00                       | ⭐⭐⭐⭐⭐    | ⚡ Fast       |
| `gpt-4.1-mini`  | $0.40                      | $1.60                       | ⭐⭐⭐⭐      | ⚡⚡ Very Fast |
| `o3-mini`       | $1.10                      | $4.40                       | ⭐⭐⭐⭐⭐    | 🐢 Slower     |

#### Cost Estimation per Interview

| Interview Type           | Model          | Est. Tokens | Est. Cost    |
|--------------------------|----------------|-------------|--------------|
| 5-question mock (free)   | `gpt-4o`       | ~30,000     | **~$0.08**   |
| 8-question mock (paid)   | `gpt-4o`       | ~50,000     | **~$0.13**   |
| 12-question enterprise   | `gpt-4o`       | ~80,000     | **~$0.21**   |
| 5-question mock (free)   | `gpt-4o-mini`  | ~30,000     | **~$0.005**  |
| 8-question mock (paid)   | `gpt-4o-mini`  | ~50,000     | **~$0.008**  |
| 12-question enterprise   | `gpt-4o-mini`  | ~80,000     | **~$0.012**  |

#### Monthly Cost Projections

| Usage Level            | Model         | Interviews/Month | Monthly Cost     |
|------------------------|---------------|-------------------|------------------|
| Light (testing)        | `gpt-4o-mini` | 50                | **~$0.25**       |
| Medium (small team)    | `gpt-4o`      | 200               | **~$16.00**      |
| Heavy (enterprise)     | `gpt-4o`      | 1,000             | **~$130.00**     |
| Budget production      | `gpt-4o-mini` | 1,000             | **~$8.00**       |

> **💡 Pro Tip:** Use `gpt-4o-mini` for mock interviews and `gpt-4o` for enterprise assessments. You can change the model per environment via the `OPENAI_MODEL` environment variable.

### 4.3 OpenAI API Key Management & Security

```
📍 View all keys:      https://platform.openai.com/api-keys
📍 Usage tracking:     https://platform.openai.com/usage
📍 Billing overview:   https://platform.openai.com/settings/organization/billing/overview
📍 Set spending limit: https://platform.openai.com/account/billing/limits
📍 Rate limits:        https://platform.openai.com/settings/organization/limits
```

**Security Best Practices:**
- Set a **monthly spending cap** (e.g., $20) to prevent surprise bills
- Use **project-scoped keys** (starts with `sk-proj-`) instead of user keys
- Rotate keys every 90 days
- Never commit API keys to Git — always use `.env` files
- Add `.env` to `.gitignore`

---

## 5. Option C: Ollama (100% Free, Self-Hosted)

### 5.1 Overview

Ollama runs open-source LLMs **entirely on your local machine**. There are:
- **No API keys** to create
- **No accounts** to register
- **No internet** needed (after initial model download)
- **No costs** — ever

### 5.2 How to Set Up Ollama

#### Step 1 — Install Ollama

| Platform   | Installation Command / Method                        |
|-----------|------------------------------------------------------|
| **Windows** | Download installer from [ollama.com/download](https://ollama.com/download) |
| **macOS**   | `brew install ollama`                               |
| **Linux**   | `curl -fsSL https://ollama.com/install.sh \| sh`    |

#### Step 2 — Start the Ollama Server
```powershell
ollama serve
```
The server starts on **http://localhost:11434** by default.

#### Step 3 — Download a Model
```powershell
# ── Recommended: Llama 3.1 (8B parameters) ──
ollama pull llama3.1          # ~4.7 GB download

# ── Alternative Models ──
ollama pull llama3.2          # 3B params, ~2.0 GB — faster, lighter
ollama pull mistral           # 7B params, ~4.1 GB — good quality
ollama pull phi3              # 3.8B params, ~2.3 GB — Microsoft's model
ollama pull gemma2            # 9B params, ~5.4 GB — Google's model
ollama pull codellama         # 7B params, ~3.8 GB — code-focused
ollama pull deepseek-coder    # 6.7B params, ~3.8 GB — code-focused
```

#### Step 4 — Verify It Works
```powershell
# Quick test
ollama run llama3.1 "Say hello in one sentence"
# Expected: A friendly greeting response

# Check what models are installed
ollama list
```

#### Step 5 — Configure in Your `.env`
```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

> **⚠️ Docker Note:** When your backend runs inside Docker, change the URL:
> ```env
> OLLAMA_BASE_URL=http://host.docker.internal:11434
> ```
> This allows the Docker container to reach Ollama running on your host machine.

**⏱️ Total Time: ~10–15 minutes (including model download)**

### 5.3 Ollama Pricing

| Item                    | Cost           |
|-------------------------|----------------|
| Ollama software         | **$0.00** (MIT license, open source) |
| LLM models              | **$0.00** (open weights)             |
| API requests            | **$0.00** (runs locally)             |
| Monthly subscription    | **$0.00**                            |
| **Total lifetime cost** | **$0.00**                            |

### 5.4 System Requirements for Ollama

| Model Size                | RAM Required | GPU Recommended?         | Response Time (approx.) |
|--------------------------|-------------|---------------------------|------------------------|
| 3B (Llama 3.2, Phi3)    | 8 GB        | No (CPU is OK)            | 3–10 seconds           |
| 7–8B (Llama 3.1, Mistral)| 16 GB      | Yes (NVIDIA 8GB+ VRAM)   | 5–15 sec (GPU) / 30–60 sec (CPU) |
| 13B+ (CodeLlama 13B)    | 32 GB       | Yes (NVIDIA 12GB+ VRAM)  | 10–30 sec (GPU)        |
| 70B (Llama 3.1 70B)     | 64 GB       | Yes (NVIDIA 24GB+ VRAM)  | 30–120 sec (GPU)       |

> **💡 Without a dedicated GPU**, stick to 3B models (`llama3.2`, `phi3`) for acceptable performance during testing.

### 5.5 Ollama Model Comparison for Interviews

| Model             | Params | Interview Quality | Code Questions | Behavioral Qs | Speed   |
|-------------------|--------|-------------------|----------------|---------------|---------|
| `llama3.1`        | 8B     | ⭐⭐⭐⭐          | ⭐⭐⭐⭐       | ⭐⭐⭐⭐      | Medium  |
| `llama3.2`        | 3B     | ⭐⭐⭐            | ⭐⭐⭐         | ⭐⭐⭐        | Fast    |
| `mistral`         | 7B     | ⭐⭐⭐⭐          | ⭐⭐⭐         | ⭐⭐⭐⭐      | Medium  |
| `phi3`            | 3.8B   | ⭐⭐⭐            | ⭐⭐⭐⭐       | ⭐⭐⭐        | Fast    |
| `gemma2`          | 9B     | ⭐⭐⭐⭐          | ⭐⭐⭐⭐       | ⭐⭐⭐⭐      | Medium  |
| `deepseek-coder`  | 6.7B   | ⭐⭐⭐            | ⭐⭐⭐⭐⭐     | ⭐⭐          | Medium  |

---

## 6. Cost Comparison Summary

### Per-Interview Cost

| Provider                | 5 Questions (Mock Free) | 8 Questions (Mock Paid) | 12 Questions (Enterprise) |
|------------------------|------------------------|------------------------|--------------------------|
| **Gemini (Free Tier)**  | **$0.00**              | **$0.00**              | **$0.00**                |
| **Gemini (Paid)**       | ~$0.003                | ~$0.005                | ~$0.008                  |
| **OpenAI (GPT-4o)**     | ~$0.08                 | ~$0.13                 | ~$0.21                   |
| **OpenAI (GPT-4o-mini)**| ~$0.005                | ~$0.008                | ~$0.012                  |
| **Ollama**              | **$0.00**              | **$0.00**              | **$0.00**                |

### Setup Cost

| Provider         | Account Creation | API Key | Payment Method | Minimum Deposit | Total Setup Cost |
|------------------|-----------------|---------|----------------|-----------------|------------------|
| **Google Gemini** | Free            | Free    | Not required   | $0              | **$0.00**        |
| **OpenAI**        | Free            | Free    | Required       | ~$5             | **~$5.00**       |
| **Ollama**        | Not needed      | None    | Not required   | $0              | **$0.00**        |

### Recommendation Matrix

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  🥇 FOR FREE TESTING & DEVELOPMENT:                               │
│     → Google Gemini (Free Tier)                                    │
│     → 2 minutes setup, no credit card, excellent quality           │
│     → 33+ interviews/day at zero cost                              │
│                                                                    │
│  🥈 FOR OFFLINE / AIR-GAPPED / PRIVACY:                           │
│     → Ollama (Self-Hosted)                                         │
│     → 100% free forever, no internet needed, complete data privacy │
│     → Requires 8-16GB RAM for decent performance                   │
│                                                                    │
│  🥉 FOR PRODUCTION AT SCALE:                                      │
│     → OpenAI GPT-4o                                                │
│     → Highest quality, most reliable, best documentation           │
│     → ~$0.08–$0.21 per interview                                   │
│                                                                    │
│  💰 BUDGET PRODUCTION:                                             │
│     → OpenAI GPT-4o-mini                                           │
│     → 90% of the quality at 5% of the cost                        │
│     → ~$0.005–$0.012 per interview                                 │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 7. JWT Secret Key

### 7.1 What Is It?

The platform uses **JWT (JSON Web Tokens)** for user authentication. Every token is signed with the `SECRET_KEY`. This key must be:
- **Random** — at least 64 characters
- **Secret** — never shared or committed to Git
- **Consistent** — changing it invalidates all active user sessions

### 7.2 How to Generate a Secure Key

Choose any one method:

```powershell
# ── Method 1: Python (recommended) ──
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Output example: dK8x_mP2qR7vNhJwYzT3cFaL9sBnXeU5gW1iO6tA4kEmZpC...

# ── Method 2: PowerShell ──
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
# Output example: aK7mXr2pQ9sLdH5jBvN8cYwF1gT6eI3oZ4uR0xW...

# ── Method 3: OpenSSL (if installed) ──
openssl rand -base64 64
# Output example: Qm9vdC1zZWNyZXQta2V5LWZvci1wcm9kdWN0aW9u...

# ── Method 4: Node.js ──
node -e "console.log(require('crypto').randomBytes(64).toString('base64url'))"
```

### 7.3 Configure in `.env`

```env
SECRET_KEY=paste-your-generated-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440    # 24 hours (adjust as needed)
```

### 7.4 Security Rules

| Rule | Details |
|------|---------|
| ❌ Never use the default | `dev-secret-key-change-me-in-production` is NOT safe |
| ❌ Never commit to Git | Add `.env` to `.gitignore` |
| ❌ Never share publicly | Treat it like a password |
| ✅ Use 64+ characters | Longer = more secure |
| ✅ Regenerate if compromised | All users will need to re-login |
| ✅ Use different keys per environment | Dev, staging, production should each have unique keys |

### 7.5 Cost: **$0.00** (self-generated)

---

## 8. Database (PostgreSQL)

### 8.1 Docker Setup (Automatic)

The database is **automatically provisioned** by Docker Compose — no manual installation needed.

**From `docker-compose.yml`:**
```yaml
ai_interview_db:
  image: postgres:16-alpine
  container_name: ai_interview_db
  restart: unless-stopped
  environment:
    POSTGRES_DB: ${AI_INTERVIEW_DB:-ai_interview_db}
    POSTGRES_USER: ${AI_INTERVIEW_DB_USER:-ai_interview}
    POSTGRES_PASSWORD: ${AI_INTERVIEW_DB_PASSWORD:-ai_interview_password}
  volumes:
    - ai_interview_postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${AI_INTERVIEW_DB_USER:-ai_interview}"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### 8.2 Default Credentials

```env
AI_INTERVIEW_DB=ai_interview_db
AI_INTERVIEW_DB_USER=ai_interview
AI_INTERVIEW_DB_PASSWORD=ai_interview_password
AI_INTERVIEW_DATABASE_URL=postgresql+psycopg2://ai_interview:ai_interview_password@ai_interview_db:5432/ai_interview_db
```

### 8.3 Production Security

For production deployments, **change the default database password**:

```powershell
# Generate a secure database password
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Then update your `.env`:
```env
AI_INTERVIEW_DB_PASSWORD=your-secure-generated-password
AI_INTERVIEW_DATABASE_URL=postgresql+psycopg2://ai_interview:your-secure-generated-password@ai_interview_db:5432/ai_interview_db
```

### 8.4 Data Persistence

The database uses a Docker named volume: `ai_interview_postgres_data`
- Data **persists** across container restarts and `docker compose down`
- Data is **deleted** only if you run `docker compose down -v` (the `-v` flag removes volumes)

### 8.5 Cost: **$0.00** (runs in Docker container)

---

## 9. Frontend Dependencies

### 9.1 Technology Stack

| Package          | Version  | Purpose                       | License |
|------------------|----------|-------------------------------|---------|
| `next`           | 14.1.0   | React framework (SSR/SSG)     | MIT     |
| `react`          | 18.2.0   | UI component library          | MIT     |
| `react-dom`      | 18.2.0   | React DOM renderer            | MIT     |
| `tailwindcss`    | ^3.4.1   | Utility-first CSS framework   | MIT     |
| `postcss`        | ^8.5.6   | CSS post-processing           | MIT     |
| `autoprefixer`   | ^10.4.27 | Browser prefix automation     | MIT     |
| `typescript`     | 5.3.3    | Type safety                   | Apache-2.0 |

### 9.2 Install Command (Local Dev)

```powershell
cd ai-interview-app/frontend
npm install
```

### 9.3 Build & Run Locally

```powershell
# Development mode (hot reload)
npm run dev          # Starts on http://localhost:3000

# Production build
npm run build
npm run start        # Starts on http://localhost:3000
```

### 9.4 Cost: **$0.00** (all packages are open source)

---

## 10. Backend Dependencies

### 10.1 Core Framework

| Package              | Version  | Purpose                          | License |
|----------------------|----------|----------------------------------|---------|
| `fastapi`            | 0.111.0  | Async web framework              | MIT     |
| `uvicorn[standard]`  | 0.30.1   | ASGI server                      | BSD     |
| `pydantic`           | 2.8.2    | Data validation & serialization  | MIT     |
| `pydantic-settings`  | 2.3.4    | Environment config management    | MIT     |

### 10.2 Database

| Package              | Version  | Purpose                          | License |
|----------------------|----------|----------------------------------|---------|
| `sqlalchemy`         | 2.0.31   | SQL ORM (Object Relational Mapper) | MIT   |
| `psycopg2-binary`    | 2.9.9    | PostgreSQL database driver       | LGPL    |

### 10.3 Authentication

| Package                      | Version | Purpose                    | License |
|------------------------------|---------|----------------------------|---------|
| `python-jose[cryptography]`  | 3.3.0   | JWT token creation & verification | MIT |
| `passlib[bcrypt]`            | 1.7.4   | Password hashing           | BSD     |
| `bcrypt`                     | 4.1.3   | Bcrypt hash algorithm      | Apache-2.0 |
| `email-validator`            | 2.2.0   | Email format validation    | CC0     |

### 10.4 AI / LLM Providers

| Package                | Version | Purpose                       | License      |
|------------------------|---------|-------------------------------|--------------|
| `openai`               | 1.35.10 | OpenAI GPT API client         | Apache-2.0   |
| `google-generativeai`  | 0.7.2   | Google Gemini API client       | Apache-2.0   |
| `httpx`                | 0.27.0  | Async HTTP client (for Ollama) | BSD          |

### 10.5 File Processing

| Package          | Version | Purpose                    | License |
|------------------|---------|----------------------------|---------|
| `python-multipart`| 0.0.9  | File upload handling        | Apache-2.0 |
| `pymupdf`        | 1.24.5  | PDF resume parsing          | AGPL / Commercial |
| `python-docx`    | 1.1.2   | DOCX resume parsing         | MIT     |

### 10.6 Proctor Agent (Optional — Desktop Client)

| Package    | Purpose                    | Install Command       |
|-----------|----------------------------|-----------------------|
| `psutil`  | Process & system monitoring | `pip install psutil`  |
| `requests`| HTTP heartbeat to backend  | `pip install requests` |

### 10.7 Install Command (Local Dev)

```powershell
cd ai-interview-app/backend
pip install -r requirements.txt

# For proctor agent (optional)
pip install psutil requests
```

### 10.8 Cost: **$0.00** (all packages are open source)

---

## 11. Environment Variable Reference

### Complete `.env` File with Documentation

```env
# ═══════════════════════════════════════════════════════════════
#  VAREX AI Interview Platform — Environment Configuration
# ═══════════════════════════════════════════════════════════════

# ────────────────────────────────────────────────────────────────
#  DATABASE
# ────────────────────────────────────────────────────────────────
AI_INTERVIEW_DB=ai_interview_db                          # Database name
AI_INTERVIEW_DB_USER=ai_interview                        # Database username
AI_INTERVIEW_DB_PASSWORD=ai_interview_password           # ⚠️ CHANGE for production!
AI_INTERVIEW_DATABASE_URL=postgresql+psycopg2://ai_interview:ai_interview_password@ai_interview_db:5432/ai_interview_db
AI_INTERVIEW_ALLOWED_ORIGINS=http://localhost:3010,http://localhost:3000
# ^ Comma-separated list of allowed frontend origins (CORS)

# ────────────────────────────────────────────────────────────────
#  JWT AUTHENTICATION
# ────────────────────────────────────────────────────────────────
SECRET_KEY=change-this-to-a-strong-random-secret         # ⚠️ MUST generate a real key!
ACCESS_TOKEN_EXPIRE_MINUTES=1440                         # Session duration: 1440 = 24 hours

# ────────────────────────────────────────────────────────────────
#  AI PROVIDER — Choose ONE: gemini | openai | ollama
# ────────────────────────────────────────────────────────────────
AI_PROVIDER=gemini

# ── Google Gemini ──
GEMINI_API_KEY=your-gemini-api-key-here                  # Get from aistudio.google.com/apikey
GEMINI_MODEL=gemini-2.0-flash                            # Options: gemini-2.0-flash, gemini-2.0-flash-lite, gemini-2.5-pro

# ── OpenAI ──
OPENAI_API_KEY=sk-your-openai-key-here                   # Get from platform.openai.com/api-keys
OPENAI_MODEL=gpt-4o                                      # Options: gpt-4o, gpt-4o-mini, gpt-4.1, gpt-4.1-mini

# ── Ollama (Self-Hosted) ──
OLLAMA_BASE_URL=http://localhost:11434                    # Use http://host.docker.internal:11434 inside Docker
OLLAMA_MODEL=llama3.1                                    # Options: llama3.1, llama3.2, mistral, phi3, gemma2

# ────────────────────────────────────────────────────────────────
#  RESUME UPLOAD
# ────────────────────────────────────────────────────────────────
MAX_RESUME_SIZE_MB=5                                     # Max file size: PDF or DOCX

# ────────────────────────────────────────────────────────────────
#  INTERVIEW TIMER
# ────────────────────────────────────────────────────────────────
DEFAULT_TOTAL_TIME_SECONDS=2700                          # 45 minutes total interview
DEFAULT_QUESTION_TIME_SECONDS=300                        # 5 minutes per question

# Timer by difficulty level (hardcoded in interview_timer.py):
#   junior:    30 min total, 4 min/question
#   mid:       45 min total, 5 min/question
#   senior:    60 min total, 6 min/question
#   architect: 75 min total, 7 min/question

# ────────────────────────────────────────────────────────────────
#  ANTI-CHEAT
# ────────────────────────────────────────────────────────────────
MAX_TAB_SWITCHES_BEFORE_FLAG=3                           # Tab switches before flagging

# ────────────────────────────────────────────────────────────────
#  QUESTION COUNTS PER MODE
# ────────────────────────────────────────────────────────────────
QUESTIONS_MOCK_FREE=5                                    # Free mock interview
QUESTIONS_MOCK_PAID=8                                    # Paid mock interview
QUESTIONS_ENTERPRISE=12                                  # Enterprise assessment
```

---

## 12. Free Testing Strategy — Zero Cost Setup

### 🎯 Method 1: Gemini Free Tier (Easiest — Recommended)

```
Total Cost:   $0.00
Setup Time:   ~5 minutes
Quality:      ⭐⭐⭐⭐ (Excellent)
Internet:     Required
Credit Card:  NOT required
```

**Steps:**
```powershell
# 1. Get a free Gemini API key (2 min)
#    → Go to: https://aistudio.google.com/apikey
#    → Click "Create API key"
#    → Copy the key

# 2. Set up environment
cd ai-interview-app
copy .env.example .env

# 3. Edit .env — set these values:
#    AI_PROVIDER=gemini
#    GEMINI_API_KEY=AIzaSyD-your-actual-key
#    SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(64))">

# 4. Start the platform
docker compose up --build -d

# 5. Open in browser
#    → http://localhost:3010
```

### 🎯 Method 2: Ollama (Completely Offline)

```
Total Cost:   $0.00
Setup Time:   ~15 minutes (includes model download)
Quality:      ⭐⭐⭐ (Good for testing)
Internet:     Only for initial setup
Credit Card:  NOT required
```

**Steps:**
```powershell
# 1. Install Ollama
#    → Download from: https://ollama.com/download

# 2. Download a model (one-time)
ollama pull llama3.1            # ~4.7 GB download
# OR for faster/lighter:
ollama pull llama3.2            # ~2.0 GB download

# 3. Start Ollama server
ollama serve

# 4. Set up environment
cd ai-interview-app
copy .env.example .env

# 5. Edit .env — set these values:
#    AI_PROVIDER=ollama
#    OLLAMA_BASE_URL=http://host.docker.internal:11434
#    OLLAMA_MODEL=llama3.1
#    SECRET_KEY=<generate a key>

# 6. Start the platform
docker compose up --build -d

# 7. Open in browser
#    → http://localhost:3010
```

### 🎯 Method 3: OpenAI Free Credits

```
Total Cost:   $0.00 (only if new account has credits)
Setup Time:   ~5 minutes
Quality:      ⭐⭐⭐⭐⭐ (Best)
Internet:     Required
Credit Card:  May be required
```

**Steps:**
```powershell
# 1. Create OpenAI account
#    → Go to: https://platform.openai.com/signup

# 2. Check for free credits
#    → Go to: https://platform.openai.com/settings/organization/billing/overview
#    → Look for "Credit Balance" section

# 3. If credits exist, create API key
#    → Go to: https://platform.openai.com/api-keys
#    → Click "+ Create new secret key"
#    → Copy the key

# 4. Set up environment and use gpt-4o-mini (cheapest model)
#    AI_PROVIDER=openai
#    OPENAI_API_KEY=sk-proj-your-key
#    OPENAI_MODEL=gpt-4o-mini        # ← Use mini to stretch free credits

# 5. Start and test
docker compose up --build -d
```

---

## 13. Deployment Checklist

### ✅ Pre-Deployment

| #  | Task                                              | Required? | Status |
|----|---------------------------------------------------|-----------|--------|
| 1  | Docker & Docker Compose installed                 | ✅ Yes    | ☐     |
| 2  | Git installed                                     | ✅ Yes    | ☐     |
| 3  | Repository cloned                                 | ✅ Yes    | ☐     |
| 4  | `.env` file created from `.env.example`           | ✅ Yes    | ☐     |
| 5  | AI Provider chosen (`gemini` / `openai` / `ollama`) | ✅ Yes  | ☐     |
| 6  | API key created and added to `.env`               | ✅ Yes    | ☐     |
| 7  | JWT `SECRET_KEY` generated (not the default!)     | ✅ Yes    | ☐     |
| 8  | Database password changed (production only)       | ⚠️ Prod   | ☐     |
| 9  | `ALLOWED_ORIGINS` set for your domain (production)| ⚠️ Prod   | ☐     |
| 10 | Ollama server running (if using Ollama)           | ⚠️ If Ollama | ☐  |

### ✅ Deployment

| #  | Task                                              | Command / Action                              |
|----|---------------------------------------------------|-----------------------------------------------|
| 11 | Build and start all containers                    | `docker compose up --build -d`                |
| 12 | Verify all 4 containers are running              | `docker compose ps`                            |
| 13 | Check backend logs for errors                    | `docker compose logs ai_interview_backend --tail 50` |
| 14 | Check frontend logs for errors                   | `docker compose logs ai_interview_frontend --tail 50` |

### ✅ Smoke Test

| #  | Task                                              | Expected Result                               |
|----|---------------------------------------------------|-----------------------------------------------|
| 15 | Open `http://localhost:3010`                     | Frontend loads                                 |
| 16 | Check `http://localhost:3010/health`             | Returns `200 OK`                               |
| 17 | Create a new user account                        | Account created successfully                   |
| 18 | Log in with the new account                      | JWT token received, dashboard loads            |
| 19 | Start a mock interview                           | AI introduction is generated                   |
| 20 | Answer a question                                | AI evaluates and shows score                   |
| 21 | Complete the interview                           | Final report is generated                      |

### Quick Smoke Test Commands

```powershell
# Start everything
docker compose up --build -d

# Verify containers
docker compose ps
# Expected: 4 containers (db, backend, frontend, web) all "Up"

# Check health
curl http://localhost:3010/health
# Expected: {"status":"healthy"} or 200 OK

# Check logs if something fails
docker compose logs ai_interview_backend --tail 100
docker compose logs ai_interview_frontend --tail 50
docker compose logs ai_interview_db --tail 50

# Stop everything
docker compose down

# Stop and remove all data (⚠️ deletes database!)
docker compose down -v
```

---

## Quick Reference Card

```
╔═════════════════════════════════════════════════════════════════╗
║              VAREX AI Interview Platform                        ║
║              Prerequisites Quick Reference                      ║
╠═════════════════════════════════════════════════════════════════╣
║                                                                 ║
║  🟢 FASTEST FREE SETUP (5 min):                                ║
║     1. Get Gemini key → aistudio.google.com/apikey              ║
║     2. copy .env.example .env                                   ║
║     3. Set GEMINI_API_KEY + SECRET_KEY in .env                  ║
║     4. docker compose up --build -d                             ║
║     5. Open http://localhost:3010                               ║
║                                                                 ║
║  🔑 KEYS NEEDED:                                                ║
║     • AI Provider key (Gemini OR OpenAI OR none for Ollama)     ║
║     • JWT Secret Key (self-generated, free)                     ║
║                                                                 ║
║  💰 MINIMUM COST:   $0.00 (Gemini free tier or Ollama)          ║
║  💰 PRODUCTION EST: ~$0.08–$0.21 per interview (OpenAI GPT-4o) ║
║                                                                 ║
║  📦 SERVICES (4 containers):                                    ║
║     Backend  → FastAPI (Python 3.12)                            ║
║     Frontend → Next.js 14 (Node 20)                             ║
║     Database → PostgreSQL 16                                    ║
║     Proxy    → Nginx Alpine                                     ║
║                                                                 ║
║  🌐 PORTS:                                                      ║
║     http://localhost:3010  → Frontend (via Nginx)               ║
║     :8010 (internal)       → Backend API                        ║
║     :5432 (internal)       → PostgreSQL                         ║
║     :11434 (host)          → Ollama (if used)                   ║
║                                                                 ║
╚═════════════════════════════════════════════════════════════════╝
```

---

> **Last Updated:** March 1, 2026
> **Platform Version:** VAREX AI Interview Platform v1.0
> **Document:** Prerequisites & Setup Guide



🛠️ VAREX AI Interview Platform — Prerequisites & API Keys Guide
Complete reference for setting up all dependencies, creating API keys, understanding costs, and testing for FREE.

📑 Table of Contents
System Prerequisites
AI Provider API Keys — Overview
Option A: Google Gemini (Recommended for Free Testing)
Option B: OpenAI (Recommended for Production)
Option C: Ollama (100% Free, Self-Hosted)
Cost Comparison Summary
JWT Secret Key
Database (PostgreSQL)
Frontend Dependencies
Backend Dependencies
Environment Variable Reference
Free Testing Strategy
Deployment Checklist
1. System Prerequisites
Prerequisite	Minimum Version	Purpose	Install Link
Docker	20.10+	Containerized deployment	docker.com
Docker Compose	2.0+	Multi-container orchestration	Bundled with Docker Desktop
Node.js	20.x LTS	Frontend build (Next.js 14)	nodejs.org
Python	3.12+	Backend runtime (FastAPI)	python.org
Git	2.30+	Version control	git-scm.com
PostgreSQL (auto)	16 Alpine	Database (auto-provisioned by Docker)	N/A (Docker image)
Nginx (auto)	Alpine	Reverse proxy (auto-provisioned)	N/A (Docker image)
NOTE

If you run via docker-compose up, you only need Docker and Docker Compose installed. PostgreSQL, Nginx, Node.js, and Python are all handled inside containers.

Quick Check Commands
powershell
# Verify Docker
docker --version          # Expected: Docker version 20.10+
docker compose version    # Expected: Docker Compose version v2.x+
# Verify Node.js (only for local frontend dev)
node --version            # Expected: v20.x.x
npm --version             # Expected: 10.x.x
# Verify Python (only for local backend dev)
python --version          # Expected: Python 3.12.x
# Verify Git
git --version             # Expected: git version 2.30+
2. AI Provider API Keys — Overview
The VAREX AI Interview Platform uses an LLM (Large Language Model) to power:

🎤 AI Interviewer introduction generation
❓ Contextual question generation (7-phase flow)
📊 Multi-criteria answer evaluation
📝 Final assessment report generation
📄 Resume parsing & analysis
You need exactly ONE of these three providers configured:

Provider	API Key Needed?	Free Tier?	Best For	Default Model
Google Gemini	✅ Yes	✅ Generous free tier	Development & Testing	gemini-2.0-flash
OpenAI	✅ Yes	❌ Pay-as-you-go only	Production	gpt-4o
Ollama	❌ No	✅ Completely free	Offline / Air-gapped	llama3.1
3. Option A: Google Gemini (Recommended for Free Testing)
🔑 How to Create a Gemini API Key
Step-by-Step:
Go to Google AI Studio

URL: https://aistudio.google.com/apikey
Sign in with your Google account

Any personal Gmail account works
No credit card required for the free tier
Click "Create API Key"

You'll see a button labeled "Create API key"
Select an existing Google Cloud project OR let it create one automatically
Copy the key

The key looks like: AIzaSyD...xxxxx
Save it immediately — you won't be able to see it again unless you regenerate
Set in your 
.env
 file:

env
AI_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyD...your-actual-key-here
GEMINI_MODEL=gemini-2.0-flash
⏱️ Time Required: ~2 minutes
💰 Gemini Pricing (as of March 2026)
Plan	Price	Rate Limits	Notes
Free Tier	$0.00	15 RPM (requests/min), 1M tokens/day, 1,500 requests/day	✅ Perfect for development & testing
Pay-as-you-go	$0.075 / 1M input tokens, $0.30 / 1M output tokens (Flash)	2,000 RPM	Production scale
TIP

For testing, the free tier is MORE than enough. A single interview session uses approximately:

~2,000 input tokens per question generation
~500 output tokens per question
~3,000 input tokens per answer evaluation
~800 output tokens per evaluation
A complete 5-question interview ≈ 30,000 tokens total → You can run ~33 full interviews per day on the free tier.

Available Gemini Models
Model	Speed	Quality	Recommended For
gemini-2.0-flash	⚡ Very fast	⭐⭐⭐⭐	Default — Best balance
gemini-2.0-flash-lite	⚡⚡ Fastest	⭐⭐⭐	High volume, lower cost
gemini-2.5-pro	🐢 Slower	⭐⭐⭐⭐⭐	Maximum quality (paid only)
4. Option B: OpenAI (Recommended for Production)
🔑 How to Create an OpenAI API Key
Step-by-Step:
Create an OpenAI Account

URL: https://platform.openai.com/signup
Sign up with Google, Microsoft, or email
Add billing / payment method

Go to: https://platform.openai.com/account/billing
Click "Add payment method"
Add a credit card or debit card
Set a monthly usage limit (recommended: start with $10/month)
Create an API key

Go to: https://platform.openai.com/api-keys
Click "+ Create new secret key"
Name: varex-ai-interview (or any label)
Permissions: All (or restrict to Chat Completions only)
Click "Create secret key"
Copy the key

The key looks like: sk-proj-xxxxx...xxxxx
⚠️ SAVE IT NOW — you will NOT see it again
Set in your 
.env
 file:

env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxx...your-actual-key
OPENAI_MODEL=gpt-4o
⏱️ Time Required: ~5 minutes
CAUTION

OpenAI does NOT have a free tier for API usage. You MUST add a payment method. New accounts sometimes get a small credit ($5–$18) that expires in 3 months — check your billing dashboard.

💰 OpenAI Pricing (as of March 2026)
Model	Input Cost	Output Cost	Quality	Speed
gpt-4o	$2.50 / 1M tokens	$10.00 / 1M tokens	⭐⭐⭐⭐⭐	Fast
gpt-4o-mini	$0.15 / 1M tokens	$0.60 / 1M tokens	⭐⭐⭐⭐	Very Fast
gpt-4.1	$2.00 / 1M tokens	$8.00 / 1M tokens	⭐⭐⭐⭐⭐	Fast
gpt-4.1-mini	$0.40 / 1M tokens	$1.60 / 1M tokens	⭐⭐⭐⭐	Very Fast
Cost Estimation per Interview
Scenario	Model	Est. Tokens	Est. Cost
5-question mock (free)	gpt-4o	~30K	~$0.08
8-question mock (paid)	gpt-4o	~50K	~$0.13
12-question enterprise	gpt-4o	~80K	~$0.21
5-question mock (free)	gpt-4o-mini	~30K	~$0.005
12-question enterprise	gpt-4o-mini	~80K	~$0.012
TIP

Budget-Friendly Production Tip: Use gpt-4o-mini for mock interviews and gpt-4o for enterprise interviews. Change the model per environment via the OPENAI_MODEL env variable.

OpenAI Free Credits Check
1. Go to: https://platform.openai.com/settings/organization/billing/overview
2. Look for "Credit Balance" section
3. New accounts may have $5-$18 free credit (expires in ~3 months)
4. If you see credit → you can test without paying anything
5. Option C: Ollama (100% Free, Self-Hosted)
🔑 No API Key Needed!
Ollama runs LLMs locally on your machine. Zero cost, zero API keys, complete privacy.

Step-by-Step Setup:
Install Ollama

URL: https://ollama.com/download
Windows: Download and run the installer
Mac: brew install ollama
Linux: curl -fsSL https://ollama.com/install.sh | sh
Start the Ollama server

powershell
ollama serve
The server starts on http://localhost:11434

Download a model

powershell
# Recommended: Llama 3.1 (8B parameters, ~4.7GB download)
ollama pull llama3.1
# Alternative lighter models:
ollama pull llama3.2        # 3B params, ~2GB — faster, lighter
ollama pull mistral         # 7B params, ~4.1GB — good quality
ollama pull phi3            # 3.8B params, ~2.3GB — Microsoft's model
ollama pull gemma2          # 9B params, ~5.4GB — Google's model
Set in your 
.env
 file:

env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
IMPORTANT

When running inside Docker, change OLLAMA_BASE_URL to http://host.docker.internal:11434 so the container can reach Ollama running on your host machine.

⏱️ Time Required: ~10-15 minutes (depending on download speed)
💰 Ollama Pricing
Item	Cost
Ollama software	FREE (open source)
Models (Llama 3.1, Mistral, etc.)	FREE (open weights)
API calls	FREE (runs locally)
Total	$0.00 forever
System Requirements for Ollama
Model Size	RAM Required	GPU Recommended?	Quality
3B (Llama 3.2, Phi3)	8 GB	No (CPU OK)	⭐⭐⭐
7-8B (Llama 3.1, Mistral)	16 GB	Yes (NVIDIA 8GB+)	⭐⭐⭐⭐
13B+ (CodeLlama 13B)	32 GB	Yes (NVIDIA 12GB+)	⭐⭐⭐⭐⭐
WARNING

Without a GPU, larger models (8B+) will be very slow (30-60 seconds per response). For testing without a GPU, use llama3.2 (3B) or phi3 (3.8B) which can run on CPU in 5-10 seconds.

6. Cost Comparison Summary
Provider	Setup Cost	Per Interview (5Q)	Per Interview (12Q)	Free Tier?	Best For
Gemini (Flash)	$0	$0.00 (free tier)	$0.00 (free tier)	✅ 1,500 req/day	Dev & Testing
OpenAI (GPT-4o)	$5 minimum load	~$0.08	~$0.21	❌	Production
OpenAI (GPT-4o-mini)	$5 minimum load	~$0.005	~$0.012	❌	Budget Production
Ollama (Llama 3.1)	$0 (~5GB disk)	$0.00	$0.00	✅ Always free	Offline / Privacy
🏆 Recommendation for Testing:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  🥇 BEST FOR FREE TESTING:  Google Gemini (Free Tier)       │
│     → 2 minutes setup, no credit card, excellent quality    │
│                                                             │
│  🥈 BEST FOR OFFLINE:       Ollama                          │
│     → 100% free, no internet needed, complete privacy       │
│                                                             │
│  🥉 BEST FOR PRODUCTION:    OpenAI GPT-4o                   │
│     → Highest quality, reliable, well-documented            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
7. JWT Secret Key
The platform uses JWT (JSON Web Tokens) for authentication. You need a strong random secret key.

How to Generate a Secure Secret Key
powershell
# Option 1: Python (recommended)
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Option 2: PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
# Option 3: OpenSSL (if installed)
openssl rand -base64 64
Example output: dK8x_mP2qR7vNhJwYzT3cFaL9sBnXeU5gW1iO6tA4kE...

Set in your 
.env
:
env
SECRET_KEY=paste-your-generated-key-here
CAUTION

NEVER use the default dev-secret-key-change-me-in-production in production
NEVER commit your secret key to Git
Changing the secret key will invalidate all existing user sessions
Cost: $0.00 (self-generated)
8. Database (PostgreSQL)
Docker Setup (Automatic — No Action Needed)
The database is automatically provisioned by Docker Compose:

yaml
# From docker-compose.yml — already configured!
ai_interview_db:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: ai_interview_db
    POSTGRES_USER: ai_interview
    POSTGRES_PASSWORD: ai_interview_password
Default Credentials (
.env
):
env
AI_INTERVIEW_DB=ai_interview_db
AI_INTERVIEW_DB_USER=ai_interview
AI_INTERVIEW_DB_PASSWORD=ai_interview_password
AI_INTERVIEW_DATABASE_URL=postgresql+psycopg2://ai_interview:ai_interview_password@ai_interview_db:5432/ai_interview_db
IMPORTANT

For production, change the default database password to a strong random string!

Cost: $0.00 (runs in Docker container)
9. Frontend Dependencies
Package	Version	Purpose
next	14.1.0	React framework (SSR/SSG)
react	18.2.0	UI library
react-dom	18.2.0	React DOM renderer
tailwindcss	^3.4.1	Utility CSS framework
postcss	^8.5.6	CSS processing
autoprefixer	^10.4.27	Browser prefix automation
typescript	5.3.3	Type safety
Install (local development):
powershell
cd ai-interview-app/frontend
npm install
Cost: $0.00 (all open source)
10. Backend Dependencies
Package	Version	Purpose
fastapi	0.111.0	Web framework
uvicorn[standard]	0.30.1	ASGI server
sqlalchemy	2.0.31	Database ORM
psycopg2-binary	2.9.9	PostgreSQL driver
pydantic	2.8.2	Data validation
pydantic-settings	2.3.4	Environment config management
email-validator	2.2.0	Email validation
python-multipart	0.0.9	File upload handling
python-jose[cryptography]	3.3.0	JWT token handling
passlib[bcrypt]	1.7.4	Password hashing
bcrypt	4.1.3	Bcrypt algorithm
openai	1.35.10	OpenAI API client
google-generativeai	0.7.2	Google Gemini API client
httpx	0.27.0	Async HTTP client (Ollama)
pymupdf	1.24.5	PDF resume parsing
python-docx	1.1.2	DOCX resume parsing
Install (local development):
powershell
cd ai-interview-app/backend
pip install -r requirements.txt
Proctor Agent Additional Dependencies:
powershell
pip install psutil requests
Cost: $0.00 (all open source)
11. Environment Variable Reference
Below is every environment variable used by the platform with its purpose and default:

env
# ══════════════════════════════════════════════════════════
#  COMPLETE .env REFERENCE
# ══════════════════════════════════════════════════════════
# ── Database ─────────────────────────────────────────────
AI_INTERVIEW_DB=ai_interview_db                    # Database name
AI_INTERVIEW_DB_USER=ai_interview                  # DB username
AI_INTERVIEW_DB_PASSWORD=ai_interview_password     # ⚠️ CHANGE in production!
AI_INTERVIEW_DATABASE_URL=postgresql+psycopg2://ai_interview:ai_interview_password@ai_interview_db:5432/ai_interview_db
AI_INTERVIEW_ALLOWED_ORIGINS=http://localhost:3010,http://localhost:3000
# ── JWT Authentication ──────────────────────────────────
SECRET_KEY=change-this-to-a-strong-random-secret   # ⚠️ MUST change!
ACCESS_TOKEN_EXPIRE_MINUTES=1440                   # 24 hours
# ── AI Provider ─────────────────────────────────────────
AI_PROVIDER=gemini                                 # gemini | openai | ollama
# Google Gemini
GEMINI_API_KEY=your-gemini-api-key-here            # From aistudio.google.com
GEMINI_MODEL=gemini-2.0-flash                      # Model to use
# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here             # From platform.openai.com
OPENAI_MODEL=gpt-4o                                # Model to use
# Ollama (self-hosted)
OLLAMA_BASE_URL=http://localhost:11434              # Ollama server URL
OLLAMA_MODEL=llama3.1                              # Model to use
# ── Resume Upload ───────────────────────────────────────
MAX_RESUME_SIZE_MB=5                               # Max PDF/DOCX size
# ── Interview Timer ─────────────────────────────────────
DEFAULT_TOTAL_TIME_SECONDS=2700                    # 45 min total
DEFAULT_QUESTION_TIME_SECONDS=300                  # 5 min per question
# ── Anti-Cheat ──────────────────────────────────────────
MAX_TAB_SWITCHES_BEFORE_FLAG=3                     # Tab switch warning limit
# ── Question Counts ─────────────────────────────────────
QUESTIONS_MOCK_FREE=5                              # Free mock interview
QUESTIONS_MOCK_PAID=8                              # Paid mock interview
QUESTIONS_ENTERPRISE=12                            # Enterprise assessment
12. Free Testing Strategy — Zero Cost Setup
Here is how to run and test the entire platform for $0.00:

🎯 Method 1: Gemini Free Tier (Easiest — Recommended)
Total Cost: $0.00
Setup Time: ~5 minutes
Quality: ⭐⭐⭐⭐ (Excellent)
Internet: Required
Steps:

Get a free Gemini API key (2 min) → aistudio.google.com/apikey
Copy 
.env.example
 to 
.env
Set AI_PROVIDER=gemini and paste your key
Generate a JWT secret key
Run docker compose up --build
Open http://localhost:3010
powershell
# Complete setup commands:
cd ai-interview-app
copy .env.example .env
# Edit .env and add your Gemini API key
# Then:
docker compose up --build -d
🎯 Method 2: Ollama (Completely Offline)
Total Cost: $0.00
Setup Time: ~15 minutes (includes model download)
Quality: ⭐⭐⭐ (Good for testing)
Internet: Only for initial download
Steps:

Install Ollama → ollama.com/download
Run ollama pull llama3.1 (one-time download, ~4.7GB)
Run ollama serve
Set AI_PROVIDER=ollama in 
.env
Set OLLAMA_BASE_URL=http://host.docker.internal:11434 (for Docker)
Run docker compose up --build
🎯 Method 3: OpenAI Free Credits (If Available)
Total Cost: $0.00 (with free credits)
Setup Time: ~5 minutes
Quality: ⭐⭐⭐⭐⭐ (Best)
Internet: Required
Steps:

Create an OpenAI account → platform.openai.com/signup
Check billing for free credits
If credits available → create an API key
Set AI_PROVIDER=openai and OPENAI_MODEL=gpt-4o-mini (cheapest)
Run docker compose up --build
TIP

Use gpt-4o-mini instead of gpt-4o during testing — it's ~50x cheaper and still provides excellent quality for interview questions and evaluations.

13. Deployment Checklist
Use this checklist before deploying the platform:

✅ Prerequisites Checklist
#	Task	Status
1	Docker & Docker Compose installed	☐
2	
.env
 file created from 
.env.example
☐
3	AI Provider chosen (gemini/openai/ollama)	☐
4	API key created and added to 
.env
☐
5	JWT SECRET_KEY generated and set	☐
6	Database password changed (production)	☐
7	ALLOWED_ORIGINS set correctly	☐
8	docker compose up --build runs without errors	☐
9	http://localhost:3010 loads the frontend	☐
10	/health endpoint returns OK	☐
11	Can create account and start interview	☐
12	AI questions are being generated	☐
Quick Smoke Test
powershell
# 1. Start all services
docker compose up --build -d
# 2. Check all containers are running
docker compose ps
# 3. Check backend health
curl http://localhost:3010/health
# 4. Check backend API
curl http://localhost:3010/api/v1/health
# 5. View logs if something fails
docker compose logs ai_interview_backend --tail 50
docker compose logs ai_interview_frontend --tail 50
Appendix: Quick Reference Card
╔═══════════════════════════════════════════════════════════════╗
║              VAREX AI Interview Platform                      ║
║              Quick Reference Card                             ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  🟢 FASTEST FREE SETUP:                                      ║
║     1. Get Gemini key → aistudio.google.com/apikey            ║
║     2. copy .env.example .env                                 ║
║     3. Set GEMINI_API_KEY in .env                             ║
║     4. docker compose up --build                              ║
║     5. Open http://localhost:3010                              ║
║                                                               ║
║  🔑 KEYS NEEDED:                                              ║
║     • AI Provider key (Gemini OR OpenAI OR none for Ollama)   ║
║     • JWT Secret Key (self-generated, free)                   ║
║                                                               ║
║  💰 MINIMUM COST:   $0.00 (Gemini free tier or Ollama)        ║
║  💰 PRODUCTION EST: ~$0.08–$0.21 per interview (OpenAI)       ║
║                                                               ║
║  📦 SERVICES: Backend (FastAPI) · Frontend (Next.js)          ║
║               Database (PostgreSQL) · Proxy (Nginx)           ║
║                                                               ║
║  🌐 PORTS: Frontend → :3010 · Backend → :8010 (internal)     ║
║            Database → :5432 (internal) · Ollama → :11434      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
Last Updated: March 1, 2026
Platform Version: VAREX AI Interview Platform v1.0
Document Author: Generated for VERTEX project