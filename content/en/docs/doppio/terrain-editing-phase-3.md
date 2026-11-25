# Terrain editing: Phase 3 report (vegetation)

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Done</span>
  <span class="doc-badge">Doppio</span>
  <span>Last updated: <time datetime="2026-11-24">2026-11-24</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/en/docs/doppio/terrain-editing-phase-3.md"><code>terrain-editing-phase-3.md</code></a></span>
</div>

<p class="doc-lede">Vegetation as terrain data, not entities, as built: a palette of species, two stacking sources (plants that grow by themselves from rules and a seed, and plants placed by hand), stable ids with edits that survive regenerating, nothing overlapping, brush tools, baking, a renderer that draws one instanced call per chunk and species variant, and the Terrain Vegetation tab, with the C ABI 30 that carries it. It stands on <a href="terrain-editing-phase-2.md">Phase 2</a>; the plan is in <a href="terrain-editing-roadmap.md"><code>terrain-editing-roadmap.md</code></a>.</p>

## 1. What Phase 3 delivered

<table>
  <thead><tr><th>Piece</th><th>Where</th><th>What it does</th></tr></thead>
  <tbody>
    <tr><td>Species</td><td><code>src/caffeine/terrain/vegetation/VegetationSpecies.*</code></td><td>Up to 256 species: variant meshes, material, density per hectare, room, priority, scale range, tilt, sink, tint, draw distance, rules; the text format</td></tr>
    <tr><td>Store</td><td><code>terrain/vegetation/TerrainVegetation.*</code></td><td>The procedural and manual sources, stable ids, overrides, conflict resolution, <code>resolveChunk</code>, the <code>.terrainveg</code> file</td></tr>
    <tr><td>Edits</td><td><code>terrain/vegetation/VegetationStroke.*</code></td><td>Seven brush tools on the sculpting brush's shape; bake, re-derive, reseed and palette edits; records that undo exactly</td></tr>
    <tr><td>Cache and scene</td><td><code>terrain/TerrainCache.*</code>, <code>scene/EditorSceneSerializer.cpp</code></td><td>The cache owns the store, builds the ground a resolve reads (heights, normals, rules over masks) and tracks the chunks the GPU has not seen; scene blob 13; saving writes the file next to the terrain</td></tr>
    <tr><td>Renderer</td><td><code>render/TerrainVegetationGpu.*</code>, <code>render/GpuSceneRenderer.cpp</code></td><td>One instance buffer per chunk and species variant, frustum and distance culling, a build budget per frame, drawn with the existing instanced pipeline</td></tr>
    <tr><td>C ABI</td><td><code>capi/EngineAPI.*</code></td><td>Version 30: vegetation on and off, the palette (read, apply), vegetation strokes, bake, re-derive, reseed, instances near a point</td></tr>
    <tr><td>Terrain Vegetation tab</td><td><code>uikit/panels/terrain_vegetation.rs</code>, <code>windows/main/terrainvegetation.rs</code></td><td>Species list, the selected species' settings, variants and rules, the brush, the procedural source</td></tr>
  </tbody>
</table>

## 2. Two sources that stack

- <strong>Procedural:</strong> every species with a density grows by itself. A chunk (32 m) is a pure function of the world seed, the chunk and the rules (<code>scatter/Scatter</code>), so any chunk can be made in any order, on any thread, and nothing is stored: the store holds only the palette, the seed and the edits.
- <strong>Manual:</strong> plants placed by the brush or by baking, stored one by one (37 bytes each in the file).
- Each species can switch its procedural source off without losing anything else (<em>Grows by itself</em>), and can be hidden (<em>Drawn</em>).
- <strong>Bake</strong> turns a species' grown plants into manual ones (same spots, same sizes, overrides applied) and switches its procedural source off, so what stands on the ground can be edited one by one. <strong>Re-derive</strong> removes the baked plants and switches the source back on. <strong>Reseed</strong> grows the procedural plants from another seed.

## 3. Stable ids and overrides

- A procedural id is a hash of the species' uid and the plant's position in integer centimetres; a manual id of a counter and the position. Resampling the heightmap changes neither.
- Editing a grown plant (erase, scale, rotate, tint, move) is an <strong>override</strong> keyed by that id; it survives regenerating, changing the species' look, and saving. Editing a manual plant changes it in place.
- A species keeps its plants by <code>uid</code>, not by position in the palette: removing or reordering species does not reassign ids.

## 4. Nothing overlaps

