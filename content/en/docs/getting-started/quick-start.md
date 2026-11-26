# Quick start

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">Create a project, add an entity, save a scene and learn the
viewport gestures in a few minutes.</p>

<figure class="doc-figure">
  <img src="../images/editor/project-manager.png" alt="Doppio project manager before a project is opened" loading="lazy">
  <figcaption>Doppio starts in the project manager. Create a project, open a recent one or browse a projects folder.</figcaption>
</figure>

## 1. Create a project

Launch Doppio without arguments:

```bash
cd doppio
cargo run -p doppio-ui
```

In the project manager:

1. Open **Create New**.
2. Enter a project name and a location.
3. Choose **Empty**, **2D** or **3D**.
4. Press **Create & Open**.

Doppio writes `project.caffeine` and creates `assets/raw`, `assets/processed`,
`scripts`, `scenes`, `materials`, `texture_sets` and `build`. The 3D template also
prepares model, texture, material, animation, audio, prefab and sky folders under
`assets/raw`.

## 2. Meet the workspace

<figure class="doc-figure">
  <img src="../images/editor/workspace-scene.png" alt="Default Doppio workspace with hierarchy, viewport, inspector and bottom asset and console panes" loading="lazy">
  <figcaption>The default layout: Hierarchy on the left, Viewport and generator tabs in the centre, Inspector and material tabs on the right, and Assets next to Console in the bottom dock.</figcaption>
</figure>

<table class="doc-table">
  <thead>
    <tr><th>Pane</th><th>Tabs</th><th>What it does</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Hierarchy</strong></td>
      <td>Hierarchy</td>
      <td>Scene tree, search, add/delete entities and drag-to-reparent.</td>
    </tr>
    <tr>
      <td rowspan="2"><strong>Centre</strong></td>
      <td>Viewport</td>
      <td>Engine render, selection, gizmos, scene markers and camera flight.</td>
    </tr>
    <tr>
      <td>Material Generator · Texture Generator · Texture Set · Script · Dryad Nodes</td>
      <td>Content tools that share the centre pane; drag their tabs to another pane.</td>
    </tr>
    <tr>
      <td rowspan="2"><strong>Right</strong></td>
      <td>Inspector</td>
      <td>Entity name, transform, component cards and <em>Add Behaviour</em>.</td>
    </tr>
    <tr>
      <td>Material · Nature · Water · Terrain</td>
      <td>Asset and procedural generators with live previews.</td>
    </tr>
    <tr>
      <td><strong>Bottom</strong></td>
      <td>Assets · Console</td>
      <td>Project browser with import/pack, plus typed and filterable logs.</td>
    </tr>
  </tbody>
</table>

Drag a tab away from its header to dock it in another pane. The docking guide shows
the centre and edge targets; the pane buttons maximise or restore a pane. View
presets live in **View → Default Layout** (`Ctrl+1`) and **View → Viewport Layout**
(`Ctrl+2`).

## 3. Add an entity

1. Press `Ctrl+N`, use **Scene → Add Entity**, or press the **+** in the Hierarchy.
2. Select the new row; the Inspector shows its **Transform** card.
3. Open **Scene → Create Entity…** (`Ctrl+Shift+N`) for the prefab palette: mesh,
   lights, camera, physics, terrain, water and duplicate selection.
4. Edit **Position**, **Rotation** and **Scale**, or drag the gizmo in the viewport.

Parent groups compose their transform into their children; the gizmo projects the
resolved world position.

## 4. Move around the viewport

| Input | Action |
|---|---|
| Drag in the viewport | Orbit the camera |
| Right or middle drag | Pan the camera |
| Mouse wheel | Zoom |
| `W` `A` `S` `D` | Fly horizontally |
| `Q` / `E` | Fly down / up |
| `Shift` | Fly boost |
| `1` / `2` / `3` | Move / Rotate / Scale gizmo |
| `G` | Toggle the grid |
| `F` | Frame the selection (focus) |
| `Ctrl+0` | Reset the camera |

The viewport HUD shows resolution, grid state, gizmo mode, view model, FPS and the
lighting overlay. Rendering is offscreen and asynchronous, so the UI stays
responsive while the engine renders.

## 5. Save the scene

Press `Ctrl+S` or use **Scene → Save Scene**. Scenes are `.caf` files; the title bar
shows the scene name and a **Saved** badge. The inspector and hierarchy edits are
undoable with `Ctrl+Z` and `Ctrl+Shift+Z`.

## Next steps

- [Editor UI gallery](../editor/ui-gallery.md) for a visual tour of every pane.
- [Scene viewport](../editor/scene-viewport.md) for rendering and camera details.
- [Headless testing](../doppio/headless-testing.md)
  to script the same steps without a window.
