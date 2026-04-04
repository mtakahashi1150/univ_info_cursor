"""上智大学: 入試サイト「イベント・オープンキャンパス」一覧（/jpn/event_ad/）から四谷・目白向け日程を抽出する。"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _items_yotsuya_mejiro_section(soup: BeautifulSoup) -> list[dict[str, str]]:
    """見出し「【四谷キャンパス・目白聖母キャンパス】」直下の最初の c-scheduleList のみ。"""
    out: list[dict[str, str]] = []
    for h2 in soup.find_all("h2", class_="c-decHeading3t4"):
        t = _norm(h2.get_text())
        if "四谷キャンパス" not in t or "目白聖母" not in t:
            continue
        sticky = h2.find_parent("div", class_="c-stickyBlock")
        if not sticky or not isinstance(sticky, Tag):
            continue
        contents = sticky.find("div", class_="c-stickyBlock__contents")
        if not contents or not isinstance(contents, Tag):
            continue
        sched_list = contents.find("div", class_="c-scheduleList")
        if not sched_list or not isinstance(sched_list, Tag):
            continue
        for dl in sched_list.find_all("dl", class_="c-scheduleItem"):
            if not isinstance(dl, Tag):
                continue
            dt = dl.find("dt")
            dd = dl.find("dd")
            if not dt or not dd:
                continue
            t_el = dt.select_one("time[datetime]")
            date_iso = (t_el.get("datetime") or "").strip() if t_el else ""
            date_disp = _norm(t_el.get_text()) if t_el else ""
            ts = dt.select_one("time.-start")
            te = dt.select_one("time.-end")
            t_start = _norm(ts.get_text()) if ts else ""
            t_end = _norm(te.get_text()) if te else ""
            time_part = ""
            if t_start and t_end:
                time_part = f"{t_start}–{t_end}"
            elif t_start:
                time_part = t_start

            a = dd.find("a", href=True)
            detail_url = str(a["href"]).strip() if a and a.get("href") else ""
            title = _norm(dd.get_text(" ", strip=True))

            line = " ".join(x for x in (date_disp or date_iso, time_part, title) if x)
            out.append(
                {
                    "line": line,
                    "date_iso": date_iso,
                    "detail_url": detail_url,
                }
            )
        break
    return out


def parse(
    soup: BeautifulSoup,
    *,
    page_url: str,
    reservation_url: Optional[str],
) -> dict[str, Any]:
    title_el = soup.find("title")
    page_title = _norm(title_el.get_text()) if title_el else ""

    base = page_url.split("#")[0].rstrip("/")
    items = _items_yotsuya_mejiro_section(soup)

    schedule_lines = [it["line"] for it in items]
    if not schedule_lines:
        schedule_lines.append("（四谷・目白のイベント一覧の抽出に失敗。公式のイベントページを確認）")

    summary_blob = " / ".join(schedule_lines)[:900]

    apply_links: list[dict[str, str]] = [{"label": "イベント・OC一覧", "url": base}]
    seen: set[str] = {base}
    for it in items:
        u = it.get("detail_url") or ""
        if u and u not in seen:
            seen.add(u)
            apply_links.append(
                {
                    "label": "詳細",
                    "url": u if u.startswith(("http://", "https://")) else urljoin(base + "/", u),
                }
            )

    campus_block_schedule = {
        "四谷キャンパス": {
            "schedule_summary_line": summary_blob,
            "dept_line": "理工学部（情報理工学科ほか）・OCは一覧の【理工】表記イベントを参照",
            "apply_links": list(apply_links),
        },
        "目白聖母キャンパス": {
            "schedule_summary_line": summary_blob,
            "dept_line": "同一ページに四谷・目白向けイベントを掲載（キャンパス別詳細は公式イベントを確認）",
            "apply_links": list(apply_links),
        },
    }

    note_805 = ""
    if any("2026-08-05" in it.get("date_iso", "") for it in items):
        note_805 = (
            "※2026年8月5日の項目は、公式見出しが「SOPHIA OPEN CAMPUS 2025」表記です。"
            "日程・対象学部は必ず公式ページで確認してください。"
        )

    normalized = {
        "page_title": page_title,
        "highlights": schedule_lines[:8],
        "schedule_lines": schedule_lines[:16],
        "reservation_note": "公式ページの案内に従う（自動抽出は参考）",
        "application_period_note": "各イベントの事前申込は公式を参照",
        "catalog_season_warning": note_805,
        "omit_table_schedule_dates": False,
        "campus_block_schedule": campus_block_schedule,
    }

    canon = "|".join([page_title, "##".join(schedule_lines), note_805])
    fingerprint = hashlib.sha256(canon.encode("utf-8")).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized": normalized,
        "raw_text_sample": summary_blob[:1800],
    }
