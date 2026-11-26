# 📢 Event Bus

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span><strong>Namespace:</strong> <code>Caffeine::Events</code></span>
  <span><strong>Arquivos:</strong> <code>src/caffeine/events/EventBus.hpp</code>, <code>src/caffeine/events/EventBus.cpp</code>, <code>src/caffeine/events/Events.hpp</code></span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">Um bus publish/subscribe tipado que permite aos sistemas
comunicar sem se conhecerem, com entrega imediata na main thread e uma fila
diferida thread-safe consumida uma vez por frame.</p>

---

## Visão Geral

O Event Bus permite comunicação **desacoplada** entre sistemas. Um sistema publica um evento; outros se inscrevem sem conhecer quem publica. Isso elimina dependências diretas (ex: Physics não precisa conhecer Audio).

**Dois modos de entrega:**
- `publish<T>()` — imediato, chama listeners agora (main thread)
- `publishDeferred<T>()` — enfileira para o próximo `dispatch()` (thread-safe)

---

## API

### `EventBus`

```cpp
namespace Caffeine::Events {

using ListenerHandle = u32;

class EventBus {
public:
    // Inscreve um listener tipado. Retorna handle para cancelamento.
    template<typename T>
    ListenerHandle subscribe(std::function<void(const T&)> callback);

    // Remove o listener. No-op se handle inválido. Zero dangling pointers.
    void unsubscribe(ListenerHandle handle);

    // Entrega imediata: chama todos os listeners agora (snapshot seguro).
    template<typename T>
    void publish(const T& event);

    // Enfileira evento para o próximo dispatch(). Thread-safe.
    template<typename T>
    void publishDeferred(T event);

    // Processa toda a fila diferida. Chamar uma vez por frame, no GameLoop.
    void dispatch();

    // Número de eventos pendentes na fila.
    usize pendingCount() const;

    // Remove todos os listeners e esvazia a fila.
    void clear();
};

} // namespace Caffeine::Events
```

### Tipo ID de Evento

Cada tipo `T` recebe um ID único em runtime via endereço de variável static local — zero colisão prática, zero registro manual:

```cpp
namespace Caffeine::Events::Detail {

template<typename T>
u32 eventTypeId() {
    static char s_sentinel = 0;
    return static_cast<u32>(reinterpret_cast<uintptr_t>(&s_sentinel));
}

} // namespace Caffeine::Events::Detail
```

> Nota: o endereço de 64 bits é truncado para `u32`. Colisão teórica é
> possível mas desprezível na prática (exigiria dois statics a exatamente
> 4 GiB de distância com os mesmos 32 bits baixos).

---

## Eventos Pré-definidos

Todos em `src/caffeine/events/Events.hpp`, namespace `Caffeine::Events`.

### ECS

```cpp
struct OnEntityCreated   { u32 entityId; };
struct OnEntityDestroyed { u32 entityId; };
```

### Física / Colisão

```cpp
struct OnCollision2D {
    u32  entityA;
    u32  entityB;
    Vec2 contactPoint;
    Vec2 normal;
    f32  impulse;
};

struct OnTrigger2D {
    u32  triggerEntity;
    u32  otherEntity;
    bool entered; // true = enter, false = exit
};
```

### Combate / Stats

```cpp
struct OnHealthChanged {
    u32 entityId;
    f32 previousHealth;
    f32 currentHealth;
    f32 maxHealth;
};

struct OnDeath {
    u32 entityId;
    u32 killerEntityId; // 0 = environmental / no killer
};
```

### Progressão

```cpp
struct OnScoreChanged {
    u32 playerId;
    i32 previousScore;
    i32 currentScore;
    i32 delta;
};
```

### Cena

```cpp
struct OnLevelLoaded   { u32 levelId; c8 levelName[64]; };
struct OnLevelUnloaded { u32 levelId; };
```

### Input

```cpp
struct OnActionPressed  { u32 actionId; u32 playerId; };
struct OnActionReleased { u32 actionId; u32 playerId; };
```

### Map surfaces

```cpp
struct OnMapSurfaceChunkRequest {
    u32 surfaceEntityId = 0;
    i32 chunkX = 0;
    i32 chunkY = 0;
    f32 worldMinX = 0.0f;
    f32 worldMinY = 0.0f;
    f32 chunkSize = 0.0f;
};
```

---

## Exemplos de Uso

### Setup básico

```cpp
Caffeine::Events::EventBus bus;

// Inscrever
ListenerHandle h = bus.subscribe<OnDeath>([](const OnDeath& e) {
    if (e.killerEntityId == 0) {
        // morte ambiental
    }
});

// Publicar imediato (main thread)
bus.publish(OnDeath{ entityId, killerId });

// Cancelar
bus.unsubscribe(h);
```

### Publicação diferida (de worker thread)

```cpp
// PhysicsSystem rodando em job worker:
bus.publishDeferred(OnCollision2D{
    entityA, entityB, contactPoint, normal, impulse
});

// GameLoop, início do fixed update:
bus.dispatch(); // entrega todos os eventos enfileirados
```

### Comunicação entre sistemas sem acoplamento

