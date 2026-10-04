"""O modelo de dados do build. Dataclasses, sem comportamento de I/O."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Fragment:
    """Um arquivo de `content/<lang>/<path>.html`."""

    meta: dict[str, str]
    body: str

    @property
    def title(self) -> str:
        return self.meta.get("data-title", "")

    @property
    def lead(self) -> str:
        return self.meta.get("data-lead", "")

    @property
    def updated(self) -> str:
        return self.meta.get("data-updated", "")


@dataclass
class Node:
    """Um nível intermediário do menu. Não tem página."""

    name: str
    slug: str
    kids: list = field(default_factory=list)
    parent: Node | None = None

    @property
    def is_folder(self) -> bool:
        return True


@dataclass
class Area:
    """Uma das quatro áreas de topo. Tem página de visão geral."""

    name: str
    slug: str
    icon: str
    titles: dict[str, str]
    about: dict[str, str]
    loose: dict[str, str]
    kids: list = field(default_factory=list)

    def title(self, lang: str) -> str:
        return self.titles.get(lang) or self.titles.get("pt") or self.name

    def about_text(self, lang: str) -> str:
        return self.about.get(lang) or self.about.get("pt") or ""

    def loose_label(self, lang: str) -> str:
        return self.loose.get(lang) or self.loose.get("pt") or ""


@dataclass
class Page:
    """Uma página construída: uma rota, num idioma.

    kind:
      home      a raiz de um idioma
      overview  visão geral de uma área
      leaf      uma página de documento
    """

    id: str  # 'modules/agents/utils/model-gateway'
    kind: str
    lang: str
    name: str  # rótulo estrutural, do manifest
    slug_path: str  # caminho do fragmento, sem extensão
    path: str  # 'pt/modules/agents/utils/model-gateway/' — relativo à raiz
    out_path: str  # 'pt/modules/agents/utils/model-gateway/index.html'
    area: Area | None = None
    crumbs: list[str] = field(default_factory=list)
    ancestors: list[Node] = field(default_factory=list)
    empty: bool = False
    fragment: Fragment | None = None
    is_mirror: bool = False  # serve corpo pt sob URL de outro idioma
    translations: set[str] = field(default_factory=set)
    alt: dict[str, str] = field(default_factory=dict)  # lang -> url
    prev: Page | None = None
    next: Page | None = None
    order: int = 0  # ordem no manifest, desempate da busca

    @property
    def rel_root(self) -> str:
        """Prefixo para voltar à raiz do site a partir desta página.

        É o que torna todo link interno relativo, e por isso o site roda em
        qualquer ponto de montagem — raiz de domínio, subpasta do GitHub
        Pages, ou até `file://` — sem nenhuma configuração.
        """
        depth = self.out_path.count("/")
        return "../" * depth if depth else ""

    def href(self, other: "Page") -> str:
        """Link desta página para outra."""
        return self.rel_root + other.path

    def asset(self, rel: str) -> str:
        """Link desta página para um arquivo em assets/."""
        return self.rel_root + "assets/" + rel.lstrip("/")

    @property
    def abs_url(self) -> str:
        """Só para canonical, hreflang e sitemap."""
        return "/" + self.path

    @property
    def title(self) -> str:
        """O que vai no <h1>. Fragmento manda; manifest é a reserva."""
        if self.fragment and self.fragment.title:
            return self.fragment.title
        return self.name

    @property
    def nav_label(self) -> str:
        """O que vai no menu. Sempre o manifest, para preservar o menu aprovado."""
        return self.name

    @property
    def noindex(self) -> bool:
        return self.is_mirror or self.empty
