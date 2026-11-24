# Doppio: the editor guides

<div class="doc-meta">
  <span class="doc-badge doc-badge--reference">Reference</span>
  <span class="doc-badge">Doppio</span>
  <span>Last updated: <time datetime="2026-11-21">2026-11-21</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine-website/tree/main/content/en/docs/doppio"><code>content/en/docs/doppio</code></a></span>
</div>

<p class="doc-lede">The guides of the Rust/Iced Doppio editor: how the UI is built, how to drive it headless, and the generators that
make rocks, trees, water, terrain, textures and materials. The engine repository keeps the same files next to the code.</p>

## 1. The editor

| Page | What it covers |
|---|---|
| [`rust-ui.md`](rust-ui.md) | Architecture of the Iced editor: panes, panels, components, ids, messages, the agent bridge |
| [`headless-testing.md`](headless-testing.md) | The `doppio-headless` driver: actions, targets, flows, screenshots |
| [`gizmos-and-markers.md`](gizmos-and-markers.md) | Transform gizmos and the scene markers for lights, cameras and colliders |
| [`runtime-modifiers.md`](runtime-modifiers.md) | Tint, wetness, snow and age on materials at run time |

## 2. Generators

| Page | What it covers |
|---|---|
| [`generator-recipes.md`](generator-recipes.md) | `generator.*` recipes, prefabs and how a generated thing stays editable |
| [`nature-generator-guide.md`](nature-generator-guide.md) | Rocks, trees and plants from a node graph, the Edit Library Material node |
| [`terrain-generator-guide.md`](terrain-generator-guide.md) | Terrains from field sources, modifiers, masks and erosion |
| [`water-generator-guide.md`](water-generator-guide.md) | Water surfaces from wave sources and modifiers |
| [`texture-generator-guide.md`](texture-generator-guide.md) | Textures, VFX and flipbooks from a node graph |
| [`materials-guide.md`](materials-guide.md) | The material library, depth, variation and UV scale, with renders |
| [`material-pipeline.md`](material-pipeline.md) | The living checklist of the material pipeline |

## 3. Rendering and roadmaps

| Page | What it covers |
|---|---|
| [`micromeshes.md`](micromeshes.md) | Micromeshes: a cluster hierarchy and a GPU cut for dense meshes |
| [`photon-guide.md`](photon-guide.md) | Photon: global illumination, the Photon tab, the voxel volume and its statistics |
| [`profiler-guide.md`](profiler-guide.md) | Profiler: timed scopes for the renderer, GPU timing, the Profiler tab and how to read a profile |
| [`environment-guide.md`](environment-guide.md) | Environment: clouds, height fog and rain, the Environment tab, and how they agree with the sun and Photon |
| [`graphics-roadmap.md`](graphics-roadmap.md) | The renderer plan: Micromeshes, Photon and what is next |
| [`photoreal-world-roadmap.md`](photoreal-world-roadmap.md) | The content plan: terrain, nature, water, scatter and streaming |
| [`terrain-editing-roadmap.md`](terrain-editing-roadmap.md) | The terrain editing plan: custom brushes, a material palette, adaptive vegetation and the native terrain format |
| [`terrain-editing-phase-0.md`](terrain-editing-phase-0.md) | The terrain editing foundation as built: tile model, stroke engine, native container, regional GI, brush cursor, C ABI 25 to 27 |
| [`terrain-editing-phase-2.md`](terrain-editing-phase-2.md) | Terrain material painting as built: a palette of up to 64 layers, the layer map, paint strokes, auto-layering, the array-texture renderer, the Terrain Paint tab, C ABI 29 |
| [`terrain-editing-phase-1.md`](terrain-editing-phase-1.md) | Terrain sculpting as built: 16 brush modes, 58 brushes, `.brush` files, symmetry, protection, the Terrain Brush tab, C ABI 28 |
