# 📦 Asset Manager

> **Phase:**3 — The Eye of Engine
> **Namespace:** `Caffeine::Assets` 
> **Files:** `src/assets/AssetManager.hpp` , `src/assets/AssetManager.cpp` , `src/assets/AssetHandle.hpp` , `src/assets/AssetTypes.hpp` 
> **Status: ** Implemented
> **RFs:** RF3.8, RF3.9

---

## Overview

Asset Manager loads, caches and provides assets (textures, audio, shaders) transparently to the game. Supports **async loading** via [Job System](../concurrency/job-system.md) and **hot-reload** in builds debug.

** Philosophy:** Game code asks for an asset on the way; Asset Manager returns a `AssetHandle<T>` . The game never sees raw bytes — only `AssetHandle<Texture>` .

**Carregamento zero-copy:** Os assets são carregados via `BlobLoader` that makes a single `fread()` para um `LinearAllocator` . As structs `Texture` , `AudioClip` e `ShaderBlob` are *views* about this buffer — no copying, no demerialization.

---

## Arquitetura

- `Game code:`
- `auto tex = assets.loadAsync<Texture>("textures/hero.caf");`
  - `1. acquireOrCreate("textures/hero.caf", AssetType::Texture)`
  - `Já em cache? → retorna ID existente, incrementa cacheHit`
  - `Novo? → cria AssetEntry, adiciona ao pathIndex`
- `2. scheduleLoad(id)`
  - `status = Loading`
  - `JobSystem::scheduleData(Background priority)`
    - `loadInternal(id):`
    - `BlobLoader::load(path, allocator)`
    - `resolveEntry() → Texture/Audio/Shader`
    - `status = Loaded`
  - `(se jobs == nullptr: loadInternal roda inline)`
- `3. handle.isReady() → true`
- `handle.get() → ponteiro const T* para o asset resolvido`


---

## Public API

