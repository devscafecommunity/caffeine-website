# World Composer: build a prefab world from generator recipes

<div class="doc-meta">
  <span class="doc-badge doc-badge--reference">Design</span>
  <span class="doc-badge">Doppio</span>
  <span>Last updated: <time datetime="2026-11-23">2026-11-23</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/content/en/docs/doppio/world-composition.md"><code>world-composition.md</code></a></span>
</div>

<p class="doc-lede">One file that says <em>what the world is made of</em>: a terrain, the trees, rocks and grass
that grow on it, the rivers and lakes that cut through it, and the materials that dress it. You choose the
composition; the system builds the world, and every plant adapts to the place where it stands because its
randomness comes from a hash of its coordinates. It is a <strong>complement to the Terrain Generator</strong>,
not a replacement: the terrain stays a graph, the composition decides what lives on it.</p>

> **Status: design, nothing of the composer itself is built.** The pieces it stands on (recipes, hash, masks,
> biome table, scatter) mostly exist on the engine's `main`; this page names them and lists what is missing.
> It replaces the "target architecture" and "World tab" parts of
> [`photoreal-world-roadmap.md`](photoreal-world-roadmap.md), which stays as the validation of the idea and the
> engine and rendering phases.

## 1. The idea in one picture

```text
Valley.generator.world                         ← the composition (one file, you edit it)
  seed 1234, generator_version 2
  terrain   Terrain/Alpine.generator.terrain   ← height + masks (slope, wetness, flow, ...)
  water     Water/River.generator.water        ← follows the terrain's flow mask
            Water/Lake.generator.water         ← fills basins under a level
  classes   (what grows where, in priority order)
    boulder  Nature/MossRock.generator.nature   where slope > 0.3
    oak      Nature/OakTree.generator.nature    where gentle, dry, near water
    grass    Nature/LowerGrass.generator.nature where flat, not rock
  materials Materials/Moss.generator.material   ground layers, rock moss, ...
        │
        ▼  build (deterministic)
  placement per cell:  sub-seed = hash(world seed, class, cell x, cell z)
        │                → variant, yaw, scale, tint, lean — all from that one number
        ▼
  prefab world: terrain + water + instances, always identical for the same inputs
```

Three properties define it:

1. **Composition, not generation.** The user picks parts (`.generator.*` recipes) and rules; nothing is random
   unless a seed says so. Open the same file tomorrow, get the same world.
2. **Everything in one place.** Terrain, nature, water, materials and textures are listed in one file and one
   tab, instead of five tools that each place their own result.
3. **Adapts to position.** A tree is not a copy of a model dropped at (x, z). Its variant, size, lean and tint
   derive from the hash of its cell *and* from what the terrain is there (slope, height, wetness, distance to
   water). The same oak recipe looks different on a dry ridge and on a wet bank.

It is **not** an open-world streamer (that is the runtime path of the world roadmap). The composer builds a
bounded, authored world. It is designed so that the same build function can later run per chunk for streaming.

## 2. What already exists

Verified against the engine's `main` (C ABI version 27).

| Piece | Where | State |
|---|---|---|
| Recipe files, one per generator | `Oak.generator.nature`, `Lake.generator.water`, ... (`uikit/recipe.rs`, [`generator-recipes.md`](generator-recipes.md)) | done; `generator_version` in every one |
| Recipe resolver and variants | `uikit/recipe_ref.rs`: `nature_variants`, `bake_nature_variant(recipe, seed, quality, cache)` | done, cache keyed by graph + version + seed + quality |
| Integer hash | `core/Hash.hpp`: SplitMix64 `deriveSeed(parent, salt, x, z)`, `toUnit`; Rust twin in `recipe_ref.rs`; golden tests | done |
| Terrain masks | C ABI v15: `height`, `slope`, `curvature` (engine), `flow`, `wetness`, `wear`, `deposit` (graph) | done |
| Biome table | `terrain/TerrainBiome`: `base x` product of trapezoids over masks, plain text | done |
| Scatter core | `src/caffeine/scatter`: jittered grid, priority, exclusion radius, cell ownership, chunk-independent result | done |
| Scatter on a terrain | C ABI v16, `Scatter/default.scatter`, **Scene > Scatter on Terrain**, composite classes (`part mesh ...`) | done, one entity per instance |
| Nature output for scattering | vertex colour, flutter weight, material slots per submesh, per-instance tint and scale range | done |
| Rendering of many instances | Micromesh cluster LOD for opaque parts, wind, leaf translucency | partial (no impostors, no per-chunk buffers) |
| Water | surface and `water_height`, Gerstner waves on the GPU | done as a separate placement |
| Prefabs | `.prefab` entity tree that remembers its source recipe (`uikit/prefab_file.rs`) | done |

