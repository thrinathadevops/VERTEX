# 🎯 VAREX AI Interview Platform

> AI-powered interview assessment platform with real-time evaluation, anti-cheat detection, and enterprise analytics.

## ✨ Features

### 🏗️ Modular Architecture
- **8 separate modules**: User, Resume Processing, Interview Engine, Pricing, Real-time Analysis, Report Generator, Payment, Admin Analytics
- **FastAPI** backend with **PostgreSQL** and **SQLAlchemy**
- **JWT authentication** with role-based access (`candidate`, `enterprise_admin`, `super_admin`)
- **Docker-ready** deployment

### 💰 Smart Pricing
| Type | Price | Details |
|------|-------|---------|
| **Mock (B2C)** — First | ₹0 | Free forever (1 per user) |
| **Mock (B2C)** — Next | ₹50 | Per session |
| **Enterprise (B2B)** | ₹500 | Per interview with volume discounts |

**Enterprise Discounts**: 2→5%, 5→10%, 10→30%, 20→50%

### 🎙️ 7-Phase AI Interview Flow
1. AI Introduction
2. Ice-Breaker (resume-based)
3. Resume Summary Validation
4. Technical Deep Dive
5. Scenario-Based Questions
6. Behavioral Evaluation
7. Closing Remarks

### 📄 Resume-Powered Question Generation
- Upload PDF/DOCX/TXT
- AI extracts structured skill profile
- Questions tailored to resume skills and experience level

### ⚡ Real-Time Background Evaluation
- Answers evaluated **asynchronously** (candidate doesn't wait)
- Scores **hidden during interview** (realistic simulation)
- Final report generated only after completion

### 📊 Weighted Score Breakdown
| Category | Weight |
|----------|--------|
| Technical Depth | 40% |
| Scenario Handling | 25% |
| Communication | 20% |
| Confidence | 15% |

### 🔥 Additional Features
- **Anti-Cheat Detection**: Tab switches, window blur, copy/paste monitoring
- **Interview Timers**: Per-question + total timers based on difficulty
- **Difficulty Levels**: Junior, Mid, Senior, Architect
- **Enterprise Dashboard**: Candidate rankings, skill gap analytics, CSV reports
- **Admin Analytics**: Platform-wide stats, revenue tracking

### 🧠 RAG-Based AI (No Fine-Tuning Cost)
- Uses Retrieval-Augmented Generation instead of fine-tuning
- 645 lines of real-world interview training data
- Supports: OpenAI GPT-4o, Google Gemini, Ollama (self-hosted)

## 🚀 Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — set your AI provider API key

# 2. Start with Docker
docker-compose up --build -d

# 3. Access
# API Docs: http://localhost:3010/docs
# Frontend: http://localhost:3010
```

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/register` — Register
- `POST /api/v1/auth/login` — Login (JWT)
- `GET /api/v1/auth/profile` — Profile (auth required)

### Interview
- `POST /api/v1/interview/pricing` — Calculate pricing
- `GET /api/v1/interview/eligibility?email=` — Check eligibility
- `POST /api/v1/interview/session` — Create session
- `POST /api/v1/interview/session/{id}/upload-resume` — Upload resume
- `POST /api/v1/interview/session/{id}/answer` — Submit answer
- `GET /api/v1/interview/session/{id}/report` — Get report

### Enterprise (role: enterprise_admin)
- `GET /api/v1/enterprise/dashboard` — Dashboard
- `GET /api/v1/enterprise/report/csv` — Download CSV

### Admin (role: super_admin)
- `GET /api/v1/admin/analytics` — Platform analytics

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Auth | JWT (python-jose + bcrypt) |
| AI | OpenAI / Gemini / Ollama |
| Resume Parsing | PyMuPDF + python-docx |
| Deployment | Docker Compose + Nginx |

## 📂 Project Structure

```
backend/app/
├── auth/           # JWT authentication + role deps
├── ai/             # Interview engine, prompts, LLM providers
├── services/       # Pricing, evaluation, anti-cheat, timers, reports
├── routes/         # API endpoints (auth, interview, enterprise, admin)
├── models.py       # SQLAlchemy models
├── schemas.py      # Pydantic schemas
├── config.py       # Application settings
└── main.py         # FastAPI application entry point
```
