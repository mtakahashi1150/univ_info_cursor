from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Any, Optional, Union

# 表示順: 早慶上理 → G-MARCH → 東京4理工 → その他
_UNIV_RANK: dict[str, int] = {
    "早稲田大学": 10,
    "慶應義塾大学": 11,
    "上智大学": 12,
    "東京理科大学": 13,
    "明治大学": 20,
    "青山学院大学": 21,
    "立教大学": 22,
    "中央大学": 23,
    "法政大学": 24,
    "芝浦工業大学": 30,
    "東京都市大学": 31,
    "東京電機大学": 32,
    "工学院大学": 33,
    "東京工科大学": 90,
}


def _md_table_cell(value: Optional[str]) -> str:
    if value is None:
        return ""
    s = str(value).replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
    return s.replace("|", "\\|")


def _dedupe_date_substrings(phrases: list[str]) -> list[str]:
    """「2026年8月4日」と「8月4日」のように長い表記に含まれる短い表記を除く。"""
    out: list[str] = []
    for s in phrases:
        if any(t != s and len(t) > len(s) and s in t for t in phrases):
            continue
        if s not in out:
            out.append(s)
    return out


def extract_schedule_dates_only_from_blob(blob: str) -> str:
    """任意テキストから表用の日付断片を抽出（立教の 8/3（月）形式を含む）。"""
    if not blob or not blob.strip():
        return "—"
    found: list[str] = []
    for pat in (
        r"\d{4}年\d{1,2}月\d{1,2}日(?:\([日月火水木金土]\)|（[^）]+）)?",
        r"\d{1,2}月\d{1,2}日(?:\([日月火水木金土]\)|（[^）]+）)?",
        r"、\d{1,2}日(?:\([日月火水木金土]\)|（[日月火水木金土]）)",
        r"\d{4}/\d{1,2}/\d{1,2}",
        r"\d{1,2}/\d{1,2}（[日月火水木金土]）",
    ):
        for m in re.findall(pat, blob):
            if m.startswith("、"):
                m = m[1:]
            if m not in found:
                found.append(m)
    found = _dedupe_date_substrings(found)
    return "、".join(found[:14]) if found else "—"


def extract_schedule_dates_only(normalized: dict[str, Any], schedule_summary: str) -> str:
    """表用: 日付らしき部分だけ抽出。"""
    blob = schedule_summary + "\n" + "\n".join(normalized.get("schedule_lines") or [])
    return extract_schedule_dates_only_from_blob(blob)


def sort_base_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda r: (
            _UNIV_RANK.get(r.get("university") or "", 50),
            r.get("university") or "",
            r.get("source_id") or "",
        ),
    )


def _parse_campus_access_value(val: Union[str, dict[str, Any], None]) -> tuple[str, str]:
    """YAML の値が str または {access,duration} 辞書のとき、(逗子から目安, 所要目安) を返す。"""
    if val is None:
        return "（目安未設定・公式で確認）", "—"
    if isinstance(val, dict):
        acc = str(val.get("access") or val.get("from_station") or "").strip()
        dur = str(val.get("duration") or val.get("total") or "").strip()
        if not acc:
            acc = "（目安未設定・公式で確認）"
        if not dur:
            dur = "—"
        return acc, dur
    s = str(val).strip()
    return (s if s else "（目安未設定・公式で確認）"), "—"


