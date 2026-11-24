# Terrain editing: Phase 2 report (material palette and painting)

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Done</span>
  <span class="doc-badge">Doppio</span>
  <span>Last updated: <time datetime="2026-11-24">2026-11-24</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/en/docs/doppio/terrain-editing-phase-2.md"><code>terrain-editing-phase-2.md</code></a></span>
</div>

<p class="doc-lede">Painting a terrain with up to 64 material layers as built: a palette, a layer map that names four layers at every texel, paint, erase, replace and smooth strokes that share the sculpting brush, auto-layering by slope, height and masks, a renderer that draws it from one array texture, and the Terrain Paint tab, with the C ABI 29 that carries it. It stands on <a href="terrain-editing-phase-1.md">Phase 1</a>; the plan is in <a href="terrain-editing-roadmap.md"><code>terrain-editing-roadmap.md</code></a>.</p>

## 1. What Phase 2 delivered

<table>
  <thead><tr><th>Piece</th><th>Where</th><th>What it does</th></tr></thead>
  <tbody>
    <tr><td>Palette</td><td><code>src/caffeine/terrain/paint/TerrainPalette.*</code></td><td>Up to 64 layers: name, picture, normal path (kept, not drawn yet), metres per repeat, rotation, tint, sharpness class (256 to 4096), lock. The <code>.terrainpalette</code> text file</td></tr>
    <tr><td>Layer map</td><td><code>terrain/paint/TerrainLayerMap.*</code></td><td>Four layers and their weights at every splat texel (8 bytes a texel), edits by shares with deterministic rounding, locks, renumbering, the legacy four-layer conversion, the <code>.terrainlayers</code> file with a CRC-32</td></tr>
    <tr><td>Paint stroke</td><td><code>terrain/paint/TerrainPaintStroke.*</code></td><td>Paint, Erase, Replace and Smooth on the sculpting brush's shape (falloff, stamp, rotation, jitter, symmetry, protection masks); block-by-block undo records</td></tr>
    <tr><td>Auto-layering</td><td><code>terrain/paint/TerrainAutoLayer.*</code></td><td>Paints the layers from rules on slope, height, curvature and stored masks, in the syntax of the biome table</td></tr>
    <tr><td>Shared stroke core</td><td><code>terrain/edit/TerrainStroke.*</code></td><td><code>placeStamp</code>, <code>shapeWeight</code> and <code>protectionWeight</code> are now shared by sculpting and painting (Phase 0 and 1 results are unchanged: the golden tests pass)</td></tr>
    <tr><td>Cache and scene</td><td><code>terrain/TerrainCache.*</code>, <code>scene/EditorSceneSerializer.cpp</code></td><td>The cache owns palette and map; the scene (blob version 12) records whether layers are on and where the files are; saving writes both files next to the terrain data</td></tr>
    <tr><td>Renderer</td><td><code>render/shaders/terrain_lit.frag</code>, <code>terrain/TerrainGpuTextures.*</code>, <code>render/GpuTextureCache.*</code></td><td>An index map and a weight map (RGBA8) over a 2D array texture with one slice per layer in use; per-layer tiling and rotation; a VRAM budget</td></tr>
    <tr><td>C ABI</td><td><code>capi/EngineAPI.*</code></td><td>Version 29: layers on and off, the palette (read, apply as text, remove, move), paint strokes, auto-layering, a layer probe</td></tr>
    <tr><td>Terrain Paint tab</td><td><code>uikit/panels/terrain_paint.rs</code>, <code>windows/main/terrainpaint.rs</code></td><td>Palette list with swatches and coverage, the selected layer's settings, the paint brush, auto-layering rules</td></tr>
  </tbody>
</table>

## 2. The model

