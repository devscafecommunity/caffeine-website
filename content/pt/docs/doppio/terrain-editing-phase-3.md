# Edição de terreno: relatório da Fase 3 (vegetação)

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Feito</span>
  <span class="doc-badge">Doppio</span>
  <span>Última atualização: <time datetime="2026-11-24">2026-11-24</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/pt/docs/doppio/terrain-editing-phase-3.md"><code>terrain-editing-phase-3.md</code></a></span>
</div>

<p class="doc-lede">A vegetação como dado do terreno, não como entidades, como foi construída: uma paleta de espécies, duas fontes que se empilham (plantas que nascem sozinhas por regras e uma semente, e plantas postas à mão), ids estáveis com edições que sobrevivem à regeneração, nada se sobrepondo, ferramentas de pincel, bake, um renderizador que desenha uma chamada instanciada por chunk e variante de espécie e a aba Terrain Vegetation, com a C ABI 30 que a leva. Ela se apoia na <a href="terrain-editing-phase-2.md">Fase 2</a>; o plano está em <a href="terrain-editing-roadmap.md"><code>terrain-editing-roadmap.md</code></a>.</p>

## 1. O que a Fase 3 entregou

<table>
  <thead><tr><th>Peça</th><th>Onde</th><th>O que faz</th></tr></thead>
  <tbody>
    <tr><td>Espécies</td><td><code>src/caffeine/terrain/vegetation/VegetationSpecies.*</code></td><td>Até 256 espécies: malhas das variantes, material, densidade por hectare, espaço, prioridade, faixa de escala, inclinação, afundamento, tinta, distância de desenho, regras; o formato de texto</td></tr>
    <tr><td>Armazém</td><td><code>terrain/vegetation/TerrainVegetation.*</code></td><td>As fontes procedural e manual, ids estáveis, overrides, resolução de conflitos, <code>resolveChunk</code>, o arquivo <code>.terrainveg</code></td></tr>
    <tr><td>Edições</td><td><code>terrain/vegetation/VegetationStroke.*</code></td><td>Sete ferramentas de pincel sobre a forma do pincel da escultura; bake, re-derive, reseed e edições da paleta; registros que desfazem exatamente</td></tr>
    <tr><td>Cache e cena</td><td><code>terrain/TerrainCache.*</code>, <code>scene/EditorSceneSerializer.cpp</code></td><td>O cache é dono do armazém, monta o terreno que uma resolução lê (alturas, normais, regras sobre máscaras) e acompanha os chunks que a GPU ainda não viu; blob de cena 13; salvar escreve o arquivo ao lado do terreno</td></tr>
    <tr><td>Renderizador</td><td><code>render/TerrainVegetationGpu.*</code>, <code>render/GpuSceneRenderer.cpp</code></td><td>Um buffer de instâncias por chunk e variante de espécie, descarte por frustum e distância, um orçamento de construção por quadro, desenhado com o pipeline instanciado que já existia</td></tr>
    <tr><td>C ABI</td><td><code>capi/EngineAPI.*</code></td><td>Versão 30: vegetação ligada e desligada, a paleta (ler, aplicar), traços de vegetação, bake, re-derive, reseed, instâncias perto de um ponto</td></tr>
    <tr><td>Aba Terrain Vegetation</td><td><code>uikit/panels/terrain_vegetation.rs</code>, <code>windows/main/terrainvegetation.rs</code></td><td>Lista de espécies, as configurações da espécie selecionada, variantes e regras, o pincel, a fonte procedural</td></tr>
  </tbody>
</table>

## 2. Duas fontes que se empilham

- <strong>Procedural:</strong> toda espécie com densidade nasce sozinha. Um chunk (32 m) é uma função pura da semente do mundo, do chunk e das regras (<code>scatter/Scatter</code>), então qualquer chunk pode ser feito em qualquer ordem, em qualquer thread, e nada é guardado: o armazém só tem a paleta, a semente e as edições.
- <strong>Manual:</strong> plantas postas pelo pincel ou pelo bake, guardadas uma a uma (37 bytes cada no arquivo).
- Cada espécie pode desligar a sua fonte procedural sem perder mais nada (<em>Grows by itself</em>), e pode ser escondida (<em>Drawn</em>).
- <strong>Bake</strong> transforma as plantas nascidas de uma espécie em manuais (mesmos lugares, mesmos tamanhos, overrides aplicados) e desliga a sua fonte procedural, para que o que está no chão possa ser editado uma a uma. <strong>Re-derive</strong> remove as plantas do bake e liga a fonte de novo. <strong>Reseed</strong> faz as plantas procedurais nascerem de outra semente.

