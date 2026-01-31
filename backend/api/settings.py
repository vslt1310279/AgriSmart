"""Backend API settings (env + paths)."""
import os
from pathlib import Path

# Paths relative to this package
API_DIR = Path(__file__).resolve().parent
BACKEND_DIR = API_DIR.parent

# Disease model (plant_disease_recognition_model)
DISEASE_MODEL_DIR = BACKEND_DIR / "plant_disease_recognition_model"
DISEASE_MODEL_PATH = DISEASE_MODEL_DIR / "plant_disease_model_working.h5"
DISEASE_CLASSES_PATH = DISEASE_MODEL_DIR / "classes.txt"

# IFS recommender
IFS_DIR = BACKEND_DIR / "ifs_recommender"
IFS_CSV_PATH = IFS_DIR / "ifs - TN_IFS_TNAU_Complete.csv"

# Database: PostgreSQL in production; SQLite for local (file in project root)
# Use forward slashes so sqlite:/// URL is valid on Windows too
_default_sqlite = (BACKEND_DIR.parent / "agrismart.db").as_posix()
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{_default_sqlite}",
)
# Render/Railway etc. use postgres:// but SQLAlchemy 1.4+ expects postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
