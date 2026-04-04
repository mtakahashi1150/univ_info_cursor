from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any, Optional


def _md_table_cell(value: Optional[str]) -> str:
    """Markdown 表セル内の | や改行で表が壊れないようにする。"""
    if value is None:
        return ""
    s = str(value).replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
    return s.replace("|", "\\|")


def render_catalog_markdown(catalog: dict[str, Any]) -> str:
    """target_catalog.yaml から一覧表を生成。"""
    lines: list[str] = [
        "## 対象エリア・グループ・大学別（情報工学・情報科学系の整理）",
        "",
    ]
    meta = catalog.get("meta") or {}
    ap = meta.get("area_prefectures", [])
    if ap:
        lines.append(f"- **対象エリア（都県）**: {' / '.join(ap)}")
    if meta.get("focus"):
        lines.append(f"- **情報系の扱い**: {meta['focus']}")
    if meta.get("groups_note"):
        lines.append(f"- **グループ**: {meta['groups_note']}")
    lines.append("")
    lines.append("### 大学一覧（学部・学科と主な OC キャンパス）")
    lines.append("")
    lines.append("| グループ | 大学名 | 情報系として追う学部・学科 | OC キャンパス | 都県 | メモ |")
    lines.append("| --- | --- | --- | --- | --- | --- |")

    for u in catalog.get("universities", []):
        gname = u.get("group", "")
        name = u.get("name", "")
        depts_raw = "<br>".join(u.get("info_departments", []))
        for i, oc in enumerate(u.get("oc_campuses", [])):
            lines.append(
                "| {g} | {n} | {d} | {c} | {p} | {note} |".format(
                    g=gname.replace("|", "\\|") if i == 0 else "〃",
                    n=name.replace("|", "\\|") if i == 0 else "〃",
                    d=depts_raw.replace("|", "\\|") if i == 0 else "〃",
                    c=str(oc.get("campus", "")).replace("|", "\\|"),
                    p=str(oc.get("prefecture", "")).replace("|", "\\|"),
                    note=str(oc.get("note", "")).replace("|", "\\|"),
                )
            )
    lines.append("")
    lines.append(
        "> 学習院大学は独立の情報工学・情報科学学部がないため、**自動取得（sources）は登録していません**。"
        " カタログには参考として掲載しています。"
    )
    lines.append("")
    return "\n".join(lines)


def render_update_summary_block(rows: list[dict[str, Any]]) -> str:
    """今回の実行で差分があった大学のサマリー（文書先頭用）。"""
    changed = [r for r in rows if r.get("changed_this_run")]
    lines = [
        "## 今回の更新サマリー",
        "",
    ]
    if not changed:
        lines.append(
            "直近の取得では、保存済みスナップショットと**差分はありませんでした**"
            "（公式ページのフィンガープリント一致）。"
        )
        lines.append("")
        return "\n".join(lines)

    lines.append("次の大学で、公式ページから取得した内容に**変化**が検知されています。")
    lines.append("")
    for r in changed:
        uni = r.get("university", "")
        snip = r.get("update_snippet") or "掲載内容の変化"
        lines.append(f"- **{uni}**: {snip}")
    lines.append("")
    lines.append(
        "下の「一覧」表の **NEW** 列と、詳細カード左の強調枠・**NEW** バッジで同じ箇所が分かります。"
    )
    lines.append("")
    return "\n".join(lines)


def render_quick_jump_table(rows: list[dict[str, Any]]) -> str:
    """スマホでも横スクロールほぼ不要なジャンプ用の簡易表。"""
    lines = [
        "### 大学一覧（詳細へジャンプ）",
        "",
        "| 大学 | 今回 |",
        "| --- | --- |",
    ]
    for r in rows:
        sid = r.get("source_id", "")
        uni = _md_table_cell(r.get("university", ""))
        mark = "**NEW**" if r.get("changed_this_run") else "—"
        if sid:
            lines.append(f"| [{uni}](#{sid}) | {mark} |")
        else:
            lines.append(f"| {uni} | {mark} |")
    lines.append("")
    return "\n".join(lines)


def _schedule_bullets(schedule_summary: str, limit: int = 10) -> str:
    parts = [p.strip() for p in schedule_summary.split(" / ") if p.strip()]
    if not parts:
        return "    - （公式ページで日程を確認してください）"
    return "\n".join(f"    - {p}" for p in parts[:limit])


def _external_links_html(page_url: str, reservation_url: str) -> str:
    """公式サイトは別タブで開く（表示はラベルのみ）。"""
    chunks: list[str] = []
    if page_url:
        u = html.escape(page_url, quote=True)
        chunks.append(
            f'<a href="{u}" target="_blank" rel="noopener noreferrer">オープンキャンパス案内</a>'
        )
    if reservation_url:
        u = html.escape(reservation_url, quote=True)
        chunks.append(
            f'<a href="{u}" target="_blank" rel="noopener noreferrer">申込・予約の案内</a>'
        )
    if not chunks:
        return "（このソースでは案内リンクのみ別途確認）"
    return " ・ ".join(chunks)


