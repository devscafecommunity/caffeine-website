# Editor UI gallery

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/captures/flows/capture-editor-docs.json"><code>capture-editor-docs.json</code></a></span>
</div>

<p class="doc-lede">A visual tour of the Rust Doppio workspace, captured off-screen by
the headless driver so every image matches the current widget tree.</p>

<figure class="doc-figure">
  <img src="../images/editor/project-manager.png" alt="Doppio Project Manager with Create New, Open Recent and Browse Projects tabs" loading="lazy">
  <figcaption>The Project Manager opens before any scene. Create a project, reopen a recent one or scan a projects folder.</figcaption>
</figure>

## Startup and project manager

Doppio starts in the project manager when no scene is passed on the command line. The
dialog has three tabs:

| Tab | Purpose |
|---|---|
| **Create New** | Project name, location, template (Empty / 2D / 3D) and **Create &amp; Open**. |
| **Open Recent** | Recent projects with search and **Open Selected**. |
| **Browse Projects** | Scans a folder for `project.caffeine` files. |

The default projects directory is `~/Documents/CaffeineProjects`; override it with
`CAFFEINE_PROJECTS_DIR`. The manifest is `project.caffeine`, and the standard folders
are created on demand.

## Default workspace

<figure class="doc-figure">
  <img src="../images/editor/workspace-scene.png" alt="Default Doppio workspace with Hierarchy, Viewport, Inspector and Assets and Console panes" loading="lazy">
  <figcaption>The default layout with an engine-backed scene. The top bar holds the menus and the project/scene status; the bottom dock holds Assets and Console.</figcaption>
</figure>

<video class="doc-video" autoplay loop muted playsinline width="960"
       poster="../images/editor/workspace-scene.png">
  <source src="../images/editor/doppio-tour.mp4" type="video/mp4">
  <a href="../images/editor/doppio-tour.gif">Watch the workspace tour (GIF)</a>
</video>

<p class="doc-caption">The same capture flow can record motion: menus open, a hierarchy row is selected, and the result is encoded to MP4 by ffmpeg.</p>

The workspace is a single Iced window split into four docked regions:

- **Hierarchy** on the left.
- **Viewport** and the content tools in the centre.
- **Inspector** and the asset generators on the right.
- **Assets + Console** in the bottom dock.

Tabs can be dragged between panes; the docking guide shows the centre and edge
targets. Pane buttons maximise and restore. Layout presets are `Ctrl+1` (Default) and
`Ctrl+2` (Viewport).

## Panes

<figure class="doc-figure">
  <img src="../images/editor/pane-hierarchy.png" alt="Hierarchy pane with a scene tree, search field and add button" loading="lazy">
  <figcaption>Hierarchy: search, scene tree with parent groups, selection and the add button. Drag a row onto another to reparent.</figcaption>
</figure>

<figure class="doc-figure">
  <img src="../images/editor/pane-inspector.png" alt="Inspector pane with entity name, transform fields, component cards and Add Behaviour" loading="lazy">
  <figcaption>Inspector: name, combined transform, collapsible component cards and the Add Behaviour picker.</figcaption>
</figure>

<figure class="doc-figure">
  <img src="../images/editor/pane-assets.png" alt="Assets pane with folder tree, breadcrumb, New and Import buttons and an asset grid" loading="lazy">
  <figcaption>Assets: folder tree, breadcrumb, search, grid/list modes and the New/Import wizard.</figcaption>
</figure>

<figure class="doc-figure">
  <img src="../images/editor/pane-console.png" alt="Console pane with typed and filterable log entries" loading="lazy">
  <figcaption>Console: Errors, Log, Actions, Engine and UI filters, with the newest entry at the bottom.</figcaption>
</figure>

## Menus

<figure class="doc-figure">
  <img src="../images/editor/menu-scene.png" alt="Scene menu open with Add Entity, Create Entity, New Material, generators, Save Scene and Play" loading="lazy">
  <figcaption>Scene menu: entities, material generator, script and Dryad panels, save and play.</figcaption>
</figure>

<figure class="doc-figure">
  <img src="../images/editor/menu-view.png" alt="View menu open with generators, camera commands, markers, grid, gizmos and layouts" loading="lazy">
  <figcaption>View menu: generators, focus/reset camera, render now, markers, grid, gizmo modes and layout presets.</figcaption>
</figure>

The menus are floating overlays. Hovering a widget behind an open menu does not close
it; click outside, press `Escape` or choose an item.

## Content tools

### Material Generator

<figure class="doc-figure">
  <img src="../images/editor/material-generator.png" alt="Material Generator with node graph, preview and channel packing controls" loading="lazy">
  <figcaption>The Material Generator: node palette, graph canvas, live preview, channel previews and ORM packing. Bake to Material writes the maps into the open <code>.mat</code>.</figcaption>
</figure>

### Texture Generator

<figure class="doc-figure">
  <img src="../images/editor/texture-generator.png" alt="Texture Generator with node graph, preview and export controls" loading="lazy">
  <figcaption>The Texture Generator uses the same node canvas with texture-specific ops, presets, export and flipbooks.</figcaption>
</figure>

### Nature, Water and Terrain

<figure class="doc-figure">
  <img src="../images/editor/nature-generator.png" alt="Nature Generator with a node graph and generated plants" loading="lazy">
  <figcaption>Nature Generator: rocks, trees and plants from a node graph, with quality modes and OBJ export.</figcaption>
</figure>

<figure class="doc-figure">
  <img src="../images/editor/water-generator.png" alt="Water Generator with a wave node graph and water preview" loading="lazy">
  <figcaption>Water Generator: wave sources, modifiers, look controls and presets.</figcaption>
</figure>

<figure class="doc-figure">
  <img src="../images/editor/terrain-generator.png" alt="Terrain Generator with a field graph, splat layers and 3D preview" loading="lazy">
  <figcaption>Terrain Generator: field sources, modifiers, masks and erosion, with splat preview and Place in Scene.</figcaption>
</figure>

## Rebuilding this gallery

The images come from a committed headless flow:

```bash
./scripts/capture-editor-docs.sh   # PNGs
./scripts/capture-editor-tour.sh   # MP4 + GIF
```

It writes stable names under `content/en/docs/images/doppio/editor/`. Copy the files into
`content/{en,pt}/docs/images/editor/` after regenerating. Do not edit the PNGs by
hand.
