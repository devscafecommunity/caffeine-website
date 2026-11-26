# Host ImGui (runtime e plugins legados)

<div class="doc-meta">
  <span class="doc-badge doc-badge--reference">Reference</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Legacy</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/apps/runtime/ImGuiIntegration.hpp"><code>apps/runtime/ImGuiIntegration.hpp</code></a></span>
</div>

<p class="doc-lede">O Dear ImGui deixou de ser a UI do editor Doppio. Continua a ser o
host imediato do <code>caffeine-runtime</code> e do SDK legado de plugins C++. O editor
ativo é Rust/Iced.</p>

<div class="doc-callout doc-callout--warning">
  <p><strong>Não construa painéis novos de editor em ImGui.</strong> O editor Rust usa
  <a href="../editor/workspace-and-theme.md">componentes Iced</a>. Painéis ImGui são
  para o runtime autónomo e plugins que ainda usam o SDK C++.</p>
</div>

## Dois modelos de UI

<table class="doc-table">
  <thead>
    <tr><th>Modelo</th><th>Usado por</th><th>Onde</th></tr>
  </thead>
  <tbody>
    <tr><td>Retida, Iced</td><td>Editor Doppio: docking, hierarchy, inspector, viewport, assets, console, geradores</td><td><code>doppio/crates/ui/</code></td></tr>
    <tr><td>Imediata, Dear ImGui</td><td><code>caffeine-runtime</code>, Doppio C++ arquivado, plugins legados</td><td><code>apps/runtime/</code>, <code>include/caffeine/ui/</code>, <code>doppio-archived/</code></td></tr>
    <tr><td>UI de jogo retida</td><td>HUD e menus in-game</td><td><code>src/caffeine/ui/</code>, <a href="game-ui.md">Game UI</a></td></tr>
  </tbody>
</table>

## Integração no runtime

`apps/runtime/ImGuiIntegration.hpp` detém o backend ImGui SDL3 + RHI usado pelo
executável de runtime:

- `init(window, device)` — cria o contexto ImGui e os dados do backend.
- `beginFrame()` / `endFrame(commandBuffer)` — grava o draw data no RHI.
- `processEvent(SDL_Event)` — encaminha input SDL.
- `wantsKeyboard()` / `wantsMouse()` — diz ao runtime se o ImGui capturou o input.

O runtime desenha profiler, console e overlays de cena através deste host. O core
(`caffeine-core`) não tem dependência de ImGui; os adaptadores vivem em
`caffeine-editor-support` e no runtime.

## UIKit para plugins

Plugins C++ desenham com o kit imediato público em `include/caffeine/ui/`:

| Header | Conteúdo |
|---|---|
| `UI.hpp` | Umbrella do kit de elementos composáveis |
| `Widgets.hpp` | Botões, linhas de propriedades, cabeçalhos, empty states |
| `Theme.hpp` | Paleta e métricas |
| `Icons.hpp` | Glifos vetoriais |
| `PanelRegistry.hpp` | Ids estáveis e categorias de painéis |
| `Workspace.hpp` | Layout de docking JSON para o host de plugins |
| `Panel.hpp` | Descritores de painel |

Os painéis de plugins chamam `Caffeine::UIKit` e registam-se via `PanelRegistry`; não
ligam contra internals do Doppio. Veja [Plugin SDK](../editor/plugin-sdk.md).

## Profiler e console

As janelas de profiler e console são ferramentas do runtime/editor legado. Consomem
dados de `Debug::Profiler` e `Debug::LogSystem`; o editor Rust tem o seu próprio painel
Console tipado e não embebe ImGui.

## Páginas relacionadas

- [Workspace, tema e componentes](../editor/workspace-and-theme.md)
- [Game UI](game-ui.md)
- [Plugin SDK](../editor/plugin-sdk.md)
- [Debug tools](../debug/debug-tools.md)
