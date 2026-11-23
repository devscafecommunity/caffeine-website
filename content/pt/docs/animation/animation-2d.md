# 🎬 Sistema de Animação

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span><strong>Namespace:</strong> <code>Caffeine::Animation</code></span>
  <span>Atualizado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/animation/AnimationSystem.hpp"><code>animation/AnimationSystem.hpp</code></a></span>
</div>

<p class="doc-lede">Animação de sprite sheets conduzida por uma state machine
<code>Animator</code>: clipes, parâmetros, transições com crossfade, camadas e frame
events.</p>

---

## Visão Geral

`AnimationSystem` avança todas as entidades que têm `Animator` e `ECS::Sprite`:

- Avalia transições do estado atual (e de cada camada extra do animator).
- Avança `timeInState` com a velocidade do estado e o `playbackScale` do animator.
- Calcula o frame do sprite a partir do `fps` do clipe e escreve `Sprite::frameIndex`.
- Dispara os callbacks de `frameEvents` para o frame atual.

Entidades com `Animator` mas sem `Sprite` são tratadas como personagens esqueléticos; o
percurso esquelético está documentado em
[`animation/skeletal-animation.md`](../animation/skeletal-animation.md).

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

`AnimationTransition` suporta os dois modelos: parâmetros nomeados em `conditions` e o
`std::function<bool()>` mais antigo em `legacyCondition`. Uma transição sem condições e
com `hasExitTime = true` dispara apenas pelo tempo normalizado.

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

`anyStateTransitions` são verificadas antes das transições do estado atual, o que é útil
para reações a dano e morte.

---

## Suavização e Transições

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

Os clipes referenciados por `AnimationState::clip` têm de sobreviver ao animator. Cenas
carregadas do disco guardam os clipes em `Animator::embeddedClips` e apontam os estados
para essas entradas.

---

## Decisões de Design

| Decisão | Justificativa |
|---------|-------------|
| State machine | A lógica de animação fica separada da lógica de gameplay |
| Parâmetros e condições nomeados | Serializáveis e editáveis na timeline, ao contrário de lambdas |
| `legacyCondition` | Mantém grafos C++ antigos a funcionar sem os reconstruir |
| `blendTime` por transição | O crossfade é o comportamento por omissão; `0` troca instantaneamente |
| Exit time e offset | O tempo normalizado do clipe não depende da duração |
| Frame events | O gameplay pode reagir a um frame específico do sprite |
| Camadas extra e body masks | Camadas additive/override para ações de tronco superior e máscaras esqueléticas |
| Sem campo de prioridade | O host chama `onUpdate`; a ordem de registo é a ordem de processamento |

---

## Critérios de Aceitação

`tests/test_animation.cpp` cobre:

- [x] Duração do clipe com zero frames, fps zero e clipes normais
- [x] Defaults de transições e estados
- [x] Entidades sem `Sprite` ou `Animator` são ignoradas sem crash
- [x] Animators em pausa não avançam o tempo
- [x] Clipes em loop dão a volta e clipes sem loop param no último frame
- [x] Transições só disparam quando as condições correspondem
- [x] Frame events disparam no frame correto
- [x] `play`, `pause`, `resume`, `setSpeed` e `isPlaying`

A suite não impõe um orçamento de frame fixo; faz profiling do teu próprio número de
animações.

---

## Dependências

- **Upstream:** [ECS Core](../ecs/core.md), [Asset Manager](../assets/asset-manager.md)
- **Downstream:** [Skeletal Animation](../animation/skeletal-animation.md), rendering de sprites

---

## 🔗 Tópicos Relacionados

| Tópico | Descrição |
|--------|-----------|
| [ECS Core](../ecs/core.md) | `World`, `Entity` e queries usados pelo sistema |
| [Rendering & Pipeline](../rendering/rhi.md) | Como os sprites animados chegam ao renderer |
| [Skeletal Animation](../animation/skeletal-animation.md) | Bones 3D, clipes importados e skinning |

## Referências

- [`src/caffeine/animation/AnimationComponents.hpp`](https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/animation/AnimationComponents.hpp) — clipes, estados e o animator
- [`src/caffeine/animation/AnimationSystem.hpp`](https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/animation/AnimationSystem.hpp) — update e lógica de transições
- [`tests/test_animation.cpp`](https://github.com/devscafecommunity/caffeine/blob/main/tests/test_animation.cpp) — suite de comportamento
