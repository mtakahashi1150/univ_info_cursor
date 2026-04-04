from __future__ import annotations

import os

import typer
from dotenv import load_dotenv

from univ_oc import fetch as fetch_mod
from univ_oc.config_loader import load_sources, repo_root
from univ_oc.mail import build_email_body, load_smtp_settings_from_env, send_update_email
from univ_oc.parsers import parse as parse_with
from univ_oc.render import build_row, render_markdown_table
from univ_oc.snapshot import (
    days_since_content_change,
    load_snapshot,
    merge_snapshot,
    save_snapshot,
)

app = typer.Typer(no_args_is_help=True)


@app.command()
def run(
    notify: bool = typer.Option(False, "--notify", help="差分時にメール送信（SMTP 環境変数が必要）"),
    dry_run: bool = typer.Option(False, "--dry-run", help="HTTP を行わずスナップショットのみ表示"),
) -> None:
    """設定の全ソースを取得し、スナップショット・Markdown を更新する。"""
    load_dotenv()
    root = repo_root()
    os.chdir(root)

    sources = load_sources(root / "config" / "sources.yaml")
    snapshot_dir = root / "data" / "snapshots"
    out_md = root / "docs" / "opencampus.md"

    any_changed: list[str] = []
    rows: list[dict] = []
    change_details: list[str] = []

    for src in sources:
        snap_path = snapshot_dir / f"{src.id}.json"
        prev = load_snapshot(snap_path)

        if dry_run:
            if not prev:
                typer.echo("dry-run には既存の data/snapshots/*.json が必要です。", err=True)
                raise typer.Exit(code=1)
            normalized = prev["normalized"]
            fp = prev["fingerprint"]
            changed = False
        else:
            html = fetch_mod.fetch_html(src.page_url)
            soup = fetch_mod.parse_html(html)
            parsed = parse_with(src.parser, soup, page_url=src.page_url, reservation_url=src.reservation_url)
            fp = parsed["fingerprint"]
            normalized = parsed["normalized"]
            merged, changed = merge_snapshot(
                src.id,
                src.university,
                src.department_label,
                src.page_url,
                src.reservation_url,
                fp,
                normalized,
                prev,
            )
            save_snapshot(snap_path, merged)
            if changed:
                any_changed.append(src.id)
                hl = ", ".join(normalized.get("highlights", [])[:2])
                change_details.append(f"- {src.university}: {hl or '本文構成の変化'}")

        data = load_snapshot(snap_path)
        assert data is not None
        ddays = days_since_content_change(data["last_content_change_at"])
        row = build_row(
            university=src.university,
            department_label=src.department_label,
            page_url=src.page_url,
            reservation_url=src.reservation_url,
            normalized=data["normalized"],
            last_fetch_at=data["last_fetch_at"],
            last_content_change_at=data["last_content_change_at"],
            changed_this_run=changed if not dry_run else False,
            days_no_update=ddays,
        )
        rows.append(row)

    md = render_markdown_table(rows)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md, encoding="utf-8")

    pages_url = os.environ.get(
        "PAGES_BASE_URL",
        "https://mtakahashi1150.github.io/univ_info_cursor/",
    )
    if any_changed and notify:
        settings = load_smtp_settings_from_env()
        if settings:
            body = build_email_body(
                pages_base_url=pages_url,
                changed_summaries=change_details or ["（詳細はスナップショット参照）"],
                cumulative_brief="\n".join(
                    f"- {r['university']}: {r['schedule_summary'][:120]}..."
                    if len(r["schedule_summary"]) > 120
                    else f"- {r['university']}: {r['schedule_summary']}"
                    for r in rows
                ),
            )
            try:
                send_update_email(
                    to_addr=settings["email_to"],
                    smtp_host=settings["smtp_host"],
                    smtp_port=settings["smtp_port"],
                    smtp_user=settings["smtp_user"],
                    smtp_password=settings["smtp_password"],
                    subject="[大学OC] オープンキャンパス情報に更新がありました",
                    body_text=body,
                )
                typer.echo("Notification email sent.")
            except Exception as e:  # noqa: BLE001
                typer.echo(f"Email send failed (continuing): {e}", err=True)
        else:
            typer.echo("SMTP_USER / SMTP_PASSWORD not set; skip email.", err=True)

    if any_changed:
        typer.echo(f"CHANGED: {', '.join(any_changed)}")
    else:
        typer.echo("OK (no content change)")


@app.command("verify-urls")
def verify_urls() -> None:
    """sources.yaml の URL に HTTP GET でアクセスし、ステータスを表示する。"""
    root = repo_root()
    sources = load_sources(root / "config" / "sources.yaml")
    for src in sources:
        try:
            fetch_mod.fetch_html(src.page_url)
            typer.echo(f"OK  {src.id} page_url")
        except Exception as e:  # noqa: BLE001
            typer.echo(f"NG  {src.id} page_url: {e}", err=True)
        if src.reservation_url:
            try:
                fetch_mod.fetch_html(src.reservation_url)
                typer.echo(f"OK  {src.id} reservation_url")
            except Exception as e:  # noqa: BLE001
                typer.echo(f"NG  {src.id} reservation_url: {e}", err=True)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
