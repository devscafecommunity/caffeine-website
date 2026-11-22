# Photon — native hybrid radiance-cascade GI

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Editor</span>
  <span>Last updated: <time datetime="2026-11-21">2026-11-21</time></span>
</div>

<p class="doc-lede">Real-time global illumination without hardware ray tracing, managed from the Photon tab.</p>

Photon is a **native Doppio and runtime system**: it is compiled into the editor and
runtime binaries, not loaded as a plugin. It provides real-time global illumination
without hardware ray tracing.

![Photon indirect lighting in the runtime](../images/captures/photon-gi.png)

## Status

| Photon part | Status |
|-------------|--------|
| Screen-anchored near field | **Implemented**: world-aligned cascades traced against the depth buffer, merged front to back, resolved to SH-L1 |
| Far field | **Implemented**: four voxel clipmap levels with probes, the whole scene's triangles voxelised (terrain, skinned and cut-out meshes included) |
| Dirty regions | **Implemented**: a moving object revoxelises only the boxes where it was and is |
| Direct light into GI | **Implemented**: sun, point and spot lights injected into the voxels, shadowed through the material volume |
| Multi-bounce feedback | **Implemented**: the previous irradiance is fed back with a cap and a reprojected history |
| Bounce gain | **Implemented**: scales the light the voxels hold |
| Motion vectors | Not yet: the history reprojects with the previous matrix |
| Glossy reflection pass | Not yet |
| Temporal denoiser | Provided by the engine's TAA: Photon runs before it |

The complete guide, with the Photon tab, presets, statistics and the C ABI, is
[Photon: global illumination in Doppio](../doppio/photon-guide.md).

## Use it

1. Open a scene with a Camera 3D and geometry.
2. Open **View → Photon (Global Illumination)**.
3. Press **Add Photon GI** if the scene has no component yet.
4. Pick a preset, then tune **Radius**, **Sky**, **Bounce gain** and the voxel geometry switches.
5. Switch **Debug → GI only** to inspect the result, and read the **Voxel volume** card for what the far field is doing.

The component is `ECS::PhotonGIComponent`; the Inspector shows the same fields.


## Baked ambient occlusion (no RTX)

The native **Baked ambient occlusion** section precomputes static AO into the
selected mesh material:

1. Select a static mesh entity (or use **Bake scene**).
2. Choose resolution (256/512/1024), rays, max distance and bias.
3. Press **Bake selected mesh**.

The baker uses **GPU compute** when the render device exposes compute, and falls
back to the CPU BVH otherwise. The CPU only rasterises UVs and builds the triangle
list; the expensive ray tests run on the GPU. Scenes above 8192 triangles use the
CPU path.

The baker:

- gathers every static mesh triangle as an occluder,
- rasterises the target mesh in UV space,
- casts cosine-weighted rays,
- writes an **ORM PNG** with AO in R (roughness/metallic preserved in G/B),
- updates the material's `orm_map` and `ao_strength`.

The runtime shader already samples ORM.R as ambient occlusion, so the result is
applied with **no ray-tracing hardware** and no screen-space noise. Re-bake after
changing static geometry.

> Baked AO is for static meshes. Moving objects should keep using the screen-space
> Photon pass. Meshes with overlapping UVs average their faces; use unique UVs for
> per-face AO.

## Troubleshooting the bake

| Message | Cause / fix |
|---------|-------------|
| **Select a mesh entity in the Hierarchy** | The bake targets a mesh (`MeshFilterComponent`). Select a mesh entity, not the environment or a light. |
| **Selected entity has no mesh** | The entity has no `MeshFilterComponent`, or its custom mesh path is invalid. |
| **Mesh has no usable UV coverage** | The mesh has no UVs, or all UVs are degenerate. Unwrap the mesh before baking. |
| **Could not read material** | `customMaterialPath` points to a missing or invalid `.mat`. Fix the path or clear it so the baker creates a new material. |
| **Bake scene: N failed** | Hover the status/log; the first failing entity and reason are shown. Other meshes are baked normally. |
| **GPU compute unavailable** | The device does not expose compute; the baker automatically uses the CPU BVH. |
| **ORM generated but viewport unchanged** | The material must be assigned to the mesh and the ORM path must resolve under the project root. Re-select the entity or reload the material. |

The bake is queued by the panel and executed **between frames** (after the editor
frame is submitted). This keeps the GPU command buffer independent from the
in-flight frame.

## Performance

- Low: 4 rays × 2 steps per interval
- Medium: 8 rays × 2 steps
- High: 12 rays × 3 steps

Photon runs **before TAA**, so the temporal resolve cleans the stochastic ray
pattern. Start at Balanced for editing and High/Cinematic for captures.


## Limitations

- Photon has no motion vectors yet: the history reprojects with the previous matrix, so fast
  movers can ghost.
- The terrain counts with one earth colour in the voxel volume, and a cut-out mesh counts as a
  solid block when its switch is on.
- Screen-space occlusion can leak on thin geometry; use a smaller **Radius**.
- Glossy reflections are not part of Photon yet.

## Related

- [Photon: global illumination in Doppio](../doppio/photon-guide.md)
- [Scene viewport](scene-viewport.md)
- [Workspace and theme](workspace-and-theme.md)
- [Plugin catalog](../plugins/README.md)