## 3. Ids estáveis e overrides

- Um id procedural é um hash do uid da espécie e da posição da planta em centímetros inteiros; um id manual, de um contador e da posição. Reamostrar o mapa de alturas não muda nenhum dos dois.
- Editar uma planta nascida (apagar, escalar, girar, tingir, mover) é um <strong>override</strong> ligado a esse id; ele sobrevive à regeneração, a mudar o visual da espécie e a salvar. Editar uma planta manual a muda no lugar.
- Uma espécie mantém as suas plantas pelo <code>uid</code>, não pela posição na paleta: remover ou reordenar espécies não reatribui ids.

## 4. Nada se sobrepõe

- Duas plantas conflitam quando estão mais perto que a soma dos seus raios (o <em>espaço</em> da espécie vezes a escala da planta). A maior prioridade ganha; uma planta manual vence um empate com uma nascida.
- Pintar rejeita um lugar ocupado por uma planta de maior prioridade ou por uma manual da mesma prioridade; as plantas nascidas de prioridade menor ou igual cedem automaticamente quando uma manual é posta (voltam se ela for removida).
- As plantas nascidas de uma mesma espécie guardam a distância pela mesma regra (a regra de conflito do scatter só precisa de uma margem de um raio em torno de um chunk, então os chunks continuam independentes).
- Nada fica fora do terreno.

## 5. O terreno se adapta