- Two plants conflict when they are closer than the sum of their radii (a species' <em>room</em> times the plant's scale). A higher priority wins; a manual plant wins a tie with a grown one.
- Painting rejects a spot taken by a plant of higher priority or by a manual one of the same priority; grown plants of lower or equal priority give way automatically when a manual one is placed (they come back if it is removed).
- The grown plants of one species keep their distance by the same rule (the scatter's conflict rule needs only a margin of one radius around a chunk, so chunks stay independent).
- Nothing stands off the terrain.

## 5. The terrain adapts

- Heights are never stored in the vegetation: a plant stands on the ground as it is, so <strong>sculpting re-projects the plants for free</strong> (the chunks under the stroke are drawn again).
- A species' rules (slope, height, curvature or a stored mask, each a trapezoid over 0 to 1) decide where it may stand. A plant whose spot no longer satisfies them is <strong>hidden, not deleted</strong>; a plant painted on purpose (<em>Only where the species' rules allow</em> off) is immune.
- <em>Lean to ground</em> blends the plant's up axis toward the terrain normal; <em>Sink</em> buries its base.

## 6. Brush tools

<table>
  <thead><tr><th>Tool</th><th>What a stamp does</th></tr></thead>
  <tbody>
    <tr><td>Paint</td><td>Places plants of the selected species: candidates per 100 m2, accepted by the brush's weight, rejected where something in the way has priority or the rules say no</td></tr>
    <tr><td>Erase</td><td>Removes plants under it (a manual plant is deleted, a grown one gets an override)</td></tr>
    <tr><td>Scale, Rotate, Tint</td><td>Change what is under it by the brush's weight</td></tr>
    <tr><td>Replace</td><td>Swaps one species for another; a grown plant becomes a manual one of the new species at the same spot and size</td></tr>
    <tr><td>Thin out</td><td>Removes a share of what is under it, evenly: each plant has a fixed rank, so thinning twice with the same share removes no more</td></tr>
  </tbody>
</table>

The brush is the one that sculpts and paints layers (falloff, stamp picture, jitter, symmetry, protection masks apply when <em>Shape from the Terrain Brush</em> is on). Stamps are laid by spacing in metres, so the same path gives the same plants at any sampling rate. One stroke is one undo step. <kbd>Ctrl</kbd> turns plant into erase and back; <kbd>[</kbd> and <kbd>]</kbd> resize the active brush.

## 7. Rendering

