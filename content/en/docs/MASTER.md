# Master index

<div class="doc-meta">
  <span class="doc-badge doc-badge--reference">Reference</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Doppio</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">A single entry point for the documentation tree. The functional
index with descriptions lives in <a href="README.md">README.md</a>; this page keeps
the old “master” entry point working and gives the current architecture at a glance.</p>

<div class="doc-callout doc-callout--note">
  <p><strong>Historical material.</strong> <a href="HISTORY.md">HISTORY.md</a> and
  the pages under <code>plans/</code> record how the project arrived here. They are
  not current API documentation. For the current editor, start with
  <a href="editor/scene-editor.md">Scene editor</a>.</p>
</div>

## Architecture at a glance

<table class="doc-table">
  <thead>
    <tr><th>Layer</th><th>What it is</th><th>Where</th></tr>
  </thead>
  <tbody>
    <tr><td>GPU API</td><td>Vulkan, D3D12 or Metal through SDL3 GPU</td><td>Platform drivers</td></tr>
    <tr><td>Engine core</td><td>Runtime, render, RHI, ECS, assets, physics, scripting. No ImGui, no editor state.</td><td><code>src/caffeine/</code></td></tr>
    <tr><td>C ABI</td><td>Stable boundary for any frontend; versioned in <code>CAFFEINE_CAPI_VERSION</code>.</td><td><code>include/caffeine/capi/EngineAPI.h</code>, <code>src/caffeine/capi/</code></td></tr>
    <tr><td>Engine bridge</td><td>Rust <code>libloading</code> bindings; the only crate allowed to touch FFI.</td><td><code>doppio/crates/engine/</code></td></tr>
    <tr><td>Doppio UI</td><td>Iced workspace, panels, components and generators.</td><td><code>doppio/crates/ui/</code></td></tr>
    <tr><td>Plugins</td><td>Optional C++/ImGui tools compiled from the submodule.</td><td><code>doppio-plugins/</code>, <code>include/caffeine/plugin/</code></td></tr>
  </tbody>
</table>

## Main entry points

| Need | Page |
|---|---|
| Build and run | [Getting started](getting-started/README.md) |
| Learn the editor | [Scene editor](editor/scene-editor.md) |
| Visual tour | [UI gallery](editor/ui-gallery.md) |
| Materials | [Material editor](editor/material-editor.md) |
| Render pipeline | [RHI](rendering/rhi.md), [PBR materials](rendering/materials-pbr.md) |
| ECS and scenes | [ECS core](ecs/core.md), [Scene manager](ecs/scene.md) |
| Scripting | [Scripting overview](scripting/scripting.md) |
| C ABI and APIs | [API reference](api/README.md) |
| Headless testing | [Driver reference](doppio/headless-testing.md) |
| Project history | [History](HISTORY.md) |

## Repository map

| Path | Contents |
|---|---|
| `src/caffeine/` | Engine core |
| `include/caffeine/` | Public headers (C API, plugins, UI kit, runtime) |
| `apps/` | `caffeine-runtime` and `caffeine-combined` executables |
| `doppio/` | Rust editor workspace |
| `doppio-archived/` | Frozen C++ editor snapshot (reference only) |
| `tests/` | Catch2 suites |
| `caf-pack/` | Asset packer submodule |
| `doppio-plugins/` | Plugin submodule |
| `caffeine-website/` | This documentation tree |

## Documentation standards

- HTML-first Markdown: [`DOCS_STYLE.md`](https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/DOCS_STYLE.md).
- Current pages carry `Stable`, `Beta` or `Reference`; plans carry `Historical`.
- Source links use absolute GitHub URLs; images live under `images/`.
- Run both audits before publishing:

```bash
cd caffeine-website
python3 scripts/audit-docs.py --include-engine
python3 scripts/audit-docs-i18n.py
```
