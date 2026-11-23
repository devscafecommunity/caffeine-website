#!/usr/bin/env python3
"""Build the static Caffeine documentation website.

Renders content/{en,pt}/docs/**/*.md into a self-contained static site: no CDN,
no network access at view time, works from a plain file server.

Requirements: markdown-it-py and Pygments (`pip install markdown-it-py pygments`).

Usage (from caffeine-website/):
    python3 scripts/build-site.py                 # writes site/
    python3 scripts/build-site.py --out /tmp/docs # custom output directory
    python3 -m http.server -d site 8080           # preview at http://localhost:8080

Output:
    site/index.html                  English home
    site/pt/index.html               Portuguese home
    site/<lang>/docs/<path>.html     one page per Markdown file (README.md -> README.html)
    site/assets/                     stylesheet, script and lazy search indexes

Static assets (CSS and JS) live next to this script in scripts/site/.
"""
from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
import shutil
import sys
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONTENT = ROOT / "content"
ASSET_SRC = HERE / "site"
MARKER = ".caffeine-site"
LANGS = ("en", "pt")
HOME_OUT = {"en": "index.html", "pt": "pt/index.html"}
ENGINE_URL = "https://github.com/devscafecommunity/caffeine"
ENGINE_BLOB = ENGINE_URL + "/blob/main/"
WEBSITE_BLOB = "https://github.com/devscafecommunity/caffeine-website/blob/main/"
ASSET_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf", ".mp4", ".webm"}

# Sections in display order. "_root" holds the Markdown files directly under docs/.
SECTION_ORDER = [
    "getting-started", "editor", "doppio", "plugins", "scripting", "ecs", "rendering", "assets",
    "physics", "audio", "input", "animation", "terrain", "ui", "core", "math", "memory",
    "concurrency", "debug", "performance", "architecture", "api", "releases", "plans",
    "analysis", "_root",
]

SECTION_INFO = {
    "en": {
        "getting-started": ("Getting started", "Build the engine, run Doppio and create your first project."),
        "editor": ("Doppio editor", "Panels, viewport, inspector, materials and generators."),
        "doppio": ("Doppio guides", "Editor architecture, headless driver, generators and roadmaps."),
        "plugins": ("Plugins", "Install, write and ship plugins for Doppio."),
        "scripting": ("Scripting", "Runtime APIs and native modules available to scripts."),
        "ecs": ("ECS", "Entities, components, archetypes, scenes and serialization."),
        "rendering": ("Rendering", "Cameras, materials, lighting, shadows and post-processing."),
        "assets": ("Assets", "Asset pipeline, the .caf format and loaders."),
        "physics": ("Physics", "2D and 3D physics and spatial partitioning."),
        "audio": ("Audio", "Audio system, mixing and spatial sound."),
        "input": ("Input", "Actions, devices and input mapping."),
        "animation": ("Animation", "2D sprite and skeletal animation."),
        "terrain": ("Terrain", "Terrain system and procedural tools."),
        "ui": ("UI", "Editor UI, in-game UI and the UI kit."),
        "core": ("Core", "Types, timers, the game loop and events."),
        "math": ("Math", "Vectors, matrices and quaternions."),
        "memory": ("Memory", "Allocators, containers and the memory model."),
        "concurrency": ("Concurrency", "Job system and threading."),
        "debug": ("Debug & testing", "Debug tools, testing and automation."),
        "performance": ("Performance", "Profiling and performance notes."),
        "architecture": ("Architecture", "How the engine is put together."),
        "api": ("API", "Public API reference."),
        "releases": ("Releases", "Changelog, patch notes and the release checklist."),
        "plans": ("Plans & roadmap", "Design documents, implementation plans and roadmaps."),
        "analysis": ("Analysis", "Status analyses and audits."),
        "_root": ("Project", "Documentation index, history and project-level notes."),
    },
    "pt": {
        "getting-started": ("Começar", "Compilar o motor, executar o Doppio e criar o primeiro projeto."),
        "editor": ("Editor Doppio", "Painéis, viewport, inspetor, materiais e geradores."),
        "doppio": ("Guias do Doppio", "Arquitetura do editor, driver headless, geradores e roadmaps."),
        "plugins": ("Plugins", "Instalar, escrever e publicar plugins para o Doppio."),
        "scripting": ("Scripting", "APIs de runtime e módulos nativos disponíveis para scripts."),
        "ecs": ("ECS", "Entidades, componentes, arquétipos, cenas e serialização."),
        "rendering": ("Renderização", "Câmaras, materiais, iluminação, sombras e pós-processamento."),
        "assets": ("Assets", "Pipeline de assets, formato .caf e carregadores."),
        "physics": ("Física", "Física 2D e 3D e particionamento espacial."),
        "audio": ("Áudio", "Sistema de áudio, mistura e som espacial."),
        "input": ("Input", "Ações, dispositivos e mapeamento de entrada."),
        "animation": ("Animação", "Animação 2D de sprites e esquelética."),
        "terrain": ("Terreno", "Sistema de terreno e ferramentas procedurais."),
        "ui": ("UI", "UI do editor, UI de jogo e kit de UI."),
        "core": ("Núcleo", "Tipos, temporizadores, game loop e eventos."),
        "math": ("Matemática", "Vetores, matrizes e quaterniões."),
        "memory": ("Memória", "Alocadores, contentores e modelo de memória."),
        "concurrency": ("Concorrência", "Sistema de jobs e threads."),
        "debug": ("Depuração e testes", "Ferramentas de depuração, testes e automação."),
        "performance": ("Desempenho", "Perfil e notas de desempenho."),
        "architecture": ("Arquitetura", "Como o motor está organizado."),
        "api": ("API", "Referência da API pública."),
        "releases": ("Versões", "Changelog, notas de versão e checklist de release."),
        "plans": ("Planos e roadmap", "Documentos de design, planos de implementação e roadmaps."),
        "analysis": ("Análises", "Análises de estado e auditorias."),
        "_root": ("Projeto", "Índice da documentação, histórico e notas do projeto."),
    },
}

