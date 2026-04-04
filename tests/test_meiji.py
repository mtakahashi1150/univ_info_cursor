from pathlib import Path

from bs4 import BeautifulSoup

from univ_oc.parsers.meiji import parse

FIXTURE = Path(__file__).parent / "fixtures" / "meiji_oc.html"


def test_meiji_parse_fingerprint_stable() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    out = parse(
        soup,
        page_url="https://www.meiji.ac.jp/exam/event/opencampus/index.html",
        reservation_url="https://www.meiji.ac.jp/exam/reference/official_line.html",
    )
    assert len(out["fingerprint"]) == 64
    assert "オープンキャンパス" in out["normalized"]["page_title"] or "明治" in out["normalized"]["page_title"]
    assert out["normalized"]["schedule_lines"]


def test_render_table() -> None:
    from univ_oc.render import build_row, render_full_document

    row = build_row(
        source_id="test_src",
        university_group="テスト群",
        university="テスト大学",
        department_label="情報",
        campus_label="テストキャンパス",
        area_prefectures=["東京都"],
        page_url="https://example.com/oc",
        reservation_url="https://example.com/r",
        normalized={
            "highlights": ["2025/1/1：更新"],
            "schedule_lines": ["【駿河台】2026年8月6日"],
            "application_period_note": "公式参照",
        },
        last_fetch_at="2026-01-01T00:00:00+00:00",
        last_content_change_at="2026-01-01T00:00:00+00:00",
        changed_this_run=True,
        days_no_update=0,
    )
    catalog = {"meta": {"area_prefectures": ["東京都"], "focus": "情報系"}, "universities": []}
    md = render_full_document(catalog, [row])
    assert "テスト大学" in md
    assert "累積" in md
    assert "今回の更新サマリー" in md
    assert "NEW" in md
    assert "オープンキャンパス案内" in md
    assert 'target="_blank"' in md
    assert "test_src" in md
