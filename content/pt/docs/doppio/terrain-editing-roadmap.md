# Edição de terreno: pincéis, paleta de materiais e vegetação

<div class="doc-meta">
  <span class="doc-badge doc-badge--plan">Plano</span>
  <span class="doc-badge">Doppio</span>
  <span>Última atualização: <time datetime="2026-11-24">2026-11-24</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/pt/docs/doppio/terrain-editing-roadmap.md"><code>terrain-editing-roadmap.md</code></a></span>
</div>

<p class="doc-lede">Um editor de terreno completo, não um pincel que sobe e desce: uma biblioteca de pincéis customizados, uma paleta de materiais para pintar e uma paleta de vegetação (árvores, plantas, pedras, prontas ou receitas <code>.generator.nature</code>) colocada de forma adaptativa e sem sobreposição, onde a edição de uma espécie chega a todas as instâncias que já estão no mapa.</p>

## 1. Ponto de partida

O que existe e é reaproveitado, e o que falta.

<table>
  <thead><tr><th>Peça</th><th>Estado</th></tr></thead>
  <tbody>
    <tr><td><code>TerrainSculptor</code></td><td>5 modos (Raise, Lower, Smooth, Flatten, Noise), um pincel redondo; sem C ABI e sem UI interativa</td></tr>
    <tr><td><code>TerrainSplatPainter</code></td><td>Pinta <strong>4 camadas fixas</strong> (um mapa RGBA): o teto de uma paleta de materiais hoje</td></tr>
    <tr><td><code>TerrainMasks</code> e <code>BiomeTable</code></td><td>Altura, declive, curvatura e até 16 máscaras guardadas; regras como "pinheiros onde é suave e seco"</td></tr>
    <tr><td>Scatter (<code>scatterTerrain</code>)</td><td>Determinístico por seed, prioridade e raio de exclusão; cria <strong>uma entidade por instância</strong> (limite 5000) e não se edita depois</td></tr>
    <tr><td>Receitas (<code>.generator.nature</code>, <code>recipe_ref.rs</code>)</td><td>"Carvalho, variante 17" é o mesmo modelo em qualquer máquina; as variantes assadas ficam em cache por hash de conteúdo</td></tr>
    <tr><td>Asset manager, instanciamento, collider do terreno</td><td>Referências dentro do projeto; draws instanciados; um collider heightfield reconstruído por inteiro</td></tr>
    <tr><td><strong>Falta</strong></td><td>Pincéis customizados, muitas camadas, vegetação como dado do terreno (não entidades), editar uma vez e aplicar a todas, undo por tiles, atualizações incrementais, preview do pincel</td></tr>
  </tbody>
</table>

## 2. Decisões

- <strong>Formato nativo.</strong> Um contêiner <code>.terrain</code> no formato <code>caf</code> guarda o terreno em tiles regionais. O <code>caf-pack</code> descompila o <code>.cterrain</code> legado para ele, sem perdas, e o motor abre projetos antigos convertendo.
- <strong>Resolução por camada.</strong> Cada camada da paleta tem a sua resolução, e um terreno pode alternar entre o modo de material em camadas e o simples.
- <strong>Residência por câmera.</strong> Só o que uma câmera pode ver fica carregado (tiles, camadas, texturas, instâncias); o resto é descarregado e volta a carregar com orçamentos de RAM e CPU.
- <strong>Procedural e manual são ambos fontes.</strong> O editor de terreno e os geradores procedurais são ferramentas de um mesmo framework, e cada fonte de colocação pode ser ligada ou desligada sem perder os seus dados.
- <strong>GI regional.</strong> Uma edição invalida só a região que toca, de forma dinâmica ou a partir de dados pré-compilados.
- <strong>1M de instâncias</strong> é meta da Fase 3, então culling na GPU, LOD e impostores entram nela. A meta é dita em unidades reais (instâncias por hectare em quilómetros de terreno), não como uma contagem solta.
- <strong>Unidades métricas reais em todo o lado:</strong> centímetros, metros e quilómetros. O raio e o espaçamento do pincel são em metros, as alturas guardam-se ao centímetro, as densidades são por metro quadrado ou hectare, e os terrenos chegam a quilómetros.
- <strong>Ids estáveis ao reamostrar</strong> são uma migração explícita: os overrides são remapeados.
- <strong>Fora de escopo aqui:</strong> a atualização parcial do collider de física. O pipeline de traço emite regiões sujas, então ele pode assinar depois. A pressão de tablet é Fase 5; os parâmetros do pincel já trazem um gancho de pressão (padrão 1).

