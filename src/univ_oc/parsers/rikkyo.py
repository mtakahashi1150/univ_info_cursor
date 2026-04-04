"""立教大学 オープンキャンパス（池袋・新座の別セクションを分離）。"""

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
    return f"{base}#{frag}"


def _wysiwyg_after_h2(soup: BeautifulSoup, h2_id: str, want_substring: str) -> str:
    h2 = soup.find("h2", id=h2_id)
    if not h2:
        return ""
    for div in h2.find_all_next("div", class_=True, limit=40):
        cl = div.get("class") or []
        cs = " ".join(cl) if isinstance(cl, list) else str(cl)
        if "p-image-set" not in cs:
            continue
        h4 = div.find("h4", class_="w-title4")
        if not h4 or want_substring not in h4.get_text():
            continue
        wg = div.select_one(".wysiwyg")
        if wg:
            return wg.get_text("\n", strip=True)
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

    ike_blob = _wysiwyg_after_h2(soup, "池袋キャンパス", "開催日時")
    nii_blob = _wysiwyg_after_h2(soup, "新座キャンパス", "開催日時")

    if ike_blob:
        campus_block_schedule["池袋キャンパス"] = {
            "schedule_summary_line": ike_blob[:1200],
            "dept_line": "（日程ごとに対象学部が異なります。公式の池袋セクションを参照）",
            "apply_links": [
                {"label": "池袋：日程・予約案内", "url": _page_with_frag(page_url, "池袋キャンパス")},
            ],
        }
    if nii_blob:
        campus_block_schedule["新座キャンパス"] = {
            "schedule_summary_line": nii_blob[:800],
            "dept_line": "（新座は予約不要・入退場自由。公式の新座セクションを参照）",
            "apply_links": [
                {"label": "新座：日程案内", "url": _page_with_frag(page_url, "新座キャンパス")},
            ],
        }

    schedule_lines: list[str] = []
    for bid, blob in [("池袋", ike_blob), ("新座", nii_blob)]:
        if blob:
            schedule_lines.append(f"【{bid}】" + _norm(blob.replace("\n", " "))[:200])

    highlights: list[str] = []
    for a in soup.find_all("a", href=True, limit=40):
        t = _norm(a.get_text())
        if "オープンキャンパス" in t and len(t) > 8 and t not in highlights:
            highlights.append(t)
        if len(highlights) >= 6:
            break

    normalized = {
        "page_title": page_title,
        "highlights": highlights,
        "schedule_lines": schedule_lines or ["オープンキャンパス（公式ページで池袋・新座を確認）"],
        "reservation_note": "池袋の一部プログラムは事前予約（マイページ）。詳細は公式参照。",
        "application_period_note": "予約受付は公式記載の時期にマイページから（自動抽出は参考）",
        "catalog_season_warning": "",
        "campus_block_schedule": campus_block_schedule,
    }

    cbs_ser = json.dumps(campus_block_schedule, ensure_ascii=False, sort_keys=True)
    canon = "|".join(
        [
            page_title,
            "##".join(normalized["schedule_lines"]),
            cbs_ser,
        ]
    )
    fingerprint = hashlib.sha256(canon.encode("utf-8")).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized": normalized,
        "raw_text_sample": text_blob[:1800],
    }
