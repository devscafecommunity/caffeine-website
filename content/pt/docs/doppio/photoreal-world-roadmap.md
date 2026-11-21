# Mundo procedural fotorrealista — validação e roadmap

<div class="doc-meta">
  <span class="doc-badge doc-badge--reference">Referência</span>
  <span class="doc-badge">Doppio</span>
  <span>Última atualização: <time datetime="2026-11-21">2026-11-21</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/photoreal-world-roadmap.md"><code>photoreal-world-roadmap.md</code></a></span>
</div>

<p class="doc-lede">Uma seed, ficheiros de regras (<code>.nature</code>, <code>.mat</code>, grafos de terreno e de água) e
streaming determinístico de chunks, para que um mundo fotorrealista inteiro seja gerado a pedido, sempre idêntico, e
em grande parte pré-calculado (baked). Esta página confronta a ideia com o código e lista o que construir, por ordem.</p>

## 1. Veredicto

**Implementável, com a stack atual (editor Rust/Iced, motor C++ sobre SDL3 GPU, C ABI).** Nada na ideia
exige um novo renderer. As partes difíceis não são gráficas: são o *determinismo*, as *fronteiras entre chunks* e
a *ligação dos geradores*. A maioria das funcionalidades de rendering que uma passagem "fotorrealista" pede já existe; a
peça em falta é a **camada de mundo** que liga terreno, natureza, materiais e água.

A ideia tem quatro partes. O seu estado no repositório:

| Ideia | Estado | Evidência |
|---|---|---|
| Materiais procedurais, multifrequência, anti-tiling | **Feito**, afine com receitas | ~123 ops procedurais, 78 presets, classe Variation (`material-pipeline.md`) |
| Profundidade: parallax, micro-sombras, AO, IBL | **Feito** | POM com autossombra, displacement geométrico, AO derivado da altura, env map + IBL por probe (`scene_lit.frag`) |
| Regras como ficheiros (`.nature`, `.mat`, grafos de terreno/água) | **Feito por ferramenta**, sem ligação entre si | cada gerador guarda o seu próprio grafo e coloca assets |
| Seed → mundo determinístico, com streaming por chunk | **Parcial** | `ProceduralStreamer` + `hash01(cx, cz, seed)` existem, mas usam um terreno fbm e props incorporados, não os geradores |
| Vegetação/rochas adaptadas ao terreno, dispersas por máscaras | **Parcial** | o núcleo de scatter + tabela de biomas + **Scene > Scatter on Terrain** (C ABI v16) colocam planos por inclinação, humidade e altura (`terrain-generator-guide.md`); o streaming por chunk e a saída dos geradores como conteúdo de scatter continuam em aberto |
| Instancing, LOD, impostors para vegetação em massa | **Parcial** | existem draws instanciados (também com cor de vértice pintada), vento, translucência e sombras com alpha test; o **LOD por clusters Micromesh** desenha agora partes opacas densas (rochas, troncos) através do renderer de cena (`micromeshes.md`); os cartões de folhagem ainda não têm cadeia de LOD nem impostors |

## 2. Revisão das afirmações da discussão original

Mantidas como verdadeiras, com ressalvas que importam para o desenho.

* **"Estável por seeds derivadas."** Verdade, e já é assim que o streamer funciona (`hash01(cx, cz, seed, salt)`).
  Ressalvas: (1) usar um **hash inteiro** (xxHash ou SplitMix) por célula, nunca somas em vírgula flutuante;
  (2) nunca deixar uma redução paralela decidir a ordem dos resultados, ordenar por id de célula; (3) fixar as chamadas de ruído e de
  `libm` (ou evitar `sin`/`pow` em tudo o que decide a *colocação*), caso contrário duas plataformas colocam
  uma árvore a um metro de distância; (4) versionar o algoritmo: uma alteração a uma op de `.nature` muda todas as árvores, por isso cada ficheiro
  de regras leva um `generator_version` e os mundos antigos mantêm o comportamento antigo ou são re-baked de propósito.
* **"Guardar apenas regra + posição + sub-seed."** Verdade para conteúdo *gerado*. Tudo o que o utilizador *edita* (terreno
  esculpido, uma árvore movida, uma rocha apagada) tem de ser guardado como uma **camada de deltas** esparsa sobre o mundo
  gerado, ou a edição quebra o determinismo. Acrescentar isto desde o início.
