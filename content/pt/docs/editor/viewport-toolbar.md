# HUD e controlos do viewport

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/doppio/crates/ui/src/uikit/components/viewport_surface.rs"><code>viewport_surface.rs</code></a></span>
</div>

<p class="doc-lede">O viewport Rust tem um HUD compacto em vez de uma toolbar de
ícones. O modo de vista, o gizmo, a grelha e os marcadores são controlados pelo menu
View e por atalhos; o HUD reporta exatamente o que o renderer está a fazer.</p>

<figure class="doc-figure">
  <img src="../images/editor/workspace-scene.png" alt="HUD do viewport com resolução, grelha, anti-aliasing, modo do gizmo, tempo de frame e FPS" loading="lazy">
  <figcaption>O chip no canto superior esquerdo mostra tamanho de render, grelha, anti-aliasing, modo do gizmo, latência e FPS. O chip de dica lista os gestos da câmara; a linha inferior nomeia a seleção.</figcaption>
</figure>

## HUD

O chip de estado é montado em `windows/main.rs` e desenhado por
`viewport_surface`:

```text
1872×1075 · grid · FXAA · Move · 18 ms · 57 FPS
```

| Campo | Significado |
|---|---|
| `width×height` | Tamanho interno de render em pixels físicos, depois do `render_scale`. |
| `grid` / `no grid` | Estado da grelha de referência. |
| `no AA` / `FXAA` / `TAA` | Modo de anti-aliasing ativo. |
| `Move` / `Rotate` / `Scale` | Modo do gizmo. |
| `ms` | Latência do último readback concluído. |
| `FPS` | Frames de viewport concluídos no último segundo. |

A dica inferior mostra `Selected: <entidade> · Double-click to focus`, ou a dica de
foco quando nada está selecionado.

## Menu View

<table class="doc-table">
  <thead>
    <tr><th>Item</th><th>Atalho</th><th>Efeito</th></tr>
  </thead>
  <tbody>
    <tr><td>Focus Selection</td><td><code>Ctrl+F</code> ou <code>F</code></td><td>Move o foco da órbita para a entidade selecionada.</td></tr>
    <tr><td>Reset Camera</td><td><code>Ctrl+0</code></td><td>Restaura a distância e os ângulos padrão.</td></tr>
    <tr><td>Render Now</td><td><code>Ctrl+R</code></td><td>Pede um frame imediato do viewport.</td></tr>
    <tr><td>Show / Hide Scene Markers</td><td>—</td><td>Alterna marcadores de luz, câmara, collider e empty.</td></tr>
    <tr><td>Show / Hide Grid</td><td><code>G</code></td><td>Alterna a grelha de referência.</td></tr>
    <tr><td>Move Tool</td><td><code>1</code></td><td>Gizmo de translação.</td></tr>
    <tr><td>Rotate Tool</td><td><code>2</code></td><td>Gizmo de rotação.</td></tr>
    <tr><td>Scale Tool</td><td><code>3</code></td><td>Gizmo de escala.</td></tr>
    <tr><td>Terrain / Water / Nature / Texture Generator</td><td>—</td><td>Abre o separador do gerador correspondente.</td></tr>
    <tr><td>Default Layout</td><td><code>Ctrl+1</code></td><td>Restaura a disposição padrão dos painéis.</td></tr>
    <tr><td>Viewport Layout</td><td><code>Ctrl+2</code></td><td>Maximiza a área do viewport.</td></tr>
  </tbody>
</table>

## Gestos da câmara

| Gesto | Ação |
|---|---|
| Arrastar | Orbitar |
| Arrastar com botão direito ou do meio | Pan |
| Roda | Zoom |
| `W` `A` `S` `D` / `Q` `E` | Voar / descer-subir |
| `Shift` | Boost |
| Duplo clique | Focar a entidade sob o cursor |

## Anti-aliasing e render scale

O anti-aliasing e o render scale fazem parte de `CaffeineViewportSettings` na C ABI e
são limitados pelo motor:

- `anti_aliasing`: `Off`, `FXAA` ou `TAA`.
- `render_scale`: `0.5` a `2.0`; acima de 1 faz supersampling, abaixo de 1 troca
  nitidez por velocidade.

O tamanho de render é o tamanho lógico do painel multiplicado pela escala e pelo fator
de escala do ecrã. Alterar o tamanho do painel altera a resolução; o HUD atualiza no
próximo frame concluído.

<div class="doc-callout doc-callout--note">
  <p><strong>Nota histórica.</strong> O editor C++ arquivado tinha uma toolbar
  flutuante só de ícones com 2D/3D/Iso e botões de perspetiva/ortográfica. Não faz
  parte do viewport Rust; use o menu View e os atalhos acima.</p>
</div>

## Páginas relacionadas

- [Scene viewport](scene-viewport.md) — pipeline de readback, picking e câmara.
- [Gizmos e marcadores](../doppio/gizmos-and-markers.md)
- [Performance](../performance/editor-viewport-performance.md)
