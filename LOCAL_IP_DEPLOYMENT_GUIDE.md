# Local EC2 IP-Only Deployment Guide 

This guide provides a detailed, step-by-step walk-through for deploying the VAREX platform on a fresh AWS EC2 instance without a domain name. 

When you don't have a domain name configured, Nginx's default behavior—which forces traffic over a secure SSL connection (HTTPS)—will cause your application to fail, as Let's Encrypt cannot issue SSL certificates for a bare IP address. To fix this, you need to modify the Nginx config, tweak your Docker setup, and adjust environment variables so everything runs smoothly over standard HTTP (`http://`).

Let's assume AWS assigned your EC2 instance the public IP address: **`13.235.122.9`**. Wherever you see this IP, replace it with your actual EC2 IP.

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

You must explicitly tell your Frontend and Backend to accept traffic natively on your EC2 IP address over HTTP. 

### 1. Backend `.env`

Create or open:
```bash
nano varex_backend/.env
```

**What to set:**
Ensure `ALLOWED_ORIGINS` and `FRONTEND_URL` represent the exact IP you use in the browser, starting with `http://`.

```env
ENVIRONMENT=production
SECRET_KEY=generate_with_openssl_rand_hex_32_here

# Put your AWS IP address here:
FRONTEND_URL=http://13.235.122.9
ALLOWED_ORIGINS=http://13.235.122.9,http://localhost:3000

# Database strings remain the same
DATABASE_URL=postgresql+asyncpg://varex:varexpassword@db:5432/varexdb
REDIS_URL=redis://redis:6379/0

# (Add your Sendgrid, Razorpay keys here as well...)
```

### 2. Frontend `.env.local`

Create or open:
```bash
nano varex_frontend/.env.local
```

**What to set:**
Ensure Next.js knows exactly where to send API requests under the hood.

```env
# Put your AWS IP address here:
NEXT_PUBLIC_API_BASE_URL=http://13.235.122.9

# (Add your AWS S3, Razorpay keys here as well...)
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
