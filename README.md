# Caffeine documentation

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Docs</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

Documentation, plans, screenshots and books for the **Caffeine Engine** and
**Doppio** editor. This repository is included in the engine as the
`caffeine-website` submodule; the engine tree contains no user-facing Markdown.

## The site (caffeine.devscafe.org)

The documentation is published as a static site at **https://caffeine.devscafe.org**
(English at `/en/`, Portuguese at `/pt/`). It is generated from `content/` by a small
Node script, with no framework and no client-side rendering.

```bash
pnpm install          # markdown-it, highlight.js, mermaid
pnpm dev              # build, serve http://localhost:4173 and rebuild on change
pnpm build            # write dist/
pnpm check            # build and fail on broken links or missing images
```

| Path | Purpose |
|------|---------|
| `site/config.json` | Section groups, folder titles (EN/PT), domain and repository URLs |
| `site/build.mjs` | Markdown to HTML, link and image resolution, navigation, search index, sitemap |
| `site/templates.mjs` | Page, landing and home templates and the UI strings |
| `site/assets/` | Stylesheet, behaviour (search, theme, copy, image zoom) and logo |
| `Dockerfile`, `nginx.conf` | Static image for Coolify; the deploy goes through staging and main |

How pages are placed:

- A folder is a section; its `README.md` (or `index.md`) is the section page. Relative links
  between `.md` files and to images are rewritten to clean URLs, so keep writing them the way
  `DOCS_STYLE.md` describes.
- Add a folder to a group in `site/config.json` (`groups[].items`) to put it in the top
  navigation, and give it a title in `titles` when the folder name is not enough.
- The first `#` heading is the page title, `##` and `###` build the right-hand table of
  contents, and the `doc-lede` paragraph is the search and social description.
- Images are click-to-zoom; `mermaid` fences load Mermaid only on pages that use them.
- Search is built at publish time (`/<lang>/search.json`); press <kbd>Ctrl</kbd>+<kbd>K</kbd> or <kbd>/</kbd>.

## Layout

| Path | Contents |
|------|----------|
| `content/en/docs/` | English documentation (canonical) |
| `content/pt/docs/` | Portuguese mirror of the English tree |
| `tex/` | LaTeX books and PDF sources |
| `captures/` | Legacy screenshot manifest and fixture project |
| `scripts/` | Docs audits, translation and diagram helpers |
| `site/` | Static site generator, templates and assets |
| `DOCS_STYLE.md` | Authoring standard (HTML-first Markdown) |

## Where to write

| Topic | Folder |
|-------|--------|
| Build, install, first project | `content/en/docs/getting-started/` |
| Editor UI, panels, viewport | `content/en/docs/editor/` |
| Engine modules (ECS, rendering, audio…) | matching module folder |
| Doppio generators | `doppio/docs/` in the engine, linked from the site |
| Roadmaps and historical plans | `content/en/docs/plans/` |
| Book-length material | `tex/` |
| Plugins | `content/en/docs/plugins/` and `doppio-plugins/docs/` |

## Adding a page

1. Create the Markdown file under `content/en/docs/<section>/`.
2. Follow [`DOCS_STYLE.md`](DOCS_STYLE.md): title, `doc-meta` strip, lede, HTML figures and
   callouts where they add meaning.
3. Add it to the section index (`content/en/docs/README.md`) when relevant.
4. Mirror the structure to `content/pt/docs/<section>/` and translate the prose.
5. Run both audits:

```bash
python3 scripts/audit-docs.py --include-engine
python3 scripts/audit-docs-i18n.py
```

## Images and recordings

| Kind | Location |
|------|----------|
| Screenshots | `content/{en,pt}/docs/images/` |
| Diagrams | `content/{en,pt}/docs/images/diagrams/` (SVG when hand-drawn) |
| GIF/MP4 | `content/{en,pt}/docs/images/editor/` (recorded by the headless driver) |

Generate editor images from the engine checkout, not from a desktop screenshot:

