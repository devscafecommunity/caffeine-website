# Material editor

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span class="doc-badge">Engine</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/doppio/crates/ui/src/uikit/panels/material.rs"><code>panels/material.rs</code></a></span>
</div>

<p class="doc-lede">The Material tab edits <code>.mat</code> PBR assets in the Rust
editor, while the engine owns the material model, the preview renderer and the
<code>CAFMAT3</code> file format.</p>

<figure class="doc-figure">
  <img src="../images/editor/material-panel.png" alt="Material tab with surface, maps, UV, advanced and baker sections" loading="lazy">
  <figcaption>The Material tab. Values publish to the engine material cache immediately; the renderer reads the same surface for the viewport and the preview sphere.</figcaption>
</figure>

## Where it lives

<table class="doc-table">
  <thead>
    <tr><th>Part</th><th>Owner</th><th>Location</th></tr>
  </thead>
  <tbody>
    <tr><td>Material panel (Rust UI)</td><td>Doppio</td><td><code>uikit/panels/material.rs</code></td></tr>
    <tr><td>Material model and file format</td><td>Engine</td><td><code>src/caffeine/assets/MaterialTypes.hpp</code>, <code>MaterialFile.cpp</code></td></tr>
    <tr><td>Offscreen preview</td><td>Engine</td><td><code>src/caffeine/render/MaterialPreviewRenderer.cpp</code></td></tr>
    <tr><td>PBR shader</td><td>Engine</td><td><code>scene_lit.frag</code> / <code>terrain_lit.frag</code></td></tr>
  </tbody>
</table>

The archived C++ `MaterialEditorPanel.cpp` is not the current editor. Doppio reads and
writes materials through the C ABI, and the panel is a pure Rust view over
`doppio_engine::Material`.

## Data flow

1. Open or create a `.mat` (the file starts with `CAFMAT3`; `CAFMAT1` and `CAFMAT2` are still loaded).
2. A field edit updates `MaterialSurface` in memory. The engine crate wraps
   `caffeine_material_save`, `caffeine_session_apply_material` and the asynchronous
   `caffeine_session_render_material_preview_begin` / `..._poll` pair.
3. The engine updates its material cache and asks the preview renderer for a new
   frame; the viewport reads the same surface.
4. The preview renderer draws a sphere on a small floor with a directional light and
   the scene sky, using HDR, the post-processing stack and reflection probes.
5. **Save** writes `CAFMAT3` to disk; the material is then available to the asset
   browser and to scenes.

<div class="doc-callout doc-callout--note">
  <p><strong>Note.</strong> Albedo is stored in sRGB as picked in the editor. The
  renderer linearises it in the shader; do not pre-linearise values in a script.</p>
</div>

## Panel sections

| Section | Fields |
|---|---|
| **Surface** | Albedo (RGBA), metallic, roughness, reflectance, emission colour and strength. |
| **Maps** | Albedo, normal, ORM and emission map slots with asset pickers, normal strength, AO strength and DirectX normal convention. |
| **UV** | Tiling, offset and object-scale UVs (a mesh scaled 2× keeps texture density). |
| **Advanced** | Alpha mode and cutoff, transmission and IOR, clearcoat and roughness, sheen colour and roughness, iridescence strength/thickness/IOR, reflection controls and parallax/displacement. |
| **Baker** | Normal/AO/roughness/metallic/ORM bakes, Unity packings, resolution and strength. |

Height is read from the alpha channel of the normal map. `heightScale` enables
parallax occlusion; `displacementMode = 1` switches to geometric displacement with
mesh subdivision, so the silhouette changes and relief casts real shadows.

## Preview

The preview sphere uses the same `scene_lit` shader as the viewport. Controls in the
panel choose the shape, environment, exposure, light generation and sun
yaw/elevation/intensity. TAA, probes and auto-exposure request extra frames until the
image converges.

<figure class="doc-figure">
  <img src="../images/editor/generator-red-brick.png" alt="Material Generator baking a red brick material into the open material" loading="lazy">
  <figcaption>The Material Generator can build a material from a node graph and bake it into the open <code>.mat</code>.</figcaption>
</figure>

## Material Generator

The **Material Generator** tab shares the centre pane with the viewport. It is a node
graph over image, noise, pattern, filter, blend and output nodes, with a live preview,
channel views (base, normal, height, roughness, AO, emissive, opacity, metal) and
channel packing for ORM and Unity layouts. **Bake to Material** writes the selected
maps into the open material.

See the [material pipeline](../doppio/material-pipeline.md)
and [materials guide](../doppio/materials-guide.md).

## File format

| File | Purpose |
|---|---|
| `MaterialTypes.hpp` | `MaterialSurface`, `MaterialAlphaMode`, defaults and validation. |
| `MaterialFile.cpp` | `CAFMAT3` read/write and `sanitizeMaterialSurface`. |
| `MaterialPresets.hpp` | Named presets (mirror, chrome, gold, glass…). |
| `MaterialPreviewRenderer.cpp` | Offscreen preview world, lights and readback. |

## Related pages

- [PBR materials](../rendering/materials-pbr.md)
- [Reflections](../rendering/reflections.md)
- [Material pipeline](../doppio/material-pipeline.md)
- [Texture Generator guide](../doppio/texture-generator-guide.md)
