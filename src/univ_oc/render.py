from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


def render_markdown_table(rows: list[dict[str, Any]]) -> str:
    """累積表（1 行 = 1 source）。"""
    lines = [
        "# オープンキャンパス情報（累積）",
        "",
        "自動取得のスナップショットです。URL は `config/sources.yaml` に手動で検証したものだけが入ります。",
        "",
        "| 大学名 | 学科名 | 申込期間・備考 | OC開催日・備考 | 申込URL | 案内ページURL | 最終取得(UTC) | 最終内容更新(UTC) | 検索ステータス |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(
            "| {university} | {dept} | {app_note} | {sched} | {res_url} | {page_url} | {fetch} | {change} | {status} |".format(
                university=r["university"],
                dept=r["department_label"],
                app_note=r["application_note"].replace("|", "\\|"),
                sched=r["schedule_summary"].replace("|", "\\|"),
                res_url=r["reservation_url"],
                page_url=r["page_url"],
                fetch=r["last_fetch_at"],
                change=r["last_content_change_at"],
                status=r["status"],
            )
        )
    lines.append("")
    lines.append(f"_Generated at {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}_")
    lines.append("")
    return "\n".join(lines)


def build_row(
    *,
    university: str,
    department_label: str,
    page_url: str,
    reservation_url: Optional[str],
    normalized: dict[str, Any],
    last_fetch_at: str,
    last_content_change_at: str,
    changed_this_run: bool,
    days_no_update: int,
) -> dict[str, Any]:
    sched = " / ".join(normalized.get("schedule_lines", [])[:4]) or "（ページ要確認）"
    if len(sched) > 200:
        sched = sched[:197] + "..."

    app_note = normalized.get("application_period_note", "")
    highlights = normalized.get("highlights", [])
    if highlights:
        app_note = (highlights[0] + " " + app_note).strip()

    if changed_this_run:
        status = "本実行で更新あり（フィンガープリント変化）"
    else:
        status = f"直近 {days_no_update} 日間、内容に変化なし"

    return {
        "university": university,
        "department_label": department_label,
        "application_note": app_note,
        "schedule_summary": sched,
        "reservation_url": reservation_url or "",
        "page_url": page_url,
        "last_fetch_at": last_fetch_at,
        "last_content_change_at": last_content_change_at,
        "status": status,
    }