```cpp
// AudioSystem (não conhece PhysicsSystem)
bus.subscribe<OnCollision2D>([&audio](const OnCollision2D& e) {
    audio.playSFX("impact.caf");
});

// ScoreSystem (não conhece nada de gameplay)
bus.subscribe<OnDeath>([&score](const OnDeath& e) {
    score.add(100);
});

// PhysicsSystem publica, ambos recebem
bus.publishDeferred(OnCollision2D{ ... });
```

---

## Integração no GameLoop

- `Frame N:`
  - `InputManager.beginFrame()` + eventos injetados + `InputManager.endFrame()` (se usado)
  - `EventBus.dispatch()          ← entrega diferidos do frame N-1`
  - `World.update(fixedDt)`
    - `PhysicsSystem → publishDeferred(OnCollision2D)`
    - `CombatSystem  → publish(OnDeath)   ← imediato`
    - `...`
  - `render(alpha)`
- `Frame N+1:`
  - `EventBus.dispatch()          ← entrega os OnCollision2D do frame N`
  - `...`


---

## Decisões de Design

| Decisão | Justificativa |
|---------|---------------|
| Type-erased `void*` internamente | Permite `std::unordered_map<u32, vector<Record>>` sem virtual por tipo |
| Snapshot antes de iterar em `publish()` | Listener pode chamar `unsubscribe()` sem invalidar iteração |
| Mutex apenas na fila deferred | `publish()` e `subscribe()` são main-thread only; só `publishDeferred()` precisa de lock |
| `ListenerHandle = u32` | Sem ponteiros pendentes; unsubscribe por ID, não por referência |
| `Detail::eventTypeId<T>()` via `static char` | Zero custo de registro; ID único garantido por endereço de static |
| `unsubscribe()` com busca linear | O(tipos × listeners); aceitável porque unsubscribe é raro (não hot path) |

---

## Thread Safety

| Operação | Thread-safe? | Motivo |
|----------|-------------|--------|
| `subscribe()` | Main thread only | Modifica `m_listeners` sem lock |
| `unsubscribe()` | Main thread only | Modifica `m_listeners` sem lock |
| `publish()` | Main thread only | Lê `m_listeners` sem lock |
| `publishDeferred()` | ✅ Qualquer thread | Protegido por `m_queueMutex` |
| `dispatch()` | Main thread only | Consome fila após swap; não precisa de lock |

---

## Critérios de Aceitação

| Critério | Resultado |
|----------|-----------|
| 1K eventos/frame sem overhead perceptível | ✅ 1000× `publish()` = **0.085ms** total |
| `publish()` < 0.1ms (hot path) | ✅ **0.086µs**/call (10K reps, Release) |
| `publishDeferred` thread-safe | ✅ 8 threads × 125 eventos = 1000/1000 sem race |
| Eventos diferidos entregues no próximo `dispatch()` | ✅ Zero entregues antes, todos depois |
| Zero listeners mortos após `unsubscribe` | ✅ 0 callbacks após unsubscribe (imediato e deferred) |

---

## Testes

`tests/test_eventbus.cpp` — 18 casos de teste, 39 asserções:

| Teste | Cobertura |
|-------|-----------|
| subscribe + publish imediato | Fluxo base |
| Múltiplos listeners no mesmo tipo | Fan-out |
| unsubscribe remove listener | Cancelamento correto |
| unsubscribe handle inválido | No-op seguro |
| Tipos de evento isolados | Sem cross-talk |
| publish sem listeners | No-op seguro |
| publishDeferred não entrega imediatamente | Fila correta |
| dispatch entrega todos | Entrega garantida |
| dispatch esvazia fila | Estado pós-dispatch |
| Ordem de entrega deferred | FIFO preservado |
| clear remove listeners e fila | Reset completo |
| Handles únicos por subscription | IDs não colidem |
| Unsubscribe seletivo entre vários | Precisão cirúrgica |
| Deferred com tipos mistos | Multi-type queue |
| `OnEntityCreated` predefinido | Evento ECS |
| `OnDeath` predefinido | Evento combate |
| `OnScoreChanged` predefinido + dispatch | Evento progressão |
| 8 threads × 125 `publishDeferred` | Thread safety |

---

## Dependências

- **Upstream:** `Caffeine::Core::Types`, `src/caffeine/math/Vec2.hpp`
- **Downstream (uso real no código):** `PhysicsSystem2D` (`src/caffeine/physics`) publica colisão;
  `ScriptEngine` (`src/caffeine/script`) expõe `on`/`emit` para Lua; `UISystem` (`src/caffeine/ui`)
  e `SceneEditor` (`doppio-archived/src/doppio/editor/`) consomem eventos
- **Docs relacionados:** [Physics 2D](../physics/physics-2d.md), [Audio](../audio/audio-system.md),
  [Game UI](../runtime-ui/game-ui.md), [GameLoop](../core/game-loop.md) (chama `dispatch()`)

---

## 🔗 Tópicos Relacionados

| Tópico | Descrição |
|--------|-----------|
| [Concorrência & Runtime]() | Event Bus no contexto do Game Loop |
| [Sistemas de Jogo]() | Eventos conectam sistemas de gameplay |

## Referências

- [`docs/architecture_specs.md`](../architecture_specs.md) — §6 Event Bus
- [`../physics/physics-2d.md`](../physics/physics-2d.md) — publica `OnCollision2D`
- [`core/game-loop.md`](../core/game-loop.md) — chama `eventBus.dispatch()`
- [Índice de Tópicos Transversais]()
