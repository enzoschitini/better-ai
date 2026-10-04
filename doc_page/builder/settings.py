"""site.toml → dataclass congelada. `tomllib` é stdlib no 3.12."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root: Path  # doc_page/
    site_url: str
    base: str
    github_repo: str
    github_branch: str
    swagger_url: str
    banner: str
    foot_links: dict[str, str] = field(default_factory=dict)

    @property
    def content(self) -> Path:
        return self.root / "content"

    @property
    def theme(self) -> Path:
        return self.root / "theme"

    @property
    def assets(self) -> Path:
        return self.root / "assets"

    @property
    def dist(self) -> Path:
        return self.root / "dist"

    @property
    def github_url(self) -> str:
        return f"https://github.com/{self.github_repo}"

    def blob(self, rel: str) -> str:
        return f"{self.github_url}/blob/{self.github_branch}/doc_page/{rel}"

    def edit(self, rel: str) -> str:
        return f"{self.github_url}/edit/{self.github_branch}/doc_page/{rel}"


def load(root: Path, base_override: str | None = None) -> Settings:
    data = tomllib.loads((root / "site.toml").read_text(encoding="utf-8"))
    base = base_override if base_override is not None else data.get("base", "")
    base = base.rstrip("/")
    return Settings(
        root=root,
        site_url=data.get("site_url", "").rstrip("/"),
        base=base,
        github_repo=data.get("github_repo", ""),
        github_branch=data.get("github_branch", "main"),
        swagger_url=data.get("swagger_url", "#"),
        banner=data.get("banner", ""),
        foot_links=dict(data.get("links", {})),
    )
