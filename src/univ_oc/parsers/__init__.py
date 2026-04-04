from __future__ import annotations

from typing import Any, Optional

from bs4 import BeautifulSoup

from univ_oc.parsers import aoyama as aoyama_mod
from univ_oc.parsers import chuo as chuo_mod
from univ_oc.parsers import dendai as dendai_mod
from univ_oc.parsers import generic as generic_mod
from univ_oc.parsers import hosei as hosei_mod
from univ_oc.parsers import keio as keio_mod
from univ_oc.parsers import kogakuin as kogakuin_mod
from univ_oc.parsers import meiji as meiji_mod
from univ_oc.parsers import rikkyo as rikkyo_mod
from univ_oc.parsers import shibaura as shibaura_mod
from univ_oc.parsers import sophia as sophia_mod
from univ_oc.parsers import tcu as tcu_mod
from univ_oc.parsers import teu as teu_mod
from univ_oc.parsers import tus as tus_mod
from univ_oc.parsers import waseda as waseda_mod

PARSERS: dict[str, Any] = {
    "meiji": meiji_mod.parse,
    "waseda": waseda_mod.parse,
    "generic": generic_mod.parse,
    "aoyama": aoyama_mod.parse,
    "rikkyo": rikkyo_mod.parse,
    "chuo": chuo_mod.parse,
    "keio": keio_mod.parse,
    "sophia": sophia_mod.parse,
    "hosei": hosei_mod.parse,
    "shibaura": shibaura_mod.parse,
    "tcu": tcu_mod.parse,
    "dendai": dendai_mod.parse,
    "kogakuin": kogakuin_mod.parse,
    "teu": teu_mod.parse,
    "tus": tus_mod.parse,
}


def parse(
    parser_name: str, soup: BeautifulSoup, page_url: str, reservation_url: Optional[str]
) -> dict[str, Any]:
    fn = PARSERS.get(parser_name)
    if not fn:
        raise ValueError(f"Unknown parser: {parser_name}")
    return fn(soup, page_url=page_url, reservation_url=reservation_url)
