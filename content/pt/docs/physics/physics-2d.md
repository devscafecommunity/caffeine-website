# Physics 2D

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span><strong>Namespace:</strong> `Caffeine::Physics2D`</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/physics/PhysicsSystem2D.hpp"><code>physics/PhysicsSystem2D.hpp</code></a></span>
</div>

<p class="doc-lede">O sistema de corpos rígidos 2D: broad phase por hash espacial, colisão
AABB e círculo, resposta por impulso com atrito, layers, triggers e raycasts.</p>

---

## Visão Geral

Um sistema de física 2D simples com dinâmica de corpos rígidos, colisão AABB e circular,
layers e uma resposta de colisão simples (restitution + friction). O `caffeine-runtime`
registra-o ao lado do event bus.

**Âmbito intencional:** cobre a maioria dos casos 2D. Para joints, CCD ou convex hulls, integra
uma biblioteca dedicada (Box2D/Jolt) como gatilho de escala.

**Comportamento (verificado por `tests/test_physics2d.cpp`):**

- **Passo fixo.** `onUpdate(dt)` corre passos inteiros de `kFixedStep` (1/60 s) e leva o resto para a chamada seguinte (no máximo 8 passos por frame), então quedas, forças e aterragens são iguais a qualquer frame rate. Uma força vale pelo frame em que foi pedida (força x tempo do frame); impulsos são instantâneos; um empurrão acorda um corpo adormecido.
- **Cenário.** Um collider com `isStatic` nunca se move, mesmo com um `RigidBody2D`; um chão que é só collider segura os corpos. Um corpo que andaria mais de metade do seu tamanho numa fatia avança em até 8 fatias, com uma passagem de colisão em cada, e paredes finas não são saltadas.
- **Contactos.** Círculo contra caixa tem a normal de A para B nas duas ordens (um centro dentro da caixa sai pelo lado mais próximo). A restituição é a menor das duas e é ignorada para uma velocidade de um passo de gravidade (sem tremor em repouso). Os pares são resolvidos numa ordem fixa, então uma cena repete-se igual.
- **Hierarquia.** Um corpo sob um pai é simulado no espaço do mundo (o deslocamento, a rotação e a escala do pai contam): as posições são lidas pela matriz do pai, os movimentos e as correções viram mudanças locais, e `teleport`, `raycast` e as consultas de sobreposição usam posições do mundo. O tamanho de um collider não é escalado pelos pais.
- **Plataformas one-way** travam um corpo que está acima e desce, e deixam-no passar por baixo ou de lado. **Layers** acima de 31 nunca colidem.
- **Eventos.** `OnCollision2D` uma vez por par por frame; `OnTrigger2D` quando um corpo entra (`entered = true`) e quando sai (`entered = false`), com `triggerEntity` o trigger.

---

## API

```cpp
namespace Caffeine::Physics2D {

struct PhysicsMaterial {
    f32 friction    = 0.5f;
    f32 restitution = 0.3f;
    static PhysicsMaterial ice();
    static PhysicsMaterial rubber();
    static PhysicsMaterial metal();
    static PhysicsMaterial wood();
    static PhysicsMaterial stone();
};

struct RigidBody2D {
    f32  mass          = 1.0f;
    f32  restitution   = 0.3f;
    f32  friction      = 0.5f;
    f32  linearDamping = 0.0f;
    bool isKinematic   = false;
    bool lockRotation  = true;
    bool isSleeping    = false;
    f32  sleepTimer    = 0.0f;
    f32  velocityX     = 0.0f;
    f32  velocityY     = 0.0f;
};

struct Collider2D {
    Vec2          size      = { 1.0f, 1.0f };
    Vec2          offset    = { 0.0f, 0.0f };
    f32           radius    = 0.5f;
    u32           layer     = 0;
    u32           layerMask = 0xFFFFFFFF;
    ColliderShape shape     = ColliderShape::AABB;
    bool          isStatic  = false;
    bool          isTrigger = false;
    bool          isOneWay  = false;
    u8            debugColor[4] = { 80, 200, 255, 220 };
};

struct Rect2D { Vec2 position; Vec2 size; };
struct RaycastHit { ECS::Entity entity; Vec2 point; Vec2 normal; f32 distance; bool hit; };
struct CollisionManifold { Vec2 contactPoint; Vec2 normal; f32 penetration; };

class PhysicsSystem2D : public ECS::ISystem {
public:
    explicit PhysicsSystem2D(Events::EventBus* eventBus = nullptr);
    void onUpdate(ECS::World& world, f32 dt) override;

    void setGravity(Vec2 gravity);
    Vec2 gravity() const;

    RaycastHit raycast(ECS::World& world, Vec2 origin, Vec2 dir, f32 maxDist,
                       u32 layerMask = 0xFFFFFFFF);
    std::vector<ECS::Entity> overlapCircle(ECS::World& world, Vec2 center, f32 radius,
                                           u32 layerMask = 0xFFFFFFFF);
    std::vector<ECS::Entity> overlapAABB(ECS::World& world, Rect2D rect,
                                         u32 layerMask = 0xFFFFFFFF);

    void applyForce(ECS::Entity e, Vec2 force);
    void applyImpulse(ECS::World& world, ECS::Entity e, Vec2 impulse);
    void setKinematic(ECS::World& world, ECS::Entity e, bool kinematic);
    void teleport(ECS::World& world, ECS::Entity e, Vec2 position);

    const std::vector<CollisionManifold>& lastManifolds() const;
};

}
```

