# Editor de cena

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/doppio/crates/ui/src/windows/main.rs"><code>windows/main.rs</code></a></span>
</div>

<p class="doc-lede">A superfície de edição do Doppio: uma árvore de cena, um viewport
renderizado, um inspector feito de cartões de componentes e um histórico de comandos
que cada ação de edição regista.</p>

<figure class="doc-figure">
  <img src="../images/editor/workspace-scene.png" alt="Editor de cena do Doppio com hierarchy, viewport, inspector e painéis de assets" loading="lazy">
  <figcaption>Uma cena aberta no Doppio. A seleção na Hierarchy comanda o Inspector; o Viewport desenha o render do motor com gizmos e marcadores de cena por cima.</figcaption>
</figure>

## O que o editor edita

O editor lê e escreve os mesmos dados ECS que o runtime usa. Uma cena é um ficheiro
`.caf`, guardado pelo projeto em `scenes/`. O editor nunca tem um formato de cena
paralelo.

<table class="doc-table">
  <thead>
    <tr><th>Superfície</th><th>O que pode fazer</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>Hierarchy</strong></td><td>Pesquisar, selecionar, adicionar e eliminar entidades; expandir grupos pai; arrastar uma linha para outra para reparentar.</td></tr>
    <tr><td><strong>Viewport</strong></td><td>Orbitar, fazer pan e voar com a câmara; clicar para selecionar; arrastar o gizmo move/rotate/scale; duplo clique para focar.</td></tr>
    <tr><td><strong>Inspector</strong></td><td>Renomear a entidade, editar a transform combinada, expandir cartões de componentes, remover componentes e adicionar behaviours.</td></tr>
    <tr><td><strong>Assets</strong></td><td>Navegar no projeto, criar/importar assets e empacotar um <code>.cap</code>.</td></tr>
    <tr><td><strong>Console</strong></td><td>Entradas filtradas de Errors, Log, Actions, Engine e UI.</td></tr>
  </tbody>
</table>

## Hierarchy

- As linhas são construídas a partir dos links `Scene::Parent`, não de uma árvore só
  de UI. Reordenar ou reparentar escreve o componente pai no ECS, e o viewport resolve
  as transforms mundiais pela cadeia de pais.
- O campo de pesquisa filtra por nome. Grupos pai compõem posição, rotação e escala
  nos filhos.
- Cada linha e controlo tem um id estável (`hierarchy.list.entity_row.<n>`,
  `hierarchy.search`, `hierarchy.add`), para flows e agentes.
- O menu de contexto adiciona, elimina e foca uma entidade.

## Inspector

O inspector é composto por cartões reutilizáveis:

| Cartão | Conteúdo |
|---|---|
| **Entity** | Nome e identidade, com seletor de material. |
| **Transform** | Posição, rotação e escala no mesmo conjunto de linhas; valores limitados com arrasto e entrada por teclado. |
| **Component cards** | Um cartão colapsável por componente, com campos específicos e botão de remoção. |
| **Add Behaviour** | Abre o seletor de behaviours para os componentes expostos pelo motor. |

Campos de cor usam o color picker, números limitados usam sliders e campos
numéricos, e referências usam asset pickers com pesquisa. Todas as edições publicam
uma `Message`; nenhum widget chama o motor diretamente.

## Gizmos e marcadores de cena

O viewport sobrepõe dois componentes:

- **Gizmo de transform** — handles de move (`1`), rotate (`2`) e scale (`3`) para a
  entidade selecionada, com handles de plano no move e um handle central para escala
  uniforme. Cada arrasto é um passo de undo.
- **Marcadores de cena** — ícones e frusta para luzes, câmaras, colliders e empties,
  que não têm mesh para selecionar. Os marcadores ficam por baixo do gizmo na ordem
  de hit: handle do gizmo, depois marcador, depois picking da cena.

Veja [Gizmos e marcadores](../doppio/gizmos-and-markers.md)
para o modelo completo e capturas.

## Undo, redo e play mode

- Cada comando de edição chama `App::commit`, registando um passo de undo. `Ctrl+Z` e
  `Ctrl+Shift+Z` percorrem o histórico.
- **Scene → Play** (`Ctrl+Enter`) faz tick no motor. A barra de estado mostra o chip
  **Playing**; alterações de play mode ficam fora dos caminhos exclusivos do editor.
- **Scene → Save Scene** (`Ctrl+S`) escreve a cena `.caf` e atualiza o selo
  **Saved**.

## Paleta de prefabs

**Scene → Create Entity…** (`Ctrl+Shift+N`) abre uma paleta integrada: mesh, luzes
point, directional e spot, câmara, corpo físico, terreno, água, grupo vazio e
**Duplicate Selection**. A mesma paleta está no **+** da Hierarchy. Escolher uma
entrada adiciona uma entidade configurada; não é preciso plugin.

## Estados vazio e fixture

Uma cena nova não tem entidades. Sem sessão de motor (por exemplo numa fixture
headless), o viewport mostra **Waiting for the engine viewport…** enquanto o resto do
editor continua totalmente interativo. A fixture `scene3d` arranca uma cena com
luzes, câmara e meshes para testes visuais.

## Páginas relacionadas

- [Scene viewport](scene-viewport.md) — render, câmara e readback.
- [Galeria de UI](ui-gallery.md) — visita visual aos painéis.
- [Headless testing](../doppio/headless-testing.md)
  — automatizar o editor sem janela.
