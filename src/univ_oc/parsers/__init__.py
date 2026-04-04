from __future__ import annotations

from typing import Any, Optional

from bs4 import BeautifulSoup

from univ_oc.parsers import meiji as meiji_mod

PARSERS: dict[str, Any] = {
    "meiji": meiji_mod.parse,
}


def parse(
    parser_name: str, soup: BeautifulSoup, page_url: str, reservation_url: Optional[str]
) -> dict[str, Any]:
    fn = PARSERS.get(parser_name)
    if not fn:
        raise ValueError(f"Unknown parser: {parser_name}")
    return fn(soup, page_url=page_url, reservation_url=reservation_url)
