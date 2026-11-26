# Testes de UI headless para o Doppio (`doppio-headless`)

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Estável</span>
  <span class="doc-badge">Doppio</span>
  <span class="doc-badge">Ferramentas</span>
  <span>Última verificação: <time datetime="2026-11-20">2026-11-20</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/doppio/crates/ui/src/windows/main/headless/"><code>windows/main/headless/</code></a></span>
</div>

<p class="doc-lede">Controle a interface real do editor Doppio sem abrir uma janela: clique,
arraste, escreva, prima atalhos, leia o ecrã, tire capturas de ecrã e grave GIF ou
MP4. Um só binário, um só protocolo JSON, sem SDK.</p>

<video class="doc-video" autoplay loop muted playsinline width="960"
       poster="../images/doppio/editor/workspace-scene.png">
  <source src="../images/doppio/editor/doppio-tour.mp4" type="video/mp4">
  <a href="../images/doppio/editor/doppio-tour.gif">Ver a interação (GIF)</a>
</video>

<p class="doc-caption">Gravado pelo próprio <code>doppio-headless</code>: abrir os menus
Scene e View e depois selecionar uma linha da hierarquia. O mesmo script pode produzir um GIF, MP4
ou WebM para um guia ou um pull request.</p>

Concebido para que *qualquer* agente, modelo, job de CI ou pessoa o possa usar da mesma forma; não
há servidor MCP, SDK nem cliente especial para instalar.

## Porque existe

| Princípio | O que significa |
|---|---|
| **Headless** | Nada se abre. As capturas são renderizadas fora do ecrã (GPU ou CPU). Os agentes nunca precisam de olhar para um ambiente de trabalho real, o que também evita capturar janelas alheias. |
| **Semelhante a um humano** | As ações do ponteiro deslizam em pequenos passos, descansam um frame sobre o alvo, premem, mantêm e largam. A escrita é feita tecla a tecla. Os atalhos seguem o mesmo caminho que na aplicação real. Hover, foco, arrastos e duplos cliques comportam-se como se fossem feitos por uma mão humana. |
| **Agnóstico** | Um só binário, um só protocolo JSON, `stdin`/`stdout`/códigos de saída. Funciona a partir de uma shell, de um script, de CI, Cursor, Claude Code, Codex, um simples ciclo `bash`… |
| **Padronizado** | Um só vocabulário de ações, uma só sintaxe de alvos, uma só forma de resultado, um só sítio que os define (`reference.rs`), a partir do qual são geradas a validação, o JSON Schema e esta referência. |
| **Verificável** | As asserções `expect`, os snapshots JSON de `state`, as capturas anotadas e a comparação com baselines transformam "parece certo" num resultado de passa/falha. |

## Início rápido

```bash
# 1. See what is on screen (ids you can target):
./scripts/doppio-headless.sh widgets --size 1440x800

# 2. Run a flow and read the report:
./scripts/doppio-headless.sh run doppio/tests/ui-flows/menus-and-hover.json --format text

# 3. Take an annotated screenshot (every catalogued widget numbered + legend):
./scripts/doppio-headless.sh screenshot --annotate --name home --out /tmp/shots
```

`scripts/doppio-headless.sh` é um invólucro fino em torno de
`cargo run -p doppio-ui --features headless --bin doppio-headless --`. Todos os
argumentos são reencaminhados, pelo que tudo o que se segue também funciona com a forma
`cargo run` direta ou com o binário compilado em
`doppio/target/<profile>/doppio-headless`.

Script mínimo:

```json
{
  "name": "open the Scene menu and close it",
  "fixture": "entities",
  "size": [1280, 720],
  "steps": [
    { "action": "click", "target": "id:editor.menu.scene" },
    { "action": "expect", "state": { "/menu": "Scene" }, "exists": "text:Add Entity" },
    { "action": "screenshot", "name": "scene-menu", "annotate": true },
    { "action": "key", "key": "Escape" },
    { "action": "expect", "state": { "/menu": null } }
  ]
}
```

## Como funciona

O driver possui uma `App` real (o mesmo estado, `update` e `view` que o editor
executa) mais um renderizador headless, e repete o ciclo de frames da aplicação real:

1. o evento percorre a árvore de widgets (`UserInterface::update`), com a
   **árvore de estado dos widgets mantida entre passos** (o foco, os desvios de scroll e os arrastos
   de canvas sobrevivem de um passo para o seguinte);
2. as mensagens publicadas pelos widgets são aplicadas com `App::update`;
3. os eventos que nenhum widget capturou passam também pelo **mesmo mapeamento que as
   subscrições reais usam** (`keyboard_event_message`, `global_event_message`: atalhos,
   teclas de voo, largar o ponteiro, largar ficheiros);
4. cada passo termina com frames inativos (um redraw mais o `ViewportTick` de 16 ms),
   e a vista é reconstruída a partir do novo estado antes do evento seguinte.

### O que é e não é simulado

* ✅ Widgets, layout, hover/press/focus, arrastos, duplos cliques, roda do rato,
  teclado, introdução de texto, atalhos, largar ficheiros, redimensionamento e o tick da aplicação reais.
