# Caffeine documentation

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Doppio</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine"><code>devscafecommunity/caffeine</code></a></span>
</div>

<p class="doc-lede">The Caffeine Engine is a C++20 engine on SDL3. Doppio is its
Rust/Iced editor. The engine exposes a stable C ABI so any frontend can drive it, and
the editor talks to it through <code>libcaffeine-capi</code>.</p>

<div class="doc-callout doc-callout--tip">
  <p><strong>New here?</strong> Start with <a href="getting-started/README.md">Getting
  started</a> and the <a href="getting-started/quick-start.md">Quick start</a>, then
  take the visual tour in the <a href="editor/ui-gallery.md">UI gallery</a>.</p>
</div>

## Documentation map

<table class="doc-table">
  <thead>
    <tr><th>Area</th><th>Start with</th><th>Also read</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Build and run</strong></td>
      <td><a href="getting-started/README.md">Getting started</a></td>
      <td><a href="getting-started/building.md">Building</a>, <a href="getting-started/build-guide.md">Build guide</a>, <a href="getting-started/contributing.md">Contributing</a></td>
    </tr>
    <tr>
      <td><strong>Doppio editor</strong></td>
      <td><a href="editor/scene-editor.md">Scene editor</a></td>
      <td><a href="editor/scene-viewport.md">Scene viewport</a>, <a href="editor/workspace-and-theme.md">Workspace and theme</a>, <a href="editor/material-editor.md">Material editor</a></td>
    </tr>
    <tr>
      <td><strong>Editor testing</strong></td>
      <td><a href="editor/test-automation.md">Test automation</a></td>
      <td><a href="doppio/headless-testing.md">Headless driver reference</a>, <a href="editor/ui-reference.md">UI reference</a></td>
    </tr>
    <tr>
      <td><strong>Content tools</strong></td>
      <td><a href="doppio/material-pipeline.md">Material pipeline</a></td>
      <td><a href="doppio/materials-guide.md">Materials guide</a>, <a href="doppio/nature-generator-guide.md">Nature</a>, <a href="doppio/terrain-generator-guide.md">Terrain</a>, <a href="doppio/water-generator-guide.md">Water</a>, <a href="doppio/texture-generator-guide.md">Texture</a></td>
    </tr>
    <tr>
      <td><strong>Engine core</strong></td>
      <td><a href="core/types.md">Core types</a></td>
      <td><a href="core/timer.md">Timer</a>, <a href="core/game-loop.md">Game loop</a>, <a href="core/events.md">Events</a>, <a href="memory/memory-model.md">Memory</a>, <a href="math/vectors.md">Math</a></td>
    </tr>
    <tr>
      <td><strong>ECS and scenes</strong></td>
      <td><a href="ecs/core.md">ECS core</a></td>
      <td><a href="ecs/scene.md">Scene manager</a>, <a href="ecs/examples.md">Examples</a></td>
    </tr>
    <tr>
      <td><strong>Rendering</strong></td>
      <td><a href="rendering/rhi.md">RHI</a></td>
      <td><a href="rendering/materials-pbr.md">PBR materials</a>, <a href="rendering/post-processing.md">Post-processing</a>, <a href="rendering/shadow-mapping.md">Shadows</a>, <a href="rendering/reflections.md">Reflections</a></td>
    </tr>
    <tr>
      <td><strong>Physics, audio, animation</strong></td>
      <td><a href="physics/physics-3d.md">Physics 3D</a></td>
      <td><a href="physics/physics-2d.md">Physics 2D</a>, <a href="audio/audio-system.md">Audio</a>, <a href="animation/animation-2d.md">Animation 2D</a>, <a href="animation/skeletal-animation.md">Skeletal animation</a></td>
    </tr>
    <tr>
      <td><strong>Assets and terrain</strong></td>
      <td><a href="assets/asset-manager.md">Asset manager</a></td>
      <td><a href="assets/caf-format.md">CAF format</a>, <a href="assets/asset-pipeline.md">Asset pipeline</a>, <a href="terrain/terrain-system.md">Terrain system</a></td>
    </tr>
    <tr>
      <td><strong>Scripting</strong></td>
      <td><a href="scripting/scripting.md">Scripting overview</a></td>
      <td><a href="scripting/runtime-apis.md">Runtime APIs</a>, <a href="api/scripting-components.md">Generic component access</a>, <a href="scripting/native-modules.md">Native modules</a></td>
    </tr>
    <tr>
      <td><strong>Plugins</strong></td>
      <td><a href="plugins/README.md">Plugin catalog</a></td>
      <td><a href="plugins/writing-a-plugin.md">Writing a plugin</a>, <a href="editor/plugin-manager.md">Plugin Manager</a>, <a href="editor/plugin-sdk.md">Plugin SDK</a></td>
    </tr>
    <tr>
      <td><strong>Reference</strong></td>
      <td><a href="api/README.md">API reference</a></td>
      <td><a href="architecture_specs.md">Architecture specs</a>, <a href="MASTER.md">Master index</a>, <a href="HISTORY.md">History</a></td>
    </tr>
  </tbody>
</table>

## Status of this documentation

The tree mixes **current guides** and **historical plans**. Every page starts with a
status badge:

| Badge | Meaning |
|---|---|
| <span class="doc-badge doc-badge--stable">Stable</span> | Verified against the current source and safe to follow. |
| <span class="doc-badge doc-badge--beta">Beta</span> | Implemented but still changing. |
| <span class="doc-badge doc-badge--reference">Reference</span> | API or module reference; check the linked header. |
| <span class="doc-badge doc-badge--planned">Planned</span> | Design only; no current implementation. |
| <span class="doc-badge doc-badge--historical">Historical</span> | Kept for context; not current API. |

Plans under `plans/` are historical unless the page says otherwise. They document
decisions and sessions, not the current editor.

## Editing the docs

The authoring standard is **HTML-first Markdown**:
[`DOCS_STYLE.md`](https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/DOCS_STYLE.md).
Every page needs a `doc-meta` strip, figures for screenshots and relative links that
stay inside the docs tree. Source links use absolute GitHub URLs.

```bash
cd caffeine-website
python3 scripts/audit-docs.py --include-engine
python3 scripts/audit-docs-i18n.py
```

Screenshots are generated by the headless driver, never by a desktop screenshot:

```bash
./scripts/capture-editor-docs.sh
```

## References

- Engine and Doppio: <https://github.com/devscafecommunity/caffeine>
- Editor plugins: <https://github.com/devscafecommunity/doppio-plugins>
- Launcher: <https://github.com/devscafecommunity/caffeine-launcher>
- Asset packer: <https://github.com/devscafecommunity/caf-pack>
- Website and books: this repository (`content/`, `tex/`, `captures/`)
