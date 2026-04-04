"""法政大学 OC: #a01 市ケ谷 / #a03 小金井 の「学部名」テキストと、開催日画像セクションをキャンパス別に紐づける。"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from bs4 import BeautifulSoup
from bs4.element import Tag


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _dept_after_anchor(soup: BeautifulSoup, anchor_id: str) -> str:
    a = soup.find("a", id=anchor_id)
    if not a or not isinstance(a, Tag):
        return ""
    # 次の p-openCampus__columnWrap 内の 学部名 の直後 p
    for wrap in a.find_all_next("div", class_=lambda c: c and "p-openCampus__columnWrap" in str(c)):
        if not isinstance(wrap, Tag):
            continue
        for aw in wrap.select(".p-article-wrap"):
            h3 = aw.find("h3")
            if h3 and "学部名" in _norm(h3.get_text()):
                p = aw.find("p")
                if p:
                    return _norm(p.get_text())[:220]
    return ""


def parse(
    soup: BeautifulSoup,
    *,
    page_url: str,
    reservation_url: Optional[str],
) -> dict[str, Any]:
    title_el = soup.find("title")
    page_title = _norm(title_el.get_text()) if title_el else ""
    base = page_url.split("#")[0].rstrip("/")

    sched_note = "開催日は公式ページ内「開催日」の画像で掲載（自動抽出では日付テキストなし）"

    campus_block_schedule = {
        "市ケ谷キャンパス": {
            "schedule_summary_line": sched_note,
            "dept_line": _dept_after_anchor(soup, "a01") or "（学部は公式の市ケ谷セクションを参照）",
            "apply_links": [
                {"label": "市ケ谷キャンパス（このページ）", "url": f"{base}#a01"},
            ],
        },
        "小金井キャンパス": {
            "schedule_summary_line": sched_note,
            "dept_line": _dept_after_anchor(soup, "a03") or "情報科学部・理工学部ほか（公式を参照）",
            "apply_links": [
                {"label": "小金井キャンパス（このページ）", "url": f"{base}#a03"},
            ],
        },
    }

    schedule_lines = [
        f"{name}: {sched_note}／対象: {b['dept_line'][:80]}"
        for name, b in campus_block_schedule.items()
    ]
    h2 = soup.find("h2")
    if h2:
        schedule_lines.insert(0, _norm(h2.get_text())[:200])

    normalized = {
        "page_title": page_title,
        "highlights": schedule_lines[:6],
        "schedule_lines": schedule_lines[:16],
        "reservation_note": "公式ページの案内に従う（自動抽出は参考）",
        "application_period_note": "各キャンパスの申込は公式を参照",
        "catalog_season_warning": "",
        "omit_table_schedule_dates": True,
        "campus_block_schedule": campus_block_schedule,
    }

    canon = "|".join(
        [
            page_title,
            campus_block_schedule["市ケ谷キャンパス"]["dept_line"],
            campus_block_schedule["小金井キャンパス"]["dept_line"],
        ]
    )
    fingerprint = hashlib.sha256(canon.encode("utf-8")).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized": normalized,
        "raw_text_sample": "",
    }