UI = {
    "en": {
        "eyebrow": "Caffeine Engine · Doppio editor",
        "hero_h1": 'Documentation for the <em>Caffeine</em> engine.',
        "hero_lede": "From the first build to the Doppio editor and the scripting APIs: everything "
                     "organised by module, with search that answers while you type.",
        "hero_search": "Search the documentation",
        "hero_start": "Start here",
        "stat_pages": "Pages", "stat_modules": "Modules", "stat_langs": "Languages",
        "start_title": "Start here", "modules_title": "Explore by module",
        "pages": "pages", "home": "Home", "index": "Documentation index",
        "search_label": "Search", "search_title": "Search documentation",
        "search_placeholder": "Search titles, headings and text…",
        "no_results": "No results for", "type_hint": "Type to search. Use ↑ ↓ to move and Enter to open.",
        "loading": "Loading index…",
        "on_page": "On this page", "contents": "Contents",
        "prev": "Previous", "next": "Next", "edit": "Edit on GitHub", "source": "Source",
        "min_read": "min read", "theme": "Switch light and dark theme",
        "menu": "Open navigation", "close": "Close", "skip": "Skip to content",
        "copy": "Copy", "copied": "Copied", "copy_label": "Copy code",
        "lang": "Language", "nav_label": "Documentation navigation", "github": "Caffeine on GitHub",
        "footer": "Caffeine engine documentation",
        "books": "Books and PDFs", "books_lede": "LaTeX books and PDF exports built from the `tex/` sources.",
        "crumb_docs": "Docs", "footer_built": "Built",
    },
    "pt": {
        "eyebrow": "Motor Caffeine · Editor Doppio",
        "hero_h1": 'Documentação do motor <em>Caffeine</em>.',
        "hero_lede": "Do primeiro build ao editor Doppio e às APIs de scripting: tudo organizado por "
                     "módulo, com pesquisa que responde enquanto escreve.",
        "hero_search": "Pesquisar a documentação",
        "hero_start": "Começar agora",
        "stat_pages": "Páginas", "stat_modules": "Módulos", "stat_langs": "Idiomas",
        "start_title": "Comece aqui", "modules_title": "Explorar por módulo",
        "pages": "páginas", "home": "Início", "index": "Índice da documentação",
        "search_label": "Pesquisar", "search_title": "Pesquisar documentação",
        "search_placeholder": "Pesquisar títulos, cabeçalhos e texto…",
        "no_results": "Sem resultados para", "type_hint": "Escreva para pesquisar. Use ↑ ↓ para navegar e Enter para abrir.",
        "loading": "A carregar índice…",
        "on_page": "Nesta página", "contents": "Conteúdo",
        "prev": "Anterior", "next": "Seguinte", "edit": "Editar no GitHub", "source": "Fonte",
        "min_read": "min de leitura", "theme": "Alternar tema claro e escuro",
        "menu": "Abrir navegação", "close": "Fechar", "skip": "Saltar para o conteúdo",
        "copy": "Copiar", "copied": "Copiado", "copy_label": "Copiar código",
        "lang": "Idioma", "nav_label": "Navegação da documentação", "github": "Caffeine no GitHub",
        "footer": "Documentação do motor Caffeine",
        "books": "Livros e PDFs", "books_lede": "Livros LaTeX e exportações PDF geradas a partir de `tex/`.",
        "crumb_docs": "Docs", "footer_built": "Gerado em",
    },
}

# ---------------------------------------------------------------------------
# Icons (inline SVG, currentColor)
# ---------------------------------------------------------------------------
CUP_MARK = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M4 9h12v4.5A5.5 5.5 0 0 1 10.5 19h-1A5.5 5.5 0 0 1 4 13.5z" fill="currentColor"/>'
    '<path d="M16 10.5h1.2a2.6 2.6 0 0 1 0 5.2H16" fill="none" stroke="currentColor" stroke-width="1.8"/>'
    '<path d="M3 21.2h15" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>'
    '<path d="M8 2.6c-.9 1.3.9 2.2 0 3.6M12 2.6c-.9 1.3.9 2.2 0 3.6" fill="none" '
    'stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>'
)
SEARCH_ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/></svg>'
)
MENU_ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h10"/></svg>'
)
MOON_ICON = (
    '<svg class="i-moon" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" '
    'stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>'
)
SUN_ICON = (
    '<svg class="i-sun" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" '
    'stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><circle cx="12" cy="12" r="4"/>'
    '<path d="M12 2.5v2M12 19.5v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2.5 12h2M19.5 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg>'
)
GITHUB_ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor">'
    '<path d="M12 .5a11.5 11.5 0 0 0-3.6 22.4c.6.1.8-.3.8-.6v-2.1c-3.2.7-3.9-1.4-3.9-1.4-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.1.1 1.7 1.2 1.7 1.2 1 1.7 2.7 1.2 3.4.9.1-.7.4-1.2.7-1.5-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.2 1.2a11 11 0 0 1 5.8 0c2.2-1.5 3.2-1.2 3.2-1.2.6 1.6.2 2.8.1 3.1.8.8 1.2 1.9 1.2 3.1 0 4.4-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A11.5 11.5 0 0 0 12 .5z"/></svg>'
)
CHEV = '<svg class="chev" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'

