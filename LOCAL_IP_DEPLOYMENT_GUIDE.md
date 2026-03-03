# Local EC2 IP-Only Deployment Guide 

This guide provides a detailed, step-by-step walk-through for deploying the VAREX platform on a fresh AWS EC2 instance without a domain name. 

When you don't have a domain name configured, Nginx's default behavior—which forces traffic over a secure SSL connection (HTTPS)—will cause your application to fail, as Let's Encrypt cannot issue SSL certificates for a bare IP address. To fix this, you need to modify the Nginx config, tweak your Docker setup, and adjust environment variables so everything runs smoothly over standard HTTP (`http://`).

Let's assume AWS assigned your EC2 instance the **Public IPv4 address**: **`13.235.122.9`**. Wherever you see this IP, replace it with your actual EC2 Public IP. Do NOT use the Private IP.

---

## Step 1: Clone the Project onto EC2

1. SSH into your EC2 instance.
2. Clone the repository and navigate into the folder:
   ```bash
   cd /opt
   sudo git clone https://github.com/your-org/varex.git
   sudo chown -R $USER:$USER varex/
   cd varex
   ```

---

## Step 2: Update Nginx Configuration

By default, the `nginx/nginx.conf` file tries to listen on port 443 (HTTPS) and redirects port 80 (HTTP) to HTTPS. We must strip out all SSL logic and tell Nginx to serve the site strictly on port 80.

### Open the file:
```bash
nano nginx/nginx.conf
```

### ❌ Before (What it looks like initially):
```nginx
events { worker_connections 1024; }

http {
  upstream frontend { server frontend:3000; }
  upstream backend  { server backend:8000;  }

  server {
    listen 80;
    server_name varextech.in www.varextech.in;
    return 301 https://$host$request_uri;
  }

  server {
    listen 443 ssl http2;
    server_name varextech.in www.varextech.in;

    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    # ... more ssl config ...
    
    location / {
      proxy_pass http://frontend;
      # ... proxy headers ...
    }
    # ... more locations ...
  }
}
```

### ✅ After (What you should change it to):
Replace the ENTIRE contents of `nginx/nginx.conf` with this simplified HTTP-only block:

```nginx
events { worker_connections 1024; }

http {
  upstream frontend { server frontend:3000; }
  upstream backend  { server backend:8000;  }

  server {
    listen 80;
    server_name _;  # The underscore means "listen to any IP or domain"

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1000;

    add_header X-Frame-Options        "SAMEORIGIN"    always;
    add_header X-XSS-Protection       "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff"       always;
    add_header Referrer-Policy        "no-referrer-when-downgrade" always;

    location /api/ {
      proxy_pass         http://backend;
      proxy_set_header   Host              $host;
      proxy_set_header   X-Real-IP         $remote_addr;
      proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
      proxy_set_header   X-Forwarded-Proto $scheme;
      proxy_read_timeout 120s;
    }

    location /docs         { proxy_pass http://backend; }
    location /redoc        { proxy_pass http://backend; }
    location /openapi.json { proxy_pass http://backend; }

    location / {
      proxy_pass         http://frontend;
      proxy_set_header   Host              $host;
      proxy_set_header   X-Real-IP         $remote_addr;
      proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
      proxy_set_header   X-Forwarded-Proto $scheme;
      proxy_http_version 1.1;
      proxy_set_header   Upgrade           $http_upgrade;
      proxy_set_header   Connection        "upgrade";
    }
  }
}
```
*Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).*

---

## Step 3: Remove Certbot from Docker Compose

Since we aren't using SSL, attempting to boot the `certbot` container in `docker-compose.yml` will just result in errors.

### Open the file:
```bash
nano docker-compose.yml
```

### Changes to Make in `docker-compose.yml`:
1. Find the `nginx` service and remove the `certbot` and `ssl` volume mounts.
2. Find the `certbot:` service block at the bottom and delete it entirely.

### ✅ What your `nginx` block should look like after:
```yaml
  nginx:
    image: nginx:alpine
    container_name: varex_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      # REMOVED: - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      # REMOVED: ssl and certbot volumes
    depends_on:
      - frontend
      - backend
```

---

