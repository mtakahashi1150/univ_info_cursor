"""東京理科大学 OC: /visittus/opencampus/ の「重要なお知らせ」（2026年春）と 2025夏アーカイブをキャンパス別に整理する。"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from univ_oc.parsers import generic as generic_mod


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _abs(base: str, href: str) -> str:
    return urljoin(base if base.endswith("/") else base + "/", href)


def parse(
    soup: BeautifulSoup,
    *,
    page_url: str,
    reservation_url: Optional[str],
) -> dict[str, Any]:
    base = generic_mod.parse(soup, page_url=page_url, reservation_url=reservation_url)
    norm = base["normalized"]
    link_top = page_url.split("#")[0].rstrip("/")

    campus_block_schedule: dict[str, dict[str, Any]] = {}
    schedule_lines: list[str] = []

    # --- 2026年春（重要なお知らせ）---
    notice_h2 = None
    for h2 in soup.find_all("h2"):
        if _norm(h2.get_text()) == "重要なお知らせ":
            notice_h2 = h2
            break
    if notice_h2:
        p = notice_h2.find_next_sibling("p")
        if p:
            blob = p.get_text("\n", strip=True)
            schedule_lines.append(_norm(blob.replace("\n", " "))[:400])
            for a in p.find_all("a", href=True):
                t = _norm(a.get_text())
                href = str(a["href"])
                if "野田" in t:
                    campus_block_schedule["野田キャンパス"] = {
                        "schedule_summary_line": f"2026年春 OC 予定: {t}（公式「重要なお知らせ」）",
                        "dept_line": "創域理工・創域情報（夏アーカイブ表記参照）",
                        "apply_links": [
                            {"label": "詳細（公式）", "url": _abs("https://www.tus.ac.jp/", href)},
                            {"label": "OCトップ", "url": link_top},
                        ],
                    }
                elif "葛飾" in t:
                    campus_block_schedule["葛飾キャンパス"] = {
                        "schedule_summary_line": f"2026年春 OC 予定: {t}（公式「重要なお知らせ」）",
                        "dept_line": "薬・工学・先進工学（夏アーカイブ表記参照）",
                        "apply_links": [
                            {"label": "詳細（公式）", "url": _abs("https://www.tus.ac.jp/", href)},
                            {"label": "OCトップ", "url": link_top},
                        ],
                    }

    # --- 2025夏アーカイブ（h2: 夏の野田オープンキャンパス 2025年8月9日(土)）---
    pat_summer = re.compile(
        r"^夏の(\S+?)オープンキャンパス\s+(\d{4})年(\d{1,2})月(\d{1,2})日",
    )
    campus_suffix = {"野田": "野田キャンパス", "葛飾": "葛飾キャンパス", "神楽坂": "神楽坂キャンパス"}
    for h2 in soup.find_all("h2"):
        t = _norm(h2.get_text())
        m = pat_summer.match(t)
        if not m:
            continue
        stem = m.group(1)
        y, mo, d = m.group(2), m.group(3), m.group(4)
        cname = campus_suffix.get(stem, f"{stem}キャンパス")
        line = f"{y}年{mo}月{d}日 夏のOC（アーカイブ・動画等は公式ページ）"
        if cname not in campus_block_schedule:
            campus_block_schedule[cname] = {
                "schedule_summary_line": line,
                "dept_line": "",
                "apply_links": [{"label": "OCトップ", "url": link_top}],
            }
        else:
            prev = campus_block_schedule[cname]["schedule_summary_line"]
            campus_block_schedule[cname]["schedule_summary_line"] = f"{prev} / {line}"

    # 神楽坂: 2026年春は「重要なお知らせ」に日付が無い場合の注記を先頭に
    if "神楽坂キャンパス" in campus_block_schedule:
        sk = campus_block_schedule["神楽坂キャンパス"]["schedule_summary_line"]
        campus_block_schedule["神楽坂キャンパス"]["schedule_summary_line"] = (
            "2026年春の日付は同ページの先頭告知では未掲載のため公式で確認 / " + sk
        )
    else:
        campus_block_schedule["神楽坂キャンパス"] = {
            "schedule_summary_line": (
                "2026年春の来校型OCは公式OCページで確認（本ページでは野田・葛飾の春予定が明示）"
            ),
            "dept_line": "理学第一部・第二部・経営（公式参照）",
            "apply_links": [{"label": "OCトップ", "url": link_top}],
        }

    norm["campus_block_schedule"] = campus_block_schedule
    norm["catalog_season_warning"] = (
        "※2025年度夏のOCアーカイブ・動画が同ページにあります。"
        "**2026年春の開催は「重要なお知らせ」の日付を優先して確認してください。**"
    )
    norm["omit_table_schedule_dates"] = False

    merged_sl = schedule_lines + [
        f"{k}: {v['schedule_summary_line'][:180]}"
        for k, v in sorted(campus_block_schedule.items())
    ]
    norm["schedule_lines"] = merged_sl[:24]
    norm["highlights"] = (schedule_lines + norm.get("highlights", []))[:8]

    canon = "|".join(
        [
            norm["page_title"],
            "##".join(merged_sl[:14]),
            str(sorted(campus_block_schedule.keys())),
        ]
    )
    base["fingerprint"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    base["normalized"] = norm
    return base
