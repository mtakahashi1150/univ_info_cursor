"""明治大学 入試総合サイト オープンキャンパスページ用パーサー。"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Optional

from bs4 import BeautifulSoup


def _norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _page_url_with_fragment(page_url: str, fragment: str) -> str:
    base = (page_url or "").split("#")[0].rstrip("/")
    frag = fragment.lstrip("#")
    return f"{base}#{frag}" if base else f"#{frag}"


_CAMPUS_MAP = {
    "駿河台": "駿河台キャンパス",
    "中野": "中野キャンパス",
    "生田": "生田キャンパス",
}


def _build_campus_block_schedule(
    soup: BeautifulSoup,
    *,
    page_url: str,
    reservation_url: Optional[str],
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for jp, catalog_name in _CAMPUS_MAP.items():
        h3 = None
        for cand in soup.select("h3.title"):
            t = _norm_text(cand.get_text())
            if t.startswith(f"【{jp}】"):
                h3 = cand
                break
        if not h3 or not h3.get("id"):
            continue
        title_line = _norm_text(h3.get_text())
        dept_line = ""
        sec = h3.find_parent("section")
        if sec:
            h4 = sec.find("h4", class_="title")
            if h4:
                dt = _norm_text(h4.get_text())
                if dt.startswith("実施学部"):
                    dept_line = dt
        frag = h3.get("id", "")
        detail_url = _page_url_with_fragment(page_url, frag)
        apply_links: list[dict[str, str]] = [
            {"label": "このキャンパスの日程・学部", "url": detail_url},
        ]
        if reservation_url:
            apply_links.append({"label": "申込（LINE）", "url": reservation_url})
        out[catalog_name] = {
            "schedule_summary_line": title_line,
            "dept_line": dept_line,
            "apply_links": apply_links,
        }
    return out


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

    campus_block_schedule = _build_campus_block_schedule(
        soup, page_url=page_url, reservation_url=reservation_url
    )

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
        "campus_block_schedule": campus_block_schedule,
    }

    cbs_ser = json.dumps(campus_block_schedule, ensure_ascii=False, sort_keys=True)
    canon = "|".join(
        [
            page_title,
            "##".join(normalized["highlights"]),
            "##".join(normalized["schedule_lines"]),
            cbs_ser,
        ]
    )
    fingerprint = hashlib.sha256(canon.encode("utf-8")).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized": normalized,
        "raw_text_sample": text_blob[:2000],
    }
