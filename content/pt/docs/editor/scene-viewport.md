# Scene viewport

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/doppio/crates/ui/src/uikit/components/viewport_surface.rs"><code>viewport_surface.rs</code></a></span>
</div>

<p class="doc-lede">O viewport é um render GPU do motor, lido de volta para o editor
Rust e composto por baixo do gizmo, marcadores e HUD. Nunca bloqueia a thread da UI.</p>

<figure class="doc-figure">
  <img src="../images/editor/workspace-scene.png" alt="Viewport do Doppio com grelha, gizmo de transform e marcadores de cena sobre uma cena renderizada" loading="lazy">
  <figcaption>O render do motor chega como pixels; a toolbar, o HUD, o gizmo e os marcadores são desenhados pelo editor por cima do frame.</figcaption>
</figure>

## Pipeline de frame

1. O painel reporta o tamanho lógico. O editor guarda o tamanho de render desejado em
   pixels físicos e pede um frame no máximo a cada 16 ms.
2. `caffeine_session_render_begin(width, height)` inicia um render offscreen do motor.
3. O `ViewportTick` de 16 ms faz polling de
   `caffeine_session_render_poll` para um buffer RGBA reutilizado. Os estados são
   `Pending`, `Ready`, `Idle` e `Failed`.
4. Em `Ready`, os pixels são enviados para uma textura Iced/wgpu através de
   `uikit/components/viewport_shader.rs`. Um hash de conteúdo salta frames idênticos,
   por isso uma cena estática não reenvia a textura a cada tick.
5. O editor desenha toolbar, HUD, gizmo e marcadores por cima do frame. Esses overlays
   projetam com a mesma câmara que produziu a imagem.

<div class="doc-callout doc-callout--warning">
  <p><strong>Aviso.</strong> SDL_GPU não expõe um handle nativo de textura através da
  API pública. Uma textura wgpu partilhada não é possível sem alterar o renderer
  (backend wgpu, patch do SDL ou uma janela separada). O caminho de readback é o
  suportado; não o descreva como zero-copy.</p>
</div>

## Definições de qualidade

<table class="doc-table">
  <thead>
    <tr><th>Definição</th><th>Valores</th><th>Notas</th></tr>
  </thead>
  <tbody>
    <tr><td>Anti-aliasing</td><td><code>Off</code>, <code>FXAA</code>, <code>TAA</code></td><td>FXAA é o padrão; TAA acumula entre frames e precisa de câmara estável.</td></tr>
    <tr><td>Render scale</td><td><code>0.5</code> … <code>2.0</code></td><td>Supersampling interno; padrão <code>1.5</code>. A UI fica na resolução lógica.</td></tr>
    <tr><td>Grelha</td><td>on / off</td><td><code>G</code> ou View → Show/Hide Grid.</td></tr>
    <tr><td>Marcadores</td><td>on / off</td><td>View → Show/Hide Scene Markers.</td></tr>
    <tr><td>Gizmo</td><td>Move / Rotate / Scale</td><td><code>1</code>, <code>2</code>, <code>3</code> ou View → Move/Rotate/Scale Tool.</td></tr>
  </tbody>
</table>

O HUD mostra resolução, grelha, modo do gizmo, modelo de vista, FPS e latência do
render. `Ctrl+R` força um frame; `Ctrl+0` repõe a câmara.

## Câmara

| Entrada | Ação |
|---|---|
| Arrastar | Orbitar em torno do ponto de foco |
| Arrastar com o botão direito ou do meio | Fazer pan do foco |
| Roda | Zoom (exponencial) |
| `W` `A` `S` `D` | Voar na horizontal |
| `Q` / `E` | Descer / subir |
| `Shift` | Boost de voo |
| `F` ou duplo clique | Focar a seleção |
| `Ctrl+0` | Repor a câmara |

O estado da câmara vive em `windows/main.rs`; `viewport_surface` apenas converte
eventos de ponteiro e roda em mensagens de câmara. Essa separação mantém a matemática
fora do widget e torna-a testável.

## Seleção e picking

Um clique usa um raio do cursor através da câmara. Se o raio atingir um handle do
gizmo, o gizmo consome-o; caso contrário, um marcador de cena; caso contrário, o
motor faz picking da mesh. O resultado atualiza a seleção e o Inspector. O picking usa
a transform mundial resolvida pela cadeia de pais, por isso filhos de grupos movidos
são selecionados corretamente.

## Estado vazio e fixtures

Quando não há sessão de motor, o viewport mostra **Waiting for the engine
viewport…**. Isto é esperado nas fixtures headless `entities` e `empty`. A fixture
`scene3d` inicia uma sessão real com luzes, câmara e meshes, e é a usada pelos flows
de captura do gizmo e marcadores.

## Páginas relacionadas

- [Toolbar do viewport](viewport-toolbar.md) — toolbar de ícones e projeções.
- [Gizmos e marcadores](../doppio/gizmos-and-markers.md)
- [Guia de materiais](../doppio/materials-guide.md)
- [Performance](../performance/editor-viewport-performance.md)
