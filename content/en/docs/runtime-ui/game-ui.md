# 🖼️ UI System

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span><strong>Namespace:</strong> <code>Caffeine::UI</code></span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/ui/UISystem.hpp"><code>ui/UISystem.hpp</code></a></span>
</div>

<p class="doc-lede">A retained-mode, ECS-backed UI for in-game HUDs and menus: widgets
are entities, layout resolves anchor rects each frame, and value bindings can drive
progress bars and sliders from game state.</p>

---

## Overview

The game UI is **retained mode**: widgets are ECS entities with a `UIWidget` component
plus a widget-specific component (`UIButton`, `UILabel`, …). Every frame `UISystem`:

1. Runs value bindings and writes `UIProgressBar::currentValue` / `UISlider::currentValue`.
2. Resolves anchor offsets into `UIWidget::computedRect` (up to 8 passes).
3. Hit-tests the mouse, fires hover/click callbacks and updates button state.

This is the runtime game UI. The Doppio editor uses Rust/Iced components, not this
system; the legacy ImGui host is documented in [ImGui host](../runtime-ui/editor-ui.md).

---

## Componentes

### `UIColor`

RGBA colour with `f32` channels in `[0, 1]`. Static presets: `white()`, `black()`,
`transparent()`, `red()`, `green()`, `blue()`.

### `UIRect`

Screen rectangle with `position` and `size` (`Vec2`). Methods: `contains(Vec2)`,
`isValid()` (true when both size components are positive).

### `RectTransform`

Layout relative to the parent. `anchorMin` / `anchorMax` are fractions of the parent
size; `offsetMin` / `offsetMax` are pixel deltas from those anchor corners.

```mermaid
stateDiagram-v2
  anchorMin=anchorMax={0,0}, offsetMin={px,py}, offsetMax={px+w,py+h} --> widget fixo em (px,py) tamanho (w,h)
```

### `UIStyle`

Visual appearance: `backgroundColor`, `textColor`, `borderColor`, `borderWidth`,
`borderRadius`, `fontSize`, `textAlignment` (a `Vec2` in `[0, 1]`).

### `UIWidget`

Base component present on every UI entity:

| Field | Type | Description |
|-------|------|-------------|
| `type` | `UIWidgetType` | Canvas, Panel, Button, Label, ProgressBar, Checkbox, Slider |
| `parentId` | `u32` | Parent id; `kUIInvalidParent` for a root canvas |
| `visible` | `bool` | If false, it is not laid out or returned by `hitTest` |
| `interactable` | `bool` | If false, `hitTest` ignores it |
| `siblingOrder` | `i32` | Higher value wins when two widgets overlap |
| `style` | `UIStyle` | Colours, border and font size |
| `transform` | `RectTransform` | Anchors and offsets used by layout |
| `computedRect` | `UIRect` | Filled every frame by `layoutWidgets()` |
| `onClick` | `std::function<void(Entity)>` | Fired on click |
| `onHoverEnter` | `std::function<void(Entity)>` | Fired when the mouse enters |
| `onHoverExit` | `std::function<void(Entity)>` | Fired when the mouse leaves |
| `onValueChanged` | `std::function<void(Entity, f32)>` | Fired by `bindValue` |

### Specific components

| Struct | Relevant fields |
|--------|-----------------|
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

`bindValue` updates a `UIProgressBar` or a `UISlider`; other widget types are ignored.
The binding list lives in the `UISystem` instance, not in the component, so it is not
serialized.

---

## Hierarquia de Widgets

- `Canvas (root)`
  - `Panel (HUD)`
    - `ProgressBar (health) ← bindValue → returns Health.current`
    - `Label (score)`
    - `Label (fps counter)`
  - `Panel (inventory)`
    - `[slots criados dinamicamente]`
  - `Panel (pause menu — visible=false por omissão)`
  - `Button "Resume"`
  - `Button "Options"`
  - `Button "Quit"`

A panel can also parent a widget through `Scene::Parent` when `parentId` is
`kUIInvalidParent`; `layoutWidgets` falls back to the scene hierarchy in that case.

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

`Health::current` is a `u32`; the getter returns `f32`, so cast it.

---

## Design Decisions

| Decision | Justification |
|---------|-------------|
| Retained mode | UI persists between frames without reconstruction |
| Widgets as ECS entities | UI can be queried and affected by systems |
| `bindValue` with an `f32` getter | Avoids C++ reflection; enough for progress bars and sliders |
| `UIColor` with `f32` | The engine's `Scene::Color` uses `u8`; UI wants float precision |
| Up to 8 layout passes | `forEach` does not guarantee topological order, so deep hierarchies settle over passes |
| `kUIInvalidParent = 0xFFFFFFFFu` | Sentinel compatible with `u32` ids |
| No serialization in `UISystem` | Bindings are code, not scene data; widget components are serialized by the scene serializer |

---

## Acceptance Criteria

`tests/test_ui.cpp` covers:

- [x] `UIColor` presets and equality
- [x] `UIRect::contains` inside, outside and on the edge; `isValid`
- [x] Defaults for `UIWidget`, `UIButton`, `UILabel`, `UIProgressBar`, `UISlider` and `UICheckbox`
- [x] `createCanvas`, `createPanel`, `createButton`, `createLabel`, `createProgressBar` and `createSlider` return valid entities with the expected components
- [x] `onUpdate` on an empty world and with multiple canvases does not crash
- [x] `hitTest` returns the widget under the point; `INVALID` with no widgets or outside every rect
- [x] `visible = false` widgets are not returned by `hitTest`
- [x] `onClick` fires inside the widget and not outside
- [x] `onHoverEnter` fires when the mouse enters
- [x] `bindValue` updates `UIProgressBar::currentValue`

---

## Dependencies

- **Upstream:** [ECS Core](../ecs/core.md), [Event Bus](../core/events.md)
- **Downstream:** game HUDs and menus; the Doppio editor uses Iced, not this system

---

## 🔗 Related Topics

| Topic | Description |
|--------|-----------|
| [ImGui host](../runtime-ui/editor-ui.md) | The legacy immediate-mode host used by the runtime and old plugins |
| [Workspace and theme](../editor/workspace-and-theme.md) | The Rust/Iced editor UI |
| [ECS Core](../ecs/core.md) | Components and queries |

## References

- [`src/caffeine/ui/UIComponents.hpp`](https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/ui/UIComponents.hpp) — widget components
- [`src/caffeine/ui/UISystem.hpp`](https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/ui/UISystem.hpp) — layout, input and bindings
- [`tests/test_ui.cpp`](https://github.com/devscafecommunity/caffeine/blob/main/tests/test_ui.cpp) — behaviour suite