* **"Gerar uma vez por chunk, congelar o resultado."** Certo, e resolve a preocupação com o desempenho. Fazer cache por
  `(world_seed, chunk, rule hashes, generator_version)`, em disco e também em RAM (esta é a parte "pré-compilada"
  da ideia).
* **As fronteiras entre chunks são a verdadeira armadilha.** Uma árvore cuja copa atravessa a aresta de um chunk não pode ser duplicada nem
  cortada. Usar **propriedade por célula**: a colocação corre numa grelha global com jitter (ou células de blue-noise/Poisson); uma célula
  pertence a exatamente um chunk, e um chunk gera as suas próprias células *mais uma margem só de leitura* para resolver
  colisões com as células dos vizinhos, pela mesma ordem determinística.
* **"As árvores não atravessam rochas nem outras árvores."** Resolver na *colocação*, não na altura da malha: classes de prioridade
  (rochas, depois árvores, depois arbustos, depois relva), raio de exclusão por classe e uma máscara de densidade. É barato
  e determinístico. Os raycasts por vértice servem apenas para a base do tronco.
* **Adaptação ao chão.** Amostrar `terrain_height(x, z)` (existe na C ABI) e a normal do terreno. As árvores
  usam uma *mistura* de cima e da normal (fator pequeno), as rochas afundam-se pela menor altura sob a sua pegada,
  a relva segue a normal. O alargamento das raízes e as saias das rochas precisam de uma malha de base deformada e de cor de vértice (não feito,
  veja a fase 3).
* **Mistura no contacto.** Correto: cor de vértice na base mais uma mistura com o chão no shader. Precisa do
  canal de **cor de vértice** que o Nature Generator ainda não tem.
* **O código Height-to-AO colado** (Rust, 8 direções): a ideia é certa, e já temos um AO a partir da
  altura. Se for reutilizado: a versão paralela tem um erro de escrita, a direção `(0, 2)` devia ser `(0, -1)`, e
  o termo de inclinação `height_diff / distance` ignora a escala do texel no mundo, pelo que a intensidade do AO muda com
  a resolução. Compare com o nosso antes de substituir fosse o que fosse.
* **"O fotorrealismo é só o grafo."** Em parte. O fotorrealismo depende também da **escala e da variedade**:
  uma textura de casca em todos os troncos parece falsa seja qual for a qualidade. A tinta por instância, a humidade, o vento e a
  variação sazonal importam tanto como mais oitavas de ruído.

Correções específicas deste projeto:

* O texto original fala de `SDL_CreateTexture`, uma API 2D. O motor usa **SDL3 GPU**; os mips já são
  gerados (`createMippedTexture`, filtro box). Melhor filtragem (Kaiser) e uma definição explícita de sampler anisotrópico
  são melhorias opcionais, não uma lacuna.
* A mistura de normais (whiteout) já existe como nó do grafo; o caminho de material da pré-visualização não precisa de
  uma nova função de mistura.
* O IBL especular aqui usa um céu equirretangular e um probe; um **cubemap pré-filtrado com uma BRDF LUT** é
  a forma split-sum correta e uma possível melhoria de qualidade, não uma funcionalidade em falta.

## 3. Arquitetura alvo

```text
world.cworld  (seed, generator_version, layer list, edit deltas)
   ├─ terrain graph  → height + masks (slope, wetness, flow, biome)   [exists: terrain generator]
   ├─ biome rules    → density per class from the masks               [new]
   ├─ scatter rules  → .nature / .rock / grass refs + placement rules [new]
   ├─ water graph    → water bodies from flow and sea level           [partial]
   └─ material layers→ splat/blend from the same masks                [partial]

per chunk (worker thread, deterministic):
   masks → placement (cells, priority, exclusion) → instances (transform + sub-seed + variant)
        → bake cache (RAM + disk) → GPU instance buffers per LOD → draw
```

Princípios: (1) um chunk é uma **função pura** do ficheiro de mundo e das suas coordenadas; (2) os geradores produzem
**dados** (campos, listas de instâncias, malhas), o renderer nunca executa um grafo; (3) apenas comandos através de
`Message`s e ações MCP, como no resto do Doppio; (4) `libcaffeine-capi` continua a ser a única fronteira.