## 3. Arquitetura

### 3.1 Núcleo de pincéis (C++, <code>terrain/edit/</code>)

- <strong>Stamp:</strong> uma imagem em tons de cinza (64 a 256 px) com raio, rotação, falloff, espaçamento, intensidade e jitter (posição, rotação, tamanho, opacidade).
- <strong>Traço:</strong> os stamps são distribuídos ao longo do caminho por espaçamento em metros, nunca por frame, então o resultado não depende do frame rate.
- <strong>Biblioteca:</strong> cerca de 40 pincéis procedurais (redondo macio e duro, quadrado, ruídos Perlin, Worley e ridged, rachaduras, estratos, dunas, crateras, terraços, penhascos), imagens em tons de cinza importadas pelo asset manager, ficheiros <code>Nome.brush</code> (texto puro: stamp, parâmetros, modo) e presets do usuário.
- <strong>Operações:</strong> Raise e Lower, Smooth, Flatten (altura, plano, sob o cursor), Ramp, Terrace, Noise, Pinch e Bulge, Stamp (soma, absoluto, max, min), Clone, Smudge, erosão térmica e hidráulica como pincel.
- <strong>Máscara de proteção</strong> (editar só onde declive, altura ou uma máscara permite) e <strong>simetria</strong> (espelho em X e Z, radial).
- <strong>Pipeline:</strong> um traço acumula em tiles sujos; cada tile sujo reconstrói só a sua região de malha, recalcula as suas máscaras e avisa o GI e o collider. O <strong>undo</strong> guarda os tiles de antes e depois, um passo por traço.

### 3.2 Paleta de materiais

- Uma paleta tem até <strong>64 camadas</strong>; cada tile lista só as camadas que usa (no máximo 4 misturadas por texel), então só as camadas dos tiles visíveis ficam residentes, o que torna 64 viável. Cada uma referencia um <code>.mat</code> PBR (albedo, normal, ORM, tiling) pelo asset manager. Guardada como asset <code>.terrainpalette</code>.
- <strong>Renderização:</strong> um mapa de índices e um de pesos (4 camadas misturadas por texel) sobre texture arrays agrupados por faixa de tamanho; blend por altura, triplanar em declives fortes, anti-tiling, tint e rotação de UV por camada.
- <strong>Resolução por camada</strong> de 256 a 4096, comprimida offline (BC7 e BC5) pelo <code>caf-pack</code>. O <strong>modo simples</strong> (uma textura ou cor, ou as 4 camadas legadas) é selecionável por terreno e por nível de qualidade.
- <strong>A pintura</strong> usa o núcleo de pincéis nos modos Paint, Erase, Replace, Smooth e Lock; o <strong>auto-layering</strong> preenche por regras de declive, altura e máscaras, na sintaxe da tabela de bioma.

### 3.3 Fontes de colocação e vegetação

- Uma <strong>fonte</strong> produz densidade ou instâncias: pintada (manual), procedural (regras e seed), um plano de scatter importado, ou um grafo ou script. As fontes empilham, e cada uma pode ser ligada, desligada ou misturada.
- <strong>Ids estáveis:</strong> o id de uma instância é um hash de fonte, célula (ou traço) e índice. Os overrides (movida, removida, escalada) ficam presos a ele e sobrevivem a regerar. Operações: <em>assar procedural em manual</em> e <em>rederivar</em>.
- <strong>Sem sobreposição:</strong> uma grade espacial global com footprint por espécie, prioridade e distância mínima entre espécies, aplicada na pintura (rejeita) e num passe de resolução determinístico; respeita também os objetos da cena.
- <strong>Espécie</strong> (a entrada da paleta): um prefab, um mesh ou uma receita <code>.generator.nature</code> com N variantes assadas, densidade, raio de exclusão, faixa de escala, regras de declive, altura e máscara, alinhamento à normal, afundamento, tint, prioridade, vento e LOD.
- <strong>Ferramentas:</strong> Paint, Erase, Scale, Rotate, Tint, Replace species, Select e Move, Thin out, Reseed.