* ✅ Menus, diálogos, assistente, guias de docking, separadores, árvores, scrollables, canvases.
* ⚠️ **Fixtures, não um motor.** A sessão começa a partir de uma fixture
  (`entities` ou `empty`) sem `libcaffeine-capi`, pelo que a viewport 3D mostra
  "Waiting for the engine viewport…". Tudo o que pertence ao chrome do editor é real.
  Use as opções `assets` / `asset_root` / `components` para dar ao painel Assets,
  ao assistente de assets e ao seletor Add Behaviour algo com que trabalhar.
* ⚠️ Os tipos de letra são os *Fira Sans* incluídos, por isso os píxeis diferem de um ambiente de trabalho
  com outros tipos de letra do sistema. As baselines só são, por isso, válidas para execuções headless.
* ❌ Diálogos nativos do SO, área de transferência de outras aplicações, várias janelas.

## Linha de comandos

```text
doppio-headless run <script.json|dir|->...   run scripts, print the report (JSON)
doppio-headless session                      JSON step per line in, result per line out
doppio-headless widgets                      list widgets of the first frame
doppio-headless screenshot                   render the starting fixture
doppio-headless catalog | actions | schema | docs
```

Opções (`run`, `session`, `widgets`, `screenshot`):

| Opção | Significado | Predefinição |
|---|---|---|
| `--out <dir>` | Onde são escritas as capturas/artefactos | `doppio-headless-out` |
| `--size <WxH>` | Tamanho da janela, em píxeis lógicos | `1600x900` |
| `--fixture <name>` | `entities`, `empty` ou `material` (novo material, separador Generator aberto) | `entities` |
| `--asset-root <dir\|temp>` | Pasta onde o assistente de assets escreve (`temp` = pasta temporária apagada à saída) | nenhuma |
| `--baselines <dir>` | Imagens de baseline para `screenshot.baseline` | nenhuma |
| `--update-baselines` | Cria/atualiza as baselines em vez de falhar | desativado |
| `--format json\|text` | Formato do relatório de `run` | `json` |
| `--name`, `--annotate` | Apenas o comando `screenshot` | `shot`, desativado |

Os campos `fixture`, `size`, `assets` e `asset_root` de um script sobrepõem-se às
opções (que são valores predefinidos). Passar uma **pasta** a `run` executa todos os
`*.json` nela, cada um com a sua própria subpasta de artefactos.

**Códigos de saída:** `0` tudo passou · `1` um passo ou asserção falhou ·
`2` erro de utilização, ficheiro ilegível ou JSON de script inválido.
**Streams:** os relatórios vão para stdout, os diagnósticos para stderr.

`ICED_TEST_BACKEND=tiny-skia` força o renderizador por CPU (CI sem GPU).

### Auxiliares legíveis por máquina

* `doppio-headless actions` — a referência de ações em JSON.
* `doppio-headless schema` — JSON Schema (draft-07) de um script; aponte um
  editor ou validador para ele.
* `doppio-headless catalog` — todos os ids de widgets catalogados com tipo e
  descrição (o mesmo catálogo que `uikit/id.rs` mantém para a UI).
* `doppio-headless docs` — a referência em Markdown no fim deste ficheiro.

## Scripts

Um script é um objeto JSON:

```json
{
  "name": "optional title",
  "description": "optional",
  "fixture": "entities",
  "size": [1440, 800],
  "assets": [{ "name": "rock.png", "path": "Textures/rock.png" },
             { "name": "Textures", "path": "Textures", "directory": true }],
  "asset_root": "temp",
  "components": [{ "name": "Mesh Renderer", "fields": ["Mesh", "Material"] }],
  "preset": "Red Brick",
  "steps": [ { "action": "…" } ]
}
```

Cada passo é um objeto com uma `action` e os seus parâmetros, mais os campos comuns
`label` (texto livre devolvido no resultado) e `continue_on_error`.
Ações ou parâmetros desconhecidos são **rejeitados com a lista dos válidos**
(`unknown parameter "tagret" for "click"; expected: target, …`), para que os erros de escrita nunca
passem em silêncio. Por predefinição, um script pára no primeiro passo que falhe.

### Alvos

Um alvo indica *sobre o que atuar*:

| Forma | Exemplo | Notas |
|---|---|---|
| `id:<ui id>` | `id:editor.menu.scene` | **Preferida.** Ids estáveis e hierárquicos do catálogo da UI. |
| `text:<text>` | `text:Add Entity` | Etiqueta visível ou valor de um campo de texto; primeiro a correspondência exata, depois "contém". |
| `point:<x>,<y>` | `point:640,360` | Coordenadas da janela em píxeis lógicos. |
| objeto | `{ "id": "…" }`, `{ "text": "…" }`, `{ "point": [x, y] }` | O mesmo em JSON. |

Uma string simples é aceite como atalho (`"assets.wizard"` é um id,
`"Create"` é texto), mas os prefixos são a forma canónica — use-os nos flows versionados.
`nth` (a partir de 0) escolhe entre várias correspondências e `offset: [dx, dy]` desloca o
ponto de clique a partir do centro do widget.

Os ids dinâmicos seguem o padrão da sua entrada no catálogo:
`hierarchy.list.entity_row.<n>`, `assets.grid.asset_card.<n>`,
`editor.pane.tab.<page>`, `editor.pane.maximize.<Pane(n)>` (os ids dos painéis aparecem em
`state`)…