HERO_ART = (
    '<svg class="hero-cup" viewBox="0 0 340 320" role="presentation" focusable="false">'
    '<ellipse cx="170" cy="296" rx="150" ry="12" class="cup-shadow"/>'
    '<path d="M250 150h22a36 36 0 0 1 0 72h-26" class="cup-handle"/>'
    '<path d="M70 132h190v78c0 52-38 86-95 86h0c-57 0-95-34-95-86z" class="cup-body"/>'
    '<path d="M86 160h158" class="cup-glaze"/>'
    '<path d="M46 292h248" class="cup-saucer"/>'
    '<path d="M124 110c-14-22 14-34 0-60" class="steam s1"/>'
    '<path d="M170 104c-14-24 14-38 0-68" class="steam s2"/>'
    '<path d="M216 110c-14-22 14-34 0-60" class="steam s3"/>'
    '<circle cx="60" cy="58" r="3" class="spark"/><circle cx="296" cy="40" r="2.2" class="spark"/>'
    '<circle cx="312" cy="200" r="2.6" class="spark"/></svg>'
)

# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------
_FORMATTER = HtmlFormatter(nowrap=True, classprefix="tok-", style="monokai")
_SCRIPT = re.compile(r"<(script|style)\b.*?</\1\s*>", re.I | re.S)
_HANDLER = re.compile(r"(<[a-zA-Z][^>]*?)\s+on[a-zA-Z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)")
_JS_HREF = re.compile(r"href\s*=\s*([\"'])\s*javascript:[^\"']*\1", re.I)
_BLOCKQUOTE = re.compile(r"<blockquote>\n?(.*?)</blockquote>", re.S)
_ALERT = re.compile(r"^<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*")
_META = re.compile(r"^<strong>([^<]+?)(:?)</strong>(:?)\s*(.*)$", re.S)
_TABLE = re.compile(r"(<table>.*?</table>)", re.S)
_TONE_OK = ("implement", "done", "conclu", "complete", "shipped", "active", "ativo", "ready")
_TONE_OLD = ("historical", "histórico", "archiv", "deprecated", "obsolete", "superseded")
_TONE_WIP = ("planned", "plane", "draft", "rascunho", "progress", "curso", "wip", "proposed")


def _slugify(text: str) -> str:
    """GitHub-compatible heading slug: keep letters and digits (accents included), spaces become hyphens."""
    text = re.sub(r"[^\w\- ]", "", text.strip().lower())
    return text.replace(" ", "-") or "section"


def _unique(slug: str, used: set[str]) -> str:
    base, n, out = slug, 2, slug
    while out in used:
        out = f"{base}-{n}"
        n += 1
    used.add(out)
    return out


def _plain(tok: Token) -> str:
    parts: list[str] = []
    for child in tok.children or []:
        if child.type in ("text", "code_inline"):
            parts.append(child.content)
        elif child.type in ("softbreak", "hardbreak"):
            parts.append(" ")
        elif child.children:
            parts.append(_plain(child))
    return " ".join("".join(parts).split())


def _fence(tokens, idx, options, env):
    tok = tokens[idx]
    lang = (tok.info or "").strip().split(" ")[0].lower()
    try:
        lexer = get_lexer_by_name(lang) if lang else TextLexer()
    except ClassNotFound:
        lexer = TextLexer()
    body = highlight(tok.content, lexer, _FORMATTER).rstrip("\n")
    label = html.escape(lang or "text")
    return (
        f'<div class="codeblock"><div class="codeblock__bar"><span>{label}</span>'
        f'<button type="button" class="codeblock__copy" data-copy aria-label="Copy code">Copy</button></div>'
        f'<pre><code class="language-{label}">{body}</code></pre></div>\n'
    )


ENGINE_DIRS = {
    "src", "include", "doppio", "tests", "scripts", "apps", "cmake", "assets", "caffeine-launcher",
    "doppio-plugins", "caf-pack", "infra", "build", "references", "doppio-archived",
}


def _find(rel: str, docs: Path) -> str | None:
    """Return the docs-relative file a link points at, or None."""
    candidates = [rel]
    if rel.startswith("docs/"):  # legacy links written from the engine root
        candidates.append(rel[len("docs/"):])
    for cand in candidates:
        target = docs / cand
        if target.is_dir() and (target / "README.md").is_file():
            return posixpath.join(cand, "README.md")
        if target.is_file() and (cand.endswith(".md") or target.suffix.lower() in ASSET_EXT):
            return cand
    return None


def _resolve(href: str, env: dict) -> tuple[str, bool]:
    """Rewrite a relative link from a Markdown page. Returns (href, resolved)."""
    if not href or href.startswith(("#", "http://", "https://", "mailto:", "data:", "//", "/")):
        return href, True
    path, hash_sign, frag = href.partition("#")
    path = path.split("?", 1)[0]
    suffix = hash_sign + frag if hash_sign else ""
    if not path:
        return href, True
    joined = posixpath.normpath(posixpath.join(env["rel_dir"], path))
    docs: Path = env["docs"]
    if joined == ".." or joined.startswith("../"):
        # Links that climb out of docs/ point into the engine tree (e.g. ../../src/...).
        return ENGINE_BLOB + re.sub(r"^(\.\./)+", "", joined) + suffix, True
    found = _find(joined, docs)
    if found is None:
        if joined.split("/")[0] in ENGINE_DIRS:
            return ENGINE_BLOB + joined + suffix, True
        if (docs / joined).exists():  # e.g. a LaTeX source: link to the file in the repository
            return WEBSITE_BLOB + f"content/{env['lang']}/docs/{joined}" + suffix, True
        env["warn"].append(f"{env['src']}: missing link {href}")
        return href, False
    dest = found[:-3] + ".html" if found.endswith(".md") else found
    site_target = f"{env['lang']}/docs/{dest}"
    return posixpath.relpath(site_target, start=env["page_dir"]) + suffix, True


