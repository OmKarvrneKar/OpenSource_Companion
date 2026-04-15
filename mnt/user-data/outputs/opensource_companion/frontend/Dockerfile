# ── Frontend Dockerfile ─────────────────────────────────────────
# Next.js 14 (React)
# Node 20 LTS slim for smaller image size
# ────────────────────────────────────────────────────────────────

FROM node:20-slim

# Set working directory
WORKDIR /app

# Install dependencies first (cached layer)
# (Member 4 creates package.json in ./frontend/)
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Expose Next.js port
EXPOSE 3000

# Default command — starts Next.js dev server with hot reload
# Member 4: change to `npm run start` after `npm run build` for production
CMD ["npm", "run", "dev"]