### 3.4 Uma edição chega a todas as instâncias, e o terreno adapta

- Uma instância guarda só <code>espécie, variante, seed, escala, yaw, tint</code> e referencia a espécie; nunca copia um mesh.
- Editar uma espécie abre a sua receita no Nature Generator; ao salvar, as variantes são re-assadas (cache por hash de conteúdo) e todas as instâncias atualizam. O mesmo vale para um prefab, mesh ou material alterado. O override por instância fica mínimo, e <em>destacar para entidade</em> é opcional.
- <strong>Adaptativo:</strong> curvas sobre máscaras modulam tamanho, cor e variante (úmido é mais verde e maior, declive é menor, altitude escala). Esculpir re-projeta as instâncias; as que ficam inválidas (declive, água, altura) ficam ocultas, e as manuais não são apagadas.

### 3.5 Formato nativo do terreno

- <code>.terrain</code> (um tipo de asset <code>caf</code>): tiles regionais de alturas (16 ou 32 bit), pesos por camada, máscaras e tiles de vegetação, com versão e CRC por tile; carrega só as regiões pedidas.
- O <code>caf-pack</code> lê um <code>.cterrain</code> (alturas, splat de 4 camadas, máscaras) e escreve o contêiner. Sem perdas verifica-se por uma ida e volta que compara alturas, pesos de 8 bits e máscaras bit a bit. O leitor legado fica só leitura.
- <strong>Unidades reais e mundos grandes:</strong> as alturas são de 16 bits quantizadas a 1 cm com um desvio base por tile (655 m de alcance; tiles mais altos usam 32 bit), as posições são locais ao tile com coordenadas inteiras de tile, a renderização é relativa à câmera, e um id estável é um hash de <em>coordenadas do mundo em centímetros inteiros</em>, não de índices de texel, então reamostrar o heightmap não o altera.
- A mesma grade de tiles serve ao undo, à malha, ao GI e à vegetação.

### 3.6 GI por região

- Toda edição emite regiões sujas na grade de tiles, que alimentam o Photon (que já tem cache por vista).
- <strong>Dinâmico:</strong> recalcula só a região suja. <strong>Pré-compilado:</strong> guarda a iluminação por região nos tiles do <code>.terrain</code>, marca como desatualizada quando a região é editada e re-assa em segundo plano. O modo é escolhido por região ou terreno.

### 3.7 Residência, orçamentos e 1M de instâncias

- <strong>Residência por câmera:</strong> tiles, camadas, texturas e buffers de instância ficam residentes só para o que qualquer câmera ativa (viewport do editor, câmera do jogo, preview) pode ver, com histerese. Carregar e descarregar é assíncrono, faz prefetch ao longo do caminho da câmera e tem orçamentos por frame de RAM, CPU e uploads. Segue as opções de otimização que o motor já tem e aparece na aba Performance e no profiler.
- <strong>1M de instâncias:</strong> buffers de instância por chunk (cerca de 32 bytes cada, uns 32 MB na GPU), culling em compute (frustum e oclusão), draws indiretos, LOD mais um impostor octaédrico assado por espécie e variante pelo <code>caf-pack</code>, sombras só para LODs próximos, vento no vertex shader.
- <strong>Edição:</strong> durante um traço desenha-se um proxy de menor densidade, com um teto de custo por traço que precisa ser medido.

### 3.8 UI do editor (Doppio)