## Step 4: Configure Environment Variables for IP Access

You must explicitly tell your Frontend and Backend to accept traffic natively on your EC2 Public IP address over HTTP. 
 
 to generate random secret key:-  `openssl rand -hex 32`
### 1. Backend `.env`

Create or open:
```bash
nano varex_backend/.env
```

**What to set:**
Ensure `ALLOWED_ORIGINS` and `FRONTEND_URL` represent the exact **Public IP** you use in the browser, starting with `http://`.

```env
ENVIRONMENT=production
SECRET_KEY=generate_with_openssl_rand_hex_32_here

# Put your AWS Public IP address here:
FRONTEND_URL=http://YOUR_EC2_PUBLIC_IP
ALLOWED_ORIGINS=http://YOUR_EC2_PUBLIC_IP,http://localhost:3000

# Database strings remain the same
DATABASE_URL=postgresql+asyncpg://varex:varexpassword@db:5432/varexdb
REDIS_URL=redis://redis:6379/0

# 3. Third-Party Integrations
RAZORPAY_KEY_ID=rzp_test_your_real_key
RAZORPAY_KEY_SECRET=your_real_razorpay_secret
AWS_S3_BUCKET=varex-assets
AWS_REGION=ap-south-1
```

### 💎 How to get your Temporary Razorpay Test Keys:
1. Go to the [Razorpay Dashboard](https://dashboard.razorpay.com/) and sign up for a free account.
2. In the top-left corner, ensure the toggle is set to **Test Mode**.
3. Go to **Settings > API Keys** in the left sidebar.
4. Click **Generate Key**. This will give you:
   - Your `Key Id` (starts with `rzp_test_...`) → put this in `RAZORPAY_KEY_ID`
   - Your `Key Secret` → put this in `RAZORPAY_KEY_SECRET`
*(Keep them safe; the Secret will not be shown again.)*

### 2. Frontend `.env.local`

Create or open:
```bash
nano varex_frontend/.env.local
```

**What to set:**
Since your current file only has the Next.js API URL setup, you just need to replace `http://localhost:8000` with the EC2 IP.

```env
# URL of FastAPI backend
NEXT_PUBLIC_API_BASE_URL=http://YOUR_EC2_PUBLIC_IP
```

---

## Step 5: Start the Cluster!

Now that Nginx knows not to expect SSL, and your applications know they are operating on an IP address instead of a domain, it's time to fire up Docker.

```bash
# 1. Build and start the containers in the background (-d)
docker compose up -d --build

# 2. MANDATORY: Run exactly ONE time to build Postgres SQL Tables
docker compose exec backend alembic upgrade head
```

### Verification
Open your browser and navigate to:
**`http://13.235.122.9`**

You should see the VAREX Platform load natively! You can access the API docs directly at `http://13.235.122.9/docs`.

---

## 🛑 Important Security Warnings

1. **Authentication Risks**: Because you are running over unencrypted HTTP, any passwords logged in on `http://13.235.122.9` are transmitted via plaintext over the internet. **Never use real, sensitive passwords** when testing via an IP address. Wait until HTTPS is configured for production data.
2. **Payment Webhooks**: Razorpay webhooks might not be successfully delivered or validated over bare HTTP connections depending on their strictest security updates. Be aware of this when testing payments.



1) Main VERTEX nginx/nginx.conf (HTTP, stable Docker DNS, no stale IP 502)
events { worker_connections 1024; }

http {
  resolver 127.0.0.11 valid=10s ipv6=off;

  map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
  }

  server {
    listen 80;
    server_name _;

    client_max_body_size 20m;

    location /api/ {
      set $backend_upstream http://backend:8000;
      proxy_pass         $backend_upstream;
      proxy_set_header   Host              $host;
      proxy_set_header   X-Real-IP         $remote_addr;
      proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
      proxy_set_header   X-Forwarded-Proto $scheme;
      proxy_read_timeout 120s;
    }

    location /docs {
      set $backend_upstream http://backend:8000;
      proxy_pass $backend_upstream;
    }

    location /redoc {
      set $backend_upstream http://backend:8000;
      proxy_pass $backend_upstream;
    }

    location /openapi.json {
      set $backend_upstream http://backend:8000;
      proxy_pass $backend_upstream;
    }

    location / {
      set $frontend_upstream http://frontend:3000;
      proxy_pass         $frontend_upstream;
      proxy_set_header   Host              $host;
      proxy_set_header   X-Real-IP         $remote_addr;
      proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
      proxy_set_header   X-Forwarded-Proto $scheme;
      proxy_http_version 1.1;
      proxy_set_header   Upgrade           $http_upgrade;
      proxy_set_header   Connection        $connection_upgrade;
    }
  }
}
2) AI Interview ai-interview-app/nginx/nginx.conf (same anti-stale pattern)
events { worker_connections 1024; }

