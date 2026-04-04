"""青山学院大学 オープンキャンパス（1ページ内のキャンパス別ブロックを分離）。"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Optional

from bs4 import BeautifulSoup


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _page_with_frag(page_url: str, frag: str) -> str:
    base = (page_url or "").split("#")[0].rstrip("/")
    return f"{base}#{frag.lstrip('#')}"


def _block_for_anchor(soup: BeautifulSoup, anchor_id: str) -> str:
    span = soup.find("span", id=anchor_id)
    if not span:
        return ""
    for p in span.find_all_next("p", class_=True, limit=12):
        cl = p.get("class") or []
        cs = " ".join(cl) if isinstance(cl, list) else str(cl)
        if "parabox2_text" not in cs:
            continue
        t = p.get_text("\n", strip=True)
        if "開催" in t or "2026" in t or "2025" in t:
            return t
    return ""


def parse(
    soup: BeautifulSoup,
    *,
    page_url: str,
    reservation_url: Optional[str],
) -> dict[str, Any]:
    title_el = soup.find("title")
    page_title = _norm(title_el.get_text()) if title_el else ""

    body = soup.find("main") or soup.body
    text_blob = _norm(body.get_text()) if body else ""

    campus_block_schedule: dict[str, dict[str, Any]] = {}

    blocks_cfg = [
        ("anchor_01", "相模原キャンパス", "相模原OCの案内"),
        ("anchor_02", "青山キャンパス", "青山OCの案内"),
    ]
    schedule_lines: list[str] = []
    for aid, cname, label in blocks_cfg:
        raw = _block_for_anchor(soup, aid)
        if not raw:
            continue
        first_line = raw.split("\n")[0].strip() if raw else ""
        summary = _norm(first_line)[:220] if first_line else _norm(raw)[:220]
        if summary and summary not in schedule_lines:
            schedule_lines.append(summary)
        detail_url = _page_with_frag(page_url, aid)
        dept_hint = ""
        if "対象学部" in raw:
            for line in raw.split("\n"):
                if "対象学部" in line:
                    dept_hint = _norm(line)[:300]
                    break
        apply_links = [{"label": label, "url": detail_url}]
        campus_block_schedule[cname] = {
            "schedule_summary_line": summary + "\n" + raw[:800],
            "dept_line": dept_hint,
            "apply_links": apply_links,
        }

    highlights: list[str] = []
    for a in soup.find_all("a", href=True, limit=60):
        t = _norm(a.get_text())
        if len(t) < 10:
            continue
        if "オープンキャンパス" in t and t not in highlights:
            highlights.append(t)
        if len(highlights) >= 6:
            break

    catalog_season_warning = ""
    if "2025年度" in page_title and "2026年" not in text_blob[:8000]:
        catalog_season_warning = (
            "※ページタイトルが2025年度表記です。**本文の開催日は公式ページで必ず確認してください。**"
        )

    normalized = {
        "page_title": page_title,
        "highlights": highlights,
        "schedule_lines": schedule_lines[:15] or ["オープンキャンパス（キャンパス別は公式ページのアンカー参照）"],
        "reservation_note": "公式ページの案内に従う（自動抽出は参考）",
        "application_period_note": "各キャンパスで申込時期・方法が異なる場合があります（公式参照）",
        "catalog_season_warning": catalog_season_warning,
        "campus_block_schedule": campus_block_schedule,
    }

    cbs_ser = json.dumps(campus_block_schedule, ensure_ascii=False, sort_keys=True)
    canon = "|".join(
        [
            page_title,
            "##".join(normalized["schedule_lines"][:10]),
            cbs_ser,
            catalog_season_warning,
        ]
    )
    fingerprint = hashlib.sha256(canon.encode("utf-8")).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized": normalized,
        "raw_text_sample": text_blob[:1800],
    }
