# ── main.py ─────────────────────────────────────────────────────
# FastAPI app entry point
# Member 3: add your routers below the webhook router
# ────────────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers import auth, contributions, enrollments, gamification, recommendations, users
from app.routers.webhooks import router as webhooks_router

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

app.include_router(webhooks_router, tags=["Webhooks"])

# Member 3 Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
app.include_router(enrollments.router, prefix="/enrollments", tags=["Enrollments"])
app.include_router(contributions.router, prefix="/contributions", tags=["Contributions"])
app.include_router(gamification.router, prefix="/gamification", tags=["Gamification"])
app.include_router(users.router, prefix="/users", tags=["Users"])


# ── Health check ──────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok"}
