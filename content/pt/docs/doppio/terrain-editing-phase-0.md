# Edição de terreno: relatório da Fase 0

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Feito</span>
  <span class="doc-badge">Doppio</span>
  <span>Última atualização: <time datetime="2026-11-23">2026-11-23</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/pt/docs/doppio/terrain-editing-phase-0.md"><code>terrain-editing-phase-0.md</code></a></span>
</div>

<p class="doc-lede">O que é a base do editor de terreno, como foi construída: o modelo de tiles, o motor de traço, o contêiner nativo <code>.terrain</code>, o GI regional e o cursor do pincel, com a C ABI que os leva, como cada peça é verificada, as decisões por trás e o que falta. O plano em si está em <a href="terrain-editing-roadmap.md"><code>terrain-editing-roadmap.md</code></a>.</p>

## 1. O que a Fase 0 entregou

<table>
  <thead><tr><th>Peça</th><th>Onde</th><th>O que faz</th></tr></thead>
  <tbody>
    <tr><td>Modelo de tiles</td><td><code>src/caffeine/terrain/edit/TerrainTiles.*</code></td><td>Tiles de 64 células que possuem vértices disjuntos; tiles sujos e a região alterada; coordenadas em centímetros inteiros; tiles de altura de 16 bits em centímetros com um recurso exato em float</td></tr>
    <tr><td>Motor de traço</td><td><code>terrain/edit/TerrainStroke.*</code></td><td>Stamps espaçados em metros ao longo de um caminho; cinco modos; imagens de stamp, curvas de falloff, rotação, um gancho de pressão; registros de undo tile a tile</td></tr>
    <tr><td>Contêiner nativo</td><td><code>terrain/TerrainContainer.*</code></td><td>Um asset <code>caf</code> do tipo Terrain: um diretório de tiles e um registro por tile com CRC; carga parcial; conversão sem perdas de um <code>.cterrain</code> legado</td></tr>
    <tr><td>Conversor</td><td><code>caf-pack --convert-terrain</code>, <code>convertLegacyTerrain</code></td><td>Lê um <code>.cterrain</code>, escreve o <code>.terrain</code>, relê e compara bit a bit antes de reportar sucesso</td></tr>
    <tr><td>Cache</td><td><code>terrain/TerrainCache.*</code></td><td><code>commitHeightEdit</code> (rebuild local da malha), revisões por tile, <code>giTilesFor</code>, <code>dataFileIsLegacy</code>, <code>convertToNative</code>, <code>saveNativeTerrainFile</code></td></tr>
    <tr><td>GI regional</td><td><code>render/GpuSceneRenderer.cpp</code></td><td>Um terreno é um objeto do Photon por tile, cada um com a sua revisão, então um traço revoxeliza só os tiles que tocou</td></tr>
    <tr><td>C ABI</td><td><code>capi/EngineAPI.*</code></td><td>Versões 25 (traços), 26 (formato dos dados, conversão) e 27 (raycast no terreno, contorno do pincel)</td></tr>
    <tr><td>Editor</td><td><code>doppio/crates/ui</code>, <code>doppio/crates/engine</code></td><td>Wrappers Rust; o overlay do cursor do pincel; <em>Scene &gt; Convert terrains to .terrain</em>; as ações de agente <code>convert_terrains</code> e <code>terrain_brush_cursor</code></td></tr>
  </tbody>
</table>

## 2. O modelo de tiles

- Um terreno de <code>N</code> vértices tem <code>ceil((N-1)/64)</code> tiles por lado (257 dá 4, 4097 dá 64). Um tile <em>possui</em> os seus vértices (o último tile de uma linha possui também o final), então tiles nunca se sobrepõem; a sua <em>região de malha</em> são os vértices possuídos mais um de cada lado.
- Um ponto também é nomeado em <strong>centímetros inteiros desde o canto</strong> (<code>vertexXCm</code>), a forma de que um id estável é calculado: reamostrar o heightmap não o altera, e um terreno de quilómetros é endereçado primeiro pelo tile e depois por um pequeno deslocamento.
- <code>DirtyTiles</code> guarda os tiles que uma edição tocou e o retângulo justo dos vértices que realmente mudaram; a malha e o GI expandem esse retângulo por um vértice.
- <code>quantizeHeights</code> guarda um tile como deslocamentos de 16 bits de 1 cm a partir de uma base (655 m de alcance); um tile que não cabe mantém os floats.

