# Galeria de UI do editor

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/captures/flows/capture-editor-docs.json"><code>capture-editor-docs.json</code></a></span>
</div>

<p class="doc-lede">Uma visita visual ao workspace Rust do Doppio, capturada fora do
ecrã pelo driver headless para que cada imagem corresponda à árvore de widgets atual.</p>

<figure class="doc-figure">
  <img src="../images/editor/project-manager.png" alt="Gestor de projetos do Doppio com os separadores Create New, Open Recent e Browse Projects" loading="lazy">
  <figcaption>O Project Manager abre antes de qualquer cena. Crie um projeto, reabra um recente ou procure numa pasta de projetos.</figcaption>
</figure>

## Arranque e gestor de projetos

O Doppio arranca no gestor de projetos quando não recebe uma cena na linha de comandos.
O diálogo tem três separadores:

| Separador | Função |
|---|---|
| **Create New** | Nome do projeto, local, template (Empty / 2D / 3D) e **Create &amp; Open**. |
| **Open Recent** | Projetos recentes com pesquisa e **Open Selected**. |
| **Browse Projects** | Procura `project.caffeine` numa pasta. |

A pasta padrão é `~/Documents/CaffeineProjects`; pode ser alterada com
`CAFFEINE_PROJECTS_DIR`. O manifesto é `project.caffeine`, e as pastas padrão são
criadas na hora.

## Workspace padrão

<figure class="doc-figure">
  <img src="../images/editor/workspace-scene.png" alt="Workspace padrão do Doppio com Hierarchy, Viewport, Inspector e os painéis Assets e Console" loading="lazy">
  <figcaption>O layout padrão com uma cena do motor. A barra superior tem os menus e o estado do projeto/cena; a doca inferior tem Assets e Console.</figcaption>
</figure>

<video class="doc-video" autoplay loop muted playsinline width="960"
       poster="../images/editor/workspace-scene.png">
  <source src="../images/editor/doppio-tour.mp4" type="video/mp4">
  <a href="../images/editor/doppio-tour.gif">Ver a visita ao workspace (GIF)</a>
</video>

<p class="doc-caption">O mesmo flow de captura pode gravar movimento: os menus abrem, uma linha da hierarchy é selecionada, e o ffmpeg codifica o resultado em MP4.</p>

O workspace é uma única janela Iced dividida em quatro regiões encaixadas:

- **Hierarchy** à esquerda.
- **Viewport** e ferramentas de conteúdo ao centro.
- **Inspector** e geradores de assets à direita.
- **Assets + Console** na doca inferior.

Os separadores podem ser arrastados entre painéis; o guia de docking mostra o centro e
as arestas. Os botões maximizam e restauram. Os presets são `Ctrl+1` (Default) e
`Ctrl+2` (Viewport).

## Painéis

<figure class="doc-figure">
  <img src="../images/editor/pane-hierarchy.png" alt="Painel Hierarchy com árvore de cena, campo de pesquisa e botão de adicionar" loading="lazy">
  <figcaption>Hierarchy: pesquisa, árvore com grupos pai, seleção e botão de adicionar. Arraste uma linha para outra para reparentar.</figcaption>
</figure>

<figure class="doc-figure">
  <img src="../images/editor/pane-inspector.png" alt="Painel Inspector com nome da entidade, campos de transform, cartões de componentes e Add Behaviour" loading="lazy">
  <figcaption>Inspector: nome, transform combinada, cartões de componentes colapsáveis e o seletor Add Behaviour.</figcaption>
</figure>

<figure class="doc-figure">
  <img src="../images/editor/pane-assets.png" alt="Painel Assets com árvore de pastas, breadcrumb, botões New e Import e grelha de assets" loading="lazy">
  <figcaption>Assets: árvore de pastas, breadcrumb, pesquisa, modos grelha/lista e o wizard New/Import.</figcaption>
</figure>

<figure class="doc-figure">
  <img src="../images/editor/pane-console.png" alt="Painel Console com entradas de log tipadas e filtráveis" loading="lazy">
  <figcaption>Console: filtros Errors, Log, Actions, Engine e UI, com a entrada mais recente no fundo.</figcaption>
</figure>

## Menus

<figure class="doc-figure">
  <img src="../images/editor/menu-scene.png" alt="Menu Scene aberto com Add Entity, Create Entity, New Material, geradores, Save Scene e Play" loading="lazy">
  <figcaption>Menu Scene: entidades, gerador de materiais, painéis de script e Dryad, gravar e play.</figcaption>
</figure>

<figure class="doc-figure">
  <img src="../images/editor/menu-view.png" alt="Menu View aberto com geradores, comandos de câmara, marcadores, grelha, gizmos e layouts" loading="lazy">
  <figcaption>Menu View: geradores, focar/repor câmara, render now, marcadores, grelha, modos de gizmo e presets de layout.</figcaption>
</figure>

Os menus são overlays flutuantes. Passar o rato sobre um widget por trás de um menu
aberto não o fecha; clique fora, prima `Escape` ou escolha um item.

## Ferramentas de conteúdo

### Material Generator

<figure class="doc-figure">
  <img src="../images/editor/material-generator.png" alt="Material Generator com grafo de nós, pré-visualização e controlos de channel packing" loading="lazy">
  <figcaption>O Material Generator: paleta de nós, canvas do grafo, pré-visualização ao vivo, canais e packing ORM. Bake to Material escreve os mapas no <code>.mat</code> aberto.</figcaption>
</figure>

### Texture Generator

<figure class="doc-figure">
  <img src="../images/editor/texture-generator.png" alt="Texture Generator com grafo de nós, pré-visualização e controlos de exportação" loading="lazy">
  <figcaption>O Texture Generator usa o mesmo node canvas com operações de textura, presets, exportação e flipbooks.</figcaption>
</figure>

### Nature, Water e Terrain

<figure class="doc-figure">
  <img src="../images/editor/nature-generator.png" alt="Nature Generator com grafo de nós e plantas geradas" loading="lazy">
  <figcaption>Nature Generator: rochas, árvores e plantas a partir de um grafo, com modos de qualidade e exportação OBJ.</figcaption>
</figure>

<figure class="doc-figure">
  <img src="../images/editor/water-generator.png" alt="Water Generator com grafo de ondas e pré-visualização da água" loading="lazy">
  <figcaption>Water Generator: fontes de onda, modificadores, controlos de aspeto e presets.</figcaption>
</figure>

<figure class="doc-figure">
  <img src="../images/editor/terrain-generator.png" alt="Terrain Generator com grafo de campos, camadas splat e pré-visualização 3D" loading="lazy">
  <figcaption>Terrain Generator: fontes de campo, modificadores, máscaras e erosão, com pré-visualização splat e Place in Scene.</figcaption>
</figure>

## Reconstruir esta galeria

As imagens vêm de um flow headless comprometido:

```bash
./scripts/capture-editor-docs.sh   # PNGs
./scripts/capture-editor-tour.sh   # MP4 + GIF
```

Escreve nomes estáveis em `content/en/docs/images/doppio/editor/`. Copie os ficheiros para
`content/{en,pt}/docs/images/editor/` depois de regenerar. Não edite os PNGs à mão.
