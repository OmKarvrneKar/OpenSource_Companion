# ── database.py ─────────────────────────────────────────────────
# SQLAlchemy engine + session setup
# Import get_db in FastAPI route functions as a dependency
# ────────────────────────────────────────────────────────────────

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv(override=False)  # Docker-injected vars take priority over .env file

DATABASE_URL = os.getenv("DATABASE_URL")

# create_engine handles the connection pool automatically
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # drops stale connections automatically
    pool_size=10,             # max persistent connections
    max_overflow=20           # extra connections allowed under load
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# All models inherit from this Base
Base = declarative_base()


def get_db():
    """
    FastAPI dependency — yields a DB session per request,
    closes it when the request is done.

    Usage in a route:
        from app.database import get_db
        from sqlalchemy.orm import Session
        from fastapi import Depends

        @router.get("/something")
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