## 4. Roadmap

Cada fase termina com algo visível e testável em headless. Façam-se por ordem; as fases 1 e 2 são
independentes do trabalho no renderer.

### Phase 0 — Base de determinismo

- [x] `core/Hash.hpp`: SplitMix64 `deriveSeed(parent, salt, x, z)`, `toUnit`, `GENERATOR_VERSION`; o teste golden
      `tests/test_hash.cpp` fixa as saídas, `recipe_ref.rs` fixa os mesmos números em Rust.
- [x] As decisões de colocação do streamer passam por `placementHash(version, ...)`: a versão 1 é o `hash01` legado, a versão 2 o
      SplitMix64 de `core/Hash.hpp`. `ProceduralWorldComponent::generatorVersion` guarda a escolha e **por omissão é 1**, por isso
      os mundos existentes não se movem; os mundos novos devem definir `Core::GENERATOR_VERSION`. Testado em `tests/test_scatter.cpp`.
- [x] Campo `generator_version` em todas as receitas `generator.*` (nature, material, texture, terrain, water).
- [ ] O mesmo campo em ficheiros `.mat` simples e no ficheiro de mundo (ainda não há ficheiro de mundo).
- [x] Teste: as seeds derivadas para um bloco de células são idênticas com 1 e com 7 threads (`tests/test_hash.cpp`).
- [x] O mesmo teste para chunks de scatter gerados por inteiro: 1 e 7 threads dão resultados idênticos, e cortar o mundo em
      chunks de 32 m, 48 m ou 96 m dá as mesmas instâncias (`tests/test_scatter.cpp`). Os chunks inteiros do streamer (cubos) ainda por fazer.

### Phase 1 — Máscaras de terreno exportadas para o motor

- [x] O terreno expõe **máscaras** com nome como campos legíveis pelo motor: `height`, `slope` e `curvature` derivadas pelo motor a partir do
      heightfield (exatas, nada guardado), e `flow` (drenagem D8), `wetness`, `wear` e `deposit` (erosão) enviadas pelo gerador como máscaras de
      8 bits, guardadas com o ficheiro do terreno (versão 3). O nó Output ganhou entradas opcionais Wear e Deposit (os presets com erosão
      ligam-nas). 8 bits é a única precisão; as máscaras de 16 bits foram abandonadas por desnecessárias para pesos. Imagem em `terrain-generator-guide.md`.
- [x] C ABI v15: `set_terrain_mask`, `terrain_mask_count/at`, `terrain_mask` num ponto, `terrain_mask_rect` sobre um retângulo,
      `terrain_normal` num ponto (struct de informação POD); a crate Rust encapsula-as. Testado dos dois lados: `tests/test_terrain_masks.cpp`,
      `tests/test_capi.cpp`, e um teste do Doppio com motor que coloca a Alpine Range e verifica cada máscara contra as alturas.
- [x] **Tabela de biomas** (`terrain/TerrainBiome`): por classe de scatter, `base x` um produto de termos trapezoidais sobre máscaras, em texto simples, ligada ao
      callback de densidade do módulo de scatter; uma máscara desconhecida não coloca nada e é listada por `missingMasks`. Testada com o módulo de scatter
      (árvores nunca em terreno íngreme ou húmido, rochas só na crista). Ainda não lida nem escrita pelo editor: isso é o separador World (fase 6).
- [ ] Máscaras ainda por fazer: *bandas* de altura como máscaras com nome (`height` cobre o valor bruto; uma banda é hoje um termo de bioma), uma máscara `wear` para
      terrenos que não usaram erosão hidráulica, e máscaras pintadas no editor.

### Phase 2 — Motor de scatter (núcleo, sem UI)

- [x] Módulo `scatter` (`src/caffeine/scatter/Scatter.hpp`): grelha com jitter por classe, densidade vinda de um callback (os mapas de bioma
      ligar-se-ão aí), raios de exclusão, ordem de prioridade, propriedade por posição e uma margem para as fronteiras de chunk. Os conflitos usam uma
      **regra não recursiva** (um ponto cede perante qualquer ponto mais próximo com uma chave mais alta, sobreviva este ou não), de modo que um chunk
      precisa apenas de uma margem de dois raios e nunca depende dos vizinhos nem da ordem de carregamento.
