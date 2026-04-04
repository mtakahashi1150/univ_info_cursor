from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

# ブラウザ相当の UA（一部大学サイトがボット用 UA で 403 になるため末尾に識別子を付与）
DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
    "univ_info_cursor/0.1 (+https://github.com/mtakahashi1150/univ_info_cursor; educational)"
)


def fetch_html(url: str, timeout: float = 30.0) -> str:
    with httpx.Client(
        headers={
            "User-Agent": DEFAULT_UA,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en;q=0.8",
        },
        follow_redirects=True,
        timeout=timeout,
    ) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.text


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")
