"""芝浦工業大学 OC: og:description 等から大宮・豊洲の開催日を分離（ページが前年度終了表示の場合は警告維持）。"""

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

    og = soup.find("meta", property="og:description")
    desc = _norm(og.get("content", "")) if og and og.get("content") else ""

    campus_block_schedule: dict[str, dict[str, Any]] = {}
    link = page_url.split("#")[0].rstrip("/")

    # 例: 大宮キャンパスで8月2日(土)、3日(日)、豊洲キャンパスで8月23日(土)、24日(日)に開催
    m_omiya = re.search(
        r"大宮キャンパスで([^、]+?)、([^、]+?)(?:、|，)?豊洲",
        desc,
    )
    m_toyosu = re.search(
        r"豊洲キャンパスで([^。]+?)(?:に開催|開催)",
        desc,
    )
    if m_omiya:
        campus_block_schedule["大宮キャンパス"] = {
            "schedule_summary_line": f"大宮: {m_omiya.group(1)}・{m_omiya.group(2)}（og:description 掲載）",
            "dept_line": "工学部・システム理工学域ほか（公式参照）",
            "apply_links": [{"label": "日程・詳細", "url": link}],
        }
    if m_toyosu:
        campus_block_schedule["豊洲キャンパス"] = {
            "schedule_summary_line": f"豊洲: {_norm(m_toyosu.group(1))}（og:description 掲載）",
            "dept_line": "理工系OCの会場の一つ（公式参照）",
            "apply_links": [{"label": "日程・詳細", "url": link}],
        }

    if campus_block_schedule:
        norm["campus_block_schedule"] = campus_block_schedule
        extra = [f"{k}: {v['schedule_summary_line']}" for k, v in campus_block_schedule.items()]
        norm["schedule_lines"] = extra + [x for x in norm.get("schedule_lines", []) if x not in extra][:12]

    canon = "|".join(
        [
            norm["page_title"],
            desc,
            str(sorted(campus_block_schedule.keys())),
            "##".join(norm.get("schedule_lines", [])[:8]),
            norm.get("catalog_season_warning", ""),
        ]
    )
    base["fingerprint"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    base["normalized"] = norm
    return base
