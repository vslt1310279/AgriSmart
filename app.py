"""
AgriSmart - Streamlit Frontend

- Upload a crop leaf image + enter a location/district
- Backend runs disease recognition + IFS recommender concurrently
- View query history from Postgres/SQLite
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import pandas as pd
import requests
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://0.0.0.0:8000").rstrip("/")

SOIL_TYPES = ["Alluvial", "Black Cotton", "Red Laterite", "Desert Sandy", "Mountain Forest", "Coastal Saline"]
CROPS = ["Rice", "Wheat", "Maize", "Cotton", "Sugarcane", "Pulses", "Millets", "Vegetables"]


st.set_page_config(
    page_title="AgriSmart",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
  .main { background-color: #F4F7F6; }
  .stApp { background-color: #F4F7F6; }
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1B5E20 0%, #2E7D32 100%);
  }
  .card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 1.25rem;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.06);
    border: 1px solid rgba(46, 125, 50, 0.10);
  }
  .card-title {
    color: #2E7D32;
    font-weight: 700;
    margin-bottom: 0.75rem;
    font-size: 1.05rem;
  }
  .pill {
    display: inline-block;
    padding: 0.35rem 0.8rem;
    border-radius: 999px;
    color: white;
    font-weight: 700;
    font-size: 0.85rem;
  }
  .pill-ok { background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%); }
  .pill-warn { background: linear-gradient(135deg, #FF9800 0%, #FFB74D 100%); }
  .pill-bad { background: linear-gradient(135deg, #f44336 0%, #e57373 100%); }
  .muted { color: #666; font-size: 0.92rem; }
  .small { color: #666; font-size: 0.85rem; }
  .stButton > button {
    background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%);
    box-shadow: 0 4px 15px rgba(46, 125, 50, 0.35);
  }
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


def _api_post_analyze(
    image_file,
    *,
    location: str | None,
    district: str | None,
    crop: str | None,
    soil_type: str | None,
) -> dict[str, Any]:
    files = {
        "file": (image_file.name, image_file.getvalue(), image_file.type),
    }
    data = {
        "location": location or "",
        "district": district or "",
        "crop": crop or "",
        "soil_type": soil_type or "",
        "top_k": "3",
    }
    r = requests.post(f"{BACKEND_URL}/analyze", files=files, data=data, timeout=120)
    r.raise_for_status()
    return r.json()


def _api_get_history(limit: int = 50) -> dict[str, Any]:
    r = requests.get(f"{BACKEND_URL}/history", params={"limit": limit, "offset": 0}, timeout=30)
    r.raise_for_status()
    return r.json()


def _pill_for_conf(conf: float | None) -> tuple[str, str]:
    if conf is None:
        return "pill-warn", "Unknown"
    if conf >= 0.85:
        return "pill-ok", f"{conf:.1%}"
    if conf >= 0.65:
        return "pill-warn", f"{conf:.1%}"
    return "pill-bad", f"{conf:.1%}"


def _backend_ok() -> tuple[bool, str]:
    """Check if the backend API is reachable. Returns (ok, message)."""
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if r.status_code == 200:
            return True, "Connected"
        return False, f"HTTP {r.status_code}"
    except requests.exceptions.ConnectionError as e:
        return False, "Connection refused — is the backend running?"
    except requests.exceptions.Timeout:
        return False, "Timeout — backend may be starting (wait 1–2 min)"
    except Exception as e:
        return False, str(e)


with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 1rem 0 1.25rem 0;">
          <div style="font-size: 2.6rem;">🌾</div>
          <div style="color:white; font-weight:800; font-size: 1.35rem;">AgriSmart</div>
          <div style="color: rgba(255,255,255,0.75); font-size: 0.85rem;">AI Farming Assistant</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    backend_ok, backend_msg = _backend_ok()
    if backend_ok:
        st.success("✅ Backend connected")
    else:
        st.error("❌ Backend not connected")
        st.caption(f"**Reason:** {backend_msg}")
        st.markdown(
            "**To fix:**\n\n"
            "1. Open a **new** Command Prompt or PowerShell window.\n\n"
            "2. Go to the AgriSmart folder and run:\n"
            "   ```\n   run_backend.bat\n   ```\n"
            "   (Or double‑click **run_backend.bat** in File Explorer.)\n\n"
            "3. Wait until you see: *Uvicorn running on http://0.0.0.0:8000*\n\n"
            "4. Then click **Check again** below or refresh this page."
        )
        if st.button("🔄 Check again", use_container_width=True):
            st.rerun()

    page = st.radio("Navigation", ["Analyze", "History"], horizontal=False)

    st.markdown("---")
    st.caption("Backend API")
    st.code(BACKEND_URL, language="text")


if page == "Analyze":
    st.markdown("## 🌿 Disease + IFS Analysis")
    if not backend_ok:
        st.warning(
            "**Backend not connected.** Start the backend first (run **run_backend.bat** in the AgriSmart folder and wait until it says *Uvicorn running*), then refresh this page or click **Check again** in the sidebar."
        )
    st.markdown(
        "<div class='muted'>Upload a leaf image and enter a location (or district). The backend runs both models concurrently and returns combined results.</div>",
        unsafe_allow_html=True,
    )

    colA, colB, colC = st.columns([1.2, 1, 1])
    with colA:
        location = st.text_input("📍 Location (village/town/city)", placeholder="e.g., Chengalpattu")
    with colB:
        district = st.text_input("🗺️ District (optional, skips geocoding)", placeholder="e.g., Kanchipuram")
    with colC:
        crop = st.selectbox("🌾 Crop (optional)", [""] + CROPS, index=0)

    colD, colE = st.columns([1, 2])
    with colD:
        soil_type = st.selectbox("🏔️ Soil Type (optional)", [""] + SOIL_TYPES, index=0)
    with colE:
        st.markdown(
            "<div class='small'>Tip: If geocoding fails (no internet / uncertain match), fill the <b>District</b> field directly.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("### 📤 Upload leaf image")
    uploaded = st.file_uploader("Upload JPG/PNG image", type=["jpg", "jpeg", "png"], accept_multiple_files=False)

    can_run = uploaded is not None and ((location.strip() if location else "") or (district.strip() if district else ""))

    if uploaded is not None:
        st.image(uploaded, caption="Uploaded image", use_container_width=True)

    run = st.button("Run analysis", disabled=not can_run, use_container_width=True)

    if run:
        with st.spinner("Running disease recognition + IFS recommender..."):
            try:
                result = _api_post_analyze(
                    uploaded,
                    location=location,
                    district=district,
                    crop=crop or None,
                    soil_type=soil_type or None,
                )
            except requests.HTTPError as e:
                st.error("Backend returned an error (500).")
                err_text = str(e)
                detail = err_text
                if e.response is not None:
                    try:
                        body = e.response.json()
                        d = body.get("detail", body.get("message", err_text))
                        detail = d if isinstance(d, str) else str(d)
                    except Exception:
                        try:
                            detail = (e.response.text or err_text).strip() or err_text
                        except Exception:
                            pass
                st.markdown("**What went wrong:**")
                st.code(detail)
                st.caption("👉 Check the **backend terminal** (where uvicorn is running) for the full Python traceback.")
                st.stop()
            except requests.RequestException as e:
                st.error("Backend request failed.")
                err_text = str(e)
                if "Connection refused" in err_text or "Failed to establish" in err_text or "Name or service not known" in err_text:
                    st.markdown(
                        "**The backend is not running or not reachable.**\n\n"
                        "1. Open a **new** terminal in the AgriSmart folder.\n\n"
                        "2. Start the backend (see **RUN.md** or README for terminal commands).\n\n"
                        "3. Wait until you see *Uvicorn running*.\n\n"
                        "4. Check the sidebar — it should show **Backend connected**. Then try **Run analysis** again."
                    )
                else:
                    st.markdown("**Error details:** (check backend terminal for logs)")
                st.code(err_text)
                st.stop()

        disease = result.get("disease") or {}
        ifs = result.get("ifs") or {}

        st.success("Analysis complete")

        left, right = st.columns([1.05, 1])
        with left:
            st.markdown("<div class='card'><div class='card-title'>🌿 Disease Detection</div>", unsafe_allow_html=True)
            cls = disease.get("class")
            conf = disease.get("confidence")
            # Backend may return float or string (e.g. "95.00%")
            if isinstance(conf, str) and "%" in conf:
                try:
                    conf = float(conf.replace("%", "").strip()) / 100.0
                except ValueError:
                    conf = None
            pill_class, pill_text = _pill_for_conf(conf if isinstance(conf, (int, float)) else None)
            st.markdown(
                f"<div style='display:flex; gap:0.75rem; align-items:center; flex-wrap:wrap;'>"
                f"<span class='pill {pill_class}'>Confidence {pill_text}</span>"
                f"<span style='font-weight:800; font-size: 1.05rem;'>{cls or 'Unknown'}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            top = disease.get("top") or []
            if isinstance(top, list) and top:
                df_top = pd.DataFrame(
                    [{"Class": t.get("class"), "Confidence": float(t.get("confidence", 0.0))} for t in top]
                )
                df_top["Confidence"] = df_top["Confidence"].map(lambda x: f"{x:.1%}")
                st.dataframe(df_top, hide_index=True, use_container_width=True)

            st.markdown(
                f"<div class='small'>Logged as ID <b>{result.get('log_id')}</b> • "
                f"{result.get('created_at') or ''}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown("<div class='card'><div class='card-title'>🌾 IFS Recommendations</div>", unsafe_allow_html=True)

            matched = ifs.get("matched_district")
            score = ifs.get("match_score")
            st.markdown(
                f"<div class='small'><b>Matched district:</b> {matched or '—'} "
                f"({score if score is not None else '—'} / 100)</div>",
                unsafe_allow_html=True,
            )

            recs = ifs.get("recommendations") or []
            if isinstance(recs, list) and recs:
                df = pd.DataFrame(recs)
                st.dataframe(df, hide_index=True, use_container_width=True)
            else:
                st.info("No IFS recommendations returned.")

            with st.expander("Raw IFS output"):
                st.json(ifs)

            st.markdown("</div>", unsafe_allow_html=True)


if page == "History":
    st.markdown("## 📚 History")
    st.markdown(
        "<div class='muted'>All analyses (inputs + outputs) are stored in the database. This page reads them from the backend.</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        limit = st.number_input("Rows", min_value=5, max_value=200, value=50, step=5)
        refresh = st.button("Refresh", use_container_width=True)
    with col2:
        st.caption(f"Backend: {BACKEND_URL}")

    try:
        data = _api_get_history(int(limit))
    except requests.RequestException as e:
        st.error("Could not load history. Is the API running and connected to the DB?")
        st.code(str(e))
        st.stop()

    items = data.get("items") or []
    if not items:
        st.info("No history yet. Run an analysis first.")
        st.stop()

    df = pd.DataFrame(items)
    if "created_at" in df.columns:
        # make it prettier (best-effort)
        def _fmt(ts: str) -> str:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return ts

        df["created_at"] = df["created_at"].map(_fmt)

    st.dataframe(df, hide_index=True, use_container_width=True)

    st.markdown("### 🔎 Inspect one record")
    ids = [int(x["id"]) for x in items]
    selected_id = st.number_input("Log ID", min_value=min(ids), max_value=max(ids) if ids else 1, value=ids[0] if ids else 1, step=1)
    if st.button("Load record", use_container_width=True):
        try:
            r = requests.get(f"{BACKEND_URL}/history/{int(selected_id)}", timeout=30)
            r.raise_for_status()
            st.json(r.json())
        except requests.RequestException as e:
            st.error("Failed to load record.")
            st.code(str(e))

