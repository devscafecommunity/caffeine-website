# Terrain editing: brushes, material palette and vegetation

<div class="doc-meta">
  <span class="doc-badge doc-badge--plan">Plan</span>
  <span class="doc-badge">Doppio</span>
  <span>Last updated: <time datetime="2026-11-24">2026-11-24</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/en/docs/doppio/terrain-editing-roadmap.md"><code>terrain-editing-roadmap.md</code></a></span>
</div>

<p class="doc-lede">A complete terrain editor, not one brush that raises and lowers: a library of custom brushes, a palette of materials to paint with, and a palette of vegetation (trees, plants, rocks, ready-made or <code>.generator.nature</code> recipes) placed adaptively and without overlap, where an edit to a species reaches every instance already on the map.</p>

## 1. Where we start

What exists and is reused, and what is missing.

<table>
  <thead><tr><th>Piece</th><th>State</th></tr></thead>
  <tbody>
    <tr><td><code>TerrainSculptor</code></td><td>5 modes (Raise, Lower, Smooth, Flatten, Noise), one round brush; no C ABI and no interactive UI</td></tr>
    <tr><td><code>TerrainSplatPainter</code></td><td>Paints <strong>4 fixed layers</strong> (one RGBA map): the ceiling of a material palette today</td></tr>
    <tr><td><code>TerrainMasks</code> and <code>BiomeTable</code></td><td>Height, slope, curvature and up to 16 stored masks; rules such as "pines where it is gentle and dry"</td></tr>
    <tr><td>Scatter (<code>scatterTerrain</code>)</td><td>Deterministic by seed, priority and exclusion radius; makes <strong>one entity per instance</strong> (limit 5000) and cannot be edited afterwards</td></tr>
    <tr><td>Recipes (<code>.generator.nature</code>, <code>recipe_ref.rs</code>)</td><td>"Oak, variant 17" is the same model on every machine; baked variants are cached by content hash</td></tr>
    <tr><td>Asset manager, instancing, terrain collider</td><td>References inside the project; instanced draws; a height-field collider rebuilt as a whole</td></tr>
    <tr><td><strong>Missing</strong></td><td>Custom brushes, many layers, vegetation as terrain data (not entities), edit-once-apply-to-all, tile undo, incremental updates, a brush preview</td></tr>
  </tbody>
</table>

## 2. Decisions

- <strong>Native format.</strong> A <code>.terrain</code> container in the <code>caf</code> format holds the terrain in regional tiles. <code>caf-pack</code> decompiles the legacy <code>.cterrain</code> into it, losslessly, and the engine opens old projects by converting.
- <strong>Per-layer resolution.</strong> Each palette layer has its own resolution, and a terrain can switch between a layered and a simple material mode.
- <strong>Residency by camera.</strong> Only what a camera can see stays loaded (tiles, layers, textures, instances); the rest is unloaded and loaded back with RAM and CPU budgets.
- <strong>Procedural and manual are both sources.</strong> The terrain editor and the procedural generators are tools of one framework, and each placement source can be switched on or off without losing its data.
- <strong>Regional GI.</strong> An edit invalidates only the region it touches, either dynamically or from precompiled data.
- <strong>1M instances</strong> are a goal of Phase 3, so GPU culling, LOD and impostors are in it. The goal is stated in real units (instances per hectare over kilometres of terrain), not as a raw count.
- <strong>Real metric units everywhere:</strong> centimetres, metres and kilometres. Brush radius and spacing are in metres, heights are stored to the centimetre, densities are per square metre or hectare, and terrains reach kilometres.
- <strong>Stable ids across resampling</strong> are an explicit migration: the overrides are remapped.
- <strong>Out of scope here:</strong> the partial update of the physics collider. The stroke pipeline emits dirty regions, so it can subscribe later. Tablet pressure is Phase 5; brush parameters carry a pressure hook (default 1) from the start.

## 3. Architecture

### 3.1 Brush core (C++, <code>terrain/edit/</code>)

