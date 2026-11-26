# Workspace, tema e componentes

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/doppio/crates/ui/src/uikit/theme.rs"><code>uikit/theme.rs</code></a></span>
</div>

<p class="doc-lede">Como o workspace Rust do Doppio é composto: o layout PaneGrid, o
kit de componentes Iced, os tokens visuais, e onde o kit legado C++ ainda se aplica.</p>

<figure class="doc-figure">
  <img src="../images/editor/workspace-scene.png" alt="Workspace do Doppio com hierarchy, viewport, inspector e painéis de assets em baixo" loading="lazy">
  <figcaption>O editor é uma janela dividida por um <code>PaneGrid</code>. Os painéis são funções de vista puras; os primitivos interativos vivem em <code>uikit/components/</code>.</figcaption>
</figure>

## Duas stacks de UI, um produto

<table class="doc-table">
  <thead>
    <tr><th>Stack</th><th>Usada por</th><th>Localização</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Rust / Iced</strong></td>
      <td>O editor Doppio ativo: docking, hierarchy, viewport, inspector, assets, console e geradores.</td>
      <td><code>doppio/crates/ui/</code></td>
    </tr>
    <tr>
      <td><strong>C++ / ImGui UIKit</strong></td>
      <td>O runtime autónomo, plugins legados e painéis do Doppio C++ arquivado.</td>
      <td><code>include/caffeine/ui/</code></td>
    </tr>
  </tbody>
</table>

As stacks partilham vocabulário visual, não código. Não descreva o editor Rust como
usando `Caffeine::UIKit`; o kit C++ só é carregado pelo runtime e pelos plugins.

## Janela → painel → componente

| Camada | Localização | Regra |
|---|---|---|
| **Janela** | `windows/main.rs` | Detém `App`, mensagens, subscrições e o `PaneGrid`. |
| **Painel** | `uikit/panels/*.rs` | `view(...) -> Element` pura; nunca chama `text_input`, `checkbox`, `slider` ou `button` diretamente. |
| **Componente** | `uikit/components/*.rs` | Primitivos reutilizáveis: botões, campos, cartões, tabs, menus, tree view, gizmo, viewport surface, node canvas. |

Os painéis compõem componentes. `scripts/check-rust-ui.sh` rejeita widgets crus em
`uikit/panels/`, o que mantém foco, hover, estados disabled e tema consistentes.

## Layout e docking

O `PaneGrid` padrão é construído a partir de quatro regiões:

1. **Hierarchy** à esquerda.
2. Um **grupo central** com Viewport, Material Generator, Texture Generator, Texture
   Set, Script e Dryad Nodes.
3. Um **grupo direito** com Inspector, Material, Nature, Water e Terrain.
4. Um **grupo inferior** com Assets e Console.

Arraste um separador pelo cabeçalho para mostrar os guias de docking: o centro
adiciona ao painel de destino, uma aresta divide o painel. Os botões maximizam e
restauram. Os presets estão no menu View:

| Preset | Atalho | Resultado |
|---|---|---|
| Default Layout | `Ctrl+1` | Hierarchy à esquerda, ferramentas ao centro/direita, Assets + Console em baixo |
| Viewport Layout | `Ctrl+2` | Dá a maior parte da janela ao viewport |

O layout Rust é estado de sessão; não é escrito em `workspace.json`. O
`Caffeine::Workspace` legado em ImGui continua a persistir
`~/.config/caffeine/ui/workspace.json` para o runtime e hosts de plugins.

## Tokens do tema

`doppio/crates/ui/src/uikit/theme.rs` é a única fonte de cores, bordas e espaçamento.
Os painéis não devem fixar cores.

<table class="doc-table">
  <thead>
    <tr><th>Token</th><th>Valor</th><th>Usado em</th></tr>
  </thead>
  <tbody>
    <tr><td><code>BACKGROUND</code></td><td><code>#151515</code></td><td>Janela e envolvência do viewport</td></tr>
    <tr><td><code>PANEL</code></td><td><code>#242424</code></td><td>Corpo dos painéis e cartões</td></tr>
    <tr><td><code>PANEL_ALT</code></td><td><code>#2e2e2e</code></td><td>Linhas alternadas e inputs</td></tr>
    <tr><td><code>TOOLBAR</code></td><td><code>#1e1e1e</code></td><td>Barras de tabs, menus e barra de estado</td></tr>
    <tr><td><code>BORDER</code></td><td><code>#313131</code></td><td>Contornos de painéis e campos</td></tr>
    <tr><td><code>TEXT</code></td><td><code>#d6d6d6</code></td><td>Labels e valores primários</td></tr>
    <tr><td><code>TEXT_MUTED</code></td><td><code>#8e8e8e</code></td><td>Labels secundários e dicas</td></tr>
    <tr><td><code>ACCENT</code></td><td><code>#4a8fe0</code></td><td>Seleção, foco e ferramentas ativas</td></tr>
    <tr><td><code>DANGER</code></td><td><code>#c24f4f</code></td><td>Eliminar, erros e ações destrutivas</td></tr>
    <tr><td><code>WARNING</code></td><td><code>#d1a03c</code></td><td>Avisos e estados pendentes</td></tr>
    <tr><td><code>SUCCESS</code></td><td><code>#5da56b</code></td><td>Estado gravado e verificações bem-sucedidas</td></tr>
  </tbody>
</table>

As barras de identidade dos geradores usam a paleta de ícones: ciano para Material,
laranja para Texture e Terrain, verde para Nature, azul-ciano para Water.

## Ids de widgets estáveis

Cada widget interativo tem um `UiId` hierárquico
(`editor.menu.scene`, `inspector.entity.name`, `hierarchy.list.entity_row.3`) e uma
entrada em `uikit::id::CATALOG` com tipo e descrição. O catálogo alimenta:

- o targeting headless e as capturas anotadas;
- a [referência de UI](ui-reference.md) gerada;
- as ações dos agentes e as legendas em `captures/ui-captions.json`.

Adicione um id e uma entrada no catálogo com cada widget novo.

## Kit C++ legado (runtime e plugins)

`include/caffeine/ui/` ainda fornece `Theme`, `Widgets`, `Icons`, `PanelRegistry` e
`Workspace` para `caffeine-runtime` e plugins C++. É ImGui em modo imediato, não
Iced. Os painéis de plugins usam `caffeine/plugin/PluginUI.hpp` e os mesmos ids do
`PanelRegistry`; o layout é persistido pelo `Workspace` em
`~/.config/caffeine/ui/workspace.json`.

<div class="doc-callout doc-callout--note">
  <p><strong>Nota.</strong> O editor C++ arquivado em <code>doppio-archived/</code>
  também usava este kit. É código de referência congelado e não faz parte do editor
  ativo.</p>
</div>
