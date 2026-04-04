"""公式OCページの汎用パーサー（大学ごとの専用ロジックなしで差分検知）。"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from bs4 import BeautifulSoup


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def parse(
    soup: BeautifulSoup,
    *,
    page_url: str,
    reservation_url: Optional[str],
) -> dict[str, Any]:
    title_el = soup.find("title")
    page_title = _norm(title_el.get_text()) if title_el else ""

    body = soup.find("main") or soup.find("article") or soup.body
    text_blob = _norm(body.get_text()) if body else ""

    highlights: list[str] = []
    for a in soup.find_all("a", href=True, limit=80):
        t = _norm(a.get_text())
        if len(t) < 12:
            continue
        if re.match(r"^\d{4}", t) or "オープンキャンパス" in t or "OPEN CAMPUS" in t.upper():
            if t not in highlights:
                highlights.append(t)
        if len(highlights) >= 8:
            break

    schedule_lines: list[str] = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        t = _norm(tag.get_text())
        if not t or len(t) < 6:
            continue
        if re.search(r"\d{4}年|\d{1,2}月\d{1,2}日|OC|オープンキャンパス", t):
            if t not in schedule_lines:
                schedule_lines.append(t)
        if len(schedule_lines) >= 15:
            break

    app_note = ""
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日[^。]{0,40}オープン", text_blob)
    if m:
        app_note = f"（ページ内表記: {m.group(0)[:60]}…）"

    catalog_season_warning = ""
    if page_url and re.search(r"2025", page_url) and not re.search(r"2026", page_url):
        catalog_season_warning = (
            "※URLに2025年度のOC案内が含まれる可能性が高いです。"
            "掲載日程が**既に過去の年度**であることがあります。**最新の開催は必ず公式サイトで確認してください。**"
        )
    elif "2025年度" in page_title and "2026年度" not in page_title:
        if not re.search(r"2026\s*年|2026年度", text_blob[:4000]):
            catalog_season_warning = (
                "※ページタイトル等が2025年度の案内に見えます。"
                "**最新年度の情報は公式サイトで確認してください。**"
            )

    normalized = {
        "page_title": page_title,
        "highlights": highlights,
        "schedule_lines": schedule_lines,
        "reservation_note": "公式ページの案内に従う（自動抽出は参考）",
        "application_period_note": app_note or "各キャンパス・日程の予約は公式を参照",
        "catalog_season_warning": catalog_season_warning,
    }

    canon = "|".join(
        [
            page_title,
            "##".join(highlights[:6]),
            "##".join(schedule_lines[:10]),
            catalog_season_warning,
        ]
    )
    fingerprint = hashlib.sha256(canon.encode("utf-8")).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized": normalized,
        "raw_text_sample": text_blob[:1800],
    }
