# Caffeine documentation

Documentation, plans, screenshots and books for the **Caffeine Engine** and
**Doppio** editor. This repository is included in the engine as the
`caffeine-website` submodule; the engine tree contains no Markdown docs.

## Layout

| Path | Contents |
|------|----------|
| `content/en/docs/` | English documentation (canonical) |
| `content/pt/docs/` | Portuguese mirror of the English tree |
| `tex/` | LaTeX books and PDF sources |
| `captures/` | Screenshot manifest, fixture project, the capture flows (`flows/`) and the widget captions (`ui-captions.json`) |
| `scripts/` | i18n audit, translation and diagram helpers |

## Where to write

| Topic | Folder |
|-------|--------|
| Build, install, first project | `content/en/docs/getting-started/` |
| Editor UI, panels, viewport | `content/en/docs/editor/` |
| Doppio guides (architecture, generators, headless testing, roadmaps) | `content/en/docs/doppio/` |
| Engine modules (ECS, rendering, audio…) | matching module folder |
| Roadmaps and historical plans | `content/en/docs/plans/` |
| Book-length material | `tex/` |
| Plugins | `content/en/docs/plugins/` and `doppio-plugins/docs/` |

## Adding a page

1. Create the Markdown file under `content/en/docs/<section>/`.
2. Add it to the section index (`content/en/docs/README.md`) when relevant.
3. Mirror the structure to `content/pt/docs/<section>/`.
4. Run the i18n audit:

   ```bash
   python3 scripts/audit-docs-i18n.py
   ```

5. Include images with a relative path:

   ```markdown
   ![Viewport toolbar](../images/captures/doppio-scene.png)
   ```

## Images and diagrams

| Kind | Location |
|------|----------|
| Screenshots | `content/en/docs/images/captures/` |
| Diagrams | `content/en/docs/images/diagrams/` |
| Portuguese copies | `content/pt/docs/images/` |

Generate screenshots from the engine checkout:

```bash
python3 scripts/capture_doppio_ui.py
```

The shot list lives in [`captures/shots.json`](captures/shots.json). Prefer SVG for
diagrams so they stay sharp and diff-friendly.

## Translation

`content/pt/docs/` mirrors `content/en/docs/`. Keep heading levels and code fences
aligned; the audit checks structure and reports mismatches. New English pages should
get a Portuguese counterpart, even if the first pass is a summary.

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
