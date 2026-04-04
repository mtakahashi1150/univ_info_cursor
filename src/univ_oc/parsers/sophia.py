"""上智大学 OC 案内ページ: 四谷・目白のイベント一覧（2026年度対面OCの明示が薄い場合の警告付き）。"""

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
    body = soup.body
    text_sample = _norm(body.get_text()[:4000]) if body else ""

    warning = ""
    if re.search(r"2023年度.*夏のオープンキャンパス", text_sample) or "終了いたしました" in text_sample:
        warning = (
            "※ページ本文に「2023年度 夏のオープンキャンパス」終了の案内が見えます。"
            "**2026年度の来校型OC日程は公式の最新情報で必ず確認してください。**"
        )

    link = page_url.split("#")[0].rstrip("/")
    sched_msg = (
        "（本ページは主に過去開催・アーカイブ案内。2026年度の対面OC日程は公式で確認）"
        if warning
        else "（四谷・目白のイベント情報は公式ページを参照）"
    )

    campus_block_schedule = {
        "四谷キャンパス": {
            "schedule_summary_line": sched_msg,
            "dept_line": "理工学部（情報理工学科ほか）",
            "apply_links": [{"label": "イベント・OC情報", "url": link}],
        },
        "目白聖母キャンパス": {
            "schedule_summary_line": sched_msg,
            "dept_line": "（キャンパスによりプログラム異なる場合あり）",
            "apply_links": [{"label": "イベント・OC情報", "url": link}],
        },
    }

    schedule_lines = [
        page_title or "上智大学 オープンキャンパス関連",
        "四谷キャンパス・目白聖母キャンパスで開催のイベント（公式ページ）",
    ]

    normalized = {
        "page_title": page_title,
        "highlights": schedule_lines[:6],
        "schedule_lines": schedule_lines,
        "reservation_note": "公式ページの案内に従う（自動抽出は参考）",
        "application_period_note": "各イベントの申込は公式を参照",
        "catalog_season_warning": warning,
        "omit_table_schedule_dates": bool(warning),
        "campus_block_schedule": campus_block_schedule,
    }

    canon = "|".join([page_title, warning, text_sample[:800]])
    fingerprint = hashlib.sha256(canon.encode("utf-8")).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized": normalized,
        "raw_text_sample": text_sample[:1800],
    }
