# Índice master

<div class="doc-meta">
  <span class="doc-badge doc-badge--reference">Reference</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">Um ponto de entrada único para a árvore de documentação. O índice
funcional com descrições vive em <a href="README.md">README.md</a>; esta página mantém
o antigo ponto de entrada “master” e resume a arquitetura atual.</p>

<div class="doc-callout doc-callout--note">
  <p><strong>Material histórico.</strong> <a href="HISTORY.md">HISTORY.md</a> e as
  páginas em <code>plans/</code> registam como o projeto chegou aqui. Não são
  documentação da API atual. Para o editor atual, comece em
  <a href="editor/scene-editor.md">Editor de cena</a>.</p>
</div>

## Arquitetura num relance

<table class="doc-table">
  <thead>
    <tr><th>Camada</th><th>O que é</th><th>Onde</th></tr>
  </thead>
  <tbody>
    <tr><td>GPU API</td><td>Vulkan, D3D12 ou Metal através do SDL3 GPU</td><td>Drivers da plataforma</td></tr>
    <tr><td>Core do motor</td><td>Runtime, render, RHI, ECS, assets, física, scripting. Sem ImGui, sem estado do editor.</td><td><code>src/caffeine/</code></td></tr>
    <tr><td>C ABI</td><td>Fronteira estável para qualquer frontend; versionada em <code>CAFFEINE_CAPI_VERSION</code>.</td><td><code>include/caffeine/capi/EngineAPI.h</code>, <code>src/caffeine/capi/</code></td></tr>
    <tr><td>Bridge do motor</td><td>Bindings Rust com <code>libloading</code>; a única crate que toca FFI.</td><td><code>doppio/crates/engine/</code></td></tr>
    <tr><td>UI do Doppio</td><td>Workspace Iced, painéis, componentes e geradores.</td><td><code>doppio/crates/ui/</code></td></tr>
    <tr><td>Plugins</td><td>Ferramentas C++/ImGui opcionais compiladas do submódulo.</td><td><code>doppio-plugins/</code>, <code>include/caffeine/plugin/</code></td></tr>
  </tbody>
</table>

## Pontos de entrada principais

| Necessidade | Página |
|---|---|
| Compilar e executar | [Começar](getting-started/README.md) |
| Aprender o editor | [Editor de cena](editor/scene-editor.md) |
| Visita visual | [Galeria de UI](editor/ui-gallery.md) |
| Materiais | [Editor de materiais](editor/material-editor.md) |
| Pipeline de render | [RHI](rendering/rhi.md), [Materiais PBR](rendering/materials-pbr.md) |
| ECS e cenas | [ECS core](ecs/core.md), [Scene manager](ecs/scene.md) |
| Scripting | [Visão geral](scripting/scripting.md) |
| C ABI e APIs | [Referência da API](api/README.md) |
| Testes headless | [Referência do driver](doppio/headless-testing.md) |
| História do projeto | [História](HISTORY.md) |

## Mapa do repositório

| Caminho | Conteúdo |
|---|---|
| `src/caffeine/` | Core do motor |
| `include/caffeine/` | Headers públicos (C API, plugins, UI kit, runtime) |
| `apps/` | Executáveis `caffeine-runtime` e `caffeine-combined` |
| `doppio/` | Workspace do editor Rust |
| `doppio-archived/` | Snapshot congelado do editor C++ (só referência) |
| `tests/` | Suites Catch2 |
| `caf-pack/` | Submódulo do asset packer |
| `doppio-plugins/` | Submódulo de plugins |
| `caffeine-website/` | Esta árvore de documentação |

## Padrões de documentação

- Markdown HTML-first: [`DOCS_STYLE.md`](https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/DOCS_STYLE.md).
- Páginas atuais usam `Stable`, `Beta` ou `Reference`; planos usam `Historical`.
- Links para código usam URLs absolutos do GitHub; imagens vivem em `images/`.
- Corra as duas auditorias antes de publicar:

```bash
cd caffeine-website
python3 scripts/audit-docs.py --include-engine
python3 scripts/audit-docs-i18n.py
```
