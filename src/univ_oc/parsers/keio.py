"""慶應 OC: module-detail-text 内の日吉（講義編）・三田（学生生活編）をキャンパス別に分離する。"""

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

    blob = ""
    for block in soup.select(".module-detail-text"):
        blob = _norm(block.get_text(" ", strip=True))
        if "日吉キャンパス" in blob or "三田キャンパス" in blob:
            break

    campus_block_schedule: dict[str, dict[str, Any]] = {}
    link = page_url.split("#")[0].rstrip("/")

    m_yoko = re.search(
        r"2026年6月7日[（(]日[）)]",
        blob,
    )
    if m_yoko or "日吉キャンパス" in blob:
        yokohama_line = (
            "2026年6月7日（日） 講義編（事前申込・開始は4月下旬予定の案内）"
            if m_yoko
            else "日吉キャンパス（講義編・詳細は公式）"
        )
        campus_block_schedule["日吉キャンパス"] = {
            "schedule_summary_line": yokohama_line,
            "dept_line": "全学部対象（講義編・学部説明・模擬講義中心）",
            "apply_links": [{"label": "日程・詳細", "url": link}],
        }

    m_mita = re.search(
        r"2026年8月4日[（(]火[）)]、\s*8月5日[（(]水[）)]",
        blob,
    )
    if m_mita or ("三田キャンパス" in blob and "8月4日" in blob):
        mita_line = (
            "2026年8月4日（火）・8月5日（水） 学生生活編（事前申込）"
            if m_mita
            else "三田キャンパス（学生生活編・詳細は公式）"
        )
        campus_block_schedule["三田キャンパス"] = {
            "schedule_summary_line": mita_line,
            "dept_line": "全学部対象（学生生活編）",
            "apply_links": [{"label": "日程・詳細", "url": link}],
        }

    schedule_lines = [f"{k}: {v['schedule_summary_line']}" for k, v in campus_block_schedule.items()]
    if not schedule_lines and blob:
        schedule_lines.append(blob[:280])

    highlights = schedule_lines[:6] if schedule_lines else [_norm(page_title)]

    normalized = {
        "page_title": page_title,
        "highlights": highlights,
        "schedule_lines": schedule_lines or [page_title or "（公式ページを確認）"],
        "reservation_note": "公式ページの案内に従う（自動抽出は参考）",
        "application_period_note": "事前申込制（詳細は公式の案内）",
        "catalog_season_warning": "",
        "omit_table_schedule_dates": False,
        "campus_block_schedule": campus_block_schedule,
    }

    canon = "|".join([page_title, blob[:1200], str(sorted(campus_block_schedule.keys()))])
    fingerprint = hashlib.sha256(canon.encode("utf-8")).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized": normalized,
        "raw_text_sample": blob[:1800],
    }