## 3. O motor de traço

- Um traço é um caminho de pontos. O pincel é aplicado nele como stamps <strong>espaçados um número fixo de metros</strong>, nunca um por frame: o mesmo caminho dá o mesmo terreno com 2 ou 240 amostras. Raio, espaçamento e alturas são metros; as posições são metros desde o centro do terreno.
- Raise, lower e noise mudam a altura em <em>metros por stamp</em>; smooth e flatten movem uma fração de 0 a 1 para a média ou para o alvo. O smooth lê uma cópia da região, então o resultado não depende da ordem dos vértices. O noise é determinístico para uma seed.
- O primeiro toque num tile copia as suas alturas; <code>finish</code> devolve um <code>StrokeRecord</code> com o antes e o depois dos tiles que realmente mudaram. Undo e redo são exatos bit a bit, e o registro são poucos tiles mesmo num terreno de 8 km.

## 4. O contêiner nativo .terrain

<table>
  <thead><tr><th>Parte</th><th>Conteúdo</th></tr></thead>
  <tbody>
    <tr><td>Cabeçalho (32 B)</td><td>magic caf <code>0xCAFECAFE</code>, tipo Terrain, CRC32 do payload</td></tr>
    <tr><td>Metadados</td><td><code>TerrainFileMeta</code> (versão de formato 1, resolução, extensão em metros, altura máxima), o diretório de máscaras e o diretório de tiles (offset, tamanho e CRC32 de cada tile)</td></tr>
    <tr><td>Payload</td><td>Um registro por tile, linhas e depois colunas, cada um alinhado a 16 bytes: as alturas, os pesos de splat dos texels de splat que o tile possui e o mesmo sub-retângulo de cada máscara guardada</td></tr>
    <tr><td>Rodapé</td><td>CRC32 do ficheiro inteiro</td></tr>
    <tr><td>Regra sem perdas</td><td>Um tile de altura só é de 16 bits quando decodificar devolve cada bit do float (então NaN, infinitos, -0 e relevo acima de 655 m ficam como floats); os pesos de splat só são bytes quando cada peso é exatamente byte/255, senão quatro floats; as máscaras já são de 8 bits</td></tr>
    <tr><td>Leitor</td><td><code>open</code> lê o cabeçalho e os diretórios; <code>loadTile</code> e <code>loadTilesInto</code> leem só os tiles pedidos e conferem cada CRC; <code>verifyWholeFile</code> confere o rodapé; um load que falha deixa os mapas do chamador intactos</td></tr>
    <tr><td>Abrir projetos antigos</td><td><code>loadTerrainAny</code> detecta o formato pela assinatura (<code>CTRN</code> é o legado); um terreno legado abre como está e é sinalizado, e <code>nativeTerrainPath</code> dá o caminho <code>.terrain</code> a oferecer</td></tr>
  </tbody>
</table>

## 5. C ABI

<table>
  <thead><tr><th>Versão</th><th>Funções</th><th>Propósito</th></tr></thead>
  <tbody>
    <tr><td>25</td><td><code>caffeine_session_terrain_stroke_begin / _point / _end / _revert / _reapply</code></td><td>Um traço numa entidade de terreno: pontos no espaço do mundo, um rebuild local da malha por ponto, uma atualização da malha de colisão por traço, registros de undo num orçamento de 512 MB</td></tr>
    <tr><td>26</td><td><code>caffeine_session_terrain_data_legacy</code>, <code>caffeine_session_terrain_convert_native</code></td><td>Se um terreno ainda está no formato antigo; salvá-lo como <code>.terrain</code>, verificado bit a bit, e apontar a cena para ele (o ficheiro antigo fica)</td></tr>
    <tr><td>27</td><td><code>caffeine_session_terrain_raycast</code>, <code>caffeine_session_terrain_brush_outline</code></td><td>Onde um raio encontra um terreno, e o anel que um pincel faz no relevo</td></tr>
  </tbody>
</table>

## 6. GI regional

