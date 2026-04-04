from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass(frozen=True)
class Source:
    id: str
    university: str
    university_group: str
    department_label: str
    campus_label: str
    area_prefectures: tuple[str, ...]
    parser: str
    page_url: str
    reservation_url: Optional[str]
    regions: list[str]
    tags: list[str]


def load_sources(path: Optional[Path] = None) -> list[Source]:
    base = path or Path("config/sources.yaml")
    raw = yaml.safe_load(base.read_text(encoding="utf-8"))
    sources: list[Source] = []
    for item in raw.get("sources", []):
        prefs = item.get("area_prefectures") or item.get("prefectures") or []
        sources.append(
            Source(
                id=item["id"],
                university=item["university"],
                university_group=item.get("university_group", ""),
                department_label=item.get("department_label", ""),
                campus_label=item.get("campus_label", ""),
                area_prefectures=tuple(prefs),
                parser=item["parser"],
                page_url=item["page_url"],
                reservation_url=item.get("reservation_url"),
                regions=list(item.get("regions", [])),
                tags=list(item.get("tags", [])),
            )
        )
    return sources


def load_target_catalog(path: Optional[Path] = None) -> dict[str, Any]:
    p = path or Path("config/target_catalog.yaml")
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def load_campus_access(path: Optional[Path] = None) -> dict[str, dict[str, Any]]:
    """campus_access.yaml: by_source_id -> { キャンパス名: 目安文字列 or {access,duration} }"""
    p = path or Path("config/campus_access.yaml")
    if not p.is_file():
        return {}
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    out: dict[str, dict[str, Any]] = {}
    for sid, mapping in (raw.get("by_source_id") or {}).items():
        if isinstance(mapping, dict):
            out[str(sid)] = {str(k): v for k, v in mapping.items()}
    return out


def repo_root() -> Path:
    """config/sources.yaml からリポジトリルートを推定。"""
    cwd = Path.cwd()
    for p in (cwd, *cwd.parents):
        if (p / "config" / "sources.yaml").is_file():
            return p
    return cwd
