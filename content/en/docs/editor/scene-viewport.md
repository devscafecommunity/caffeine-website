# Scene viewport

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/doppio/crates/ui/src/uikit/components/viewport_surface.rs"><code>viewport_surface.rs</code></a></span>
</div>

<p class="doc-lede">The viewport is a GPU render owned by the engine, read back into
the Rust editor and composited under the gizmo, markers and HUD. It never blocks the
UI thread.</p>

<figure class="doc-figure">
  <img src="../images/editor/workspace-scene.png" alt="Doppio viewport with the grid, transform gizmo and scene markers over a rendered scene" loading="lazy">
  <figcaption>The engine render arrives as pixels; the toolbar, HUD, gizmo and scene markers are drawn by the editor over the frame.</figcaption>
</figure>

## Frame pipeline

1. The pane reports its logical size. The editor keeps a desired render size in
   physical pixels and requests a frame at most every 16 ms.
2. `caffeine_session_render_begin(width, height)` starts an offscreen engine render.
3. The 16 ms `ViewportTick` polls `caffeine_session_render_poll` into a reusable RGBA
   buffer. States are `Pending`, `Ready`, `Idle` and `Failed`.
4. On `Ready`, the pixels are uploaded to an Iced/wgpu texture through
   `uikit/components/viewport_shader.rs`. A content hash skips identical frames, so a
   static scene does not re-upload every tick.
5. The editor draws the toolbar, HUD, gizmo and scene markers over the frame. Those
   overlays project with the same camera that produced the image.

<div class="doc-callout doc-callout--warning">
  <p><strong>Warning.</strong> SDL_GPU does not expose a native texture handle through
  the public API. A shared wgpu texture is therefore not possible without a renderer
  change (wgpu backend, SDL patch or a separate window). The readback path is the
  supported one; do not describe it as zero-copy.</p>
</div>

## Quality settings

<table class="doc-table">
  <thead>
    <tr><th>Setting</th><th>Values</th><th>Notes</th></tr>
  </thead>
  <tbody>
    <tr><td>Anti-aliasing</td><td><code>Off</code>, <code>FXAA</code>, <code>TAA</code></td><td>FXAA is the default; TAA accumulates across frames and needs camera stability.</td></tr>
    <tr><td>Render scale</td><td><code>0.5</code> … <code>2.0</code></td><td>Internal supersampling; default <code>1.5</code>. The UI stays at logical resolution.</td></tr>
    <tr><td>Grid</td><td>on / off</td><td><code>G</code> or View → Show/Hide Grid.</td></tr>
    <tr><td>Scene markers</td><td>on / off</td><td>View → Show/Hide Scene Markers.</td></tr>
    <tr><td>Gizmo</td><td>Move / Rotate / Scale</td><td><code>1</code>, <code>2</code>, <code>3</code> or View → Move/Rotate/Scale Tool.</td></tr>
  </tbody>
</table>

The HUD reports resolution, grid, gizmo mode, view model, FPS and render latency.
`Ctrl+R` forces a frame; `Ctrl+0` resets the camera.

## Camera

| Input | Action |
|---|---|
| Drag | Orbit around the focus point |
| Right or middle drag | Pan the focus |
| Wheel | Zoom (exponential) |
| `W` `A` `S` `D` | Fly horizontally |
| `Q` / `E` | Fly down / up |
| `Shift` | Fly boost |
| `F` or double-click | Focus the selection |
| `Ctrl+0` | Reset the camera |

The camera state lives in `windows/main.rs`; `viewport_surface` only converts pointer
and wheel events into camera messages. That separation keeps the camera maths out of
the widget and makes it testable.

## Selection and picking

A click uses a ray from the cursor through the camera. If the ray hits a gizmo handle,
the gizmo consumes it; otherwise a scene marker takes it; otherwise the engine picks
the mesh. The result updates the selection and the Inspector. Picking uses the world
transform resolved through the parent chain, so children of moved groups select
correctly.

## Empty state and fixtures

When no engine session is available, the viewport shows **Waiting for the engine
viewport…**. This is expected in the `entities` and `empty` headless fixtures. The
`scene3d` fixture starts a real engine session with lights, a camera and meshes, and
is the fixture used by the gizmo/marker capture flows.

## Related pages

- [Viewport toolbar](viewport-toolbar.md) — icon toolbar and projections.
- [Gizmos and markers](../doppio/gizmos-and-markers.md)
- [Materials guide](../doppio/materials-guide.md)
- [Performance](../performance/editor-viewport-performance.md)
