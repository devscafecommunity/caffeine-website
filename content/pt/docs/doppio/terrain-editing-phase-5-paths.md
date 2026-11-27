# Edição de terreno: relatório da Fase 5.2 (estradas e rios)

<div class="doc-meta">
  <span class="doc-badge doc-badge--beta">Em andamento</span>
  <span class="doc-badge">Doppio</span>
  <span>Última atualização: <time datetime="2026-11-27">2026-11-27</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/content/pt/docs/doppio/terrain-editing-phase-5-paths.md"><code>terrain-editing-phase-5-paths.md</code></a></span>
</div>

<p class="doc-lede">Uma estrada ou um rio desenhado como spline sobre um terreno. O motor nivela o chão ao longo do caminho, pinta uma camada da paleta e escreve uma máscara guardada de por onde passa, num só passo de undo. A aba Terrain Path desenha-o no viewport e mostra o corte e o aterro antes de mudar seja o que for.</p>

## 1. O que entrega

<table>
  <thead><tr><th>Peça</th><th>Onde</th><th>O que faz</th></tr></thead>
  <tbody>
    <tr><td>Spline</td><td><code>terrain/spline/TerrainSpline.*</code></td><td>Um caminho Catmull-Rom por até 256 pontos. Uma estrada nivela o chão a um perfil tirado ao longo do caminho, com média numa janela e limitado a uma inclinação máxima, por isso corta e aterra colinas. Um rio abre um canal de leito arredondado que nunca sobe da nascente ao fim. Ambos se fundem ao chão numa berma.</td></tr>
    <tr><td>Superfície</td><td>camada e máscara</td><td>Uma camada da paleta é pintada no corredor (a pintura em camadas tem de estar ligada) e uma máscara guardada é criada se faltar e posta a 1 no corredor, caindo a 0 na berma. Uma regra de espécie sobre essa máscara mantém as plantas fora da estrada.</td></tr>
    <tr><td>Undo</td><td>registo do traço</td><td>Um registo para chão, camada e máscara juntos; funciona com as chamadas de reverter e refazer o traço.</td></tr>
    <tr><td>C ABI 34</td><td><code>capi/EngineAPI.*</code></td><td><code>caffeine_session_terrain_spline_apply</code> e <code>caffeine_session_terrain_spline_sample</code> (a pré-visualização, que não muda nada).</td></tr>
    <tr><td>Aba Terrain Path</td><td><code>uikit/panels/terrain_path.rs</code>, <code>windows/main/terrainpath.rs</code></td><td>A ferramenta de desenho, tipo e presets, a lista de pontos, um perfil de elevação e os cards Shape e Surface.</td></tr>
    <tr><td>Overlay do viewport</td><td><code>uikit/components/path_overlay.rs</code></td><td>Uma fita translúcida, as duas bordas, uma linha central tracejada, handles numerados e uma perna fantasma até ao cursor.</td></tr>
  </tbody>
</table>

## 2. Desenhar

<table>
  <thead><tr><th>Gesto</th><th>Efeito</th></tr></thead>
  <tbody>
    <tr><td>Clique esquerdo no chão</td><td>Larga um ponto de controlo (a altura é achada no terreno)</td></tr>
    <tr><td>Arrastar um handle</td><td>Move-o; a câmara não orbita</td></tr>
    <tr><td>Clique direito num handle</td><td>Remove-o</td></tr>
    <tr><td><kbd>Backspace</kbd></td><td>Remove o último ponto</td></tr>
    <tr><td><kbd>Enter</kbd></td><td>Aplica o caminho (com dois ou mais pontos)</td></tr>
    <tr><td><kbd>Esc</kbd></td><td>Recomeça</td></tr>
  </tbody>
</table>

Cada clique pede uma pré-visualização ao motor, por isso a fita, o perfil de elevação (chão contra caminho) e o comprimento, corte, aterro e inclinação máxima (ou a queda de um rio) acompanham o rato. Só Apply muda o terreno.

## 3. Presets

