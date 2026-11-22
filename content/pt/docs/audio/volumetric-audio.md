# Áudio volumétrico

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Estável</span>
  <span class="doc-badge">Áudio</span>
  <span>Última atualização: <time datetime="2026-11-22">2026-11-22</time></span>
</div>

<p class="doc-lede">Um mixer opcional que simula como o som viaja pelo mundo: chega atrasado, sofre efeito Doppler, é abafado pelo que está no caminho, contorna esquinas, ecoa e soa com a sala, e fica mais claro à medida que se chega perto.</p>

O `VolumetricMixer` (`src/caffeine/audio/volumetric/`) é separado do `AudioService`: um jogo que quer som 2D ou 3D simples
continua a usá-lo. O mixer não precisa de placa de som. Renderiza blocos de amostras estéreo, por isso o mesmo código alimenta um dispositivo
em jogo, um ficheiro WAV num teste e um vídeo nas demonstrações.

## 1. O que uma voz atravessa

| Etapa | O que faz |
|---|---|
| Propagação | O clip é lido em `t - distância / c`, por isso um tiro a 150 m ouve-se 0.44 s depois. Uma fonte em movimento muda esse atraso continuamente, o que **é** o efeito Doppler: exato, sem truques de pitch (`dopplerScale` 0 congela-o) |
| Distância | Ganho pela lei inversa (metade por cada duplicação) e absorção do ar: o corte desce com a distância, por isso o som próximo é claro e o distante é abafado |
| Oclusão | O segmento fonte-ouvinte é traçado pelo `AcousticWorld`. O que uma parede deixa passar é baixo e abafado: os graves atravessam paredes muito melhor do que os agudos, e paredes mais grossas deixam passar menos |
| Difração | Se o som pode contornar o obstáculo (o fim de uma parede, uma porta) esse caminho também é misturado, mais baixo e abafado com a distância extra, e a voz ouve-se a vir da abertura |
| A sala | 31 raios à volta do ouvinte (até 300 m) dão o tamanho, a abertura, a exposição ao céu e a refletividade. Uma rede de atrasos com realimentação (8 linhas) ajusta a cauda e o nível do reverb a eles, e superfícies duras distantes devolvem ecos distintos a `2 d / c`. Uma fonte atrás de uma parede está noutra sala: essa sala também é lida, e o seu próprio reverb passa através da parede |
| Clareza | O reverb cai mais devagar do que o som direto, por isso o som distante é mais "molhado" e o próximo é seco e claro. O que chega à sala por trás de uma parede é só o que a parede deixa passar |
| Ouvidos | Uma cabeça esférica (8.75 cm): a diferença de tempo de Woodworth (até 0.66 ms) e a sombra da cabeça de Brown e Duda, um filtro que realça os agudos no ouvido virado para o som e os corta muito no ouvido distante (os graves chegam a ambos), e uma retaguarda mais abafada. Sem ficheiros de dados HRTF |
| Camadas | **World** é espacial; **Ambient** (chuva, vento) cobre a cena e segue a exposição do ouvinte, abafado e mais baixo sob um telhado; **Music** e **Ui** são simples. Cada camada tem o seu volume |

## 2. Como usar

```cpp
AcousticBoxWorld world;                       // ou o seu próprio AcousticWorld sobre os colliders do jogo
world.add({-500, -1, -500}, {500, 0, 500}, AcousticMaterial::ground(), false);
world.addRoom({-8, 0, -6}, {8, 3, 6}, AcousticMaterial::brick(), 0.3f, /*door*/ 2.0f);

VolumetricMixer mixer(48000);
mixer.setWorld(&world);
mixer.setListener(camera.position, camera.forward);
VoiceId siren = mixer.play({.clip = clip, .position = start, .loop = true});
// a cada bloco de áudio (cerca de 5 ms): mexa nas coisas e misture
mixer.setPosition(siren, vehicle.position);
mixer.render(stereo, 256);
```

Mova as vozes e o ouvinte entre blocos, com blocos pequenos: o efeito Doppler é a variação do atraso de um bloco para o
seguinte. `debug(voice)` comunica o que o mixer decidiu (distância, atraso, razão de pitch, ganho, corte, bloqueada, difratada, de onde o
som parece vir), e `room()` o que os raios leram. `settings()` desliga cada etapa (`occlusion`, `diffraction`,
`reverb`, `airAbsorption`, `propagationDelay`, `ears`).

## 3. O mundo que o som atravessa

O `AcousticWorld` responde a duas perguntas: a transmissão entre dois pontos, e até onde vai um raio antes de bater em algo.
O `AcousticBoxWorld` é um conjunto de caixas, alinhadas aos eixos ou **orientadas** (centro, meias dimensões, três eixos: um cubo escalado e rodado até ser uma parede), com materiais (`concrete`, `brick`, `wood`, `glass`, `foliage`, `curtain`, `ground`), e `addRoom` para quatro paredes, um teto e uma porta opcional. Um material diz quanto dos graves e dos agudos passa em 20 cm dele e
quanta energia reflete. Um jogo com outras formas implementa a interface sobre os seus próprios colliders.

## 4. No editor e numa cena

A cena decide o que se ouve, com três componentes refletidos (o Inspector e os scripts editam-nos como a qualquer outro):

