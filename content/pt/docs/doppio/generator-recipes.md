# Receitas de geradores (`generator.*`)

<div class="doc-meta">
  <span class="doc-badge doc-badge--reference">Referência</span>
  <span class="doc-badge">Doppio</span>
  <span>Última atualização: <time datetime="2026-11-20">2026-11-20</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/doppio/crates/ui/src/uikit/recipe.rs"><code>recipe.rs</code></a></span>
</div>

<p class="doc-lede">Uma receita é o grafo editável por trás de tudo o que um gerador cozinhou (bake). É um ficheiro
ao lado do produto, pelo que a origem de uma textura, material, árvore, lago ou terreno nunca se perde.</p>

## 1. Tipo de ficheiro

`<name>.generator.<kind>`, um tipo por gerador:

| Ficheiro | Gerador | Produto ao lado |
|---|---|---|
| `Bark.generator.texture` | Texture Generator | `Bark.png` |
| `Rock.generator.material` | Material Generator | `Rock.mat` |
| `Oak.generator.nature` | Nature Generator | `oak_trunk.obj`, `oak_leaves.obj` |
| `Lake.generator.water` | Water Generator | `lake.mat` |
| `Alpine.generator.terrain` | Terrain Generator | `alpine_height.png` |

O ficheiro é JSON: `format` (`caffeine-generator`), `version`, `kind`, `name`, `product`, `graph` (a forma textual própria do gerador)
e `generator_version`, a versão do algoritmo com que a receita foi criada (os ficheiros sem ela leem-se como 1; os novos escrevem 2,
o mesmo número que `Caffeine::Core::GENERATOR_VERSION`). Cada gerador continua a ser dono do seu formato de grafo; a receita limita-se a envolvê-lo.
Um ficheiro escrito por um Doppio mais recente é recusado com uma mensagem, em vez de ser mal interpretado.
O motor lista estes ficheiros com o tipo de asset `generator`.

## 2. Comportamento

- Guardar, exportar **ou colocar** o resultado de um gerador escreve a sua receita ao lado do produto: *Place in scene* nos
  separadores Nature, Water e Terrain guarda também o grafo, pelo que nada do que é colocado fica sem saída. Water e Terrain escrevem a
  receita **antes** de tocarem na cena, por isso uma falha ao colocar nunca perde o grafo; a receita fica em `Water/` ou
  `Terrain/` ao lado do material ou do mapa de altura e aparece no painel Assets assim que é escrita.
- Faça **duplo clique** numa receita, ou num asset cozinhado que tenha uma, para reabrir o grafo no seu gerador.
- Os assets importados não têm receita, por isso o duplo clique comporta-se como antes (uma imagem torna-se um novo material).
  Um arquivo MaterialCraft é a exceção, porque transporta o seu grafo.
- Os sidecars mais antigos (`.mgraph`, `.texgraph`, `.nature`, `.water`, `.terrain-graph`) continuam a ser encontrados e
  abertos; a gravação seguinte escreve o novo ficheiro.
- Os produtos de várias partes (`oak_trunk.obj`) encontram a receita Nature ou Terrain cujo nome é prefixo do seu.
- Uma receita pode listar os ficheiros que escreveu em `products` (caminhos relativos à raiz dos assets). A receita Nature fá-lo.
- Os agentes e os testes reabrem um grafo com a ação `open_generator` (`Message::OpenGeneratorFor`): o caminho pode ser uma
  receita, um `.prefab`, ou qualquer coisa que um gerador tenha cozinhado.

### Uma árvore é um bundle

Colocar ou exportar um modelo Nature escreve tudo aquilo de que é feito, para que possa ser editado, reutilizado e partilhado:

| Ficheiro | O que é |
|---|---|
| `Models/Nature/oak_trunk.obj`, `oak_leaves.obj` | as meshes |
| `Materials/Nature/*.mat` e `Textures/Nature/*.png` | um material por parte, com os seus mapas |
| `Models/Nature/oak.generator.nature` | o grafo, mais `products`: todos os ficheiros acima |
| `Materials/Nature/<name>.generator.material` | o grafo do Material Generator de cada material de **biblioteca** (chão, agulhas…); nunca é substituído depois de o ter editado |
| `Prefabs/oak.prefab` | a árvore tal como foi colocada (grupo, partes, slots de material, interruptores de Micromesh), a apontar de volta para a sua receita |