```bash
./scripts/capture-editor-docs.sh
./scripts/capture-editor-tour.sh
```

The flows live in `doppio/docs/flows/capture-editor-docs.json` and
`capture-editor-tour.json`; copy the resulting PNGs, GIFs and MP4s into both
language trees. For generator captures, use
`capture-material-docs.sh`, `capture-nature-docs.sh`, `capture-terrain-docs.sh`,
`capture-texture-docs.sh`, `capture-water-docs.sh` or `capture-gizmo-docs.sh`.

Embed images with a `<figure>` and a caption that explains what to look at:

```html
<figure class="doc-figure">
  <img src="../images/editor/workspace-scene.png" alt="Doppio workspace with the five panes" loading="lazy">
  <figcaption>The default workspace with an engine-backed scene.</figcaption>
</figure>
```

## Audits

`audit-docs.py` checks links, images, stale source paths, HTML rules and the required
metadata. `audit-docs-i18n.py` checks that EN and PT have the same page set, heading
levels, code-fence languages and image names. Both must exit 0 before publishing.

`fix-doc-paths.py` repairs moved source references, and `modernize-docs.py` can add
metadata strips and convert standalone images to figures; run them with `--apply`
only after reviewing the dry run.

## Translation

`content/pt/docs/` mirrors `content/en/docs/`. Keep heading levels, code-fence languages
and image names aligned; translate prose, captions and `alt` text. Identifiers, paths,
CLI flags and code are never translated. New English pages get a Portuguese
counterpart in the same change.

## Website

`scripts/build-site.py` turns `content/{en,pt}/docs/` into a static website in `site/`
(ignored by git). It needs `markdown-it-py` and `pygments`:

```bash
pip install markdown-it-py pygments
python3 scripts/build-site.py
python3 -m http.server -d site 8080    # http://localhost:8080
```

- Pages are generated from Markdown only; no CDN, no network access at view time.
- The first `# Heading` becomes the page title; `> **Key:** value` lines at the top of a page
  become metadata chips; `> [!NOTE]`, `[!TIP]`, `[!WARNING]` … become callouts.
- Links between pages are rewritten to `.html`. Links that climb out of `docs/` (for example
  `../../src/...`) point at the engine repository on GitHub. Targets that do not exist are shown
  with a dotted underline, and the build lists them by file.
- Styles and behaviour live in `scripts/site/site.css` and `scripts/site/site.js`.
- The site is generated on every run; edit the source, never `site/`.

## Website

`scripts/build-site.py` turns `content/{en,pt}/docs/` into a static website in `site/`
(ignored by git). It needs `markdown-it-py` and `pygments`:

```bash
pip install markdown-it-py pygments
python3 scripts/build-site.py
python3 -m http.server -d site 8080    # http://localhost:8080
```

- Pages are generated from Markdown only; no CDN, no network access at view time.
- The first `# Heading` becomes the page title; `> **Key:** value` lines at the top of a page
  become metadata chips; `> [!NOTE]`, `[!TIP]`, `[!WARNING]` … become callouts.
- Links between pages are rewritten to `.html`. Links that climb out of `docs/` (for example
  `../../src/...`) point at the engine repository on GitHub. Targets that do not exist are shown
  with a dotted underline, and the build lists them by file.
- Styles and behaviour live in `scripts/site/site.css` and `scripts/site/site.js`.
- The site is generated on every run; edit the source, never `site/`.

## Books

LaTeX sources are under `tex/`:

- `tex/caffeine-internals/` — engine internals
- `tex/fundamentos-computacao-grafica/` — computer graphics fundamentals
- `tex/scripting-reference/` — scripting reference

Build them with your LaTeX toolchain of choice (`pdflatex`/`latexmk`).

## Related repositories

- Engine and Doppio: <https://github.com/devscafecommunity/caffeine>
- Editor plugins: <https://github.com/devscafecommunity/doppio-plugins>
- Launcher: <https://github.com/devscafecommunity/caffeine-launcher>
- Asset packer: <https://github.com/devscafecommunity/caf-pack>
