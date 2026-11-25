# Doppio: os guias do editor

<div class="doc-meta">
  <span class="doc-badge doc-badge--reference">Referência</span>
  <span class="doc-badge">Doppio</span>
  <span>Última atualização: <time datetime="2026-11-21">2026-11-21</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine-website/tree/main/content/en/docs/doppio"><code>content/en/docs/doppio</code></a></span>
</div>

<p class="doc-lede">Os guias do editor Doppio em Rust/Iced: como a UI é construída, como a controlar sem janela, e os geradores que
fazem rochas, árvores, água, terreno, texturas e materiais. O repositório do motor guarda os mesmos ficheiros junto ao código.</p>

## 1. O editor

| Página | O que cobre |
|---|---|
| [`rust-ui.md`](rust-ui.md) | Arquitetura do editor Iced: painéis, componentes, ids, mensagens, a ponte para agentes |
| [`headless-testing.md`](headless-testing.md) | O driver `doppio-headless`: ações, alvos, fluxos, capturas de ecrã |
| [`gizmos-and-markers.md`](gizmos-and-markers.md) | Gizmos de transformação e marcadores de cena para luzes, câmaras e colisores |
| [`runtime-modifiers.md`](runtime-modifiers.md) | Tinta, humidade, neve e idade nos materiais em tempo de execução |

## 2. Geradores

| Página | O que cobre |
|---|---|
| [`generator-recipes.md`](generator-recipes.md) | Receitas `generator.*`, prefabs e como uma coisa gerada continua editável |
| [`nature-generator-guide.md`](nature-generator-guide.md) | Rochas, árvores e plantas a partir de um grafo de nós, o nó Edit Library Material |
| [`terrain-generator-guide.md`](terrain-generator-guide.md) | Terrenos a partir de fontes de campo, modificadores, máscaras e erosão |
| [`water-generator-guide.md`](water-generator-guide.md) | Superfícies de água a partir de fontes de ondas e modificadores |
| [`texture-generator-guide.md`](texture-generator-guide.md) | Texturas, VFX e flipbooks a partir de um grafo de nós |
| [`materials-guide.md`](materials-guide.md) | A biblioteca de materiais, profundidade, variação e escala UV, com renders |
| [`material-pipeline.md`](material-pipeline.md) | A lista viva do pipeline de materiais |

## 3. Renderização e roadmaps

| Página | O que cobre |
|---|---|
| [`micromeshes.md`](micromeshes.md) | Micromeshes: uma hierarquia de clusters e um corte na GPU para malhas densas |
| [`photon-guide.md`](photon-guide.md) | Photon: iluminação global, o separador Photon, o volume de voxels e as suas estatísticas |
| [`profiler-guide.md`](profiler-guide.md) | Profiler: scopes cronometrados do renderer, GPU timing, o separador Profiler e como ler um perfil |
| [`environment-guide.md`](environment-guide.md) | Environment: nuvens, névoa de altura e chuva, o separador Environment, e como concordam com o sol e o Photon |
| [`graphics-roadmap.md`](graphics-roadmap.md) | O plano do renderer: Micromeshes, Photon e o que vem a seguir |
| [`photoreal-world-roadmap.md`](photoreal-world-roadmap.md) | O plano de conteúdo: terreno, natureza, água, scatter e streaming |
| [`terrain-editing-roadmap.md`](terrain-editing-roadmap.md) | O plano de edição de terreno: pincéis customizados, paleta de materiais, vegetação adaptativa e o formato nativo do terreno |
| [`terrain-editing-phase-0.md`](terrain-editing-phase-0.md) | A base da edição de terreno como foi construída: modelo de tiles, motor de traço, contêiner nativo, GI regional, cursor do pincel, C ABI 25 a 27 |
| [`terrain-editing-phase-4.md`](terrain-editing-phase-4.md) | Espécies do terreno a partir de receitas como construídas: variantes geradas com um material por parte, regeneração automática, adaptação por máscara, C ABI 31 |
| [`terrain-editing-phase-3.md`](terrain-editing-phase-3.md) | A vegetação do terreno como foi construída: espécies, fontes procedural e manual, ids estáveis, ferramentas de pincel, renderização instanciada por chunk, a aba Terrain Vegetation, C ABI 30 |
| [`terrain-editing-phase-2.md`](terrain-editing-phase-2.md) | A pintura de materiais do terreno como foi construída: uma paleta de até 64 camadas, o mapa de camadas, traços de pintura, auto-camadas, o renderizador com textura array, a aba Terrain Paint, C ABI 29 |
| [`terrain-editing-phase-1.md`](terrain-editing-phase-1.md) | A escultura de terreno como foi construída: 16 modos de pincel, 58 pincéis, arquivos `.brush`, simetria, proteção, a aba Terrain Brush, C ABI 28 |
