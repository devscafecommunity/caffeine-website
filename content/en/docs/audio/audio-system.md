# 🎵 Audio System

> **Phase:**4 — The Brain
> **Namespace:** `Caffeine::Audio` 
> **File:** `src/audio/AudioSystem.hpp` 
> **Status: ** Implemented
> **RF:** RF4.8

---

## Overview

O Audio System usa `SDL_AudioStream` for music streaming and SFX preloading. Supports 2D spatial positioning (pan + volume per distance).

**Modelo:**
- **SFX** — loaded in whole `PoolAllocator` (buffer fixo por canal)
- **Music** — streaming on 64KB chunks to save memory
- **Spatial** — pan and volume calculated by listener distance ↔ emitter

---

## API

```cpp
namespace Caffeine::Audio {

struct AudioClip {
    const u8* data          = nullptr;
    u64       size          = 0;
    u32       sampleRate    = 44100;
    u16       channels      = 2;
    u16       bitsPerSample = 16;
    f32       duration      = 0.0f;
};

struct AudioEmitter {
    FixedString<128> clipPath;
    f32              volume      = 1.0f;
    f32              maxDistance = 500.0f;
    bool             loop        = false;
    bool             playOnSpawn = true;
    bool             spatial     = true;
};

class AudioSource {
public:
    void play();
    void pause();
    void stop();
    void seek(f32 seconds);

    void setVolume(f32 v);
    void setPan(f32 pan);
    void setPitch(f32 pitch);
    void setLoop(bool loop);

    bool isPlaying()   const;
    bool isPaused()    const;
    bool isFree()      const;
    f32  currentTime() const;
    f32  duration()    const;
    f32  volume()      const;
    f32  pan()         const;
    f32  pitch()       const;
    bool loop()        const;
};

class AudioSystem {
public:
    bool init(u32 sfxChannelCount = 32, u32 musicChannelCount = 2);
    void shutdown();

    AudioClip*   registerClip(const u8* data, u64 size,
                               u32 sampleRate = 44100, u16 channels = 2,
                               u16 bitsPerSample = 16, f32 duration = 0.0f);

    AudioSource* playSFX(const AudioClip* clip,
                         f32 volume = 1.0f, f32 pan = 0.0f);
    AudioSource* playSFXAt(const AudioClip* clip, Vec2 worldPos,
                            f32 maxDistance = 500.0f);

    void setListenerPosition(Vec2 pos, Vec2 forward = {1.0f, 0.0f});
    void setSourcePosition(AudioSource* source, Vec2 worldPos,
                           f32 maxDistance = 500.0f);

    void setMasterVolume(f32 volume);
    void setMasterPaused(bool paused);

    void update(f64 dt);

    bool isInitialized()    const;
    f32  masterVolume()     const;
    bool masterPaused()     const;
    Vec2 listenerPosition() const;

    struct Stats {
        u32  activeSFX;
        u32  sfxPoolUsed;
        u32  sfxPoolTotal;
        bool musicPlaying;
        f32  musicVolume;
    };
    Stats stats() const;
};

}  // namespace Caffeine::Audio
```

---

## Componente ECS para Audio

```cpp
namespace Caffeine::Components {

// ============================================================================
// @brief  Emitter de som no mundo 2D.
//
//  Usado pelo AudioSystem para calcular pan/volume por distância ao listener.
// ============================================================================
struct AudioEmitter {
    FixedString<128> clipPath;      // path do SFX
    f32              volume       = 1.0f;
    f32              maxDistance  = 500.0f;  // pixels
    bool             loop         = false;
    bool             playOnSpawn  = true;
    bool             spatial      = true;    // false = sem atenuação
};

}  // namespace Caffeine::Components
```

---

## Spatial Audio

```mermaid
flowchart TD
  Listener__Camera2D_position_["Listener (Camera2D position)"] --> m[""]
  n[""] --> distance["distance"]
  distance["distance"] --> _["│"]
  n[""] --> _["│"]
  n[""] --> AudioEmitter__worldPos_["AudioEmitter (worldPos)"]
  n[""] --> m[""]
```


---

## Exemplos de Uso