def expand_display_rows(
    base_rows: list[dict[str, Any]],
    catalog: dict[str, Any],
    campus_access: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """カタログの oc_campuses ごとに表行を分割。source_id は同一のまま（詳細アンカー共用）。"""
    by_name = {u.get("name"): u for u in catalog.get("universities", []) if u.get("name")}
    out: list[dict[str, Any]] = []
    for r in base_rows:
        sid = r.get("source_id") or ""
        uni = r.get("university") or ""
        cu = by_name.get(uni)
        acc = campus_access.get(sid, {})
        if cu and cu.get("oc_campuses"):
            depts = cu.get("info_departments") or []
            short_dept = "・".join(depts[:2])
            if len(short_dept) > 100:
                short_dept = short_dept[:97] + "…"
            cbs = r.get("campus_block_schedule") or {}
            for oc in cu["oc_campuses"]:
                campus_name = str(oc.get("campus", ""))
                pref = str(oc.get("prefecture", ""))
                rr = {**r}
                rr["display_campus_line"] = f"{campus_name}（{pref}）" if pref else campus_name
                rr["display_dept_short"] = short_dept or (r.get("department_label") or "")[:100]
                raw_av = acc.get(campus_name, acc.get("_default"))
                tr, dur = _parse_campus_access_value(raw_av)
                rr["transit_note"] = tr
                rr["duration_note"] = dur

                block = cbs.get(campus_name) if isinstance(cbs, dict) else None
                if isinstance(block, dict) and block.get("schedule_summary_line"):
                    blob = str(block["schedule_summary_line"])
                    rr["schedule_dates_only"] = extract_schedule_dates_only_from_blob(blob)
                    dline = (block.get("dept_line") or "").strip()
                    if dline:
                        rr["display_dept_short"] = dline[:200]
                    rr["schedule_apply_links"] = list(block.get("apply_links") or [])

                if not rr.get("schedule_apply_links"):
                    sl: list[dict[str, str]] = []
                    if r.get("reservation_url"):
                        sl.append({"label": "申込・予約", "url": str(r["reservation_url"])})
                    pu = r.get("page_url") or ""
                    if pu and not any(x.get("url") == pu for x in sl):
                        sl.append({"label": "日程・詳細", "url": str(pu)})
                    rr["schedule_apply_links"] = sl

                out.append(rr)
        else:
            rr = {**r}
            rr["display_campus_line"] = r.get("campus_label") or "—"
            rr["display_dept_short"] = (r.get("department_label") or "")[:100]
            tr, dur = _parse_campus_access_value(acc.get("_default"))
            rr["transit_note"] = tr
            rr["duration_note"] = dur
            sl = []
            if r.get("reservation_url"):
                sl.append({"label": "申込・予約", "url": str(r["reservation_url"])})
            pu = r.get("page_url") or ""
            if pu and not any(x.get("url") == pu for x in sl):
                sl.append({"label": "日程・詳細", "url": str(pu)})
            rr["schedule_apply_links"] = sl
            out.append(rr)
    return sorted(
        out,
        key=lambda x: (
            _UNIV_RANK.get(x.get("university") or "", 50),
            x.get("university") or "",
            x.get("display_campus_line") or "",
        ),
    )


def render_repo_and_run_banner(run_meta: dict[str, Any]) -> str:
    """ページ最上部: 更新日時・差分有無（表の前）。"""
    gen = html.escape(run_meta.get("generated_at") or "")
    has_diff = bool(run_meta.get("has_diff"))
    ids = run_meta.get("changed_source_ids") or []
    if has_diff and ids:
        diff_line = "**前回スナップショットとの差分**: あり（`" + "`, `".join(html.escape(i) for i in ids) + "`）"
    elif has_diff:
        diff_line = "**前回スナップショットとの差分**: あり"
    else:
        diff_line = "**前回スナップショットとの差分**: なし（フィンガープリント一致）"

    return "\n".join(
        [
            "リポジトリ: [mtakahashi1150/univ_info_cursor](https://github.com/mtakahashi1150/univ_info_cursor)",
            "",
            f"**サイト更新（取得実行・UTC）**: `{gen}`",
            "",
            diff_line,
            "",
            "> 表の **日程** は公式ページからの抜粋です。詳細・申込は **公式サイト** リンク先で確認してください。",
            "> **逗子（JR 横須賀線・逗子駅／または京急逗子・葉山駅）から** の所要は手動の目安です（`config/campus_access.yaml`）。経路で大きく変わります。未設定時は公式で確認してください。",
            "",
        ]
    )


def render_catalog_markdown(catalog: dict[str, Any]) -> str:
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


def _schedule_cell_html(dates_plain: str, apply_links: list[dict[str, str]]) -> str:
    """日程列: テキスト＋申込・詳細リンク（markdown=0 の表用 HTML）。"""
    parts: list[str] = [html.escape(dates_plain)]
    for link in apply_links:
        lab = html.escape(link.get("label") or "リンク")
        u = link.get("url") or ""
        if not u:
            continue
        u_esc = html.escape(u, quote=True)
        parts.append(
            f'<a class="oc-schedule-link" href="{u_esc}" target="_blank" rel="noopener noreferrer">{lab}</a>'
        )
    return "<br/>".join(parts)


def _external_links_html(page_url: str, reservation_url: str) -> str:
    chunks: list[str] = []
    if page_url:
        u = html.escape(page_url, quote=True)
        chunks.append(
            f'<a href="{u}" target="_blank" rel="noopener noreferrer">オープンキャンパス案内</a>'
        )
    if reservation_url:
        u = html.escape(reservation_url, quote=True)
        chunks.append(
            f'<a href="{u}" target="_blank" rel="noopener noreferrer">申込・予約</a>'
        )
    if not chunks:
        return "—"
    return " ".join(chunks)


def render_oc_overview_html_table(display_rows: list[dict[str, Any]]) -> str:
    """スマホは CSS でカード風（各行に大学名を繰り返し、rowspan は使わない）。"""
    lines = [
        "## 一覧表",
        "",
        '<div class="oc-overview-wrap" markdown="0">',
        '<table class="oc-overview-table">',
        "<thead><tr>",
        '<th data-label="大学">大学</th>',
        '<th data-label="学部・学科">学部・学科</th>',
        '<th data-label="OC">オープンキャンパス<br/><span class="oc-th-sub">逗子から（目安）</span><br/><span class="oc-th-sub">所要（目安）</span></th>',
        '<th data-label="日程">日程</th>',
        '<th data-label="差分">差分</th>',
        '<th data-label="公式">公式</th>',
        '<th data-label="詳細">詳細</th>',
        "</tr></thead>",
        "<tbody>",
    ]

    seen_changed_sid: set[str] = set()
    for r in display_rows:
        sid_raw = (r.get("source_id") or "").replace('"', "").replace("'", "")
        sid = html.escape(sid_raw)
        uni_plain = html.escape(r.get("university", "") or "")
        new_html = ""
        if r.get("changed_this_run") and sid_raw and sid_raw not in seen_changed_sid:
            new_html = ' <span class="oc-new-badge">NEW</span>'
            seen_changed_sid.add(sid_raw)
        uni_cell = f'<a class="oc-overview-uni" href="#{sid}">{uni_plain}</a>{new_html}'

        lines.append("<tr>")
        lines.append(f'<td data-label="大学">{uni_cell}</td>')

        dept = html.escape(r.get("display_dept_short") or "")
        campus = html.escape(r.get("display_campus_line") or "")
        transit = html.escape(r.get("transit_note") or "")
        dur_raw = (r.get("duration_note") or "").strip()
        dur_esc = html.escape(dur_raw) if dur_raw and dur_raw != "—" else ""
        oc_cell = f'<span class="oc-campus-name">{campus}</span><br/><span class="oc-transit">（{transit}）</span>'
        if dur_esc:
            oc_cell += f'<br/><span class="oc-duration">（所要 {dur_esc}）</span>'

        raw_dates = (r.get("schedule_dates_only") or "—").strip()
        if r.get("changed_this_run"):
            dates_display = f"更新 {raw_dates}" if raw_dates != "—" else "更新"
        else:
            dates_display = raw_dates
        apply_links = list(r.get("schedule_apply_links") or [])
        dates_td = _schedule_cell_html(dates_display, apply_links)
        diff_cell = "○" if r.get("changed_this_run") else "—"
        links_td = _external_links_html(r.get("page_url") or "", r.get("reservation_url") or "")
        detail_td = f'<a href="#{sid}">詳細</a>' if sid_raw else "—"

        lines.append(f'<td data-label="学部・学科">{dept}</td>')
        lines.append(f'<td data-label="OC">{oc_cell}</td>')
        lines.append(f'<td data-label="日程" class="oc-col-dates">{dates_td}</td>')
        lines.append(f'<td data-label="差分" class="oc-col-diff">{diff_cell}</td>')
        lines.append(f'<td data-label="公式" class="oc-overview-links">{links_td}</td>')
        lines.append(f'<td data-label="詳細">{detail_td}</td>')
        lines.append("</tr>")

    lines.append("</tbody></table></div>")
    lines.append("")
    return "\n".join(lines)


def _schedule_bullets(schedule_summary: str, limit: int = 10) -> str:
    parts = [p.strip() for p in schedule_summary.split(" / ") if p.strip()]
    if not parts:
        return "    - （公式ページで日程を確認してください）"
    return "\n".join(f"    - {p}" for p in parts[:limit])


def render_oc_detail_cards(rows: list[dict[str, Any]]) -> str:
    n = len(rows)
    lines: list[str] = [
        "## 大学別の詳細（公式ページへ）",
        "",
        f"上の **公式** または下のリンクから各大学の案内ページへ。**全 {n} ソース**（取得単位）。",
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
            lines.append(f'<h3 class="oc-title">{uni_esc} <span class="oc-new-badge">NEW</span></h3>')
        else:
            lines.append(f'<h3 class="oc-title">{uni_esc}</h3>')
        lines.append("")
        cw = (r.get("catalog_season_warning") or "").strip()
        if cw:
            lines.append(f'<p class="oc-catalog-warning">{html.escape(cw)}</p>')
            lines.append("")
        cbs = r.get("campus_block_schedule") or {}
        if isinstance(cbs, dict) and cbs:
            lines.append("- **キャンパス別日程（抜粋・公式の該当リンクで確認）**")
            for cname in sorted(cbs.keys()):
                blk = cbs[cname]
                if not isinstance(blk, dict):
                    continue
                sl = (blk.get("schedule_summary_line") or "").replace("\n", " ").strip()
                if len(sl) > 260:
                    sl = sl[:257] + "…"
                lines.append(f"    - **{cname}**: {sl}")
        else:
            lines.append("- **日程（抜粋）**")
            lines.append(_schedule_bullets(r.get("schedule_summary") or ""))
        lines.append(
            f"- **公式**: {_external_links_html(r.get('page_url') or '', r.get('reservation_url') or '')}"
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

    if normalized.get("omit_table_schedule_dates"):
        schedule_dates_only = "—"
        sched = "（掲載URL・抽出元は過去年度の可能性があります。最新の日程は公式サイトで確認）"
    else:
        schedule_dates_only = extract_schedule_dates_only(normalized, sched)

    return {
        "source_id": source_id,
        "university_group": university_group,
        "university": university,
        "department_label": department_label,
        "campus_label": campus_label,
        "area_prefectures_str": "・".join(area_prefectures),
        "application_note": app_note,
        "schedule_summary": sched,
        "schedule_dates_only": schedule_dates_only,
        "campus_block_schedule": normalized.get("campus_block_schedule") or {},
        "reservation_url": reservation_url or "",
        "page_url": page_url,
        "last_fetch_at": last_fetch_at,
        "last_content_change_at": last_content_change_at,
        "status": status,
        "changed_this_run": changed_this_run,
        "update_snippet": update_snippet,
        "catalog_season_warning": catalog_season_warning,
    }


def render_full_document(
    catalog: dict[str, Any],
    rows: list[dict[str, Any]],
    campus_access: dict[str, dict[str, Any]],
    run_meta: Optional[dict[str, Any]] = None,
) -> str:
    run_meta = run_meta or {}
    base_sorted = sort_base_rows(rows)
    display_rows = expand_display_rows(base_sorted, catalog, campus_access)

    parts = [
        render_repo_and_run_banner(run_meta),
        "# オープンキャンパス情報（早慶上理・G-MARCH・東京4理工ほか）",
        "",
        render_oc_overview_html_table(display_rows),
        render_oc_detail_cards(base_sorted),
        "---",
        "",
        render_catalog_markdown(catalog),
    ]
    return "\n".join(parts)