- Um modo <strong>Terrain Editor</strong> no viewport com as abas Sculpt, Paint, Foliage e Masks.
- Um painel de pincel (grade de pincéis com preview, sliders, curva de falloff, espaçamento, jitter, simetria), painéis de paleta para materiais e espécies (cartões, busca, favoritos) e um decal do pincel projetado no terreno com um HUD de latência.
- Atalhos: <kbd>[</kbd> e <kbd>]</kbd> para o raio, <kbd>Ctrl</kbd> para inverter, <kbd>Shift</kbd> para suavizar.
- Regras do projeto: painéis compõem componentes, cada widget tem um <code>UiId</code> e uma entrada no catálogo, agentes usam ações <code>Message</code> em <code>main/agent.rs</code>, fluxos headless cobrem cada ferramenta.

## 4. Fases

<table>
  <thead><tr><th>Fase</th><th>Entrega</th><th>Depende de</th><th>Verificação</th></tr></thead>
  <tbody>
    <tr><td><strong>0. Base</strong></td><td>ABI de traço, modelo de tiles em unidades reais (cm, m, km), tiles e regiões sujas, rebuild incremental de malha, undo por tiles, decal do pincel, o contêiner <code>.terrain</code> e o conversor do <code>caf-pack</code></td><td>nada</td><td>Teste golden por traço; ida e volta bit a bit de um terreno legado</td></tr>
    <tr><td><strong>1. Escultura</strong></td><td>Stamp, <code>.brush</code>, cerca de 40 pincéis, todos os modos, máscara de proteção, simetria, UI</td><td>0</td><td>O mesmo traço a 30, 60 e 144 fps; fluxos headless</td></tr>
    <tr><td><strong>2. Materiais</strong></td><td>Paleta com resolução por camada, modo em camadas ou simples, mapas de índices e pesos, pintura, auto-layering, orçamento de VRAM, residência</td><td>0</td><td>Render de referência; um projeto antigo abre idêntico</td></tr>
    <tr><td><strong>3. Vegetação</strong></td><td>Fontes de colocação (pintada e procedural, alternáveis), ids estáveis, sem sobreposição, pipeline GPU para 1M com LOD e impostores</td><td>0</td><td>Determinismo por seed; 1M de instâncias dentro do orçamento do frame</td></tr>
    <tr><td><strong>4. Receitas e adaptação</strong></td><td>Espécie a partir de <code>.generator.nature</code>, edição que propaga, overrides, re-projeção, variação por máscara</td><td>3</td><td>Editar uma receita muda todas as instâncias; esculpir readapta</td></tr>
    <tr><td><strong>5. Acabamento</strong></td><td>Máscaras pintadas, estradas e rios por spline, GI regional pré-compilado, pincéis em GPU, pressão de tablet, presets compartilháveis, docs</td><td>1 a 4</td><td>Docs EN e PT, capturas headless</td></tr>
  </tbody>
</table>

As Fases 1, 2 e 3 podem andar em paralelo depois da Fase 0, porque tocam arquivos diferentes. O GI regional começa na Fase 0 (regiões sujas) e se completa na Fase 5.

