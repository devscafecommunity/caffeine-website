# Terrain editing: Phase 5.2 report (roads and rivers)

<div class="doc-meta">
  <span class="doc-badge doc-badge--beta">In progress</span>
  <span class="doc-badge">Doppio</span>
  <span>Last updated: <time datetime="2026-11-27">2026-11-27</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/en/docs/doppio/terrain-editing-phase-5-paths.md"><code>terrain-editing-phase-5-paths.md</code></a></span>
</div>

<p class="doc-lede">A road or a river drawn as a spline over a terrain. The engine levels the ground along the path, paints a palette layer on it and writes a stored mask of where it runs, as one undo step. The Terrain Path tab draws it on the viewport and previews the cut and fill before anything changes.</p>

## 1. What it delivers

<table>
  <thead><tr><th>Piece</th><th>Where</th><th>What it does</th></tr></thead>
  <tbody>
    <tr><td>Spline</td><td><code>terrain/spline/TerrainSpline.*</code></td><td>A Catmull-Rom path through up to 256 points. A road levels the ground to a profile taken along the path, averaged over a window and limited to a steepest grade, so it cuts and fills hills. A river cuts a channel with a rounded bed that never rises from the source to the end. Both blend into the ground over a shoulder.</td></tr>
    <tr><td>Surface</td><td>layer and mask</td><td>A palette layer is painted on the corridor (layered painting must be on) and a stored mask is made when missing and set to 1 on the corridor, falling to 0 over the shoulder. A species rule on that mask keeps plants off the road.</td></tr>
    <tr><td>Undo</td><td>stroke record</td><td>One record for ground, layer and mask together; it works with the stroke revert and reapply calls.</td></tr>
    <tr><td>C ABI 34</td><td><code>capi/EngineAPI.*</code></td><td><code>caffeine_session_terrain_spline_apply</code> and <code>caffeine_session_terrain_spline_sample</code> (the preview, which changes nothing).</td></tr>
    <tr><td>Terrain Path tab</td><td><code>uikit/panels/terrain_path.rs</code>, <code>windows/main/terrainpath.rs</code></td><td>The drawing tool, type and presets, the point list, an elevation profile, and the Shape and Surface cards.</td></tr>
    <tr><td>Viewport overlay</td><td><code>uikit/components/path_overlay.rs</code></td><td>A translucent ribbon, the two edges, a dashed centre line, numbered handles and a ghost leg to the cursor.</td></tr>
  </tbody>
</table>

## 2. Drawing

<table>
  <thead><tr><th>Gesture</th><th>Effect</th></tr></thead>
  <tbody>
    <tr><td>Left click on the ground</td><td>Drops a control point (the height is found on the terrain)</td></tr>
    <tr><td>Drag a handle</td><td>Moves it; the camera does not orbit</td></tr>
    <tr><td>Right click a handle</td><td>Removes it</td></tr>
    <tr><td><kbd>Backspace</kbd></td><td>Removes the last point</td></tr>
    <tr><td><kbd>Enter</kbd></td><td>Applies the path (with two or more points)</td></tr>
    <tr><td><kbd>Esc</kbd></td><td>Starts over</td></tr>
  </tbody>
</table>

Every click asks the engine for a preview, so the ribbon, the elevation profile (ground against path) and the length, cut, fill and steepest grade (or a river's drop) follow the mouse. Only Apply changes the terrain.

## 3. Presets

<table>
  <thead><tr><th>Preset</th><th>Kind</th><th>Width</th><th>Shoulder</th><th>Depth</th><th>Smooth</th><th>Grade</th><th>Mask</th></tr></thead>
  <tbody>
    <tr><td>Footpath</td><td>Road</td><td>1.5 m</td><td>1.5 m</td><td>-</td><td>8 m</td><td>30%</td><td>path</td></tr>
    <tr><td>Dirt road</td><td>Road</td><td>4.5 m</td><td>3 m</td><td>-</td><td>25 m</td><td>15%</td><td>road</td></tr>
    <tr><td>Highway</td><td>Road</td><td>12 m</td><td>6 m</td><td>-</td><td>80 m</td><td>6%</td><td>road</td></tr>
    <tr><td>Creek</td><td>River</td><td>3 m</td><td>3 m</td><td>0.8 m</td><td>12 m</td><td>-</td><td>river</td></tr>
    <tr><td>River</td><td>River</td><td>12 m</td><td>8 m</td><td>2.5 m</td><td>40 m</td><td>-</td><td>river</td></tr>
  </tbody>
</table>

Dragging any number turns the preset back to custom. A point can carry its own width, which overrides the path's there.

## 4. C ABI 34

<code>CAFFEINE_CAPI_VERSION</code> is 34. Points are in world space in metres and the height is ignored. A call that cannot be applied returns <code>INVALID_ARGUMENT</code> with the reason and changes nothing: fewer than two points, none on the terrain, a bad number, a built-in mask name, a missing layer or layered painting off.

```c
CaffeineSplineDesc desc = {0};
desc.kind = CAFFEINE_SPLINE_ROAD;
desc.width_m = 4.5f; desc.shoulder_m = 3.0f; desc.smooth_m = 25.0f; desc.max_grade = 0.15f;
desc.layer = -1;
strcpy(desc.mask, "road");
CaffeineSplinePoint pts[2] = {{-40, 0, 0, 0}, {40, 0, 10, 0}};
caffeine_session_terrain_spline_apply(session, terrain, &desc, pts, 2, &record, &length, error, sizeof error);
```

## 5. Agent actions

<code>show_terrain_path</code>, <code>terrain_path_active</code>, <code>terrain_path_kind</code>, <code>terrain_path_preset</code>, <code>terrain_path_set</code>, <code>terrain_path_add_point</code>, <code>terrain_path_move_point</code>, <code>terrain_path_select_point</code>, <code>terrain_path_remove_point</code>, <code>terrain_path_reverse</code>, <code>terrain_path_clear</code> and <code>terrain_path_apply</code>. The <code>terrain_path</code> query returns the settings, the points, the engine preview and the profile.

## 6. Verification

- C++: <code>tests/test_terrain_spline.cpp</code> (4 cases: a road levelled and graded with the ground away from it untouched, layer and mask with exact undo, a river bed that never rises downstream, and bad requests that change nothing).
- Rust: harness tests of the tab (the tool takes the left button from the other tools, clicks preview the path, dragging and removing handles, Backspace, Esc and reverse, Apply and Enter as one undo step, a river with layer and mask, errors, and an agent drawing with world positions) and a headless flow, <code>terrain-path-panel.json</code>.

## 7. Known limits and what is next

- The headless fixtures have no terrain entity, so the flow covers the tab (types, presets, tool, messages) and not drawing on the viewport; clicking, dragging and applying are covered by the app tests.
- A river only cuts a channel: there is no water surface yet.
- Next in Phase 5: tablet pressure and presets, GPU brushes, precompiled regional GI.
