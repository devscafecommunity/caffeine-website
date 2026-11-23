# 🎬 Animation System

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span><strong>Namespace:</strong> <code>Caffeine::Animation</code></span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/animation/AnimationSystem.hpp"><code>animation/AnimationSystem.hpp</code></a></span>
</div>

<p class="doc-lede">Sprite-sheet animation driven by an <code>Animator</code> state
machine: clips, parameters, transitions with crossfades, layers and frame events.</p>

---

## Overview

`AnimationSystem` advances every entity that has both `Animator` and `ECS::Sprite`:

- It evaluates transitions for the current state (and for every extra animator layer).
- It advances `timeInState` with the state speed and the animator's `playbackScale`.
- It computes the sprite frame from the clip's `fps` and writes `Sprite::frameIndex`.
- It fires `frameEvents` callbacks for the current frame.

Entities with an `Animator` but no `Sprite` are treated as skeletal characters; the
skeletal path is documented in [`animation/skeletal-animation.md`](../animation/skeletal-animation.md).

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

struct AnimationClip {
    FixedString<32>        name;
    u32                    fps    = 12;
    std::vector<FrameRect> frames;
    bool                   loop   = true;
    f32 duration() const;          // frames.size() / fps, or 0
};

enum class ParameterType : u8 { Bool, Float, Int, Trigger };

struct AnimatorParameter {
    FixedString<32> name;
    ParameterType   type = ParameterType::Bool;
    union { bool boolValue; f32 floatValue; i32 intValue; };
    bool triggered = false;
};

enum class ConditionOperator : u8 {
    Equals, NotEquals, Greater, Less, GreaterOrEqual, LessOrEqual
};

struct TransitionCondition {
    FixedString<32>   parameterName;
    ConditionOperator op = ConditionOperator::Equals;
    union { bool boolValue; f32 floatValue; i32 intValue; };
};

enum class KeyInterp : u8 { Linear, Constant, EaseIn, EaseOut, EaseInOut, Custom };

struct KeyCurve {
    KeyInterp mode = KeyInterp::Linear;
    f32 x1 = 0.33f, y1 = 0.33f, x2 = 0.67f, y2 = 0.67f;
};

// Transition target that leaves through Exit and re-enters at the default state.
inline constexpr const char* kAnimatorExitState = "Exit";

struct AnimationTransition {
    FixedString<32>                  toState;
    std::vector<TransitionCondition> conditions;   // all must match
    f32                              blendTime   = 0.1f;
    bool                             hasExitTime = false;
    f32                              exitTime    = 1.0f;  // normalized
    f32                              offset      = 0.0f;  // normalized start
    KeyCurve                         blendCurve;
    std::function<bool()>            legacyCondition;
};

struct AnimationState {
    FixedString<32>                  name;
    const AnimationClip*             clip  = nullptr;
    f32                              speed = 1.0f;
    std::vector<AnimationTransition> transitions;
    FixedString<32>                  motion;     // skeletal clip name
    f32                              editorX = 0.0f, editorY = 0.0f;
    bool                             hasEditorPosition = false;
};

struct AnimatorStateMachine {
    HashMap<FixedString<32>, AnimationState> states;
    FixedString<32>                          currentState;
    FixedString<32>                          previousState;
    FixedString<32>                          defaultState;
    f32                                      timeInState = 0.0f;
    std::vector<AnimationTransition>         anyStateTransitions;

    FixedString<32> fadeFromState;
    f32             fadeFromTime = 0.0f;
    f32             fadeElapsed  = 0.0f;
    f32             fadeDuration = 0.0f;
    KeyCurve        fadeCurve;

    bool fading() const;
};

enum class LayerBlendMode : u8 { Override, Additive };

enum class BodyMask : u32 {
    Root = 1u << 0, Body = 1u << 1, Head = 1u << 2,
    LeftArm = 1u << 3, RightArm = 1u << 4,
    LeftLeg = 1u << 5, RightLeg = 1u << 6,
    All = 0x7Fu
};

