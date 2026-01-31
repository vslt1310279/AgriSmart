"""IFS recommender wrapper (district/location -> IFS recommendations)."""
import sys
from pathlib import Path
from typing import Any

# Add ifs_recommender parent so we can import recommend
backend_dir = Path(__file__).resolve().parent.parent.parent
ifs_dir = backend_dir / "ifs_recommender"
if str(backend_dir.parent) not in sys.path:
    sys.path.insert(0, str(backend_dir.parent))

from backend.api.settings import IFS_CSV_PATH

# Import after path is set
from backend.ifs_recommender.recommend import (
    load_ifs_csv,
    recommend_for_district,
    recommend_for_location,
)

_records_cache: list | None = None


def _get_records():
    global _records_cache
    if _records_cache is None:
        if not IFS_CSV_PATH.exists():
            raise FileNotFoundError(f"IFS CSV not found: {IFS_CSV_PATH}")
        _records_cache = load_ifs_csv(str(IFS_CSV_PATH))
    return _records_cache


def recommend(
    *,
    location: str | None = None,
    district: str | None = None,
) -> dict[str, Any]:
    """
    Get IFS recommendations. Prefer district if provided (no geocoding);
    otherwise use location (geocodes to district).
    """
    records = _get_records()
    district = (district or "").strip()
    location = (location or "").strip()
    if district:
        return recommend_for_district(district, records)
    if location:
        return recommend_for_location(location, records)
    raise ValueError("Provide either location or district")
