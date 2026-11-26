# 📢 Event Bus

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span><strong>Namespace:</strong> <code>Caffeine::Events</code></span>
  <span><strong>Files:</strong> <code>src/caffeine/events/EventBus.hpp</code>, <code>src/caffeine/events/EventBus.cpp</code>, <code>src/caffeine/events/Events.hpp</code></span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">A typed publish/subscribe bus that lets systems communicate
without knowing each other, with immediate delivery on the main thread and a
thread-safe deferred queue drained once per frame.</p>

---

## Overview

The Event Bus enables **decoupled** communication between systems. One system
publishes an event; others subscribe without knowing who publishes it. This
removes direct dependencies (for example, Physics does not need to know about
Audio).

**Two delivery modes:**
- `publish<T>()` — immediate, calls listeners now (main thread)
- `publishDeferred<T>()` — enqueues for the next `dispatch()` (thread-safe)

---

## API

### `EventBus`

```cpp
namespace Caffeine::Events {

using ListenerHandle = u32;

class EventBus {
public:
    // Subscribes a typed listener. Returns a handle for cancellation.
    template<typename T>
    ListenerHandle subscribe(std::function<void(const T&)> callback);

    // Removes the listener. No-op for an invalid handle. No dangling pointers.
    void unsubscribe(ListenerHandle handle);

    // Immediate delivery: calls every listener now (safe snapshot).
    template<typename T>
    void publish(const T& event);

    // Enqueues the event for the next dispatch(). Thread-safe.
    template<typename T>
    void publishDeferred(T event);

    // Drains the deferred queue. Call once per frame from the GameLoop.
    void dispatch();

    // Number of pending events in the queue.
    usize pendingCount() const;

    // Removes every listener and empties the queue.
    void clear();
};

} // namespace Caffeine::Events
```

### Event type ID

Each type `T` receives a unique runtime ID from the address of a local static
variable — no practical collisions and no manual registration:

```cpp
namespace Caffeine::Events::Detail {

template<typename T>
u32 eventTypeId() {
    static char s_sentinel = 0;
    return static_cast<u32>(reinterpret_cast<uintptr_t>(&s_sentinel));
}

} // namespace Caffeine::Events::Detail
```

> Note: the 64-bit address is truncated to `u32`. A theoretical collision is
> possible but negligible in practice (it would require two statics exactly
> 4 GiB apart with the same low 32 bits).

---

## Predefined Events

All live in `src/caffeine/events/Events.hpp`, namespace `Caffeine::Events`.

### ECS

```cpp
struct OnEntityCreated   { u32 entityId; };
struct OnEntityDestroyed { u32 entityId; };
```

### Physics / Collision

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

### Combat / Stats

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

### Progression

```cpp
struct OnScoreChanged {
    u32 playerId;
    i32 previousScore;
    i32 currentScore;
    i32 delta;
};
```

### Scene

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

## Usage Examples

### Basic setup

```cpp
Caffeine::Events::EventBus bus;

// Subscribe
Caffeine::Events::ListenerHandle h = bus.subscribe<Caffeine::Events::OnDeath>(
    [](const Caffeine::Events::OnDeath& e) {
        if (e.killerEntityId == 0) {
            // environmental death
        }
    });

// Publish immediately (main thread)
bus.publish(Caffeine::Events::OnDeath{ entityId, killerId });

// Cancel
bus.unsubscribe(h);
```

### Deferred publication (from a worker thread)

```cpp
// PhysicsSystem running on a job worker:
bus.publishDeferred(Caffeine::Events::OnCollision2D{
    entityA, entityB, contactPoint, normal, impulse
});

// GameLoop, at the start of the fixed update:
bus.dispatch(); // delivers every queued event
```

### Communication between systems without coupling

```cpp
// AudioSystem (does not know PhysicsSystem)
bus.subscribe<Caffeine::Events::OnCollision2D>(
    [&audio](const Caffeine::Events::OnCollision2D& e) {
        audio.playSFX("impact.caf");
    });

// ScoreSystem (knows nothing about gameplay internals)
bus.subscribe<Caffeine::Events::OnDeath>(
    [&score](const Caffeine::Events::OnDeath& e) {
        score.add(100);
    });

// PhysicsSystem publishes; both receive
bus.publishDeferred(Caffeine::Events::OnCollision2D{ /* ... */ });
```

---

## Integration in the GameLoop

