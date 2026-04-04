"""明治大学 入試総合サイト オープンキャンパスページ用パーサー。"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from bs4 import BeautifulSoup


def _norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def parse(
    soup: BeautifulSoup,
    *,
    page_url: str,
    reservation_url: Optional[str],
) -> dict[str, Any]:
    title_el = soup.find("title")
    page_title = _norm_text(title_el.get_text()) if title_el else ""

    content = soup.select_one("div.examContent") or soup.find("main") or soup.body
    text_blob = _norm_text(content.get_text()) if content else ""

    highlights: list[str] = []
    skip_labels = {"オープンキャンパス開催日程", "プログラム", "参加資格・予約方法・よくある問い合わせ", "更新情報"}
    # 「更新情報」ブロック付近の目次リンク（日付付き告知を優先）
    for ul in soup.select("div.examContent ul.anchorLink"):
        for a in ul.find_all("a", href=True):
            t = _norm_text(a.get_text())
            if not t or t in skip_labels or len(t) < 8:
                continue
            if re.match(r"^\d{4}/\d{1,2}/\d{1,2}", t) or ("オープンキャンパス" in t and "開催" in t):
                highlights.append(t)
        if highlights:
            break

    schedule_lines = []
    seen: set[str] = set()
    for h in soup.select("h2#title5-1, h3.title"):
        t = _norm_text(h.get_text())
        if not t:
            continue
        if re.match(r"^Q\d+[:：]", t) or "前年参考" in t and "販売" in t:
            continue
        if re.search(r"【.+】\d{4}年\d{1,2}月", t) or t.startswith("【NEW】オープンキャンパス"):
            if t not in seen:
                seen.add(t)
                schedule_lines.append(t)
        elif "オープンキャンパス" in t and re.search(r"\d{4}年", t) and "？" not in t:
            if t not in seen:
                seen.add(t)
                schedule_lines.append(t)
    schedule_lines = schedule_lines[:12]

    app_period_note = ""
    m = re.search(
        r"(\d{4}/\d{1,2}/\d{1,2})[^。]*予約",
        text_blob,
    )
    if m:
        app_period_note = f"（ページ内に予約関連の日付表記あり: {m.group(1)} 付近を参照）"

    normalized = {
        "page_title": page_title,
        "highlights": highlights[:8],
        "schedule_lines": schedule_lines,
        "reservation_note": "LINE による事前参加登録（詳細は公式ページ・LINE案内を参照）",
        "application_period_note": app_period_note or "公式ページの記載に従う（自動抽出は参考）",
    }

    canon = "|".join(
        [
            page_title,
            "##".join(normalized["highlights"]),
            "##".join(normalized["schedule_lines"]),
        ]
    )
    fingerprint = hashlib.sha256(canon.encode("utf-8")).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized": normalized,
        "raw_text_sample": text_blob[:2000],
    }