http {
  resolver 127.0.0.11 valid=10s ipv6=off;

  server {
    listen 80;
    server_name _;

    client_max_body_size 10m;

    location /api/ {
      set $ai_backend http://ai_interview_backend:8010;
      proxy_pass         $ai_backend;
      proxy_set_header   Host              $host;
      proxy_set_header   X-Real-IP         $remote_addr;
      proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
      proxy_set_header   X-Forwarded-Proto $scheme;
      proxy_read_timeout 120s;
    }

    location /health {
      set $ai_backend http://ai_interview_backend:8010;
      proxy_pass $ai_backend/health;
      proxy_set_header Host $host;
    }

    location / {
      set $ai_frontend http://ai_interview_frontend:3000;
      proxy_pass         $ai_frontend;
      proxy_set_header   Host              $host;
      proxy_set_header   X-Real-IP         $remote_addr;
      proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
      proxy_set_header   X-Forwarded-Proto $scheme;
    }
  }
}
3) varex_frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://65.0.102.249:8080
NEXT_PUBLIC_AI_INTERVIEW_APP_URL=http://65.0.102.249:3010
AI_INTERVIEW_APP_URL=http://65.0.102.249:3010
4) varex_backend/.env
ENVIRONMENT=production
FRONTEND_URL=http://65.0.102.249:8080
ALLOWED_ORIGINS=["http://65.0.102.249:8080","http://localhost:3000","https://varextech.in","https://www.varextech.in"]
5) ai-interview-app/backend/.env
ALLOWED_ORIGINS=http://65.0.102.249:3010,http://65.0.102.249:8080,https://varextech.in,https://www.varextech.in
6) Restart
# main app
docker compose up -d --build --force-recreate nginx frontend backend

# ai interview app
cd ai-interview-app
docker compose up -d --build --force-recreate
7) Quick checks
docker logs varex_nginx --tail 100
docker exec -it varex_nginx wget -qO- http://frontend:3000 | head
docker exec -it varex_nginx wget -qO- http://backend:8000/health

with your current setup, yes, you must open port 3010 if you want direct access to AI Interview (http://IP:3010).

Your compose files currently expose:

Main app via 8080:80 (varex_nginx)
AI app via 3010:80 (ai_interview_web)
So with only inbound 8080, AI Interview on 3010 is blocked externally.

What to open in AWS Security Group
If you keep current docker-compose as-is
Open inbound:
TCP 8080 from 0.0.0.0/0
TCP 3010 from 0.0.0.0/0 (for AI Interview)
Do NOT open (not needed publicly)
3000, 8000, 5432, 6379
Better production approach (single public port)
If you want only 8080 open, then:

keep AI app internal (no public 3010)
route AI app through main Nginx under a path/subdomain (example: /ai-interview/)
That way only 8080 is public.

If you want, I can send you exact Nginx + compose configs for this single-port (8080-only) architecture in next message.

error 
Target Subsystem: 
AI Engine
Expected Port:
3010
Endpoint:
/api/ai-interview/status
Last Status:
Connection Refused / Timeout

That message means: main VERTEX frontend container cannot reach AI app health URL (not browser issue).

/api/ai-interview/status runs inside varex_frontend, so it must be able to connect to AI app from container network.

Quick verify (run on EC2)
# 1) AI app alive on host?
curl -i http://127.0.0.1:3010/health

# 2) Public path alive?
curl -i http://65.0.102.249:3010/health

# 3) From main frontend container, can it reach AI app?
docker exec -it varex_frontend sh -lc "wget -qO- http://65.0.102.249:3010/health || echo FAIL"
If step 3 fails, your container cannot hairpin to public IP.
Use shared Docker network (best fix).

Best fix (stable): connect both compose projects via shared network
A) Create shared network once
docker network create vertex_shared
B) Add to ~/VERTEX/docker-compose.yml (main app)
services:
  frontend:
    networks:
      - default
      - vertex_shared
    environment:
      NEXT_PUBLIC_API_BASE_URL: http://backend:8000
      AI_INTERVIEW_APP_URL: http://ai_interview_web
      NEXT_PUBLIC_AI_INTERVIEW_APP_URL: http://65.0.102.249:3010

  nginx:
    networks:
      - default
      - vertex_shared