### Resultados

Cada passo produz:

```json
{
  "index": 3, "action": "click", "label": "open the wizard",
  "ok": true, "elapsed_ms": 45, "frame": 12,
  "data": { "point": [234.25, 548.3], "messages": ["Wizard(Open(Create))"] },
  "error": null, "hint": null
}
```

* `data` é específico de cada ação (ver a referência). As ações de ponteiro/teclado listam
  as `messages` que causaram — a forma mais rápida de ver *porque* algo aconteceu ou
  não aconteceu.
* Em caso de falha, `error` diz o que correu mal e `hint` sugere a correção
  (`did you mean id:editor.menu.scene?`, `the widget is clipped: maximise the pane`).

`run` envolve os passos em `{ "protocol", "script", "ok", "passed", "failed",
"out_dir", "artifacts", "steps" }`. `--format text` imprime o mesmo como um breve
resumo legível.

## Simulação humana, em detalhe

| Ação | O que é produzido |
|---|---|
| `move` | o cursor move-se da posição anterior em incrementos de `steps` (6) e depois um frame inativo. O primeiro movimento entra na janela a partir de ligeiramente fora do alvo. |
| `click` | modificadores premidos → deslizar → frame inativo (a mão descansa) → premir → largar → frame inativo. Dois cliques *separados* no mesmo sítio distam ≥ 330 ms para nunca contarem como um duplo clique acidental; `count: 2` / `double_click` produzem um verdadeiro. |
| `drag` | desliza até `from`, prime, `steps` (8) amostras do ponteiro com um frame inativo entre cada uma (para que canvases/overlays se redesenhem como num arrasto real), larga. `hold: true` mantém o botão premido; termine com `mouse_up`. |
| `scroll` | desliza e depois um evento de roda em linhas. |
| `type` | clique opcional em `target` para lhe dar foco, depois **uma tecla de cada vez** (premir/largar por carácter, aplicação atualizada entre teclas). |
| `key` | modificadores → tecla premida → tecla largada. Os atalhos (`ctrl+z`, `ctrl+shift+n`, `Escape`, `F5`, `g`, `1`…) chegam à aplicação pelo mesmo mapeamento de subscrições que na aplicação real. |
| `key_down` / `key_up` | mantêm teclas premidas, como `w` (câmara de voo) ou `shift` (aceleração). |
| `wait` | frames inativos (`frames`) ou milissegundos simulados (`ms`, 16 ms/frame). `real_time: true` também espera de facto (para tarefas em segundo plano como `caf-pack`). |
| `file_drop` | um evento de largar ficheiro do SO. |

Como a árvore de estado dos widgets persiste, um campo de texto mantém o foco entre
passos, os desvios de scroll ficam onde os deixou e um canvas mantém o seu estado de
arrasto — exatamente o que um agente precisa para interações com vários passos.

## Descobrir a UI (leia isto, agentes)

Nunca tem de adivinhar ids. Por ordem de preferência:

1. **`widgets`** — o que está no ecrã *agora*:
   `{ "action": "widgets", "prefix": "assets." }` →
   `[{ "id": "assets.toolbar.new", "kind": "container", "bounds": [x,y,w,h], "text": null }, …]`.
   Acrescente `"with_text": true` para ver também as etiquetas anónimas para alvos `text:`.
2. **`find`** — este alvo existe, onde está e está visível?
3. **`state`** — o estado da aplicação em JSON (ver abaixo). Mais barato do que uma captura de ecrã.
4. **`screenshot` com `annotate: true`** — caixas numeradas e uma legenda de
   `id — descrição` para cada widget catalogado; olhe para a imagem uma vez,
   depois atue por id.
5. **`catalog`** — a lista completa de ids catalogados (não depende do que está aberto).

Se um id não aparece, a coisa provavelmente não está aberta: clique no separador,
abra primeiro o menu ou o assistente, ou use `resize` na janela se estiver cortada.

### O snapshot de `state`

| Chave | Conteúdo |
|---|---|
| `panes[]` | `{ id, pages[], active, maximized }` para cada painel (os ids de painel como `Pane(3)` correspondem a `editor.pane.maximize.Pane(3)`) |
| `entities[]`, `selected`, `selected_index` | entidades da cena (id, nome, posição, rotação, escala, pai) e seleção |
| `menu`, `hierarchy_menu` | nome do menu aberto / linha do menu de contexto |
| `tab_drag`, `dock_hover` | arrasto de separador em curso (`dragging` é true quando o separador saiu do seu cabeçalho) e a guia de docking sob o cursor |
| `assets` | `directory`, `count`, `selected`, `search`, `view_mode`, `tree_open`, `tree_collapsed` |
| `wizard` | `open`, `tab`, `template`, `name`, `sources`, `packing`, `status { text, ok }` |
| `project`, `material`, `texture_set`, `script`, `viewport` | o que está aberto em cada editor |
| `console` | `count` e as `last` 10 entradas `{ level, text }` |
| `window`, `pointer`, `frame` | tamanho da janela, posição do ponteiro, frames executados |

Use JSON pointers: `{ "action": "state", "path": "/assets/directory" }`.

## Asserções