- A chunk's plants are grouped by species and variant; each group is one vertex buffer of model matrices (64 bytes a plant) drawn with one instanced call through the pipeline the renderer already had.
- Chunks are culled by frustum and by distance (a species' <em>Drawn to</em> distance), and at most <strong>6 chunks are built per frame</strong>, nearest first, so a view that suddenly sees a forest fills in over a few frames.
- An edit rebuilds only the chunks it touched (and their neighbours); a moved terrain rebuilds its own. The panel shows the GPU bytes.
- A species' material (<code>.mat</code>), alpha cut-out and wind come from the same code the entities use.

## 8. Files and the scene

<table>
  <thead><tr><th>File</th><th>Content</th></tr></thead>
  <tbody>
    <tr><td><code>Name.terrainveg</code></td><td>Binary: <code>TVEG</code>, a version, the seed, the species as text, the manual plants, the overrides, a CRC-32 of the whole. A damaged or truncated file is refused with a reason</td></tr>
  </tbody>
</table>

Saving the scene writes the file next to the terrain data and records its path in the terrain component (scene blob version 13); a missing or damaged file leaves the terrain with an empty palette instead of losing it. In-memory scene snapshots do not carry the vegetation: it is set aside and handed back to its terrain, so undoing other edits loses no plants.

## 9. Undo

Strokes, species edits, bake, re-derive and reseed are engine records, like sculpting strokes (the same revert and reapply calls). A run of edits of one species field (dragging a slider) folds into the first edit's record. Turning vegetation on or off is a scene step.

## 10. C ABI 30

<table>
  <thead><tr><th>Function</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>caffeine_session_terrain_vegetation_enable</code>, <code>_vegetation</code></td><td>On and off; counts (species, manual plants, overrides, seed, GPU bytes)</td></tr>
    <tr><td><code>caffeine_session_terrain_veg_species</code>, <code>_veg_species_apply</code></td><td>Read a species; replace the palette (by uid), with <code>merge_into</code> to fold a slider drag; the error names the line</td></tr>
    <tr><td><code>caffeine_session_terrain_veg_paint_begin</code></td><td>Opens a vegetation stroke; points, end, revert and reapply are the stroke calls of version 25</td></tr>
    <tr><td><code>caffeine_session_terrain_veg_bake</code>, <code>_veg_rederive</code>, <code>_veg_reseed</code></td><td>Whole-palette operations, undoable</td></tr>
    <tr><td><code>caffeine_session_terrain_veg_instances</code></td><td>The plants near a world point: id, species, variant, manual or grown, position, scale</td></tr>
  </tbody>
</table>

## 11. Agent actions

<code>show_terrain_vegetation</code>, <code>terrain_vegetation_active</code>, <code>terrain_vegetation_enable</code>, <code>terrain_vegetation_add_species</code>, <code>terrain_vegetation_select_species</code>, <code>terrain_vegetation_edit_species</code>, <code>terrain_vegetation_remove_species</code>, <code>terrain_vegetation_rule</code>, <code>terrain_vegetation_set_rule</code>, <code>terrain_vegetation_set</code>, <code>terrain_vegetation_reseed</code>, <code>terrain_vegetation_bake</code>, <code>terrain_vegetation_rederive</code> and <code>terrain_vegetation_stroke</code> (one stroke along world points, the same path as the mouse). The <code>terrain_vegetation</code> query reads the state and <code>terrain_vegetation_instances</code> the plants near a point. Widget ids start with <code>terrain_vegetation.</code> and are in the catalogue.

## 12. Verification and measurements

- C++: <code>tests/test_terrain_vegetation.cpp</code> (31 cases): the species text and its errors; 256 species and the removal of a species with its plants; a chunk is a pure function of the seed (same twice, any order); the density per hectare is what grows; a new seed grows another forest; rules; nothing overlaps; priority; ids are stable and sculpting keeps them; sink and tilt follow the ground; manual plants (add, move between chunks, remove, ids); a manual plant wins its spot and rules hide without deleting; overrides survive regenerating; every tool undoes and redoes bit for bit; the same path gives the same plants at any sampling rate; paint respects rules and priority; erase, scale, rotate, tint, replace and thin; bake, re-derive, reseed and species edits with undo; the file and its damage. A C ABI case covers species, painting, erasing, undo, bake, reseed and a scene save and load.
- Rust: an engine-crate test that <strong>renders</strong> a terrain with a green-tinted species and counts the pixels of that colour, erases the plants (they leave the picture), undoes (they come back), redoes and hides the species; <code>terrain_vegetation</code> app tests (the pane, vegetation on as one step, grown plants, planting by agent and by mouse, Ctrl to erase, a slider drag as one step, variants and rules, removing a species with undo, reseed, bake and re-derive, tool exclusivity, brush limits); panel unit tests. The headless flow <code>terrain-vegetation-panel.json</code> runs through the real CLI.
- <strong>Cost of generating:</strong> a lawn of about 92 000 plants (10 per m2 over 96 x 96 m) resolves in about 1.7 s, roughly 18 microseconds a plant, once per chunk until an edit changes it. The renderer then draws from the chunk's buffer. 1M plants cost about 18 s of generation spread over the chunks a camera reaches, and 64 MB of GPU buffers; the build budget keeps a frame from stalling.

## 13. Decisions recorded

- Vegetation is data of the terrain with its own file; a plant is 37 bytes in the file and 64 bytes in a GPU buffer, never an entity.
- Procedural plants are not stored: the seed, the rules and the edits are.
- Palette entries are identified by uid, not by index, in ids, seeds and instances.
- A plant is drawn with its species' tint; per-instance colour variation is kept in the data but is not drawn yet.

## 14. Known limits and what is next

- <strong>Not done from the roadmap:</strong> GPU compute culling and indirect draws, per-species LOD meshes and the octahedral impostors baked by <code>caf-pack</code>, shadows from vegetation, and the tools <em>Select and Move</em> (a move is an override in the data but has no tool). The 1M target is met in memory and generation, not in the draw path: culling is on the CPU by chunk.
- Species come from meshes of the project. The recipe field is kept for Phase 4, which bakes a <code>.generator.nature</code> into the variants and re-bakes them when it changes, so that editing a species reaches every plant.
- Other sources (an imported scatter plan, a graph, a script) are not wired; <code>scatterTerrain</code>'s entities are unchanged.
- Vegetation is not in planar reflections or in Photon's GI yet, and per-instance tint is not drawn.
- Next: Phase 4 (species from recipes and edits that propagate) and Phase 5 (painted masks, roads and rivers, tablet pressure, precompiled GI).

## 15. Work log

- <strong>2026-11-24</strong>: the species, the store (sources, ids, overrides, conflicts, the file), the brush and the whole-palette operations with tests; the cache, scene format 13 and the file; the per-chunk GPU buffers and their draws, checked by a rendering test; C ABI 30; the Rust wrappers; the Terrain Vegetation tab, the mouse tool, agent actions and these pages. Incidents: the procedural source did not know where the terrain ends (a query reached 10 000 plants for a 6.5 ha terrain), so a resolve now drops what stands off it; the test that expected a few milliseconds for a dense lawn measured 1.7 s, so the page states the real cost.