```cpp
namespace Caffeine::Assets {

// ============================================================================
// LoadStatus — estado de carregamento de um asset
// ============================================================================
enum class LoadStatus : u8 {
    Pending,   // slot created, load not yet scheduled
    Loading,
    Ready,     // payload resolved and safe to use
    Failed,
    Invalid    // slot invalidado (LRU/GC); generation foi incrementada
};

// ============================================================================
// Tipos de asset runtime (zero-copy views)
// ============================================================================
struct Texture {
    u32       width;
    u32       height;
    u32       format;         // 0 = RGBA8
    u32       mipLevels;
    const u8* pixels;
    u64       pixelDataSize;
};

struct AudioClip {
    u32       sampleRate;
    u16       channels;
    u16       bitsPerSample;
    u32       sampleCount;
    const u8* pcmData;
    u64       pcmDataSize;
};

struct ShaderBlob {
    u32       stage;          // 0=vertex, 1=fragment, 2=compute
    const u8* bytecode;
    u64       bytecodeSize;
};

// ============================================================================
// CacheStats — snapshot do estado do cache
// ============================================================================
struct CacheStats {
    u64 totalCachedBytes;
    u64 maxCacheBytes;
    u32 textureCount;
    u32 audioCount;
    u32 pendingJobs;
    u32 evictedCount;   // entradas removidas por LRU desde o boot
    f32 cacheHitRate;
};

// ============================================================================
// AssetHandle<T> — handle RAII com ref counting + generation counter
//
//  - Copiar um handle incrementa o ref count do asset.
//  - O destructor decrementa o ref count.
//  - collectGarbage() descarrega assets com refCount == 0.
//  - invalidateEntry() (LRU/GC) incrementa generation → handles antigos ficam Invalid.
//  - Hot-reload NÃO incrementa generation — handles activos continuam válidos.
// ============================================================================
template<typename T>
class AssetHandle {
public:
    AssetHandle();
    AssetHandle(AssetManager* mgr, u32 id, u16 generation);
    ~AssetHandle();

    AssetHandle(const AssetHandle& o);
    AssetHandle& operator=(const AssetHandle& o);

    AssetHandle(AssetHandle&& o) noexcept;
    AssetHandle& operator=(AssetHandle&& o) noexcept;

    bool     isValid()  const;   // id + generation coincidem com a entrada
    bool     isReady()  const;   // isValid() && status == Ready
    const T* get()      const;   // nullptr se não estiver pronto ou generation stale

    explicit operator bool() const;

    u32  id()         const;
    u16  generation() const;
};

using AssetInvalidationCallback = void (*)(const InvalidatedAsset& info, void* userData);

// ============================================================================
// AssetManager — gerenciador central
// ============================================================================
class AssetManager {
public:
    explicit AssetManager(Threading::JobSystem* jobs,
                          const char*           basePath,
                          u64                   maxCacheMB = 256);
    ~AssetManager();

    // ── Loading ────────────────────────────────────────────────
    // Async: retorna imediatamente, carrega em background
    template<typename T>
    AssetHandle<T> loadAsync(const char* path);

    // Sync: bloqueia até carregado (use somente no init)
    template<typename T>
    AssetHandle<T> loadSync(const char* path);

    // ── Gerenciamento de cache ─────────────────────────────────
    void       collectGarbage();   // descarrega assets sem referências
    CacheStats cacheStats() const; // estatísticas do cache

    // ── Invalidation callbacks (GPU textures, etc.) ────────────
    void registerInvalidationCallback(AssetInvalidationCallback cb, void* userData);
    void unregisterInvalidationCallback(AssetInvalidationCallback cb, void* userData);

    // ── Frame tick ─────────────────────────────────────────────
    void tick(u64 frameIndex = 0); // atualiza frame index + hot-reload + LRU

private:
    // incRef / decRef / getStatus — usados por AssetHandle
    void       incRef(u32 id);
    void       decRef(u32 id);
    LoadStatus getStatus(u32 id) const;

    template<typename T>
    const T* getResolved(u32 id) const; // retorna Texture/Audio/Shader resolvido

    // ... (membros internos)
};

} // namespace Caffeine::Assets
```

---

## Estrutura Interna

Each loaded asset is represented by one `AssetEntry` :

- `AssetEntry`
  - `path : std::string (caminho completo no disco)`
  - `cafType : AssetType`
  - `status : std::atomic<LoadStatus>`
  - `allocator : unique_ptr<LinearAllocator> (dono do buffer)`
  - `header : const CafHeader*`
  - `metadata : const void* (TextureMetadata, AudioMetadata, etc.)`
  - `payload : const void* (pixels brutos, PCM, bytecode)`
  - `resolved : ResolvedData { Texture, AudioClip, ShaderBlob }`
  - `refCount : std::atomic<u32>`
  - `generation : u16 (incrementada em invalidateEntry, não em hot-reload)`
  - `sizeBytes : u64`
  - `lastAccessFrame : u64`


O `LinearAllocator` aloca um buffer de `fileSize + 64` bytes. O `BlobLoader` faz a `fread()` unique and adjusts the hands `header` , `metadata` e `payload` dentro desse buffer. As structs `resolved` are filled with the values extracted from the methadata + payload.

---

## Project References

The manager is also the **one place that decides what a path refers to**. A component field, an Inspector field or a generator node never keeps a path on its own: it asks the manager, and keeps what comes back, so what it points at is a file *inside the project* (or an engine built-in).

