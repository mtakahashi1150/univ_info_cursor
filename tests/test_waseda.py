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
