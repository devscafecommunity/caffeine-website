# Terrain editing: Phase 4 report (species from recipes)

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Done</span>
  <span class="doc-badge">Doppio</span>
  <span>Last updated: <time datetime="2026-11-25">2026-11-25</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/en/docs/doppio/terrain-editing-phase-4.md"><code>terrain-editing-phase-4.md</code></a></span>
</div>

<p class="doc-lede">A species that comes from a <code>.generator.nature</code> recipe, and edits that reach every plant: the recipe is baked into several variants, each with a material per part, the editor bakes again by itself when the recipe file changes, and the ground can change a species' size and colour through its masks, so sculpting and painting masks re-adapt the plants. It stands on <a href="terrain-editing-phase-3.md">Phase 3</a>; the plan is in <a href="terrain-editing-roadmap.md"><code>terrain-editing-roadmap.md</code></a>. The C ABI is now 31.</p>

## 1. What Phase 4 delivered

<table>
  <thead><tr><th>Piece</th><th>Where</th><th>What it does</th></tr></thead>
  <tbody>
    <tr><td>Species data</td><td><code>terrain/vegetation/VegetationSpecies.*</code></td><td>A material per sub-mesh (<code>slot_material</code>), the recipe's content hash (<code>recipe_hash</code>) and adaptations by mask (<code>adapt scale</code>, <code>adapt tint</code>), in the species text with parse errors that name the line</td></tr>
    <tr><td>Adaptation</td><td><code>terrain/vegetation/TerrainVegetation.*</code>, <code>terrain/TerrainCache.cpp</code></td><td>A resolve reads the stored mask under each plant and scales or tints it between the mask's 0 and 1; nothing is stored per plant</td></tr>
    <tr><td>Renderer</td><td><code>render/GpuSceneRenderer.cpp</code></td><td>A species with several sub-meshes is drawn once per sub-mesh, each with its own material</td></tr>
    <tr><td>C ABI 31</td><td><code>capi/EngineAPI.*</code></td><td><code>CaffeineVegSpecies</code> carries <code>recipe_hash</code>, up to 8 slot materials and up to 4 adaptations (<code>CaffeineVegAdapt</code>)</td></tr>
    <tr><td>Recipe baking</td><td><code>uikit/vegetation_recipe.rs</code></td><td>Bakes a recipe into N variants (other seeds of the same graph), one OBJ each with the parts as sub-meshes, in a folder named by the recipe's content hash; a cached bake is reused</td></tr>
    <tr><td>Terrain Vegetation tab</td><td><code>uikit/panels/terrain_vegetation.rs</code>, <code>windows/main/terrainvegetation.rs</code></td><td>A <em>Recipe</em> card (file, number of variants, Bake) and a <em>How the ground changes it</em> card (size and colour terms by mask)</td></tr>
  </tbody>
</table>

## 2. A species from a recipe

- Setting a species' <em>Recipe</em> to a <code>.generator.nature</code> file of the project bakes it: the graph is evaluated for N seeds (1 to 8, default 4), each seed is one variant, and every part of the model becomes a sub-mesh of its variant's OBJ. The seed of variant <em>i</em> is a function of the species' uid and <em>i</em>, so a bake is reproducible.
- Each part gets its own <code>.mat</code> (the same materials the Nature Generator uses), stored as the species' <em>slot materials</em>; the renderer draws one call per sub-mesh and variant.
- The recipe file's content hash is kept in the species (<code>recipe_hash</code>). Baked files live in <code>Vegetation/&lt;hash&gt;/</code> under the project's nature models folder, so another recipe content is another folder and a bake already on disk is not made again.
- Baking is one undo step: the species' meshes, slot materials and hash change together, and undo puts the previous ones back. A recipe that does not exist or does not parse is reported in the tab's status line and the species keeps the meshes it had.

## 3. Edits that propagate

- Every plant of a species refers to the species by uid and draws whatever the species says now, so changing the species (its meshes, materials, scale range, tint) changes every plant at once; no plant is replaced and no id changes.
- The editor compares each baked species' <code>recipe_hash</code> with the recipe file's hash on the viewport tick, at most every 2 seconds. When the file changed (edited in the Nature Generator or by hand) it bakes again by itself, as one undo step; when nothing changed it does nothing and records no step.
- Changing the number of variants may change which variant a plant shows, never which plants exist.

