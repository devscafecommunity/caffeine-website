# 🎬 Sistema de Animação

> **Fase:** 4 — The Brain
> **Namespace:** `Caffeine::Animation`
> **Ficheiros:** `src/caffeine/animation/` (`AnimationComponents.hpp`, `AnimationSystem.hpp`, `Smoothing.hpp`, `Skeleton2D.hpp`, `Rig2DAsset.hpp`, `Rig2DSystem.hpp`)
> **Estado:** Implementado para PhaseShift, suavização e rigs 2D. O desenho de rigs 2D pelo batch renderer está em curso.

---

## Visão Geral

Cada entidade animada pode ter um componente **PhaseShift**. É a máquina de estados antes chamada `Animator`, renomeada para o vocabulário da engine. Lê e escreve parâmetros com nome, e três tipos de pose os consomem: frames de sprite, rigs 2D (ossos e malhas com skin ao estilo Live2D) e poses 3D com skin.

A regra: as fontes de animação nunca tocam em ossos nem em vértices. Escrevem **parâmetros**, e o rig transforma os parâmetros numa pose.

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

## Máquina de Estados (PhaseShift)

Um estado é um clip mais transições. Uma transição dispara quando as condições se verificam sobre os parâmetros, e mistura para o estado alvo durante `blendTime`. As transições com exit time esperam que o clip atual atinja um tempo normalizado.

```text
  idle ──(speed > 0.5, smoothed 0.15 s)──► run
   ▲                                        │
   └──────────(speed <= 0.5)────────────────┘
  Exit   returns to the default state
```

---

## Suavização e Transições

`setSmoothing(name, segundos)` põe um parâmetro float numa mola criticamente amortecida. As condições leem o valor suavizado, por isso um parâmetro que passa de 0 para 1 ainda leva o tempo escolhido a cruzar um limiar. A mola nunca ultrapassa o alvo. A suavização é guardada com a cena numa secção final opcional, pelo que as cenas antigas continuam a abrir.

As misturas entre estados usam `blendCurve` (um `KeyCurve`): linear, ease in, ease out, ease in-out ou uma Bézier cúbica.

---

## Parâmetros e Rigs 2D

Um `Rig2D` tem ossos, uma malha de vértices com até quatro pesos de osso cada, uma lista de triângulos, parâmetros com nome e bindings. Um binding soma uma curva de deslocamentos a um canal de osso (rotação, translação ou escala) conforme o parâmetro se move. Em cada tick, o rig recolhe os parâmetros dos valores por omissão, depois do clip de parâmetros no tempo da entidade, e depois dos parâmetros float do PhaseShift com o mesmo nome. O resultado é aplicado por skinning às posições dos vértices, na ordem do rig.

Rigs e clips de parâmetros são ficheiros de texto. Os nomes não têm espaços.

Os sprites são desenhados da mesma forma. O `Name` de um componente `Sprite` é o caminho da imagem, relativo à raiz do projeto; um nome vazio desenha um quad branco. Um `SpriteSheet` escolhe o frame pelo `frameIndex` do `Sprite`. Um sprite tem uma unidade do mundo no lado mais longo, escalada pela colocação da entidade (o seu `Transform`, ou os componentes 2D quando não tem 3D).

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

As funções abaixo estão na tabela `caffeine.animation`. Cada uma devolve `true` em caso de sucesso.

```lua
local e = caffeine.entity.create()
caffeine.component.add(e, "PhaseShift")
caffeine.animation.attachRig2D(e, "assets/hero.rig2d")
caffeine.animation.playRig2DClip(e, "assets/hero_blink.pclip")
caffeine.animation.setSmoothing(e, "Bend", 0.15)   -- seconds to reach the target
caffeine.animation.setFloat(e, "Bend", 1.0)        -- the rig's Bend parameter follows
```

---

## Decisões de Design

| Decisão | Justificativa |
|---------|-------------|
| Parâmetros são a única interface | Sprites, rigs e esqueletos podem partilhar uma máquina de estados |
| Suavização criticamente amortecida | Sem overshoot e estável com qualquer tempo de frame |
| Floats do PhaseShift substituem por nome | Os valores por omissão e os clips dão a pose base; um estado pode assumir qualquer parâmetro |
| Formatos de asset em texto | Comparáveis e revisáveis no git, como o `CAFANIM1` |

---

## Critérios de Aceitação

- [x] O skinning do rig é exato na pose de repouso
- [x] Um float suavizado só dispara a transição quando a mola alcança o limiar
- [x] Os ficheiros de rig e de clip fazem round-trip, e índices fora do intervalo são recusados
- [ ] Rigs desenhados no viewport através do batch renderer (caminho GPU construído, ainda não executado num dispositivo)
- [x] Painéis de rig e PhaseShift ligados ao motor pela C ABI (C ABI v22)

---

## Dependências

- **Upstream:** [ECS Core](ecs.md), [Asset Manager](../assets/asset-manager.md) (clips e rigs são carregados a partir de assets)
- **Downstream:** [Fase 5 — Animação Esquelética](../animation/skeletal-animation.md)

---

## 🔗 Tópicos Relacionados

| Tópico | Descrição |
|--------|-----------|
| [Sistemas de Jogo]() | Sistema de animação como sistema ECS |
| [Rendering & Pipeline]() | Sprites e rigs animados desenhados pelo batch renderer |

## Referências

- [`animation/skeletal-animation.md`](../animation/skeletal-animation.md) — poses 3D com skin
- [`architecture_specs.md`](../architecture_specs.md) — §12 Sistema de Animação
- [Índice de Tópicos Transversais]()