- As alturas nunca são guardadas na vegetação: uma planta fica no chão como ele está, então <strong>esculpir reprojeta as plantas de graça</strong> (os chunks sob o traço são desenhados de novo).
- As regras de uma espécie (inclinação, altura, curvatura ou uma máscara guardada, cada uma um trapézio sobre 0 a 1) decidem onde ela pode ficar. Uma planta cujo lugar deixou de satisfazê-las fica <strong>escondida, não apagada</strong>; uma planta posta de propósito (<em>Only where the species' rules allow</em> desligado) é imune.
- <em>Lean to ground</em> mistura o eixo para cima da planta com a normal do terreno; <em>Sink</em> enterra a sua base.

## 6. Ferramentas de pincel

<table>
  <thead><tr><th>Ferramenta</th><th>O que um stamp faz</th></tr></thead>
  <tbody>
    <tr><td>Paint</td><td>Põe plantas da espécie selecionada: candidatas por 100 m2, aceitas pelo peso do pincel, rejeitadas onde algo no caminho tem prioridade ou as regras dizem não</td></tr>
    <tr><td>Erase</td><td>Remove as plantas sob ele (uma manual é apagada, uma nascida ganha um override)</td></tr>
    <tr><td>Scale, Rotate, Tint</td><td>Mudam o que está sob ele pelo peso do pincel</td></tr>
    <tr><td>Replace</td><td>Troca uma espécie por outra; uma planta nascida vira uma manual da nova espécie no mesmo lugar e tamanho</td></tr>
    <tr><td>Thin out</td><td>Remove uma fração do que está sob ele, de modo uniforme: cada planta tem um posto fixo, então afinar duas vezes com a mesma fração não remove mais</td></tr>
  </tbody>
</table>

O pincel é o mesmo que esculpe e pinta camadas (falloff, imagem do stamp, variação, simetria e máscaras de proteção valem quando <em>Shape from the Terrain Brush</em> está ligado). Os stamps são postos por espaçamento em metros, então o mesmo caminho dá as mesmas plantas em qualquer taxa de amostragem. Um traço é um passo de desfazer. <kbd>Ctrl</kbd> transforma plantar em apagar e de volta; <kbd>[</kbd> e <kbd>]</kbd> redimensionam o pincel ativo.

## 7. Renderização

- As plantas de um chunk são agrupadas por espécie e variante; cada grupo é um buffer de vértices de matrizes de modelo (64 bytes por planta) desenhado com uma chamada instanciada pelo pipeline que o renderizador já tinha.
- Os chunks são descartados por frustum e por distância (a distância <em>Drawn to</em> da espécie), e no máximo <strong>6 chunks são construídos por quadro</strong>, os mais próximos primeiro, então uma vista que de repente enxerga uma floresta se preenche em alguns quadros.
- Uma edição reconstrói só os chunks que ela tocou (e os vizinhos); um terreno movido reconstrói os seus. O painel mostra os bytes de GPU.
- O material de uma espécie (<code>.mat</code>), o corte alfa e o vento vêm do mesmo código que as entidades usam.

## 8. Arquivos e a cena

<table>
  <thead><tr><th>Arquivo</th><th>Conteúdo</th></tr></thead>
  <tbody>
    <tr><td><code>Name.terrainveg</code></td><td>Binário: <code>TVEG</code>, uma versão, a semente, as espécies como texto, as plantas manuais, os overrides, um CRC-32 do todo. Um arquivo danificado ou truncado é recusado com um motivo</td></tr>
  </tbody>
</table>

Salvar a cena escreve o arquivo ao lado dos dados do terreno e registra o seu caminho no componente do terreno (blob de cena versão 13); um arquivo ausente ou danificado deixa o terreno com uma paleta vazia em vez de perdê-lo. Os snapshots de cena em memória não levam a vegetação: ela é posta de lado e devolvida ao seu terreno, então desfazer outras edições não perde plantas.

## 9. Desfazer

Traços, edições de espécie, bake, re-derive e reseed são registros do motor, como os traços de escultura (as mesmas chamadas de reverter e refazer). Uma sequência de edições de um mesmo campo da espécie (arrastar um slider) se funde no registro da primeira edição. Ligar ou desligar a vegetação é um passo de cena.

## 10. C ABI 30

<table>
  <thead><tr><th>Função</th><th>Propósito</th></tr></thead>
  <tbody>
    <tr><td><code>caffeine_session_terrain_vegetation_enable</code>, <code>_vegetation</code></td><td>Ligar e desligar; contagens (espécies, plantas manuais, overrides, semente, bytes de GPU)</td></tr>
    <tr><td><code>caffeine_session_terrain_veg_species</code>, <code>_veg_species_apply</code></td><td>Ler uma espécie; substituir a paleta (por uid), com <code>merge_into</code> para fundir um arrasto de slider; o erro nomeia a linha</td></tr>
    <tr><td><code>caffeine_session_terrain_veg_paint_begin</code></td><td>Abre um traço de vegetação; pontos, fim, reverter e refazer são as chamadas de traço da versão 25</td></tr>
    <tr><td><code>caffeine_session_terrain_veg_bake</code>, <code>_veg_rederive</code>, <code>_veg_reseed</code></td><td>Operações da paleta inteira, com desfazer</td></tr>
    <tr><td><code>caffeine_session_terrain_veg_instances</code></td><td>As plantas perto de um ponto do mundo: id, espécie, variante, manual ou nascida, posição, escala</td></tr>
  </tbody>
</table>

## 11. Ações de agente

<code>show_terrain_vegetation</code>, <code>terrain_vegetation_active</code>, <code>terrain_vegetation_enable</code>, <code>terrain_vegetation_add_species</code>, <code>terrain_vegetation_select_species</code>, <code>terrain_vegetation_edit_species</code>, <code>terrain_vegetation_remove_species</code>, <code>terrain_vegetation_rule</code>, <code>terrain_vegetation_set_rule</code>, <code>terrain_vegetation_set</code>, <code>terrain_vegetation_reseed</code>, <code>terrain_vegetation_bake</code>, <code>terrain_vegetation_rederive</code> e <code>terrain_vegetation_stroke</code> (um traço por pontos do mundo, o mesmo caminho do mouse). A consulta <code>terrain_vegetation</code> lê o estado e a consulta <code>terrain_vegetation_instances</code> as plantas perto de um ponto. Os ids dos widgets começam com <code>terrain_vegetation.</code> e estão no catálogo.

## 12. Verificação e medidas

- C++: <code>tests/test_terrain_vegetation.cpp</code> (31 casos): o texto das espécies e os seus erros; 256 espécies e a remoção de uma espécie com as suas plantas; um chunk é uma função pura da semente (igual duas vezes, em qualquer ordem); a densidade por hectare é o que nasce; uma semente nova faz outra floresta; regras; nada se sobrepõe; prioridade; os ids são estáveis e esculpir os mantém; afundamento e inclinação acompanham o terreno; plantas manuais (adicionar, mover entre chunks, remover, ids); uma planta manual vence o seu lugar e as regras escondem sem apagar; overrides sobrevivem à regeneração; toda ferramenta desfaz e refaz bit a bit; o mesmo caminho dá as mesmas plantas em qualquer taxa de amostragem; pintar respeita regras e prioridade; apagar, escalar, girar, tingir, substituir e afinar; bake, re-derive, reseed e edições de espécie com desfazer; o arquivo e o seu dano. Um caso da C ABI cobre espécies, pintura, apagar, desfazer, bake, reseed e salvar e carregar uma cena.
- Rust: um teste da crate do motor que <strong>renderiza</strong> um terreno com uma espécie tingida de verde e conta os pixels dessa cor, apaga as plantas (elas saem da imagem), desfaz (voltam), refaz e esconde a espécie; testes de app <code>terrain_vegetation</code> (o painel, vegetação ligada como um passo, plantas nascidas, plantar por agente e por mouse, Ctrl para apagar, um arrasto de slider como um passo, variantes e regras, remover uma espécie com desfazer, reseed, bake e re-derive, exclusividade de ferramenta, limites do pincel); testes unitários do painel. O fluxo headless <code>terrain-vegetation-panel.json</code> roda pela CLI real.
- <strong>Custo de gerar:</strong> um gramado de cerca de 92 000 plantas (10 por m2 sobre 96 x 96 m) resolve em cerca de 1,7 s, algo como 18 microssegundos por planta, uma vez por chunk até uma edição mudá-lo. O renderizador então desenha a partir do buffer do chunk. 1M de plantas custam cerca de 18 s de geração espalhados pelos chunks que uma câmera alcança, e 64 MB de buffers de GPU; o orçamento de construção impede que um quadro trave.

## 13. Decisões registradas

- A vegetação é dado do terreno com arquivo próprio; uma planta tem 37 bytes no arquivo e 64 bytes num buffer de GPU, nunca é uma entidade.
- As plantas procedurais não são guardadas: a semente, as regras e as edições são.
- As entradas da paleta são identificadas por uid, não por índice, em ids, sementes e instâncias.
- Uma planta é desenhada com a tinta da sua espécie; a variação de cor por instância fica nos dados mas ainda não é desenhada.

## 14. Limites conhecidos e o que vem

- <strong>Não feito do roadmap:</strong> descarte por compute na GPU e desenhos indiretos, malhas de LOD por espécie e os impostores octaédricos gerados pelo <code>caf-pack</code>, sombras da vegetação e as ferramentas <em>Select and Move</em> (mover é um override nos dados mas não tem ferramenta). A meta de 1M é atendida em memória e geração, não no caminho de desenho: o descarte é na CPU, por chunk.
- As espécies vêm de malhas do projeto. O campo de receita é guardado para a Fase 4, que gera uma <code>.generator.nature</code> nas variantes e as regenera quando ela muda, para que editar uma espécie alcance todas as plantas.
- Outras fontes (um plano de scatter importado, um grafo, um script) não estão ligadas; as entidades de <code>scatterTerrain</code> continuam como eram.
- A vegetação ainda não está nos reflexos planares nem no GI do Photon, e a tinta por instância não é desenhada.
- Próximo: a Fase 4 (espécies a partir de receitas e edições que se propagam) e a Fase 5 (máscaras pintadas, estradas e rios, pressão de mesa digitalizadora, GI pré-compilado).

## 15. Diário de trabalho

- <strong>2026-11-24</strong>: as espécies, o armazém (fontes, ids, overrides, conflitos, o arquivo), o pincel e as operações da paleta inteira com testes; o cache, o formato de cena 13 e o arquivo; os buffers de GPU por chunk e os seus desenhos, conferidos por um teste de renderização; a C ABI 30; os wrappers Rust; a aba Terrain Vegetation, a ferramenta do mouse, as ações de agente e estas páginas. Incidentes: a fonte procedural não sabia onde o terreno termina (uma consulta chegou a 10 000 plantas para um terreno de 6,5 ha), então uma resolução agora descarta o que fica fora dele; o teste que esperava alguns milissegundos para um gramado denso mediu 1,7 s, então a página afirma o custo real.
