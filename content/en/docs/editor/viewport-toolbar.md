# Viewport HUD and controls

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/doppio/crates/ui/src/uikit/components/viewport_surface.rs"><code>viewport_surface.rs</code></a></span>
</div>

<p class="doc-lede">The Rust viewport has a compact HUD instead of an icon toolbar.
View mode, gizmo mode, grid and markers are driven by the View menu and shortcuts;
the HUD reports exactly what the renderer is doing.</p>

<figure class="doc-figure">
  <img src="../images/editor/workspace-scene.png" alt="Viewport HUD showing resolution, grid, anti-aliasing, gizmo mode, frame time and FPS" loading="lazy">
  <figcaption>The top-left chip reports render size, grid, anti-aliasing, gizmo mode, latency and FPS. The hint chip lists the camera gestures; the bottom line names the selection.</figcaption>
</figure>

## HUD

The status chip is assembled in `windows/main.rs` and rendered by
`viewport_surface`:

```text
1872×1075 · grid · FXAA · Move · 18 ms · 57 FPS
```

| Field | Meaning |
|---|---|
| `width×height` | Internal render size in physical pixels, after `render_scale`. |
| `grid` / `no grid` | Reference grid state. |
| `no AA` / `FXAA` / `TAA` | Active anti-aliasing mode. |
| `Move` / `Rotate` / `Scale` | Gizmo mode. |
| `ms` | Latency of the last completed readback. |
| `FPS` | Completed viewport frames in the last second. |

The bottom hint shows `Selected: <entity> · Double-click to focus`, or the focus hint
when nothing is selected.

## View menu

<table class="doc-table">
  <thead>
    <tr><th>Item</th><th>Shortcut</th><th>Effect</th></tr>
  </thead>
  <tbody>
    <tr><td>Focus Selection</td><td><code>Ctrl+F</code> or <code>F</code></td><td>Moves the orbit focus to the selected entity.</td></tr>
    <tr><td>Reset Camera</td><td><code>Ctrl+0</code></td><td>Restores the default orbit distance and angles.</td></tr>
    <tr><td>Render Now</td><td><code>Ctrl+R</code></td><td>Requests an immediate viewport frame.</td></tr>
    <tr><td>Show / Hide Scene Markers</td><td>—</td><td>Toggles light, camera, collider and empty markers.</td></tr>
    <tr><td>Show / Hide Grid</td><td><code>G</code></td><td>Toggles the reference grid.</td></tr>
    <tr><td>Move Tool</td><td><code>1</code></td><td>Translate gizmo.</td></tr>
    <tr><td>Rotate Tool</td><td><code>2</code></td><td>Rotate gizmo.</td></tr>
    <tr><td>Scale Tool</td><td><code>3</code></td><td>Scale gizmo.</td></tr>
    <tr><td>Terrain / Water / Nature / Texture Generator</td><td>—</td><td>Opens the matching generator tab.</td></tr>
    <tr><td>Default Layout</td><td><code>Ctrl+1</code></td><td>Restores the standard pane arrangement.</td></tr>
    <tr><td>Viewport Layout</td><td><code>Ctrl+2</code></td><td>Maximises the viewport area.</td></tr>
  </tbody>
</table>

## Camera gestures

| Gesture | Action |
|---|---|
| Drag | Orbit |
| Right or middle drag | Pan |
| Wheel | Zoom |
| `W` `A` `S` `D` / `Q` `E` | Fly / down-up |
| `Shift` | Boost |
| Double-click | Focus the entity under the cursor |

## Anti-aliasing and render scale

Anti-aliasing and render scale are part of `CaffeineViewportSettings` in the C ABI and
are clamped by the engine:

- `anti_aliasing`: `Off`, `FXAA` or `TAA`.
- `render_scale`: `0.5` to `2.0`; values above 1 supersample, below 1 trade sharpness
  for speed.

The render size is the pane's logical size multiplied by the scale and the display
scale factor. Change the pane size to change the render resolution; the HUD updates
on the next completed frame.

<div class="doc-callout doc-callout--note">
  <p><strong>Historical note.</strong> The archived C++ editor had a floating
  icon-only toolbar with 2D/3D/Iso and perspective/orthographic buttons. It is not
  part of the Rust viewport; use the View menu and shortcuts above.</p>
</div>

## Related pages

- [Scene viewport](scene-viewport.md) — readback pipeline, picking and camera maths.
- [Gizmos and markers](../doppio/gizmos-and-markers.md)
- [Performance](../performance/editor-viewport-performance.md)
