# Quick start

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">Crie um projeto, adicione uma entidade, grave uma cena e aprenda
os gestos do viewport em poucos minutos.</p>

<figure class="doc-figure">
  <img src="../images/editor/project-manager.png" alt="Gestor de projetos do Doppio antes de abrir um projeto" loading="lazy">
  <figcaption>O Doppio arranca no gestor de projetos. Crie um projeto, abra um recente ou procure numa pasta de projetos.</figcaption>
</figure>

## 1. Criar um projeto

Execute o Doppio sem argumentos:

```bash
cd doppio
cargo run -p doppio-ui
```

No gestor de projetos:

1. Abra **Create New**.
2. Introduza o nome e o local do projeto.
3. Escolha **Empty**, **2D** ou **3D**.
4. Prima **Create & Open**.

O Doppio escreve `project.caffeine` e cria `assets/raw`, `assets/processed`,
`scripts`, `scenes`, `materials`, `texture_sets` e `build`. O template 3D também
prepara as pastas de modelos, texturas, materiais, animações, áudio, prefabs e céu
em `assets/raw`.

## 2. Conhecer o workspace

<figure class="doc-figure">
  <img src="../images/editor/workspace-scene.png" alt="Workspace padrão do Doppio com hierarchy, viewport, inspector e os painéis de assets e console em baixo" loading="lazy">
  <figcaption>O layout padrão: Hierarchy à esquerda, Viewport e separadores de geradores ao centro, Inspector e materiais à direita, e Assets ao lado da Console na doca inferior.</figcaption>
</figure>

<table class="doc-table">
  <thead>
    <tr><th>Painel</th><th>Separadores</th><th>Função</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Hierarchy</strong></td>
      <td>Hierarchy</td>
      <td>Árvore da cena, pesquisa, adicionar/eliminar entidades e arrastar para reparentar.</td>
    </tr>
    <tr>
      <td rowspan="2"><strong>Centro</strong></td>
      <td>Viewport</td>
      <td>Render do motor, seleção, gizmos, marcadores de cena e voo da câmara.</td>
    </tr>
    <tr>
      <td>Material Generator · Texture Generator · Texture Set · Script · Dryad Nodes</td>
      <td>Ferramentas de conteúdo que partilham o painel central; arraste os separadores para outro painel.</td>
    </tr>
    <tr>
      <td rowspan="2"><strong>Direita</strong></td>
      <td>Inspector</td>
      <td>Nome da entidade, transform, cartões de componentes e <em>Add Behaviour</em>.</td>
    </tr>
    <tr>
      <td>Material · Nature · Water · Terrain</td>
      <td>Geradores de assets e procedurais com pré-visualização ao vivo.</td>
    </tr>
    <tr>
      <td><strong>Inferior</strong></td>
      <td>Assets · Console</td>
      <td>Navegador do projeto com import/pack, mais registos tipados e filtráveis.</td>
    </tr>
  </tbody>
</table>

Arraste um separador para fora do cabeçalho para o encaixar noutro painel. O guia de
docking mostra o centro e as arestas; os botões do painel maximizam ou restauram.
Os presets estão em **View → Default Layout** (`Ctrl+1`) e **View → Viewport
Layout** (`Ctrl+2`).

## 3. Adicionar uma entidade

1. Prima `Ctrl+N`, use **Scene → Add Entity** ou o **+** na Hierarchy.
2. Selecione a nova linha; o Inspector mostra o cartão **Transform**.
3. Abra **Scene → Create Entity…** (`Ctrl+Shift+N`) para a paleta de prefabs: mesh,
   luzes, câmara, física, terreno, água e duplicação da seleção.
4. Edite **Position**, **Rotation** e **Scale**, ou arraste o gizmo no viewport.

Os grupos pai compõem a transformação nos filhos; o gizmo projeta a posição
mundial resolvida.

## 4. Navegar no viewport

| Entrada | Ação |
|---|---|
| Arrastar no viewport | Orbitar a câmara |
| Arrastar com o botão direito ou do meio | Fazer pan da câmara |
| Roda do rato | Zoom |
| `W` `A` `S` `D` | Voar na horizontal |
| `Q` / `E` | Descer / subir |
| `Shift` | Boost de voo |
| `1` / `2` / `3` | Gizmo Move / Rotate / Scale |
| `G` | Alternar a grelha |
| `F` | Enquadrar a seleção (focus) |
| `Ctrl+0` | Repor a câmara |

O HUD do viewport mostra resolução, estado da grelha, modo do gizmo, modelo de vista,
FPS e overlay de iluminação. O render é offscreen e assíncrono, por isso a UI
continua responsiva enquanto o motor desenha.

## 5. Gravar a cena

Prima `Ctrl+S` ou use **Scene → Save Scene**. As cenas são ficheiros `.caf`; a barra
de título mostra o nome da cena e o selo **Saved**. As edições no inspector e na
hierarchy têm undo com `Ctrl+Z` e `Ctrl+Shift+Z`.

## Próximos passos

- [Galeria de UI do editor](../editor/ui-gallery.md) para uma visita visual a cada painel.
- [Scene viewport](../editor/scene-viewport.md) para render e câmara.
- [Headless testing](../doppio/headless-testing.md)
  para automatizar os mesmos passos sem janela.
