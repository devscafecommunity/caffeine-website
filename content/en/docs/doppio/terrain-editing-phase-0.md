# Terrain editing: Phase 0 report

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Done</span>
  <span class="doc-badge">Doppio</span>
  <span>Last updated: <time datetime="2026-11-23">2026-11-23</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/en/docs/doppio/terrain-editing-phase-0.md"><code>terrain-editing-phase-0.md</code></a></span>
</div>

<p class="doc-lede">What the foundation of the terrain editor is, as built: the tile model, the stroke engine, the native <code>.terrain</code> container, regional GI and the brush cursor, with the C ABI that carries them, how each piece is verified, the decisions behind it and what is left. The plan itself is in <a href="terrain-editing-roadmap.md"><code>terrain-editing-roadmap.md</code></a>.</p>

## 1. What Phase 0 delivered

<table>
  <thead><tr><th>Piece</th><th>Where</th><th>What it does</th></tr></thead>
  <tbody>
    <tr><td>Tile model</td><td><code>src/caffeine/terrain/edit/TerrainTiles.*</code></td><td>Tiles of 64 cells that own disjoint vertices; dirty tiles and the changed region; integer-centimetre coordinates; 16-bit centimetre height tiles with an exact float fallback</td></tr>
    <tr><td>Stroke engine</td><td><code>terrain/edit/TerrainStroke.*</code></td><td>Stamps spaced in metres along a path; five modes; stamp images, falloff curves, rotation, a pressure hook; tile-by-tile undo records</td></tr>
    <tr><td>Native container</td><td><code>terrain/TerrainContainer.*</code></td><td>A <code>caf</code> asset of type Terrain: a tile directory and one CRC-checked record per tile; partial loading; lossless conversion of a legacy <code>.cterrain</code></td></tr>
    <tr><td>Converter</td><td><code>caf-pack --convert-terrain</code>, <code>convertLegacyTerrain</code></td><td>Reads a <code>.cterrain</code>, writes the <code>.terrain</code>, reads it back and compares bit for bit before it reports success</td></tr>
    <tr><td>Cache</td><td><code>terrain/TerrainCache.*</code></td><td><code>commitHeightEdit</code> (local mesh rebuild), per-tile revisions, <code>giTilesFor</code>, <code>dataFileIsLegacy</code>, <code>convertToNative</code>, <code>saveNativeTerrainFile</code></td></tr>
    <tr><td>Regional GI</td><td><code>render/GpuSceneRenderer.cpp</code></td><td>A terrain is one Photon object per tile with its own revision, so a stroke revoxelises only the tiles it touched</td></tr>
    <tr><td>C ABI</td><td><code>capi/EngineAPI.*</code></td><td>Versions 25 (strokes), 26 (data format, conversion) and 27 (terrain raycast, brush outline)</td></tr>
    <tr><td>Editor</td><td><code>doppio/crates/ui</code>, <code>doppio/crates/engine</code></td><td>Rust wrappers; the brush cursor overlay; <em>Scene &gt; Convert terrains to .terrain</em>; the <code>convert_terrains</code> and <code>terrain_brush_cursor</code> agent actions</td></tr>
  </tbody>
</table>

## 2. The tile model

- A terrain of <code>N</code> vertices has <code>ceil((N-1)/64)</code> tiles a side (257 is 4, 4097 is 64). A tile <em>owns</em> its vertices (the last tile of a row also owns the final one), so tiles never overlap; its <em>mesh region</em> is the owned vertices plus one on every side.
- A point is also named in <strong>integer centimetres from the corner</strong> (<code>vertexXCm</code>), the form a stable id is hashed from: resampling the heightmap does not change it, and a kilometre-wide terrain is addressed by tile first and a small offset after.
- <code>DirtyTiles</code> keeps the tiles an edit touched and the tight rectangle of vertices that really changed; the mesh and the GI grow that rectangle by one vertex themselves.
- <code>quantizeHeights</code> stores a tile as 16-bit offsets of 1 cm from a base (655 m of range); a tile that does not fit keeps its floats.

## 3. The stroke engine

- A stroke is a path of points. The brush is laid on it as stamps <strong>spaced a fixed number of metres apart</strong>, never one per frame: the same path gives the same terrain at 2 or 240 samples. Radius, spacing and heights are metres; positions are metres from the terrain's centre.
- Raise, lower and noise change the height by <em>metres per stamp</em>; smooth and flatten move a 0 to 1 share toward the average or the target. Smoothing reads a copy of the region, so the result does not depend on the order of vertices. Noise is deterministic for a seed.
- The first touch of a tile copies its heights; <code>finish</code> returns a <code>StrokeRecord</code> with before and after for the tiles that really changed. Undo and redo are bit-exact, and the record is a few tiles even on an 8 km terrain.

## 4. The native .terrain container

