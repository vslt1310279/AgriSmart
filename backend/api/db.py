"""Database session and helpers."""
from contextlib import contextmanager
from typing import Generator

from backend.api.models import SessionLocal, QueryLog, init_db

# Defer DB init so server starts even if DB file can't be created (e.g. permissions)
def _ensure_db():
    try:
        init_db()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("DB init failed (tables may exist): %s", e)
_ensure_db()


@contextmanager
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_log(
    *,
    location: str | None = None,
    district: str | None = None,
    crop: str | None = None,
    soil_type: str | None = None,
    disease_result: dict | None = None,
    ifs_result: dict | None = None,
    error_message: str | None = None,
) -> dict:
    """Create a log row and return id + created_at (read while session is open)."""
    with get_db() as db:
        row = QueryLog(
            location=location,
            district=district,
            crop=crop,
            soil_type=soil_type,
            disease_result=disease_result,
            ifs_result=ifs_result,
            error_message=error_message,
        )
        db.add(row)
        db.flush()
        db.refresh(row)
        log_id = row.id
        created_at = row.created_at
        return {"id": log_id, "created_at": created_at}