- O Photon construía um objeto para um terreno, então qualquer edição revoxelizava tudo, e um terreno feito de chunks (o padrão) nem era voxelizado, porque não tem uma malha única. Agora o terreno é cortado em tiles; cada tile tem uma malha grossa e uma revisão que só muda quando uma edição o tocou.
- O passo da malha mantém o terreno inteiro dentro de 400 000 triângulos e células de pelo menos cerca de um metro (o volume de voxels não resolve mais que isso). As caixas de tiles de terreno vizinhos são juntadas, porque o voxelizador reconstrói um nível inteiro quando recebe mais de oito caixas; as caixas de objetos comuns não são juntadas, então uma cena que mudou por inteiro continua a reconstruir inteira e a luz volta a assentar.
- Ainda não feito: GI pré-compilado por região guardado no contêiner. Fase 5.

## 7. Verificação

- C++: <code>tests/test_terrain_edit.cpp</code> (tiles, traços, impressões digitais golden dos cinco modos, um orçamento por stamp de cerca de 0,03 a 0,05 ms que não cresce com o terreno, tiles de GI, abrir e converter um terreno legado), <code>tests/test_terrain_container.cpp</code> (10 casos) e os casos da C ABI em <code>tests/test_capi.cpp</code>. A suíte inteira: 1099 casos.
- Rust: o teste da crate do motor de um traço e do seu undo; <code>photon_gi::a_terrain_stroke_revoxelises_only_the_tiles_it_touched</code> (16 objetos, nenhuma reconstrução total, no máximo 8 caixas); <code>terrain_format</code> (um projeto antigo é reportado, convertido e reaberto bit a bit); <code>terrain_cursor</code> (o anel segue o mouse e acompanha o relevo). A suíte inteira: 590 testes, clippy com e sem a feature <code>agent</code>, <code>./scripts/check-rust-ui.sh</code>.

## 8. Decisões registadas

- Camadas de material: até 64 por paleta, 4 misturadas por texel, resolução por camada, um modo em camadas ou simples por terreno; só o que uma câmera pode ver fica carregado.
- Vegetação: procedural e manual são ambas <em>fontes</em> de colocação, alternáveis sem perder dados; a meta é 1M de instâncias em unidades reais (por hectare), então culling na GPU, LOD e impostores entram na Fase 3.
- Unidades métricas reais em todo o lado (cm, m, km); os ids estáveis vêm de coordenadas do mundo em centímetros inteiros; um terreno legado converte sem perder um bit; a atualização parcial do collider de física está fora de escopo; a pressão de tablet é Fase 5 (o traço já leva uma pressão e o pincel um gancho).

## 9. Limites conhecidos e o que vem a seguir

- Uma conversão é uma migração de formato de ficheiro, não uma edição desfazível; o motor marca a cena como alterada para que salvar a mantenha. <code>saveTerrainFile</code> com caminho <code>.terrain</code> devolve false de propósito (falta a extensão e a escala de altura); as cenas usam <code>saveNativeTerrainFile</code>.
- O cursor do pincel ainda não tem botão: a ação de agente e os testes ligam-no, e o Terrain Editor da Fase 1 ligará. Um ponto de traço chega ao motor no espaço do mundo por uma matriz de float, o que será revisto com a renderização relativa à câmera para terrenos longe da origem.
- Os tiles de vegetação e o GI pré-compilado no contêiner pertencem às Fases 3 e 5. A seguir: Fase 1, a biblioteca de pincéis (<code>.brush</code>, cerca de 40 pincéis procedurais, todos os modos, máscara de proteção, simetria) e a UI do Terrain Editor.

## 10. Diário de trabalho

- <strong>2026-11-22</strong>: o plano e as suas decisões foram escritos (<code>terrain-editing-roadmap.md</code>); o modelo de tiles, o motor de traço, a C ABI 25 e o wrapper Rust foram construídos. A sessão <em>Contêiner .terrain e conversor</em> construiu em paralelo o contêiner e o conversor do <code>caf-pack</code>, em ficheiros em que esta sessão não tocou.
- <strong>2026-11-23</strong>: os testes golden e de orçamento, o GI regional, o aviso e a conversão de terrenos legados (C ABI 26) e o cursor do pincel (C ABI 27) fecharam a fase. Incidentes: um <code>git stash</code> no submódulo do site foi desfeito de imediato, sem conflitos; o <code>/tmp</code> encheu duas vezes e só se removeram artefatos antigos de testes; juntar todas as caixas sujas do Photon quebrou o teste de GI da parede fina, e por isso só os tiles de terreno são juntados.
