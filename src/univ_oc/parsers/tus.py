"""東京理科大学 OC: h2 の「◯◯キャンパス（YYYY年M月D日開催）」をキャンパス別に抽出（URL が過去年度でも本文構造は維持）。"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from bs4 import BeautifulSoup

from univ_oc.parsers import generic as generic_mod


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def parse(
    soup: BeautifulSoup,
    *,
    page_url: str,
    reservation_url: Optional[str],
) -> dict[str, Any]:
    base = generic_mod.parse(soup, page_url=page_url, reservation_url=reservation_url)
    norm = base["normalized"]
    link = page_url.split("#")[0].rstrip("/")

    campus_block_schedule: dict[str, dict[str, Any]] = {}
    pat = re.compile(r"^(.+キャンパス)[（(](.+?)[）)]$")
    for h2 in soup.find_all("h2"):
        t = _norm(h2.get_text())
        m = pat.match(t)
        if not m:
            continue
        name, inner = m.group(1), m.group(2)
        campus_block_schedule[name] = {
            "schedule_summary_line": inner,
            "dept_line": "創域情報・工学・先進工学ほか（キャンパスにより異なる）",
            "apply_links": [{"label": "日程・詳細", "url": link}],
        }

    if campus_block_schedule:
        norm["campus_block_schedule"] = campus_block_schedule

    canon = "|".join(
        [
            norm["page_title"],
            norm.get("catalog_season_warning", ""),
            str(sorted(campus_block_schedule.keys())),
            "##".join(norm.get("schedule_lines", [])[:8]),
        ]
    )
    base["fingerprint"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    base["normalized"] = norm
    return base
