# 🎵 Audio System

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span><strong>Namespace:</strong> <code>Caffeine::Audio</code></span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/audio/AudioSystem.hpp"><code>audio/AudioSystem.hpp</code></a></span>
</div>

<p class="doc-lede">SDL3-backed sound effects with a fixed voice pool, per-source
volume/pan/pitch and simple 2D distance attenuation. Music streaming is not implemented.</p>

---

## Overview

`AudioSystem` opens one SDL3 playback device and owns a pool of `AudioSource` objects.
Each source wraps an `SDL_AudioStream` bound to the device:

- **SFX** — the whole clip is pushed into the stream. A free source is reused; when the
  pool is exhausted, `playSFX` returns `nullptr` and the sound is dropped.
- **Voices** — `init(sfxChannelCount, musicChannelCount)` sizes the SFX pool. The music
  channel count is accepted but unused; `Stats::musicPlaying` and `musicVolume` are
  always `false` / `0`.
- **Spatial** — a 2D listener position gives linear volume falloff and a pan value from
  the horizontal offset. There is no 3D attenuation, cone or Doppler.

`AudioSystem` is a plain engine service, not an `ECS::ISystem`: the host calls
`update(dt)` once per frame.

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

    void setVolume(f32 v);   // clamped 0..1
    void setPan(f32 pan);    // clamped -1..1
    void setPitch(f32 pitch); // stored 0.1..4; not applied by SDL
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

    void tick(f32 dt);
};

class AudioSystem {
public:
    bool init(u32 sfxChannelCount = 32, u32 musicChannelCount = 2);
    void shutdown();

    AudioClip* registerClip(const u8* data, u64 size,
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

The whole header is wrapped in `#ifdef CF_HAS_SDL3`; without SDL3 the types are not
available. `registerClip` does not copy the bytes: the caller owns the buffer for as
long as the clip is used.

`setPitch` stores a value but SDL3's audio stream gain path does not resample, so pitch
is currently informational only.

---

## ECS audio component

```cpp
namespace Caffeine::Audio {

// Emitter data for a 2D sound in the world.
struct AudioEmitter {
    FixedString<128> clipPath;      // path to the SFX
    f32              volume       = 1.0f;
    f32              maxDistance  = 500.0f;  // pixels
    bool             loop         = false;
    bool             playOnSpawn  = true;
    bool             spatial      = true;    // false = no attenuation
};

}  // namespace Caffeine::Audio
```

`AudioEmitter` is a component in `Caffeine::Audio`, not `Caffeine::Components`. The
engine stores it with the entity; a runtime or tool is responsible for registering the
clip and calling `playSFXAt`.

---

## Spatial audio

```text
distance = length(emitter.xy - listener.xy)
volume   = clamp(1 - distance / maxDistance, 0, 1)
pan      = clamp((emitter.x - listener.x) / maxDistance, -1, 1)

listener position ──► setListenerPosition()
emitter position  ──► playSFXAt() or setSourcePosition()
```

`playSFXAt` applies volume and pan once, at start. `setSourcePosition` updates an
already-playing source; call it every frame for a moving emitter. `forward` in
`setListenerPosition` is currently ignored.

---

## Exemplos de Uso

```cpp
Caffeine::Audio::AudioSystem audio;
audio.init(32, 2);

// bytes must stay alive while the clip is in use
static const u8 jumpPCM[64] = {};
auto* jumpSFX = audio.registerClip(jumpPCM, sizeof(jumpPCM), 44100, 2, 16, 0.5f);

// Non-positional SFX.
audio.playSFX(jumpSFX, 0.8f);

// Positional SFX relative to the listener.
audio.setListenerPosition(camera.position());
audio.playSFXAt(jumpSFX, {300.0f, 150.0f}, 500.0f);

// Per-frame upkeep: advances source timers and restarts looping clips.
audio.update(dt);

audio.setMasterVolume(0.7f);
audio.setMasterPaused(paused);
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

| Decision | Justification |
|---------|-------------|
| Fixed source pool | No allocation while playing; predictable voice count |
| Whole SFX in the stream | Lowest latency for short sounds |
| No music streaming yet | `musicChannelCount` and the music stats are reserved |
| `update()` on the main thread | SDL's audio callback runs on its own thread; source state stays on the main thread |
| Linear 2D falloff | Cheap and predictable for side-scrollers and top-down games |
| Caller-owned PCM | `registerClip` avoids a copy and lets assets stream from their own storage |

---

## Acceptance Criteria

`tests/test_audio.cpp` covers:

- [x] Default `AudioClip`, `AudioEmitter` and `AudioSystem` state
- [x] `init` is idempotent; `shutdown` on an uninitialised system is safe
- [x] Master volume clamps to 0..1
- [x] Listener position and pause flag are stored before init
- [x] `playSFX(nullptr)` returns `nullptr`
- [x] `registerClip` returns a stable clip pointer
- [x] Distance attenuation reaches zero at `maxDistance` and full volume at the centre
- [x] `setSourcePosition(nullptr)` is a no-op
- [x] `update` and `shutdown` after init do not crash
- [x] `stats().sfxPoolUsed` tracks active sources

There is no crossfade or music-streaming test because that feature is not implemented.

---

## Dependencies

- **Upstream:** SDL3 audio (`SDL_AudioStream`), [Asset Manager](../assets/asset-manager.md)
- **Downstream:** gameplay code that reacts to events and calls `playSFXAt`

---

## 🔗 Related Topics

| Topic | Description |
|--------|-----------|
| [ECS Core](../ecs/core.md) | Components and queries |
| [Assets & Pipeline](../assets/asset-manager.md) | How audio bytes are loaded before `registerClip` |

## References

- [`src/caffeine/audio/AudioSystem.hpp`](https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/audio/AudioSystem.hpp) — device, sources and spatial helpers
- [`src/caffeine/audio/AudioComponents.hpp`](https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/audio/AudioComponents.hpp) — `AudioClip` and `AudioEmitter`
- [`tests/test_audio.cpp`](https://github.com/devscafecommunity/caffeine/blob/main/tests/test_audio.cpp) — behaviour suite
- [SDL3 audio documentation](https://wiki.libsdl.org/SDL3/CategoryAudio)
