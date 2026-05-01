# ── main.py ─────────────────────────────────────────────────────
# FastAPI app entry point
# Member 3: add your routers below the webhook router
# ────────────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="OpenSource Companion API",
    description="Recommends GitHub issues to open source beginners",
    version="0.1.0"
)

# CORS — allows Next.js frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────

# Data pipeline webhook (Member 1)
from app.routers.webhooks import router as webhooks_router
app.include_router(webhooks_router, tags=["Webhooks"])

# Member 3 Routers
from app.routers import auth, recommendations, enrollments, contributions, gamification, users
app.include_router(auth.router, prefix="/auth")
app.include_router(recommendations.router, prefix="/recommendations")
app.include_router(enrollments.router, prefix="/enrollments")
app.include_router(contributions.router, prefix="/contributions")
app.include_router(gamification.router, prefix="/gamification")
app.include_router(users.router, prefix="/users")


# ── Health check ──────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok"}