```json
{ "action": "expect",
  "exists": ["id:assets.wizard", "text:Create"],
  "missing": "id:assets.toolbar.nope",
  "visible": "id:editor.pane.tab.console",
  "shows": "Waiting for the engine viewport…",
  "text": { "target": "id:inspector.entity.name", "equals": "Entity 1" },
  "state": { "/wizard/open": true, "/assets/tree_collapsed": { "contains": "Textures" } },
  "count": { "prefix": "assets.grid.asset_card.", "at_least": 3 } }
```

Todos os campos indicados têm de se verificar. Ponha um `label` nas asserções para que as falhas
se leiam bem no relatório.

## Capturas de ecrã

```json
{ "action": "screenshot", "name": "wizard", "target": "id:assets.wizard",
  "annotate": ["id:assets.wizard.create.name", "id:assets.wizard.create.confirm"],
  "scale": 2, "baseline": "wizard-create" }
```

* Os ficheiros são `<out>/<NNN>-<name>.png` (NNN conta para cima para que nada seja sobrescrito);
  o resultado dá `path`, `width`, `height` e um `hash` do conteúdo.
* `target` recorta para um widget (+ `padding`); `scale` aumenta a densidade de píxeis.
* `annotate: true` numera todos os widgets *catalogados* (uma caixa por id, sem
  molduras do tamanho de painéis) e acrescenta a legenda `n. id — descrição`; ou passe uma
  lista de alvos para etiquetar exatamente esses.
* **Baselines**: com `--baselines <dir>`, `baseline` compara com
  `<dir>/<name>.png`. A primeira execução (ou `--update-baselines`) escreve-a; as diferenças
  posteriores acima de `tolerance` (fração de píxeis, predefinição 0.0005) fazem falhar o
  passo e guardam um `*.diff.png` com os píxeis diferentes a vermelho.

## Flows (testes de regressão)

Os flows são scripts versionados em `doppio/tests/ui-flows/*.json`. O teste Rust
`every_shipped_flow_passes` executa-os todos em cada `cargo test`, e
`scripts/check-rust-ui.sh` também. Para acrescentar um: copie um flow, altere os passos,
execute-o com `--format text` e faça commit. Os flows incluídos cobrem o assistente de assets, docking, bibliotecas de geradores, secções do inspetor, menus e hover, o gerador de texturas
e o snapping do gizmo (`gizmo-snapping.json`). Um bom flow

* nomeia o comportamento em `name`/`description` (e o bug que protege, se existir);
* parte de uma fixture e só usa ids/textos que um utilizador possa ver;
* verifica com `expect` após cada ação significativa (e não apenas no fim);
* mantém as capturas como *artefactos* (não como baselines), a menos que o aspeto visual seja o ponto.

## Receitas para agentes

**Verificar uma alteração de UI que acabou de fazer**

```bash
./scripts/doppio-headless.sh run doppio/tests/ui-flows --format text      # all flows
./scripts/doppio-headless.sh screenshot --annotate --name after --out /tmp/after
```

Depois leia `/tmp/after/001-after.png`.

**Reproduzir um bug como o faria um utilizador**: escreva os cliques como um script, execute-o com
`--format text` e leia as `messages` do passo que falha.

**Exploração interativa sem qualquer framework** — uma sessão persistente sobre
pipes (um passo JSON por linha, um resultado JSON por linha):

```bash
mkfifo /tmp/dh.in
./scripts/doppio-headless.sh session --out /tmp/dh < /tmp/dh.in &
exec 3>/tmp/dh.in
echo '{"action":"widgets","prefix":"editor.menu"}'        >&3
echo '{"action":"click","target":"id:editor.menu.scene"}' >&3
echo '{"action":"screenshot","name":"menu"}'              >&3
echo '{"action":"quit"}'                                  >&3
```

```python
import json, subprocess
p = subprocess.Popen(["scripts/doppio-headless.sh", "session"], text=True,
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE)
print(p.stdout.readline())                      # {"event":"ready",...}
def step(**s):
    p.stdin.write(json.dumps(s) + "\n"); p.stdin.flush()
    return json.loads(p.stdout.readline())
assert step(action="click", target="id:editor.menu.scene")["ok"]
print(step(action="state", path="/menu")["data"])   # "Scene"
```

## Capturas para a documentação

A documentação usa este driver em vez de capturas de ecrã do ambiente de trabalho. Os flows de captura estão em
`caffeine-website/captures/flows/capture-*.json`; os invólucros de shell apenas retiram o prefixo numérico
para que os nomes das imagens se mantenham estáveis:

```bash
./scripts/capture-editor-docs.sh    # workspace, panes, menus, generators
./scripts/capture-editor-tour.sh    # short MP4/GIF tour (ffmpeg for GIF)
./scripts/capture-material-docs.sh
./scripts/capture-nature-docs.sh
./scripts/capture-terrain-docs.sh
./scripts/capture-texture-docs.sh
./scripts/capture-water-docs.sh
./scripts/capture-gizmo-docs.sh
```

Um flow de captura é um flow normal mais passos `screenshot`:

```json
{ "action": "screenshot", "name": "pane-inspector",
  "target": "id:editor.pane.inspector", "padding": 4 }
```

Use `target` para recortar para um painel, `padding` para dar respiro, `scale: 2` para um detalhe
semelhante ao retina e `annotate` quando o objetivo for ensinar ids. Mantenha as capturas como artefactos,
não como baselines, a menos que o aspeto visual seja a regressão.

