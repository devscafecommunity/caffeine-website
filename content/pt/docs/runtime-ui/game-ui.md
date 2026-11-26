# 🖼️ UI System

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span><strong>Namespace:</strong> <code>Caffeine::UI</code></span>
  <span>Atualizado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/ui/UISystem.hpp"><code>ui/UISystem.hpp</code></a></span>
</div>

<p class="doc-lede">UI retained-mode sobre ECS para HUDs e menus de jogo: os widgets são
entidades, o layout resolve retângulos de âncoras em cada frame e bindings de valor
podem conduzir progress bars e sliders a partir do estado do jogo.</p>

---

## Visão Geral

A UI de jogo é **retained mode**: widgets são entidades ECS com um componente
`UIWidget` mais um componente específico (`UIButton`, `UILabel`, …). Em cada frame o
`UISystem`:

1. Corre os bindings de valor e escreve `UIProgressBar::currentValue` / `UISlider::currentValue`.
2. Resolve os offsets das âncoras em `UIWidget::computedRect` (até 8 passagens).
3. Faz hit-test do rato, dispara callbacks de hover/click e atualiza o estado dos botões.

Esta é a UI de jogo em runtime. O editor Doppio usa componentes Rust/Iced, não este
sistema; o host ImGui legado está documentado em [ImGui host](../runtime-ui/editor-ui.md).

---

## Componentes

### `UIColor`

Cor RGBA com canais `f32` em `[0, 1]`. Presets estáticos: `white()`, `black()`,
`transparent()`, `red()`, `green()`, `blue()`.

### `UIRect`

Retângulo de ecrã com `position` e `size` (`Vec2`). Métodos: `contains(Vec2)`,
`isValid()` (verdadeiro quando ambas as componentes de `size` são positivas).

### `RectTransform`

Layout relativo ao parent. `anchorMin` / `anchorMax` são frações do tamanho do parent;
`offsetMin` / `offsetMax` são deltas em píxeis a partir desses cantos.

```mermaid
stateDiagram-v2
  anchorMin=anchorMax={0,0}, offsetMin={px,py}, offsetMax={px+w,py+h} --> widget fixo em (px,py) tamanho (w,h)
```

### `UIStyle`

Aparência visual: `backgroundColor`, `textColor`, `borderColor`, `borderWidth`,
`borderRadius`, `fontSize`, `textAlignment` (um `Vec2` em `[0, 1]`).

### `UIWidget`

Componente base presente em todas as entidades de UI:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `type` | `UIWidgetType` | Canvas, Panel, Button, Label, ProgressBar, Checkbox, Slider |
| `parentId` | `u32` | Id do parent; `kUIInvalidParent` para um canvas raiz |
| `visible` | `bool` | Se falso, não é disposto nem devolvido por `hitTest` |
| `interactable` | `bool` | Se falso, `hitTest` ignora-o |
| `siblingOrder` | `i32` | Valor maior vence quando dois widgets se sobrepõem |
| `style` | `UIStyle` | Cores, bordo e tamanho de fonte |
| `transform` | `RectTransform` | Âncoras e offsets usados pelo layout |
| `computedRect` | `UIRect` | Preenchido em cada frame por `layoutWidgets()` |
| `onClick` | `std::function<void(Entity)>` | Disparado ao clicar |
| `onHoverEnter` | `std::function<void(Entity)>` | Disparado quando o rato entra |
| `onHoverExit` | `std::function<void(Entity)>` | Disparado quando o rato sai |
| `onValueChanged` | `std::function<void(Entity, f32)>` | Disparado por `bindValue` |

### Componentes específicos

| Struct | Campos relevantes |
|--------|-------------------|
| `UIButton` | `labelText` (`FixedString<64>`), `idleColor`, `hoverColor`, `pressedColor`, `isHovered`, `isPressed` |
| `UILabel` | `text` (`FixedString<256>`), `wordWrap` |
| `UIProgressBar` | `minValue`, `maxValue`, `currentValue`, `showText`, `fillColor` |
| `UISlider` | `minValue`, `maxValue`, `currentValue`, `snapToInt` |
| `UICheckbox` | `checked`, `checkedColor` |

---

## API — `UISystem`

```cpp
namespace Caffeine::UI {

class UISystem : public ECS::ISystem {
public:
    explicit UISystem(Events::EventBus* eventBus = nullptr);

    void onUpdate(ECS::World& world, f32 dt) override;
    void layout(ECS::World& world);   // resolve rects without consuming input

    ECS::Entity createCanvas(ECS::World& world, Vec2 size = {1280.0f, 720.0f});
    ECS::Entity createPanel(ECS::World& world, u32 parentId, UIRect rect);
    ECS::Entity createButton(ECS::World& world, u32 parentId, const char* text,
                             Vec2 pos, Vec2 size = {120.0f, 40.0f});
    ECS::Entity createLabel(ECS::World& world, u32 parentId, const char* text, Vec2 pos);
    ECS::Entity createProgressBar(ECS::World& world, u32 parentId,
                                  Vec2 pos, Vec2 size = {200.0f, 20.0f});
    ECS::Entity createSlider(ECS::World& world, u32 parentId,
                             Vec2 pos, Vec2 size = {200.0f, 20.0f});
    ECS::Entity createCheckbox(ECS::World& world, u32 parentId, Vec2 pos);

    void bindValue(ECS::Entity widget, std::function<f32(ECS::World&)> getter);

    ECS::Entity hitTest(ECS::World& world, Vec2 screenPos);

    void injectMousePosition(Vec2 pos);
    void injectMouseClick(bool pressed);
};

}  // namespace Caffeine::UI
```

