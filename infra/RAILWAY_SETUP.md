# Railway Deployment Setup Guide

## One-time setup (do this once)

### 1. Create Railway account
Go to https://railway.app and sign up with GitHub.

### 2. Install Railway CLI
```powershell
npm install -g @railway/cli
railway login
```

### 3. Create a new Railway project
```powershell
# From your project root
railway init
# Choose "Empty Project"
# Name it: opensource-companion
```

### 4. Add environment variables on Railway
Go to your Railway project → each service → Variables tab.
Add ALL variables from your .env file for each service:

Required for backend + celery services:
```
DATABASE_URL              → your Neon DB connection string
REDIS_URL                 → Railway will provide this (see step 5)
GITHUB_APP_ID             → from GitHub App settings
GITHUB_APP_PRIVATE_KEY    → contents of your .pem file
GITHUB_CLIENT_ID          → from GitHub App settings
GITHUB_CLIENT_SECRET      → from GitHub App settings
GITHUB_WEBHOOK_SECRET     → your webhook secret
JWT_SECRET_KEY            → generate with: openssl rand -hex 32
ENVIRONMENT               → production
FRONTEND_URL              → https://your-frontend.railway.app
```

Required for frontend:
```
NEXT_PUBLIC_API_URL       → https://your-backend.railway.app
```

### 5. Add Redis on Railway
In your Railway project:
- Click "New Service" → "Database" → "Redis"
- Railway auto-injects REDIS_URL into all services

### 6. Add RAILWAY_TOKEN to GitHub Secrets
- Go to Railway → Account Settings → Tokens → Create token
- Go to your GitHub repo → Settings → Secrets → Actions
- Add secret: RAILWAY_TOKEN = (paste token)

---

## Deploy manually (first time)
```powershell
# From project root
railway up
```

## After that — automatic deploys
Every merge to main triggers GitHub Actions which deploys automatically.

---

## Update GitHub App webhook URL
After first Railway deploy, update your GitHub App webhook URL:
- Old: https://your-ngrok-url.ngrok-free.app/webhooks/github
- New: https://your-backend.railway.app/webhooks/github

Go to: GitHub → Settings → Developer Settings → GitHub Apps → Edit

---

## Verify deployment
```powershell
# Check backend health
curl https://your-backend.railway.app/health

# Expected: {"status":"ok"}
```
