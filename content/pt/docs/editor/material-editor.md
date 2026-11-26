# Editor de materiais

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span class="doc-badge">Engine</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/doppio/crates/ui/src/uikit/panels/material.rs"><code>panels/material.rs</code></a></span>
</div>

<p class="doc-lede">O separador Material edita assets PBR <code>.mat</code> no editor
Rust, enquanto o motor detém o modelo de material, o renderer de pré-visualização e o
formato <code>CAFMAT3</code>.</p>

<figure class="doc-figure">
  <img src="../images/editor/material-panel.png" alt="Separador Material com secções de superfície, mapas, UV, avançado e baker" loading="lazy">
  <figcaption>O separador Material. Os valores são publicados imediatamente na cache de materiais do motor; o renderer usa a mesma superfície para o viewport e para a esfera de pré-visualização.</figcaption>
</figure>

## Onde vive

<table class="doc-table">
  <thead>
    <tr><th>Parte</th><th>Dono</th><th>Localização</th></tr>
  </thead>
  <tbody>
    <tr><td>Painel Material (UI Rust)</td><td>Doppio</td><td><code>uikit/panels/material.rs</code></td></tr>
    <tr><td>Modelo e formato de material</td><td>Motor</td><td><code>src/caffeine/assets/MaterialTypes.hpp</code>, <code>MaterialFile.cpp</code></td></tr>
    <tr><td>Pré-visualização offscreen</td><td>Motor</td><td><code>src/caffeine/render/MaterialPreviewRenderer.cpp</code></td></tr>
    <tr><td>Shader PBR</td><td>Motor</td><td><code>scene_lit.frag</code> / <code>terrain_lit.frag</code></td></tr>
  </tbody>
</table>

O `MaterialEditorPanel.cpp` C++ arquivado não é o editor atual. O Doppio lê e escreve
materiais através da C ABI, e o painel é uma vista Rust pura sobre
`doppio_engine::Material`.

## Fluxo de dados

1. Abra ou crie um `.mat` (o ficheiro começa por `CAFMAT3`; `CAFMAT1` e `CAFMAT2` continuam a ser carregados).
2. Uma edição de campo atualiza `MaterialSurface` em memória. A crate do motor
   envolve `caffeine_material_save`, `caffeine_session_apply_material` e o par
   assíncrono `caffeine_session_render_material_preview_begin` / `..._poll`.
3. O motor atualiza a cache de materiais e pede um novo frame ao renderer de
   pré-visualização; o viewport lê a mesma superfície.
4. O renderer desenha uma esfera num pequeno chão com luz direcional e o céu da cena,
   usando HDR, a stack de post-processing e probes de reflexão.
5. **Save** escreve `CAFMAT3` em disco; o material fica disponível no asset browser e
   nas cenas.

<div class="doc-callout doc-callout--note">
  <p><strong>Nota.</strong> O albedo é guardado em sRGB como escolhido no editor. O
  renderer lineariza no shader; não pré-linearize valores num script.</p>
</div>

## Secções do painel

| Secção | Campos |
|---|---|
| **Surface** | Albedo (RGBA), metallic, roughness, reflectance, cor e intensidade da emissão. |
| **Maps** | Slots de albedo, normal, ORM e emissão com asset pickers, normal strength, AO strength e convenção DirectX da normal. |
| **UV** | Tiling, offset e UVs com escala de objeto (um mesh a 2× mantém a densidade da textura). |
| **Advanced** | Alpha mode e cutoff, transmission e IOR, clearcoat e roughness, cor e roughness do sheen, força/espessura/IOR da iridescência, controlos de reflexão e parallax/displacement. |
| **Baker** | Bakes normal/AO/roughness/metallic/ORM, packings Unity, resolução e força. |

A altura é lida do canal alpha do normal map. `heightScale` ativa parallax occlusion;
`displacementMode = 1` passa a displacement geométrico com subdivisão do mesh, para a
silhueta mudar e o relevo projetar sombras reais.

## Pré-visualização

A esfera usa o mesmo shader `scene_lit` do viewport. Os controlos do painel escolhem a
forma, o ambiente, a exposição, a geração de luz e o yaw/elevação/intensidade do sol.
TAA, probes e auto-exposure pedem frames extra até a imagem convergir.

<figure class="doc-figure">
  <img src="../images/editor/generator-red-brick.png" alt="Material Generator a fazer bake de um material de tijolo vermelho para o material aberto" loading="lazy">
  <figcaption>O Material Generator pode construir um material a partir de um grafo e
  fazer bake para o <code>.mat</code> aberto.</figcaption>
</figure>

## Material Generator

O separador **Material Generator** partilha o painel central com o viewport. É um grafo
de nós sobre imagens, ruído, padrões, filtros, blends e saídas, com pré-visualização ao
vivo, vistas de canal (base, normal, height, roughness, AO, emissive, opacity, metal) e
channel packing para ORM e layouts Unity. **Bake to Material** escreve os mapas
selecionados no material aberto.

Veja o [material pipeline](../doppio/material-pipeline.md)
e o [guia de materiais](../doppio/materials-guide.md).

## Formato de ficheiro

| Ficheiro | Função |
|---|---|
| `MaterialTypes.hpp` | `MaterialSurface`, `MaterialAlphaMode`, defaults e validação. |
| `MaterialFile.cpp` | Leitura/escrita `CAFMAT3` e `sanitizeMaterialSurface`. |
| `MaterialPresets.hpp` | Presets nomeados (mirror, chrome, gold, glass…). |
| `MaterialPreviewRenderer.cpp` | Mundo de preview offscreen, luzes e readback. |

## Páginas relacionadas

- [Materiais PBR](../rendering/materials-pbr.md)
- [Reflexos](../rendering/reflections.md)
- [Material pipeline](../doppio/material-pipeline.md)
- [Guia do Texture Generator](../doppio/texture-generator-guide.md)