O `applyForce` é thread-safe (protegido por mutex) e acumula até ao próximo update; o
`applyImpulse` altera a velocidade do corpo imediatamente no passo seguinte.

---

## Pipeline de física do frame

- `1. Broad phase`
  - grelha de hash espacial (`kGridCellSize = 128`) sobre as AABBs dos colliders
- `2. Narrow phase`
  - AABB vs AABB
  - Círculo vs Círculo
  - Círculo vs AABB
- `3. Resolver colisões`
  - impulso a partir de restitution/friction/mass
  - correcção posicional (Baumgarte 0.4, slop 0.01)
- `4. Integrar`
  - `vel += (gravity + forces) * dt`
  - `pos += vel * dt` (Euler semi-implícito, 2 substeps)
- `5. Publicar eventos`
  - `OnCollision2D` e `OnTrigger2D` via `EventBus::publishDeferred`


---

## Exemplos de uso

```cpp
// ── Setup ─────────────────────────────────────────────────────
Caffeine::Physics2D::PhysicsSystem2D physics(&eventBus);
physics.setGravity({0, -500.0f});  // pixels/s²
// ... chamar physics.onUpdate(world, dt) uma vez por frame

// ── Entidade com física ───────────────────────────────────────
world.add<RigidBody2D>(player, {
    .mass        = 5.0f,
    .restitution = 0.3f,
    .friction    = 0.8f
});
world.add<Collider2D>(player, {
    .size     = {30, 60},
    .offset   = {0, 0},
    .isStatic = false,
    .layer    = 1  // player layer
});

// ── Plataforma estática ───────────────────────────────────────
world.add<Collider2D>(platform, {
    .size     = {200, 20},
    .isStatic = true,
    .layer    = 0  // world layer
});

// ── Impulso de salto ──────────────────────────────────────────
if (input.justPressed(Action::Jump)) {
    physics.applyImpulse(world, player, {0, 800.0f});
}

// ── Raycast para "há chão por baixo?" ─────────────────────────
auto hit = physics.raycast(world, playerPos, {0, -1}, 32.0f);
bool onGround = hit.hit;

// ── Overlap para uma área de ataque ───────────────────────────
Rect2D attackBox = { playerPos + Vec2{20, 0}, {40, 40} };
auto hits = physics.overlapAABB(world, attackBox);
for (auto& enemy : hits) {
    world.add<TakeDamage>(enemy, { .amount = 25 });
}
```

---

## Layers de colisão

```text
Layer 0 = World (plataformas, paredes)
Layer 1 = Player
Layer 2 = Enemy
Layer 3 = Projectile
Layer 4 = Trigger

Máscara: layerMask = (1<<0)|(1<<2) = colide com World E Enemy
```

Um par colide quando o `layerMask` de cada collider inclui o `layer` do outro.

---

## Gatilhos de escalada

Se o jogo precisar de:

- Rotação de corpos rígidos → integra **Box2D** ou **Jolt Physics**
- Joints/constraints → biblioteca dedicada
- CCD (evitar tunneling a alta velocidade) → biblioteca dedicada

---

## Decisões de design

| Decisão | Justificativa |
|---------|---------------|
| Formas AABB/círculo simples | Cobre a maioria dos casos 2D sem complexidade |
| Euler semi-implícito | Estável e simples para platformers |
| Eventos de colisão via EventBus | A física não acopla Audio/FX |
| Mutex no `applyForce` | Forças podem ser enfileiradas de outras threads |
| Limiar de sleep | Corpos parados deixam de integrar |

---

## Critérios de aceitação

- [ ] 1K corpos rígidos a 60fps
- [ ] Passo de física < 3ms para 1K corpos
- [ ] `tsan` limpo — `applyForce` thread-safe
- [x] Raycast devolve o hit correcto em todos os ângulos
- [x] Colisões publicam `OnCollision2D` correctamente

---

## Dependências

- **Upstream:** [ECS Core](../ecs/core.md), [Event Bus](../core/events.md), [Math](../math/vectors.md)
- **Downstream:** [Audio](../audio/audio-system.md) (reage a colisões), [Spatial Partitioning](spatial-partitioning.md)

---

## Referências

- [`architecture_specs.md`](../architecture_specs.md) — §13 Physics 2D
- [`../core/events.md`](../core/events.md) — evento `OnCollision2D`
- [Box2D/LiquidFun](https://github.com/google/liquidfun) — referência para casos avançados
