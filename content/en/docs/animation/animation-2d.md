# 🎬 Animation System

> **Phase:** 4 — The Brain
> **Namespace:** `Caffeine::Animation`
> **Files:** `src/caffeine/animation/` (`AnimationComponents.hpp`, `AnimationSystem.hpp`, `Smoothing.hpp`, `Skeleton2D.hpp`, `Rig2DAsset.hpp`, `Rig2DSystem.hpp`)
> **Status:** Implemented for PhaseShift, smoothing and 2D rigs. Drawing 2D rigs through the batch renderer is in progress.

---

## Overview

Every animated entity can carry a **PhaseShift** component. It is the state machine formerly called `Animator`, renamed to match the engine's vocabulary. It reads and writes named parameters, and three kinds of pose consume them: sprite frames, 2D rigs (bones and skinned meshes in the Live2D style) and 3D skinned poses.

The rule: animation sources never touch bones or vertices. They write **parameters**, and the rig turns parameters into a pose.

---

## API

```cpp
namespace Caffeine::Animation {

// The state machine (formerly `Animator`). One per entity.
struct PhaseShift : PhaseShiftStateMachine {
    std::vector<PhaseShiftLayer>      layers;
    std::vector<PhaseShiftParameter>  parameters;
    std::vector<AnimationClip>        embeddedClips;
    f32  playbackScale = 1.0f;
    bool paused        = false;

    void addParameter(const char* name, ParameterType type);
    void setFloat(const char* name, f32 value);
    void setSmoothing(const char* name, f32 smoothTime);  // critically damped spring, 0 = off
    f32  getSmoothedFloat(const char* name) const;
};

// Float parameters can be smoothed. Conditions read `smoothed` when smoothTime > 0.
struct PhaseShiftParameter {
    FixedString<32> name;
    ParameterType   type;
    f32 floatValue;
    f32 smoothTime     = 0.0f;
    f32 smoothed       = 0.0f;
    f32 smoothVelocity = 0.0f;
};

// Live2D-style 2D rig: parameters drive bone channels, bones skin a mesh.
struct Rig2D {
    Skeleton2D                  skeleton;
    std::vector<Vertex2D>       vertices;
    std::vector<u32>            indices;
    std::vector<Parameter2D>    parameters;
    std::vector<ParamBinding2D> bindings;
};

std::vector<Vec2> skinMesh2D(const Rig2D& rig, const ParamValues2D& params);

}  // namespace Caffeine::Animation
```

## State Machine (PhaseShift)

A state is a clip plus transitions. A transition fires when its conditions hold on the parameters, and it blends into the target over `blendTime`. Exit time transitions wait for the current clip to reach a normalized time.

```text
  idle ──(speed > 0.5, smoothed 0.15 s)──► run
   ▲                                        │
   └──────────(speed <= 0.5)────────────────┘
  Exit   returns to the default state
```

---

## Smoothing and Transitions

`setSmoothing(name, seconds)` puts a float parameter on a critically damped spring. Conditions read the smoothed value, so a parameter that jumps from 0 to 1 still takes the chosen time to cross a threshold. The spring never overshoots. Smoothing is saved with the scene as an optional trailing section, so older scenes still load.

Blends between states use `blendCurve` (a `KeyCurve`): linear, ease in, ease out, ease in-out or a cubic Bezier.

---

## Parameters and 2D Rigs

A `Rig2D` has bones, a mesh of vertices with up to four bone weights each, a triangle list, named parameters and bindings. A binding adds a curve of offsets to one bone channel (rotation, translation or scale) as its parameter moves. Each tick the rig takes its parameters from the rig defaults, then from the parameter clip at the entity's time, then from the PhaseShift float parameters of the same name. The result is skinned into vertex positions in rig order.

Rigs and parameter clips are text files. Names have no spaces.

Sprites are drawn the same way. A `Sprite` component's `Name` is the image path, relative to the project root; an empty name draws a white quad. A `SpriteSheet` picks the frame by the `Sprite`'s `frameIndex`. A sprite is one world unit on its longer side, scaled by the entity's placement (its `Transform`, or its 2D components when it has no 3D ones).

```text
CAFRIG2D1                         rig header
bone  <name> <parent> <px> <py> <rotation> <sx> <sy>
vert  <px> <py> <u> <v> <n> [<bone> <weight>] x n
tri   <a> <b> <c>
param <name> <min> <default> <max>
bind  <parameter index> <bone> <channel> <n> [<x> <y>] x n

CAFPCLIP1                         parameter clip header
name <text>
loop <0|1>
duration <seconds>
track <parameter name> <n> [<time> <value>] x n
```

## Lua

The functions below are in the `caffeine.animation` table. Each returns `true` on success.

```lua
local e = caffeine.entity.create()
caffeine.component.add(e, "PhaseShift")
caffeine.animation.attachRig2D(e, "assets/hero.rig2d")
caffeine.animation.playRig2DClip(e, "assets/hero_blink.pclip")
caffeine.animation.setSmoothing(e, "Bend", 0.15)   -- seconds to reach the target
caffeine.animation.setFloat(e, "Bend", 1.0)        -- the rig's Bend parameter follows
```

---

## Design Decisions

| Decision | Rationale |
|---------|-------------|
| Parameters are the only interface | Sprites, rigs and skeletons can share one state machine |
| Critically damped smoothing | No overshoot, stable at any frame time |
| PhaseShift floats override by name | The rig defaults and clips give the base pose; a state can take over any parameter |
| Text asset formats | Diffable and reviewable in git, like `CAFANIM1` |

---

## Acceptance Criteria

- [x] Rig skinning is exact at the rest pose
- [x] Smoothed float gates a transition until the spring catches up
- [x] Rig and clip files round-trip, and out-of-range indices are rejected
- [ ] Rigs drawn in the viewport through the batch renderer (GPU path built, not yet run on a device)
- [x] Rig and PhaseShift panels bound to the engine through the C ABI (C ABI v22)

---

## Dependencies

- **Upstream:** [ECS Core](ecs.md), [Asset Manager](../assets/asset-manager.md) (clips and rigs are loaded from assets)
- **Downstream:** [Phase 5 — Skeletal Animation](../animation/skeletal-animation.md)

---

## 🔗 Related Topics

| Topic | Description |
|--------|-----------|
| [Game Systems]() | Animation System as an ECS system |
| [Rendering & Pipeline]() | Animated sprites and rigs drawn by the batch renderer |

## References

- [`animation/skeletal-animation.md`](../animation/skeletal-animation.md) — 3D skinned poses
- [`architecture_specs.md`](../architecture_specs.md) — §12 Animation System
- [Transversal Topic Index]()
