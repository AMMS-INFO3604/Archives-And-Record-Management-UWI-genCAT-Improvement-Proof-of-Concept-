import os

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# Reads DATABASE_URL from the environment so the same codebase works with
# both SQLite (local dev) and PostgreSQL (staging / production).
#
# Heroku, Render, and Railway all export a DATABASE_URL that starts with the
# legacy "postgres://" scheme.  SQLAlchemy 1.4+ only accepts "postgresql://",
# so we normalise it here.

_db_url = os.getenv("DATABASE_URL", "sqlite:///temp-database.db")

if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)

SQLALCHEMY_DATABASE_URI = _db_url

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
# Never leave the default secret key in production – set SECRET_KEY in your
# environment or .env file.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
