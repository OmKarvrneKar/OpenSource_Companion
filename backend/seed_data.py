# ── seed_data.py ────────────────────────────────────────────────
# Populates the database with sample repos, issues, and a test user
# for development and demo purposes.
#
# Usage:  python seed_data.py
# Requires: DATABASE_URL in .env
# ────────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import Repo, Issue, User, IssueState, Difficulty, SkillLevel


# ── Sample Repos ─────────────────────────────────────────────────

REPOS = [
    {"github_repo_id": 100001, "owner": "facebook",   "name": "react",       "full_name": "facebook/react",       "language": "JavaScript", "stars": 220000, "description": "A declarative, efficient, and flexible JavaScript library for building user interfaces"},
    {"github_repo_id": 100002, "owner": "django",     "name": "django",      "full_name": "django/django",        "language": "Python",     "stars": 77000,  "description": "The Web framework for perfectionists with deadlines"},
    {"github_repo_id": 100003, "owner": "microsoft",  "name": "vscode",      "full_name": "microsoft/vscode",     "language": "TypeScript", "stars": 160000, "description": "Visual Studio Code — free and open source code editor"},
    {"github_repo_id": 100004, "owner": "torvalds",   "name": "linux",       "full_name": "torvalds/linux",       "language": "C",          "stars": 170000, "description": "Linux kernel source tree"},
    {"github_repo_id": 100005, "owner": "golang",     "name": "go",          "full_name": "golang/go",            "language": "Go",         "stars": 120000, "description": "The Go programming language"},
    {"github_repo_id": 100006, "owner": "pallets",    "name": "flask",       "full_name": "pallets/flask",        "language": "Python",     "stars": 66000,  "description": "The Python micro framework for building web applications"},
    {"github_repo_id": 100007, "owner": "vercel",     "name": "next.js",     "full_name": "vercel/next.js",       "language": "JavaScript", "stars": 120000, "description": "The React Framework for the Web"},
    {"github_repo_id": 100008, "owner": "fastapi",    "name": "fastapi",     "full_name": "tiangolo/fastapi",     "language": "Python",     "stars": 72000,  "description": "FastAPI framework, high performance, easy to learn"},
]


# ── Sample Issues ────────────────────────────────────────────────