struct AnimatorLayer : AnimatorStateMachine {
    FixedString<32> name;
    FixedString<32> parentGroup;
    bool            isGroup  = false;
    bool            muted    = false;
    bool            expanded = true;
    f32             weight   = 1.0f;
    LayerBlendMode  blend    = LayerBlendMode::Override;
    u32             mask     = static_cast<u32>(BodyMask::All);
};

struct Animator : AnimatorStateMachine {
    std::vector<AnimationClip>                   embeddedClips;
    std::vector<AnimatorLayer>                   layers;
    f32                                          blendWeight   = 1.0f;
    f32                                          playbackScale = 1.0f;
    bool                                         paused        = false;
    std::vector<AnimatorParameter>               parameters;
    std::vector<std::pair<u32, FixedString<32>>> frameEvents;
    std::function<void(const FixedString<32>&)>  onFrameEvent;

    void addParameter(const char* name, ParameterType type);
    void setBool(const char* name, bool value);
    void setFloat(const char* name, f32 value);
    void setInt(const char* name, i32 value);
    void setTrigger(const char* name);
    bool getBool(const char* name) const;
    f32  getFloat(const char* name) const;
    i32  getInt(const char* name) const;
};

class AnimationSystem : public ECS::ISystem {
public:
    void onUpdate(ECS::World& world, f32 dt) override;

    static void stepStateMachine(Animator& anim, f32 dt, f32 stateDuration);
    static void stepStateMachine(Animator& anim, f32 dt, const StateDurationFn& durationOf);

    void play(ECS::World& world, ECS::Entity e, const char* stateName);
    void pause(ECS::World& world, ECS::Entity e);
    void resume(ECS::World& world, ECS::Entity e);
    void setSpeed(ECS::World& world, ECS::Entity e, f32 speed);
    bool isPlaying(ECS::World& world, ECS::Entity e, const char* stateName) const;

    void addParameter(ECS::World& world, ECS::Entity e, const char* name, ParameterType type);
    void setBool(ECS::World& world, ECS::Entity e, const char* name, bool value);
    void setFloat(ECS::World& world, ECS::Entity e, const char* name, f32 value);
    void setInt(ECS::World& world, ECS::Entity e, const char* name, i32 value);
    void setTrigger(ECS::World& world, ECS::Entity e, const char* name);
    bool getBool(ECS::World& world, ECS::Entity e, const char* name) const;
    f32  getFloat(ECS::World& world, ECS::Entity e, const char* name) const;
    i32  getInt(ECS::World& world, ECS::Entity e, const char* name) const;
};

}  // namespace Caffeine::Animation
```

`AnimationTransition` supports both models: named parameters in `conditions`, and the
older `std::function<bool()>` in `legacyCondition`. A transition with no conditions and
`hasExitTime = true` fires on normalized time alone.

---

## State Machine Visual

```text
idle ──[MoveX != 0]──► walk ──[MoveX == 0]──► idle
  │
  ├──[Jump trigger]──► jump_rise ──[exit 1.0]──► jump_fall
  │                                              │
  │                                              └──[exit 1.0]──► idle
  └──[Attack trigger]──► attack_1 ──[exit 1.0]──► attack_2 ──[exit 1.0]──► idle
```

`anyStateTransitions` are checked before the current state's own transitions, which is
useful for hit reactions and death.

---

## Smoothing and Transitions

```cpp
AnimationClip idleClip;
idleClip.name = "idle";
idleClip.fps  = 8;
idleClip.frames = { {0, 0, 64, 64}, {64, 0, 64, 64} };
idleClip.loop = true;

AnimationClip walkClip;
walkClip.name = "walk";
walkClip.fps  = 12;
walkClip.frames = { {128, 0, 64, 64}, {192, 0, 64, 64},
                    {256, 0, 64, 64}, {320, 0, 64, 64} };
walkClip.loop = true;