def render_oc_detail_cards(rows: list[dict[str, Any]]) -> str:
    """累積情報をカード状（OC 内容優先・リンクはラベルのみ）。"""
    n = len(rows)
    lines: list[str] = [
        "## オープンキャンパス情報（累積・自動取得）",
        "",
        f"`config/sources.yaml` の検証済み URL から取得したスナップショットです（**全 {n} 件**）。",
        "",
    ]
    for r in rows:
        sid = r.get("source_id", "row")
        is_new = bool(r.get("changed_this_run"))
        klass = "oc-card oc-card--updated" if is_new else "oc-card"
        uni = r.get("university", "")
        uni_esc = html.escape(uni)

        safe_id = sid.replace('"', "").replace("'", "") if sid else "row"
        lines.append(f'<div class="{klass}" id="{html.escape(safe_id)}" markdown="1">')
        lines.append("")
        if is_new:
            lines.append(
                f'<h3 class="oc-title">{uni_esc} '
                f'<span class="oc-new-badge">NEW</span></h3>'
            )
        else:
            lines.append(f'<h3 class="oc-title">{uni_esc}</h3>')
        lines.append("")
        cw = (r.get("catalog_season_warning") or "").strip()
        if cw:
            lines.append(f'<p class="oc-catalog-warning">{html.escape(cw)}</p>')
            lines.append("")
        lines.append("- **OC 日程・プログラム**")
        lines.append(_schedule_bullets(r.get("schedule_summary") or ""))
        app = r.get("application_note") or ""
        app_esc = _md_table_cell(app) if app else ""
        lines.append(f"- **申込・更新メモ**: {app_esc or '—'}")
        lines.append(
            f"- **公式リンク**: {_external_links_html(r.get('page_url') or '', r.get('reservation_url') or '')}"
        )
        meta = (
            f"{r.get('university_group', '')} / {r.get('department_label', '')} / "
            f"{r.get('campus_label', '')} / 対象エリア: {r.get('area_prefectures_str', '')}"
        )
        lines.append(f"- **大学・学部・キャンパス**: {meta}")
        lines.append(
            f"- **最終取得(UTC)** `{r.get('last_fetch_at', '')}` ・ "
            f"**最終内容更新(UTC)** `{r.get('last_content_change_at', '')}` ・ {r.get('status', '')}"
        )
        lines.append("")
        lines.append("</div>")
        lines.append("")

    lines.append(f"_Generated at {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}_")
    lines.append("")
    return "\n".join(lines)


def build_row(
    *,
    source_id: str,
    university_group: str,
    university: str,
    department_label: str,
    campus_label: str,
    area_prefectures: list[str],
    page_url: str,
    reservation_url: Optional[str],
    normalized: dict[str, Any],
    last_fetch_at: str,
    last_content_change_at: str,
    changed_this_run: bool,
    days_no_update: int,
) -> dict[str, Any]:
    sched = " / ".join(normalized.get("schedule_lines", [])[:4]) or "（ページ要確認）"
    if len(sched) > 220:
        sched = sched[:217] + "..."

    app_note = normalized.get("application_period_note", "")
    highlights = normalized.get("highlights", [])
    if highlights:
        app_note = (highlights[0] + " " + app_note).strip()

    hl = normalized.get("highlights") or []
    sl = normalized.get("schedule_lines") or []
    if hl:
        update_snippet = ", ".join(hl[:3])
    elif sl:
        update_snippet = (" / ".join(sl[:2]))[:220]
    else:
        update_snippet = "公式ページ上の掲載内容に変化が検知されました"

    if changed_this_run:
        status = "本実行で更新あり（フィンガープリント変化）"
    else:
        status = f"直近 {days_no_update} 日間、内容に変化なし"

    catalog_season_warning = (normalized.get("catalog_season_warning") or "").strip()

    return {
        "source_id": source_id,
        "university_group": university_group,
        "university": university,
        "department_label": department_label,
        "campus_label": campus_label,
        "area_prefectures_str": "・".join(area_prefectures),
        "application_note": app_note,
        "schedule_summary": sched,
        "reservation_url": reservation_url or "",
        "page_url": page_url,
        "last_fetch_at": last_fetch_at,
        "last_content_change_at": last_content_change_at,
        "status": status,
        "changed_this_run": changed_this_run,
        "update_snippet": update_snippet,
        "catalog_season_warning": catalog_season_warning,
    }


def render_full_document(catalog: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    """先頭: 更新サマリー → 簡易一覧表 → OC 詳細カード → 末尾: 対象カタログ表。"""
    title = "# オープンキャンパス情報（早慶上理・G-MARCH・情報系・首都圏）"
    ordered = sorted(
        rows,
        key=lambda r: (not r.get("changed_this_run", False), r.get("university", "")),
    )
    parts = [
        title,
        "",
        render_update_summary_block(ordered),
        render_quick_jump_table(ordered),
        render_oc_detail_cards(ordered),
        "---",
        "",
        render_catalog_markdown(catalog),
    ]
    return "\n".join(parts)