So the work is the **layer that connects them**, which the roadmap called "the world layer".

## 3. The composition file

`<Name>.generator.world`, a new recipe kind in the same family, so double-clicking it reopens the Composer
and caf-pack skips it as an editor-only source (add `world` to `Registry::isEditorOnly`). JSON, like the others;
the composer owns its graph text.

```json
{
  "format": "caffeine-generator", "version": 1, "kind": "world",
  "name": "Valley", "generator_version": 2,
  "graph": {
    "seed": 1234,
    "terrain": { "ref": "Terrain/Alpine.generator.terrain", "size_m": [1024, 1024] },
    "water": [
      { "ref": "Water/River.generator.water", "follow": "flow",    "min": 0.8 },
      { "ref": "Water/Lake.generator.water",  "fill": "basins",   "level": 0.18 }
    ],
    "materials": [
      { "slot": "terrain.layer0", "ref": "Materials/Moss.generator.material" }
    ],
    "classes": [
      { "id": "boulder", "ref": "Nature/MossRock.generator.nature", "variants": 6,
        "priority": 30, "cell_m": 16, "radius_m": 2.2, "density": 0.9,
        "scale": [0.7, 1.6], "tilt": 0.8, "sink": 0.3,
        "where": { "slope": [0.30, 0.45, 1.00, 1.00] },
        "adapt": {} },
      { "id": "oak", "ref": "Nature/OakTree.generator.nature", "variants": 8,
        "priority": 20, "cell_m": 9, "radius_m": 3.0, "density": 0.8,
        "scale": [0.8, 1.4], "tilt": 0.1, "tint": 0.1,
        "where": { "slope": [0, 0, 0.15, 0.35], "wetness": [0.2, 0.4, 0.8, 1.0] },
        "adapt": { "size_from": "wetness", "lean_from": "slope" } }
    ],
    "overrides": []
  }
}
```

Rules for the file:

- **References are project paths to recipes**, never to baked OBJs; the Composer re-runs recipes, so editing an
  oak recipe changes every oak. A missing or wrong-kind reference is an error in the status bar and nothing is
  built (the same refusal the recipe slots already use).
- **`where` is the existing biome syntax** (trapezoids over masks), so the biome table, the `.scatter` plan and the
  composition share one grammar. A `.scatter` file becomes a *view* of the `classes` list, not a second format.
- **Everything has a version.** `generator_version` at the top; the build records the versions of every recipe it
  used, so an old world keeps its old behaviour until it is re-baked on purpose.
- **`overrides`** is the sparse edit layer (section 7), kept in the file so determinism survives hand edits.

## 4. Adapting to position

Two separate mechanisms; keep them apart because they cost differently.

### 4.1 Hash of the coordinates (cheap, exists)

For each class, placement runs on a global jittered grid. For a cell `(cx, cz)`:

```text
cell_seed = deriveSeed(world_seed, class_salt, cx, cz)        // integer, platform independent
variant   = floor(toUnit(deriveSeed(cell_seed, 1, 0, 0)) * N)
yaw       = toUnit(deriveSeed(cell_seed, 2, 0, 0)) * 360
scale     = lerp(min, max, toUnit(deriveSeed(cell_seed, 3, 0, 0)))
tint      = jitter(toUnit(deriveSeed(cell_seed, 4, 0, 0)))
```

The result depends only on seed, composition and terrain, never on load order or chunk size, so two halves of a
region add up to the whole (already tested in the scatter core). `class_salt` is derived from the class `id`, not
its position in the list, so reordering classes does not move every tree.

### 4.2 Ground context (new)

Hash alone gives variety, not adaptation. The Composer also samples the terrain at the instance position and
feeds a small **context** to the class:

