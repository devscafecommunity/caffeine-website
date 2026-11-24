# Edição de terreno: relatório da Fase 1 (escultura)

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Feito</span>
  <span class="doc-badge">Doppio</span>
  <span>Última atualização: <time datetime="2026-11-24">2026-11-24</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/pt/docs/doppio/terrain-editing-phase-1.md"><code>terrain-editing-phase-1.md</code></a></span>
</div>

<p class="doc-lede">A escultura como foi construída: 16 modos de pincel, uma biblioteca de 58 pincéis (42 deles stamps procedurais), arquivos <code>.brush</code>, simetria, máscaras de proteção, variação, a aba Terrain Brush e a ferramenta do mouse, com a C ABI 28 que os leva e como cada peça é verificada. Ela se apoia na <a href="terrain-editing-phase-0.md">Fase 0</a>; o plano está em <a href="terrain-editing-roadmap.md"><code>terrain-editing-roadmap.md</code></a>.</p>

## 1. O que a Fase 1 entregou

<table>
  <thead><tr><th>Peça</th><th>Onde</th><th>O que faz</th></tr></thead>
  <tbody>
    <tr><td>Stamps procedurais</td><td><code>src/caffeine/terrain/edit/BrushStamps.*</code></td><td>42 stamps em tons de cinza gerados só com aritmética (sem bibliotecas, iguais em qualquer máquina): Basic 8, Noise 8, Rock 7, Dunes 4, Craters 5, Terraces 3, Shapes 7</td></tr>
    <tr><td>Motor de traço</td><td><code>terrain/edit/TerrainStroke.*</code></td><td>Dez modos novos, variação por stamp, simetria, máscaras de proteção (os cinco modos da Fase 0 mantêm o resultado dos testes dourados bit a bit)</td></tr>
    <tr><td>Pincel como documento</td><td><code>terrain/edit/BrushPreset.*</code></td><td><code>BrushPreset</code>, o formato de texto <code>.brush</code> (leitura e escrita), stamps de imagem pelo gerenciador de assets e a biblioteca embutida de 58 pincéis</td></tr>
    <tr><td>C ABI</td><td><code>capi/EngineAPI.*</code></td><td>Versão 28: a biblioteca, ler e escrever texto, uma prévia do stamp e um traço iniciado a partir de um preset inteiro</td></tr>
    <tr><td>Wrappers Rust</td><td><code>doppio/crates/engine</code></td><td><code>BrushMode</code> (16), <code>Falloff</code>, <code>SymmetryKind</code>, <code>BrushPreset</code>, <code>builtin_brushes</code>, <code>parse_brush</code>, <code>format_brush</code>, <code>brush_stamp_image</code>, <code>terrain_stroke_begin_preset</code></td></tr>
    <tr><td>Aba Terrain Brush</td><td><code>uikit/panels/terrain_brush.rs</code>, <code>uikit/components/brush_card.rs</code></td><td>Grade da biblioteca com prévias, busca e chips de categoria, as configurações do pincel, variação, simetria, proteção e o arquivo <code>.brush</code></td></tr>
    <tr><td>Ferramenta de escultura</td><td><code>windows/main/terraineditor.rs</code></td><td>Apertar o botão esquerdo no terreno inicia um traço, mover o estende, soltar o fecha como um passo de desfazer</td></tr>
    <tr><td>Desfazer</td><td><code>history.rs</code></td><td>Passos de traço: as alturas do terreno não estão no snapshot da cena, então um passo leva o registro de traço do motor e desfazer reverte só esse registro</td></tr>
  </tbody>
</table>

## 2. Modos