- [x] Saída: lista de instâncias `(position, up, yaw, scale, variant, sub-seed, tint)`; adaptadas à altura e à normal com regras
      por classe (`tiltToNormal`, `sink` por escala, jitter de tinta, intervalo de escala). O afundamento das rochas pelo mínimo da pegada continua a ser uma única
      amostra no centro.
- [x] Testes: sem sobreposição dentro e através das fronteiras de chunk (todos os pares em 3 x 3 chunks); mesmo resultado para qualquer divisão em chunks e ordem de carregamento;
      a densidade segue a máscara; as classes de prioridade não são afetadas pelas inferiores.
- [x] **C ABI v16 e a ação *Scatter* do Doppio**: `scatterTerrain` (região, independente do tamanho do chunk) por trás de `caffeine_session_scatter_terrain` e
      `caffeine_biome_check`; *Scene > Scatter on Terrain* e a ação de agente `scatter_on_terrain` colocam um plano de texto (`Scatter/*.scatter`) como entidades num
      só passo de undo, com a tabela de biomas como densidade. Testado em `tests/test_scatter.cpp`, `tests/test_capi.cpp` e com motor no Doppio
      (`terrain-generator-guide.md`).

### Phase 3 — Assets de natureza que podem ser dispersos

- [x] **Cor de vértice** e um **peso de flutter pintado** na saída de malha do Nature: OBJ `v x y z r g b a`, lido pelo motor para um
      segundo stream de vértices (sem alteração de ABI); o balanço ao vento, o flutter e a translucência são campos do material (C ABI v9).
- [x] **Slots de material por submalha**: os grupos `usemtl` do OBJ carregam como submalhas, o `Material slots` do Mesh Filter (`a.mat;b.mat`) dá a cada uma o seu próprio
      material (um draw por slot, por isso sombras, alfa e Micromesh seguem o slot), sem alteração de ABI; o *Merge parts* do gerador Nature
      coloca um modelo como uma entidade sólida e uma recortada, com um slot por parte. Testado em `tests/test_material_slots.cpp` e com motor no Doppio.
- [ ] Deformação da base: alargamento das raízes e saia da rocha a partir de um callback de altura do chão na altura do bake.
- [x] Variantes: N seeds por receita nature, geradas para um conjunto de variantes em cache (`recipe_ref::nature_variants`, `doppio-material variants`).
- [x] Tinta por instância e intervalo de escala (`ScatterClass::tintJitter`, `minScale`/`maxScale`). Aplicar a tinta através do modificador do Mesh Renderer
      (C ABI v10) é o último passo em falta da integração do scatter.
- [ ] Mistura de contacto com o chão no shader (da rocha/tronco para a cor do chão usando a cor de vértice).

### Phase 4 — Rendering em escala

- [ ] Vegetação instanciada na GPU com buffers de instâncias por chunk. O caminho instanciado cobre agora também malhas com um stream de
      cor pintada (as partes de scatter nature são colocadas como cópias em lote); o limite de 256 por lote e os buffers por chunk continuam.
- [x] **LOD por clusters para partes opacas** (rochas, troncos, boulders): Mesh Renderer -> Micromesh desenha uma malha como um corte de clusters escolhido na GPU,
      sem fissuras, com cascatas de sombras, cores de vértice e submalhas, e oclusão opcional. Medido em 81 rochas densas e numa floresta de 300 árvores:
      6.1x e 3.3x menos triângulos (`micromeshes.md`, `./scripts/benchmark-micromesh.sh`).
- [ ] Cadeia de LOD a partir do mesmo grafo para o que o Micromesh não aceita (cartões de folhagem com alpha test, partes animadas pelo vento): cartões
      simplificados e um **atlas de impostors billboard** gerado por variante, com troca por distância e tamanho no ecrã e cross-fade com dithering. Também em aberto:
      o gerador Nature liga agora o Micromesh nas partes sólidas com 3 000 triângulos ou mais (a opção *Micromesh* do Nature); o terreno e a água não.