`bindValue` atualiza um `UIProgressBar` ou um `UISlider`; os outros tipos de widget são
ignorados. A lista de bindings vive na instância do `UISystem`, não no componente, pelo
que não é serializada.

---

## Hierarquia de Widgets

- `Canvas (raiz)`
  - `Panel (HUD)`
    - `ProgressBar (health) ← bindValue → devolve Health.current`
    - `Label (score)`
    - `Label (fps counter)`
  - `Panel (inventory)`
    - `[slots criados dinamicamente]`
  - `Panel (pause menu — visible=false por omissão)`
  - `Button "Resume"`
  - `Button "Options"`
  - `Button "Quit"`

Um painel também pode ser parent de um widget através de `Scene::Parent` quando
`parentId` é `kUIInvalidParent`; nesse caso `layoutWidgets` recorre à hierarquia da
cena.

---

## Exemplo de Uso

```cpp
UISystem uiSys;

Entity canvas   = uiSys.createCanvas(world, {1280.0f, 720.0f});
Entity hudPanel = uiSys.createPanel(world, canvas.id(), {{0, 0}, {1280, 720}});

Entity healthBar = uiSys.createProgressBar(world, hudPanel.id(), {20.0f, 700.0f}, {200.0f, 20.0f});
world.get<UIProgressBar>(healthBar)->fillColor = {0.9f, 0.2f, 0.2f, 1.0f};

uiSys.bindValue(healthBar, [&](ECS::World& w) {
    return static_cast<f32>(w.get<Health>(playerEntity)->current);
});

Entity scoreLabel = uiSys.createLabel(world, hudPanel.id(), "Score: 0", {1100.0f, 700.0f});

Entity playBtn = uiSys.createButton(world, canvas.id(), "Play Game", {640.0f, 360.0f}, {200.0f, 50.0f});
world.get<UIWidget>(playBtn)->onClick = [&](ECS::Entity) {
    sceneManager.switchScene("assets/scenes/level1.caf");
};

// Once per frame: bindings, layout, input.
uiSys.injectMousePosition(mousePos);
uiSys.injectMouseClick(isMouseDown);
uiSys.onUpdate(world, dt);
```

`Health::current` é `u32`; o getter devolve `f32`, por isso faz o cast.

---

## Decisões de Design

| Decisão | Justificativa |
|---------|-------------|
| Retained mode | A UI persiste entre frames sem reconstrução |
| Widgets como entidades ECS | A UI pode ser consultada e afetada por sistemas |
| `bindValue` com getter `f32` | Evita reflexão em C++; suficiente para progress bars e sliders |
| `UIColor` com `f32` | O `Scene::Color` da engine usa `u8`; a UI quer precisão float |
| Até 8 passagens de layout | `forEach` não garante ordem topológica, por isso hierarquias profundas assentam ao longo de passagens |
| `kUIInvalidParent = 0xFFFFFFFFu` | Sentinela compatível com ids `u32` |
| Sem serialização no `UISystem` | Bindings são código, não dados de cena; os componentes dos widgets são serializados pelo serializador de cenas |

---

## Critério de Aceitação

`tests/test_ui.cpp` cobre:

- [x] Presets e igualdade de `UIColor`
- [x] `UIRect::contains` dentro, fora e na borda; `isValid`
- [x] Defaults de `UIWidget`, `UIButton`, `UILabel`, `UIProgressBar`, `UISlider` e `UICheckbox`
- [x] `createCanvas`, `createPanel`, `createButton`, `createLabel`, `createProgressBar` e `createSlider` devolvem entidades válidas com os componentes esperados
- [x] `onUpdate` num world vazio e com vários canvases não faz crash
- [x] `hitTest` devolve o widget sob o ponto; `INVALID` sem widgets ou fora de todos os retângulos
- [x] Widgets com `visible = false` não são devolvidos por `hitTest`
- [x] `onClick` dispara dentro do widget e não fora
- [x] `onHoverEnter` dispara quando o rato entra
- [x] `bindValue` atualiza `UIProgressBar::currentValue`

---

## Dependências

- **Upstream:** [ECS Core](../ecs/core.md), [Event Bus](../core/events.md)
- **Downstream:** HUDs e menus de jogo; o editor Doppio usa Iced, não este sistema

---

## 🔗 Tópicos Relacionados

| Tópico | Descrição |
|--------|-----------|
| [ImGui host](../runtime-ui/editor-ui.md) | O host immediate-mode legado usado pelo runtime e por plugins antigos |
| [Workspace and theme](../editor/workspace-and-theme.md) | A UI do editor em Rust/Iced |
| [ECS Core](../ecs/core.md) | Componentes e queries |

## Referências

- [`src/caffeine/ui/UIComponents.hpp`](https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/ui/UIComponents.hpp) — componentes dos widgets
- [`src/caffeine/ui/UISystem.hpp`](https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/ui/UISystem.hpp) — layout, input e bindings
- [`tests/test_ui.cpp`](https://github.com/devscafecommunity/caffeine/blob/main/tests/test_ui.cpp) — suite de comportamento
