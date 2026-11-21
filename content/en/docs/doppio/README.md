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
| [`graphics-roadmap.md`](graphics-roadmap.md) | The renderer plan: Micromeshes, Photon and what is next |
| [`photoreal-world-roadmap.md`](photoreal-world-roadmap.md) | The content plan: terrain, nature, water, scatter and streaming |
