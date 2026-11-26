# Editor test automation

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="../doppio/headless-testing.md"><code>headless-testing.md</code></a></span>
</div>

<p class="doc-lede">Doppio is tested by driving the real widget tree off-screen:
plain JSON scripts, human-like input, assertions, screenshots, baselines and
GIF/MP4 recordings. There is no separate Python harness.</p>

<div class="doc-callout doc-callout--note">
  <p><strong>Note.</strong> Older revisions of this page described a Python
  <code>editor_test_automation.py</code> process bridge. That harness is gone. The
  supported path is <code>doppio-headless</code> and the committed UI flows.</p>
</div>

## The three layers

<table class="doc-table">
  <thead>
    <tr><th>Layer</th><th>Location</th><th>Runs</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>Flow</strong></td><td><code>doppio/tests/ui-flows/*.json</code></td><td>Every <code>cargo test</code> through <code>every_shipped_flow_passes</code> and through <code>scripts/check-rust-ui.sh</code>.</td></tr>
    <tr><td><strong>Driver</strong></td><td><code>doppio/crates/ui/src/windows/main/headless/</code></td><td>Actions, targets, state snapshots, screenshots and recording.</td></tr>
    <tr><td><strong>CLI</strong></td><td><code>scripts/doppio-headless.sh</code></td><td>Any shell, CI job or agent; no window opens.</td></tr>
  </tbody>
</table>

## Run the flows

```bash
./scripts/doppio-headless.sh run doppio/tests/ui-flows --format text
```

Each flow gets its own artifact folder. A failing step prints the action, the target,
the messages it produced and a hint. Exit codes: `0` pass, `1` step/assertion failure,
`2` usage or invalid JSON.

## Write a flow

```json
{
  "name": "Open the Scene menu and add an entity",
  "description": "Guards keyboard and menu routing for the add action.",
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

Guidelines:

- Start from a fixture (`entities`, `empty`, `material`, `texture`, `scene3d`,
  `nature`, `water`, `terrain`).
- Use catalogue ids (`id:...`), not points, unless the point is the behaviour under
  test.
- Assert after each meaningful action; put a `label` on assertions so failures read
  well.
- Keep screenshots as artifacts; use `baseline` only when the visuals are the point.
- Name the bug the flow guards in `description`.

## Inspect the UI

```bash
./scripts/doppio-headless.sh widgets --size 1440x800
./scripts/doppio-headless.sh screenshot --annotate --name workspace --out /tmp/shots
```

`widgets` lists ids, kinds and bounds. `screenshot --annotate` numbers every
catalogued widget and appends the legend `n. id — description`. The same catalogue
drives the [UI reference](ui-reference.md).

## Capture documentation images

Committed capture flows live in `captures/flows/capture-*.json`. Their shell
wrappers strip the numeric prefix so image names are stable:

```bash
./scripts/capture-material-docs.sh
./scripts/capture-nature-docs.sh
./scripts/capture-terrain-docs.sh
./scripts/capture-texture-docs.sh
./scripts/capture-water-docs.sh
./scripts/capture-gizmo-docs.sh
./scripts/capture-editor-tour.sh   # short MP4/GIF tour
```

A capture flow is a normal flow plus `screenshot` steps with `target`, `padding` and
`scale`. See `captures/flows/capture-gizmo-docs.json` for the scene3d pattern.

## Record GIFs and videos

`record_start` / `record_stop` capture the window or one widget and encode with
ffmpeg:

```json
{ "steps": [
  { "action": "record_start", "name": "dock", "format": "mp4", "fps": 30, "target": "id:editor.pane.viewport" },
  { "action": "drag", "from": "id:editor.pane.tab.console", "to": "point:900,300" },
  { "action": "wait", "ms": 1200, "real_time": true },
  { "action": "record_stop" }
] }
```

`format` accepts `gif`, `mp4` and `webm`; `width`, `scale`, `fps` and `keep_frames`
control the output. A recording left open when the script ends is finished
automatically.

## Regression rules

1. A user-visible fix or feature adds a flow under `doppio/tests/ui-flows/`.
2. The flow must pass in `cargo test` and in `scripts/check-rust-ui.sh`.
3. New widgets get a `UiId` and a `CATALOG` entry; otherwise they cannot be
   targeted, annotated or documented.
4. Visual changes regenerate the affected capture flow images; do not edit PNGs by
   hand.

## Related pages

- [Headless testing reference](../doppio/headless-testing.md)
  — every action, target form, state key and screenshot option.
- [UI reference](ui-reference.md) — generated ids and captions.
- [Building](../getting-started/building.md) — test binaries and feature flags.
