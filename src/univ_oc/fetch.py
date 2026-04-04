from __future__ import annotations

import time

import httpx
from bs4 import BeautifulSoup

# ブラウザ相当の UA（一部大学サイトがボット用 UA で 403 になるため末尾に識別子を付与）
DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
    "univ_info_cursor/0.1 (+https://github.com/mtakahashi1150/univ_info_cursor; educational)"
)

# GitHub Actions 等、海外出口からの接続でタイムアウトしやすいサイト向けに長め＋再試行
DEFAULT_TIMEOUT = 45.0
DEFAULT_RETRIES = 4


def fetch_html(url: str, timeout: float = DEFAULT_TIMEOUT, retries: int = DEFAULT_RETRIES) -> str:
    last: Exception | None = None
    for attempt in range(retries):
        try:
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
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError) as e:
            last = e
            if attempt < retries - 1:
                time.sleep(min(8.0, 1.5 * (2**attempt)))
    assert last is not None
    raise last


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")