Para movimento, grave o próprio flow:

```json
{ "steps": [
  { "action": "record_start", "name": "tour", "format": "mp4", "fps": 12, "width": 960 },
  { "action": "click", "target": "id:editor.menu.scene" },
  { "action": "wait", "ms": 700, "real_time": true },
  { "action": "key", "key": "Escape" },
  { "action": "record_stop" }
] }
```

`format` aceita `gif`, `mp4` e `webm`. Um GIF é a alternativa mais portátil;
o MP4 é mais pequeno e nítido para páginas modernas. Use `width` para manter o ficheiro pequeno e
`keep_frames` apenas quando precisar dos PNG intermédios.

A referência da UI é gerada em separado:
`./scripts/generate-doppio-ui-docs.sh --publish` captura todos os widgets catalogados
a partir de `ui-captions.json`. Nunca edite `editor/ui-reference.md` à mão.

## Estender o driver

* **Nova ação**: acrescente o seu `ActionDoc` em `headless/reference.rs` (parâmetros,
  retorno, exemplo), trate-a em `Driver::execute`, adicione um teste em
  `headless/tests.rs` e depois atualize a referência deste ficheiro
  (`./scripts/doppio-headless.sh docs`, cole entre os marcadores — um teste
  falha se divergirem).
* **Nova chave de estado**: acrescente-a a `headless/state.rs` e à tabela acima.
* **Novo widget**: dê-lhe um `UiId` + entrada no catálogo (`uikit/id.rs`) como as
  regras do projeto exigem — isso torna-o automaticamente alvejável, listado por
  `widgets` e anotável.
* Mantenha o protocolo aditivo; incremente `PROTOCOL_VERSION` em alterações incompatíveis.

## Resolução de problemas

| Sintoma | Solução |
|---|---|
| `could not create a headless renderer` | `ICED_TEST_BACKEND=tiny-skia` |
| `no widget matches id:…` | leia o `hint`; execute `widgets`; abra o separador/menu/diálogo a que pertence |
| `the widget exists but is clipped` | `resize`, maximize o painel ou faça scroll do seu contentor |
| O clique não fez nada | leia `data.messages`; havia um modal/overlay por cima? O alvo é o contentor em vez do texto do botão? Experimente `text:` |
| Dois cliques tornaram-se um duplo clique | use um `click` por intenção; o driver já espaça cliques separados |
| Diferença na baseline só noutra máquina | os tipos de letra/AA diferem; aumente `tolerance` ou regenere as baselines aí |
| A escrita não vai parar a lado nenhum | passe `target` a `type` para que o campo receba primeiro o clique (foco) |

## Referência

### Gravar GIFs e vídeos (ffmpeg)

`record_start` / `record_stop` capturam a janela (ou um widget) enquanto um script corre e deixam o **ffmpeg**
codificar um **GIF, MP4 ou WebM**. É tirado um frame após cada passo que altere algo (para que um clique seja
visível) e a cada poucos frames durante um `wait`; com `real_time: true` a espera decorre a velocidade normal, pelo que
`{ "action": "wait", "ms": 2000, "real_time": true }` equivale a cerca de dois segundos de vídeo. `fps` é simultaneamente a taxa de captura
e de reprodução. O ffmpeg tem de estar no `PATH` (ou defina `FFMPEG` com o seu caminho); sem ele o passo falha
com uma sugestão e os frames são mantidos. Uma gravação deixada aberta no fim de um script é terminada automaticamente.

```json
{ "steps": [
  { "action": "record_start", "name": "orbit", "format": "mp4", "fps": 30, "target": "id:editor.pane.terrain_generator" },
  { "action": "click", "target": "id:terraingen.preset" },
  { "action": "wait", "ms": 2000, "real_time": true },
  { "action": "record_stop" }
] }
```

O resultado de `record_stop` indica `path`, `frames`, `seconds` e `bytes`. Use `width` para um ficheiro mais pequeno,
`scale` para uma captura mais nítida e `keep_frames` para manter os PNG.

As secções abaixo são geradas a partir de `headless/reference.rs`.

<!-- BEGIN GENERATED REFERENCE -->

### Ponteiro

#### `move`

Move o ponteiro para um alvo em vários passos pequenos (hover).

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `target` | `target` | sim | Sobre o que atuar: `id:<ui id>`, `text:<visible text>` ou `point:<x>,<y>` (ver Alvos). |
| `nth` | `int` | não | Índice a partir de 0 quando vários widgets correspondem ao alvo (predefinição 0). |
| `offset` | `[x, y]` | não | Píxeis lógicos somados ao centro do alvo, por exemplo para acertar num canto. |
| `steps` | `int` | não | Posições intermédias do ponteiro emitidas durante o movimento, como uma mão real (predefinição 6). |

Devolve: `{ "point": [x, y] }`

```json
{ "action": "move", "target": "id:editor.menu.scene" }
```
#### `click`

