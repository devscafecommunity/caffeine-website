# ☕ Caffeine Engine — Documentation

> Technical documentation organized by functional modules.

---

## Documentation Index

### Getting started

| Document | Description |
|----------|-------------|
| **Getting started** | [`getting-started/README.md`](getting-started/README.md) | Clone, build and run Doppio |
| **Build guide** | [`getting-started/build-guide.md`](getting-started/build-guide.md) | `caffeine-build` wrapper for every platform |
| **UI gallery** | [`editor/ui-gallery.md`](editor/ui-gallery.md) | Screenshots of the editor, viewport and docking |
| **UI reference (generated)** | [`editor/ui-reference.md`](editor/ui-reference.md) | Every widget id with a captioned, highlighted image |
| **Doppio guides** | [`doppio/README.md`](doppio/README.md) | Editor architecture, headless driver, generators (nature, terrain, water, texture, materials), roadmaps |
| **Plugin Manager** | [`editor/plugin-manager.md`](editor/plugin-manager.md) | Build, install and enable plugins explicitly |

### Arquitectura

| Documento | Description |
|-----------|-----------|
| **Cafpack** | [`architecture/cafpack.md`](architecture/cafpack.md) | Unified asset layer — Doppio, caf-pack and the runtime |

### Roadmap & Planos

| Documento | Description |
|-----------|-----------|
| **Editor milestones** | [`plans/milestones/README.md`](plans/milestones/README.md) | M1–M4 editor program and terrain track |
| **Session archive** | [`plans/archive/README.md`](plans/archive/README.md) | Historical implementation sessions |
| **Engine Pillars** | [`plans/2026-09-22-engine-pillars-roadmap.md`](plans/2026-09-22-engine-pillars-roadmap.md) | Fundamental Pillars: Phong 3D, Bullet3, OpenAL, ECS, handles, networking, PBR, animation, scripting, Android |
| **Rendering Roadmap** | [`plans/2026-09-21-rendering-roadmap.md`](plans/2026-09-21-rendering-roadmap.md) | Plan P0–P6: Single GPU, textures, LOD, PBR, shadows, reflexes, volumetric |
| **Sessão 2026-09-22 (Phong)** | [`plans/2026-09-22-phong-gpu-handles-session.md`](plans/2026-09-22-phong-gpu-handles-session.md) | Changelog: Phong GPU, sombras, handles, normal maps, inspector |
| ** Session 2026-09-22 (Viewport)** | [`plans/2026-09-22-viewport-rendering-quality-session.md`](plans/2026-09-22-viewport-rendering-quality-session.md) | HiDPI, GPU wireless, LOD textures, camera performance |
| **Session 2026-10-02 (PBR + Post)** | [`plans/2026-10-02-forward-pbr-post-session.md`](plans/2026-10-02-forward-pbr-post-session.md) | HDR, TAA, probes, stack GPU, Material Editor, Lua postprocess |
| **Performance — Viewport Editor** | [`performance/editor-viewport-performance.md`](performance/editor-viewport-performance.md) | FPS Doppio, GPU/CPU exclusivo, sombras, profiler, SIGSEGV NVIDIA |

### Engine Core

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Core Types** | [`core/types.md`](core/types.md) | Tipos fundamentais ( `u8..u64` , `f32` , `f64` , `usize` ), plataforma, compilador, assertions |
| **Timer** | [`core/timer.md`](core/timer.md) | High-Resolution Timer, `TimePoint` , `Duration` , `ScopeTimer` |
| **Game Loop** | [`core/game-loop.md`](core/game-loop.md) | Fixed timestep, accumulator, interpolation, spiral of death prevention |
| **Event Bus** | [`core/events.md`](core/events.md) | Pub/sub tipado, `Event<T>` , fila diferida, thread-safe |

### Memory & Data

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Allocators** | [`memory/allocators.md`](memory/allocators.md) | `IAllocator` , Linear, Pool, Stack allocators |
| **Memory Model** | [`memory/memory-model.md`](memory/memory-model.md) | Engine memory model, allocation strategies |
| **Containers** | [`memory/containers.md`](memory/containers.md) | Vector, HashMap, StringView, FixedString |

### Math Library

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Vectors & Matrices** | [`math/vectors.md`](math/vectors.md) | Vec2, Vec3, Vec4, Mat4, operations and transformations |
| **Quaternions** | [`math/quaternions.md`](math/quaternions.md) | Quaternion, SLERP, Mat4 3D extensions (perspective, lookAt) |

### Concurrency

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Job System** | [`concurrency/job-system.md`](concurrency/job-system.md) | Thread pool, work-stealing, job priorities, fiber support |

### Input

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Input System** | [`input/input-system.md`](input/input-system.md) | Action mapping, polling, gamepad/keyboard/mouse abstraction |