ISSUES = [
    # Python — Beginner
    {"github_issue_id": 200001, "repo_idx": 1, "title": "Fix typo in Django admin documentation",               "description": "There's a typo in the admin docs page that references the wrong model name.",                    "difficulty": Difficulty.beginner,     "language": "Python",     "github_url": "https://github.com/django/django/issues/1001",  "comment_count": 3,  "days_open": 5},
    {"github_issue_id": 200002, "repo_idx": 5, "title": "Add docstring to Flask request helper",                "description": "The request helper function is missing a proper docstring. Add one following project conventions.", "difficulty": Difficulty.beginner,     "language": "Python",     "github_url": "https://github.com/pallets/flask/issues/2001",  "comment_count": 1,  "days_open": 12},
    {"github_issue_id": 200003, "repo_idx": 7, "title": "Improve error message in FastAPI validation",          "description": "When a Pydantic model fails validation, the error message is unclear. Improve it.",                "difficulty": Difficulty.beginner,     "language": "Python",     "github_url": "https://github.com/tiangolo/fastapi/issues/3001", "comment_count": 5, "days_open": 8},

    # Python — Intermediate
    {"github_issue_id": 200004, "repo_idx": 1, "title": "Add pagination support to Django REST views",          "description": "Implement cursor-based pagination for the generic list views.",                                    "difficulty": Difficulty.intermediate, "language": "Python",     "github_url": "https://github.com/django/django/issues/1002",  "comment_count": 8,  "days_open": 20},
    {"github_issue_id": 200005, "repo_idx": 7, "title": "Implement rate limiting middleware for FastAPI",        "description": "Create a middleware that limits API requests per IP using a sliding window algorithm.",              "difficulty": Difficulty.intermediate, "language": "Python",     "github_url": "https://github.com/tiangolo/fastapi/issues/3002", "comment_count": 12, "days_open": 30},
    {"github_issue_id": 200006, "repo_idx": 5, "title": "Add async support to Flask blueprints",                "description": "Flask blueprints don't properly support async views. Add async compatibility.",                    "difficulty": Difficulty.intermediate, "language": "Python",     "github_url": "https://github.com/pallets/flask/issues/2002",  "comment_count": 7,  "days_open": 15},

    # Python — Advanced
    {"github_issue_id": 200007, "repo_idx": 1, "title": "Optimize Django ORM query planner for complex joins",   "description": "Complex many-to-many joins are generating suboptimal SQL. Rewrite the query planner.",             "difficulty": Difficulty.advanced,     "language": "Python",     "github_url": "https://github.com/django/django/issues/1003",  "comment_count": 20, "days_open": 60},

    # JavaScript — Beginner
    {"github_issue_id": 200008, "repo_idx": 0, "title": "Fix broken link in React README",                      "description": "The getting started link in the README points to a 404 page.",                                     "difficulty": Difficulty.beginner,     "language": "JavaScript", "github_url": "https://github.com/facebook/react/issues/4001", "comment_count": 2,  "days_open": 3},
    {"github_issue_id": 200009, "repo_idx": 6, "title": "Add aria-label to Next.js navigation component",       "description": "The default navigation component is missing accessibility attributes.",                            "difficulty": Difficulty.beginner,     "language": "JavaScript", "github_url": "https://github.com/vercel/next.js/issues/5001", "comment_count": 4,  "days_open": 7},
    {"github_issue_id": 200010, "repo_idx": 0, "title": "Update React testing examples to use vitest",          "description": "Replace outdated Jest examples with Vitest in the testing documentation.",                         "difficulty": Difficulty.beginner,     "language": "JavaScript", "github_url": "https://github.com/facebook/react/issues/4002", "comment_count": 6,  "days_open": 10},

    # JavaScript — Intermediate
    {"github_issue_id": 200011, "repo_idx": 0, "title": "Implement React concurrent rendering improvements",    "description": "Optimize the concurrent renderer for better priority scheduling.",                                 "difficulty": Difficulty.intermediate, "language": "JavaScript", "github_url": "https://github.com/facebook/react/issues/4003", "comment_count": 15, "days_open": 25},
    {"github_issue_id": 200012, "repo_idx": 6, "title": "Add ISR cache invalidation API to Next.js",            "description": "Implement a programmatic API for invalidating ISR cached pages.",                                  "difficulty": Difficulty.intermediate, "language": "JavaScript", "github_url": "https://github.com/vercel/next.js/issues/5002", "comment_count": 9,  "days_open": 18},

    # TypeScript — Beginner
    {"github_issue_id": 200013, "repo_idx": 2, "title": "Fix VS Code tooltip rendering on hover",               "description": "Tooltips sometimes render behind other UI elements. Fix the z-index.",                             "difficulty": Difficulty.beginner,     "language": "TypeScript", "github_url": "https://github.com/microsoft/vscode/issues/6001", "comment_count": 3, "days_open": 4},
    {"github_issue_id": 200014, "repo_idx": 2, "title": "Add keyboard shortcut for VS Code terminal split",     "description": "There's no default shortcut to split the integrated terminal. Add one.",                            "difficulty": Difficulty.beginner,     "language": "TypeScript", "github_url": "https://github.com/microsoft/vscode/issues/6002", "comment_count": 5, "days_open": 9},

    # TypeScript — Intermediate
    {"github_issue_id": 200015, "repo_idx": 2, "title": "Implement VS Code extension API for custom themes",    "description": "Extend the theme API to support dynamic color tokens from extensions.",                             "difficulty": Difficulty.intermediate, "language": "TypeScript", "github_url": "https://github.com/microsoft/vscode/issues/6003", "comment_count": 11, "days_open": 35},

    # Go — Beginner
    {"github_issue_id": 200016, "repo_idx": 4, "title": "Fix Go fmt edge case with nested structs",             "description": "go fmt misaligns fields in deeply nested anonymous structs.",                                       "difficulty": Difficulty.beginner,     "language": "Go",         "github_url": "https://github.com/golang/go/issues/7001", "comment_count": 2,  "days_open": 6},

    # Go — Intermediate
    {"github_issue_id": 200017, "repo_idx": 4, "title": "Improve Go garbage collector pause times",             "description": "Reduce GC pause times for large heap allocations by improving the mark phase.",                    "difficulty": Difficulty.intermediate, "language": "Go",         "github_url": "https://github.com/golang/go/issues/7002", "comment_count": 18, "days_open": 45},

    # C — Advanced
    {"github_issue_id": 200018, "repo_idx": 3, "title": "Fix race condition in Linux scheduler",                "description": "A race condition in the CFS scheduler can cause priority inversion under heavy load.",             "difficulty": Difficulty.advanced,     "language": "C",          "github_url": "https://github.com/torvalds/linux/issues/8001", "comment_count": 25, "days_open": 90},

    # Additional Python — Beginner (more variety)
    {"github_issue_id": 200019, "repo_idx": 1, "title": "Add unit test for Django forms clean method",          "description": "The forms.clean() method is missing test coverage. Write tests for edge cases.",                   "difficulty": Difficulty.beginner,     "language": "Python",     "github_url": "https://github.com/django/django/issues/1004",  "comment_count": 2,  "days_open": 4},
    {"github_issue_id": 200020, "repo_idx": 5, "title": "Update Flask quickstart guide for Python 3.12",        "description": "The quickstart guide references deprecated Python 3.8 syntax. Update for 3.12.",                   "difficulty": Difficulty.beginner,     "language": "Python",     "github_url": "https://github.com/pallets/flask/issues/2003",  "comment_count": 1,  "days_open": 2},
]


