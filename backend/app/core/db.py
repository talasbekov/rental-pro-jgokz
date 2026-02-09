from sqlmodel import create_engine

from app.core.config import settings

# Sync engine kept for Alembic migrations and pre-start scripts
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI_SYNC))
