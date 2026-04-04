"""公式OCページの汎用パーサー（大学ごとの専用ロジックなしで差分検知）。"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _has_date_fragment(t: str) -> bool:
    return bool(
        re.search(r"\d{4}年\d{1,2}月\d{1,2}日", t)
        or re.search(r"\d{1,2}月\d{1,2}日", t)
        or re.search(r"\d{4}/\d{1,2}/\d{1,2}", t)
    )


def _schedule_context_keywords(t: str) -> bool:
    return bool(
        re.search(
            r"開催|オープンキャンパス|オープン\s*キャンパス|OPEN\s*CAMPUS|"
            r"日時|講義|模擬|キャンパス|事前申込|申込|学部|年度|OC",
            t,
            re.I,
        )
    )


def _lines_from_text_block(text: str, *, max_lines: int = 12) -> list[str]:
    """複数行の p 要素などから、日付＋文脈語を含む行だけ拾う。"""
    out: list[str] = []
    for raw in re.split(r"[\n\r]+|<br\s*/?>", text, flags=re.I):
        t = _norm(raw)
        if len(t) < 8 or len(t) > 400:
            continue
        if not _has_date_fragment(t):
            continue
        # 慶應など「■日時」と日付が改行で分かれている箇所では、日付行単体にキーワードが無い
        if not _schedule_context_keywords(t):
            if not (len(t) <= 120 and re.search(r"\d{4}年\d{1,2}月", t)):
                continue
        if t not in out:
            out.append(t)
        if len(out) >= max_lines:
            break
    return out


def _collect_schedule_from_headings(soup: BeautifulSoup) -> list[str]:
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
    return schedule_lines


def _schedule_search_roots(soup: BeautifulSoup, body: Tag) -> list[Tag]:
    """グローバルナビの li が大量にあるサイトでは body 全体を走査すると上限で本文に届かない。本文らしきブロックを優先する。"""
    roots: list[Tag] = []
    for sel in (".module-detail-text", ".module-detail-wrap", ".parabox2_wrap", "main", "article"):
        try:
            for el in soup.select(sel):
                if isinstance(el, Tag) and el not in roots:
                    roots.append(el)
        except ValueError:
            continue
    if not roots:
        roots = [body]
    return roots


def _collect_schedule_from_body_blocks(soup: BeautifulSoup, body: Tag) -> list[str]:
    """本文の p / li / td から日程っぽい行を抽出（慶應・青山など h 以外に日付があるサイト向け）。"""
    found: list[str] = []
    # 日時と日付が span/br で分断されているブロックをまとめて読む
    for block in soup.select(".module-detail-text, .module-detail-wrap"):
        if not isinstance(block, Tag):
            continue
        blob = block.get_text("\n", strip=True)
        for line in _lines_from_text_block(blob, max_lines=24):
            if line not in found:
                found.append(line)
            if len(found) >= 20:
                return found
    for root in _schedule_search_roots(soup, body):
        for tag in root.find_all(["p", "li", "td"], limit=160):
            if not isinstance(tag, Tag):
                continue
            if tag.find_parent(["nav", "header", "footer"]):
                continue
            classes = " ".join(tag.get("class") or [])
            if "nav" in classes or "menu" in classes or "breadcrumb" in classes:
                continue
            text = tag.get_text("\n", strip=True)
            for line in _lines_from_text_block(text):
                if line not in found:
                    found.append(line)
                if len(found) >= 20:
                    return found
    return found


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

    schedule_lines = _collect_schedule_from_headings(soup)
    if body and isinstance(body, Tag):
        for line in _collect_schedule_from_body_blocks(soup, body):
            if line not in schedule_lines:
                schedule_lines.append(line)
            if len(schedule_lines) >= 25:
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

    # 表の「日程」列: 過去年度専用URLなどは日付を出さず紛らわしさを避ける
    omit_table_schedule_dates = False
    if page_url:
        path = (urlparse(page_url).path or "").lower()
        if re.search(r"2025", path) and not re.search(r"2026", path):
            omit_table_schedule_dates = True
        elif re.search(r"opencampus20\d{2}", path):
            mpath = re.search(r"opencampus(20\d{2})", path)
            if mpath and mpath.group(1) < "2026":
                omit_table_schedule_dates = True

    normalized = {
        "page_title": page_title,
        "highlights": highlights,
        "schedule_lines": schedule_lines,
        "reservation_note": "公式ページの案内に従う（自動抽出は参考）",
        "application_period_note": app_note or "各キャンパス・日程の予約は公式を参照",
        "catalog_season_warning": catalog_season_warning,
        "omit_table_schedule_dates": omit_table_schedule_dates,
    }

    canon = "|".join(
        [
            page_title,
            "##".join(highlights[:6]),
            "##".join(schedule_lines[:14]),
            catalog_season_warning,
        ]
    )
    fingerprint = hashlib.sha256(canon.encode("utf-8")).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized": normalized,
        "raw_text_sample": text_blob[:1800],
    }