// Build the Animator in place; add returns a reference.
Animator& anim = world.add<Animator>(player);
anim.defaultState = "idle";

AnimationState idleState;
idleState.name = "idle";
idleState.clip = &idleClip;
idleState.transitions.push_back({
    .toState = "walk",
    .conditions = { { "MoveX", ConditionOperator::NotEquals, { .floatValue = 0.0f } } },
    .blendTime = 0.15f
});

AnimationState walkState;
walkState.name = "walk";
walkState.clip = &walkClip;
walkState.transitions.push_back({
    .toState = "idle",
    .conditions = { { "MoveX", ConditionOperator::Equals, { .floatValue = 0.0f } } },
    .blendTime = 0.15f
});

anim.states.set(FixedString<32>("idle"), idleState);
anim.states.set(FixedString<32>("walk"), walkState);
anim.addParameter("MoveX", ParameterType::Float);

// Drive the parameter from gameplay code.
AnimationSystem animSys;
animSys.setFloat(world, player, "MoveX", input.axisValue(Axis::MoveX));

// Fire a gameplay event when the attack clip reaches frame 3.
world.get<Animator>(player)->frameEvents.push_back({3u, FixedString<32>("attack_hit")});
world.get<Animator>(player)->onFrameEvent = [](const FixedString<32>& evt) {
    if (evt == FixedString<32>("attack_hit")) damageEnemiesInRange();
};

// The host calls onUpdate once per frame.
animSys.onUpdate(world, dt);
```

Clips referenced by `AnimationState::clip` must outlive the animator. Scenes loaded
from disk store their clips in `Animator::embeddedClips` and point states at those
entries.

---

## Design Decisions

| Decision | Justification |
|---------|-------------|
| State machine | Animation logic stays separate from gameplay logic |
| Named parameters and conditions | Serializable and editable in the timeline, unlike raw lambdas |
| `legacyCondition` | Keeps older C++ setups working without rebuilding their graphs |
| `blendTime` per transition | Crossfade is the default; `0` switches instantly |
| Exit time and offset | Normalized clip time is independent of clip length |
| Frame events | Gameplay can react to a specific sprite frame |
| Extra layers and body masks | Additive/override layers for upper-body actions and skeletal masks |
| No priority field | The host calls `onUpdate`; registration order is processing order |

---

## Acceptance Criteria

`tests/test_animation.cpp` covers:

- [x] Clip duration for zero frames, zero fps and normal clips
- [x] Transition and state defaults
- [x] Entities without `Sprite` or `Animator` are skipped without crashing
- [x] Paused animators do not advance time
- [x] Looping clips wrap and non-looping clips clamp at the last frame
- [x] Transitions fire only when their conditions match
- [x] Frame events fire on the correct frame
- [x] `play`, `pause`, `resume`, `setSpeed` and `isPlaying`

The suite does not assert a fixed frame budget; profile your own animation count.

---

## Dependencies

- **Upstream:** [ECS Core](../ecs/core.md), [Asset Manager](../assets/asset-manager.md)
- **Downstream:** [Skeletal Animation](../animation/skeletal-animation.md), sprite rendering

---

## 🔗 Related Topics

| Topic | Description |
|--------|-----------|
| [ECS Core](../ecs/core.md) | `World`, `Entity` and queries used by the system |
| [Rendering & Pipeline](../rendering/rhi.md) | How animated sprites reach the renderer |
| [Skeletal Animation](../animation/skeletal-animation.md) | 3D bones, imported clips and skinning |

## References

- [`src/caffeine/animation/AnimationComponents.hpp`](https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/animation/AnimationComponents.hpp) — clips, states and the animator
- [`src/caffeine/animation/AnimationSystem.hpp`](https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/animation/AnimationSystem.hpp) — update and transition logic
- [`tests/test_animation.cpp`](https://github.com/devscafecommunity/caffeine/blob/main/tests/test_animation.cpp) — behaviour suite
