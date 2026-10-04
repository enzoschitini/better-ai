"""Strings do chrome, resolvidas no build.

Porte do objeto `I18N` do protótipo, guardando suas duas propriedades boas:
valores podem ser string ou callable (interpolação), e `pt` é o fallback.

Como cada página é monolíngue (URL por idioma), resolver aqui significa zero
JavaScript de i18n, `<html lang>` correto desde o primeiro byte e nenhum
flash de texto no idioma errado.

String ausente sem fallback em pt é erro de build, não `undefined` silencioso.
"""

from __future__ import annotations

HTML_LANG = {"pt": "pt-BR", "en": "en", "it": "it"}

LANG_NAMES = [("en", "English"), ("it", "Italiano"), ("pt", "Português")]

I18N: dict[str, dict] = {
    "pt": {
        "skip": "Ir para o conteúdo",
        "brandSub": "Docs",
        "tagline": "Where intelligence finds purpose.",
        "searchLbl": "Buscar na documentação",
        "searchPh": "Buscar...",
        "dlgPh": "Buscar páginas e seções",
        "resultsLbl": "Resultados",
        "navigate": "navegar",
        "openRes": "abrir",
        "noResults": lambda q: f"Nada encontrado para “{q}”. Tente o nome de um módulo, como “Pinecone”.",
        "suggestions": "Sugestões",
        "langLbl": "Idioma",
        "themeLbl": "Alternar tema",
        "menuLbl": "Abrir menu",
        "areasLbl": "Áreas da documentação",
        "closeBanner": "Fechar aviso",
        "overview": "Visão geral",
        "overviewOf": lambda t: f"{t}: visão geral",
        "onThisPage": "Nesta página",
        "badge": "vazio",
        "source": "Fonte:",
        "prev": "Anterior",
        "next": "Próxima",
        "pagerLbl": "Páginas vizinhas",
        "feedbackQ": "Esta página foi útil?",
        "yes": "Sim",
        "no": "Não",
        "edit": "Editar no GitHub",
        "copyPage": "Copiar página",
        "moreOpts": "Mais opções",
        "footResources": "Recursos",
        "footPlatform": "Plataforma",
        "sideNavLbl": "Navegação da documentação",
        "untranslated": "Esta página ainda não foi traduzida. Você está lendo a versão em português.",
        "emptyTitle": "Esta página ainda não tem conteúdo",
        "emptyText": "O documento está previsto na estrutura, mas ainda não foi escrito.",
        "emptyCta": "Ver a visão geral da área",
        "notFound": "Página não encontrada",
        "notFoundText": "O endereço não existe ou mudou. Comece por uma das áreas:",
        "redirect": "Abrindo a documentação...",
    },
    "en": {
        "skip": "Skip to content",
        "tagline": "Where intelligence finds purpose.",
        "searchLbl": "Search the documentation",
        "searchPh": "Search...",
        "dlgPh": "Search pages and sections",
        "resultsLbl": "Results",
        "navigate": "navigate",
        "openRes": "open",
        "noResults": lambda q: f"Nothing found for “{q}”. Try a module name, such as “Pinecone”.",
        "suggestions": "Suggestions",
        "langLbl": "Language",
        "themeLbl": "Toggle theme",
        "menuLbl": "Open menu",
        "areasLbl": "Documentation areas",
        "closeBanner": "Dismiss notice",
        "overview": "Overview",
        "overviewOf": lambda t: f"{t}: overview",
        "onThisPage": "On this page",
        "badge": "empty",
        "source": "Source:",
        "prev": "Previous",
        "next": "Next",
        "pagerLbl": "Nearby pages",
        "feedbackQ": "Was this page helpful?",
        "yes": "Yes",
        "no": "No",
        "edit": "Edit on GitHub",
        "copyPage": "Copy page",
        "moreOpts": "More options",
        "footResources": "Resources",
        "footPlatform": "Platform",
        "sideNavLbl": "Documentation navigation",
        "untranslated": "This page has not been translated yet. You are reading the Portuguese version.",
        "emptyTitle": "This page has no content yet",
        "emptyText": "The document is planned in the structure but has not been written.",
        "emptyCta": "See the area overview",
        "notFound": "Page not found",
        "notFoundText": "That address does not exist or has moved. Start from one of the areas:",
        "redirect": "Opening the documentation...",
    },
    "it": {
        "skip": "Vai al contenuto",
        "tagline": "Where intelligence finds purpose.",
        "searchLbl": "Cerca nella documentazione",
        "searchPh": "Cerca...",
        "dlgPh": "Cerca pagine e sezioni",
        "resultsLbl": "Risultati",
        "navigate": "naviga",
        "openRes": "apri",
        "noResults": lambda q: f"Nessun risultato per “{q}”. Prova il nome di un modulo, come “Pinecone”.",
        "suggestions": "Suggerimenti",
        "langLbl": "Lingua",
        "themeLbl": "Cambia tema",
        "menuLbl": "Apri menu",
        "areasLbl": "Aree della documentazione",
        "closeBanner": "Chiudi avviso",
        "overview": "Panoramica",
        "overviewOf": lambda t: f"{t}: panoramica",
        "onThisPage": "In questa pagina",
        "badge": "vuoto",
        "source": "Fonte:",
        "prev": "Precedente",
        "next": "Successiva",
        "pagerLbl": "Pagine vicine",
        "feedbackQ": "Questa pagina è stata utile?",
        "yes": "Sì",
        "no": "No",
        "edit": "Modifica su GitHub",
        "copyPage": "Copia pagina",
        "moreOpts": "Altre opzioni",
        "footResources": "Risorse",
        "footPlatform": "Piattaforma",
        "sideNavLbl": "Navigazione della documentazione",
        "untranslated": "Questa pagina non è ancora stata tradotta. Stai leggendo la versione portoghese.",
        "emptyTitle": "Questa pagina non ha ancora contenuto",
        "emptyText": "Il documento è previsto nella struttura ma non è ancora stato scritto.",
        "emptyCta": "Vedi la panoramica dell'area",
        "notFound": "Pagina non trovata",
        "notFoundText": "L'indirizzo non esiste o è cambiato. Parti da una delle aree:",
        "redirect": "Apertura della documentazione...",
    },
}


def tr(lang: str, key: str, *args):
    v = I18N.get(lang, {}).get(key)
    if v is None:
        v = I18N["pt"].get(key)
    if v is None:
        raise KeyError(f"string {key!r} não existe (sem fallback em pt)")
    return v(*args) if callable(v) else v


def bag(lang: str) -> dict:
    """Todas as strings simples de um idioma, com fallback pt aplicado."""
    out = dict(I18N["pt"])
    out.update(I18N.get(lang, {}))
    return {k: v for k, v in out.items() if not callable(v)}