<table>
  <thead><tr><th>Modo</th><th>O que faz</th><th>Configurações que usa</th></tr></thead>
  <tbody>
    <tr><td>Raise, Lower</td><td>Somam ou tiram metros de altura por stamp</td><td>força</td></tr>
    <tr><td>Smooth, Flatten</td><td>Movem uma fração em direção à média local, ou a uma altura (a sob o primeiro stamp quando é negativa)</td><td>força, altura do Flatten</td></tr>
    <tr><td>Noise</td><td>Ruído determinístico para a semente</td><td>força, semente</td></tr>
    <tr><td>Ramp</td><td>Faz uma rampa reta de onde o traço começou até o cursor</td><td>força</td></tr>
    <tr><td>Terrace</td><td>Degraus suavizados de uma altura dada</td><td>altura do degrau</td></tr>
    <tr><td>Pinch, Bulge</td><td>Puxam o terreno para o centro do stamp, ou o empurram para fora</td><td>força</td></tr>
    <tr><td>Stamp (absolute), (keep higher), (keep lower)</td><td>Pressionam o relevo do stamp no terreno: definem-no, só elevam até ele, só rebaixam até ele. Keep higher repetido constrói sobre o terreno novo</td><td>força, stamp com sinal</td></tr>
    <tr><td>Clone</td><td>Copia o relevo que está a um deslocamento do stamp</td><td>origem X e Z</td></tr>
    <tr><td>Smudge</td><td>Arrasta o terreno na direção do traço</td><td>força</td></tr>
    <tr><td>Erode (thermal)</td><td>Desliza material por encostas mais íngremes que o ângulo de talude; o volume é conservado</td><td>ângulo de talude, passadas</td></tr>
    <tr><td>Erode (hydraulic)</td><td>Gotas que escavam e depositam, determinísticas para a semente</td><td>gotas</td></tr>
  </tbody>
</table>

O painel mostra um número só para os modos que o usam, então um pincel de elevar não oferece ângulo de talude.

## 3. A biblioteca

- <strong>42 pincéis de stamp</strong>, cada um um stamp procedural com o raio, a força e o espaçamento que combinam com ele. Um stamp <em>com sinal</em> (crateras, vales, leitos de rio) trata o cinza médio como neutro: mais claro eleva, mais escuro rebaixa, que é como uma cratera ganha a borda elevada e a bacia.
- <strong>16 ferramentas</strong>, uma para cada modo, com padrões sensatos (Raise, Lower, Smooth, Flatten, Noise, Ramp, Terrace, Pinch, Bulge, Stamp absolute, Stamp max, Stamp min, Clone, Smudge, Thermal erosion, Hydraulic erosion).
- <strong>Os seus</strong>: todo arquivo <code>.brush</code> da pasta <code>Brushes</code> do projeto entra na biblioteca em <em>Custom</em>. <em>Save .brush</em> escreve o pincel de trabalho lá; um arquivo que não pode ser lido é relatado com a sua linha e não impede os outros.
- Escolher um pincel o <em>copia</em> para o pincel de trabalho. As edições mudam só a cópia; <em>Revert</em> devolve a versão da biblioteca.

## 4. Variação, simetria e proteção

- <strong>Variação</strong> por stamp, determinística para a semente: dispersão (uma fração do raio), giro (graus para cada lado), tamanho e força.
- <strong>Simetria</strong> em torno de um centro em metros do centro do terreno: espelho X, espelho Z, ambos, ou radial com 2 a 16 cópias. Um stamp que cai sobre o eixo é posto uma vez, não duas.
- <strong>Proteção</strong>: até quatro termos. Cada um nomeia uma máscara (<code>slope</code>, <code>height</code>, <code>curvature</code>, ou uma máscara guardada pelo nome no arquivo) e um trapézio de quatro números (0 a 1); o pincel age só onde a máscara está dentro dele e esmaece nas bordas. Uma máscara que não existe protege tudo. Todos os pesos são calculados antes de qualquer altura mudar, então o resultado não depende da ordem dos vértices.

## 5. O arquivo .brush

Um <code>.brush</code> é texto puro, um <code>chave valor</code> por linha (o roadmap dizia JSON; o núcleo não tem leitor de JSON, e um formato por linhas compara e mescla bem). <code>#</code> começa um comentário e chaves desconhecidas são ignoradas, então uma versão antiga abre um arquivo mais novo.

```
# A crater with a raised rim, scattered a little
name My crater
category Craters
mode raise
radius 14
strength 3
stamp procedural crater_simple 128
signed 1
jitter 0.1 15 0.1 0
symmetry none 4 0 0
protect slope 0 0 0.3 0.4
```