_HTML_HREF = re.compile(r'(\bhref=")([^"]+\.md(?:#[^"]*)?)(")')


def _rewrite_html_links(content: str, env: dict) -> str:
    """Raw HTML links to other pages (`<a href="other.md">`) get the same rewrite as Markdown links."""
    return _HTML_HREF.sub(lambda m: m.group(1) + _resolve(m.group(2), env)[0] + m.group(3), content)


def _site_rule(state) -> None:
    """Core rule: heading ids, anchors, TOC, lede, link and image rewriting."""
    env = state.env
    tokens = state.tokens
    used: set[str] = set()
    toc: list[tuple[int, str, str]] = []
    drop: list[int] = []
    title = None
    lede_at = None
    for i, tok in enumerate(tokens):
        if tok.type != "heading_open":
            continue
        level = int(tok.tag[1])
        inline = tokens[i + 1]
        text = _plain(inline)
        slug = _unique(_slugify(text), used)
        tok.attrSet("id", slug)
        if level == 1 and title is None:
            # The page header renders the title, so the first H1 is removed from the body.
            title = text
            drop.extend([i, i + 1, i + 2])
            lede_at = i + 3
            continue
        if level in (2, 3):
            toc.append((level, text, slug))
        if inline.children is not None:
            inline.children.append(Token(
                "html_inline", "", 0,
                content=f'<a class="anchor" href="#{slug}" aria-label="Link to {html.escape(text)}">#</a>',
            ))
    if lede_at is not None and lede_at < len(tokens) and tokens[lede_at].type == "paragraph_open":
        tokens[lede_at].attrSet("class", "lede")
    for tok in tokens:
        if tok.type == "html_block":
            tok.content = _rewrite_html_links(tok.content, env)
            continue
        if tok.type != "inline" or not tok.children:
            continue
        for child in tok.children:
            if child.type == "html_inline":
                child.content = _rewrite_html_links(child.content, env)
            if child.type == "link_open" and child.attrGet("href") is not None:
                new, ok = _resolve(child.attrGet("href"), env)
                child.attrSet("href", new)
                if not ok:
                    child.attrSet("class", "is-missing")
                    child.attrSet("title", "Target not found in the documentation tree")
            elif child.type == "image":
                child.attrSet("src", _resolve(child.attrGet("src") or "", env)[0])
                child.attrSet("loading", "lazy")
                child.attrSet("decoding", "async")
    for j in sorted(drop, reverse=True):
        del tokens[j]
    env["title"] = title
    env["toc"] = toc


def _make_markdown() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True, "linkify": False, "typographer": False})
    md.enable(["table", "strikethrough"])
    md.renderer.rules["fence"] = _fence
    md.core.ruler.push("site", _site_rule)
    return md


def _sanitize(out: str) -> str:
    out = _SCRIPT.sub("", out)
    out = _HANDLER.sub(r"\1", out)
    return _JS_HREF.sub('href="#"', out)


