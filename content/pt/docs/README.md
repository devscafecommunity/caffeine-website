# Documentação Caffeine

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine"><code>devscafecommunity/caffeine</code></a></span>
</div>

<p class="doc-lede">O Caffeine Engine é um motor C++20 sobre SDL3. O Doppio é o seu
editor Rust/Iced. O motor expõe uma C ABI estável para qualquer frontend o conduzir, e
o editor comunica através de <code>libcaffeine-capi</code>.</p>

<div class="doc-callout doc-callout--tip">
  <p><strong>Novo aqui?</strong> Comece em <a href="getting-started/README.md">Começar</a>
  e no <a href="getting-started/quick-start.md">Quick start</a>, depois faça a visita
  visual na <a href="editor/ui-gallery.md">galeria de UI</a>.</p>
</div>

## Mapa da documentação

<table class="doc-table">
  <thead>
    <tr><th>Área</th><th>Comece em</th><th>Leia também</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Compilar e executar</strong></td>
      <td><a href="getting-started/README.md">Começar</a></td>
      <td><a href="getting-started/building.md">Compilar</a>, <a href="getting-started/build-guide.md">Guia de build</a>, <a href="getting-started/contributing.md">Contribuir</a></td>
    </tr>
    <tr>
      <td><strong>Editor Doppio</strong></td>
      <td><a href="editor/scene-editor.md">Editor de cena</a></td>
      <td><a href="editor/scene-viewport.md">Scene viewport</a>, <a href="editor/workspace-and-theme.md">Workspace e tema</a>, <a href="editor/material-editor.md">Editor de materiais</a></td>
    </tr>
    <tr>
      <td><strong>Testes do editor</strong></td>
      <td><a href="editor/test-automation.md">Automação de testes</a></td>
      <td><a href="doppio/headless-testing.md">Referência headless</a>, <a href="editor/ui-reference.md">Referência de UI</a></td>
    </tr>
    <tr>
      <td><strong>Ferramentas de conteúdo</strong></td>
      <td><a href="doppio/material-pipeline.md">Material pipeline</a></td>
      <td><a href="doppio/materials-guide.md">Guia de materiais</a>, <a href="doppio/nature-generator-guide.md">Nature</a>, <a href="doppio/terrain-generator-guide.md">Terrain</a>, <a href="doppio/water-generator-guide.md">Water</a>, <a href="doppio/texture-generator-guide.md">Texture</a></td>
    </tr>
    <tr>
      <td><strong>Core do motor</strong></td>
      <td><a href="core/types.md">Tipos do core</a></td>
      <td><a href="core/timer.md">Timer</a>, <a href="core/game-loop.md">Game loop</a>, <a href="core/events.md">Events</a>, <a href="memory/memory-model.md">Memória</a>, <a href="math/vectors.md">Matemática</a></td>
    </tr>
    <tr>
      <td><strong>ECS e cenas</strong></td>
      <td><a href="ecs/core.md">ECS core</a></td>
      <td><a href="ecs/scene.md">Scene manager</a>, <a href="ecs/examples.md">Exemplos</a></td>
    </tr>
    <tr>
      <td><strong>Renderização</strong></td>
      <td><a href="rendering/rhi.md">RHI</a></td>
      <td><a href="rendering/materials-pbr.md">Materiais PBR</a>, <a href="rendering/post-processing.md">Post-processing</a>, <a href="rendering/shadow-mapping.md">Sombras</a>, <a href="rendering/reflections.md">Reflexos</a></td>
    </tr>
    <tr>
      <td><strong>Física, áudio, animação</strong></td>
      <td><a href="physics/physics-3d.md">Física 3D</a></td>
      <td><a href="physics/physics-2d.md">Física 2D</a>, <a href="audio/audio-system.md">Áudio</a>, <a href="animation/animation-2d.md">Animação 2D</a>, <a href="animation/skeletal-animation.md">Animação esquelética</a></td>
    </tr>
    <tr>
      <td><strong>Assets e terreno</strong></td>
      <td><a href="assets/asset-manager.md">Asset manager</a></td>
      <td><a href="assets/caf-format.md">Formato CAF</a>, <a href="assets/asset-pipeline.md">Pipeline de assets</a>, <a href="terrain/terrain-system.md">Sistema de terreno</a></td>
    </tr>
    <tr>
      <td><strong>Scripting</strong></td>
      <td><a href="scripting/scripting.md">Visão geral</a></td>
      <td><a href="scripting/runtime-apis.md">APIs de runtime</a>, <a href="api/scripting-components.md">Acesso genérico a componentes</a>, <a href="scripting/native-modules.md">Módulos nativos</a></td>
    </tr>
    <tr>
      <td><strong>Plugins</strong></td>
      <td><a href="plugins/README.md">Catálogo de plugins</a></td>
      <td><a href="plugins/writing-a-plugin.md">Escrever um plugin</a>, <a href="editor/plugin-manager.md">Plugin Manager</a>, <a href="editor/plugin-sdk.md">Plugin SDK</a></td>
    </tr>
    <tr>
      <td><strong>Referência</strong></td>
      <td><a href="api/README.md">Referência da API</a></td>
      <td><a href="architecture_specs.md">Especificações</a>, <a href="MASTER.md">Índice master</a>, <a href="HISTORY.md">História</a></td>
    </tr>
  </tbody>
</table>

## Estado da documentação

A árvore mistura **guias atuais** e **planos históricos**. Cada página começa com um
selo de estado:

| Selo | Significado |
|---|---|
| <span class="doc-badge doc-badge--stable">Stable</span> | Verificado contra o código atual; pode seguir. |
| <span class="doc-badge doc-badge--beta">Beta</span> | Implementado, mas ainda a mudar. |
| <span class="doc-badge doc-badge--reference">Reference</span> | Referência de API/módulo; confirme o header ligado. |
| <span class="doc-badge doc-badge--planned">Planned</span> | Apenas design; sem implementação atual. |
| <span class="doc-badge doc-badge--historical">Historical</span> | Mantido por contexto; não é API atual. |

Os planos em `plans/` são históricos, salvo indicação em contrário. Documentam
decisões e sessões, não o editor atual.

## Editar a documentação

O padrão de autoria é **Markdown HTML-first**:
[`DOCS_STYLE.md`](https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/DOCS_STYLE.md).
Cada página precisa de uma faixa `doc-meta`, figuras para capturas e links relativos
dentro da árvore de docs. Links para código usam URLs absolutos do GitHub.

```bash
cd caffeine-website
python3 scripts/audit-docs.py --include-engine
python3 scripts/audit-docs-i18n.py
```

As capturas são geradas pelo driver headless, nunca por um screenshot do desktop:

```bash
./scripts/capture-editor-docs.sh
```

## Referências

- Engine e Doppio: <https://github.com/devscafecommunity/caffeine>
- Plugins do editor: <https://github.com/devscafecommunity/doppio-plugins>
- Launcher: <https://github.com/devscafecommunity/caffeine-launcher>
- Asset packer: <https://github.com/devscafecommunity/caf-pack>
- Website e livros: este repositório (`content/`, `tex/`, `captures/`)