- A terrain is painted with its <strong>four older layers</strong> until layered painting is turned on. Turning it on makes the palette from those four layers and the layer map from the splat map, so nothing visible changes; an older project opens exactly as before.
- Every texel of the <strong>layer map</strong> names up to four palette layers and how much of each (the weights add up to 255). A pixel only ever blends four layers, which is why 64 are affordable.
- Edits move <strong>shares</strong>: painting moves a share of everything that is not the layer toward it, erasing gives a layer's weight to the others, replacing moves one layer's weight to another, smoothing moves a texel toward the average of its neighbours. A small share on a soft brush edge does not vanish in a byte: the rounding is stochastic but a hash of the texel and the stamp decides it, so it is unbiased on average and identical on every run.
- A texel keeps its four heaviest layers; a fifth takes the place of the lightest.
- A <strong>locked</strong> layer never changes (painting it does nothing, and nothing can take weight from it). Lock is a property of the layer, not a mode.
- The map has the resolution of the splat map (the terrain's grid times its splat scale) and follows it when the terrain is resized.

## 3. Painting

<table>
  <thead><tr><th>Mode</th><th>What a stamp does</th></tr></thead>
  <tbody>
    <tr><td>Paint</td><td>Moves weight toward the selected layer; strength 1 paints it solid</td></tr>
    <tr><td>Erase</td><td>Takes the selected layer away and gives its weight to the others in proportion; a texel that is all that layer stays</td></tr>
    <tr><td>Replace</td><td>Moves the weight of the "replace" layer to the selected one</td></tr>
    <tr><td>Smooth</td><td>Blends each texel toward its 3 x 3 neighbourhood. Every texel of a stamp is computed from the layers as they were, so the result does not depend on the order of texels</td></tr>
  </tbody>
</table>

The brush is the one that sculpts: the panel has its own radius, strength, spacing and falloff, and a switch to take the <strong>shape</strong> (stamp picture, jitter, symmetry, protection masks) from the Terrain Brush tab's working brush. Stamps are laid by spacing in metres, so the same path gives the same layers at any sampling rate. One stroke is one undo step. <kbd>Ctrl</kbd> turns paint into erase and back, <kbd>Shift</kbd> smooths, <kbd>[</kbd> and <kbd>]</kbd> resize the active brush.

## 4. Auto-layering

Rules are the biome-table text, where the class number is the palette layer:

```
class 1 base 1
  slope 0.3 0.4 1 1
class 2 base 1
  height 0.6 0.7 1 1
```

Each texel evaluates the density of every ruled layer; the layers share the texel in proportion to their density, and a texel no rule claims takes the fallback layer. Several rules on one layer are one class whose terms must all hold. Locked layers keep their weight and the rules share what is left. The result is one undo step. Masks are <code>slope</code>, <code>height</code>, <code>curvature</code> (all 0 to 1) and the terrain's stored masks.

## 5. Rendering

- The shader reads the nearest texel's four layer indices and weights, smoothed over the four texels around the point (so a painted edge is not a staircase of squares), and blends the layers' pictures from one <strong>2D array texture</strong> with the same triplanar projection the terrain used. Each layer has its own metres per repeat and its own rotation.
- <strong>Only layers in use get a slice</strong>, so 64 layers in a palette cost what the terrain really shows. Every picture is resampled to the array's size class (the largest sharpness among the layers in use) with a full mip chain; a layer without a picture draws its tint as a flat colour.
- <strong>VRAM budget:</strong> the component's budget (256 MB by default) lowers the size class by halves until the array fits. The panel shows the slices, the class and the megabytes.
- Painting uploads <strong>only the rectangle the stroke touched</strong> (a stroke on a 4k map is kilobytes, not the 134 MB of the whole map). A new layer in use rebuilds the array once.
- With layers off nothing of this runs: the four-layer path is the same code as before.

## 6. Files and the scene

<table>
  <thead><tr><th>File</th><th>Content</th></tr></thead>
  <tbody>
    <tr><td><code>Name.terrainpalette</code></td><td>Text: one <code>layer Name</code> block per layer with <code>albedo</code>, <code>normal</code>, <code>tile</code>, <code>rotation</code>, <code>tint</code>, <code>resolution</code>, <code>locked</code>. <code>#</code> comments; unknown keys are skipped</td></tr>
    <tr><td><code>Name.terrainlayers</code></td><td>Binary: <code>TLMP</code>, a version, the size, the lock mask, 8 bytes a texel, a CRC-32 of the whole. A damaged or truncated file is refused with a reason</td></tr>
  </tbody>
</table>

Saving the scene writes both next to the terrain data and records their paths in the terrain component (scene blob version 12); opening reads them, and a missing or damaged map falls back to the splat map the terrain was made from instead of losing the terrain. In-memory scene snapshots (undo of other edits) do not carry the layer map (it can be 134 MB): the layers are set aside and handed back to their terrain, whether the restored state has layers on or off.

## 7. Undo

Painting, auto-layering and palette edits are engine records, like sculpting strokes (the same revert and reapply calls). A palette edit that renumbers layers (remove, move) keeps the blocks of the map it changed. A run of edits of one palette field (dragging a slider) folds into the first edit's record: one step, undone at once. Turning layers on or off is a scene step.

## 8. C ABI 29

<table>
  <thead><tr><th>Function</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>caffeine_session_terrain_layers_enable</code>, <code>_layers</code></td><td>Layers on or off; their state (palette size, map size, GPU slices, class and bytes)</td></tr>
    <tr><td><code>caffeine_session_terrain_palette_layer</code>, <code>_palette_text</code></td><td>Read a layer (with its texel count) or the palette as text</td></tr>
    <tr><td><code>caffeine_session_terrain_palette_apply</code></td><td>Replace the palette by text (at least as many layers; extras are appended), with <code>merge_into</code> to fold an edit into the previous record. The error names the line</td></tr>
    <tr><td><code>caffeine_session_terrain_palette_remove</code>, <code>_palette_move</code></td><td>Renumbering edits, undoable</td></tr>
    <tr><td><code>caffeine_session_terrain_paint_begin</code></td><td>Opens a paint stroke; points, end, revert and reapply are the stroke calls of version 25</td></tr>
    <tr><td><code>caffeine_session_terrain_autolayer</code></td><td>Rules in, one record out</td></tr>
    <tr><td><code>caffeine_session_terrain_layer_at</code></td><td>The layers and weights under a world point</td></tr>
  </tbody>
</table>

## 9. Agent actions

<code>show_terrain_paint</code>, <code>terrain_paint_active</code>, <code>terrain_paint_layers</code>, <code>terrain_paint_add_layer</code>, <code>terrain_paint_select_layer</code>, <code>terrain_paint_edit_layer</code>, <code>terrain_paint_remove_layer</code>, <code>terrain_paint_move_layer</code>, <code>terrain_paint_set</code>, <code>terrain_paint_rule</code>, <code>terrain_paint_set_rule</code>, <code>terrain_paint_autolayer</code> and <code>terrain_paint_stroke</code> (one stroke along world points, the same path as the mouse). The <code>terrain_paint</code> query reads the state and the <code>terrain_layer_at</code> query the layers under a point. Widget ids start with <code>terrain_paint.</code> and are in the catalogue.

## 10. Verification

- C++: <code>tests/test_terrain_paint.cpp</code> (27 cases): the palette (64 layers, renumbering, the text round trip, errors with the line, sharpness classes, the legacy four layers); the layer map (weights always add up to 255, four heaviest kept, small shares not lost to the byte, deterministic, locks, erase, replace, smooth, removing and moving layers, the legacy splat conversion both ways, the file and its damage); paint strokes (every mode undoes bit for bit, the same layers at any sampling rate, protection, symmetry, stamp pictures, a stroke on a 2049 map touches a few blocks and takes under 400 ms); auto-layering (by slope, by density, locked, by region). A C ABI case covers layers, the palette, painting, auto-layering, removal and move with undo, record merging and a scene save and load.
- Rust: an engine-crate test that <strong>renders</strong> a terrain with a red and a blue layer painted on it and counts the pixels of each colour, undoes the red stroke, redoes it and turns layers off; <code>terrain_paint</code> app tests (the pane, layers on as one step, add, paint, undo in order, a mouse drag, a slider drag as one step, rename, lock, remove and move with the paint following, auto-layering, tool exclusivity, replace); panel and module unit tests. The headless flow <code>terrain-paint-panel.json</code> runs through the real CLI.

## 11. Decisions recorded

- A palette layer costs nothing until it is used: slices are made for the layers in use, not for the 64.
- Four layers per texel is the rule of the file, the editor and the shader; the layer map is not in the scene snapshot because of its size, and records undo it exactly.
- Turning layers off draws the terrain with layers 0 to 3 (the splat map is rebuilt from them); the palette and the map stay in memory so that undo brings everything back, and turning layers on again starts over from the four-layer view.
- Lock is a layer property, so it follows a layer when layers are renumbered.

## 12. Known limits and what is next

- <strong>Not done from the roadmap:</strong> the offline BC7 and BC5 compression by <code>caf-pack</code> (pictures are uploaded as RGBA8), residency by camera (slices follow the layers in use anywhere on the terrain, not what a camera sees), and the simple mode per quality level (it is per terrain: layers off).
- Per-layer normal maps are stored but not drawn; the terrain still has its one normal map. Height blending between layers is not done.
- The renderer reads the nearest texel's four layers and smooths their weights over four texels; a layer that is in the neighbours but not in the nearest texel does not appear at that pixel.
- The palette is the terrain's own (two files next to its data); there is no shared palette asset to import yet.
- Next: Phase 3 (vegetation) can start now; Phase 5 adds painted masks, roads and rivers by spline, tablet pressure and precompiled GI.

## 13. Work log

- <strong>2026-11-24</strong>: the palette, the layer map, the paint stroke and auto-layering with tests; the shared stroke core; the cache, scene format 12 and the files; the GPU path (array texture, index and weight maps, rectangle uploads, budget) checked by a rendering test; C ABI 29; the Rust wrappers; the Terrain Paint tab, the mouse tool, agent actions and these pages. Incidents: a stale cache entry from an earlier terrain with the same id (tests share the process) put 16 layers on a new terrain, so turning layers on now always starts from the terrain's own four layers; a scene restore removes every cache entry, which would have dropped unsaved painting, so the layers are set aside and handed back.
