# Edição de terreno: relatório da Fase 5.1 (máscaras pintadas)

<div class="doc-meta">
  <span class="doc-badge doc-badge--beta">Em curso</span>
  <span class="doc-badge">Doppio</span>
  <span>Última atualização: <time datetime="2026-11-26">2026-11-26</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/pt/docs/doppio/terrain-editing-phase-5-masks.md"><code>terrain-editing-phase-5-masks.md</code></a></span>
</div>

<p class="doc-lede">Uma máscara guardada do terreno editada com o pincel que esculpe e pinta camadas. Uma máscara pintada é uma máscara normal, por isso regras, auto-layering, proteção do pincel e as adaptações de tamanho e cor das espécies de vegetação a leem, e as plantas sob um traço são resolvidas outra vez enquanto se pinta.</p>

## 1. O que entrega

<table>
  <thead><tr><th>Peça</th><th>Onde</th><th>O que faz</th></tr></thead>
  <tbody>
    <tr><td>Pincel de máscara</td><td><code>terrain/paint/TerrainMaskPaint.*</code></td><td>Carimbos postos por espaçamento em metros com o pincel partilhado (raio, falloff, carimbo, jitter, simetria, proteção). Paint leva a máscara para um nível, Erase para 0 e Smooth para os vizinhos.</td></tr>
    <tr><td>Edições da máscara inteira</td><td><code>createMask</code>, <code>editMask</code></td><td>Criar (vazia, um nível, ou cópia de slope, height, curvature ou de outra máscara), preencher, inverter, apagar.</td></tr>
    <tr><td>Desfazer</td><td><code>MaskRecord</code></td><td>Blocos de 64 x 64 texels num traço, a máscara inteira nas outras edições; exato e pequeno por maior que seja a máscara.</td></tr>
    <tr><td>Vegetação</td><td><code>TerrainCache::commitMaskEdit</code></td><td>Só os chunks que a edição alcança são resolvidos e desenhados outra vez.</td></tr>
    <tr><td>C ABI 33</td><td><code>capi/EngineAPI.*</code></td><td><code>caffeine_session_terrain_mask_paint_begin</code>, <code>_mask_create</code>, <code>_mask_edit</code></td></tr>
    <tr><td>Aba Terrain Paint</td><td><code>uikit/panels/terrain_paint.rs</code>, <code>windows/main/terrainpaint.rs</code></td><td>Um card <em>Masks</em>: as máscaras guardadas, criar vazia ou cópia, preencher, inverter, apagar, e um interruptor que faz o pincel pintar a máscara escolhida em vez das camadas.</td></tr>
  </tbody>
</table>

## 2. Como funciona

- Um traço calcula em floats e grava o byte arredondado, por isso um pincel suave de baixa força mantém o falloff em vez de saltar níveis inteiros. O mesmo caminho dá a mesma máscara a 30 e a 240 amostras por segundo.
- Uma máscara tem uma grelha própria (a do terreno por omissão), até 16 por terreno, guardada com o ficheiro do terreno.
- As máscaras built-in (height, slope, curvature) derivam do chão e não se pintam nem se editam; copie uma para pintar por cima.
- O pincel usado é o do Terrain Paint: os seus números, a forma do Terrain Brush quando pedida, Ctrl para inverter e Shift para suavizar. A pintura por camadas não precisa de estar ligada.

## 3. C ABI 33

<code>CAFFEINE_CAPI_VERSION</code> é 33. Pintar é um traço como os outros: <code>caffeine_session_terrain_stroke_point</code>, <code>_stroke_end</code>, <code>_stroke_revert</code> e <code>_stroke_reapply</code> funcionam para ele sem mudança. Criar, preencher, inverter e apagar são uma edição desfazível cada (devolve-se um id de registo).

```c
CaffeineMaskBrush brush = {0};
brush.mode = CAFFEINE_MASK_PAINT;
brush.value = 1.0f;
caffeine_session_terrain_mask_create(session, terrain, "wet", 0, 0, 0.0f, NULL, &record, error, sizeof error);
caffeine_session_terrain_mask_paint_begin(session, terrain, &brush);
```

## 4. Ações de agente

<code>terrain_mask_make</code>, <code>terrain_mask_select</code>, <code>terrain_mask_target</code>, <code>terrain_mask_value</code> e <code>terrain_mask_edit</code>. Depois de <code>terrain_mask_target</code>, <code>terrain_paint_stroke</code> pinta a máscara ao longo dos seus pontos; a consulta <code>terrain_paint</code> lista as máscaras.

## 5. Verificação

- C++: <code>tests/test_terrain_mask_paint.cpp</code> (4 casos: criar e copiar, pintar, apagar e suavizar com undo exato, falloff em 8 bits independente da amostragem, proteção, simetria e as edições da máscara inteira) e um caso da C API em que um pinheiro só cresce no chão pintado, desaparece no undo e a máscara sobrevive a guardar a cena.
- Rust: um teste do crate do motor com as novas chamadas e quatro testes da aba (criar uma máscara sem camadas, um arrasto do rato é um traço que se desfaz, um traço de agente, preencher, inverter e apagar, e pedidos inválidos que dizem porquê).

## 6. Limites conhecidos e o que vem a seguir

- Desfazer uma eliminação repõe a máscara no fim da lista, por isso os índices de <code>terrain_mask_at</code> podem mudar.
- Ainda não há um flow headless da UI para o card: os fixtures headless não têm uma entidade terreno, por isso o comportamento é coberto pelos testes da app e pelas ações de agente.
- A seguir na Fase 5: estradas e rios por spline, pressão de tablet e presets, pincéis em GPU, GI regional pré-compilado.
