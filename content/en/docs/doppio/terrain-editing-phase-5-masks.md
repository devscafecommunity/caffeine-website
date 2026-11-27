# Terrain editing: Phase 5.1 report (painted masks)

<div class="doc-meta">
  <span class="doc-badge doc-badge--beta">In progress</span>
  <span class="doc-badge">Doppio</span>
  <span>Last updated: <time datetime="2026-11-26">2026-11-26</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/en/docs/doppio/terrain-editing-phase-5-masks.md"><code>terrain-editing-phase-5-masks.md</code></a></span>
</div>

<p class="doc-lede">A stored terrain mask edited with the brush that sculpts and paints layers. A painted mask is an ordinary mask, so rules, auto-layering, brush protection and the size and colour adaptations of vegetation species read it, and the plants under a stroke are resolved again as it is painted.</p>

## 1. What it delivers

<table>
  <thead><tr><th>Piece</th><th>Where</th><th>What it does</th></tr></thead>
  <tbody>
    <tr><td>Mask brush</td><td><code>terrain/paint/TerrainMaskPaint.*</code></td><td>Stamps laid by spacing in metres with the shared brush (radius, falloff, stamp, jitter, symmetry, protection). Paint moves the mask toward a level, Erase toward 0, Smooth toward the neighbours.</td></tr>
    <tr><td>Whole-mask edits</td><td><code>createMask</code>, <code>editMask</code></td><td>Make (empty, a level, or a copy of slope, height, curvature or another mask), fill, invert, delete.</td></tr>
    <tr><td>Undo</td><td><code>MaskRecord</code></td><td>Blocks of 64 x 64 texels for a stroke, the whole mask for the other edits; exact and small however large the mask is.</td></tr>
    <tr><td>Vegetation</td><td><code>TerrainCache::commitMaskEdit</code></td><td>Only the chunks the edit reaches are resolved and drawn again.</td></tr>
    <tr><td>C ABI 33</td><td><code>capi/EngineAPI.*</code></td><td><code>caffeine_session_terrain_mask_paint_begin</code>, <code>_mask_create</code>, <code>_mask_edit</code></td></tr>
    <tr><td>Terrain Paint tab</td><td><code>uikit/panels/terrain_paint.rs</code>, <code>windows/main/terrainpaint.rs</code></td><td>A <em>Masks</em> card: the stored masks, make empty or a copy, fill, invert, delete, and a switch that makes the brush paint the selected mask instead of the layers.</td></tr>
  </tbody>
</table>

## 2. How it works

- A stroke computes in floats and writes the rounded byte, so a soft brush of low strength keeps its falloff instead of stepping whole levels. The same path gives the same mask at 30 and at 240 samples a second.
- A mask has a grid of its own (the terrain's by default), up to 16 per terrain, saved with the terrain file.
- Built-in masks (height, slope, curvature) are derived from the ground and cannot be painted or edited; copy one to paint over it.
- The Terrain Paint brush is the one used: its numbers, the Terrain Brush shape when asked for, Ctrl to invert and Shift to smooth. Layered painting does not need to be on.

## 3. C ABI 33

<code>CAFFEINE_CAPI_VERSION</code> is 33. Painting is a stroke like the others: <code>caffeine_session_terrain_stroke_point</code>, <code>_stroke_end</code>, <code>_stroke_revert</code> and <code>_stroke_reapply</code> work for it unchanged. Creating, filling, inverting and deleting are one undoable edit each (a record id comes back).

```c
CaffeineMaskBrush brush = {0};
brush.mode = CAFFEINE_MASK_PAINT;
brush.value = 1.0f;
caffeine_session_terrain_mask_create(session, terrain, "wet", 0, 0, 0.0f, NULL, &record, error, sizeof error);
caffeine_session_terrain_mask_paint_begin(session, terrain, &brush);
```

## 4. Agent actions

<code>terrain_mask_make</code>, <code>terrain_mask_select</code>, <code>terrain_mask_target</code>, <code>terrain_mask_value</code> and <code>terrain_mask_edit</code>. After <code>terrain_mask_target</code>, <code>terrain_paint_stroke</code> paints the mask along its points; the <code>terrain_paint</code> query lists the masks.

## 5. Verification

- C++: <code>tests/test_terrain_mask_paint.cpp</code> (4 cases: make and copy, paint, erase and smooth with exact undo, falloff in 8 bits independent of sampling, protection, symmetry and the whole-mask edits) and a C API case where a pine grows only on the painted ground, goes away on undo and the mask survives saving the scene.
- Rust: an engine-crate test of the new calls and four tests of the tab (make a mask without layers, a mouse drag is one stroke that undoes, an agent stroke, fill, invert and delete, and bad requests that say why).

## 6. Known limits and what is next

- Undoing a deletion puts the mask back at the end of the list, so the indices of <code>terrain_mask_at</code> may change.
- There is no headless UI flow for the card yet: the headless fixtures have no terrain entity, so the behaviour is covered by the app tests and the agent actions.
- Next in Phase 5: roads and rivers by spline, tablet pressure and presets, GPU brushes, precompiled regional GI.
