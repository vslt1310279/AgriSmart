import argparse
import csv
import difflib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


DEFAULT_CSV_PATH = r"ifs - TN_IFS_TNAU_Complete.csv"


@dataclass(frozen=True)
class IFSRecord:
    district: str
    agro_climatic_zone: str
    ifs_model: str
    description: str


def _norm_district(name: str) -> str:
    """
    Normalize district names so that small differences (case, punctuation, 'District' suffix)
    don't prevent a match.
    """
    s = (name or "").strip().lower()
    s = re.sub(r"\bdistrict\b", "", s)
    s = re.sub(r"[^a-z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_ifs_csv(csv_path: str) -> List[IFSRecord]:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found at: {csv_path}")

    records: List[IFSRecord] = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"District", "Agro_Climatic_Zone", "IFS_Model", "Description"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "CSV is missing required columns: "
                + ", ".join(sorted(missing))
                + f" (found: {reader.fieldnames})"
            )

        for row in reader:
            records.append(
                IFSRecord(
                    district=(row.get("District") or "").strip(),
                    agro_climatic_zone=(row.get("Agro_Climatic_Zone") or "").strip(),
                    ifs_model=(row.get("IFS_Model") or "").strip(),
                    description=(row.get("Description") or "").strip(),
                )
            )
    return records


def build_district_index(
    records: Iterable[IFSRecord],
) -> Tuple[Dict[str, str], Dict[str, List[IFSRecord]]]:
    """
    Returns:
      - norm_to_display: normalized_district -> a "pretty" district name
      - norm_to_records: normalized_district -> list of records
    """
    norm_to_display: Dict[str, str] = {}
    norm_to_records: Dict[str, List[IFSRecord]] = {}

    for r in records:
        key = _norm_district(r.district)
        if not key:
            continue
        norm_to_display.setdefault(key, r.district)
        norm_to_records.setdefault(key, []).append(r)

    return norm_to_display, norm_to_records


def match_district(
    user_district: str, norm_to_display: Dict[str, str]
) -> Tuple[str, str, int]:
    """
    Returns (normalized_key, display_name, score)
    score=100 for exact normalized match, otherwise fuzzy score 0..100
    """
    want = _norm_district(user_district)
    if not want:
        raise ValueError("Empty district input.")

    if want in norm_to_display:
        return want, norm_to_display[want], 100

    # Fuzzy match against normalized keys (stdlib only)
    candidates = list(norm_to_display.keys())
    close = difflib.get_close_matches(want, candidates, n=1, cutoff=0.0)
    if not close:
        raise ValueError(f"Could not match district: {user_district!r}")

    best_key = close[0]
    best_score = int(difflib.SequenceMatcher(None, want, best_key).ratio() * 100)
    # Conservative threshold: avoid wrong district recommendations.
    if best_score < 85:
        raise ValueError(
            f"District match too uncertain for {user_district!r}. "
            f"Best guess {norm_to_display[best_key]!r} (score {best_score}). "
            "Try entering the district name directly."
        )
    return best_key, norm_to_display[best_key], int(best_score)


def geocode_location_to_district(location: str, timeout_s: int = 15) -> Tuple[str, dict]:
    """
    Uses OpenStreetMap Nominatim to resolve a free-text location to a district-like field.

    Returns (district_name, raw_address_dict)
    """
    q = (location or "").strip()
    if not q:
        raise ValueError("Empty location input.")

    # Help Nominatim by pinning to TN, India if user didn't include it.
    q2 = q
    if "india" not in q.lower():
        q2 = f"{q}, Tamil Nadu, India"

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": q2,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 1,
        "countrycodes": "in",
    }
    headers = {
        # Nominatim requires a user agent identifying the application.
        "User-Agent": "tn-ifs-recommender/1.0 (educational; contact: local)",
    }

    # Respectful pause to avoid rapid repeat calls in tight loops.
    time.sleep(1.0)
    full_url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full_url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        body = resp.read().decode("utf-8")
    data = json.loads(body)
    if not data:
        raise ValueError(f"Could not geocode location: {location!r}")

    address = data[0].get("address") or {}

    # Common India keys from Nominatim:
    # - state_district: often "Chengalpattu District"
    # - district/county: varies
    district = (
        address.get("state_district")
        or address.get("district")
        or address.get("county")
        or address.get("region")
    )
    if not district:
        raise ValueError(
            f"Geocoding succeeded but district not found in address for {location!r}. "
            f"Address keys: {sorted(address.keys())}"
        )
    return str(district), address


def recommend_for_district(
    district: str, records: List[IFSRecord]
) -> Dict[str, object]:
    norm_to_display, norm_to_records = build_district_index(records)
    key, display, score = match_district(district, norm_to_display)
    recs = norm_to_records.get(key, [])

    # De-duplicate identical model+description rows.
    seen = set()
    out_items = []
    for r in recs:
        sig = (r.ifs_model, r.description, r.agro_climatic_zone)
        if sig in seen:
            continue
        seen.add(sig)
        out_items.append(
            {
                "IFS_Model": r.ifs_model,
                "Agro_Climatic_Zone": r.agro_climatic_zone,
                "Description": r.description,
            }
        )

    return {
        "input_district": district,
        "matched_district": display,
        "match_score": score,
        "recommendations": out_items,
    }


def recommend_for_location(location: str, records: List[IFSRecord]) -> Dict[str, object]:
    district, address = geocode_location_to_district(location)
    result = recommend_for_district(district, records)
    result["input_location"] = location
    result["geocoded_district"] = district
    result["geocode_address"] = address
    return result


def _print_text(result: Dict[str, object]) -> None:
    if "input_location" in result:
        print(f"Location: {result.get('input_location')}")
        print(f"District (geocoded): {result.get('geocoded_district')}")
    print(f"District (matched to CSV): {result.get('matched_district')} (score {result.get('match_score')})")
    print()
    recs = result.get("recommendations") or []
    if not recs:
        print("No recommendations found for this district in the CSV.")
        return
    for i, r in enumerate(recs, start=1):
        print(f"{i}. {r.get('IFS_Model')}")
        print(f"   Zone: {r.get('Agro_Climatic_Zone')}")
        print(f"   Description: {r.get('Description')}")
        print()


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Rule-based IFS recommender for Tamil Nadu (district-based)."
    )
    p.add_argument("--csv", default=DEFAULT_CSV_PATH, help="Path to IFS CSV file")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--location", help="Free-text location (village/town/city) in Tamil Nadu")
    g.add_argument("--district", help="District name (skips geocoding)")
    p.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = p.parse_args(argv)

    records = load_ifs_csv(args.csv)

    if args.location:
        result = recommend_for_location(args.location, records)
    else:
        result = recommend_for_district(args.district, records)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

