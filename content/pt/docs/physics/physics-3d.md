# Physics 3D (Bullet3)

> **Namespace:** `Caffeine::Physics3D`  
> **Ficheiros:** `src/physics/PhysicsComponents3D.hpp`, `PhysicsWorld3D.cpp`, `PhysicsSystem3D.hpp`  
> **Estado:** 🟡 Primeira fatia — box, sphere, capsule, sync ECS no play mode  
> **Pilar:** [`plans/2026-09-22-engine-pillars-roadmap.md`](../plans/2026-09-22-engine-pillars-roadmap.md) §3

O ECS não inclui headers do Bullet. `RigidBody3D` e `Collider3D` são POD serializáveis. Os `btRigidBody` vivem em `PhysicsWorld3D`, indexados pelo id da entidade.

## Componentes

| Componente | Campos |
|------------|--------|
| `RigidBody3D` | `mass`, damping, `friction`, `restitution`, `bodyType` (Dynamic / Kinematic / Static), `lockRotation` |
| `Collider3D` | `Box` (half extents), `Sphere` (`halfExtents.x` = raio), `Capsule` (`x` raio, `y` altura total), `offset`, `isTrigger` |

Ambos são necessários. No Doppio: **Add Component → Physics 3D**. O step corre só em play mode (`SceneEditor::tickSystems`), em passos fixos de 1/60 s (ver Política). Ao sair do play mode o mundo Bullet é destruído; a cena editada volta pelo snapshot já existente.

## Política

- Gravidade por defeito: `(0, -9.81, 0)`.
- Corpos dinâmicos: a física escreve `Position3D`, `Transform` e `Rotation3D`.
- Corpos estáticos e cinemáticos: a pose do ECS é empurrada para o Bullet em cada frame.
- Escala de `Scale3D` / `Transform.scale` entra no tamanho do collider.
- **Passo fixo, qualquer frame rate.** `PhysicsWorld3D::step(dt)` transforma cada frame em passos inteiros de `fixedStep()` (1/60 s) e leva o resto para a chamada seguinte; uma queda dura o mesmo tempo de jogo a 30, 60 ou 240 fps. No máximo 8 passos por frame (um engasgo maior é descartado, não vira câmera lenta) e `stateOf` mistura os dois últimos passos, para a imagem andar a cada frame mesmo quando um frame não corre passo.
- **Uma força vale pelo frame em que foi pedida**: `addForce` vira momento (força x tempo do frame) repartido pelos passos desse frame, e o mesmo empurrão dá a mesma velocidade a qualquer frame rate. Impulsos são instantâneos.
- **O terreno colide.** Todo `TerrainComponent` com `buildCollisionMesh` ligado vira um heightfield estático do Bullet, na resolução total das amostras (ver [terreno](../terrain/terrain-system.md)); esculpir, mover, rodar ou escalar o terreno atualiza-o e acorda os corpos apoiados nele. `raycast` também o acerta. Um `RigidBody3D` no próprio terreno, se existir, só dá o atrito e a restituição (padrões 0,8 e 0).
- Os corpos dinâmicos fazem varredura (colisão contínua) quando andam mais de metade do menor lado num passo, para uma queda rápida não atravessar o terreno, que não tem espessura.
- Mesh convexa, debug draw e joints ainda não estão ligados.
- **Eventos.** Com um `EventBus`, o `PhysicsSystem3D` publica `OnCollision3D` quando dois corpos começam a tocar-se (`entered = true`) e quando deixam de tocar (`entered = false`), com o ponto de contacto, a normal de A para B e o impulso, e `OnTrigger3D` quando um corpo entra ou sai de um volume trigger. Nada é publicado para um par que continua em repouso. Os raios ignoram triggers.
- **Superfícies.** O atrito de um contacto é a média geométrica das duas superfícies e a restituição a maior das duas (o Bullet multiplica ambas, e uma bola saltitona num chão padrão quase não saltava). `setSurfaceCombine(Product)` (Lua `caffeine.physics3d.setSurfaceCombine("product")`) devolve a multiplicação do Bullet às cenas ajustadas a ela. Esferas e cápsulas têm um pouco de atrito de rolamento, então uma bola pára em vez de deslizar para sempre.
- **Hierarquia.** Um corpo sob um pai é simulado no espaço do mundo (o deslocamento, a rotação e a escala do pai contam) e escrito de volta como pose local.
- **Movido por fora.** Se um script, o editor ou um respawn muda a posição ou a rotação de um corpo dinâmico, o corpo acompanha (a física não o sobrescreve no frame seguinte). Poses estáticas e cinemáticas só entram quando mudam, então um chão parado já não acorda tudo o que repousa nele.

Build: `CAFFEINE_ENABLE_BULLET3=ON` (defeito). Sem a flag, `PhysicsWorld3D::isAvailable()` devolve false e o sistema é no-op.