- [ ] Culling por chunk, depois por instância, primeiro no CPU; culling na GPU só se o profiling o pedir. (O culling de frustum por instância
      existe e é contado nas estatísticas de fotograma; ainda não há chunks; o Micromesh faz culling de clusters na GPU, com oclusão contra a profundidade do
      fotograma anterior, para as malhas que aderem.)
- [x] Vento (estágio de vértice, também na passagem de sombras), translucência das folhas, um normal map nos cartões de folhas e sombras com alpha test para
      cartões recortados.

### Phase 5 — Streaming e cache

- [ ] Jobs de chunk na thread pool do motor com uma fila de prioridade e um orçamento de tempo por fotograma; nunca bloquear o
      viewport (mesma regra dos bakes dos geradores).
- [ ] Cache de bake persistente indexada por `(seed, chunk, rule hashes, generator_version)`; invalidação quando um
      ficheiro de regras muda.
- [ ] Camada de edição: deltas esparsos para esculpir, instâncias movidas ou removidas; aplicados depois da geração.
- [x] Lado do motor de heightfields maiores: a C ABI aceita terrenos até 4097 x 4097 e o LOD por chunks desenha-os; um terreno de 1025 x 1025
      (2.1 M de triângulos) submete cerca de 0.84 M em cerca de 410 draws (conjunto de benchmarks). Medido, não apenas permitido.
- [ ] O gerador de terreno continua a produzir apenas 129, 257 ou 513, e não há tiling nem streaming de um terreno maior do que um heightfield
      (o guia do terreno ainda diz 513 e lista um caminho em tiles ou na GPU; o texto dos limites é anterior à medição de 1025).

### Phase 6 — Integração no editor

- [ ] Um separador **World**: seed, lista de camadas, tabela de biomas, ficheiros de regras por classe, pintura por região de overrides.
- [ ] Colocar e pré-visualizar uma grelha de chunks no viewport; mostrar acertos de cache e o tempo de build do chunk no HUD.
- [ ] Entradas `UiId`, edições com undo (`App::commit`), ações MCP e um flow headless para cada passo.
- [ ] Docs: atualizar os guias de Nature, Terrain e Water e as páginas do site; regenerar as capturas através
      do driver headless.

### Phase 7 — Passagem de qualidade visual (trilho paralelo)

- [ ] Cubemap de ambiente pré-filtrado + BRDF LUT (split-sum); manter o caminho atual como fallback. (Hoje: o céu equirretangular com mips,
      probes por objeto e uma aproximação analítica split-sum do termo BRDF em `scene_lit.frag`.)
- [x] Modificadores em tempo de execução (C ABI v10): tinta, humidade, neve, idade no Mesh Renderer e no material; os scripts podem controlá-los por
      entidade. Controlá-los a partir de máscaras de terreno está em aberto.
- [x] Água na GPU: ondas de Gerstner no vertex shader (sem reconstrução da malha por fotograma), detalhe de ondulação, cor de profundidade e espuma.
- [x] Conjuntos de casca gerados (carvalho, pinheiro, bétula) com relevo parallax; as superfícies de relva e solo a partir do bake Rock Surface continuam em aberto.
- [ ] Cenas de referência com seeds fixas, desenhadas em headless, usadas como baselines de regressão visual. (O conjunto de benchmarks já
      gera o seu conteúdo por hashes, byte a byte idêntico, e as suas contagens de triângulos e draws reproduzem-se exatamente, mas nada compara
      imagens com uma baseline guardada ainda; os testes de mancha escura da água e da cena Micromesh comparam dois renders da mesma execução.)

### Ponto da situação (2026-11-20)

22 itens feitos, 17 em aberto. O trabalho concluído é a **base e o lado do rendering**; o que falta é a **camada de mundo** que
liga os geradores, que esta página apontou como a peça em falta desde o início.