### Rendering

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Post-Processing** | [`rendering/post-processing.md`](rendering/post-processing.md) | Modular GPU Stack (HDR→RGBA8), Moon, `customEffectScript` |
| **Forward features** | [`rendering/forward-render-features.md`](rendering/forward-render-features.md) | Installation, IBL, occlusion, reflexes, volumetric (ECS) |
| **Reflexos** | [`rendering/reflections.md`](rendering/reflections.md) | Planar, SSR, probes por objeto, environment map |
| **Volumetric** | [`rendering/volumetric-lighting.md`](rendering/volumetric-lighting.md) | Analytical Fog in Forward Shader |
| **Mesh LOD** | [`rendering/mesh-lod.md`](rendering/mesh-lod.md) | LOD of meshes and distances |
| **Render snapshot** | [`rendering/render-snapshot.md`](rendering/render-snapshot.md) | Visual Regression CLI Tool |
| **RHI** | [`rendering/rhi.md`](rendering/rhi.md) | RenderDevice, CommandBuffer, Triple Buffering, SDL GPU abstraction |
| **Batch Renderer** | [`rendering/batch-renderer.md`](rendering/batch-renderer.md) | Sprite batching, Texture Atlas, Radix Sort, Persistent Mapped Buffers |
| **Camera 2D** | [`rendering/camera-2d.md`](rendering/camera-2d.md) | Spell projection, follow, shake, bundles |
| **Camera 3D** | [`rendering/camera-3d.md`](rendering/camera-3d.md) | Perspective projection, lookAt, frustum cooking |
| **Materiais Phong** | [`rendering/materials-phong.md`](rendering/materials-phong.md) | Meshe lighting and terrain |
| **Materiais PBR** | [`rendering/materials-pbr.md`](rendering/materials-pbr.md) | `.mat` : albedo, metallic, roughness, ORM, emission |
| **Shadow Mapping** | [`rendering/shadow-mapping.md`](rendering/shadow-mapping.md) | Sombras GPU direcionais e pontuais |
| **Texture Quality LOD** | [`rendering/texture-quality-lod.md`](rendering/texture-quality-lod.md) | LOD of remote textures to viewers |

### Assets

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Asset Manager** | [`assets/asset-manager.md`](assets/asset-manager.md) | Async loading, hot-reload, `AssetHandle<T>` , cache |
| **CAF Format** | [`assets/caf-format.md`](assets/caf-format.md) | Binary format `.caf` — zero-parsing, zero-copy |
| **Mesh Loading** | [`assets/mesh-loading.md`](assets/mesh-loading.md) | Mesh loader (.obj, .gltf), Shader system HLSL/GLSL |
| **Asset Pipeline** | [`assets/asset-pipeline.md`](assets/asset-pipeline.md) | CLI convert: PNG/WAV/OBJ → `.caf` |
| **Vegetation Kit** | [`assets/vegetation-kit.md`](assets/vegetation-kit.md) | CC0 PBR/alpha foliage, GI/AO and LOD test kit with a demo scene |

### ECS (Entity Component System)

| Module | Documentation | Description |
|--------|-------------|-----------|
| **ECS Core** | [`ecs/core.md`](ecs/core.md) | Archetypes, World, Entity, ComponentQuery, Command Buffer |
| **Scene Manager** | [`ecs/scene.md`](ecs/scene.md) | Scene stack, parent/child hierarchy, serialization `.caf` |
| **ECS Overview** | [`ecs/README.md`](ecs/README.md) | ECS Overview |
| **ECS Examples** | [`ecs/examples.md`](ecs/examples.md) | Exemplos de uso do ECS |

### Editor

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Plugin SDK** | [`editor/plugin-sdk.md`](editor/plugin-sdk.md) | Doppio lean + dynamic plugins, services, UI |
| **Plugin Manager** | [`editor/plugin-manager.md`](editor/plugin-manager.md) | Opt-in loading, enable list, troubleshooting |
| **UI gallery** | [`editor/ui-gallery.md`](editor/ui-gallery.md) | Screenshots and workspace layout |
| **Workspace & theme** | [`editor/workspace-and-theme.md`](editor/workspace-and-theme.md) | UIKit, `theme.json`, `workspace.json`, panel registry |
| **Viewport toolbar** | [`editor/viewport-toolbar.md`](editor/viewport-toolbar.md) | Icon toolbar, projection and isometric view |
| **Photon GI** | [`editor/photon.md`](editor/photon.md) | Native hybrid radiance-cascade GI and baked AO |
| **Plugin migration** | [`editor/plugin-migration.md`](editor/plugin-migration.md) | Move a plugin to `doppio-plugins` and the opt-in loader |
| **Git Plugin** | [`editor/git-plugin.md`](editor/git-plugin.md) | Optional management panel Project Git |
| **Doppio guides** | [`doppio/README.md`](doppio/README.md) | Editor architecture, headless driver, generators (nature, terrain, water, texture, materials), roadmaps |