networks:
  vertex_shared:
    external: true
C) Add to ~/VERTEX/ai-interview-app/docker-compose.yml
services:
  ai_interview_web:
    networks:
      - default
      - vertex_shared

  ai_interview_frontend:
    networks:
      - default
      - vertex_shared

  ai_interview_backend:
    networks:
      - default
      - vertex_shared

networks:
  vertex_shared:
    external: true
D) Restart both stacks
cd ~/VERTEX/ai-interview-app && docker compose down && docker compose up -d --build
cd ~/VERTEX && docker compose down && docker compose up -d --build
Final check
docker exec -it varex_frontend sh -lc "wget -qO- http://ai_interview_web/health"
curl -i http://65.0.102.249:8080/api/ai-interview/status
Expected: second command returns JSON with "ok": true and launchUrl.


The missing piece is: both stacks are on different Docker networks, so varex_frontend can’t reliably reach AI stack.

Use this config-only fix.

1) Create shared network once
docker network create vertex_shared
2) Update ~/VERTEX/docker-compose.yml (main app)
Add this under frontend service:

    environment:
      NEXT_PUBLIC_API_BASE_URL: http://backend:8000
      AI_INTERVIEW_APP_URL: http://ai_interview_web
      NEXT_PUBLIC_AI_INTERVIEW_APP_URL: http://65.0.102.249:3010
    networks:
      - default
      - vertex_shared
Add this under nginx service:

    networks:
      - default
      - vertex_shared
Add at bottom:

networks:
  vertex_shared:
    external: true
3) Update ~/VERTEX/ai-interview-app/docker-compose.yml
Add to ai_interview_web:

    networks:
      - default
      - vertex_shared
Add at bottom:

networks:
  vertex_shared:
    external: true
(You can also add same networks block to ai_interview_backend and ai_interview_frontend, but ai_interview_web is the critical one.)

4) Restart both stacks
cd ~/VERTEX/ai-interview-app
docker compose down
docker compose up -d --build

cd ~/VERTEX
docker compose down
docker compose up -d --build
5) Verify from inside main frontend container
docker exec -it varex_frontend sh -lc "wget -qO- http://ai_interview_web/health"
Expected:

{"status":"ok",...}
If /ai-interview still shows timeout after this, tell me output of:

curl -i http://65.0.102.249:8080/api/ai-interview/status
docker logs varex_frontend --tail 100
docker logs ai_interview_web --tail 100

Run exactly these commands.

1) Create shared network
docker network create vertex_shared || true
2) Patch main app compose (~/VERTEX/docker-compose.yml)
cd ~/VERTEX
cp docker-compose.yml docker-compose.yml.bak.$(date +%F-%H%M%S)

cat > docker-compose.yml <<'YAML'
# PATH: varex/docker-compose.yml