- **Frame N:**
  - `InputManager.beginFrame()` + injected events + `InputManager.endFrame()` (if used)
  - `EventBus.dispatch()` — delivers deferred events from frame N-1
  - `World.update(fixedDt)`
    - `PhysicsSystem → publishDeferred(OnCollision2D)`
    - `CombatSystem  → publish(OnDeath)` (immediate)
    - `...`
  - `render(alpha)`
- **Frame N+1:**
  - `EventBus.dispatch()` — delivers the `OnCollision2D` events from frame N
  - `...`

---

## Design Decisions

| Decision | Rationale |
|---------|---------------|
| Type-erased `void*` internally | Allows `std::unordered_map<u32, vector<Record>>` without a virtual per type |
| Snapshot before iterating in `publish()` | A listener may call `unsubscribe()` without invalidating iteration |
| Mutex only on the deferred queue | `publish()` and `subscribe()` are main-thread only; only `publishDeferred()` needs a lock |
| `ListenerHandle = u32` | No pending pointers; unsubscribe by ID, not by reference |
| `Detail::eventTypeId<T>()` via `static char` | Zero registration cost; unique ID guaranteed by the static address |
| `unsubscribe()` with a linear search | O(types × listeners); acceptable because unsubscribe is rare (not a hot path) |

---

## Thread Safety

| Operation | Thread-safe? | Reason |
|----------|-------------|--------|
| `subscribe()` | Main thread only | Modifies `m_listeners` without a lock |
| `unsubscribe()` | Main thread only | Modifies `m_listeners` without a lock |
| `publish()` | Main thread only | Reads `m_listeners` without a lock |
| `publishDeferred()` | ✅ Any thread | Protected by `m_queueMutex` |
| `dispatch()` | Main thread only | Swaps the queue under the lock, then dispatches without it |

---

## Acceptance Criteria

| Criterion | Result |
|----------|-----------|
| 1K events/frame without noticeable overhead | ✅ 1000× `publish()` = **0.085ms** total |
| `publish()` < 0.1ms (hot path) | ✅ **0.086µs**/call (10K reps, Release) |
| `publishDeferred` thread-safe | ✅ 8 threads × 125 events = 1000/1000 without a race |
| Deferred events delivered on the next `dispatch()` | ✅ Zero delivered before, all afterwards |
| Zero live listeners after `unsubscribe` | ✅ 0 callbacks after unsubscribe (immediate and deferred) |

---

## Tests

`tests/test_eventbus.cpp` — 18 test cases, 39 assertions:

| Test | Coverage |
|-------|-----------|
| subscribe + immediate publish | Base flow |
| Multiple listeners on the same type | Fan-out |
| unsubscribe removes the listener | Correct cancellation |
| Invalid unsubscribe handle | Safe no-op |
| Isolated event types | No cross-talk |
| publish with no listeners | Safe no-op |
| publishDeferred does not deliver immediately | Queue behaviour |
| dispatch delivers everything | Guaranteed delivery |
| dispatch empties the queue | Post-dispatch state |
| Deferred delivery order | FIFO preserved |
| clear removes listeners and queue | Full reset |
| Unique handles per subscription | IDs do not collide |
| Selective unsubscribe among several | Surgical precision |
| Deferred with mixed types | Multi-type queue |
| Predefined `OnEntityCreated` | ECS event |
| Predefined `OnDeath` | Combat event |
| Predefined `OnScoreChanged` + dispatch | Progression event |
| 8 threads × 125 `publishDeferred` | Thread safety |

---

## Dependencies

- **Upstream:** `Caffeine::Core::Types`, `src/caffeine/math/Vec2.hpp`
- **Downstream (real use in code):** `PhysicsSystem2D` (`src/caffeine/physics`) publishes collisions;
  `ScriptEngine` (`src/caffeine/script`) exposes `on` / `emit` to Lua; `UISystem` (`src/caffeine/ui`)
  and `SceneEditor` (`doppio-archived/src/doppio/editor/`) consume events
- **Related docs:** [Physics 2D](../physics/physics-2d.md), [Audio](../audio/audio-system.md),
  [Game UI](../runtime-ui/game-ui.md), [GameLoop](../core/game-loop.md) (calls `dispatch()`)

---

## 🔗 Related Topics

| Topic | Description |
|--------|-----------|
| [Concurrency & Runtime]() | Event Bus in the context of the Game Loop |
| [Game Systems]() | Events connect gameplay systems |

## References

- [`docs/architecture_specs.md`](../architecture_specs.md) — §6 Event Bus
- [`../physics/physics-2d.md`](../physics/physics-2d.md) — publishes `OnCollision2D`
- [`core/game-loop.md`](../core/game-loop.md) — calls `eventBus.dispatch()`
- [Transversal Topic Index]()