| Context | From | Possible uses |
|---|---|---|
| `slope`, `normal` | engine | lean, root flare depth, sink |
| `height_band` | height mask | stunted trees near the summit |
| `wetness`, `flow` | masks | larger, denser crown near water; moss tint |
| `water_distance` | water layer (new mask) | reeds only at the bank, willows near it |
| `neighbours` | scatter result | crowding: a tree with close neighbours grows taller and thinner |

`adapt` maps a context value onto a parameter the **class** exposes. v1 only touches the instance (scale, lean,
tint, wetness, snow: the run-time modifiers of CAPI v10 already exist). v2 lets it change the **bake**: the context
becomes inputs of the Nature graph, so a tree is grown for its place. That needs *exposed parameters* on
`generator.nature` (a graph says "this value can be driven"); until then, adaptation stays on the instance and the
variant pool.

### 4.3 Pool versus unique bake

A bake per tree would be exact and far too slow. The Composer therefore keeps a **variant pool** per class (N baked
variants, cached as today) and the hash picks one, then deforms and tints it. A class may be marked
`"unique": true` for hero objects (a few trees near the player's start) and baked per position. Default is the pool.

## 5. Build pipeline

One deterministic function, `build(composition, region) -> WorldPart`, in the core so Doppio, the runtime and the
headless driver run the same code:

```text
1. resolve     every ref -> recipe (kind and version checked); fail with a list, build nothing
2. terrain     bake height + masks (cached by recipe hash)
3. water       derive bodies from flow/level, write water_distance mask, optionally carve the bed
4. materials   splat and layer materials from the same masks
5. classes     for each class in priority order, cells in a fixed order:
                 density(masks) -> accept -> exclusion vs already placed -> conform to height/normal -> hash fields
6. overrides   apply the edit layer (remove, move, pin)
7. output      instance lists per class + terrain + water + material bindings
```

Notes:

- **Priority order is the rule that stops a tree growing through a rock**: rocks first, then trees, then bushes,
  then grass, each with its exclusion radius. Solved at placement, not at mesh time.
- **Water before scatter** so `water_distance` exists. A river carved into the terrain changes `height`, `slope`
  and `wetness`; so carving runs *before* the masks are read by the classes, and the cache key includes it.
- **Region**: the function takes a rectangle, as `scatterTerrain` does, so streaming later is the same call per chunk.
- **Output is data, not entities.** Small builds can spawn entities (as Scatter does today). Large ones write an
  instance buffer file next to the composition and draw it instanced; the per-entity path is the thing that makes
  thousands of instances slow to edit.

### Where the result goes

| Output | What it is | When |
|---|---|---|
| Live scene | holder entity `World <name>` with children | editing, small worlds |
| `World/<name>.prefab` | the saved tree, remembers its `.generator.world` | place the same world in other scenes |
| Instance bake (`.cinst`, new) | per-class instance buffers + hashes | big worlds, runtime draw |

All three come from the same `WorldPart`; the recipe stays the source of truth.

## 6. The Composer tab

A **World** tab in the Inspector pane group (roadmap phase 6), reusing components only:

- **Library** (left): the project's `generator.*` recipes by kind (terrain, nature, water, material, texture),
  drag onto the composition.
- **Composition** (centre): the layer list; a class row shows ref, variants, priority and a small preview of
  its density over the terrain masks.
- **Rules** (right): the `where` terms as sliders over a mask histogram; `adapt` mappings; seed field with a
  *reseed* button (a derived seed, undoable).
- **Preview**: a coarse build (low resolution masks, billboards) that updates as you edit, built off the UI thread.
- **Build**: full build; one undo step; reports instances per class, time, and cache hits in the status bar.

Project rules apply: every widget gets a `UiId` and a `CATALOG` entry, every edit goes through `App::commit`,
every command is a `Message` and an MCP action (`world.add_class`, `world.set_rule`, `world.build`,
`world.reseed`), queries are read-only, and the panel composes components from `uikit/components/` with theme
tokens only. A headless flow in `doppio/tests/ui-flows/` builds a small composition and asserts instance counts.

## 7. Edits, determinism and caching

- **Edit layer.** Sculpting, moving a tree and deleting a rock are stored as sparse `overrides` keyed by
  `(class, cell)`: `remove`, `move to`, `pin variant`. They apply *after* generation, so the generated world never
  stops being reproducible. Moving a tree does not change any other tree.
- **Cache key.** `(world_seed, region, hash of every recipe used, generator_version)`, on disk and in RAM.
  Changing one recipe invalidates only what depends on it.
- **No floating point in placement decisions.** Accept/reject and cell order use integers; pin noise and `libm` calls
  that decide *where*, as the roadmap already requires.
- **Golden tests**: a small composition whose instance list hash is pinned in C++ and Rust, the same pattern as
  `tests/test_hash.cpp`; a test that the build on 1 and 7 threads is identical.

## 8. Gaps, in build order

Each step is useful alone and testable headless. `[x]` means already true on the engine's `main`.

### C0 — Foundations (exist)

- [x] Recipes with `generator_version`; resolver and cached variants.
- [x] Integer hash, same numbers in C++ and Rust.
- [x] Masks, biome table, scatter core, Scatter on Terrain action.
- [ ] `generator.world` recipe kind: format, `Registry::isEditorOnly`, asset kind, double-click opens the tab.

### C1 — Composition model and headless build (core, no UI)

- [ ] `src/caffeine/world`: parse and validate `generator.world`; `build(composition, region)` using the existing
      scatter and biome code; output `WorldPart`.
- [ ] Class salt from the class `id`; ref resolution with version check; all-or-nothing error list.
- [ ] C ABI: `caffeine_world_build` (region in, instance list out), versioned, POD, tests on both sides.
- [ ] Tests: same output for any region split and load order; reordering classes does not move instances.

### C2 — Water as part of the composition

- [ ] `water_distance` mask from water bodies; rivers follow `flow`, lakes fill basins under a level.
- [ ] Optional bed carving before the masks are read (documented limit: CPU, bounded heightfield).
- [ ] Water refs wired (the recipe slot for water materials is still open in `generator-recipes.md`).

### C3 — Ground context and adaptation

- [ ] Context sampling (slope, height band, wetness, water distance, neighbours) per instance.
- [ ] `adapt` mappings to instance scale, lean, tint and the run-time modifiers.
- [ ] Exposed parameters on `generator.nature` so context can drive the **bake** (v2); pool versus `unique`.

### C4 — Output and rendering

- [ ] `.prefab` output that keeps the link to its `generator.world`.
- [ ] `.cinst` instance bake and a draw path that reads it (roadmap phase 4: per-chunk instance buffers, impostors).
- [ ] Persistent bake cache keyed as in section 7 (roadmap phase 5).

### C5 — Editor

- [ ] World tab, library drag, rules editor, preview build, build action with undo.
- [ ] `UiId`s, MCP actions, headless flows, captures through the headless driver.
- [ ] Region painting of overrides.

### C6 — Documentation

- [ ] Portuguese mirror (`content/pt/docs/doppio/world-composition.md`) and both audits.
- [ ] Update the Nature, Terrain and Water guides and link them here.

## 9. Risks and open questions

| Risk or question | Plan |
|---|---|
| Per-entity instances do not scale | `.cinst` instance buffers (C4); entities only for small builds |
| Adapting the bake needs graph parameters Nature does not expose | v1 adapts instances only; exposed parameters are C3 |
| Carving a river changes every mask | carve first, then read masks; cache key includes it |
| Reordering classes or editing one recipe reshuffles the world | salt from the class id; per-recipe hashes in the cache key |
| Floats decide placement across machines | integer decisions, golden tests |
| Is the unit "a world" or "a region"? | build takes a region, so both work; one terrain per composition until terrain tiling exists (generator output is 129/257/513) |
| `.scatter` versus `.generator.world` | `.scatter` stays readable and becomes a view of `classes`; no second format |

## 10. Related

- [`photoreal-world-roadmap.md`](photoreal-world-roadmap.md): the engine, rendering, streaming and quality phases this builds on.
- [`generator-recipes.md`](generator-recipes.md): recipe files, references, variants, the hash.
- [`terrain-generator-guide.md`](terrain-generator-guide.md): masks, biome table, scatter .
- [`nature-generator-guide.md`](nature-generator-guide.md), [`water-generator-guide.md`](water-generator-guide.md), [`material-pipeline.md`](material-pipeline.md).
