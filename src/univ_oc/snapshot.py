from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def load_snapshot(path: Path) -> Optional[dict[str, Any]]:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_snapshot(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def merge_snapshot(
    source_id: str,
    university: str,
    department_label: str,
    page_url: str,
    reservation_url: Optional[str],
    new_fp: str,
    normalized: dict[str, Any],
    previous: Optional[dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    """戻り値: (snapshot dict, changed bool)"""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    changed = previous is None or previous.get("fingerprint") != new_fp
    prev_fp = previous.get("fingerprint") if previous else None

    if not previous:
        last_change = now
    elif not changed:
        last_change = str(previous.get("last_content_change_at", now))
    else:
        last_change = now

    data = {
        "source_id": source_id,
        "university": university,
        "department_label": department_label,
        "page_url": page_url,
        "reservation_url": reservation_url,
        "fingerprint": new_fp,
        "previous_fingerprint": prev_fp,
        "normalized": normalized,
        "last_fetch_at": now,
        "last_content_change_at": last_change,
    }
    return data, changed


def days_since_content_change(last_change_iso: str) -> int:
    try:
        dt = datetime.fromisoformat(last_change_iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now.date() - dt.astimezone(timezone.utc).date()
        return max(0, delta.days)
    except (ValueError, TypeError):
        return 0