<table>
  <thead><tr><th>Part</th><th>Content</th></tr></thead>
  <tbody>
    <tr><td>Header (32 B)</td><td>caf magic <code>0xCAFECAFE</code>, type Terrain, CRC32 of the payload</td></tr>
    <tr><td>Metadata</td><td><code>TerrainFileMeta</code> (format version 1, resolution, extent in metres, maximum height), the mask directory, and the tile directory (offset, size and CRC32 of every tile)</td></tr>
    <tr><td>Payload</td><td>One record per tile, rows then columns, each 16-byte aligned: the heights, the splat weights of the splat texels the tile owns, and the same sub-rectangle of every stored mask</td></tr>
    <tr><td>Footer</td><td>CRC32 of the whole file</td></tr>
    <tr><td>Lossless rule</td><td>A height tile is 16-bit only when decoding returns every float bit for bit (so NaN, infinities, -0 and relief above 655 m stay as floats); splat weights are bytes only when every weight is exactly byte/255, otherwise four floats; masks are 8 bits already</td></tr>
    <tr><td>Reader</td><td><code>open</code> reads the header and directories; <code>loadTile</code>, <code>loadTilesInto</code> read only the tiles asked for and check each CRC; <code>verifyWholeFile</code> checks the footer; a failed load leaves the caller's maps untouched</td></tr>
    <tr><td>Opening old projects</td><td><code>loadTerrainAny</code> detects the format by signature (<code>CTRN</code> is legacy); a legacy terrain opens as it is and is flagged, and <code>nativeTerrainPath</code> gives the <code>.terrain</code> path to offer</td></tr>
  </tbody>
</table>

## 5. C ABI

<table>
  <thead><tr><th>Version</th><th>Functions</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td>25</td><td><code>caffeine_session_terrain_stroke_begin / _point / _end / _revert / _reapply</code></td><td>A stroke on a terrain entity: points in world space, a local mesh rebuild per point, one collision-mesh refresh per stroke, undo records within a 512 MB budget</td></tr>
    <tr><td>26</td><td><code>caffeine_session_terrain_data_legacy</code>, <code>caffeine_session_terrain_convert_native</code></td><td>Whether a terrain is still in the old format; save it as <code>.terrain</code>, checked bit for bit, and point the scene at it (the old file stays)</td></tr>
    <tr><td>27</td><td><code>caffeine_session_terrain_raycast</code>, <code>caffeine_session_terrain_brush_outline</code></td><td>Where a ray meets a terrain, and the ring a brush makes on the relief</td></tr>
  </tbody>
</table>

## 6. Regional GI

- Photon built one object for a terrain, so any edit revoxelised all of it, and a terrain made of chunks (the default) was not voxelised at all because it has no single mesh. A terrain is now cut into tiles; each tile has a coarse mesh and a revision that moves only when an edit touched it.
- The mesh step keeps the whole terrain within 400 000 triangles and cells of at least about a metre (the voxel volume resolves no more). The boxes of neighbouring terrain tiles are merged, because the voxeliser rebuilds a level whole when it gets more than eight boxes; boxes of ordinary objects are not merged, so a scene that changed wholesale still rebuilds whole and the light settles again.
- Not done yet: precompiled GI per region stored in the container. Phase 5.

## 7. Verification

- C++: <code>tests/test_terrain_edit.cpp</code> (tiles, strokes, golden fingerprints for the five modes, a per-stamp budget of about 0.03 to 0.05 ms that does not grow with the terrain, GI tiles, opening and converting a legacy terrain), <code>tests/test_terrain_container.cpp</code> (10 cases) and the C ABI cases in <code>tests/test_capi.cpp</code>. The whole suite: 1099 cases.
- Rust: the engine-crate test of a stroke and its undo; <code>photon_gi::a_terrain_stroke_revoxelises_only_the_tiles_it_touched</code> (16 objects, no whole rebuild, at most 8 boxes); <code>terrain_format</code> (an old project is reported, converted and reopened bit for bit); <code>terrain_cursor</code> (the ring follows the mouse and hugs the relief). The whole suite: 590 tests, clippy with and without the <code>agent</code> feature, <code>./scripts/check-rust-ui.sh</code>.

## 8. Decisions recorded

- Material layers: up to 64 per palette, 4 blended per texel, resolution per layer, a layered or a simple mode per terrain; only what a camera can see stays loaded.
- Vegetation: procedural and manual are both placement <em>sources</em>, switchable without losing data; the target is 1M instances in real units (per hectare), so GPU culling, LOD and impostors are in Phase 3.
- Real metric units everywhere (cm, m, km); stable ids come from integer-centimetre world coordinates; a legacy terrain converts without losing a bit; the partial update of the physics collider is out of scope; tablet pressure is Phase 5 (the stroke already carries a pressure and the brush a hook).

## 9. Known limits and what is next

- A conversion is a file-format migration, not an undoable edit; the engine marks the scene changed so that saving keeps it. <code>saveTerrainFile</code> with a <code>.terrain</code> path returns false on purpose (it lacks the extent and height scale); scenes use <code>saveNativeTerrainFile</code>.
- The brush cursor has no button yet: the agent action and the tests turn it on, and the Terrain Editor of Phase 1 will. A stroke point reaches the engine in world space through a float matrix, which will be revisited with camera-relative rendering for terrains far from the origin.
- Vegetation tiles and precompiled GI in the container belong to Phases 3 and 5. Next: Phase 1, the brush library (<code>.brush</code>, about 40 procedural brushes, every mode, protection mask, symmetry) and the Terrain Editor UI.

## 10. Work log

- <strong>2026-11-22</strong>: the plan and its decisions were written (<code>terrain-editing-roadmap.md</code>); the tile model, the stroke engine, C ABI 25 and the Rust wrapper were built. The session <em>Container .terrain and converter</em> built the container and the <code>caf-pack</code> converter in parallel, in files this session did not touch.
- <strong>2026-11-23</strong>: the golden and budget tests, regional GI, the legacy-terrain prompt and conversion (C ABI 26) and the brush cursor (C ABI 27) closed the phase. Incidents: a <code>git stash</code> in the website submodule was undone at once without conflicts; <code>/tmp</code> filled up twice and only old test artifacts were removed; merging every dirty Photon box broke the thin-wall GI test, which is why only terrain tiles are merged.