<p><strong>Estado da Fase 0 (2026-11-22).</strong> Feito: o modelo de tiles em unidades reais (<code>terrain/edit/TerrainTiles</code>: tiles de 64 células que possuem vértices disjuntos, tiles e regiões sujas, coordenadas em centímetros inteiros, tiles de altura de 16 bits em centímetros com um recurso exato); o motor de traço (<code>TerrainStroke</code>: stamps espaçados em metros ao longo do caminho, cinco modos, imagens de stamp, curvas de falloff, rotação, um gancho de pressão, registros de undo tile a tile); a C ABI 25 (<code>caffeine_session_terrain_stroke_*</code>: begin, point, end, revert, reapply, com um rebuild local da malha por ponto do traço e uma atualização da malha de colisão por traço) e o seu wrapper Rust. Verificado por <code>tests/test_terrain_edit.cpp</code>, pelos testes da C ABI e por um teste da crate do motor: o mesmo caminho dá o mesmo terreno a qualquer taxa de amostragem, um undo é exato bit a bit, e um traço num terreno de 8 km toca só alguns tiles. Também feito: o contêiner nativo <code>.terrain</code> (<code>terrain/TerrainContainer</code>, um asset <code>caf</code> do tipo Terrain: um cabeçalho, um diretório de tiles e um registro com CRC por tile com as suas alturas, retângulos de splat e de máscaras; um leitor que carrega só os tiles pedidos) e o conversor legado (<code>caf-pack --convert-terrain</code> e <code>convertLegacyTerrain</code>, relido bit a bit antes de reportar sucesso; o <code>TerrainCache</code> abre os dois formatos). Nada se perde: um tile de altura só é de 16 bits quando decodificar devolve cada bit do float, senão guarda os floats; os pesos de splat só são bytes quando exatos, senão floats. Verificado por <code>tests/test_terrain_container.cpp</code> (ida e volta do legado, carga de um tile, CRC de tile corrompido, tiles largos, 257 e 4097 vértices). Também feito: o editor diz quais terrenos de um projeto ainda são <code>.cterrain</code> e <em>Scene &gt; Convert terrains to .terrain</em> (a ação de agente <code>convert_terrains</code>, C ABI 26) salva-os no formato nativo, verificados bit a bit, mantendo os ficheiros antigos; terrenos novos salvam como <code>.terrain</code>. GI regional: o Photon vê um terreno como um objeto por tile, cada um com a sua revisão, então um traço revoxeliza só os tiles que tocou (a região alterada é um retângulo justo, e o Photon junta as caixas de tiles de terreno vizinhos). O cursor do pincel (C ABI 27, <code>terrain_raycast</code> e <code>terrain_brush_outline</code>, a ação de agente <code>terrain_brush_cursor</code>): o anel que um pincel faz no relevo, desenhado como overlay sob o mouse. Um teste golden fixa um terreno por modo, e um stamp custa cerca de 0,05 ms seja qual for o tamanho do terreno. <strong>A Fase 0 está completa</strong> (relatório completo: <a href="terrain-editing-phase-0.md"><code>terrain-editing-phase-0.md</code></a>). Os tiles de vegetação no contêiner pertencem à Fase 3; a atualização parcial do collider de física continua fora de escopo.</p>

<p><strong>Estado da Fase 1 (2026-11-24).</strong> Feito: 16 modos de pincel (os cinco da Fase 0 mais Ramp, Terrace, Pinch, Bulge, Stamp absolute, keep higher e keep lower, Clone, Smudge, e erosão térmica e hidráulica como pincéis), variação por stamp, simetria (espelho X, Z, ambos, radial) e máscaras de proteção (inclinação, altura, curvatura ou uma máscara guardada); 42 stamps procedurais e uma biblioteca de 58 pincéis; o formato <code>.brush</code> (texto puro, não JSON: o núcleo não tem leitor de JSON); a C ABI 28 e seus wrappers Rust; passos de traço no histórico de desfazer do editor; e a aba <strong>Terrain Brush</strong> com a ferramenta do mouse, os atalhos <kbd>[</kbd> <kbd>]</kbd>, <kbd>Ctrl</kbd> e <kbd>Shift</kbd>, ações de agente e um fluxo headless. Todo modo desfaz bit a bit e o mesmo caminho dá o mesmo terreno em qualquer taxa de amostragem. <strong>A Fase 1 está completa</strong> (relatório completo: <a href="terrain-editing-phase-1.md"><code>terrain-editing-phase-1.md</code></a>). Próximo: as Fases 2 e 3 podem começar em paralelo.</p>

<p><strong>Estado da Fase 2 (2026-11-24).</strong> Feito: uma paleta de materiais de até 64 camadas (<code>.terrainpalette</code>), um mapa de camadas que nomeia quatro camadas e os seus pesos em cada texel (<code>.terrainlayers</code>), traços de pintar, apagar, substituir e suavizar sobre a forma do pincel da escultura com desfazer exato, camadas travadas, auto-camadas por inclinação, altura, curvatura e máscaras, um renderizador que desenha tudo a partir de uma textura array (só as camadas em uso ganham uma fatia, repetição e rotação por camada, um orçamento de VRAM, envio de retângulos), o formato de cena 12, a C ABI 29 e a aba <strong>Terrain Paint</strong> com a ferramenta do mouse, ações de agente e um fluxo headless. Conferido pintando um terreno de vermelho e azul e contando os pixels. <strong>A Fase 2 está completa</strong> exceto três itens do roadmap registrados como limites: compressão offline BC7 e BC5, residência por câmera e o modo simples por nível de qualidade (relatório completo: <a href="terrain-editing-phase-2.md"><code>terrain-editing-phase-2.md</code></a>). Próximo: a Fase 3 (vegetação).</p>

