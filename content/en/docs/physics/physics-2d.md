# Physics 2D

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span><strong>Namespace:</strong> `Caffeine::Physics2D`</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/physics/PhysicsSystem2D.hpp"><code>physics/PhysicsSystem2D.hpp</code></a></span>
</div>

<p class="doc-lede">The 2D rigid-body system: a spatial-hash broad phase, AABB and circle
collision, impulse response with friction, layers, triggers and raycasts.</p>

---

## Overview

A simple 2D physics system with rigid-body dynamics, AABB and circle collision, layers and a
simple collision response (restitution + friction). `caffeine-runtime` registers it next to the
event bus.

**Intentional scope:** this covers most 2D cases. For joints, CCD or convex hulls, integrate a
dedicated library (Box2D/Jolt) as a scaling trigger.

**Behaviour (verified by `tests/test_physics2d.cpp`):**

- **Fixed step.** `onUpdate(dt)` runs whole steps of `kFixedStep` (1/60 s) and carries the remainder over (at most 8 steps per frame), so falls, forces and landings are the same at any frame rate. A force holds for the frame it is asked in (force x frame time); impulses are instant; a push wakes a sleeping body.
- **Scenery.** A collider with `isStatic` never moves, even if it carries a `RigidBody2D`; a floor that is only a collider holds bodies up. A body that would move more than half its size in a slice is advanced in up to 8 slices with a collision pass each, so thin walls are not jumped over.
- **Contacts.** Circle against box has its normal from A to B in either order (a centre inside the box leaves by the nearest side). Restitution is the smaller of the two and is ignored for a speed of one step of gravity (no jitter at rest). Pairs are resolved in a fixed order, so a scene replays identically.
- **Hierarchy.** A body under a parent is simulated in world space (the parent's offset, turn and scale count): positions are read through the parent's matrix, movements and corrections become local changes, `teleport`, `raycast` and the overlap queries take world positions. A collider's size is not scaled by its parents.
- **One-way platforms** stop a body that is above them and moving down, and let it through from below or the side. **Layers** above 31 never collide.
- **Events.** `OnCollision2D` once per pair per frame; `OnTrigger2D` when a body enters (`entered = true`) and when it leaves (`entered = false`), with `triggerEntity` the trigger.

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

`applyForce` is thread-safe (guarded by a mutex) and accumulates until the next update;
`applyImpulse` changes the body velocity immediately on the next step.

---

## Frame physics pipeline

- `1. Broad phase`
  - spatial hash grid (`kGridCellSize = 128`) over collider AABBs
- `2. Narrow phase`
  - AABB vs AABB
  - Circle vs Circle
  - Circle vs AABB
- `3. Resolve collisions`
  - impulse from restitution/friction/mass
  - positional correction (Baumgarte 0.4, slop 0.01)
- `4. Integrate`
  - `vel += (gravity + forces) * dt`
  - `pos += vel * dt` (semi-implicit Euler, 2 substeps)
- `5. Publish events`
  - `OnCollision2D` and `OnTrigger2D` via `EventBus::publishDeferred`


---

## Usage examples

```cpp
// ── Setup ─────────────────────────────────────────────────────
Caffeine::Physics2D::PhysicsSystem2D physics(&eventBus);
physics.setGravity({0, -500.0f});  // pixels/s²
// ... call physics.onUpdate(world, dt) once per frame

// ── Entity with physics ───────────────────────────────────────
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

// ── Static platform ───────────────────────────────────────────
world.add<Collider2D>(platform, {
    .size     = {200, 20},
    .isStatic = true,
    .layer    = 0  // world layer
});

// ── Jump impulse ──────────────────────────────────────────────
if (input.justPressed(Action::Jump)) {
    physics.applyImpulse(world, player, {0, 800.0f});
}

// ── Raycast for "is there ground below?" ──────────────────────
auto hit = physics.raycast(world, playerPos, {0, -1}, 32.0f);
bool onGround = hit.hit;

// ── Overlap for an attack box ─────────────────────────────────
Rect2D attackBox = { playerPos + Vec2{20, 0}, {40, 40} };
auto hits = physics.overlapAABB(world, attackBox);
for (auto& enemy : hits) {
    world.add<TakeDamage>(enemy, { .amount = 25 });
}
```

---

## Collision layers

```text
Layer 0 = World (platforms, walls)
Layer 1 = Player
Layer 2 = Enemy
Layer 3 = Projectile
Layer 4 = Trigger

Mask: layerMask = (1<<0)|(1<<2) = collides with World AND Enemy
```

A pair collides when each collider's `layerMask` includes the other's `layer`.

---

## Escalation triggers

If the game needs:

- Rotation of rigid bodies → integrate **Box2D** or **Jolt Physics**
- Joints/constraints → dedicated library
- CCD (avoid tunnelling at high speed) → dedicated library

---

## Design decisions

| Decision | Rationale |
|----------|-----------|
| Simple AABB/circle shapes | Covers most 2D cases without complexity |
| Semi-implicit Euler | Stable and simple for platformers |
| Collision events via EventBus | Physics does not couple Audio/FX |
| `applyForce` mutex | Forces can be queued from other threads |
| Sleep threshold | Idle bodies stop integrating |

---

## Acceptance criteria

- [ ] 1K rigid bodies at 60fps
- [ ] Physics step < 3ms for 1K bodies
- [ ] `tsan` clean — `applyForce` thread-safe
- [x] Raycast returns the correct hit at all angles
- [x] Collisions publish `OnCollision2D` correctly

---

## Dependencies

- **Upstream:** [ECS Core](../ecs/core.md), [Event Bus](../core/events.md), [Math](../math/vectors.md)
- **Downstream:** [Audio](../audio/audio-system.md) (reacts to collisions), [Spatial Partitioning](spatial-partitioning.md)

---

## References

- [`architecture_specs.md`](../architecture_specs.md) — §13 Physics 2D
- [`../core/events.md`](../core/events.md) — `OnCollision2D` event
- [Box2D/LiquidFun](https://github.com/google/liquidfun) — reference for advanced cases
