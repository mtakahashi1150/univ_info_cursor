"""早稲田大学 入学センター OC ページ: キャンパス×開催日時×対象学部の表から、情報理工系対象行を抽出する。"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from bs4 import BeautifulSoup

# sources / target_catalog で追う理工系（独立「情報学部」がなくても情報理工系を含む）
_INFO_SCI_FACULTY_MARKERS = (
    "基幹理工",
    "創造理工",
    "先進理工",
    "情報理工",
)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _cell_text(el) -> str:
    return _norm(el.get_text(" ", strip=True))


def _row_matches_focus(faculties_text: str) -> bool:
    if not faculties_text:
        return False
    return any(m in faculties_text for m in _INFO_SCI_FACULTY_MARKERS)


def _parse_tokyo_campus_table(table: Any) -> tuple[list[str], list[str]]:
    """キャンパス / 開催日時 / 対象学部 の表から、フォーカス学部を含む行だけ返す。"""
    schedule_lines: list[str] = []
    highlights: list[str] = []

    first_tr = table.find("tr")
    if not first_tr:
        return schedule_lines, highlights
    header_blob = _cell_text(first_tr)
    if "キャンパス" not in header_blob or "開催日時" not in header_blob or "対象学部" not in header_blob:
        return schedule_lines, highlights

    tbody = table.find("tbody") or table
    trs = tbody.find_all("tr", recursive=False)
    if len(trs) < 2:
        return schedule_lines, highlights

    start = 1 if "キャンパス" in _cell_text(trs[0].find("th") or trs[0]) else 0
    last_date = ""

    for tr in trs[start:]:
        cells = tr.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        c0 = cells[0]
        if c0.name != "th":
            continue
        campus = _cell_text(c0)
        if campus == "キャンパス":
            continue

        rest = cells[1:]
        dt = last_date
        fac = ""

        if not rest:
            continue
        first = rest[0]
        if first.name == "td":
            t0 = _cell_text(first)
            if re.search(r"\d{4}\s*年", t0) or re.search(r"\d{1,2}\s*月", t0):
                dt = t0.replace(" ", "")
                last_date = dt
                if len(rest) > 1:
                    fac = _cell_text(rest[1])
            else:
                fac = t0
        if not fac and len(rest) > 1:
            fac = _cell_text(rest[1])

        if not _row_matches_focus(fac):
            continue

        line = f"【{campus}】{dt} {fac}"
        schedule_lines.append(line)
        highlights.append(line if len(line) <= 200 else line[:197] + "...")

    return schedule_lines, highlights


def _section_intro(soup: BeautifulSoup, section_id: str) -> str:
    hdr = soup.find(id=section_id)
    if not hdr:
        return ""
    wp = hdr.find_next("div", class_=lambda c: c and "wp-text" in c.split())
    if not wp:
        return ""
    p = wp.find("p")
    if not p:
        return ""
    return _norm(p.get_text())


def parse(
    soup: BeautifulSoup,
    *,
    page_url: str,
    reservation_url: Optional[str],
) -> dict[str, Any]:
    title_el = soup.find("title")
    page_title = _norm(title_el.get_text()) if title_el else ""

    intro = _section_intro(soup, "anc_4")
    all_sched: list[str] = []
    all_high: list[str] = []

    if intro and re.search(r"\d{1,2}\s*月", intro):
        all_sched.append(f"（概要）{intro}")

    def _bordered_table(tag) -> bool:
        if tag.name != "table":
            return False
        cls = tag.get("class") or []
        if isinstance(cls, str):
            cls = cls.split()
        return "table-bordered" in cls

    for table in soup.find_all(_bordered_table):
        sl, hl = _parse_tokyo_campus_table(table)
        all_sched.extend(sl)
        all_high.extend(hl)

    if not all_sched:
        for tag in soup.find_all(["h1", "h2", "h3"]):
            t = _norm(tag.get_text())
            if "オープンキャンパス" in t and "2026" in t:
                all_sched.append(t)
        if not all_sched:
            all_sched.append("（表の抽出に失敗しました。公式ページで確認してください）")

    normalized = {
        "page_title": page_title,
        "highlights": (all_high[:8] if all_high else all_sched[:4])[:8],
        "schedule_lines": all_sched[:20],
        "reservation_note": "公式ページの案内に従う（自動抽出は参考）",
        "application_period_note": "各キャンパス・日程の予約は公式を参照",
    }

    canon = "|".join(
        [
            page_title,
            "##".join(normalized["highlights"][:8]),
            "##".join(normalized["schedule_lines"][:16]),
        ]
    )
    fingerprint = hashlib.sha256(canon.encode("utf-8")).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized": normalized,
        "raw_text_sample": "",
    }
