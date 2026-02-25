# VAREX Platform — Deployment & Configuration Guide

This document contains everything you need to know about spinning up the VAREX platform (Frontend, Backend, Postgres, Redis, SSL) entirely from scratch onto an AWS EC2 instance. 

---

## 1. Prerequisites (Hardware & OS)

### Recommended AWS Instance
For stable Dev/Prod performance running Dockerized instances of Postgres, Redis, Python, and Next.js:
- **Instance Type**: `t3.small` or `t3.medium` (Minimum 2GB RAM. 4GB recommended to avoid `npm build` Out Of Memory errors).
- **Storage**: Minimum `20GB` EBS SSD.
- **OS**: Ubuntu 22.04 LTS or Ubuntu 24.04 LTS.

### Network Rules (AWS Security Groups)
You must open the following ports on your EC2 instance's Security Group:
- `22` (SSH for deployments)
- `80` (HTTP — required for Certbot to generate SSL initially)
- `443` (HTTPS — secure application traffic)

---

## 2. Server Installation (One-Time Setup)

SSH into your freshly created AWS Ubuntu machine and run these commands to install Docker and Git.

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Git
sudo apt install git curl unzip nginx -y

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 4. Give Ubuntu user Docker permissions (so you don't need 'sudo docker')
sudo usermod -aG docker $USER

# 5. Enable Docker to start on boot
sudo systemctl enable docker
sudo systemctl start docker

# 6. RELOGIN NOW. 
# Type 'exit' to leave the server, then SSH back in so permissions refresh.
```

---

## 3. The Full Configuration List (Environment Variables)

Your application requires two `.env` files. One inside `varex_backend/` and one inside `varex_frontend/`.

### Backend: `varex_backend/.env`
Create this file physically inside your server or place these as GitHub Secrets if using Docker image builds.

```env
# Server
ENVIRONMENT=production
ALLOWED_ORIGINS=https://varextech.in,https://www.varextech.in
SECRET_KEY=generate_with_openssl_rand_hex_32_here  # Run this in terminal to generate: openssl rand -hex 32

# URLs
FRONTEND_URL=https://varextech.in
AWS_CLOUDFRONT_URL=https://dXXXXXXX.cloudfront.net

# Databases (These match your docker-compose.yml EXACTLY. Do not change internal hostnames)
DATABASE_URL=postgresql+asyncpg://varex:varexpassword@db:5432/varexdb
REDIS_URL=redis://redis:6379/0

# SMTP / Email
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=noreply@varextech.in

# Payments
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_signing_secret
```

### Frontend: `varex_frontend/.env.local`

```env
# API Connectivity
NEXT_PUBLIC_API_BASE_URL=https://varextech.in

# Payments
NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxx

# S3 Buckets
AWS_REGION=ap-south-1
AWS_S3_BUCKET=varex-assets
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

---

## 4. How to Deploy (Manual Initial Setup)

Once the machine is ready and Git is installed, pull down your code and fire off Docker!

```bash
# 1. Clone your repo onto the machine
cd /opt
sudo git clone https://github.com/your-org/varex.git
sudo chown -R $USER:$USER varex/
cd varex

# 2. Add your physical .env files as described above
nano varex_backend/.env
nano varex_frontend/.env.local

# 3. Spin up the cluster
docker compose up -d --build

# 4. Migrate your Production Database (MANDATORY FIRST RUN)
# This creates all the tables automatically inside Postgres
docker compose exec backend alembic upgrade head
```

That's it! The system is now permanently running.

---

## 5. Automated CI/CD (GitHub Actions)

We have already configured a robust deployment pipeline inside `.github/workflows/ci_cd.yml`. You do not have to manually run the commands from Step 4 every time you code.

When you push code to `main`, GitHub will automatically:
1. Run backend testing (`pytest`).
2. Run frontend testing (`jest` and `eslint`).
3. Build efficient Docker images and push them to Git.
4. SSH into your VPS and restart the cluster automatically.

**To enable this, you must add these exact 3 variables to your GitHub Repository Secrets (Settings -> Secrets & Variables -> Actions):**

| Secret Name | Value Example | Description |
|---|---|---|
| `DEPLOY_HOST` | `13.235.122.9` | The public IP of your AWS EC2 instance. |
| `DEPLOY_USER` | `ubuntu` | Your SSH user. |
| `DEPLOY_SSH_KEY` | `-----BEGIN OPENSSH...` | The **Private** contents of the `.pem` key file you use to SSH into AWS. |

---

## 6. Running Without A Domain (IP Address Only)

If you **do not** have a domain name like `varextech.in` yet and simply want to access the platform via the EC2 instance's IP address (e.g., `http://13.235.122.9`), you must bypass the SSL/HTTPS requirement.

By default, Nginx is configured to strictly demand SSL certificates and redirect all traffic to HTTPS. This will crash Docker if you don't have a domain. Follow these steps to disable SSL and run over pure HTTP:

### Step 1: Modify Nginx Configuration
Open your Nginx configuration file (`nginx/nginx.conf`) and replace the the entire `server` block routing logic so it only listens on Port 80.

```bash
nano nginx/nginx.conf
```
Replace the TWO `server {}` blocks with this single block:
```nginx
  server {
    listen 80;
    server_name _; # Listen to any IP/Domain

    # (Keep all your existing location /api/, /docs, and / proxy_pass rules here)
    # Remove all lines starting with ssl_
  }
```

### Step 2: Update Your Environment Variables
You must update your `.env` files to use `http://` and your IP address instead of `https://varextech.in`.

**In `varex_backend/.env`:**
```env
ALLOWED_ORIGINS=http://YOUR_EC2_IP,http://localhost:3000
FRONTEND_URL=http://YOUR_EC2_IP
```

**In `varex_frontend/.env.local`:**
```env
NEXT_PUBLIC_API_BASE_URL=http://YOUR_EC2_IP
```

### Step 3: Restart Docker
Now you can safely launch the application over HTTP.

```bash
docker compose down
docker compose up -d --build
```
You can now access your application from any browser at `http://YOUR_EC2_IP`.

---

## 7. Going Live (Domain & SSL)

Once AWS gives you an IP (e.g., `13.235.122.9`), you must properly link your domain:

1. **DNS Provider (GoDaddy/Cloudflare/etc)**:
   - Create an `A` record linking `@` to your AWS IP.
   - Create an `A` record linking `www` to your AWS IP.

2. **Wait 10 minutes** for DNS to propagate.

3. **Your Nginx automatically handles SSL!**
   - Inside our `docker-compose.yml`, there is a `certbot` container that automatically talks to Let's Encrypt.
   - We already mapped it, but the very first time you boot, you should manually request the certs so they populate correctly:
   
```bash
docker compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot/ -d varextech.in -d www.varextech.in
```

Restart your Nginx instance to pick up the newly generated keys:
```bash
docker compose restart nginx
```

### Summary Checklist ✨
- [ ] Spin up `t3.small` Ubuntu EC2.
- [ ] Open Ports 80, 443, 22.
- [ ] Put `.env` logic in place.
- [ ] GoDaddy DNS to point to the AWS IP.
- [ ] Add the 3 `DEPLOY_` Secrets into GitHub to activate automated Git pushes.