| Componente | O que faz |
|---|---|
| `Volumetric Audio` | As definições: ligado, os volumes das camadas e o geral, a escala do Doppler, a velocidade do som, e um interruptor para cada etapa da secção 1. Sem um ligado nada é misturado |
| `Audio Emitter` | Um som: `Clip Path` (um WAV, procurado como escrito e depois na raiz de assets), `Volume`, `Loop`, `Play On Spawn`, `Max Distance`, e os novos `Layer` (0 World, 1 Ambient, 2 Music, 3 Ui), `Ref Distance` e `Doppler` |
| `Acoustic Obstacle` | A transformação da entidade aplicada a um cubo unitário é uma caixa que o som não atravessa: um material predefinido (`Material`) ou um próprio (`Custom`, `Transmission Low/High`, `Reflectivity`) |

O tempo é tocado pelo mesmo mixer quando uma cena tem ambos: os leitos de chuva e de vento são vozes Ambient (abafadas e mais baixas sob um telhado) e cada estrondo de trovão é uma voz World lá no céu na sua direção, por isso uma parede abafa-o, um salão ressoa com ele e os ouvidos situam-no. `Weather` > `Audio Enabled` e `Audio Volume` ligam-no, como antes; o estrondo não é atrasado duas vezes (`propagate` desligado nessa voz, porque o relógio do próprio raio já esperou o tempo de viagem).

O `SceneAudio` lê-os uma vez por frame, constrói um novo mundo de caixas só quando os obstáculos mudaram, e dá às vozes e ao ouvinte uma
velocidade a partir do tempo entre frames, por isso o mixer leva-os em frente com suavidade e o desvio Doppler fica contínuo a qualquer taxa de frames.
A câmara do viewport é o ouvinte. O `VolumetricAudio` é dono do mixer, de um trinco e do dispositivo de som opcional (o predefinido do sistema ou um de `outputDevices()`, listados numa ordem estável), que puxa blocos na
thread de áudio; sem dispositivo a sessão mistura em silêncio ("monitoriza"), por isso os números continuam a mexer e os testes podem puxar amostras
com `caffeine_session_volumetric_render`. A C ABI v20 acrescenta `caffeine_session_volumetric_state`, `caffeine_session_volumetric_voice`,
`caffeine_session_set_audio_output`, `caffeine_session_set_audio_output_device`, `caffeine_audio_output_device_count`/`_name` e `caffeine_session_volumetric_render`.

O separador **Audio** do Doppio (menu View, com Inspector, Profiler, Photon e Environment) acrescenta o componente, edita-o com desfazer, liga e desliga as
colunas, escolhe o dispositivo de som, acrescenta uma fonte ou uma parede de 6 x 3 x 0.3 m, e mostra ao vivo o que o mixer decide: a sala à volta do ouvinte e uma
linha por som (distância, nível, passa-baixo, desvio de pitch, atrás de uma parede ou à volta de uma esquina). Os agentes usam `show_audio`, `audio`,
`audio_add`, `audio_set`, `audio_output`, `audio_device`, `audio_add_source` e `audio_add_wall`.

O `caffeine-runtime` também o aloja: a cada frame sincroniza a cena a partir da Camera 3D ativa, alimenta o tempo a partir do seu renderer, e abre o dispositivo de som na primeira frame em que a cena tem um componente `Volumetric Audio`.

## 5. Ouvir

O `scripts/render-audio-demo.py` renderiza quatro cenários com sons de `references/moodist` e escreve vídeos em
`build/audio-demo/videos/` (uma vista de cima da cena com o que o mixer está a fazer, e o áudio):

| Vídeo | O que ouvir |
|---|---|
| `doppler.mp4` | Uma ambulância a 108 km/h com Doppler ligado e desligado, depois um avião a 150 m/s |
| `shots.mp4` | Um tiro a 150 m num campo com um penhasco distante (atrasado, abafado, com eco), o mesmo tiro num salão de betão, e de fora da sua parede |
| `occlusion.mp4` | Um rádio atrás de uma parede, depois à volta do seu fim; uma ventoinha dentro de uma casa, depois à sua porta |
| `layers.mp4` | Chuva e vento fora e dentro de uma casa, uma lareira a que se chega, trovão através das paredes, e a camada ambiente a 30% |

Precisa de `cmake --build build --target caffeine-audio-demo`, ffmpeg, Pillow e numpy.

## 6. Testes e limites

* `tests/test_scene_audio.cpp`: as emissoras tornam-se vozes, um obstáculo bloqueia-as, mover e remover, sem componente há silêncio, e
  o tempo através do mixer (os leitos seguem-no, um telhado abafa-os, um estrondo vem do seu lado do céu).
  `tests/test_volumetric_audio.cpp`: o nível reduz-se a metade com a distância, o atraso é `d / c`, o desvio Doppler corresponde a `1 / (1 -+ v / c)`
  em 2%, o som próximo é mais brilhante, uma parede tira pelo menos 15 dB e mais nos agudos do que nos graves, uma parede mais grossa tira mais, uma
  parede curta é contornada e ouve-se da sua esquina, os raios leem salas abertas e fechadas e ecos distantes, um tiro ressoa num salão e ecoa num
  penhasco, os ouvidos, a camada ambiente dentro de casa e os volumes das camadas, e o limitador.
* A geometria são caixas (orientadas, a partir de uma cena); malhas de triângulos não são traçadas. A acústica é um modelo, não um solver de ondas: a oclusão
  é um segmento traçado mais o melhor desvio, a sala do ouvinte e a de uma fonte atrás de uma parede são ajustadas cada uma pelos seus raios
  e reverb partilhado, e os ecos vêm dos raios do ouvinte.
* O mixer é mono por voz, e os ouvidos são um modelo de cabeça esférica, não dados HRTF medidos: esquerda e direita são boas, à frente e atrás
  e cima e baixo são só sugeridos (uma retaguarda abafada). Nada mais muda: uma cena sem o componente soa como antes.