- <strong>Stamp:</strong> a grey-scale image (64 to 256 px) with radius, rotation, falloff, spacing, strength and jitter (position, rotation, size, opacity).
- <strong>Stroke:</strong> stamps are laid along the path by spacing in metres, never by frame, so the result does not depend on the frame rate.
- <strong>Library:</strong> about 40 procedural brushes (soft and hard round, square, Perlin, Worley and ridged noise, cracks, strata, dunes, craters, terraces, cliffs), grey-scale images imported through the asset manager, <code>Name.brush</code> files (plain text: stamp, parameters, mode) and user presets.
- <strong>Operations:</strong> Raise and Lower, Smooth, Flatten (height, plane, under the cursor), Ramp, Terrace, Noise, Pinch and Bulge, Stamp (add, absolute, max, min), Clone, Smudge, thermal and hydraulic erosion as a brush.
- <strong>Protection mask</strong> (edit only where slope, height or a mask allows) and <strong>symmetry</strong> (mirror X and Z, radial).
- <strong>Pipeline:</strong> a stroke accumulates into dirty tiles; each dirty tile rebuilds only its mesh region, recomputes its masks and tells the GI and the collider. <strong>Undo</strong> stores before and after tiles, one step per stroke.

### 3.2 Material palette

- A palette holds up to <strong>64 layers</strong>; each tile lists only the layers it uses (at most 4 blended per texel), so only the layers of visible tiles are resident, which is what makes 64 affordable. Each references a PBR <code>.mat</code> (albedo, normal, ORM, tiling) through the asset manager. Stored as a <code>.terrainpalette</code> asset.
- <strong>Rendering:</strong> an index map and a weight map (4 layers blended per texel) over texture arrays grouped by size class; height blend, triplanar on steep ground, anti-tiling, tint and UV rotation per layer.
- <strong>Resolution per layer</strong> from 256 to 4096, compressed offline (BC7 and BC5) by <code>caf-pack</code>. The <strong>simple mode</strong> (one texture or colour, or the legacy 4 layers) is selectable per terrain and per quality level.
- <strong>Painting</strong> uses the brush core in the modes Paint, Erase, Replace, Smooth and Lock; <strong>auto-layering</strong> fills by rules on slope, height and masks, in the syntax of the biome table.

### 3.3 Placement sources and vegetation

- A <strong>source</strong> produces density or instances: painted (manual), procedural (rules and seed), an imported scatter plan, or a graph or script. Sources stack, and each can be enabled, disabled or blended.
- <strong>Stable ids:</strong> the id of an instance is a hash of source, cell (or stroke) and index. Overrides (moved, removed, scaled) are keyed by it and survive regenerating. Operations: <em>bake procedural into manual</em> and <em>re-derive</em>.
- <strong>No overlap:</strong> a global spatial grid with a footprint per species, priority and a minimum distance between species, applied while painting (reject) and in a deterministic resolve pass; it also respects scene objects.
- <strong>Species</strong> (the palette entry): a prefab, a mesh or a <code>.generator.nature</code> recipe with N baked variants, density, exclusion radius, scale range, slope, height and mask rules, alignment to the normal, sink, tint, priority, wind and LOD.
- <strong>Tools:</strong> Paint, Erase, Scale, Rotate, Tint, Replace species, Select and Move, Thin out, Reseed.

### 3.4 One edit reaches every instance, and the terrain adapts

- An instance keeps only <code>species, variant, seed, scale, yaw, tint</code> and references the species; it never copies a mesh.
- Editing a species opens its recipe in the Nature Generator; saving it re-bakes the variants (cached by content hash) and every instance updates. The same holds for a changed prefab, mesh or material. A per-instance override is kept minimal, and <em>detach to entity</em> is optional.
- <strong>Adaptive:</strong> curves over masks modulate size, colour and variant (wet is greener and larger, steep is smaller, altitude scales). Sculpting re-projects the instances; those that become invalid (slope, water, height) are hidden, and manual ones are not deleted.

