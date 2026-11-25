# Edição de terreno: relatório da Fase 4 (espécies a partir de receitas)

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Feito</span>
  <span class="doc-badge">Doppio</span>
  <span>Última atualização: <time datetime="2026-11-25">2026-11-25</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/pt/docs/doppio/terrain-editing-phase-4.md"><code>terrain-editing-phase-4.md</code></a></span>
</div>

<p class="doc-lede">Uma espécie que vem de uma receita <code>.generator.nature</code>, e edições que chegam a todas as plantas: a receita é gerada em várias variantes, cada uma com um material por parte, o editor gera de novo sozinho quando o arquivo da receita muda, e o terreno pode mudar o tamanho e a cor de uma espécie por meio das suas máscaras, de modo que esculpir e pintar máscaras readapta as plantas. Ela assenta na <a href="terrain-editing-phase-3.md">Fase 3</a>; o plano está em <a href="terrain-editing-roadmap.md"><code>terrain-editing-roadmap.md</code></a>. A C ABI agora é a 31.</p>

## 1. O que a Fase 4 entregou

<table>
  <thead><tr><th>Peça</th><th>Onde</th><th>O que faz</th></tr></thead>
  <tbody>
    <tr><td>Dados da espécie</td><td><code>terrain/vegetation/VegetationSpecies.*</code></td><td>Um material por sub-malha (<code>slot_material</code>), o hash do conteúdo da receita (<code>recipe_hash</code>) e adaptações por máscara (<code>adapt scale</code>, <code>adapt tint</code>), no texto da espécie com erros de leitura que nomeiam a linha</td></tr>
    <tr><td>Adaptação</td><td><code>terrain/vegetation/TerrainVegetation.*</code>, <code>terrain/TerrainCache.cpp</code></td><td>Uma resolução lê a máscara guardada sob cada planta e a escala ou tinge entre o 0 e o 1 da máscara; nada é guardado por planta</td></tr>
    <tr><td>Renderizador</td><td><code>render/GpuSceneRenderer.cpp</code></td><td>Uma espécie com várias sub-malhas é desenhada uma vez por sub-malha, cada uma com o seu material</td></tr>
    <tr><td>C ABI 31</td><td><code>capi/EngineAPI.*</code></td><td><code>CaffeineVegSpecies</code> leva <code>recipe_hash</code>, até 8 materiais de slot e até 4 adaptações (<code>CaffeineVegAdapt</code>)</td></tr>
    <tr><td>Geração da receita</td><td><code>uikit/vegetation_recipe.rs</code></td><td>Gera uma receita em N variantes (outras sementes do mesmo grafo), um OBJ cada com as partes como sub-malhas, numa pasta nomeada pelo hash do conteúdo da receita; uma geração em cache é reaproveitada</td></tr>
    <tr><td>Aba Terrain Vegetation</td><td><code>uikit/panels/terrain_vegetation.rs</code>, <code>windows/main/terrainvegetation.rs</code></td><td>Um cartão <em>Recipe</em> (arquivo, número de variantes, Bake) e um cartão <em>How the ground changes it</em> (termos de tamanho e cor por máscara)</td></tr>
  </tbody>
</table>

## 2. Uma espécie a partir de uma receita

- Pôr no campo <em>Recipe</em> de uma espécie um arquivo <code>.generator.nature</code> do projeto gera-a: o grafo é avaliado para N sementes (1 a 8, por omissão 4), cada semente é uma variante, e cada parte do modelo vira uma sub-malha do OBJ da sua variante. A semente da variante <em>i</em> é função do uid da espécie e de <em>i</em>, por isso uma geração é reproduzível.
- Cada parte recebe o seu próprio <code>.mat</code> (os mesmos materiais que o Nature Generator usa), guardado como os <em>slot materials</em> da espécie; o renderizador faz uma chamada por sub-malha e variante.
- O hash do conteúdo do arquivo da receita fica guardado na espécie (<code>recipe_hash</code>). Os arquivos gerados ficam em <code>Vegetation/&lt;hash&gt;/</code> sob a pasta de modelos de natureza do projeto, assim outro conteúdo de receita é outra pasta e uma geração que já está em disco não é refeita.
- Gerar é um passo de desfazer: as malhas, os materiais de slot e o hash da espécie mudam juntos, e desfazer devolve os anteriores. Uma receita que não existe ou não lê é dita na linha de estado da aba e a espécie mantém as malhas que tinha.

## 3. Edições que se propagam

- Cada planta de uma espécie refere-se à espécie pelo uid e desenha o que a espécie diz agora, por isso mudar a espécie (as malhas, os materiais, a faixa de escala, a tinta) muda todas as plantas de uma vez; nenhuma planta é substituída e nenhum id muda.
- O editor compara o <code>recipe_hash</code> de cada espécie gerada com o hash do arquivo da receita no tick da viewport, no máximo a cada 2 segundos. Quando o arquivo mudou (editado no Nature Generator ou à mão) gera de novo sozinho, como um passo de desfazer; quando nada mudou não faz nada e não grava passo.
- Mudar o número de variantes pode mudar a variante que uma planta mostra, nunca quais plantas existem.

