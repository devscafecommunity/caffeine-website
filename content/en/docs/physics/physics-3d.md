# Physics 3D (Bullet3)

> **Namespace:** `Caffeine::Physics3D` 
> **Ficheiros:** `src/physics/PhysicsComponents3D.hpp` , `PhysicsWorld3D.cpp` , `PhysicsSystem3D.hpp` 
> **Estado:** 🟡 Primeira fatia — box, sphere, capsule, sync ECS no play mode
> **Pilar:** [`plans/2026-09-22-engine-pillars-roadmap.md`](.../plans/2026-09-22-engine-pillars-roadmap.md) §3

ECS does not include Bullet headers. `RigidBody3D` e `Collider3D` They're serializable PDs. The `btRigidBody` vivem em `PhysicsWorld3D` , indexados pelo id da entidade.

## Componentes

| Componente | Campos |
|------------|--------|
| `RigidBody3D` | `mass` , damping, `friction` , `restitution` , `bodyType` (Dynamic / Kinematic / Static), `lockRotation` |
| `Collider3D` | `Box` (half extents), `Sphere` ( `halfExtents.x` = raio), `Capsule` ( `x` raio, `y` altura total), `offset` , `isTrigger` |

Both are necessary. In Doppio: **Add Component → Physics 3D**. Step runs only in play mode ( `SceneEditor::tickSystems` ), in fixed steps of 1/60 s (see Policy). When leaving the play mode the Bullet world is destroyed; the scene edited back by the already existing snapshot.

## Policy

- Gravidade por defeito: `(0, -9.81, 0)` .
- Dynamic bodies: physics writes `Position3D` , `Transform` e `Rotation3D` .
- Static and kinematic bodies: ECS pose is pushed into Bullet in each frame.
- Escala de `Scale3D` / `Transform.scale` entra no tamanho do collider.
- **Fixed step, any frame rate.** `PhysicsWorld3D::step(dt)` turns each frame into whole steps of `fixedStep()` (1/60 s) and carries the remainder over, so a fall lasts the same game time at 30, 60 or 240 fps. At most 8 steps run per frame (a longer hitch is dropped, not played in slow motion) and `stateOf` blends the last two steps so the picture moves every frame even when a frame runs no step.
- **Forces hold for the frame they are asked in**: `addForce` is turned into momentum (force x frame time) and shared by the steps that frame runs, so the same push gives the same speed at any frame rate. Impulses are instant.
- **Terrain collides.** Every `TerrainComponent` with `buildCollisionMesh` on becomes a static Bullet height field at the full sample resolution (see [terrain](../terrain/terrain-system.md)); sculpting, moving, rotating or scaling the terrain updates it and wakes the bodies resting on it. `raycast` hits it too. A terrain's own `RigidBody3D`, if present, only supplies friction and restitution (defaults 0.8 and 0).
- Dynamic bodies sweep (continuous collision) once they move farther than half their smallest side in one step, so a fast fall does not tunnel through the terrain, which has no thickness.
- Convex mesh, debug draw and joints are still not connected.
- **Events.** With an `EventBus`, `PhysicsSystem3D` publishes `OnCollision3D` when two bodies start touching (`entered = true`) and when they stop (`entered = false`) with the contact point, the normal from A to B and the impulse, and `OnTrigger3D` when a body enters or leaves a trigger volume. Nothing is published for a pair that just keeps resting. Rays ignore triggers.
- **Surfaces.** Friction of a contact is the geometric mean of the two surfaces and restitution the larger of the two (Bullet's default multiplies both, so a bouncy ball on a default floor barely bounced). `setSurfaceCombine(Product)` (Lua `caffeine.physics3d.setSurfaceCombine("product")`) brings Bullet's multiplication back for scenes tuned against it. Spheres and capsules have a little rolling friction, so a ball comes to rest instead of coasting for ever.
- **Hierarchy.** A body under a parent is simulated in world space (the parent's offset, turn and scale count) and written back as a local pose.
- **Moved from outside.** If a script, the editor or a respawn changes a dynamic body's position or rotation, the body follows (the physics does not overwrite it next frame). Static and kinematic poses are pushed in only when they change, so a still floor no longer wakes everything resting on it.

Build: `CAFFEINE_ENABLE_BULLET3=ON` (defeito). Sem a flag, `PhysicsWorld3D::isAvailable()` It returns false and the system is no-op.