### 3.5 Native terrain format

- <code>.terrain</code> (a <code>caf</code> asset type): regional tiles of heights (16 or 32 bit), per-layer weights, masks and vegetation tiles, with a version and a CRC per tile; it loads only the regions asked for.
- <code>caf-pack</code> reads a <code>.cterrain</code> (heights, 4-layer splat, masks) and writes the container. Lossless is checked by a round trip that compares heights, 8-bit weights and masks bit by bit. The legacy reader stays read-only.
- <strong>Real units and large worlds:</strong> heights are 16-bit quantised to 1 cm with a base offset per tile (655 m of range; taller tiles use 32 bit), positions are tile-local with integer tile coordinates, rendering is camera-relative, and a stable id is hashed from <em>integer-centimetre world coordinates</em>, not texel indices, so resampling the heightmap does not change it.
- The same tile grid serves undo, the mesh, the GI and the vegetation.

### 3.6 GI by region

- Every edit emits dirty regions on the tile grid, which feed Photon (it already caches per view).
- <strong>Dynamic:</strong> recompute only the dirty region. <strong>Precompiled:</strong> store the lighting per region in the <code>.terrain</code> tiles, mark it stale when the region is edited and re-bake it in the background. The mode is chosen per region or terrain.

### 3.7 Residency, budgets and 1M instances

- <strong>Residency by camera:</strong> tiles, layers, textures and instance buffers stay resident only for what any active camera (editor viewport, game camera, preview) can see, with hysteresis. Loading and unloading is asynchronous, prefetches along the camera path and has per-frame budgets for RAM, CPU and uploads. This follows the engine's existing optimisation options and appears in the Performance tab and the profiler.
- <strong>1M instances:</strong> instance buffers per chunk (about 32 bytes each, around 32 MB on the GPU), compute culling (frustum and occlusion), indirect draws, LOD plus an octahedral impostor baked per species and variant by <code>caf-pack</code>, shadows only for near LODs, wind in the vertex shader.
- <strong>Editing:</strong> while a stroke is in progress a lower-density proxy is drawn, with a cost ceiling per stroke that has to be measured.

### 3.8 Editor UI (Doppio)

- A <strong>Terrain Editor</strong> mode in the viewport with the tabs Sculpt, Paint, Foliage and Masks.
- A brush panel (grid of brushes with previews, sliders, falloff curve, spacing, jitter, symmetry), palette panels for materials and species (cards, search, favourites) and a brush decal projected on the terrain with a latency HUD.
- Shortcuts: <kbd>[</kbd> and <kbd>]</kbd> for the radius, <kbd>Ctrl</kbd> to invert, <kbd>Shift</kbd> to smooth.
- Project rules: panels compose components, every widget has a <code>UiId</code> and a catalogue entry, agents drive it through <code>Message</code> actions in <code>main/agent.rs</code>, headless flows cover each tool.

## 4. Phases

<table>
  <thead><tr><th>Phase</th><th>Delivers</th><th>Needs</th><th>Check</th></tr></thead>
  <tbody>
    <tr><td><strong>0. Base</strong></td><td>Stroke ABI, real-unit tile model (cm, m, km), dirty tiles and regions, incremental mesh rebuild, tile undo, brush decal, the <code>.terrain</code> container and the <code>caf-pack</code> converter</td><td>nothing</td><td>Golden test per stroke; bit-for-bit round trip of a legacy terrain</td></tr>
    <tr><td><strong>1. Sculpt</strong></td><td>Stamp, <code>.brush</code>, about 40 brushes, every mode, protection mask, symmetry, UI</td><td>0</td><td>Same stroke at 30, 60 and 144 fps; headless flows</td></tr>
    <tr><td><strong>2. Materials</strong></td><td>Palette with per-layer resolution, layered or simple mode, index and weight maps, painting, auto-layering, VRAM budget, residency</td><td>0</td><td>Reference render; an old project opens identical</td></tr>
    <tr><td><strong>3. Vegetation</strong></td><td>Placement sources (painted and procedural, switchable), stable ids, no overlap, GPU pipeline for 1M with LOD and impostors</td><td>0</td><td>Determinism by seed; 1M instances inside the frame budget</td></tr>
    <tr><td><strong>4. Recipes and adaptation</strong></td><td>Species from <code>.generator.nature</code>, edits that propagate, overrides, re-projection, variation by mask</td><td>3</td><td>Editing a recipe changes every instance; sculpting re-adapts</td></tr>
    <tr><td><strong>5. Polish</strong></td><td>Painted masks, roads and rivers by spline, precompiled regional GI, GPU brushes, tablet pressure, shareable presets, docs</td><td>1 to 4</td><td>Docs EN and PT, headless captures</td></tr>
  </tbody>