```cpp
Caffeine::Audio::AudioSystem audio;
audio.init(32, 2);

static const u8 jumpPCM[64] = {};
auto* jumpSFX = audio.registerClip(jumpPCM, sizeof(jumpPCM), 44100, 2, 16, 0.5f);

audio.playSFX(jumpSFX, 0.8f);

audio.playSFXAt(jumpSFX, {300.0f, 150.0f}, 500.0f);

audio.setListenerPosition(camera.position());

audio.update(dt);
```

---

## 3D sound and the weather's sound

`AudioService` (the script-facing layer over the system above) has a 3D mode and can play sounds that exist only in memory.
The rules are pure functions in `src/caffeine/audio/Spatial.hpp`, so they are unit tests that need no device.

```cpp
audio.setListener3D({camera.position, camera.forward, {0, 1, 0}});
u32 h = audio.playAt3D("wind.wav", {120, 4, -30}, /*ref*/ 2.0f, /*max*/ 200.0f);
audio.setSourcePosition3D(h, newPosition);                  // recomputes gain and pan
audio.registerSamples("made:tone", samples, 22050, 1);      // no file needed; play("made:tone") works
```

* **Gain** is 1 up to the reference distance, then falls (`Rolloff::Inverse`: half for every doubling of the distance, or
  `Linear`) and reaches 0 at the maximum distance with a short fade, so nothing cuts off.
* **Pan** is the side the source is on (right = forward x up, right-handed), and it opens up over the reference distance so a
  sound on top of the listener does not jump from side to side. The delay (`distance / 343`) is reported; the service does not apply it.
* The values are computed when the sound starts and when `setSourcePosition3D` is called; the service does not follow a moving
  listener by itself.

The editor's weather uses it. With **Audio Enabled** on the scene's `Weather` component (the Environment tab's *Sound* card; off by
default), the session opens the audio device and plays three things made from noise, with no files:

| Sound | Follows | Made by |
|---|---|---|
| Rain bed | The rain's intensity, smoothed over about 0.6 s; stopped when it is 0 | `synthesizeRainLoop` in `AmbienceSynth.hpp`, a seamless loop |
| Wind bed | The wind's speed times its gust | `synthesizeWindLoop`, a seamless loop |
| Thunder | Each thunder event: panned to the strike's bearing against where the camera faces, quieter with the distance | `synthesizeThunder` in `ThunderSynth.hpp`: a crack that only close strikes have, and rolls that lose their highs and last longer with the distance |

`WeatherAudio` drives an `AudioSink`, so its rules are tested with a fake device. Without a device the levels and the thunder count still
follow the weather (`caffeine_session_audio_state` reports them) and nothing plays. The runtime host (`caffeine-runtime`) does not use the
GPU scene renderer, so it has no weather sound yet.

---

## Design Decisions

| Decision | Justificativa |
|---------|-------------|
| Pool de sources | Zero alloc in runtime — n sources pre-allocated |
| Whole SFX in memory | Minimum latency — no short SFX streaming |
| Music on streaming | Large files do not consume whole RAM |
| `update()` na main thread | SDL audio callbacks run in separate thread — no race conditions |

---

## Acceptance Criteria

- [ ] 32 simultaneous SFX without crackle/distortion
- [ ] Audio pool sem alloc em runtime (PoolAllocator)
- [ ] Spatial audio: volume/pan correct by distance
- [ ] Smooth crossfade between two songs
- [ ] `update()` overhead < 0.5ms

---

## Dependencies

- **Upstream:** [Asset Manager](../assets/asset-manager.md), `SDL3::SDL_AudioStream`
- **Downstream:** [Event Bus](events.md) (responde a OnCollision2D, OnDeath)

---

## 🔗 Related Topics

| Topic | Description |
|--------|-----------|
| [Sistemas de Jogo]() | Audio como sistema ECS |
| [Assets & Pipeline]() | Audio assets carregados via Asset Manager |

## References

- [`docs/architecture_specs.md`](../architecture specs.md) — §11 Audio System
- [`core/events.md`](events.md) — Audio reacts to gameplay events
- [SDL3 Audio Documentation](https://wiki.libsdl.org/SDL3/CategoryAudio)
- [Transversal Topic Index]()
