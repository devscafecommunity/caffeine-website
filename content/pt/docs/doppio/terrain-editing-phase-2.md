# Edição de terreno: relatório da Fase 2 (paleta de materiais e pintura)

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Feito</span>
  <span class="doc-badge">Doppio</span>
  <span>Última atualização: <time datetime="2026-11-24">2026-11-24</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/pt/docs/doppio/terrain-editing-phase-2.md"><code>terrain-editing-phase-2.md</code></a></span>
</div>

<p class="doc-lede">Pintar um terreno com até 64 camadas de material como foi construído: uma paleta, um mapa de camadas que nomeia quatro camadas em cada texel, traços de pintar, apagar, substituir e suavizar que compartilham o pincel da escultura, auto-camadas por inclinação, altura e máscaras, um renderizador que desenha tudo a partir de uma textura array e a aba Terrain Paint, com a C ABI 29 que a leva. Ela se apoia na <a href="terrain-editing-phase-1.md">Fase 1</a>; o plano está em <a href="terrain-editing-roadmap.md"><code>terrain-editing-roadmap.md</code></a>.</p>

## 1. O que a Fase 2 entregou

<table>
  <thead><tr><th>Peça</th><th>Onde</th><th>O que faz</th></tr></thead>
  <tbody>
    <tr><td>Paleta</td><td><code>src/caffeine/terrain/paint/TerrainPalette.*</code></td><td>Até 64 camadas: nome, imagem, caminho do normal (guardado, ainda não desenhado), metros por repetição, rotação, tinta, classe de nitidez (256 a 4096), trava. O arquivo de texto <code>.terrainpalette</code></td></tr>
    <tr><td>Mapa de camadas</td><td><code>terrain/paint/TerrainLayerMap.*</code></td><td>Quatro camadas e seus pesos em cada texel do splat (8 bytes por texel), edições por frações com arredondamento determinístico, travas, renumeração, a conversão do splat de quatro camadas, o arquivo <code>.terrainlayers</code> com um CRC-32</td></tr>
    <tr><td>Traço de pintura</td><td><code>terrain/paint/TerrainPaintStroke.*</code></td><td>Paint, Erase, Replace e Smooth sobre a forma do pincel da escultura (falloff, stamp, rotação, variação, simetria, máscaras de proteção); registros de desfazer por bloco</td></tr>
    <tr><td>Auto-camadas</td><td><code>terrain/paint/TerrainAutoLayer.*</code></td><td>Pinta as camadas por regras de inclinação, altura, curvatura e máscaras guardadas, na sintaxe da tabela de biomas</td></tr>
    <tr><td>Núcleo de traço compartilhado</td><td><code>terrain/edit/TerrainStroke.*</code></td><td><code>placeStamp</code>, <code>shapeWeight</code> e <code>protectionWeight</code> agora são compartilhados pela escultura e pela pintura (os resultados das Fases 0 e 1 não mudam: os testes dourados passam)</td></tr>
    <tr><td>Cache e cena</td><td><code>terrain/TerrainCache.*</code>, <code>scene/EditorSceneSerializer.cpp</code></td><td>O cache é dono da paleta e do mapa; a cena (blob versão 12) registra se as camadas estão ligadas e onde estão os arquivos; salvar escreve os dois ao lado dos dados do terreno</td></tr>
    <tr><td>Renderizador</td><td><code>render/shaders/terrain_lit.frag</code>, <code>terrain/TerrainGpuTextures.*</code>, <code>render/GpuTextureCache.*</code></td><td>Um mapa de índices e um mapa de pesos (RGBA8) sobre uma textura 2D array com uma fatia por camada em uso; repetição e rotação por camada; um orçamento de VRAM</td></tr>
    <tr><td>C ABI</td><td><code>capi/EngineAPI.*</code></td><td>Versão 29: camadas ligadas e desligadas, a paleta (ler, aplicar como texto, remover, mover), traços de pintura, auto-camadas, uma sonda de camadas</td></tr>
    <tr><td>Aba Terrain Paint</td><td><code>uikit/panels/terrain_paint.rs</code>, <code>windows/main/terrainpaint.rs</code></td><td>Lista da paleta com amostras de cor e cobertura, as configurações da camada selecionada, o pincel de pintura, as regras de auto-camadas</td></tr>
  </tbody>
</table>

## 2. O modelo

