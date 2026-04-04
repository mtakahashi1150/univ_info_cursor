"""東京都市大学 OC: CloudFront 等で 403 になる環境では警告付き。取得できた場合は generic に委譲。"""

from __future__ import annotations

import hashlib
from typing import Any, Optional

from bs4 import BeautifulSoup

from univ_oc.parsers import generic as generic_mod


def parse(
    soup: BeautifulSoup,
    *,
    page_url: str,
    reservation_url: Optional[str],
) -> dict[str, Any]:
    title_el = soup.find("title")
    title = (title_el.get_text() or "").strip() if title_el else ""
    blocked = "403" in title or "could not be satisfied" in title.lower() or "request blocked" in (
        soup.get_text() or ""
    ).lower()

    if not blocked:
        return generic_mod.parse(soup, page_url=page_url, reservation_url=reservation_url)

    warning = (
        "※この環境から公式サイトへのアクセスがブロックされ（403 等）、HTML を正しく取得できませんでした。"
        "**ブラウザで公式 URL を開き、最新の OC 情報を確認してください。**"
    )
    link = page_url.split("#")[0].rstrip("/")
    campus_block_schedule = {
        "世田谷キャンパス": {
            "schedule_summary_line": "（自動取得不可・公式ページで確認）",
            "dept_line": "情報工学部ほか",
            "apply_links": [{"label": "公式 OC 案内", "url": link}],
        },
        "横浜キャンパス": {
            "schedule_summary_line": "（自動取得不可・公式ページで確認）",
            "dept_line": "理工・建築ほか",
            "apply_links": [{"label": "公式 OC 案内", "url": link}],
        },
    }
    normalized = {
        "page_title": title or "東京都市大学 OC（取得エラー）",
        "highlights": [warning[:200]],
        "schedule_lines": [warning, "世田谷・横浜キャンパスは公式 URL を確認"],
        "reservation_note": "公式ページの案内に従う",
        "application_period_note": "—",
        "catalog_season_warning": warning,
        "omit_table_schedule_dates": True,
        "campus_block_schedule": campus_block_schedule,
    }
    canon = "|".join([title, warning, link])
    return {
        "fingerprint": hashlib.sha256(canon.encode("utf-8")).hexdigest(),
        "normalized": normalized,
        "raw_text_sample": (soup.get_text() or "")[:400],
    }