Move-se até ao alvo, prime e larga um botão do rato.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `target` | `target` | sim | Sobre o que atuar: `id:<ui id>`, `text:<visible text>` ou `point:<x>,<y>` (ver Alvos). |
| `nth` | `int` | não | Índice a partir de 0 quando vários widgets correspondem ao alvo (predefinição 0). |
| `offset` | `[x, y]` | não | Píxeis lógicos somados ao centro do alvo, por exemplo para acertar num canto. |
| `button` | `"left" \| "right" \| "middle"` | não | Botão do rato (predefinição left). |
| `modifiers` | `["ctrl" \| "shift" \| "alt" \| "cmd"]` | não | Teclas modificadoras mantidas durante a ação. |
| `count` | `int` | não | 1 = clique, 2 = duplo clique, 3 = triplo (predefinição 1). |
| `steps` | `int` | não | Posições intermédias do ponteiro emitidas durante o movimento, como uma mão real (predefinição 6). |

Devolve: `{ "point": [x, y], "messages": ["…"] }`

```json
{ "action": "click", "target": "id:assets.toolbar.new" }
```
#### `double_click`

Atalho para `click` com `count: 2`.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `target` | `target` | sim | Sobre o que atuar: `id:<ui id>`, `text:<visible text>` ou `point:<x>,<y>` (ver Alvos). |
| `nth` | `int` | não | Índice a partir de 0 quando vários widgets correspondem ao alvo (predefinição 0). |
| `offset` | `[x, y]` | não | Píxeis lógicos somados ao centro do alvo, por exemplo para acertar num canto. |
| `button` | `"left" \| "right" \| "middle"` | não | Botão do rato (predefinição left). |
| `modifiers` | `["ctrl" \| "shift" \| "alt" \| "cmd"]` | não | Teclas modificadoras mantidas durante a ação. |
| `steps` | `int` | não | Posições intermédias do ponteiro emitidas durante o movimento, como uma mão real (predefinição 6). |

Devolve: como `click`

```json
{ "action": "double_click", "target": "text:Textures" }
```
#### `right_click`

Atalho para `click` com `button: "right"` (menus de contexto).

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `target` | `target` | sim | Sobre o que atuar: `id:<ui id>`, `text:<visible text>` ou `point:<x>,<y>` (ver Alvos). |
| `nth` | `int` | não | Índice a partir de 0 quando vários widgets correspondem ao alvo (predefinição 0). |
| `offset` | `[x, y]` | não | Píxeis lógicos somados ao centro do alvo, por exemplo para acertar num canto. |
| `modifiers` | `["ctrl" \| "shift" \| "alt" \| "cmd"]` | não | Teclas modificadoras mantidas durante a ação. |
| `steps` | `int` | não | Posições intermédias do ponteiro emitidas durante o movimento, como uma mão real (predefinição 6). |

Devolve: como `click`

```json
{ "action": "right_click", "target": "id:hierarchy.list.entity_row.0" }
```
#### `drag`

Prime em `from`, move-se em pequenos passos e larga em `to` (ou segundo um deslocamento).

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `from` | `target` | sim | Onde o arrasto começa. |
| `to` | `target` | não | Onde o arrasto termina. É obrigatório um de `to` / `by`. |
| `by` | `[dx, dy]` | não | Distância relativa do arrasto em píxeis lógicos. |
| `button` | `"left" \| "right" \| "middle"` | não | Botão do rato (predefinição left). |
| `modifiers` | `["ctrl" \| "shift" \| "alt" \| "cmd"]` | não | Teclas modificadoras mantidas durante a ação. |
| `steps` | `int` | não | Posições intermédias do ponteiro emitidas durante o movimento, como uma mão real (predefinição 6). |
| `hold` | `bool` | não | Não largar no fim (terminar mais tarde com `mouse_up`). Predefinição false. |

Devolve: `{ "from": [x, y], "to": [x, y], "messages": ["…"] }`

```json
{ "action": "drag", "from": "id:editor.pane.tab.console", "to": "point:900,300" }
```
#### `scroll`

Move-se até ao alvo e roda a roda do rato.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `target` | `target` | não | Onde atuar; omita para atuar na posição atual do ponteiro. |
| `dy` | `number` | não | Linhas da roda na vertical; positivo faz scroll para cima/aproxima (predefinição 0). |
| `dx` | `number` | não | Linhas da roda na horizontal (predefinição 0). |

Devolve: `{ "point": [x, y] }`

```json
{ "action": "scroll", "target": "id:editor.viewport.surface", "dy": 3 }
```
#### `mouse_down`

Baixo nível: prime um botão do rato na posição atual do ponteiro.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `button` | `"left" \| "right" \| "middle"` | não | Botão do rato (predefinição left). |

Devolve: `{}`

```json
{ "action": "mouse_down" }
```
#### `mouse_up`

Baixo nível: larga um botão do rato na posição atual do ponteiro.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `button` | `"left" \| "right" \| "middle"` | não | Botão do rato (predefinição left). |

Devolve: `{}`

```json
{ "action": "mouse_up" }
```

### Teclado

#### `type`

Escreve texto um carácter de cada vez. Com `target`, clica primeiro nele para lhe dar foco.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `text` | `string` | sim | Os caracteres a escrever. |
| `target` | `target` | não | Onde atuar; omita para atuar na posição atual do ponteiro. |
| `clear` | `bool` | não | Selecionar tudo (ctrl+a) e apagar antes de escrever. |

Devolve: `{ "messages": ["…"] }`

