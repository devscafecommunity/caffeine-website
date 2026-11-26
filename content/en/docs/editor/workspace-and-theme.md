# Workspace, theme and components

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/doppio/crates/ui/src/uikit/theme.rs"><code>uikit/theme.rs</code></a></span>
</div>

<p class="doc-lede">How the Rust Doppio workspace is composed: the PaneGrid layout,
the Iced component kit, the visual tokens, and where the legacy C++ UI kit still
applies.</p>

<figure class="doc-figure">
  <img src="../images/editor/workspace-scene.png" alt="Doppio workspace with the hierarchy, viewport, inspector and bottom asset panes" loading="lazy">
  <figcaption>The editor is one window split by a <code>PaneGrid</code>. Panels are pure view functions; interactive primitives live in <code>uikit/components/</code>.</figcaption>
</figure>

## Two UI stacks, one product

<table class="doc-table">
  <thead>
    <tr><th>Stack</th><th>Used by</th><th>Location</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Rust / Iced</strong></td>
      <td>The active Doppio editor: docking, hierarchy, viewport, inspector, assets, console and generators.</td>
      <td><code>doppio/crates/ui/</code></td>
    </tr>
    <tr>
      <td><strong>C++ / ImGui UIKit</strong></td>
      <td>The standalone runtime, legacy plugins and archived C++ Doppio panels.</td>
      <td><code>include/caffeine/ui/</code></td>
    </tr>
  </tbody>
</table>

The stacks share design vocabulary, not code. Do not describe the Rust editor as
using `Caffeine::UIKit`; the C++ kit is only loaded by the runtime and plugins.

## Window → panel → component

| Layer | Location | Rule |
|---|---|---|
| **Window** | `windows/main.rs` | Owns `App`, messages, subscriptions and the `PaneGrid`. |
| **Panel** | `uikit/panels/*.rs` | Pure `view(...) -> Element`; never calls raw `text_input`, `checkbox`, `slider` or `button`. |
| **Component** | `uikit/components/*.rs` | Reusable primitives: buttons, fields, cards, tabs, menus, tree view, gizmo, viewport surface, node canvas. |

Panels compose components. `scripts/check-rust-ui.sh` rejects raw widgets in
`uikit/panels/`, which keeps focus, hover, disabled states and theme consistent.

## Layout and docking

The default `PaneGrid` is built from four regions:

1. **Hierarchy** on the left.
2. A **centre group** with Viewport, Material Generator, Texture Generator, Texture
   Set, Script and Dryad Nodes.
3. A **right group** with Inspector, Material, Nature, Water and Terrain.
4. A **bottom group** with Assets and Console.

Drag a tab by its header to show docking guides: the centre adds it to the target
pane, an edge splits the pane. Pane buttons maximise and restore. Layout presets are
in the View menu:

| Preset | Shortcut | Result |
|---|---|---|
| Default Layout | `Ctrl+1` | Hierarchy left, centre/right tools, Assets + Console bottom |
| Viewport Layout | `Ctrl+2` | Gives the viewport most of the window |

The Rust layout is session state; it is not written to `workspace.json`. The legacy
ImGui `Caffeine::Workspace` still persists `~/.config/caffeine/ui/workspace.json`
for the runtime and plugin hosts.

## Theme tokens

`doppio/crates/ui/src/uikit/theme.rs` is the only source of colours, borders and
spacing. Panels must not hardcode colours.

<table class="doc-table">
  <thead>
    <tr><th>Token</th><th>Value</th><th>Used for</th></tr>
  </thead>
  <tbody>
    <tr><td><code>BACKGROUND</code></td><td><code>#151515</code></td><td>Window and viewport surround</td></tr>
    <tr><td><code>PANEL</code></td><td><code>#242424</code></td><td>Pane bodies and cards</td></tr>
    <tr><td><code>PANEL_ALT</code></td><td><code>#2e2e2e</code></td><td>Alternating rows and inputs</td></tr>
    <tr><td><code>TOOLBAR</code></td><td><code>#1e1e1e</code></td><td>Tab bars, menus and status bar</td></tr>
    <tr><td><code>BORDER</code></td><td><code>#313131</code></td><td>Panel and field outlines</td></tr>
    <tr><td><code>TEXT</code></td><td><code>#d6d6d6</code></td><td>Primary labels and values</td></tr>
    <tr><td><code>TEXT_MUTED</code></td><td><code>#8e8e8e</code></td><td>Secondary labels and hints</td></tr>
    <tr><td><code>ACCENT</code></td><td><code>#4a8fe0</code></td><td>Selection, focus and active tools</td></tr>
    <tr><td><code>DANGER</code></td><td><code>#c24f4f</code></td><td>Delete, errors and destructive actions</td></tr>
    <tr><td><code>WARNING</code></td><td><code>#d1a03c</code></td><td>Warnings and pending states</td></tr>
    <tr><td><code>SUCCESS</code></td><td><code>#5da56b</code></td><td>Saved state and successful checks</td></tr>
  </tbody>
</table>

Generator identity bars use the icon palette: cyan for Material, orange for Texture
and Terrain, green for Nature, cyan-blue for Water.

## Stable widget ids

Every interactive widget has a hierarchical `UiId`
(`editor.menu.scene`, `inspector.entity.name`, `hierarchy.list.entity_row.3`) and an
entry in `uikit::id::CATALOG` with kind and description. The catalogue drives:

- headless targeting and annotated screenshots;
- the generated [UI reference](ui-reference.md);
- agent actions and the docs captions in `captures/ui-captions.json`.

Add an id and a catalogue entry with every new widget.

## Legacy C++ kit (runtime and plugins)

`include/caffeine/ui/` still provides `Theme`, `Widgets`, `Icons`, `PanelRegistry`
and `Workspace` for `caffeine-runtime` and C++ plugins. It is immediate-mode ImGui,
not Iced. Plugin panels use `caffeine/plugin/PluginUI.hpp` and the same
`PanelRegistry` ids; their layout is persisted by `Workspace` in
`~/.config/caffeine/ui/workspace.json`.

<div class="doc-callout doc-callout--note">
  <p><strong>Note.</strong> The archived C++ editor under <code>doppio-archived/</code>
  also used this kit. It is frozen reference code and is not part of the active
  editor.</p>
</div>
