from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

DEFAULT_UA = (
    "univ_info_cursor/0.1 (+https://github.com/mtakahashi1150/univ_info_cursor; educational)"
)


def fetch_html(url: str, timeout: float = 30.0) -> str:
    with httpx.Client(
        headers={"User-Agent": DEFAULT_UA, "Accept-Language": "ja,en;q=0.8"},
        follow_redirects=True,
        timeout=timeout,
    ) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.text


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")
