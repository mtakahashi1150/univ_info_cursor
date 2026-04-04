"""東京工科大学 OC: 蒲田・八王子の box-heading + 日程 ul をキャンパス別に抽出する。"""

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
    for h3 in soup.select("h3.box-heading"):
        t = _norm(h3.get_text())
        if "蒲田キャンパス" in t and "日程" in t:
            ul = h3.find_next_sibling("ul")
            dates = ""
            if ul:
                li = ul.find("li")
                if li:
                    dates = _norm(li.get_text())
            campus_block_schedule["蒲田キャンパス"] = {
                "schedule_summary_line": dates or "蒲田キャンパス OC 日程（公式ページのリストを参照）",
                "dept_line": "デザイン・メディア・医療保健ほか（公式参照）",
                "apply_links": [{"label": "日程・詳細", "url": link}],
            }
        elif "八王子キャンパス" in t and "日程" in t:
            ul = h3.find_next_sibling("ul")
            dates = ""
            if ul:
                li = ul.find("li")
                if li:
                    dates = _norm(li.get_text())
            campus_block_schedule["八王子キャンパス"] = {
                "schedule_summary_line": dates or "八王子キャンパス OC 日程（公式ページのリストを参照）",
                "dept_line": "コンピュータサイエンス・工学ほか（公式参照）",
                "apply_links": [{"label": "日程・詳細", "url": link}],
            }

    if campus_block_schedule:
        norm["campus_block_schedule"] = campus_block_schedule
        lines = [f"{k}: {v['schedule_summary_line']}" for k, v in campus_block_schedule.items()]
        norm["schedule_lines"] = lines + norm.get("schedule_lines", [])[:8]

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