- `resolveReference(path)` understands a path relative to the project, to the assets folder or to the engine's assets, or absolute. `Ok` only for a file in the project or the engine; `Missing`, `OutsideProject` and `NotAFile` otherwise. A relative path that climbs out with `..` is never valid. `\\`, `.` and `//` do not matter.
- `importReference(path)` does the same and copies a real file from outside into the assets folder, in the folder of its kind (`Textures`, `Models`, `Audio`, `Materials`, `Scripts`; an existing folder is reused whatever its case). A file that is already there with the same content is reused, a different one with the same name gets `_1`, `_2`…
- The result carries `projectPath` (relative to the project root: what scenes and `.mat` files store) and `assetPath` (relative to the assets folder when the file is in it: what the picker lists and components store).
- C ABI 24: `caffeine_session_asset_reference(session, path, import, out)`. Doppio calls it for every Inspector asset field and every generator slot that holds an asset; see [Rust UI](../doppio/rust-ui.md).
- Handles hold a reference from the moment a slot is found, so a load that ends before the caller's handle exists is never evicted; one file is one slot whatever its spelling; a path that climbs out of the base folder, or a file loaded as another type, gives an empty handle; threads loading the same asset share one load; invalidation callbacks run outside the manager's lock.

---

## Hot-Reload (RF3.9)

Em builds **debug** ( `#ifdef CF_DEBUG` ):

1. `tick()` chama `checkHotReload()` a cada frame
2. Para cada asset carregado, compara `last_write_time` file on disk
3. Se mudou: `clearEntryData()` + `loadInternal()` **sem** incrementar `generation`
4. `AssetHandle<T>::get()` remains valid and points to reloaded payload

**Zero overhead in release:** The hot-reload is compiled conditionally — it does not exist in production builds.

---

## LRU Eviction and Invalidation

Quando `totalCachedBytes > maxCacheBytes` (after load or `collectGarbage` ):

1. `evictLruToFitBudget()` escolhe entradas com `refCount == 0` e menor `lastAccessFrame`
2. `invalidateEntry()` limpa payload, incrementa `generation` , notifica callbacks
3. Handles antigos passam a `LoadStatus::Invalid` ; `get()` devolve `nullptr`

**Callbacks:** subsistemas GPU (ex.: `TerrainGpuTextureCache` ) registam `registerInvalidationCallback` to release textures when the corresponding asset is evicted.

```cpp
void onAssetInvalidated(const InvalidatedAsset& info, void* userData) {
    if (info.type == AssetType::Texture) {
        // libertar GPUTexture associada a info.id / info.generation
    }
}
```

---

## Exemplos de Uso

```cpp
#include <Caffeine.hpp>

using namespace Caffeine;
using namespace Caffeine::Assets;

// ── Init ──────────────────────────────────────────────────────
Threading::JobSystem jobs(4);
AssetManager assets(&jobs, "assets/", 256); // max 256 MB cache

// ── Async loading (não bloqueia) ──────────────────────────────
auto heroTex = assets.loadAsync<Texture>("textures/hero.caf");
auto bgMusic = assets.loadAsync<AudioClip>("audio/level1.caf");

// ── Game loop ─────────────────────────────────────────────────
while (running) {
    assets.tick(frameCounter);

    if (heroTex.isReady()) {
        const Texture* t = heroTex.get();
        // t->width, t->height, t->pixels, t->pixelDataSize ...
    }

    // ── Coleta lixo a cada 60 frames ──────────────────────────
    if (frameCounter % 60 == 0) {
        assets.collectGarbage();
    }

    ++frameCounter;
}

// ── Sync no init (aceitável no boot) ─────────────────────────
auto uiAtlas = assets.loadSync<Texture>("textures/ui.caf");
const Texture* atlas = uiAtlas.get();  // pronto imediatamente
```

---

## Tests

21 casos de teste em `tests/test_assetmanager.cpp` (inclui HotReloader):