```json
{ "action": "type", "target": "id:assets.wizard.create.name", "text": "Props" }
```
#### `key`

Prime uma tecla ou combinação como `Enter`, `Escape`, `F5`, `ctrl+z`, `ctrl+shift+n`.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `key` | `string` | sim | Nome da tecla (enter, escape, tab, space, backspace, delete, up/down/left/right, home, end, pageup, pagedown, f1-f12, ou um carácter), opcionalmente precedido por `ctrl+`, `shift+`, `alt+`, `cmd+`. |

Devolve: `{ "messages": ["…"] }`

```json
{ "action": "key", "key": "ctrl+z" }
```
#### `key_down`

Prime uma tecla e mantém-na premida (teclas da câmara de voo, aceleração com shift). Largue com `key_up`.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `key` | `string` | sim | Mesma sintaxe que `key`. |

Devolve: `{}`

```json
{ "action": "key_down", "key": "w" }
```
#### `key_up`

Larga uma tecla mantida por `key_down`.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `key` | `string` | sim | Mesma sintaxe que `key`. |

Devolve: `{}`

```json
{ "action": "key_up", "key": "w" }
```

### Tempo

#### `wait`

Deixa a aplicação correr: entrega redraws e o tick de 16 ms da viewport.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `frames` | `int` | não | Número de frames a executar (predefinição 1). |
| `ms` | `int` | não | Alternativa a `frames`: milissegundos de tempo simulado (16 ms por frame). |
| `real_time` | `bool` | não | Também espera durante esse tempo (para tarefas em segundo plano como o caf-pack). Predefinição false. |

Devolve: `{ "frames": n }`

```json
{ "action": "wait", "ms": 200 }
```
#### `resize`

Redimensiona a janela virtual (píxeis lógicos).

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `size` | `[w, h]` | sim | Novo tamanho da janela. |

Devolve: `{ "size": [w, h] }`

```json
{ "action": "resize", "size": [1280, 720] }
```
#### `file_drop`

Larga um ficheiro do SO sobre a janela.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `path` | `string` | sim | Caminho absoluto do ficheiro ou pasta largado. |

Devolve: `{ "messages": ["…"] }`

```json
{ "action": "file_drop", "path": "/tmp/rock.png" }
```

### Consulta

#### `find`

Procura um alvo sem lhe tocar.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `target` | `target` | sim | Sobre o que atuar: `id:<ui id>`, `text:<visible text>` ou `point:<x>,<y>` (ver Alvos). |
| `nth` | `int` | não | Índice a partir de 0 quando vários widgets correspondem ao alvo (predefinição 0). |

Devolve: `{ "found": bool, "id": …, "kind": …, "bounds": [x,y,w,h], "visible_bounds": …, "text": …, "matches": n }`

```json
{ "action": "find", "target": "id:editor.pane.viewport" }
```
#### `widgets`

Lista os widgets do frame atual (descoberta: o que posso clicar?).

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `prefix` | `string` | não | Apenas ids que começam por isto (p. ex. `assets.`). |
| `kind` | `string` | não | Apenas este tipo: container, text, text_input, focusable, scrollable, custom. |
| `visible_only` | `bool` | não | Ignorar widgets que estão cortados (predefinição true). |
| `with_text` | `bool` | não | Incluir widgets de texto anónimos para poder usar `text:` como alvo (predefinição false). |

Devolve: `{ "count": n, "widgets": [{ "id", "kind", "bounds", "text" }] }`

```json
{ "action": "widgets", "prefix": "assets." }
```
#### `text`

Lê o texto de um widget de texto ou o valor de um campo de texto.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `target` | `target` | sim | Sobre o que atuar: `id:<ui id>`, `text:<visible text>` ou `point:<x>,<y>` (ver Alvos). |
| `nth` | `int` | não | Índice a partir de 0 quando vários widgets correspondem ao alvo (predefinição 0). |

Devolve: `{ "text": "…" }`

```json
{ "action": "text", "target": "id:inspector.entity.name" }
```
#### `state`

Devolve o estado da aplicação em JSON (painéis, seleção, menus, assistente, consola…).

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `path` | `string` | não | JSON pointer para o estado, p. ex. `/panes/0/pages`. Omita para obter tudo. |

Devolve: o estado (ou a parte selecionada)

```json
{ "action": "state", "path": "/menu" }
```
#### `log`

Devolve as últimas entradas da consola.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `last` | `int` | não | Quantas entradas (predefinição 10). |

Devolve: `{ "entries": [{ "level", "text" }] }`

```json
{ "action": "log", "last": 5 }
```

### Captura

#### `screenshot`

Renderiza a janela (ou um widget) para um PNG, opcionalmente anotado ou comparado com uma baseline.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `name` | `string` | não | Nome base do ficheiro (predefinição `shot`). Os ficheiros são `<out>/<NNN>-<name>.png`. |
| `target` | `target` | não | Recortar para este widget; omita para a janela inteira. |
| `padding` | `number` | não | Píxeis lógicos acrescentados em redor de um alvo recortado (predefinição 8). |
| `annotate` | `bool \| [target]` | não | Desenha caixas numeradas com uma legenda. `true` = todos os widgets visíveis que têm um id catalogado; ou uma lista de alvos. |
| `scale` | `number` | não | Densidade de píxeis (predefinição 1; use 2 para um detalhe semelhante ao retina). |
| `baseline` | `string` | não | Compara com `<baselines>/<baseline>.png`; uma diferença faz falhar o passo. Crie/atualize com `--update-baselines`. |
| `tolerance` | `number` | não | Fração permitida de píxeis diferentes (predefinição 0.0005). |

