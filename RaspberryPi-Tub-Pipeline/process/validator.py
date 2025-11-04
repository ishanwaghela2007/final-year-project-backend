# process/validator.py
import csv
from typing import Dict, Tuple, Generator
from config import TEMP_MIN, TEMP_MAX, FILL_MIN

REQUIRED_COLS = ["camera_id","timestamp","tub_id","temperature","fill_level","seal_ok","image_ok","uptime_seconds"]

def parse_bool(v: str) -> bool:
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in ("1","true","yes","y","t")

def validate_row(row: Dict[str,str]) -> Tuple[Dict, bool, list]:
    """
    Returns (combined_row, is_defective, defects_list)
    """
    defects = []
    normalized = {}

    # required columns
    for c in REQUIRED_COLS:
        if c not in row or row[c] == "":
            defects.append(f"missing_{c}")

    if defects:
        # still return row as-is with defects
        return row, True, defects

    # parse numeric
    try:
        temp = float(row["temperature"])
        normalized["temperature"] = temp
    except Exception:
        defects.append("bad_temperature")

    try:
        fill = float(row["fill_level"])
        normalized["fill_level"] = fill
    except Exception:
        defects.append("bad_fill")

    normalized["seal_ok"] = parse_bool(row.get("seal_ok", ""))
    normalized["image_ok"] = parse_bool(row.get("image_ok", ""))

    try:
        normalized["uptime_seconds"] = int(float(row.get("uptime_seconds", 0)))
    except Exception:
        normalized["uptime_seconds"] = 0
        defects.append("bad_uptime")

    # checks
    if "temperature" in normalized:
        if normalized["temperature"] < TEMP_MIN or normalized["temperature"] > TEMP_MAX:
            defects.append("temperature_out_of_range")

    if "fill_level" in normalized:
        if normalized["fill_level"] < FILL_MIN:
            defects.append("low_fill")

    if not normalized["seal_ok"]:
        defects.append("seal_fail")

    if not normalized["image_ok"]:
        defects.append("image_fail")

    is_defective = len(defects) > 0
    combined = dict(row)
    combined.update(normalized)
    return combined, is_defective, defects

def stream_validate_csv(path: str) -> Generator[Dict, None, None]:
    """
    Yields dicts with keys: row, is_defective, defects, camera_id, timestamp, tub_id, uptime_seconds
    """
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row, is_def, defects = validate_row(raw)
            yield {
                "row": row,
                "is_defective": is_def,
                "defects": defects,
                "camera_id": row.get("camera_id"),
                "timestamp": row.get("timestamp"),
                "tub_id": row.get("tub_id"),
                "uptime_seconds": row.get("uptime_seconds", "0")
            }