- Um terreno é pintado com as suas <strong>quatro camadas antigas</strong> até a pintura em camadas ser ligada. Ligá-la faz a paleta com essas quatro camadas e o mapa de camadas com o mapa de splat, então nada visível muda; um projeto antigo abre exatamente como antes.
- Cada texel do <strong>mapa de camadas</strong> nomeia até quatro camadas da paleta e quanto de cada (os pesos somam 255). Um pixel só mistura quatro camadas, e é por isso que 64 cabem.
- As edições movem <strong>frações</strong>: pintar move uma fração de tudo o que não é a camada para ela, apagar dá o peso de uma camada às outras, substituir move o peso de uma camada para outra, suavizar move um texel em direção à média dos vizinhos. Uma fração pequena na borda macia de um pincel não some num byte: o arredondamento é estocástico mas decidido por um hash do texel e do stamp, então é imparcial na média e idêntico a cada execução.
- Um texel mantém as suas quatro camadas mais pesadas; uma quinta ocupa o lugar da mais leve.
- Uma camada <strong>travada</strong> nunca muda (pintá-la não faz nada, e nada pode tirar peso dela). A trava é uma propriedade da camada, não um modo.
- O mapa tem a resolução do mapa de splat (a grade do terreno vezes a sua escala de splat) e o acompanha quando o terreno é redimensionado.

## 3. Pintura

<table>
  <thead><tr><th>Modo</th><th>O que um stamp faz</th></tr></thead>
  <tbody>
    <tr><td>Paint</td><td>Move peso para a camada selecionada; força 1 a pinta sólida</td></tr>
    <tr><td>Erase</td><td>Tira a camada selecionada e dá o seu peso às outras em proporção; um texel que é só aquela camada fica como está</td></tr>
    <tr><td>Replace</td><td>Move o peso da camada "replace" para a selecionada</td></tr>
    <tr><td>Smooth</td><td>Mistura cada texel em direção à sua vizinhança 3 x 3. Todo texel de um stamp é calculado a partir das camadas como estavam, então o resultado não depende da ordem dos texels</td></tr>
  </tbody>
</table>

O pincel é o mesmo que esculpe: o painel tem o seu próprio raio, força, espaçamento e falloff, e uma opção para tomar a <strong>forma</strong> (imagem do stamp, variação, simetria, máscaras de proteção) do pincel de trabalho da aba Terrain Brush. Os stamps são postos por espaçamento em metros, então o mesmo caminho dá as mesmas camadas em qualquer taxa de amostragem. Um traço é um passo de desfazer. <kbd>Ctrl</kbd> transforma pintar em apagar e de volta, <kbd>Shift</kbd> suaviza, <kbd>[</kbd> e <kbd>]</kbd> redimensionam o pincel ativo.

## 4. Auto-camadas

As regras são o texto da tabela de biomas, onde o número da classe é a camada da paleta:

```
class 1 base 1
  slope 0.3 0.4 1 1
class 2 base 1
  height 0.6 0.7 1 1
```

Cada texel avalia a densidade de cada camada com regra; as camadas dividem o texel em proporção à sua densidade, e um texel que nenhuma regra reivindica recebe a camada de reserva. Várias regras sobre uma camada são uma só classe cujos termos devem valer todos. As camadas travadas mantêm o seu peso e as regras dividem o que sobra. O resultado é um passo de desfazer. As máscaras são <code>slope</code>, <code>height</code>, <code>curvature</code> (todas de 0 a 1) e as máscaras guardadas do terreno.

## 5. Renderização

- O shader lê os quatro índices de camada e pesos do texel mais próximo, suavizados sobre os quatro texels em torno do ponto (para que uma borda pintada não seja uma escada de quadrados), e mistura as imagens das camadas de uma <strong>textura 2D array</strong> com a mesma projeção triplanar que o terreno usava. Cada camada tem os seus próprios metros por repetição e a sua própria rotação.
- <strong>Só as camadas em uso ganham uma fatia</strong>, então 64 camadas numa paleta custam o que o terreno realmente mostra. Toda imagem é reamostrada para a classe de tamanho do array (a maior nitidez entre as camadas em uso) com uma cadeia completa de mips; uma camada sem imagem desenha a sua tinta como cor lisa.
- <strong>Orçamento de VRAM:</strong> o orçamento do componente (256 MB por padrão) abaixa a classe de tamanho pela metade até o array caber. O painel mostra as fatias, a classe e os megabytes.
- Pintar envia <strong>só o retângulo que o traço tocou</strong> (um traço num mapa de 4k são quilobytes, não os 134 MB do mapa inteiro). Uma camada nova em uso reconstrói o array uma vez.
- Com as camadas desligadas nada disso roda: o caminho de quatro camadas é o mesmo código de antes.