<table>
  <thead><tr><th>Preset</th><th>Tipo</th><th>Largura</th><th>Berma</th><th>Fundo</th><th>Suavização</th><th>Inclinação</th><th>Máscara</th></tr></thead>
  <tbody>
    <tr><td>Footpath</td><td>Road</td><td>1,5 m</td><td>1,5 m</td><td>-</td><td>8 m</td><td>30%</td><td>path</td></tr>
    <tr><td>Dirt road</td><td>Road</td><td>4,5 m</td><td>3 m</td><td>-</td><td>25 m</td><td>15%</td><td>road</td></tr>
    <tr><td>Highway</td><td>Road</td><td>12 m</td><td>6 m</td><td>-</td><td>80 m</td><td>6%</td><td>road</td></tr>
    <tr><td>Creek</td><td>River</td><td>3 m</td><td>3 m</td><td>0,8 m</td><td>12 m</td><td>-</td><td>river</td></tr>
    <tr><td>River</td><td>River</td><td>12 m</td><td>8 m</td><td>2,5 m</td><td>40 m</td><td>-</td><td>river</td></tr>
  </tbody>
</table>

Arrastar qualquer número volta o preset a personalizado. Um ponto pode ter a sua própria largura, que substitui a do caminho nesse sítio.

## 4. C ABI 34

<code>CAFFEINE_CAPI_VERSION</code> é 34. Os pontos estão no espaço do mundo, em metros, e a altura é ignorada. Uma chamada que não pode ser aplicada devolve <code>INVALID_ARGUMENT</code> com o motivo e não muda nada: menos de dois pontos, nenhum no terreno, um número inválido, um nome de máscara embutida, uma camada em falta ou a pintura em camadas desligada.

```c
CaffeineSplineDesc desc = {0};
desc.kind = CAFFEINE_SPLINE_ROAD;
desc.width_m = 4.5f; desc.shoulder_m = 3.0f; desc.smooth_m = 25.0f; desc.max_grade = 0.15f;
desc.layer = -1;
strcpy(desc.mask, "road");
CaffeineSplinePoint pts[2] = {{-40, 0, 0, 0}, {40, 0, 10, 0}};
caffeine_session_terrain_spline_apply(session, terrain, &desc, pts, 2, &record, &length, error, sizeof error);
```

## 5. Ações de agente

<code>show_terrain_path</code>, <code>terrain_path_active</code>, <code>terrain_path_kind</code>, <code>terrain_path_preset</code>, <code>terrain_path_set</code>, <code>terrain_path_add_point</code>, <code>terrain_path_move_point</code>, <code>terrain_path_select_point</code>, <code>terrain_path_remove_point</code>, <code>terrain_path_reverse</code>, <code>terrain_path_clear</code> e <code>terrain_path_apply</code>. A consulta <code>terrain_path</code> devolve as definições, os pontos, a pré-visualização do motor e o perfil.

## 6. Verificação

- C++: <code>tests/test_terrain_spline.cpp</code> (4 casos: uma estrada nivelada e com inclinação limitada com o chão longe dela intacto, camada e máscara com undo exato, um leito de rio que nunca sobe a jusante, e pedidos inválidos que não mudam nada).
- Rust: testes de harness da aba (a ferramenta tira o botão esquerdo às outras, cliques pré-visualizam o caminho, arrastar e remover handles, Backspace, Esc e inverter, Apply e Enter como um passo de undo, um rio com camada e máscara, erros, e um agente a desenhar com posições do mundo) e um flow headless, <code>terrain-path-panel.json</code>.

## 7. Limites conhecidos e o que vem a seguir

- As fixtures headless não têm entidade de terreno, por isso o flow cobre a aba (tipos, presets, ferramenta, mensagens) e não o desenho no viewport; clicar, arrastar e aplicar estão cobertos pelos testes da app.
- Um rio só abre um canal: ainda não há superfície de água.
- A seguir na Fase 5: pressão de tablet e presets, pincéis em GPU, GI regional pré-compilado.
