"""
AgriSmart unified API: disease + IFS run concurrently; history in PostgreSQL/SQLite.
"""
import asyncio
import logging
import traceback
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.api import db
from backend.api.models import QueryLog

logger = logging.getLogger(__name__)


def _run_disease(image_bytes: bytes) -> dict[str, Any]:
    from backend.api.services.disease import predict_disease
    return predict_disease(image_bytes)


def _run_ifs(location: Optional[str], district: Optional[str]) -> dict[str, Any]:
    from backend.api.services.ifs import recommend
    return recommend(location=location or None, district=district or None)

##############
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <--- Make sure this import is there

app = FastAPI()

# 1. Define who can talk to this API
origins = [
    "http://localhost",
    "http://localhost:8501", # Default Streamlit port
    "http://0.0.0.0:8000",   # Internal Render address
    "https://agrismart.onrender.com", # Your actual Render URL
    "*", # The "Wildcard" - allows everything (good for debugging)
]

# 2. Add the middleware RIGHT AFTER app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, etc.
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    return {"status": "Backend is running!"}
##############

'''
app = FastAPI(title="AgriSmart API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Turn any unhandled exception into a JSON 500 with 'detail' for the frontend."""
    if isinstance(exc, HTTPException):
        raise exc  # Let FastAPI return its detail
    logger.exception("Unhandled exception")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "agrismart-api"}


@app.get("/check")
def check():
    """Check if required files and imports exist (no heavy loading)."""
    from backend.api.settings import DISEASE_MODEL_PATH, DISEASE_CLASSES_PATH, IFS_CSV_PATH
    out = {"ok": True, "checks": {}}
    out["checks"]["disease_model"] = DISEASE_MODEL_PATH.exists()
    out["checks"]["disease_classes"] = DISEASE_CLASSES_PATH.exists()
    out["checks"]["ifs_csv"] = IFS_CSV_PATH.exists()
    if not all(out["checks"].values()):
        out["ok"] = False
        out["paths"] = {
            "disease_model": str(DISEASE_MODEL_PATH),
            "disease_classes": str(DISEASE_CLASSES_PATH),
            "ifs_csv": str(IFS_CSV_PATH),
        }
    return out


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    location: str = Form(""),
    district: str = Form(""),
    crop: str = Form(""),
    soil_type: str = Form(""),
    top_k: str = Form("3"),
):
    """
    Run disease recognition and IFS recommender concurrently.
    Requires: image file + (location or district).
    """
    loc = location.strip() or None
    dist = district.strip() or None
    if not loc and not dist:
        raise HTTPException(400, "Provide either location or district")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(400, "Empty image file")

    disease_result: dict[str, Any] | None = None
    ifs_result: dict[str, Any] | None = None
    err_msg: Optional[str] = None

    async def run_both():
        loop = asyncio.get_event_loop()
        disease_fut = loop.run_in_executor(None, _run_disease, image_bytes)
        ifs_fut = loop.run_in_executor(None, lambda: _run_ifs(loc, dist))
        d, i = await asyncio.gather(disease_fut, ifs_fut)
        return d, i

    try:
        disease_result, ifs_result = await run_both()
    except Exception as e:
        err_msg = str(e)
        logger.exception("Analysis failed")
        if disease_result is None and ifs_result is None:
            detail = f"Analysis failed: {err_msg}"
            raise HTTPException(status_code=500, detail=detail)

    try:
        row = db.create_log(
            location=loc,
            district=dist,
            crop=crop.strip() or None,
            soil_type=soil_type.strip() or None,
            disease_result=disease_result,
            ifs_result=ifs_result,
            error_message=err_msg,
        )
    except Exception as e:
        logger.exception("Failed to save to database")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    created_at = row["created_at"].isoformat() + "Z" if row["created_at"] else None
    return {
        "log_id": row["id"],
        "created_at": created_at,
        "disease": disease_result or {},
        "ifs": ifs_result or {},
    }


@app.get("/history", response_model=dict)
def history(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    """List recent query log entries (summary)."""
    with db.get_db() as session:
        rows = (
            session.query(QueryLog)
            .order_by(QueryLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        items = []
        for r in rows:
            dr = r.disease_result or {}
            ir = r.ifs_result or {}
            items.append({
                "id": r.id,
                "created_at": r.created_at.isoformat() + "Z" if r.created_at else None,
                "location": r.location,
                "district": r.district,
                "crop": r.crop,
                "soil_type": r.soil_type,
                "disease_class": dr.get("class"),
                "disease_confidence": dr.get("confidence"),
                "ifs_matched_district": ir.get("matched_district"),
            })
        return {"items": items, "limit": limit, "offset": offset}


@app.get("/history/{log_id}", response_model=dict)
def history_detail(log_id: int):
    """Get one query log entry with full disease + IFS results."""
    with db.get_db() as session:
        row = session.query(QueryLog).filter(QueryLog.id == log_id).first()
        if not row:
            raise HTTPException(404, "Record not found")
        return {
            "id": row.id,
            "created_at": row.created_at.isoformat() + "Z" if row.created_at else None,
            "location": row.location,
            "district": row.district,
            "crop": row.crop,
            "soil_type": row.soil_type,
            "disease_result": row.disease_result,
            "ifs_result": row.ifs_result,
            "error_message": row.error_message,
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