</table>

Phases 1, 2 and 3 can run in parallel after Phase 0, because they touch different files. The regional GI starts in Phase 0 (dirty regions) and completes in Phase 5.

<p><strong>Phase 0 status (2026-11-22).</strong> Done: the tile model in real units (<code>terrain/edit/TerrainTiles</code>: tiles of 64 cells that own disjoint vertices, dirty tiles and regions, integer-centimetre coordinates, 16-bit centimetre height tiles with an exact fallback); the stroke engine (<code>TerrainStroke</code>: stamps spaced in metres along the path, five modes, stamp images, falloff curves, rotation, a pressure hook, tile-by-tile undo records); the C ABI 25 (<code>caffeine_session_terrain_stroke_*</code>: begin, point, end, revert, reapply, with a local mesh rebuild per stroke point and one collision-mesh refresh per stroke) and its Rust wrapper. Verified by <code>tests/test_terrain_edit.cpp</code>, the C ABI tests and an engine-crate test: the same path gives the same terrain at any sampling rate, an undo is bit-exact, and a stroke on an 8 km terrain touches only a few tiles. Also done: the native <code>.terrain</code> container (<code>terrain/TerrainContainer</code>, a <code>caf</code> asset of type Terrain: a header, a tile directory and one CRC-checked record per tile with its heights, splat and mask rectangles; a reader that loads only the tiles asked for) and the legacy converter (<code>caf-pack --convert-terrain</code> and <code>convertLegacyTerrain</code>, read back bit for bit before it reports success; <code>TerrainCache</code> opens either format). Nothing is lost: a height tile is 16-bit only when decoding returns every float bit, otherwise it keeps its floats; splat weights are bytes only when exact, otherwise floats. Verified by <code>tests/test_terrain_container.cpp</code> (legacy round trip, single-tile loads, corrupted-tile CRC, wide tiles, 257 and 4097 vertices). Also done: the editor tells which terrains of a project are still <code>.cterrain</code> and <em>Scene &gt; Convert terrains to .terrain</em> (the <code>convert_terrains</code> agent action, C ABI 26) saves them natively, checked bit for bit, keeping the old files; new terrains save as <code>.terrain</code>. Regional GI: Photon sees a terrain as one object per tile with its own revision, so a stroke revoxelises only the tiles it touched (the changed region is a tight rectangle, and Photon merges the boxes of neighbouring terrain tiles). The brush cursor (C ABI 27, <code>terrain_raycast</code> and <code>terrain_brush_outline</code>, the <code>terrain_brush_cursor</code> agent action): the ring a brush makes on the relief, drawn as an overlay under the mouse. A golden test pins one terrain per mode, and a stamp costs about 0.05 ms whatever the terrain size. <strong>Phase 0 is complete</strong> (full report: <a href="terrain-editing-phase-0.md"><code>terrain-editing-phase-0.md</code></a>). Vegetation tiles in the container belong to Phase 3; the partial update of the physics collider stays out of scope.</p>

