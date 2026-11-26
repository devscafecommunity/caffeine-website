# História do desenvolvimento

<div class="doc-meta">
  <span class="doc-badge doc-badge--historical">Historical</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Doppio</span>
  <span>Atualizado em: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">Como o motor e o editor chegaram à forma atual. Esta página é um
índice histórico, não um relatório de estado: as etiquetas de fase e os marcadores
"planned" descrevem o plano da altura, não a implementação de hoje.</p>

<div class="doc-callout doc-callout--note">
  <p><strong>O estado atual vive noutro lugar.</strong> Use o
  <a href="README.md">índice da documentação</a> e as páginas dos módulos para o que
  existe agora. Para notas de release, veja <a href="releases/changelog.md">Changelog</a>.</p>
</div>

## Cronologia

<table class="doc-table">
  <thead>
    <tr><th>Quando</th><th>Marco</th><th>Registo</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>Fundação</td>
      <td>Tipos de largura fixa, allocators, containers, vetores/matrizes e as primeiras suites Catch2.</td>
      <td><a href="core/types.md">Tipos do core</a>, <a href="memory/allocators.md">Allocators</a>, <a href="math/vectors.md">Matemática</a></td>
    </tr>
    <tr>
      <td>Base de runtime</td>
      <td>Timer, game loop de passo fixo, job system, input e ferramentas de debug.</td>
      <td><a href="core/game-loop.md">Game loop</a>, <a href="concurrency/job-system.md">Job system</a>, <a href="debug/debug-tools.md">Debug tools</a></td>
    </tr>
    <tr>
      <td>RHI e 2D</td>
      <td>Abstração SDL3 GPU, batch renderer, câmara 2D, asset manager e o formato CAF.</td>
      <td><a href="rendering/rhi.md">RHI</a>, <a href="rendering/batch-renderer.md">Batch renderer</a>, <a href="assets/caf-format.md">Formato CAF</a></td>
    </tr>
    <tr>
      <td>ECS e sistemas</td>
      <td>ECS por arquétipos, scene stack, eventos, física, animação, áudio e UI retida.</td>
      <td><a href="ecs/core.md">ECS</a>, <a href="physics/physics-2d.md">Física 2D</a>, <a href="audio/audio-system.md">Áudio</a></td>
    </tr>
    <tr>
      <td>Transição 3D</td>
      <td>Quaternions, carregamento de meshes, câmara 3D, partição espacial, animação esquelética.</td>
      <td><a href="math/quaternions.md">Quaternions</a>, <a href="rendering/camera-3d.md">Câmara 3D</a>, <a href="physics/spatial-partitioning.md">Partição espacial</a></td>
    </tr>
    <tr>
      <td>Doppio</td>
      <td>Do editor C++ em ImGui para o workspace Rust/Iced, o layout de cinco painéis e a fronteira C ABI.</td>
      <td><a href="editor/scene-editor.md">Editor de cena</a>, <a href="doppio/rust-ui.md">Notas da UI Rust</a>, <a href="plans/2026-05-24-doppio-ui-test-framework.md">Plano do framework de testes</a></td>
    </tr>
    <tr>
      <td>Impulso de render</td>
      <td>PBR, pós-processamento HDR, TAA, sombras, reflexos, iluminação volumétrica e viewport com readback GPU.</td>
      <td><a href="plans/2026-09-21-rendering-roadmap.md">Roadmap de render</a>, <a href="plans/2026-10-02-forward-pbr-post-session.md">Sessão forward PBR</a>, <a href="rendering/materials-pbr.md">Materiais PBR</a></td>
    </tr>
    <tr>
      <td>Ferramentas de conteúdo</td>
      <td>Material Generator, Texture Generator, pintor Texture Set, Nature, Water e Terrain.</td>
      <td><a href="doppio/material-pipeline.md">Material pipeline</a>, <a href="doppio/texture-generator-guide.md">Guia de texturas</a>, <a href="doppio/terrain-generator-guide.md">Guia de terreno</a></td>
    </tr>
    <tr>
      <td>Testes headless</td>
      <td>Flows de UI por script, capturas anotadas, baselines e gravação GIF/MP4 sem janela.</td>
      <td><a href="doppio/headless-testing.md">Driver headless</a>, <a href="editor/test-automation.md">Automação de testes</a></td>
    </tr>
  </tbody>
</table>

## Trilhos de planeamento

| Trilho | Páginas |
|---|---|
| Pilares fundamentais | [Roadmap de pilares](plans/2026-09-22-engine-pillars-roadmap.md) |
| Renderização | [Roadmap de render](plans/2026-09-21-rendering-roadmap.md) |
| Marcos do editor M1–M4 | [Milestones](plans/milestones/README.md) |
| Plano do módulo de terreno | [Milestones de terreno](plans/milestones/terrain/README.md) |
| Arquivo de sessões | [Arquivo](plans/archive/README.md) |

## Convenções que sobreviveram

- **Design orientado a dados** — armazenamento contíguo de componentes, iteração
  cache-friendly.
- **Sem RTTI, sem exceções em caminhos quentes** — erros são valores de retorno.
- **Allocators próprios** — sem `new`/`delete` soltos no código do motor.
- **C ABI para frontends** — o editor é substituível; o Doppio é um frontend.
- **Testes para comportamento** — Catch2 no motor, flows headless no editor.

## Histórico completo

O registo cronológico é o histórico Git do repositório. Notas de release vivem em
[Changelog](releases/changelog.md); notas de sessão em `plans/` capturam o raciocínio
por trás das mudanças maiores.
