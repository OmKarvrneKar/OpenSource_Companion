# ── seed_badges.py ──────────────────────────────────────────────
# Run once after first migration to populate the badges table
# Usage: python seed_badges.py
# ────────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import Badge

BADGES = [
    {
        "name": "First Step",
        "description": "Enrolled in your first GitHub issue",
        "trigger_condition": "first_enrollment",
    },
    {
        "name": "First Merge",
        "description": "Got your first pull request merged",
        "trigger_condition": "first_pr_merged",
    },
    {
        "name": "On a Roll",
        "description": "Merged 5 pull requests",
        "trigger_condition": "5_prs_merged",
    },
    {
        "name": "Open Source Hero",
        "description": "Merged 10 pull requests",
        "trigger_condition": "10_prs_merged",
    },
    {
        "name": "Mentor",
        "description": "Promoted to mentor — 500pts + 10 merged PRs",
        "trigger_condition": "mentor_promoted",
    },
    {
        "name": "Week Warrior",
        "description": "Maintained a 7-day contribution streak",
        "trigger_condition": "7_day_streak",
    },
    {
        "name": "Helper",
        "description": "Helped a mentee complete their first contribution",
        "trigger_condition": "helped_mentee",
    },
    {
        "name": "Polyglot",
        "description": "Contributed to issues in 3 different languages",
        "trigger_condition": "3_languages_contributed",
    },
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(Badge).count()
        if existing > 0:
            print(f"Badges table already has {existing} rows. Skipping seed.")
            return

        for badge_data in BADGES:
            badge = Badge(**badge_data)
            db.add(badge)

        db.commit()
        print(f"Seeded {len(BADGES)} badges successfully.")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
