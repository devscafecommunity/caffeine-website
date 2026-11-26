# ImGui host (runtime and legacy plugins)

<div class="doc-meta">
  <span class="doc-badge doc-badge--reference">Reference</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Legacy</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/apps/runtime/ImGuiIntegration.hpp"><code>apps/runtime/ImGuiIntegration.hpp</code></a></span>
</div>

<p class="doc-lede">Dear ImGui is no longer the Doppio editor UI. It remains the
immediate-mode host for <code>caffeine-runtime</code> and the legacy C++ plugin SDK.
The active editor is Rust/Iced.</p>

<div class="doc-callout doc-callout--warning">
  <p><strong>Do not build new editor panels in ImGui.</strong> The Rust editor uses
  <a href="../editor/workspace-and-theme.md">Iced components</a>. ImGui panels are for
  the standalone runtime and plugins that still target the C++ SDK.</p>
</div>

## Two UI models

<table class="doc-table">
  <thead>
    <tr><th>Model</th><th>Used by</th><th>Where</th></tr>
  </thead>
  <tbody>
    <tr><td>Retained, Iced</td><td>Doppio editor: docking, hierarchy, inspector, viewport, assets, console, generators</td><td><code>doppio/crates/ui/</code></td></tr>
    <tr><td>Immediate, Dear ImGui</td><td><code>caffeine-runtime</code>, archived C++ Doppio, legacy plugins</td><td><code>apps/runtime/</code>, <code>include/caffeine/ui/</code>, <code>doppio-archived/</code></td></tr>
    <tr><td>Retained game UI</td><td>In-game HUD and menus</td><td><code>src/caffeine/ui/</code>, <a href="game-ui.md">Game UI</a></td></tr>
  </tbody>
</table>

## Runtime integration

`apps/runtime/ImGuiIntegration.hpp` owns the SDL3 + RHI ImGui backend used by the
runtime executable:

- `init(window, device)` — creates the ImGui context and backend data.
- `beginFrame()` / `endFrame(commandBuffer)` — records the draw data into the RHI.
- `processEvent(SDL_Event)` — forwards SDL input.
- `wantsKeyboard()` / `wantsMouse()` — tells the runtime whether ImGui captured input.

The runtime draws its profiler, console and scene overlays through this host. The
engine core (`caffeine-core`) has no ImGui dependency; the adapters live in
`caffeine-editor-support` and the runtime.

## UIKit for plugins

C++ plugins draw with the public immediate-mode kit in `include/caffeine/ui/`:

| Header | Contents |
|---|---|
| `UI.hpp` | Umbrella for the composable element kit |
| `Widgets.hpp` | Buttons, property rows, section headers, empty states |
| `Theme.hpp` | Palette and metrics |
| `Icons.hpp` | Vector glyphs |
| `PanelRegistry.hpp` | Stable panel ids and categories |
| `Workspace.hpp` | JSON docking layout for the plugin host |
| `Panel.hpp` | Panel descriptors |

Plugin panels call `Caffeine::UIKit` and register through `PanelRegistry`; they do not
link against Doppio internals. See [Plugin SDK](../editor/plugin-sdk.md).

## Profiler and console

The profiler and console windows are runtime/legacy-editor tools. They consume
`Debug::Profiler` and `Debug::LogSystem` data; the Rust editor has its own typed
Console pane and does not embed ImGui.

## Related pages

- [Workspace, theme and components](../editor/workspace-and-theme.md)
- [Game UI](game-ui.md)
- [Plugin SDK](../editor/plugin-sdk.md)
- [Debug tools](../debug/debug-tools.md)
