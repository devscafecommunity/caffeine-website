# 🏔️ Terrain System

> **Namespace:** `Caffeine::Terrain` , `Caffeine::ECS::TerrainComponent` 
> **Files:** `src/terrain/*` , `src/ecs/TerrainComponents.hpp` 
> ** Status:** 
> * *Procedural generation:** plugin — see [`terrain-plugin.md`](terrain-plugin.md)

---

## Overview

The land in Caffeine is an editable ** heightfield**: data in `TerrainHeightmap` , rendering via `TerrainMeshBuilder` + LOD por chunks, pintura de splat em `TerrainSplatmap` . The engine **don't**combut more procedural generation in the core — this stayed in the plugin **Terrain Generator**, which uses the algorithm in `assets/general-ultra-realistic-terrain-algorithm` .

**Separation of responsibilities:** the Terrain Editor, sculpt/paint tools and
`.cterrain` I/O are native engine features. Only procedural generation lives in
a plugin.

| Camada | Responsabilidade |
|--------|------------------|
| **Core** | Heightmap, mesh, LOD, coarse collision, sculpt/paint, `.cterrain` |
| **Terrain Editor (native)** | Sculpt, splat paint, undo and `.cterrain` import/export |
| **Terrain Generator (plugin)** | Presets, Node.js, import de heightmap |

---

## TerrainComponent

```cpp
struct TerrainComponent {
    u32 resolutionX = 257;
    u32 resolutionZ = 257;
    f32 worldSizeX, worldSizeZ;   // metros (1 u = 1 m)
    f32 maxHeight;                // altura 0–1 do heightmap → metros

    bool useChunks = true;
    u32 chunkVertexCount = 33;
    u32 maxLodLevels = 2;
    f32 lodDistanceScale = 520.0f;

    u32 collisionSampleStep = 4;  // passo do mesh de colisão
    bool buildCollisionMesh = true;

    bool castShadows = true;
    bool receiveShadows = true;
    char texturePath[256];        // albedo legacy / fallback
    char normalMapPath[256];      // normal map triplanar (GPU)
    f32  shininess = 16.0f;       // Phong specular

    char terrainDataPath[256];    // caminho .cterrain no projeto
};
```

O heightmap interno guarda valores **normalizados** `[0, 1]` . Na mesh, `y = sample * maxHeight` .

---

## Pipeline de Dados

- `TerrainComponent (ECS)`
- `▼`
- `TerrainCache::initializeEntity / syncEntity`
  - `TerrainHeightmap (CPU, editável)`
  - `TerrainSplatmap (4 camadas)`
  - `Mesh3D render (TerrainMeshBuilder + tangentes)`
  - `Mesh3D collision (TerrainCollisionMeshBuilder, decimado)`
  - `TerrainChunk[] (LOD + frustum cull)`


### TerrainMeshBuilder

- Generates vertices with normal heightmap ( `sampleNormalBilinear` ).
- UVs em tiling conforme `textureTileSize` / `splatTileSize` .
- **Tangents** calculated by triangle (base for normal mapping).

### Collision

`TerrainCollisionMeshBuilder` reutiliza `buildRegion` com `collisionSampleStep` (e.g.: 4 → ~16× less triangles). Access via `TerrainCache::collisionMeshFor(entity)` . That coarse mesh is for queries. **Physics** uses its own static height field at the full sample resolution, built by `PhysicsSystem3D` for every terrain with `buildCollisionMesh` on: bodies rest on the real surface, sculpting rebuilds it, and the entity's transform moves it ([Physics 3D](../physics/physics-3d.md)).

---

## Editor

| Painel | Function |
|--------|--------|
| **Inspector → Terrain** | Resolution, size, LOD, splat, collision, Normal Map, Shininess |
| **Terrain Editor (native)** | Sculpt (raise/lower/smooth/flatten/noise), splat paint, import/export `.cterrain` |

### Native Terrain Editor

![Terrain with natural ground textures](../images/captures/terrain-native.png)


Open it from **View → Terrain Editor**, the command palette (**Terrain Editor**),
or the **Open Terrain Editor** button in the Toolbox while a Terrain entity is
selected.

| Tool | Behaviour |
|------|-----------|
| **Raise / Lower** | Adds or removes height with a smooth falloff |
| **Smooth** | Averages the local neighbourhood |
| **Flatten** | Flattens to the height under the first click of the stroke |
| **Noise** | Adds deterministic detail |
| **Splat paint** | Paints Grass, Rock, Sand or Dirt weights |
| **Reset default textures** | Restores the default paths and the Grass layer |
| **Data tab** | Edits the `.cterrain` path and imports/exports the file |

Fast strokes are interpolated between frames instead of stamping only once per
frame. Undo/redo snapshots include the heightmap and splatmap, so **Ctrl+Z**
restores terrain edits instead of resetting the terrain to flat.

New terrains start with the **Grass** layer and natural 1k ground textures
from `assets/hdr-assets-texture` (dirt/rock/moss, rocks, dirt and mud). The
Inspector **Tint** colour multiplies the sampled albedo.

Scenes authored before this default stored an unpainted terrain as the old
**Light** layer. Loading such a `.cterrain` migrates the uniform Light splatmap
to Grass and upgrades the untouched Kenney prototype paths to the natural ground
set automatically.

Procedural generation: panel **Terrain Generator** (plugin). The plugin does not
own sculpting or painting.

---

## GPU Rendering (Phong)

Com `CF_HAS_SDL3` , o terreno usa `terrain_lit.frag` :

- Phong lighting (ambient + diffuse + specular) with `shininess` .
- Normal map **triplanar** via `TerrainGpuTextureCache::normalMap` (sampler slot 5).
- Directional shadows (slots 6–7) and point cubemap (slots 8–9).
- `castShadows` / `receiveShadows` respeitados em `GpuSceneRenderer::gatherMeshDraws` .

Ver [`rendering/materials-phong.md`](../rendering/materials-phong.md) e [`rendering/shadow-mapping.md`](../rendering/shadow-mapping.md).

---

## Serialization

`SceneSerializer` grava `TerrainComponent` in the scene blob (version **10**). Version 9 added `collisionSampleStep` e `buildCollisionMesh` ; version 10 adds `normalMapPath` e `shininess` . Legacy generation fields (v2–v8) are read and discarded for compatibility. Heavy height/splat data live in `.cterrain` referenciado por `terrainDataPath` .

---

## Useful API

```cpp
TerrainCache& cache = TerrainCache::instance();
cache.initializeEntity(world, entity);
cache.heightmapFor(entity)->setNormalized(x, z, h);
cache.syncEntity(world, entity);

Terrain::importHeightmapFile(world, entity, path, worldSizeX, worldSizeZ);
```