# ── Test Users ───────────────────────────────────────────────────

TEST_USERS = [
    {"github_id": 900001, "github_username": "demo_user",     "email": "demo@example.com",    "skill_level": SkillLevel.beginner,     "primary_language": "Python"},
    {"github_id": 900002, "github_username": "jane_dev",      "email": "jane@example.com",    "skill_level": SkillLevel.intermediate, "primary_language": "JavaScript"},
    {"github_id": 900003, "github_username": "senior_hacker", "email": "senior@example.com",  "skill_level": SkillLevel.advanced,     "primary_language": "C"},
]


def seed():
    db = SessionLocal()
    try:
        # ── Seed repos ───────────────────────────────────────────
        existing_repos = db.query(Repo).count()
        if existing_repos > 0:
            print(f"Repos table already has {existing_repos} rows. Skipping repo seed.")
        else:
            repo_objects = []
            for r in REPOS:
                repo = Repo(**r)
                db.add(repo)
                repo_objects.append(repo)
            db.flush()
            print(f"Seeded {len(REPOS)} repos.")

        # ── Seed issues ──────────────────────────────────────────
        existing_issues = db.query(Issue).count()
        if existing_issues > 0:
            print(f"Issues table already has {existing_issues} rows. Skipping issue seed.")
        else:
            # Get repo objects from DB for id references
            repos = db.query(Repo).order_by(Repo.id).all()
            for issue_data in ISSUES:
                repo_idx = issue_data.pop("repo_idx")
                issue = Issue(
                    repo_id=repos[repo_idx].id,
                    state=IssueState.open,
                    **issue_data,
                )
                db.add(issue)
            print(f"Seeded {len(ISSUES)} issues.")

        # ── Seed test users ──────────────────────────────────────
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"Users table already has {existing_users} rows. Skipping user seed.")
        else:
            for u in TEST_USERS:
                user = User(**u)
                db.add(user)
            print(f"Seeded {len(TEST_USERS)} test users.")

        db.commit()
        print("\nSeed complete!")
        print("Test users created:")
        for u in TEST_USERS:
            print(f"  - {u['github_username']} ({u['skill_level'].value}, {u['primary_language']})")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