Chaves: <code>name</code>, <code>category</code>, <code>mode</code>, <code>radius</code>, <code>strength</code>, <code>spacing</code>, <code>falloff</code>, <code>rotation</code>, <code>target_height</code>, <code>seed</code>, <code>stamp</code> (<code>none</code>, <code>procedural id [tamanho]</code> ou <code>image caminho [tamanho]</code>), <code>signed</code>, <code>step</code>, <code>talus</code>, <code>iterations</code>, <code>droplets</code>, <code>offset</code>, <code>jitter</code> (posição, giro, tamanho, opacidade), <code>symmetry</code> (tipo, quantidade, centro X, centro Z), <code>pressure</code> e <code>protect</code> (máscara e quatro números, repetível). Um stamp de imagem é um caminho do projeto lido pelo gerenciador de assets e reamostrado para cinza.

## 6. A aba Terrain Brush

<table>
  <thead><tr><th>Controle</th><th>O que faz</th></tr></thead>
  <tbody>
    <tr><td>View &gt; Terrain Brush</td><td>Traz a aba para a frente (ela fica com o Inspector) e carrega a biblioteca</td></tr>
    <tr><td>Brush on</td><td>Liga a ferramenta: o anel segue o mouse sobre o terreno e apertar o botão esquerdo esculpe em vez de orbitar. Os botões direito e do meio continuam movendo a câmera</td></tr>
    <tr><td>Busca e chips de categoria</td><td>Filtram a grade por nome, categoria ou modo</td></tr>
    <tr><td>Cartões de pincel</td><td>Um clique seleciona um pincel; a imagem é o seu stamp, ou a curva de falloff numa ferramenta</td></tr>
    <tr><td>Brush, Variation, Symmetry, Protection</td><td>As configurações do pincel de trabalho</td></tr>
    <tr><td>Brush file</td><td>Nome, <em>Save .brush</em>, <em>Revert</em>, <em>Reload folder</em></td></tr>
  </tbody>
</table>

<p>Atalhos com a ferramenta ligada: <kbd>[</kbd> e <kbd>]</kbd> diminuem e aumentam o raio em 15%, <kbd>Ctrl</kbd> inverte (raise vira lower, pinch vira bulge, keep higher vira keep lower), <kbd>Shift</kbd> suaviza com o mesmo raio e a mesma força. Um traço é um passo de desfazer, qualquer que seja o seu tamanho.</p>

## 7. C ABI 28

<table>
  <thead><tr><th>Função</th><th>Propósito</th></tr></thead>
  <tbody>
    <tr><td><code>caffeine_terrain_brush_count</code>, <code>caffeine_terrain_brush_at</code></td><td>A biblioteca embutida, um <code>CaffeineBrushPreset</code> por pincel</td></tr>
    <tr><td><code>caffeine_terrain_brush_stamp</code></td><td>A imagem em cinza de um stamp procedural, para uma prévia</td></tr>
    <tr><td><code>caffeine_terrain_brush_parse</code>, <code>caffeine_terrain_brush_format</code></td><td>Leem e escrevem o texto do <code>.brush</code>; um erro de leitura nomeia a linha</td></tr>
    <tr><td><code>caffeine_session_terrain_stroke_begin_preset</code></td><td>Inicia um traço a partir de um preset inteiro: modos 5 a 15, variação, simetria, até <code>CAFFEINE_BRUSH_PROTECT_MAX</code> (4) termos de proteção contra as máscaras guardadas do terreno, stamps de imagem pelo gerenciador de assets da sessão</td></tr>
  </tbody>
</table>

As funções de traço da versão 25 (<code>_point</code>, <code>_end</code>, <code>_revert</code>, <code>_reapply</code>) não mudaram; <code>_begin</code> aceita os modos 0 a 15.

## 8. Ações de agente

