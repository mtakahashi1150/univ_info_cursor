"""工学院大学 OC: 「今後のオープンキャンパスの予定」表からキャンパス付き来場型行を抽出する。"""

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
    for table in soup.select("table.info-table2"):
        for tr in table.find_all("tr"):
            cells = [_norm(td.get_text()) for td in tr.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            dt, form = cells[0], cells[1]
            if "来場型" not in form or "キャンパス" not in form:
                continue
            m = re.search(r"（([^）]+キャンパス)）", form)
            campus_key = m.group(1) if m else form
            note = f"{dt} {form}"
            if cells[2:]:
                note += f"（予約: {cells[2]}）"
            campus_block_schedule[campus_key] = {
                "schedule_summary_line": note,
                "dept_line": "工学部・先端工学部（公式参照）",
                "apply_links": [{"label": "日程・詳細", "url": link}],
            }

    if campus_block_schedule:
        norm["campus_block_schedule"] = campus_block_schedule
        lines = [f"{k}: {v['schedule_summary_line']}" for k, v in campus_block_schedule.items()]
        norm["schedule_lines"] = lines + [x for x in norm.get("schedule_lines", []) if x not in lines][:10]

    canon = "|".join(
        [
            norm["page_title"],
            "##".join(norm.get("schedule_lines", [])[:12]),
            str(sorted(campus_block_schedule.keys())),
        ]
    )
    base["fingerprint"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    base["normalized"] = norm
    return base
