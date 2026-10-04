"""site.toml → dataclass congelada. `tomllib` é stdlib no 3.12."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root: Path  # doc_page/
    site_url: str  # inclui o subcaminho, se houver
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


def load(root: Path) -> Settings:
    """Lê site.toml.

    Não existe `base`: todos os caminhos internos do site são relativos, então
    o site funciona em qualquer ponto de montagem sem configuração. O
    `site_url` é usado só onde URL absoluta é obrigatória — canonical,
    hreflang e sitemap — e deve incluir o subcaminho, se houver.
    """
    data = tomllib.loads((root / "site.toml").read_text(encoding="utf-8"))
    return Settings(
        root=root,
        site_url=data.get("site_url", "").rstrip("/"),
        github_repo=data.get("github_repo", ""),
        github_branch=data.get("github_branch", "main"),
        swagger_url=data.get("swagger_url", "#"),
        banner=data.get("banner", ""),
        foot_links=dict(data.get("links", {})),
    )
