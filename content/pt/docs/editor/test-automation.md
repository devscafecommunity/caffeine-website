# Automação de testes do editor

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="../doppio/headless-testing.md"><code>headless-testing.md</code></a></span>
</div>

<p class="doc-lede">O Doppio é testado conduzindo a árvore de widgets real fora do
ecrã: scripts JSON simples, input humano, asserções, capturas, baselines e gravações
GIF/MP4. Não existe um harness Python separado.</p>

<div class="doc-callout doc-callout--note">
  <p><strong>Nota.</strong> Revisões antigas desta página descreviam um bridge Python
  <code>editor_test_automation.py</code>. Esse harness já não existe. O caminho
  suportado é <code>doppio-headless</code> e os flows de UI comprometidos.</p>
</div>

## As três camadas

<table class="doc-table">
  <thead>
    <tr><th>Camada</th><th>Localização</th><th>Executa</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>Flow</strong></td><td><code>doppio/tests/ui-flows/*.json</code></td><td>Em cada <code>cargo test</code> através de <code>every_shipped_flow_passes</code> e de <code>scripts/check-rust-ui.sh</code>.</td></tr>
    <tr><td><strong>Driver</strong></td><td><code>doppio/crates/ui/src/windows/main/headless/</code></td><td>Ações, targets, snapshots de estado, capturas e gravação.</td></tr>
    <tr><td><strong>CLI</strong></td><td><code>scripts/doppio-headless.sh</code></td><td>Qualquer shell, job de CI ou agente; nenhuma janela abre.</td></tr>
  </tbody>
</table>

## Correr os flows

```bash
./scripts/doppio-headless.sh run doppio/tests/ui-flows --format text
```

Cada flow tem a sua pasta de artefactos. Um passo falhado imprime a ação, o target, as
mensagens produzidas e uma dica. Códigos de saída: `0` passou, `1` falha de passo ou
asserção, `2` erro de uso ou JSON inválido.

## Escrever um flow

```json
{
  "name": "Abrir o menu Scene e adicionar uma entidade",
  "description": "Protege o encaminhamento de teclado e menus para a ação de adicionar.",
  "fixture": "entities",
  "size": [1280, 720],
  "steps": [
    { "action": "click", "target": "id:editor.menu.scene" },
    { "action": "expect", "state": { "/menu": "Scene" }, "exists": "text:Add Entity" },
    { "action": "click", "target": "id:editor.add_entity" },
    { "action": "expect", "count": { "prefix": "hierarchy.list.entity_row.", "at_least": 3 } },
    { "action": "screenshot", "name": "after-add", "annotate": true }
  ]
}
```

Regras:

- Comece numa fixture (`entities`, `empty`, `material`, `texture`, `scene3d`,
  `nature`, `water`, `terrain`).
- Use ids do catálogo (`id:...`), não pontos, exceto quando o ponto é o comportamento
  em teste.
- Faça asserções após cada ação relevante; ponha um `label` nas asserções para que as
  falhas sejam legíveis.
- Guarde capturas como artefactos; use `baseline` só quando o visual é o objetivo.
- Nomeie o bug que o flow protege em `description`.

## Inspecionar a UI

```bash
./scripts/doppio-headless.sh widgets --size 1440x800
./scripts/doppio-headless.sh screenshot --annotate --name workspace --out /tmp/shots
```

`widgets` lista ids, tipos e bounds. `screenshot --annotate` numera todos os widgets
catalogados e acrescenta a legenda `n. id — descrição`. O mesmo catálogo alimenta a
[referência de UI](ui-reference.md).

## Capturar imagens para documentação

Os flows de captura comprometidos vivem em `captures/flows/capture-*.json`. Os
wrappers shell removem o prefixo numérico para os nomes das imagens ficarem estáveis:

```bash
./scripts/capture-material-docs.sh
./scripts/capture-nature-docs.sh
./scripts/capture-terrain-docs.sh
./scripts/capture-texture-docs.sh
./scripts/capture-water-docs.sh
./scripts/capture-gizmo-docs.sh
./scripts/capture-editor-tour.sh   # tour curto MP4/GIF
```

Um flow de captura é um flow normal mais passos `screenshot` com `target`, `padding`
e `scale`. Veja `captures/flows/capture-gizmo-docs.json` para o padrão scene3d.

## Gravar GIFs e vídeos

`record_start` / `record_stop` capturam a janela ou um widget e codificam com ffmpeg:

```json
{ "steps": [
  { "action": "record_start", "name": "dock", "format": "mp4", "fps": 30, "target": "id:editor.pane.viewport" },
  { "action": "drag", "from": "id:editor.pane.tab.console", "to": "point:900,300" },
  { "action": "wait", "ms": 1200, "real_time": true },
  { "action": "record_stop" }
] }
```

`format` aceita `gif`, `mp4` e `webm`; `width`, `scale`, `fps` e `keep_frames`
controlam a saída. Uma gravação deixada aberta no fim do script é finalizada
automaticamente.

## Regras de regressão

1. Uma correção ou feature visível acrescenta um flow em
   `doppio/tests/ui-flows/`.
2. O flow tem de passar em `cargo test` e em `scripts/check-rust-ui.sh`.
3. Widgets novos recebem um `UiId` e uma entrada em `CATALOG`; caso contrário não
   podem ser alvo, anotados ou documentados.
4. Alterações visuais regeneram as imagens do flow de captura afetado; não edite PNGs
   à mão.

## Páginas relacionadas

- [Referência de headless testing](../doppio/headless-testing.md)
  — todas as ações, formas de target, chaves de estado e opções de captura.
- [Referência de UI](ui-reference.md) — ids e legendas gerados.
- [Compilar](../getting-started/building.md) — binários de teste e feature flags.