| Teste | O que verifica |
|-------|---------------|
| `AssetManager - construction with null JobSystem` | Builder without jobs not crash |
| `AssetManager - loadSync Texture` | Textura carregada, campos width/height/pixels corretos |
| `AssetManager - loadSync AudioClip` | AudioClip carregado, campos sampleRate/channels corretos |
| `AssetManager - loadSync ShaderBlob` | ShaderBlob carregado, campos stage/bytecode corretos |
| `AssetManager - second load of same path is cache hit` | Cache hit rate > 0 no segundo load |
| `AssetManager - cacheStats counts textures and audio` | textureCount/audioCount corretos |
| `AssetManager - collectGarbage unloads unreferenced assets` | Asset downloaded after handle exits scope |
| `AssetManager - collectGarbage does not unload referenced assets` | Asset mantido enquanto handle existe |
| `AssetManager - handle copy increments ref, original still valid` | Handle copy keeps asset alive |
| `AssetManager - loadAsync returns handle that becomes ready` | Async loading via JobSystem completa |
| `AssetManager - failed load returns handle with Failed status` | Path inexistente retorna Failed |
| `AssetManager - stale handle after eviction returns nullptr` | Generation stale after LRU |
| `AssetManager - invalidation callback fires on collectGarbage` | Callback notified in invalidation |
| `AssetManager - LRU evicts unreferenced assets when over budget` | Eviction por `maxCacheBytes` |
| `AssetManager - reload after eviction works with new generation` | New load after eviction |
| `AssetManager - tick advances frame index` | tick() not crash |
| `HotReloader - *` | Lifecycle and reload integration |

---

## Dependencies

| Dependence | Uso |
|-------------|-----|
| [`Caffeine::Threading::JobSystem`](../concurrency/job-system.md) | Background jobs para async loading |
| [`Caffeine::IO::BlobLoader`](caf-format.md) | Zero-copy reading of .caf files |
| [`Caffeine::IO::CafTypes`](caf-format.md) | CafHeader, TextureMetadata, AudioMetadata, ShaderMetadata |
| [`Caffeine::LinearAllocator`](../memory/allocators.md) | Linear allocation for asset buffer |
| `std::filesystem` (CF_DEBUG) | Hot-reload check via last write time |

---

## Design Decisions

| Decision | Justificativa |
|---------|--------------|
| `AssetHandle<T>` tipado | Erro de tipo pego em compile time |
| `loadAsync` aceita `JobSystem*` nullable | Fallback sync when there is no JobSystem (useful in testing) |
| Zero-copy resolved views | No conversion overhead; structs are filled in the load |
| `collectGarbage()` explicit | Evita pausas inesperadas; jogo controla quando descarregar |
| Generation counter | Detects handsles stale after LRU without dangling pointers |
| Hot-reload sem bump de generation | Handles activos sobrevivem a reload em debug |
| LRU por `lastAccessFrame` | Predictable memory pressure with `maxCacheMB` |
| `tick()` as a single point | Unifies frame counter, hot-reload and avoidance in one method |
| Hot-reload CF DEBUG only | Zero custo em release |
| `std::unordered_map` + `std::vector` | Simplicity about cache performance; Custom HashMap would be over-engineering at this stage |
| `std::mutex` (no lock-free) | Low containment; simplicity of implementation |

---

## Acceptance Criteria

- [x] `loadAsync` retorna imediatamente, carrega em background via JobSystem
- [x] `loadSync` blocks until loading complete
- [x] Cache com ref counting: handle copy incrementa, destructor decrementa
- [x] `collectGarbage()` download assets without references
- [x] `cacheStats()` retorna contagem por tipo, bytes totais, hit rate
- [x] Hot-reload em debug builds via `tick()` → `checkHotReload()`
- [x] Zero-copy: `BlobLoader` → `LinearAllocator` → resolved fields
- [x] Tipos suportados: Texture, AudioClip, ShaderBlob

---

## 🔗 Related Topics

| Topic | Description |
|--------|-----------|
| [Assets & Pipeline]() | Asset Manager como runtime do pipeline |
| [Competition & Runtime]() | Async loading via Job System |

## References

- [`docs/architecture_specs.md`](../architecture specs.md) — §7 Asset Manager
- [`assets/caf-format.md`](caf-format.md) — Binary format .caf
- [`concurrency/job-system.md`](../concurrency/job-system.md) — Background jobs for loading
- [Transversal Topic Index]()
- [Issue #26](https://github.com/devscafecommunity/caffeine/issues/26) — Asset Manager task
