# PATH: varex_backend/Dockerfile
# FIX 8.3: multi-stage build, gunicorn with UvicornWorker for production

# ── Stage 1: builder ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: runner ──────────────────────────────────────────────
FROM python:3.12-slim AS runner

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --system varex && adduser --system --ingroup varex varex
USER varex

EXPOSE 8000

# Production: gunicorn with 4 UvicornWorkers
# Development override: uvicorn app.main:app --reload
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-"]
