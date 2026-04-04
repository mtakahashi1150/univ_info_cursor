"""中央大学 OC2026 LP: section#tama / #kourakuen / #itl からキャンパス別の開催日・学部リストを抽出する。"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from bs4 import BeautifulSoup
from bs4.element import Tag


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _block_from_campus_section(sec: Tag, page_url: str, fragment: str) -> dict[str, Any]:
    date_txt = ""
    depts: list[str] = []
    fig = sec.find("figure", class_="campus_figure")
    if fig and isinstance(fig, Tag):
        dt = fig.select_one("span.date")
        if dt:
            date_txt = _norm(dt.get_text())
        for li in fig.select("ol.campus_list li"):
            t = _norm(li.get_text())
            if t:
                depts.append(t)
    base = page_url.split("#")[0].rstrip("/")
    link = f"{base}#{fragment}" if fragment else base
    sched = f"開催 {date_txt}" if date_txt else "（開催日は公式ページの該当セクションを確認）"
    return {
        "schedule_summary_line": sched,
        "dept_line": "・".join(depts)[:220],
        "apply_links": [{"label": "日程・詳細（公式）", "url": link}],
    }


def parse(
    soup: BeautifulSoup,
    *,
    page_url: str,
    reservation_url: Optional[str],
) -> dict[str, Any]:
    title_el = soup.find("title")
    page_title = _norm(title_el.get_text()) if title_el else ""

    campus_block_schedule: dict[str, dict[str, Any]] = {}
    mapping: list[tuple[str, str]] = [
        ("多摩キャンパス", "tama"),
        ("後楽園キャンパス", "kourakuen"),
        ("市ヶ谷田町キャンパス", "itl"),
    ]
    for campus_name, sec_id in mapping:
        sec = soup.find("section", id=sec_id)
        if sec and isinstance(sec, Tag):
            campus_block_schedule[campus_name] = _block_from_campus_section(sec, page_url, sec_id)

    schedule_lines: list[str] = []
    for name, block in campus_block_schedule.items():
        d = (block.get("dept_line") or "").strip()
        s = (block.get("schedule_summary_line") or "").strip()
        schedule_lines.append(f"{name}: {s}" + (f"（{d}）" if d else ""))

    mini = soup.select_one("section.a_minioc h3.minioc_day span.date")
    if mini:
        schedule_lines.append(f"ミニオープンキャンパスin多摩: {_norm(mini.get_text())}")

    if not schedule_lines:
        schedule_lines.append("（公式ページでキャンパス別日程を確認してください）")

    normalized = {
        "page_title": page_title,
        "highlights": schedule_lines[:6],
        "schedule_lines": schedule_lines[:20],
        "reservation_note": "公式ページの案内に従う（自動抽出は参考）",
        "application_period_note": "各キャンパス・日程の予約は公式を参照",
        "catalog_season_warning": "",
        "omit_table_schedule_dates": False,
        "campus_block_schedule": campus_block_schedule,
    }

    canon = "|".join(
        [
            page_title,
            "##".join(schedule_lines[:12]),
            str(sorted(campus_block_schedule.keys())),
        ]
    )
    fingerprint = hashlib.sha256(canon.encode("utf-8")).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized": normalized,
        "raw_text_sample": "",
    }