Tudo o que o mouse faz também é uma ação que devolve uma <code>Message</code>, então um agente e um fluxo headless podem conduzir a ferramenta: <code>show_terrain_brush</code>, <code>terrain_brush_active</code>, <code>terrain_brush_select</code> (por nome ou índice), <code>terrain_brush_set</code> (uma configuração pela chave, ou <code>mode</code>, <code>falloff</code>, <code>symmetry</code>, <code>signed</code>, <code>name</code>), <code>terrain_brush_protect</code>, <code>terrain_brush_search</code>, <code>terrain_brush_save</code> e <code>terrain_brush_stroke</code> (um traço por pontos do mundo, o mesmo caminho do mouse). A consulta <code>terrain_brush</code> lê a biblioteca, o pincel de trabalho, seus termos de proteção, o ponto sob o mouse e a linha de status. Os ids dos widgets começam com <code>terrain_brush.</code> e estão no catálogo.

## 9. Verificação

- C++: <code>tests/test_terrain_brushes.cpp</code> (24 casos): a biblioteca tem 42 stamps únicos; os stamps ficam na faixa, são determinísticos para a semente e rápidos de gerar; cada modo novo se comporta como descrito acima; a erosão térmica conserva o volume; a erosão hidráulica é determinística e custa menos de 12 ms por stamp; simetria espelho, ambos e radial; proteção por inclinação, faixa de altura, máscara desconhecida e máscara guardada; <strong>todo modo desfaz bit a bit e repete exatamente</strong>; o mesmo caminho dá o mesmo terreno em qualquer taxa de amostragem; a ida e volta do <code>.brush</code>, erros com número de linha e stamps de imagem. Um caso da C ABI cobre a biblioteca, o texto, a prévia, um traço a partir de um preset e o seu desfazer.
- Rust: <code>history</code> (passos de traço se intercalam com edições de cena na ordem), a tabela de números do painel (todo número vai e volta e fica na faixa, cada um tem um id catalogado), o módulo do editor (miniaturas, nomes de arquivo, modificadores, filtro) e os testes de app <code>terrain_editor</code> com o motor real: arrastar o mouse sobre o terreno faz um passo que desfaz e refaz bit a bit e não orbita a câmera; um traço de agente é igual ao do mouse; traço, entidade, traço desfeitos na ordem certa; modificadores e teclas de raio; edições de proteção; salvar e recarregar um <code>.brush</code>; um registro descartado é relatado. O fluxo headless <code>terrain-brush-panel.json</code> confere os controles pela CLI real.

## 10. Decisões registradas

- Os stamps são procedurais para que um build não precise de arquivos de imagem e a biblioteca seja idêntica em todo lugar; stamps de imagem são para os pincéis do próprio usuário.
- Desfazer um traço reverte o registro do motor, não um snapshot da cena, porque as alturas do terreno vivem no cache de alturas. Os registros de traço ficam dentro de um orçamento (512 MB); um passo mais antigo que isso relata um erro em vez de falhar em silêncio.
- Os cinco modos da Fase 0 são fixados por testes dourados e mantidos bit a bit; os modos novos são fixados por testes de comportamento.

## 11. Limites conhecidos e o que vem

- A aba ainda não tem seletor de imagem de stamp (escreva <code>stamp image caminho</code> no arquivo); a prévia de uma ferramenta é a sua curva de falloff, e o anel mostra o tamanho, não a forma do stamp.
- Ramp precisa de um arrasto (a rampa vai do primeiro stamp ao cursor); com um clique só, não faz nada.
- A pressão de mesa digitalizadora está ligada no traço (<code>pressure</code> no pincel), mas o mouse envia 1; ela chega na Fase 5.
- Próximo: as Fases 2 (paleta de materiais e pintura) e 3 (vegetação) podem rodar em paralelo, porque mexem em arquivos diferentes.

## 12. Diário de trabalho

- <strong>2026-11-23</strong>: a biblioteca de stamps, os dez modos novos, variação, simetria e proteção no motor de traço; a dependência de ordem da proteção (as máscaras liam o terreno que um stamp já tinha mudado) foi achada por um teste e corrigida calculando todos os pesos antes de qualquer altura mudar; o formato <code>.brush</code> e a C ABI 28.
- <strong>2026-11-24</strong>: wrappers Rust, passos de traço no histórico, a aba Terrain Brush, a ferramenta do mouse, atalhos, ações de agente, testes e estas páginas.
