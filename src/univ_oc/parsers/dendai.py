"""東京電機大学 OC: プログラム画像の alt から千住・鳩山の日程・学部表記を抽出する。"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from bs4 import BeautifulSoup

from univ_oc.parsers import generic as generic_mod


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def parse(
    soup: BeautifulSoup,
    *,
    page_url: str,
    reservation_url: Optional[str],
) -> dict[str, Any]:
    base = generic_mod.parse(soup, page_url=page_url, reservation_url=reservation_url)
    norm = base["normalized"]
    link = page_url.split("#")[0].rstrip("/")

    campus_block_schedule: dict[str, dict[str, Any]] = {}
    for img in soup.find_all("img", alt=True):
        alt = _norm(str(img.get("alt", "")))
        if alt.startswith("東京千住キャンパス"):
            campus_block_schedule["東京千住キャンパス"] = {
                "schedule_summary_line": alt,
                "dept_line": "",
                "apply_links": [{"label": "日程・詳細・事前登録", "url": link}],
            }
        elif alt.startswith("埼玉鳩山キャンパス"):
            campus_block_schedule["埼玉鳩山キャンパス"] = {
                "schedule_summary_line": alt,
                "dept_line": "",
                "apply_links": [{"label": "日程・詳細・事前登録", "url": link}],
            }

    if campus_block_schedule:
        norm["campus_block_schedule"] = campus_block_schedule
        lines = [f"{k}: {v['schedule_summary_line']}" for k, v in campus_block_schedule.items()]
        norm["schedule_lines"] = lines + norm.get("schedule_lines", [])[:10]

    canon = "|".join(
        [
            norm["page_title"],
            "##".join(norm.get("schedule_lines", [])[:10]),
            str(sorted(campus_block_schedule.keys())),
        ]
    )
    base["fingerprint"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    base["normalized"] = norm
    return base