## 4. O terreno adapta a espécie

- Uma espécie tem até 4 <strong>adaptações</strong>. Um termo de <em>tamanho</em> multiplica a escala da planta por um valor tomado entre <em>at 0</em> e <em>at 1</em> por uma máscara guardada (inclinação, altura, curvatura ou uma máscara pintada) lida sob a planta; um termo de <em>cor</em> multiplica a sua tinta da mesma maneira.
- É aplicada quando as plantas são resolvidas, não guardada nelas, de modo que <strong>esculpir ou pintar uma máscara readapta as plantas</strong> sozinho (os chunks sob o traço são desenhados de novo). A escala fica entre 0,05 e 50 vezes, e a base afunda com a escala adaptada.
- Os overrides ficam por cima: uma planta escalada à mão é escalada à mão primeiro e depois adaptada.

## 5. C ABI 31

<code>CAFFEINE_CAPI_VERSION</code> é 31. <code>CaffeineVegSpecies</code> ganhou <code>recipe_hash</code>, <code>slot_material_count</code> com <code>slot_materials[8][256]</code>, e <code>adapt_count</code> com <code>adapt[4]</code> (<code>CaffeineVegAdapt</code>: nome da máscara, alvo tamanho ou cor, os dois valores). As chamadas de paleta da versão 30 os levam; valores além da capacidade de um campo são mantidos da espécie existente em vez de cortados em silêncio.

## 6. Ações de agente

Novas: <code>terrain_vegetation_bake_recipe</code> (gera já a espécie selecionada, com um número de variantes), <code>terrain_vegetation_sync_recipes</code> (gera as espécies cuja receita mudou) e <code>terrain_vegetation_adapt</code> (adiciona ou remove uma adaptação). <code>terrain_vegetation_edit_species</code> aceita <code>recipe</code> e <code>recipe_variants</code>; a consulta <code>terrain_vegetation</code> lista as máscaras do terreno, o número de variantes e, de cada espécie, a receita, o hash, os materiais de slot e as adaptações.

## 7. Verificação

- C++: <code>tests/test_terrain_vegetation.cpp</code> (34 casos, 3 novos): a adaptação por máscara muda tamanho e tinta e acompanha a máscara quando ela é editada; os materiais de slot e o hash da receita ida e voltam pelo texto da espécie e pelo arquivo; os novos erros de texto (números em falta, escala não positiva, um tipo desconhecido). O caso da C ABI cobre a nova ida e volta da estrutura e o desfazer.
- Rust: um teste da crate do motor que <strong>renderiza</strong> um modelo de duas partes com um material diferente por parte e conta os pixels de cada cor, depois adapta a espécie ao terreno e conta de novo; quatro testes unitários de <code>vegetation_recipe</code> (hash, sementes por variante, geração, reaproveitamento do cache); testes do app: uma espécie gerada a partir de uma receita acompanha a receita quando o arquivo muda, com as mesmas plantas antes e depois, um passo de desfazer por geração e nenhum quando nada mudou; uma receita em falta é dita e mantém as malhas; as adaptações são adicionadas, editadas num passo por arrasto e removidas com desfazer.

## 8. Decisões registradas

- A receita é a fonte de verdade do aspeto de uma espécie; os OBJ gerados são um cache nomeado pelo conteúdo, nunca editado à mão.
- A adaptação é calculada quando as plantas são resolvidas, por isso não custa nada no arquivo e não pode ficar desatualizada quando o terreno muda.
- No máximo 8 materiais de slot e 4 adaptações por espécie mantêm a estrutura C um registro simples de tamanho fixo.

## 9. Limites conhecidos e o que vem

- <strong>A variação da variante escolhida por uma máscara não está feita</strong>: uma máscara muda o tamanho e a tinta de uma planta, não a variante que ela mostra. O item do roadmap fica registrado como limite.
- Os materiais de uma espécie gerada são os que <code>ensure_nature_material</code> faz para cada parte; uma receita cujas partes não têm material ali é desenhada com o <em>material</em> único da espécie.
- Só receitas <code>.generator.nature</code> são geradas; as malhas de LOD das árvores, as sombras da vegetação e os limites do renderizador da Fase 3 continuam.
- Próximo: a Fase 5 (máscaras pintadas, estradas e rios, pressão de mesa digitalizadora, GI pré-compilado).

## 10. Diário de trabalho

- <strong>2026-11-25</strong>: os dados da espécie (materiais de slot, hash da receita, adaptações), a adaptação na resolução e o callback da máscara, os desenhos por sub-malha, a C ABI 31 e os seus testes; o gerador de receitas e o seu cache; os cartões de receita e adaptação, a regeneração automática, as ações de agente e estas páginas. Incidentes: uma espécie sem malhas não coloca plantas, por isso o teste da receita agora parte de uma espécie que tem uma; o JSON de espécie do agente bateu no limite de recursão da macro <code>json!</code> e passou para uma função auxiliar.