<p><strong>Phase 1 status (2026-11-24).</strong> Done: 16 brush modes (the five of Phase 0 plus Ramp, Terrace, Pinch, Bulge, Stamp absolute, keep higher and keep lower, Clone, Smudge, and thermal and hydraulic erosion as brushes), per-stamp jitter, symmetry (mirror X, Z, both, radial) and protection masks (slope, height, curvature or a stored mask); 42 procedural stamps and a library of 58 brushes; the <code>.brush</code> format (plain text, not JSON: the core has no JSON reader); C ABI 28 and its Rust wrappers; stroke steps in the editor's undo history; and the <strong>Terrain Brush</strong> tab with the mouse tool, the shortcuts <kbd>[</kbd> <kbd>]</kbd>, <kbd>Ctrl</kbd> and <kbd>Shift</kbd>, agent actions and a headless flow. Every mode undoes bit for bit and the same path gives the same terrain at any sampling rate. <strong>Phase 1 is complete</strong> (full report: <a href="terrain-editing-phase-1.md"><code>terrain-editing-phase-1.md</code></a>). Next: Phases 2 and 3 can start in parallel.</p>

<p><strong>Phase 2 status (2026-11-24).</strong> Done: a material palette of up to 64 layers (<code>.terrainpalette</code>), a layer map that names four layers and their weights at every texel (<code>.terrainlayers</code>), paint, erase, replace and smooth strokes on the sculpting brush's shape with exact undo, locked layers, auto-layering by slope, height, curvature and masks, a renderer that draws it from one array texture (only layers in use take a slice, per-layer tiling and rotation, a VRAM budget, rectangle uploads), scene format 12, C ABI 29 and the <strong>Terrain Paint</strong> tab with the mouse tool, agent actions and a headless flow. Checked by painting a terrain red and blue and counting the pixels. <strong>Phase 2 is complete</strong> except three roadmap items that are recorded as limits: offline BC7 and BC5 compression, residency by camera, and the simple mode per quality level (full report: <a href="terrain-editing-phase-2.md"><code>terrain-editing-phase-2.md</code></a>). Next: Phase 3 (vegetation).</p>

<p><strong>Phase 3 status (2026-11-24).</strong> Done: vegetation as terrain data (a species palette of up to 256, a procedural source that grows by itself from rules and a seed and a manual source, both stacking), stable ids with overrides that survive regenerating, nothing overlapping (priority and room), plants re-projected for free when the ground is sculpted and hidden, not deleted, when their rules fail, seven brush tools (Paint, Erase, Scale, Rotate, Tint, Replace, Thin out), bake, re-derive and reseed, the <code>.terrainveg</code> file, scene format 13, a renderer that draws one instanced call per chunk and species variant with frustum and distance culling and a build budget, C ABI 30 and the <strong>Terrain Vegetation</strong> tab with the mouse tool, agent actions and a headless flow. Checked by rendering plants and counting their pixels. <strong>Phase 3 is complete</strong> except the roadmap's GPU compute culling and indirect draws, LOD meshes and impostors, shadows from vegetation and the Select and Move tool, which are recorded as limits (full report: <a href="terrain-editing-phase-3.md"><code>terrain-editing-phase-3.md</code></a>). Next: Phase 4 (species from recipes).</p>

## 5. Risks and measurements

- <strong>VRAM and compatibility:</strong> texture-array limits on weaker cards. Layers are unloaded and loaded by camera residency with RAM and CPU budgets, and the simple mode is the safety net.
- <strong>Precision on kilometre terrains:</strong> tile-local positions and camera-relative rendering are needed from Phase 0; adding them later would touch every tile and every instance.
- <strong>Stable ids when resampling:</strong> ids come from integer-centimetre world coordinates, so a resample keeps them; resizing the terrain origin is an explicit migration that remaps the overrides.
- <strong>1M instances in the editor:</strong> real-time painting needs a cost ceiling per stroke. The low-density proxy is the answer, but it has to be measured.
- <strong>Migration:</strong> legacy <code>.cterrain</code> files must keep opening; the converter and its bit-for-bit test are part of Phase 0.
