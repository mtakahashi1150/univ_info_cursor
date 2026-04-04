from pathlib import Path

from bs4 import BeautifulSoup

from univ_oc.parsers.waseda import parse

FIXTURE = Path(__file__).parent / "fixtures" / "waseda_oc.html"


def test_waseda_extracts_sci_campuses_from_table() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    out = parse(
        soup,
        page_url="https://www.waseda.jp/inst/admission/visiting/opencampus/",
        reservation_url=None,
    )
    assert len(out["fingerprint"]) == 64
    lines = out["normalized"]["schedule_lines"]
    assert any("西早稲田" in ln and "基幹理工" in ln for ln in lines)
    assert any("TWIns" in ln and "創造理工" in ln for ln in lines)
    assert any("8月1日" in ln or "概要" in ln for ln in lines)
    cbs = out["normalized"].get("campus_block_schedule") or {}
    assert "西早稲田キャンパス" in cbs
    assert "基幹理工" in cbs["西早稲田キャンパス"]["schedule_summary_line"]


def test_generic_catalog_season_warning_for_2025_url() -> None:
    from bs4 import BeautifulSoup
    from univ_oc.parsers.generic import parse

    soup = BeautifulSoup("<html><head><title>t</title></head><body><main>x</main></body></html>", "html.parser")
    out = parse(
        soup,
        page_url="https://example.com/admission/opencampus2025/index.html",
        reservation_url=None,
    )
    assert out["normalized"].get("catalog_season_warning")
    assert out["normalized"].get("omit_table_schedule_dates") is True


def test_generic_keio_like_body_dates() -> None:
    from univ_oc.parsers.generic import parse

    html = """<html><head><title>OC2026</title></head><body><main>
    <h2>オープンキャンパス2026</h2>
    <ul><li class="listItem">■日時　2026年8月4日（火）、8月5日（水）</li></ul>
    </main></body></html>"""
    soup = BeautifulSoup(html, "html.parser")
    out = parse(soup, page_url="https://www.keio.ac.jp/ja/admissions/oc/", reservation_url=None)
    sl = " ".join(out["normalized"]["schedule_lines"])
    assert "2026年8月4日" in sl


def test_generic_aoyama_like_paragraph_dates() -> None:
    from univ_oc.parsers.generic import parse

    html = """<html><head><title>OC</title></head><body><main>
    <p class="parabox2_text">開催日　：2026年7月12日（日）<br/>開催時間：10:00～16:00</p>
    </main></body></html>"""
    soup = BeautifulSoup(html, "html.parser")
    out = parse(soup, page_url="https://www.aoyama.ac.jp/admission/undergraduate/open_campus/open_campus.html", reservation_url=None)
    sl = " ".join(out["normalized"]["schedule_lines"])
    assert "2026年7月12日" in sl