Devolve: `{ "path", "width", "height", "hash", "baseline": { "status", "diff_ratio" } }`

```json
{ "action": "screenshot", "name": "assets-wizard", "target": "id:assets.wizard", "annotate": true }
```
#### `record_start`

Começa a gravar a janela (ou um widget). Os frames são tirados após cada passo que altere algo e a cada poucos frames durante `wait`; `record_stop` transforma-os num GIF, MP4 ou WebM com o ffmpeg.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `name` | `string` | não | Nome base do ficheiro de resultado (predefinição `recording`): `<out>/<name>.<format>`. |
| `format` | `string` | não | `gif` (predefinição), `mp4` ou `webm`. |
| `fps` | `int` | não | Taxa de captura e de reprodução, 1-60 (predefinição 15). Um `wait` de 2000 ms com `real_time` equivale a cerca de dois segundos de vídeo. |
| `target` | `target` | não | Gravar apenas este widget; omita para a janela inteira. |
| `padding` | `number` | não | Píxeis lógicos em redor de um alvo (predefinição 8). |
| `scale` | `number` | não | Densidade de píxeis da captura, 0.25-3 (predefinição 1). |
| `width` | `int` | não | Largura de saída em píxeis (a altura mantém a proporção); omita para manter o tamanho capturado. |
| `keep_frames` | `bool` | não | Mantém os frames PNG (é devolvida a respetiva pasta) em vez de os apagar. |

Devolve: `{ "recording": true, "fps" }`

```json
{ "action": "record_start", "name": "orbit", "format": "mp4", "fps": 30, "target": "id:editor.pane.viewport" }
```
#### `record_stop`

Pára a gravação e codifica-a com o ffmpeg (a variável de ambiente FFMPEG substitui o caminho do programa). Uma gravação ainda aberta quando o script termina é finalizada automaticamente.

Devolve: `{ "path", "format", "frames", "fps", "seconds", "bytes" }`

```json
{ "action": "record_stop" }
```

### Asserção

#### `expect`

Verifica condições no frame/estado atual; todos os campos indicados têm de se verificar.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `exists` | `target \| [target]` | não | Estes alvos estão no ecrã. |
| `missing` | `target \| [target]` | não | Estes alvos não estão no ecrã. |
| `visible` | `target \| [target]` | não | Estes alvos existem e não estão cortados. |
| `shows` | `string \| [string]` | não | Estes textos exatos estão no ecrã. |
| `text` | `{ target, equals?, contains? }` | não | O texto de um widget é igual a / contém uma string. |
| `state` | `{ "/json/pointer": value }` | não | Valores no JSON de `state` (igualdade profunda). Use `{ "contains": … }` para arrays/strings. |
| `count` | `{ prefix, equals?, at_least? }` | não | Número de widgets visíveis cujo id começa por `prefix`. |

Devolve: `{ "checked": n }`

```json
{ "action": "expect", "exists": "id:assets.wizard", "state": { "/wizard/open": true } }
```

### Sessão

#### `reset`

Recomeça com uma aplicação nova (nova fixture, tamanho de janela e assets).

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `fixture` | `string` | não | `empty`, `entities`, `material`, `texture`, `scene3d` (uma cena com motor, com luzes, uma câmara e meshes; precisa de libcaffeine-capi) `nature` (o mesmo, preenchido com rochas, árvores e plantas geradas) `water` (o separador Water Generator em primeiro plano) `terrain` (o separador Terrain Generator em primeiro plano) `world` (o separador World Composer num projeto temporário: um terreno de colinas, duas receitas de rocha e `World/Valley.generator.world`; precisa de libcaffeine-capi) ou `world_showcase` (o mesmo separador em `World/Highlands.generator.world`: colinas à volta de um vale, um rio, um lago, carvalhos e pinheiros, rochedos, arbustos e erva; Build faz alguns milhares de instâncias, Frame aponta o Viewport para elas). Predefinição `entities`. |
| `size` | `[w, h]` | não | Tamanho da janela. |
| `assets` | `[{ name, path, kind, directory? }]` | não | Lista de assets mostrada no painel Assets. |
| `asset_root` | `string` | não | Pasta onde o assistente de assets escreve; `temp` cria uma pasta temporária. |
| `preset` | `string` | não | Preset de biblioteca aplicado ao Material Generator (fixture `material`, p. ex. `Red Brick`) ao Texture Generator (fixture `texture`, p. ex. `Torch Flame`) ao Nature Generator (fixture `nature`, p. ex. `Pine`) ao Water Generator (fixture `water`, p. ex. `Storm`) ou ao Terrain Generator (fixture `terrain`, p. ex. `Badlands`). |
| `components` | `[{ name, fields? }]` | não | Tipos de componente do motor que a fixture finge ter (para Add Behaviour). |

Devolve: `{ "asset_root": … }`

```json
{ "action": "reset", "fixture": "entities", "asset_root": "temp" }
```

<!-- END GENERATED REFERENCE -->