services:

  db:
    image: postgres:16-alpine
    container_name: varex_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: varexdb
      POSTGRES_USER: varex
      POSTGRES_PASSWORD: varexpassword
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: [ "CMD", "pg_isready", "-U", "varex" ]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: varex_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    healthcheck:
      test: [ "CMD", "redis-cli", "ping" ]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./varex_backend
      dockerfile: Dockerfile
    container_name: varex_backend
    restart: unless-stopped
    env_file:
      - ./varex_backend/.env
    environment:
      DATABASE_URL: postgresql+asyncpg://varex:varexpassword@db:5432/varexdb
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./varex_backend:/app

  frontend:
    build:
      context: ./varex_frontend
      dockerfile: Dockerfile
    container_name: varex_frontend
    restart: unless-stopped
    env_file:
      - ./varex_frontend/.env.local
    environment:
      NEXT_PUBLIC_API_BASE_URL: http://backend:8000
      AI_INTERVIEW_APP_URL: http://ai_interview_web
      NEXT_PUBLIC_AI_INTERVIEW_APP_URL: http://65.0.102.249:3010
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - default
      - vertex_shared

  nginx:
    image: nginx:alpine
    container_name: varex_nginx
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - backend
    networks:
      - default
      - vertex_shared

volumes:
  postgres_data:

networks:
  vertex_shared:
    external: true
YAML
3) Patch AI app compose (~/VERTEX/ai-interview-app/docker-compose.yml)
cd ~/VERTEX/ai-interview-app
cp docker-compose.yml docker-compose.yml.bak.$(date +%F-%H%M%S)

cat > docker-compose.yml <<'YAML'
services:
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
      test: [ "CMD-SHELL", "pg_isready -U ${AI_INTERVIEW_DB_USER:-ai_interview}" ]
      interval: 10s
      timeout: 5s
      retries: 5

  ai_interview_backend:
    build:
      context: ./backend
    container_name: ai_interview_backend
    restart: unless-stopped
    environment:
      DATABASE_URL: ${AI_INTERVIEW_DATABASE_URL:-postgresql+psycopg2://ai_interview:ai_interview_password@ai_interview_db:5432/ai_interview_db}
      ALLOWED_ORIGINS: ${AI_INTERVIEW_ALLOWED_ORIGINS:-http://localhost:3010,http://localhost:3000}
      SECRET_KEY: ${SECRET_KEY:-change-this-to-a-strong-random-secret-in-production}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES:-1440}
      AI_PROVIDER: ${AI_PROVIDER:-gemini}
      GEMINI_API_KEY: ${GEMINI_API_KEY:-}
      GEMINI_MODEL: ${GEMINI_MODEL:-gemini-2.0-flash}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      OPENAI_MODEL: ${OPENAI_MODEL:-gpt-4o}
      OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://host.docker.internal:11434}
      OLLAMA_MODEL: ${OLLAMA_MODEL:-llama3.1}
      MAX_RESUME_SIZE_MB: ${MAX_RESUME_SIZE_MB:-5}
      DEFAULT_TOTAL_TIME_SECONDS: ${DEFAULT_TOTAL_TIME_SECONDS:-2700}
      DEFAULT_QUESTION_TIME_SECONDS: ${DEFAULT_QUESTION_TIME_SECONDS:-300}
      MAX_TAB_SWITCHES_BEFORE_FLAG: ${MAX_TAB_SWITCHES_BEFORE_FLAG:-3}
      QUESTIONS_MOCK_FREE: ${QUESTIONS_MOCK_FREE:-5}
      QUESTIONS_MOCK_PAID: ${QUESTIONS_MOCK_PAID:-8}
      QUESTIONS_ENTERPRISE: ${QUESTIONS_ENTERPRISE:-12}
    depends_on:
      ai_interview_db:
        condition: service_healthy
    expose:
      - "8010"

  ai_interview_frontend:
    build:
      context: ./frontend
    container_name: ai_interview_frontend
    restart: unless-stopped
    depends_on:
      - ai_interview_backend
    expose:
      - "3000"

  ai_interview_web:
    image: nginx:alpine
    container_name: ai_interview_web
    restart: unless-stopped
    ports:
      - "3010:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - ai_interview_frontend
      - ai_interview_backend
    networks:
      - default
      - vertex_shared

volumes:
  ai_interview_postgres_data:

networks:
  vertex_shared:
    external: true
YAML
4) Restart both stacks
cd ~/VERTEX/ai-interview-app
docker compose down
docker compose up -d --build

cd ~/VERTEX
docker compose down
docker compose up -d --build
5) Validate
docker exec -it varex_frontend sh -lc "wget -qO- http://ai_interview_web/health"
curl -i http://65.0.102.249:8080/api/ai-interview/status