## 6. Arquivos e a cena

<table>
  <thead><tr><th>Arquivo</th><th>Conteúdo</th></tr></thead>
  <tbody>
    <tr><td><code>Name.terrainpalette</code></td><td>Texto: um bloco <code>layer Name</code> por camada com <code>albedo</code>, <code>normal</code>, <code>tile</code>, <code>rotation</code>, <code>tint</code>, <code>resolution</code>, <code>locked</code>. Comentários com <code>#</code>; chaves desconhecidas são ignoradas</td></tr>
    <tr><td><code>Name.terrainlayers</code></td><td>Binário: <code>TLMP</code>, uma versão, o tamanho, a máscara de travas, 8 bytes por texel, um CRC-32 do todo. Um arquivo danificado ou truncado é recusado com um motivo</td></tr>
  </tbody>
</table>

Salvar a cena escreve os dois ao lado dos dados do terreno e registra os seus caminhos no componente do terreno (blob de cena versão 12); abrir os lê, e um mapa ausente ou danificado volta para o mapa de splat do qual o terreno foi feito em vez de perder o terreno. Os snapshots de cena em memória (desfazer de outras edições) não levam o mapa de camadas (ele pode ter 134 MB): as camadas são postas de lado e devolvidas ao seu terreno, o estado restaurado tenha camadas ligadas ou desligadas.

## 7. Desfazer

Pintar, auto-camadas e edições da paleta são registros do motor, como os traços de escultura (as mesmas chamadas de reverter e refazer). Uma edição da paleta que renumera camadas (remover, mover) guarda os blocos do mapa que ela mudou. Uma sequência de edições de um mesmo campo da paleta (arrastar um slider) se funde no registro da primeira edição: um passo, desfeito de uma vez. Ligar ou desligar as camadas é um passo de cena.

## 8. C ABI 29

<table>
  <thead><tr><th>Função</th><th>Propósito</th></tr></thead>
  <tbody>
    <tr><td><code>caffeine_session_terrain_layers_enable</code>, <code>_layers</code></td><td>Camadas ligadas e desligadas; o seu estado (tamanho da paleta, tamanho do mapa, fatias da GPU, classe e bytes)</td></tr>
    <tr><td><code>caffeine_session_terrain_palette_layer</code>, <code>_palette_text</code></td><td>Ler uma camada (com a sua contagem de texels) ou a paleta como texto</td></tr>
    <tr><td><code>caffeine_session_terrain_palette_apply</code></td><td>Substituir a paleta por texto (ao menos o mesmo número de camadas; as extras são acrescentadas), com <code>merge_into</code> para fundir uma edição no registro anterior. O erro nomeia a linha</td></tr>
    <tr><td><code>caffeine_session_terrain_palette_remove</code>, <code>_palette_move</code></td><td>Edições que renumeram, com desfazer</td></tr>
    <tr><td><code>caffeine_session_terrain_paint_begin</code></td><td>Abre um traço de pintura; pontos, fim, reverter e refazer são as chamadas de traço da versão 25</td></tr>
    <tr><td><code>caffeine_session_terrain_autolayer</code></td><td>Regras entram, um registro sai</td></tr>
    <tr><td><code>caffeine_session_terrain_layer_at</code></td><td>As camadas e os pesos sob um ponto do mundo</td></tr>
  </tbody>
</table>

## 9. Ações de agente

<code>show_terrain_paint</code>, <code>terrain_paint_active</code>, <code>terrain_paint_layers</code>, <code>terrain_paint_add_layer</code>, <code>terrain_paint_select_layer</code>, <code>terrain_paint_edit_layer</code>, <code>terrain_paint_remove_layer</code>, <code>terrain_paint_move_layer</code>, <code>terrain_paint_set</code>, <code>terrain_paint_rule</code>, <code>terrain_paint_set_rule</code>, <code>terrain_paint_autolayer</code> e <code>terrain_paint_stroke</code> (um traço por pontos do mundo, o mesmo caminho do mouse). A consulta <code>terrain_paint</code> lê o estado e a consulta <code>terrain_layer_at</code> as camadas sob um ponto. Os ids dos widgets começam com <code>terrain_paint.</code> e estão no catálogo.

