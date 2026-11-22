# 🎵 Audio System

> **Fase:** 4 — O Cérebro  
> **Namespace:** `Caffeine::Audio`  
> **Arquivo:** `src/audio/AudioSystem.hpp`  
> **Status:** ✅ Implementado  
> **RF:** RF4.8

---

## Visão Geral

O Audio System usa `SDL_AudioStream` para streaming de música e pré-carregamento de SFX. Suporta posicionamento espacial 2D (pan + volume por distância).

**Modelo:**
- **SFX** — carregados inteiros em `PoolAllocator` (buffer fixo por canal)
- **Música** — streaming em chunks de 64KB para economizar memória
- **Spatial** — pan e volume calculados por distância listener ↔ emitter

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

## Som 3D e o som do tempo

O `AudioService` (a camada para scripts sobre o sistema acima) tem um modo 3D e toca sons que só existem em memória.
As regras são funções puras em `src/caffeine/audio/Spatial.hpp`, por isso são testes unitários que não precisam de dispositivo.

```cpp
audio.setListener3D({camera.position, camera.forward, {0, 1, 0}});
u32 h = audio.playAt3D("wind.wav", {120, 4, -30}, /*ref*/ 2.0f, /*max*/ 200.0f);
audio.setSourcePosition3D(h, newPosition);                  // recalcula ganho e pan
audio.registerSamples("made:tone", samples, 22050, 1);      // sem ficheiro; play("made:tone") funciona
```

* O **ganho** é 1 até à distância de referência, depois cai (`Rolloff::Inverse`: metade por cada duplicação da distância, ou
  `Linear`) e chega a 0 na distância máxima com um fade curto, por isso nada corta de repente.
* O **pan** é o lado em que a fonte está (direita = frente x cima, mão direita), e abre-se ao longo da distância de referência
  para que um som em cima do ouvinte não salte de lado para lado. O atraso (`distância / 343`) é comunicado; o serviço
  não o aplica.
* Os valores calculam-se quando o som começa e quando se chama `setSourcePosition3D`; o serviço não segue sozinho um ouvinte que se move.

O tempo do editor usa-o. Com **Audio Enabled** no componente `Weather` da cena (o cartão *Sound* do separador Environment; desligado por
omissão), a sessão abre o dispositivo de áudio e toca três coisas feitas de ruído, sem ficheiros:

| Som | Segue | Feito por |
|---|---|---|
| Leito de chuva | A intensidade da chuva, suavizada em cerca de 0.6 s; parado quando é 0 | `synthesizeRainLoop` em `AmbienceSynth.hpp`, um ciclo sem costura |
| Leito de vento | A velocidade do vento vezes a rajada | `synthesizeWindLoop`, um ciclo sem costura |
| Trovão | Cada evento de trovão: panorâmico para a direção do raio contra onde a câmara olha, mais baixo com a distância | `synthesizeThunder` em `ThunderSynth.hpp`: um estalo que só os raios próximos têm, e rolamentos que perdem os agudos e duram mais com a distância |

O `WeatherAudio` comanda um `AudioSink`, por isso as suas regras testam-se com um dispositivo falso. Sem dispositivo os níveis e a contagem de trovões
continuam a seguir o tempo (`caffeine_session_audio_state` comunica-os) e nada toca. O host de runtime (`caffeine-runtime`) não usa o
renderer de cena na GPU, por isso ainda não tem som do tempo.

---

## Decisões de Design

| Decisão | Justificativa |
|---------|-------------|
| Pool de sources | Zero alloc em runtime — n sources pre-alocadas |
| SFX inteiros em memória | Latência mínima — sem streaming de SFX curtos |
| Música em streaming | Arquivos grandes não consomem RAM inteiros |
| `update()` na main thread | Callbacks do SDL audio rodam em thread separada — sem race conditions |

---

## Critério de Aceitação

- [ ] 32 SFX simultâneos sem crackle/distorção
- [ ] Audio pool sem alloc em runtime (PoolAllocator)
- [ ] Spatial audio: volume/pan corretos por distância
- [ ] Crossfade suave entre duas músicas
- [ ] `update()` overhead < 0.5ms

---

## Dependências

- **Upstream:** [Asset Manager](../assets/asset-manager.md), `SDL3::SDL_AudioStream`
- **Downstream:** [Event Bus](events.md) (responde a OnCollision2D, OnDeath)

---

## 🔗 Tópicos Relacionados

| Tópico | Descrição |
|--------|-----------|
| [Sistemas de Jogo]() | Audio como sistema ECS |
| [Assets & Pipeline]() | Audio assets carregados via Asset Manager |

## Referências

- [`docs/architecture_specs.md`](../architecture_specs.md) — §11 Audio System
- [`core/events.md`](events.md) — Audio reage a eventos de gameplay
- [SDL3 Audio Documentation](https://wiki.libsdl.org/SDL3/CategoryAudio)
- [Índice de Tópicos Transversais]()