<p><strong>Estado da Fase 3 (2026-11-24).</strong> Feito: a vegetação como dado do terreno (uma paleta de até 256 espécies, uma fonte procedural que nasce sozinha por regras e uma semente e uma fonte manual, as duas se empilhando), ids estáveis com overrides que sobrevivem à regeneração, nada se sobrepondo (prioridade e espaço), plantas reprojetadas de graça quando o terreno é esculpido e escondidas, não apagadas, quando as suas regras falham, sete ferramentas de pincel (Paint, Erase, Scale, Rotate, Tint, Replace, Thin out), bake, re-derive e reseed, o arquivo <code>.terrainveg</code>, o formato de cena 13, um renderizador que desenha uma chamada instanciada por chunk e variante de espécie com descarte por frustum e distância e um orçamento de construção, a C ABI 30 e a aba <strong>Terrain Vegetation</strong> com a ferramenta do mouse, ações de agente e um fluxo headless. Conferido renderizando plantas e contando os seus pixels. <strong>A Fase 3 está completa</strong> exceto o descarte por compute na GPU e os desenhos indiretos, as malhas de LOD e os impostores, as sombras da vegetação e a ferramenta Select and Move do roadmap, registrados como limites (relatório completo: <a href="terrain-editing-phase-3.md"><code>terrain-editing-phase-3.md</code></a>). Próximo: a Fase 4 (espécies a partir de receitas).</p>

<p><strong>Estado da Fase 4 (2026-11-25).</strong> Feito: uma espécie que vem de uma receita <code>.generator.nature</code> (gerada em 1 a 8 variantes, um OBJ cada com as partes como sub-malhas e um material por parte), o hash do conteúdo da receita guardado na espécie para que o editor gere de novo sozinho quando o arquivo muda (um passo de desfazer, as mesmas plantas), um renderizador que desenha cada sub-malha com o seu material, adaptações por máscara (tamanho e cor entre o 0 e o 1 de uma máscara, aplicadas quando as plantas são resolvidas, de modo que esculpir e pintar máscaras as readapta), a C ABI 31 e os cartões Recipe e do terreno da aba <strong>Terrain Vegetation</strong> com ações de agente. <strong>A Fase 4 está completa</strong> exceto a variação da variante escolhida por uma máscara, registrada como limite (relatório completo: <a href="terrain-editing-phase-4.md"><code>terrain-editing-phase-4.md</code></a>). Próximo: a Fase 5 (máscaras pintadas, estradas e rios, pressão de mesa digitalizadora, GI pré-compilado).</p>

## 5. Riscos e medições

- <strong>VRAM e compatibilidade:</strong> limites de texture array em placas mais fracas. As camadas são descarregadas e carregadas pela residência por câmera, com orçamentos de RAM e CPU, e o modo simples é a rede de segurança.
- <strong>Precisão em terrenos de quilómetros:</strong> posições locais ao tile e renderização relativa à câmera são necessárias desde a Fase 0; acrescentá-las depois tocaria cada tile e cada instância.
- <strong>Ids estáveis ao reamostrar:</strong> os ids vêm de coordenadas do mundo em centímetros inteiros, então reamostrar os mantém; redimensionar a origem do terreno é uma migração explícita que remapeia os overrides.
- <strong>1M de instâncias no editor:</strong> pintar em tempo real precisa de um teto de custo por traço. O proxy de baixa densidade é a resposta, mas é preciso medir.
- <strong>Migração:</strong> os <code>.cterrain</code> legados têm de continuar a abrir; o conversor e o seu teste bit a bit fazem parte da Fase 0.