## 4. The ground adapts the species

- A species has up to 4 <strong>adaptations</strong>. A <em>size</em> term multiplies the plant's scale by a value taken between <em>at 0</em> and <em>at 1</em> by a stored mask (slope, height, curvature or a painted mask) read under the plant; a <em>colour</em> term multiplies its tint the same way.
- It is applied when plants are resolved, not stored in them, so <strong>sculpting or painting a mask re-adapts the plants</strong> by itself (the chunks under the stroke are drawn again). The scale is kept between 0.05 and 50 times, and the base sinks with the adapted scale.
- Overrides stay on top: a plant scaled by hand is scaled by hand first and then adapted.

## 5. C ABI 31

<code>CAFFEINE_CAPI_VERSION</code> is 31. <code>CaffeineVegSpecies</code> gained <code>recipe_hash</code>, <code>slot_material_count</code> with <code>slot_materials[8][256]</code>, and <code>adapt_count</code> with <code>adapt[4]</code> (<code>CaffeineVegAdapt</code>: mask name, target size or colour, the two values). The palette calls of version 30 carry them; values past a field's capacity are kept from the existing species instead of being cut silently.

## 6. Agent actions

New: <code>terrain_vegetation_bake_recipe</code> (bake the selected species now, with a number of variants), <code>terrain_vegetation_sync_recipes</code> (bake the species whose recipe file changed) and <code>terrain_vegetation_adapt</code> (add or remove an adaptation). <code>terrain_vegetation_edit_species</code> accepts <code>recipe</code> and <code>recipe_variants</code>; the <code>terrain_vegetation</code> query lists the terrain's masks, the variant count and each species' recipe, hash, slot materials and adaptations.

## 7. Verification

- C++: <code>tests/test_terrain_vegetation.cpp</code> (34 cases, 3 new): adaptation by mask changes size and tint and follows the mask when it is edited; slot materials and the recipe hash round-trip through the species text and the file; the new text errors (missing numbers, a non-positive scale, an unknown kind). The C ABI case covers the new struct round trip and undo.
- Rust: an engine-crate test that <strong>renders</strong> a two-part model with a different material per part and counts the pixels of each colour, then adapts the species to the ground and counts again; four unit tests of <code>vegetation_recipe</code> (hash, seeds per variant, bake, cache reuse); app tests: a species baked from a recipe follows the recipe when the file changes, with the same plants before and after, one undo step per bake and no step when nothing changed; a missing recipe is said and keeps the meshes; adaptations are added, edited in one step per drag and removed with undo.

## 8. Decisions recorded

- The recipe is the source of truth of a species' look; the baked OBJ files are a cache named by content, never edited by hand.
- Adaptation is computed when plants are resolved, so it costs nothing in the file and cannot go stale when the ground changes.
- At most 8 slot materials and 4 adaptations per species keep the C struct a plain fixed-size record.

## 9. Known limits and what is next

- <strong>Variation of the variant chosen by a mask is not done</strong>: a mask changes a plant's size and tint, not which variant it shows. The roadmap item is recorded as a limit.
- The materials of a baked species are the ones <code>ensure_nature_material</code> makes for each part; a recipe whose parts have no material there is drawn with the species' single <em>material</em>.
- Only <code>.generator.nature</code> recipes are baked; trees' LOD meshes, shadows from vegetation and the Phase 3 renderer limits still stand.
- Next: Phase 5 (painted masks, roads and rivers, tablet pressure, precompiled GI).

## 10. Work log

- <strong>2026-11-25</strong>: species data (slot materials, recipe hash, adaptations), the adaptation in the resolve and the mask callback, the per-sub-mesh draws, C ABI 31 and its tests; the recipe baker and its cache; the recipe and adaptation cards, the automatic re-bake, the agent actions and these pages. Incidents: a species with no meshes places no plants, so the recipe test now starts from a species that has one; the agent's species JSON hit the <code>json!</code> macro recursion limit and moved to a helper function.