def _squash(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def _meta_items(inner: str) -> list[list[str]] | None:
    """Parse a leading block of "**Key:** value" pairs into [key, value] items, or None."""
    # Authors sometimes write "** Status:**" (space after the opening asterisks); treat it as a key too.
    inner = re.sub(r"\*\*\s*([^*<>]{1,40}?)\s*:\*\*", r"<strong>\1:</strong>", inner)
    paras = [p.strip() for p in re.findall(r"<p>(.*?)</p>", inner, re.S)]
    if not paras or any(not p.startswith("<strong>") for p in paras):
        return None
    if re.search(r"<(ul|ol|table|pre|blockquote)\b", inner):
        return None
    items: list[list[str]] = []
    for para in paras:
        for chunk in re.split(r"(?=<strong>)", para):
            chunk = chunk.strip()
            if not chunk:
                continue
            m = re.match(r"^<strong>([^<]{1,60}?)(:?)</strong>(:?)\s*(.*)$", chunk, re.S)
            if m and (m.group(2) or m.group(3)):
                items.append([m.group(1).strip(), m.group(4)])
            elif items:  # stray text belongs to the previous value
                items[-1][1] += " " + chunk
            else:
                return None
    for item in items:
        value = re.sub(r"<br\s*/?>", " ", item[1]).replace("\n", " ")
        item[1] = re.sub(r"\s*,?\s*$", "", re.sub(r"^\s*[:,]\s*", "", value)).strip()
    return items


def _meta_block(items: list[list[str]]) -> str:
    chips = []
    for key, value in items:
        if not value:
            continue
        tone = ""
        if key.lower() in ("status", "estado"):
            low = value.lower()
            if any(w in low for w in _TONE_OLD):
                tone = "muted"
            elif any(w in low for w in _TONE_WIP):
                tone = "warn"
            elif any(w in low for w in _TONE_OK):
                tone = "ok"
        attr = f' data-tone="{tone}"' if tone else ""
        chips.append(f'<div class="m"{attr}><dt>{esc(key)}</dt><dd>{value}</dd></div>')
    return '<dl class="doc-meta">' + "".join(chips) + "</dl>"


def _blockquote(m: re.Match) -> str:
    inner = m.group(1).strip()
    alert = _ALERT.match(inner)
    kind = ""
    if alert:
        kind = alert.group(1).lower()
        inner = "<p>" + inner[alert.end():]
        inner = re.sub(r"<p>\s*</p>", "", inner).strip()
    else:
        items = _meta_items(inner)
        if items:
            return _meta_block(items)
    data = f' data-kind="{kind}"' if kind else ""
    return f'<blockquote class="callout"{data}>\n{inner}\n</blockquote>'


def render_markdown(md: MarkdownIt, text: str, env: dict) -> str:
    env.update(title=None, toc=[])
    out = md.render(text, env)
    out = _sanitize(out)
    out = _BLOCKQUOTE.sub(_blockquote, out)
    out = _TABLE.sub(r'<div class="table-wrap">\1</div>', out)
    return out.replace('data-copy aria-label="Copy code">Copy</button>',
                       f'data-copy aria-label="{html.escape(env["copy_label"])}">{html.escape(env["copy"])}</button>')


def rel_href(target: str, page_dir: str) -> str:
    return posixpath.relpath(target, start=page_dir or ".")


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def prettify(name: str) -> str:
    name = re.sub(r"[-_]+", " ", name).strip()
    return name[:1].upper() + name[1:]


def clean_title(title: str) -> str:
    stripped = re.sub(r"^[\W_]+", "", title).strip()
    return stripped or title.strip()


# ---------------------------------------------------------------------------
# Page model and navigation tree
# ---------------------------------------------------------------------------
class Node:
    def __init__(self, key: str, label: str):
        self.key = key
        self.label = label
        self.pages: list[dict] = []
        self.children: dict[str, Node] = {}


def build_page(lang: str, md: MarkdownIt, docs: Path, rel: str, text: str, warn: list[str]) -> dict:
    out = f"{lang}/docs/{rel[:-3]}.html"
    page_dir = posixpath.dirname(out)
    ui = UI[lang]
    env = {
        "lang": lang, "docs": docs, "rel_dir": posixpath.dirname(rel) or ".",
        "page_dir": page_dir, "warn": warn, "src": f"content/{lang}/docs/{rel}",
        "copy": ui["copy"], "copy_label": ui["copy_label"],
    }
    body = render_markdown(md, text, env)
    title = clean_title(env["title"]) if env["title"] else prettify(Path(rel).stem)
    lede = re.search(r'<p class="lede">(.*?)</p>', body, re.S) or re.search(r"<p>(.*?)</p>", body, re.S)
    desc = _squash(lede.group(1))[:200] if lede else ""
    plain = _squash(body)
    parts = rel.split("/")
    return {
        "lang": lang, "rel": rel, "out": out, "page_dir": page_dir, "title": title,
        "toc": env["toc"], "body": body, "desc": desc, "text": plain[:2200],
        "minutes": max(1, round(len(plain.split()) / 230)), "src": env["src"],
        "filename": parts[-1], "is_index": parts[-1] == "README.md",
        "section": parts[0] if len(parts) > 1 else "_root",
    }


def load_pages(lang: str, md: MarkdownIt, warn: list[str]) -> list[dict]:
    docs = CONTENT / lang / "docs"
    if not docs.is_dir():
        return []
    pages = []
    for path in sorted(docs.rglob("*.md")):
        rel = path.relative_to(docs).as_posix()
        pages.append(build_page(lang, md, docs, rel, path.read_text(encoding="utf-8"), warn))
    pdfs = sorted(p.relative_to(docs).as_posix() for p in docs.rglob("*.pdf"))
    if pdfs:
        ui = UI[lang]
        lines = [f"# {ui['books']}", "", ui["books_lede"], ""]
        for rel in pdfs:
            label = prettify(Path(rel).parent.name) + " — " + prettify(Path(rel).stem)
            lines.append(f"- [{label}]({rel})")
        pages.append(build_page(lang, md, docs, "books.md", "\n".join(lines) + "\n", warn))
    return pages


def sort_pages(pages: list[dict], section: str) -> list[dict]:
    if section == "plans":
        return sorted(pages, key=lambda p: p["filename"], reverse=True)
    return sorted(pages, key=lambda p: (not p["is_index"], p["title"].lower()))


def sort_tree(node: Node, section: str) -> None:
    node.pages = sort_pages(node.pages, section)
    for child in node.children.values():
        sort_tree(child, section)


def build_tree(lang: str, pages: list[dict]) -> dict[str, Node]:
    roots: dict[str, Node] = {}
    info = SECTION_INFO[lang]
    for p in pages:
        parts = p["rel"].split("/")
        section = p["section"]
        label = info.get(section, (prettify(section), ""))[0]
        node = roots.setdefault(section, Node(section, label))
        for d in (parts[1:-1] if section != "_root" else []):
            node = node.children.setdefault(d, Node(d, prettify(d)))
        node.pages.append(p)
    for section, node in roots.items():
        sort_tree(node, section)
    return roots


def ordered_sections(roots: dict[str, Node]) -> list[str]:
    rank = {k: i for i, k in enumerate(SECTION_ORDER)}
    return sorted(roots, key=lambda k: (rank.get(k, len(rank)), k))


def flatten(node: Node) -> list[dict]:
    out = list(node.pages)
    for key in sorted(node.children):
        out.extend(flatten(node.children[key]))
    return out


def contains(node: Node, page: dict | None) -> bool:
    return page is not None and any(p is page for p in flatten(node))


def landing_of(node: Node) -> dict:
    for p in node.pages:
        if p["is_index"]:
            return p
    return flatten(node)[0]


def nav_items(node: Node, page_dir: str, current: dict | None) -> str:
    parts = []
    for p in node.pages:
        cur = ' aria-current="page"' if p is current else ""
        parts.append(f'<li><a href="{esc(rel_href(p["out"], page_dir))}"{cur}>{esc(p["title"])}</a></li>')
    for key in sorted(node.children):
        child = node.children[key]
        is_open = " open" if contains(child, current) else ""
        parts.append(
            f'<li><details class="nav-group"{is_open}><summary><span>{esc(child.label)}</span>'
            f'<span class="count">{len(flatten(child))}</span></summary>'
            f'<ul>{nav_items(child, page_dir, current)}</ul></details></li>'
        )
    return "".join(parts)


def sidebar(ctx: dict, page_dir: str, current: dict | None) -> str:
    ui = UI[ctx["lang"]]
    sections = []
    for key in ordered_sections(ctx["roots"]):
        node = ctx["roots"][key]
        is_open = " open" if contains(node, current) else ""
        sections.append(
            f'<details class="nav-section" data-section="{esc(key)}"{is_open}>'
            f'<summary><span>{esc(node.label)}</span><span class="count">{len(flatten(node))}</span></summary>'
            f'<ul>{nav_items(node, page_dir, current)}</ul></details>'
        )
    return (
        f'<div class="sidebar__inner"><p class="nav-title">{esc(ui["contents"])}</p>'
        f'<nav aria-label="{esc(ui["nav_label"])}">{"".join(sections)}</nav></div>'
    )


# ---------------------------------------------------------------------------
# HTML shell
# ---------------------------------------------------------------------------
def shell(ctx: dict, *, current_out: str, page_dir: str, title: str, description: str,
          main_html: str, sidebar_html: str, toc: list[tuple[int, str, str]] | None,
          article_class: str, data_root: str) -> str:
    lang = ctx["lang"]
    ui = UI[lang]
    other = "pt" if lang == "en" else "en"
    other_out = ctx["counterpart"].get(current_out, HOME_OUT[other])
    lang_links = []
    for code in LANGS:
        target = current_out if code == lang else other_out
        cur = ' aria-current="true"' if code == lang else ""
        lang_links.append(
            f'<a href="{esc(rel_href(target, page_dir))}" lang="{code}" hreflang="{code}"{cur}>{code.upper()}</a>'
        )
    alternates = "".join(
        f'<link rel="alternate" hreflang="{code}" href="{esc(rel_href(current_out if code == lang else other_out, page_dir))}">'
        for code in LANGS
    )
    toc_html = ""
    layout_class = "layout"
    if toc:
        items = "".join(
            f'<li class="lvl-{lvl}"><a href="#{esc(slug)}">{esc(text)}</a></li>' for lvl, text, slug in toc
        )
        nav = f'<nav class="toc" aria-label="{esc(ui["on_page"])}"><ul>{items}</ul></nav>'
        toc_html = (
            f'<aside class="toc-rail" aria-label="{esc(ui["on_page"])}"><p class="toc-title">{esc(ui["on_page"])}</p>{nav}</aside>'
            f'<details class="toc-mobile"><summary>{esc(ui["on_page"])}</summary>{nav}</details>'
        )
        layout_class += " has-toc"
    theme_script = (
        "try{var t=localStorage.getItem('caf-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}"
    )
    return f"""<!doctype html>
<html lang="{lang}" data-theme-pref="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Caffeine docs</title>
<meta name="description" content="{esc(description or ui['footer'])}">
<meta name="generator" content="scripts/build-site.py">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M4 9h12v4.5A5.5 5.5 0 0 1 10.5 19h-1A5.5 5.5 0 0 1 4 13.5z' fill='%23e8b463'/%3E%3C/svg%3E">
{alternates}
<link rel="stylesheet" href="{esc(rel_href('assets/site.css', page_dir))}">
<script>{theme_script}</script>
</head>
<body data-root="{esc(data_root)}" data-lang="{lang}" data-copy-label="{esc(ui['copy'])}" data-copied="{esc(ui['copied'])}" data-no-results="{esc(ui['no_results'])}" data-loading="{esc(ui['loading'])}" data-hint="{esc(ui['type_hint'])}">
<a class="skip" href="#main">{esc(ui['skip'])}</a>
<header class="topbar">
  <div class="topbar__inner">
    <button type="button" class="icon-btn nav-toggle" aria-controls="sidebar" aria-expanded="false" aria-label="{esc(ui['menu'])}">{MENU_ICON}</button>
    <a class="brand" href="{esc(rel_href(HOME_OUT[lang], page_dir))}">{CUP_MARK}<span class="brand__name">Caffeine</span><span class="brand__tag">docs</span></a>
    <button type="button" class="search-trigger" data-open-search aria-label="{esc(ui['search_title'])}">{SEARCH_ICON}<span>{esc(ui['search_label'])}</span><kbd>/</kbd></button>
    <div class="topbar__actions">
      <nav class="lang" aria-label="{esc(ui['lang'])}">{''.join(lang_links)}</nav>
      <button type="button" class="icon-btn" data-theme-toggle aria-label="{esc(ui['theme'])}">{SUN_ICON}{MOON_ICON}</button>
      <a class="icon-btn" href="{ENGINE_URL}" aria-label="{esc(ui['github'])}">{GITHUB_ICON}</a>
    </div>
  </div>
  <div class="progress" aria-hidden="true"></div>
</header>
<div class="{layout_class}">
  <aside id="sidebar" class="sidebar" aria-label="{esc(ui['nav_label'])}">{sidebar_html}</aside>
  <div class="scrim" data-nav-close aria-hidden="true"></div>
  <main id="main" class="content" tabindex="-1">
    <div class="article {article_class}">
{main_html}
    </div>
    <footer class="site-footer">
      <span>{esc(ui['footer'])} · {esc(ui['footer_built'])} {ctx['built']}</span>
      <span><a href="{ENGINE_URL}">Caffeine</a> · <a href="{WEBSITE_BLOB}">{esc(ui['source'])}</a></span>
    </footer>
  </main>
  {toc_html}
</div>
<dialog class="palette" id="palette" aria-label="{esc(ui['search_title'])}">
  <div class="palette__field">{SEARCH_ICON}
    <input id="palette-input" type="search" autocomplete="off" spellcheck="false" placeholder="{esc(ui['search_placeholder'])}" aria-controls="palette-results" aria-label="{esc(ui['search_title'])}">
    <kbd>Esc</kbd>
  </div>
  <ul class="palette__results" id="palette-results" role="listbox"></ul>
  <p class="palette__hint"></p>
</dialog>
<script src="{esc(rel_href('assets/site.js', page_dir))}" defer></script>
</body>
</html>
"""


def page_html(ctx: dict, page: dict) -> str:
    lang = ctx["lang"]
    ui = UI[lang]
    flat = ctx["flat"]
    idx = next(i for i, p in enumerate(flat) if p is page)
    pdir = page["page_dir"]
    crumbs = [f'<a href="{esc(rel_href(HOME_OUT[lang], pdir))}">{esc(ui["home"])}</a>']
    if page["section"] in ctx["roots"]:
        node = ctx["roots"][page["section"]]
        crumbs.append(f'<a href="{esc(rel_href(landing_of(node)["out"], pdir))}">{esc(node.label)}</a>')
    parts = page["rel"].split("/")
    if page["section"] != "_root":
        for d in parts[1:-1]:
            crumbs.append(f"<span>{esc(prettify(d))}</span>")
    crumb_html = '<span class="sep" aria-hidden="true">/</span>'.join(crumbs)
    edit = WEBSITE_BLOB + page["src"]
    head = (
        f'<nav class="crumbs" aria-label="Breadcrumb">{crumb_html}</nav>'
        f'<h1>{esc(page["title"])}</h1>'
        f'<div class="page-meta"><span>{page["minutes"]} {esc(ui["min_read"])}</span>'
        f'<a href="{esc(edit)}">{esc(ui["edit"])}</a></div>'
    )
    pager = []
    if idx > 0:
        prev = flat[idx - 1]
        pager.append(f'<a class="prev" href="{esc(rel_href(prev["out"], pdir))}"><span>← {esc(ui["prev"])}</span>'
                     f'<strong>{esc(prev["title"])}</strong></a>')
    else:
        pager.append("<span></span>")
    if idx + 1 < len(flat):
        nxt = flat[idx + 1]
        pager.append(f'<a class="next" href="{esc(rel_href(nxt["out"], pdir))}"><span>{esc(ui["next"])} →</span>'
                     f'<strong>{esc(nxt["title"])}</strong></a>')
    main = (
        f'<header class="page-head">{head}</header>\n'
        f'{page["body"]}\n'
        f'<nav class="pager" aria-label="Pager">{"".join(pager)}</nav>'
    )
    return shell(
        ctx, current_out=page["out"], page_dir=pdir, title=page["title"], description=page["desc"],
        main_html=main, sidebar_html=sidebar(ctx, pdir, page), toc=page["toc"] or None,
        article_class="", data_root=rel_href(".", pdir),
    )


def home_html(ctx: dict) -> str:
    lang = ctx["lang"]
    ui = UI[lang]
    info = SECTION_INFO[lang]
    home_out = HOME_OUT[lang]
    hdir = posixpath.dirname(home_out)
    roots = ctx["roots"]
    populated = [k for k in ordered_sections(roots) if flatten(roots[k])]
    start_cards = []
    for i, key in enumerate(["getting-started", "editor", "scripting"], 1):
        if key not in roots:
            continue
        node = roots[key]
        landing = landing_of(node)
        links = [p for p in flatten(node) if p is not landing][:4]
        items = "".join(f'<li><a href="{esc(rel_href(p["out"], hdir))}">{esc(p["title"])}</a></li>' for p in links)
        start_cards.append(
            f'<article class="card"><span class="card__no">{i:02d}</span>'
            f'<h3><a href="{esc(rel_href(landing["out"], hdir))}">{esc(node.label)}</a></h3>'
            f'<p>{esc(info[key][1])}</p><ul class="card__links">{items}</ul></article>'
        )
    modules = []
    for i, key in enumerate(populated, 1):
        node = roots[key]
        modules.append(
            f'<a class="module" href="{esc(rel_href(landing_of(node)["out"], hdir))}">'
            f'<span class="module__no">{i:02d}</span><h3>{esc(node.label)}</h3>'
            f'<p>{esc(info[key][1])}</p>'
            f'<span class="module__count">{len(flatten(node))} {esc(ui["pages"])} {CHEV}</span></a>'
        )
    start_href = rel_href(landing_of(roots["getting-started"])["out"], hdir) if "getting-started" in roots else "#"
    main = f"""<section class="hero">
  <div class="hero__copy">
    <p class="eyebrow">{esc(ui['eyebrow'])}</p>
    <h1>{ui['hero_h1']}</h1>
    <p class="hero__lede">{esc(ui['hero_lede'])}</p>
    <div class="hero__actions">
      <button type="button" class="btn btn--primary" data-open-search>{SEARCH_ICON}<span>{esc(ui['hero_search'])}</span><kbd>/</kbd></button>
      <a class="btn" href="{esc(start_href)}">{esc(ui['hero_start'])} {CHEV}</a>
    </div>
    <dl class="hero__stats">
      <div><dt>{esc(ui['stat_pages'])}</dt><dd>{len(ctx['pages'])}</dd></div>
      <div><dt>{esc(ui['stat_modules'])}</dt><dd>{len(populated)}</dd></div>
      <div><dt>{esc(ui['stat_langs'])}</dt><dd>EN · PT</dd></div>
    </dl>
  </div>
  <div class="hero__art" aria-hidden="true">{HERO_ART}</div>
</section>
<section class="home-block" aria-labelledby="start-title">
  <div class="section-head"><h2 id="start-title">{esc(ui['start_title'])}</h2></div>
  <div class="start-grid">{''.join(start_cards)}</div>
</section>
<section class="home-block" aria-labelledby="modules-title">
  <div class="section-head"><h2 id="modules-title">{esc(ui['modules_title'])}</h2></div>
  <div class="module-grid">{''.join(modules)}</div>
</section>"""
    return shell(
        ctx, current_out=home_out, page_dir=hdir, title=ui["home"] if lang == "en" else "Início",
        description=ui["hero_lede"], main_html=main, sidebar_html=sidebar(ctx, hdir, None),
        toc=None, article_class="article--home", data_root=rel_href(".", hdir),
    )


def search_index(ctx: dict) -> str:
    entries = []
    for p in ctx["pages"]:
        entries.append({
            "t": p["title"],
            "s": ctx["roots"][p["section"]].label if p["section"] in ctx["roots"] else "",
            "u": p["out"],
            "h": " ".join(text for _, text, _ in p["toc"]),
            "d": p["desc"],
            "b": p["text"],
        })
    payload = json.dumps(entries, ensure_ascii=False)
    return f"window.CAFFEINE_SEARCH=window.CAFFEINE_SEARCH||{{}};window.CAFFEINE_SEARCH[{json.dumps(ctx['lang'])}]={payload};\n"


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build(out: Path) -> int:
    import datetime

    if out.exists():
        if (out / MARKER).exists():
            shutil.rmtree(out)
        elif any(out.iterdir()):
            sys.exit(f"refusing to overwrite {out}: not a generated site (no {MARKER} marker)")
    out.mkdir(parents=True, exist_ok=True)
    (out / MARKER).write_text("Generated by scripts/build-site.py. Safe to delete.\n", encoding="utf-8")

    md = _make_markdown()
    warnings: list[str] = []
    built = datetime.date.today().isoformat()
    contexts: dict[str, dict] = {}
    for lang in LANGS:
        pages = load_pages(lang, md, warnings)
        roots = build_tree(lang, pages)
        flat = [p for k in ordered_sections(roots) for p in flatten(roots[k])]
        contexts[lang] = {
            "lang": lang, "pages": pages, "roots": roots, "flat": flat,
            "built": built, "counterpart": {},
        }
    # Counterpart map: same docs-relative path in the other language, else that language's home.
    by_rel = {lang: {p["rel"]: p["out"] for p in contexts[lang]["pages"]} for lang in LANGS}
    for lang in LANGS:
        other = "pt" if lang == "en" else "en"
        ctx = contexts[lang]
        for p in ctx["pages"]:
            ctx["counterpart"][p["out"]] = by_rel[other].get(p["rel"], HOME_OUT[other])
        ctx["counterpart"][HOME_OUT[lang]] = HOME_OUT[other]

    total = 0
    for lang in LANGS:
        ctx = contexts[lang]
        if not ctx["pages"]:
            continue
        for page in ctx["pages"]:
            target = out / page["out"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(page_html(ctx, page), encoding="utf-8")
            total += 1
        home = out / HOME_OUT[lang]
        home.parent.mkdir(parents=True, exist_ok=True)
        home.write_text(home_html(ctx), encoding="utf-8")
        total += 1
        (out / "assets").mkdir(parents=True, exist_ok=True)
        (out / "assets" / f"search-{lang}.js").write_text(search_index(ctx), encoding="utf-8")

    # Copy images, diagrams and PDFs so relative links keep working.
    copied = 0
    for lang in LANGS:
        docs = CONTENT / lang / "docs"
        if not docs.is_dir():
            continue
        for path in docs.rglob("*"):
            if path.is_file() and path.suffix.lower() in ASSET_EXT:
                dest = out / lang / "docs" / path.relative_to(docs)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest)
                copied += 1

    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    css = (HERE / "site" / "site.css").read_text(encoding="utf-8")
    shutil.copy2(ASSET_SRC / "site.js", assets / "site.js")
    (assets / "site.css").write_text(_FORMATTER.get_style_defs(".codeblock") + "\n" + css, encoding="utf-8")

    print(f"Wrote {total} HTML pages and {copied} media files to {out}")
    for lang in LANGS:
        print(f"  {lang}: {len(contexts[lang]['pages'])} markdown pages, "
              f"{len(contexts[lang]['roots'])} sections")
    if warnings:
        by_file: dict[str, int] = {}
        for w in warnings:
            by_file[w.split(": missing link", 1)[0]] = by_file.get(w.split(": missing link", 1)[0], 0) + 1
        print(f"\n{len(warnings)} unresolved link(s) in {len(by_file)} file(s); they are shown with a dotted underline:")
        for src, n in sorted(by_file.items(), key=lambda kv: -kv[1])[:25]:
            print(f"  {n:4d}  {src}")
        if len(by_file) > 25:
            print(f"        … {len(by_file) - 25} more file(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(ROOT / "site"), help="output directory (default: site/)")
    args = parser.parse_args()
    return build(Path(args.out).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