| Fase | Feitos | Em aberto | Estado |
|---|---|---|---|
| 0 Determinism | 5 | 1 | completa para o que existe (hash, versões, testes com várias threads); o ficheiro de mundo ainda não existe |
| 1 Terrain masks | 3 | 1 | **feita** (7 máscaras, C ABI v15, tabela de biomas); máscaras pintadas e bandas em aberto |
| 2 Scatter engine | 4 | 0 | **feita**: núcleo, C ABI v16 e a ação Scatter colocam planos pelas máscaras do terreno |
| 3 Scatterable nature | 4 | 2 | cor de vértice, variantes, tinta/escala e **slots de material** feitos; alargamento das raízes e mistura com o chão em aberto |
| 4 Rendering at scale | 2 | 3 | vento/translucência/sombras e **LOD por clusters Micromesh** feitos; LOD de folhagem e impostors, buffers de instâncias por chunk em aberto |
| 5 Streaming and caching | 1 | 4 | o motor aceita terrenos grandes; sem jobs de chunk, sem cache de bake, sem camada de edição |
| 6 Editor integration | 0 | 4 | **não iniciada** (sem separador World) |
| 7 Visual quality | 3 | 2 | modificadores, água na GPU, casca feitos; cubemap pré-filtrado e baselines de imagem em aberto |

**O que falta, pela ordem que desbloqueia mais** (cada item entrega-se isoladamente):

1. ~~Fase 1, máscaras para o motor~~ **feito**: o callback de densidade do módulo de scatter, os modificadores em tempo de execução e a mistura splat/material
   já podem ler máscaras.
2. ~~Fase 2, a ação Scatter~~ **feito**: o núcleo de scatter concluído, a tabela de biomas, as variantes, a tinta e os caminhos de desenho Micromesh/instanciado
   aparecem agora numa cena (*Scene > Scatter on Terrain*). O seu limite é a escala: cada instância é uma entidade, o que os buffers por chunk da fase 4 resolvem.
3. ~~Fase 3, slots de material por submalha~~ **feito**, com o gerador Nature a ligar o **Micromesh** nas partes sólidas densas. O que resta da
   fase 3 é a deformação da base (alargamento das raízes, saia da rocha) e a mistura de contacto com o chão no shader; ambas querem a altura do terreno na altura
   do bake, que a ação de scatter já tem.
4. **Fase 4, folhagem**: cartões simplificados e um atlas de impostors billboard, depois buffers de instâncias por chunk e culling por chunk.
5. **Fase 5**: jobs de chunk com orçamento de tempo, a cache de bake, depois a camada de edição (desenhe o formato de deltas antes de o editor existir).
6. **Fase 6**: o separador World, quando 1 a 5 lhe derem algo para controlar. As baselines de imagem da fase 7 podem começar já: existe uma cena de scatter para desenhar
   (`scripts/render-scatter-docs.sh`).

A única decisão que não é de engenharia: o **ficheiro de mundo** (`world.cworld`) ainda não tem dono. As fases 0, 5 e 6 precisam dele; defina as suas
camadas e o formato de deltas antes da fase 5.

## 5. Riscos

| Risco | Mitigação |
|---|---|
| Diferenças de vírgula flutuante alteram a colocação entre máquinas | hash inteiro, algoritmo versionado, testes golden (fase 0) |
| Duplicados ou falhas nas fronteiras de chunk | propriedade por célula e margem só de leitura (fase 2) |
| Soluços de geração durante o movimento | jobs com orçamento de tempo, cache, anel de prefetch (fase 5) |
| Muitos materiais por árvore quebram o batching | slots por submalha (feito: uma entidade, um draw por slot, os lotes instanciados continuam a funcionar por slot), variantes em atlas, impostors (fases 3, 4) |
| As edições do utilizador quebram o determinismo | camada de deltas esparsa desde o primeiro dia (fase 5) |
| Âmbito: sete geradores num só mundo | cada fase entrega-se isoladamente e é útil sem a seguinte |

## 6. Relacionado

- [`material-pipeline.md`](material-pipeline.md): materiais, profundidade, variação.
- [`nature-generator-guide.md`](nature-generator-guide.md): receitas, lacunas de LOD e instancing.
- [`terrain-generator-guide.md`](terrain-generator-guide.md): máscaras, camadas de splat, limites.
- [`water-generator-guide.md`](water-generator-guide.md): superfície de água e `water_height`.
- [`graphics-roadmap.md`](graphics-roadmap.md): o lado do renderer (Micromeshes, Photon).
- [`micromeshes.md`](micromeshes.md): a hierarquia de clusters e o corte na GPU que os troncos e rochas densos usam agora, com o conjunto de benchmarks.