### Terrain

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Terrain System** | [`terrain/terrain-system.md`](terrain/terrain-system.md) | Heightmap, mesh, LOD, collision, sculpt/paint, `.cterrain` |
| **Terrain Generator Plugin** | [`terrain/terrain-plugin.md`](terrain/terrain-plugin.md) | Procedural generation via ultra-realistic algorithm (Node.js) |
| **Procedural Tools Plugin** | [`terrain/procedural-tools-plugin.md`](terrain/procedural-tools-plugin.md) | Streaming procedure (exploitation, backrooms, race) + Moon |

### Plugins

| Document | Description |
|----------|-------------|
| **Plugin catalog** | [`plugins/README.md`](plugins/README.md) | Official plugins and quick build |
| **Getting started** | [`plugins/getting-started.md`](plugins/getting-started.md) | Hello template and install |
| **Installing plugins** | [`plugins/installing-plugins.md`](plugins/installing-plugins.md) | Discovery paths and enable list |
| **Writing a plugin** | [`plugins/writing-a-plugin.md`](plugins/writing-a-plugin.md) | C ABI, lifecycle, host API |
| **Service registry** | [`plugins/service-registry.md`](plugins/service-registry.md) | Cross-plugin services |
| **Compatibility** | [`plugins/compatibility.md`](plugins/compatibility.md) | ABI, build flags and platform matrix |
| **VC&M** | [`plugins/volumetric-clouds.md`](plugins/volumetric-clouds.md) | Volumetric clouds and mist plugin |

### Physics

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Physics 2D** | [`physics/physics-2d.md`](physics/physics-2d.md) | AABB/circle collision, rigid body, layers, raycast |
| **Physics 3D** | [`physics/physics-3d.md`](physics/physics-3d.md) | Bullet3: box/sphere/capsule, play mode sync |
| **Spatial Partitioning** | [`physics/spatial-partitioning.md`](physics/spatial-partitioning.md) | Octree, broad-phase collision, frustum culling |

### Animation

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Animation 2D** | [`animation/animation-2d.md`](animation/animation-2d.md) | Sprite clips, state machine, frame events |
| **Skeletal Animation** | [`animation/skeletal-animation.md`](animation/skeletal-animation.md) | Bones, skinning, blend trees, glTF animation |

### Audio

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Audio System** | [`audio/audio-system.md`](audio/audio-system.md) | SFX, music streaming, spatial 2D, SDL_AudioStream |

### UI

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Game UI** | [`ui/game-ui.md`](ui/game-ui.md) | UI retained mode, widgets ECS, bindValue |
| **Editor UI** | [`ui/editor-ui.md`](ui/editor-ui.md) | Dear ImGui integrado, ProfilerWindow, ConsoleWindow |
| **Composable UI kit** | [`ui/ui-kit.md`](ui/ui-kit.md) | Objects → Cards → Panels, controls, canvases and nodes |

### Editor

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Scene Editor** | [`editor/scene-editor.md`](editor/scene-editor.md) | Entity Inspector, Hierarchy, Gizmos, drag-and-drop |
| **Scene Viewport** | [`editor/scene-viewport.md`](editor/scene-viewport.md) | HDR, TAA, render scale, GPU grid/heaven |
| **Material Editor** | [`editor/material-editor.md`](editor/material-editor.md) | `.mat` PBR, presets, preview com probes |

### Scripting

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Scripting** | [`scripting/scripting.md`](scripting/scripting.md) | Overview (roadmap) |
| **Lua runtime APIs** | [`scripting/runtime-apis.md`](scripting/runtime-apis.md) | `postprocess` , `forwardrender` , ciclo de vida |

### Debug

| Module | Documentation | Description |
|--------|-------------|-----------|
| **Debug Tools** | [`debug/debug-tools.md`](debug/debug-tools.md) | LogSystem, Profiler, DebugDraw |
| **Testing** | [`debug/testing.md`](debug/testing.md) | Test system, Catch2, CI integration |

### API Reference

| Documentation | Description |
|-------------|-----------|
| [`api/README.md`](api/README.md) | Full API reference per module |

---

## Reference Documents

| Documento | Description |
|-----------|-----------|
| [`MASTER.md`](MASTER.md) | Complete unified documentation (general view) |
| [`architecture_specs.md`](architecture_specs.md) | Detailed technical specifications |
| [`HISTORY.md`](HISTORY.md) | History of development (phases, roadmap, plans) |

---

> "Caffeine: Because great games are built on strong code and a lot of coffee."*
