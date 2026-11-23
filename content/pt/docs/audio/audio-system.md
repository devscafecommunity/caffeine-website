# 🎵 Audio System

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span><strong>Namespace:</strong> <code>Caffeine::Audio</code></span>
  <span>Atualizado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/audio/AudioSystem.hpp"><code>audio/AudioSystem.hpp</code></a></span>
</div>

<p class="doc-lede">Efeitos sonoros sobre SDL3 com um pool fixo de vozes, volume/pan/pitch
por source e atenuação 2D simples por distância. O streaming de música não está
implementado.</p>

---

## Visão Geral

`AudioSystem` abre um dispositivo de reprodução SDL3 e possui um pool de objetos
`AudioSource`. Cada source envolve um `SDL_AudioStream` ligado ao dispositivo:

- **SFX** — o clipe inteiro é enviado para o stream. Uma source livre é reutilizada;
  quando o pool esgota, `playSFX` devolve `nullptr` e o som é descartado.
- **Vozes** — `init(sfxChannelCount, musicChannelCount)` dimensiona o pool de SFX. A
  contagem de canais de música é aceite mas não usada; `Stats::musicPlaying` e
  `musicVolume` são sempre `false` / `0`.
- **Espacial** — uma posição de listener 2D dá queda linear de volume e um valor de pan
  a partir do desvio horizontal. Não há atenuação 3D, cone nem Doppler.

`AudioSystem` é um serviço normal da engine, não um `ECS::ISystem`: o host chama
`update(dt)` uma vez por frame.

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

Todo o header está dentro de `#ifdef CF_HAS_SDL3`; sem SDL3 os tipos não existem.
`registerClip` não copia os bytes: o chamador é dono do buffer enquanto o clipe for
usado.

`setPitch` guarda um valor, mas o caminho de gain do audio stream do SDL3 não faz
resampling, pelo que o pitch é atualmente apenas informativo.

---

## Componente ECS de áudio

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

`AudioEmitter` é um componente em `Caffeine::Audio`, não em `Caffeine::Components`. A
engine guarda-o com a entidade; um runtime ou ferramenta é responsável por registar o
clipe e chamar `playSFXAt`.

---

## Spatial Audio

```text
distance = length(emitter.xy - listener.xy)
volume   = clamp(1 - distance / maxDistance, 0, 1)
pan      = clamp((emitter.x - listener.x) / maxDistance, -1, 1)

listener position ──► setListenerPosition()
emitter position  ──► playSFXAt() or setSourcePosition()
```

`playSFXAt` aplica volume e pan uma vez, no início. `setSourcePosition` atualiza uma
source já a tocar; chama-o em cada frame para um emitter em movimento. O parâmetro
`forward` de `setListenerPosition` é atualmente ignorado.

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
| Pool fixo de sources | Sem alocação durante a reprodução; número de vozes previsível |
| SFX inteiro no stream | Latência mínima para sons curtos |
| Sem streaming de música por agora | `musicChannelCount` e as stats de música estão reservados |
| `update()` na main thread | O callback de áudio do SDL corre na sua própria thread; o estado das sources fica na main thread |
| Queda linear 2D | Barata e previsível para side-scrollers e top-down |
| PCM do chamador | `registerClip` evita uma cópia e deixa os assets viver no seu próprio armazenamento |

---

## Critério de Aceitação

`tests/test_audio.cpp` cobre:

- [x] Estado por omissão de `AudioClip`, `AudioEmitter` e `AudioSystem`
- [x] `init` é idempotente; `shutdown` num sistema não inicializado é seguro
- [x] O volume master faz clamp a 0..1
- [x] A posição do listener e a flag de pausa são guardadas antes do init
- [x] `playSFX(nullptr)` devolve `nullptr`
- [x] `registerClip` devolve um ponteiro de clipe estável
- [x] A atenuação chega a zero em `maxDistance` e a volume total no centro
- [x] `setSourcePosition(nullptr)` não faz nada
- [x] `update` e `shutdown` depois do init não fazem crash
- [x] `stats().sfxPoolUsed` acompanha as sources ativas

Não há teste de crossfade nem de streaming de música porque a funcionalidade não está
implementada.

---

## Dependências

- **Upstream:** áudio SDL3 (`SDL_AudioStream`), [Asset Manager](../assets/asset-manager.md)
- **Downstream:** código de gameplay que reage a eventos e chama `playSFXAt`

---

## 🔗 Tópicos Relacionados

| Tópico | Descrição |
|--------|-----------|
| [ECS Core](../ecs/core.md) | Componentes e queries |
| [Assets & Pipeline](../assets/asset-manager.md) | Como os bytes de áudio são carregados antes de `registerClip` |

## Referências

- [`src/caffeine/audio/AudioSystem.hpp`](https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/audio/AudioSystem.hpp) — dispositivo, sources e helpers espaciais
- [`src/caffeine/audio/AudioComponents.hpp`](https://github.com/devscafecommunity/caffeine/blob/main/src/caffeine/audio/AudioComponents.hpp) — `AudioClip` e `AudioEmitter`
- [`tests/test_audio.cpp`](https://github.com/devscafecommunity/caffeine/blob/main/tests/test_audio.cpp) — suite de comportamento
- [Documentação de áudio do SDL3](https://wiki.libsdl.org/SDL3/CategoryAudio)