## 10. Verificação

- C++: <code>tests/test_terrain_paint.cpp</code> (27 casos): a paleta (64 camadas, renumeração, a ida e volta do texto, erros com a linha, classes de nitidez, as quatro camadas antigas); o mapa de camadas (os pesos sempre somam 255, as quatro mais pesadas ficam, frações pequenas não se perdem no byte, determinístico, travas, apagar, substituir, suavizar, remover e mover camadas, a conversão do splat antigo nos dois sentidos, o arquivo e o seu dano); traços de pintura (todo modo desfaz bit a bit, as mesmas camadas em qualquer taxa de amostragem, proteção, simetria, imagens de stamp, um traço num mapa de 2049 toca poucos blocos e leva menos de 400 ms); auto-camadas (por inclinação, por densidade, travadas, por região). Um caso da C ABI cobre camadas, a paleta, pintura, auto-camadas, remoção e movimento com desfazer, a fusão de registros e salvar e carregar uma cena.
- Rust: um teste da crate do motor que <strong>renderiza</strong> um terreno com uma camada vermelha e uma azul pintadas e conta os pixels de cada cor, desfaz o traço vermelho, o refaz e desliga as camadas; testes de app <code>terrain_paint</code> (o painel, camadas ligadas como um passo, adicionar, pintar, desfazer na ordem, um arrasto do mouse, um arrasto de slider como um passo, renomear, travar, remover e mover com a tinta acompanhando, auto-camadas, exclusividade de ferramenta, substituir); testes unitários do painel e do módulo. O fluxo headless <code>terrain-paint-panel.json</code> roda pela CLI real.

## 11. Decisões registradas

- Uma camada da paleta não custa nada até ser usada: as fatias são feitas para as camadas em uso, não para as 64.
- Quatro camadas por texel é a regra do arquivo, do editor e do shader; o mapa de camadas não está no snapshot de cena por causa do tamanho, e os registros o desfazem exatamente.
- Desligar as camadas desenha o terreno com as camadas 0 a 3 (o mapa de splat é refeito a partir delas); a paleta e o mapa ficam na memória para que desfazer traga tudo de volta, e ligar as camadas de novo recomeça da visão de quatro camadas.
- A trava é uma propriedade da camada, então acompanha a camada quando as camadas são renumeradas.

## 12. Limites conhecidos e o que vem

- <strong>Não feito do roadmap:</strong> a compressão offline BC7 e BC5 pelo <code>caf-pack</code> (as imagens sobem como RGBA8), a residência por câmera (as fatias acompanham as camadas em uso em qualquer ponto do terreno, não o que uma câmera vê) e o modo simples por nível de qualidade (é por terreno: camadas desligadas).
- Os mapas normais por camada são guardados mas não desenhados; o terreno ainda tem o seu único mapa normal. A mistura por altura entre camadas não foi feita.
- O renderizador lê as quatro camadas do texel mais próximo e suaviza os seus pesos sobre quatro texels; uma camada que está nos vizinhos mas não no texel mais próximo não aparece naquele pixel.
- A paleta é do próprio terreno (dois arquivos ao lado dos seus dados); ainda não há um asset de paleta compartilhado para importar.
- Próximo: a Fase 3 (vegetação) pode começar agora; a Fase 5 acrescenta máscaras pintadas, estradas e rios por spline, pressão de mesa digitalizadora e GI pré-compilado.

## 13. Diário de trabalho

- <strong>2026-11-24</strong>: a paleta, o mapa de camadas, o traço de pintura e as auto-camadas com testes; o núcleo de traço compartilhado; o cache, o formato de cena 12 e os arquivos; o caminho da GPU (textura array, mapas de índice e de peso, envio de retângulos, orçamento) conferido por um teste de renderização; a C ABI 29; os wrappers Rust; a aba Terrain Paint, a ferramenta do mouse, as ações de agente e estas páginas. Incidentes: uma entrada velha do cache de um terreno anterior com o mesmo id pôs 16 camadas num terreno novo (os testes compartilham o processo), então ligar as camadas agora sempre parte das quatro camadas do próprio terreno; uma restauração de cena remove todas as entradas do cache, o que teria descartado a pintura não salva, então as camadas são postas de lado e devolvidas.