As superfícies de casca, rocha e cards de folhas são geradas pelo próprio grafo Nature, pelo que a receita nature é a receita delas.
**Export** constrói o mesmo bundle sem deixar a árvore na cena.

## 2b. Prefabs (`*.prefab`)

Um prefab é um snapshot JSON de uma árvore de entidades **tal como o Inspector a mostra**: todos os componentes e campos, por nome
(`uikit/prefab_file.rs`, formato `caffeine-prefab`). A primeira entidade é a raiz, guardada na origem; `generator` indica
a receita de onde veio. Faça duplo clique num prefab no painel Assets (ou chame a ação `place_prefab`) para largar uma cópia no
foco da câmara; é um único passo de undo. A água e o terreno são superfícies do lado do motor e não campos de componente, pelo que
têm uma receita mas não um prefab.

## 3. Pastas

As pastas que o editor cria começam por maiúscula: `Assets/Raw/{Animations,Audio,Generators,Materials,Models,Prefabs,Sky,TextureSets,Textures}`,
`Assets/Processed`, `Scripts`, `Scenes`, `Build`, e `Nature`, `Terrain`, `Water` para o resultado dos geradores.
Os projetos existentes mantêm os seus próprios nomes; renomear é uma escolha do utilizador.

## 4. caf-pack

Os ficheiros `.generator.*` são **fontes**, não assets a empacotar. O caf-pack tem agora uma regra explícita
(`Registry::isEditorOnly`): as receitas e os sidecars de grafo mais antigos (`.mgraph`, `.texgraph`, `.nature`, `.water`,
`.terrain-graph`) são ignorados e listados (`Skipped editor-only source: ...`) em vez de fazerem falhar o pacote com
"No processor registered". `Packer::getSkipped()` devolve a lista. Coberto por `tests/test_cafpack_editor_only.cpp`
(a alteração vive no submódulo `caf-pack`).

## 5. Referenciar receitas

Os geradores apontam para receitas, não para modelos finais: um gerador de vegetação volta a executar uma receita `Oak` para criar
variantes e adapta o resultado ao terreno. O resolvedor é `uikit/recipe_ref.rs`.

- [x] **Slots.** Os nós *Your Material (.mat)* e *Your Texture (PNG)* do Nature e os slots de camada do Terrain aceitam um
      caminho `generator.material` / `generator.texture`. Uma receita de textura é cozinhada ao seu lado quando falta o PNG;
      uma receita de material tem de ter sido cozinhada uma vez (o erro di-lo). Uma receita do tipo errado é recusada com uma mensagem.
- [x] **Variantes, em cache.** `bake_nature_variant(recipe, seed, quality, cache_dir)` volta a semear o `seed` de cada nó a partir da
      seed da variante e escreve as partes OBJ em `<cache>/<name>_<key>/`; a chave faz o hash do grafo da receita, da sua
      `generator_version`, da seed e da qualidade, pelo que editar a receita invalida a cache. A seed 0 mantém as seeds
      originais. `nature_variants` deriva N seeds a partir de uma seed base. CLI: `doppio-material variants Oak.generator.nature --out DIR --count 8 --seed 3`.
- [x] **Os mesmos números nas duas linguagens.** `derive_seed`/`unit` são SplitMix64, bit a bit `Caffeine::Core::deriveSeed`/`toUnit`;
      os testes golden em `tests/test_hash.cpp` e `recipe_ref.rs` fixam os mesmos valores.
- [x] `generator_version` em todas as receitas.
- [ ] Water: o seu material vem do nó Water Material, que já escreve `Water/<name>.mat`; um slot de receita não está ligado.
- [ ] Bake a pedido de uma receita de **material** (precisa da sessão do motor que o Material Generator usa).
- [ ] Um *gerador* de scatter ou de vegetação que consuma `nature_variants` e coloque os resultados num terreno.
