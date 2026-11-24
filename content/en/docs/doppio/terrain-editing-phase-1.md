# Terrain editing: Phase 1 report (sculpting)

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Done</span>
  <span class="doc-badge">Doppio</span>
  <span>Last updated: <time datetime="2026-11-24">2026-11-24</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/en/docs/doppio/terrain-editing-phase-1.md"><code>terrain-editing-phase-1.md</code></a></span>
</div>

<p class="doc-lede">Sculpting as built: 16 brush modes, a library of 58 brushes (42 of them procedural stamps), <code>.brush</code> files, symmetry, protection masks, jitter, the Terrain Brush tab and the mouse tool, with the C ABI 28 that carries them and how each piece is verified. It stands on <a href="terrain-editing-phase-0.md">Phase 0</a>; the plan is in <a href="terrain-editing-roadmap.md"><code>terrain-editing-roadmap.md</code></a>.</p>

## 1. What Phase 1 delivered

<table>
  <thead><tr><th>Piece</th><th>Where</th><th>What it does</th></tr></thead>
  <tbody>
    <tr><td>Procedural stamps</td><td><code>src/caffeine/terrain/edit/BrushStamps.*</code></td><td>42 grey-scale stamps generated from arithmetic only (no libraries, the same on every machine): Basic 8, Noise 8, Rock 7, Dunes 4, Craters 5, Terraces 3, Shapes 7</td></tr>
    <tr><td>Stroke engine</td><td><code>terrain/edit/TerrainStroke.*</code></td><td>Ten new modes, per-stamp jitter, symmetry, protection masks (Phase 0's five modes keep their golden results bit for bit)</td></tr>
    <tr><td>Brush as a document</td><td><code>terrain/edit/BrushPreset.*</code></td><td><code>BrushPreset</code>, the <code>.brush</code> text format (read and write), image stamps through the asset manager, and the built-in library of 58 brushes</td></tr>
    <tr><td>C ABI</td><td><code>capi/EngineAPI.*</code></td><td>Version 28: the library, parse and format, a stamp preview, and a stroke begun from a whole preset</td></tr>
    <tr><td>Rust wrappers</td><td><code>doppio/crates/engine</code></td><td><code>BrushMode</code> (16), <code>Falloff</code>, <code>SymmetryKind</code>, <code>BrushPreset</code>, <code>builtin_brushes</code>, <code>parse_brush</code>, <code>format_brush</code>, <code>brush_stamp_image</code>, <code>terrain_stroke_begin_preset</code></td></tr>
    <tr><td>Terrain Brush tab</td><td><code>uikit/panels/terrain_brush.rs</code>, <code>uikit/components/brush_card.rs</code></td><td>Library grid with previews, search and category chips, the brush's settings, variation, symmetry, protection and the <code>.brush</code> file</td></tr>
    <tr><td>Sculpting tool</td><td><code>windows/main/terraineditor.rs</code></td><td>Left press on the terrain starts a stroke, moves extend it, release closes it as one undo step</td></tr>
    <tr><td>Undo</td><td><code>history.rs</code></td><td>Stroke steps: terrain heights are not in the scene snapshot, so a step carries the engine's stroke record and undo reverts only that record</td></tr>
  </tbody>
</table>

## 2. Modes

<table>
  <thead><tr><th>Mode</th><th>What it does</th><th>Settings it uses</th></tr></thead>
  <tbody>
    <tr><td>Raise, Lower</td><td>Add or take away metres of height per stamp</td><td>strength</td></tr>
    <tr><td>Smooth, Flatten</td><td>Move a share toward the local average, or toward a height (the one under the first stamp when it is negative)</td><td>strength, flatten height</td></tr>
    <tr><td>Noise</td><td>Deterministic noise for the seed</td><td>strength, seed</td></tr>
    <tr><td>Ramp</td><td>Grades a straight slope from where the stroke began to the cursor</td><td>strength</td></tr>
    <tr><td>Terrace</td><td>Smoothed steps of a given height</td><td>step height</td></tr>
    <tr><td>Pinch, Bulge</td><td>Pull the ground toward the stamp's centre, or push it away</td><td>strength</td></tr>
    <tr><td>Stamp (absolute), (keep higher), (keep lower)</td><td>Press the stamp's relief into the ground: set it, only raise to it, only lower to it. Repeated keep-higher builds on the new ground</td><td>strength, signed stamp</td></tr>
    <tr><td>Clone</td><td>Copies the relief found at an offset from the stamp</td><td>source X and Z</td></tr>
    <tr><td>Smudge</td><td>Drags the ground along the direction of the stroke</td><td>strength</td></tr>
    <tr><td>Erode (thermal)</td><td>Slides material down slopes steeper than the talus angle; the volume is conserved</td><td>talus angle, passes</td></tr>
    <tr><td>Erode (hydraulic)</td><td>Droplets that carve and deposit, deterministic for the seed</td><td>droplets</td></tr>
  </tbody>
</table>

The panel shows a number only for the modes that use it, so a raise brush does not offer a talus angle.

## 3. The library

- <strong>42 stamp brushes</strong>, each a procedural stamp with the radius, strength and spacing that suit it. A <em>signed</em> stamp (craters, valleys, river beds) treats mid grey as neutral: lighter raises, darker lowers, which is how a crater gets a raised rim and a bowl.
- <strong>16 tools</strong>, one for every mode, with sensible defaults (Raise, Lower, Smooth, Flatten, Noise, Ramp, Terrace, Pinch, Bulge, Stamp absolute, Stamp max, Stamp min, Clone, Smudge, Thermal erosion, Hydraulic erosion).
- <strong>Your own</strong>: every <code>.brush</code> file of the project's <code>Brushes</code> folder joins the library under <em>Custom</em>. <em>Save .brush</em> writes the working brush there; a file that cannot be read is reported with its line and does not stop the others.
- Choosing a brush <em>copies</em> it into the working brush. Edits change the copy only; <em>Revert</em> puts the library's version back.

## 4. Variation, symmetry and protection

- <strong>Variation</strong> per stamp, deterministic for the seed: scatter (a share of the radius), turn (degrees either way), size and strength.
- <strong>Symmetry</strong> about a centre in metres from the terrain's centre: mirror X, mirror Z, both, or radial with 2 to 16 copies. A stamp that falls on the axis is laid once, not twice.
- <strong>Protection</strong>: up to four terms. Each names a mask (<code>slope</code>, <code>height</code>, <code>curvature</code>, or a stored mask by name in the file) and a trapezoid of four numbers (0 to 1); the brush acts only where the mask is inside it and fades across the edges. A mask that does not exist protects everything. All weights are computed before any height changes, so the result does not depend on the order of vertices.

## 5. The .brush file

A <code>.brush</code> is plain text, one <code>key value</code> per line (the roadmap said JSON; the core has no JSON reader, and a line format diffs and merges well). <code>#</code> starts a comment and unknown keys are skipped, so an old build opens a newer file.

```
# A crater with a raised rim, scattered a little
name My crater
category Craters
mode raise
radius 14
strength 3
stamp procedural crater_simple 128
signed 1
jitter 0.1 15 0.1 0
symmetry none 4 0 0
protect slope 0 0 0.3 0.4
```

Keys: <code>name</code>, <code>category</code>, <code>mode</code>, <code>radius</code>, <code>strength</code>, <code>spacing</code>, <code>falloff</code>, <code>rotation</code>, <code>target_height</code>, <code>seed</code>, <code>stamp</code> (<code>none</code>, <code>procedural id [size]</code> or <code>image path [size]</code>), <code>signed</code>, <code>step</code>, <code>talus</code>, <code>iterations</code>, <code>droplets</code>, <code>offset</code>, <code>jitter</code> (position, rotation, size, opacity), <code>symmetry</code> (kind, count, centre X, centre Z), <code>pressure</code> and <code>protect</code> (mask and four numbers, repeatable). A picture stamp is a project path read through the asset manager and resampled to grey.

## 6. The Terrain Brush tab

<table>
  <thead><tr><th>Control</th><th>What it does</th></tr></thead>
  <tbody>
    <tr><td>View &gt; Terrain Brush</td><td>Brings the tab to the front (it sits with the Inspector) and loads the library</td></tr>
    <tr><td>Brush on</td><td>Turns the tool on: the ring follows the mouse over the terrain and a left press sculpts instead of orbiting. Right and middle buttons still pan</td></tr>
    <tr><td>Search and category chips</td><td>Filter the grid by name, category or mode</td></tr>
    <tr><td>Brush cards</td><td>One click selects a brush; the picture is its stamp, or the falloff curve for a tool</td></tr>
    <tr><td>Brush, Variation, Symmetry, Protection</td><td>The working brush's settings</td></tr>
    <tr><td>Brush file</td><td>Name, <em>Save .brush</em>, <em>Revert</em>, <em>Reload folder</em></td></tr>
  </tbody>
</table>

<p>Shortcuts while the tool is on: <kbd>[</kbd> and <kbd>]</kbd> shrink and grow the radius by 15%, <kbd>Ctrl</kbd> inverts (raise becomes lower, pinch becomes bulge, keep-higher becomes keep-lower), <kbd>Shift</kbd> smooths with the same radius and strength. One stroke is one undo step, whatever its length.</p>

## 7. C ABI 28

<table>
  <thead><tr><th>Function</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>caffeine_terrain_brush_count</code>, <code>caffeine_terrain_brush_at</code></td><td>The built-in library, one <code>CaffeineBrushPreset</code> per brush</td></tr>
    <tr><td><code>caffeine_terrain_brush_stamp</code></td><td>The grey image of a procedural stamp, for a preview</td></tr>
    <tr><td><code>caffeine_terrain_brush_parse</code>, <code>caffeine_terrain_brush_format</code></td><td>Read and write the <code>.brush</code> text; a parse error names the line</td></tr>
    <tr><td><code>caffeine_session_terrain_stroke_begin_preset</code></td><td>Begins a stroke from a whole preset: modes 5 to 15, jitter, symmetry, up to <code>CAFFEINE_BRUSH_PROTECT_MAX</code> (4) protection terms against the terrain's stored masks, picture stamps through the session's asset manager</td></tr>
  </tbody>
</table>

The stroke functions of version 25 (<code>_point</code>, <code>_end</code>, <code>_revert</code>, <code>_reapply</code>) are unchanged; <code>_begin</code> accepts modes 0 to 15.

## 8. Agent actions

Everything the mouse does is also an action that returns a <code>Message</code>, so an agent and a headless flow can drive the tool: <code>show_terrain_brush</code>, <code>terrain_brush_active</code>, <code>terrain_brush_select</code> (by name or index), <code>terrain_brush_set</code> (a setting by key, or <code>mode</code>, <code>falloff</code>, <code>symmetry</code>, <code>signed</code>, <code>name</code>), <code>terrain_brush_protect</code>, <code>terrain_brush_search</code>, <code>terrain_brush_save</code> and <code>terrain_brush_stroke</code> (one stroke along world points, the same path as the mouse). The <code>terrain_brush</code> query reads the library, the working brush, its protection terms, the point under the mouse and the status line. Widget ids start with <code>terrain_brush.</code> and are in the catalogue.

## 9. Verification

- C++: <code>tests/test_terrain_brushes.cpp</code> (24 cases): the library has 42 unique stamps; stamps stay in range, are deterministic for the seed and are fast to generate; every new mode behaves as described above; thermal erosion conserves volume; hydraulic erosion is deterministic and costs under 12 ms a stamp; mirror, both and radial symmetry; protection by slope, height band, unknown mask and stored mask; <strong>every mode undoes bit for bit and repeats exactly</strong>; the same path gives the same terrain at any sampling rate; the <code>.brush</code> round trip, errors with line numbers and image stamps. A C ABI case covers the library, text, preview, a stroke from a preset and its undo.
- Rust: <code>history</code> (stroke steps interleave with scene edits in order), the panel's table of numbers (every number round trips and stays in range, each has a catalogued id), the editor module (thumbnails, file names, modifiers, filtering), and the <code>terrain_editor</code> app tests with the real engine: a mouse drag over the terrain makes one step that undoes and redoes bit for bit and does not orbit the camera; an agent stroke equals the mouse; stroke, entity, stroke undo in the right order; modifiers and radius keys; protection edits; saving and reloading a <code>.brush</code>; a dropped record is reported. The headless flow <code>terrain-brush-panel.json</code> checks the controls through the real CLI.

## 10. Decisions recorded

- Stamps are procedural so a build needs no image files and the library is identical everywhere; picture stamps are for the user's own brushes.
- Undo of a stroke reverts the engine's record, not a scene snapshot, because terrain heights live in the height cache. The stroke records are kept within a budget (512 MB); a step older than that reports an error instead of failing silently.
- Phase 0's five modes are pinned by golden tests and kept bit for bit; the new modes are pinned by behavioural tests.

## 11. Known limits and what is next

- The tab has no picker for a picture stamp yet (write <code>stamp image path</code> in the file); a tool's preview is its falloff curve, and the ring shows size, not the stamp's shape.
- Ramp needs a drag (the slope runs from the first stamp to the cursor); with a single click it does nothing.
- Tablet pressure is wired in the stroke (<code>pressure</code> in the brush) but the mouse sends 1; it arrives in Phase 5.
- Next: Phases 2 (material palette and painting) and 3 (vegetation) can run in parallel, because they touch different files.

## 12. Work log

- <strong>2026-11-23</strong>: the stamp library, the ten new modes, jitter, symmetry and protection in the stroke engine; the order-dependence of protection (masks read the ground a stamp had already changed) was found by a test and fixed by computing every weight before any height changes; the <code>.brush</code> format and C ABI 28.
- <strong>2026-11-24</strong>: Rust wrappers, stroke steps in the history, the Terrain Brush tab, the mouse tool, shortcuts, agent actions, tests and these pages.
