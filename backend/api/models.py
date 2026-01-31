"""SQLAlchemy and Pydantic models for query history."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.api.settings import DATABASE_URL

Base = declarative_base()


class QueryLog(Base):
    """Stored analysis: inputs + disease + IFS results."""
    __tablename__ = "query_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Inputs
    location = Column(String(512), nullable=True)
    district = Column(String(256), nullable=True)
    crop = Column(String(128), nullable=True)
    soil_type = Column(String(128), nullable=True)

    # Results (JSON)
    disease_result = Column(JSON, nullable=True)  # {class, confidence, top: [...]}
    ifs_result = Column(JSON, nullable=True)       # {matched_district, recommendations, ...}
    error_message = Column(Text, nullable=True)   # if analysis failed


# Engine and session (lazy init in db.py)
def get_engine():
    return create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


# --- Pydantic schemas for API ---

class HistoryItem(BaseModel):
    id: int
    created_at: datetime
    location: Optional[str] = None
    district: Optional[str] = None
    crop: Optional[str] = None
    soil_type: Optional[str] = None
    disease_class: Optional[str] = None
    disease_confidence: Optional[float] = None
    ifs_matched_district: Optional[str] = None

    class Config:
        from_attributes = True


class HistoryDetail(BaseModel):
    id: int
    created_at: datetime
    location: Optional[str] = None
    district: Optional[str] = None
    crop: Optional[str] = None
    soil_type: Optional[str] = None
    disease_result: Optional[dict[str, Any]] = None
    ifs_result: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
