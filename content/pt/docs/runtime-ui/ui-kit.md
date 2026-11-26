# UI kit composável

<div class="doc-meta">
  <span class="doc-badge doc-badge--reference">Reference</span>
  <span>Last updated: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">O kit imediato C++ composável usado pelo runtime e plugins legados.</p>

Este kit pertence ao **runtime e ao host C++/ImGui legado**, não ao Doppio Rust
ativo. Um painel é uma árvore de objetos, cards e controlos; os plugins usam o
mesmo modelo para os seus painéis parecerem nativos do host. O editor Rust usa
componentes Iced e `uikit/theme.rs`.

<figure class="doc-figure">
  <img src="../images/captures/ui-gallery-elements.png" alt="UI Gallery com cards, controlos, texto, progresso e property rows" loading="lazy">
  <figcaption>UI Gallery com cards, controlos, texto, progresso e property rows</figcaption>
</figure>


## Objetos → Cards → Painéis

```
Painel
  └─ Card
       ├─ Toolbar
       │    ├─ Button
       │    └─ IconButton
       ├─ Row
       │    ├─ Card
       │    │    ├─ Label
       │    │    └─ SliderFloat
       │    └─ Card
       │         └─ Canvas
       ├─ PropertyGrid
       └─ NodeCanvasView
            └─ NodeElement
                 ├─ InputPin
                 └─ OutputPin
```

- **Objetos** são folhas: botão, slider, label, checkbox, combo, canvas, node,
  pin, barra de progresso, badge, texto.
- **Cards** agrupam objetos numa superfície elevada: `Card`, `Row`, `Column`,
  `Grid`, `Section`, `Toolbar`, `ScrollArea`.
- **Painéis** são janelas dockáveis: `Panel`, `TabPage`, `NodeCanvasView`,
  `PropertyGrid`.
- **App shells** (`PanelRegistry`, `Workspace`, `PluginManager`) são donos dos
  painéis e do docking; nunca desenham controlos à mão.

O kit é **header-only** (`caffeine/ui/UI.hpp`), por isso os plugins podem compor
os mesmos elementos sem ligar a IDE. Por baixo, cada elemento continua a desenhar
com ImGui; a árvore dá ids estáveis, layout, debug e uma linguagem visual única.

## Elementos principais

| Grupo | Elementos |
|-------|-----------|
| Contentores | `Panel`, `Card`, `Row`, `Column`, `Grid`, `Section`, `Toolbar`, `ScrollArea`, `TabBar` / `TabPage` |
| Controlos | `Button`, `IconButton`, `Checkbox`, `SliderFloat`, `SliderInt`, `DragFloat`, `DragInt`, `Combo`, `TextInput`, `SearchField`, `PathField`, `MultilineText`, `DropZone`, `ColorPicker`, `SegmentedControl` |
| Listas e dados | `ListItem`, `ListBox`, `AssetCard`, `DataTable` / `DataRow` |
| Display | `Label` / `Text`, `Paragraph`, `Badge`, `StatusDot`, `ProgressBar`, `Separator`, `Spacer`, `Image`, `EmptyState`, `KeyValue` |
| Propriedades | `PropertyGrid`, `PropertyRow`, `FloatProperty`, `IntProperty`, `BoolProperty`, `ChoiceProperty`, `ColorFieldProperty`, `Color3FieldProperty`, `TextFieldProperty`, `PathProperty`, `Vec2Property`, `Vec3Property` |
| Canvas / nodes | `Canvas`, `CurveEditor`, `NodeCanvasView`, `NodeElement`, `InputPin`, `OutputPin` |
| Overlays | `Dialog` (modal body tree), `CustomElement` (escape hatch para widgets do host/legado) |
| Debug | `UIContext::debugDump()`, `UIContext::drawDebugOverlay()`, `DebugPanel` |

## Exemplo

```cpp
#include "caffeine/ui/UI.hpp"

using namespace Caffeine::UIKit;
using namespace Caffeine::UIKit::Elements;

Panel panel("My Tool", "Short description", "effects");
auto& card = panel.emplace<Card>("General");
card.emplace<Label>("Options", TextTone::Accent).setHeading(true);

auto& row = card.emplace<Row>("Actions");
row.emplace<Button>("Apply", ButtonVariant::Primary).setOnClick([&] { apply(); });
row.emplace<Button>("Cancel");

auto& grid = card.emplace<PropertyGrid>("Settings");
grid.typedRow<FloatProperty>("Amount", amount, 0.0f, 1.0f, 0.01f, "%.2f", true);
grid.typedRow<BoolProperty>("Enabled", enabled);

UIContext ctx;
ctx.draw(panel);
```

Um `Row` divide o espaço restante pelos filhos com `setGrow(true)`; um `Card`
adapta-se ao conteúdo; um `PropertyGrid` é uma tabela de duas colunas de
`PropertyRow`s.

## Canvas e nodes

`Canvas` dá um callback de desenho com a origem e o tamanho da superfície. Serve
para previews, grafos, timelines ou qualquer visual que deva participar no layout
dos elementos.

`NodeCanvasView` embebe o `NodeCanvas` partilhado e é dono de uma lista de
`NodeElement`s. Cada node é dono do corpo, incluindo `InputPin`/`OutputPin` e
controlos normais. As ligações e a semântica do grafo ficam na ferramenta host.

## Catálogo vivo

Abre **View → Panels → UI Gallery** (ou o comando `UI Gallery`). O painel mostra
todos os elementos em contexto: botões, inputs, tons de texto, badges, progresso,
property rows, um canvas, um node canvas e a árvore de debug.

Ativa **Draw hit rectangles** no card de Debug para ver os bounds e ids de cada
elemento. `UIContext::debugDump()` devolve a mesma informação em texto, útil em
testes e relatórios de bugs.

## Regras

1. Uma folha desenha uma coisa; um contentor é dono do layout.
2. Usa tokens do tema, nunca cores hard-coded.
3. Dá ids explícitos a listas dinâmicas; irmãos estáticos podem ser numerados
   automaticamente.
4. Mantém lógica de grafo/ligações/serialização no host, não no `NodeElement`.
5. Migra uma peça de cada vez: os widgets de função antigos continuam suportados
   e são o vocabulário de baixo nível por baixo dos elementos.

Os headers estão em
[`include/caffeine/ui/`](https://github.com/devscafecommunity/caffeine/tree/main/include/caffeine/ui).
Este kit é o vocabulário legado do SDK de plugins ImGui. O editor Doppio ativo é
Rust/Iced e consome a C ABI; ver as
[notas da UI Rust](https://github.com/devscafecommunity/caffeine-website/blob/main/content/en/docs/doppio/rust-ui.md).
