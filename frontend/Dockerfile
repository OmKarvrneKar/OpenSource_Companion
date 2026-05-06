# ── Frontend Dockerfile ──────────────────────────────────────────
# Next.js development image
# Node 20 LTS slim for smaller image size
# ────────────────────────────────────────────────────────────────

FROM node:20-slim

# Set working directory
WORKDIR /app

# Install dependencies first (layer caching)
COPY package*.json ./
RUN npm install --legacy-peer-deps 2>/dev/null || true

# Copy application code
COPY . .

# Expose Next.js dev port
EXPOSE 3000

# Default command — starts Next.js with hot reload
CMD ["npm", "run", "dev"]
