# Contributing

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Doppio</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">The rules that keep the engine, the Rust editor and the
documentation consistent, plus the exact commands a pull request must pass.</p>

## Ground rules

1. **C++20**, CMake 3.20+ and SDL3 in the engine; **Rust 2021 + Iced 0.14** in Doppio.
   Match the style of the file you edit.
2. **Minimal diffs** — one concern per change; no drive-by refactors.
3. **Tests first** — add or update a test when behaviour changes.
4. **No frontend code in the core** — `caffeine-core` has no ImGui, panels or editor
   state. Frontends talk through `libcaffeine-capi`.
5. **No plugin code in the engine** — plugin sources live in `doppio-plugins`.
6. **Documentation is HTML-first** — see [`DOCS_STYLE.md`](https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/DOCS_STYLE.md).

## Workflow

```bash
./scripts/submodules.sh
./scripts/build.sh release
cd doppio && cargo build -p doppio-ui
```

Before opening a pull request:

```bash
cd build && ctest --output-on-failure
cd ../doppio && cargo test
cd .. && ./scripts/check-rust-ui.sh
git diff --check
cmake --build build --target audit-plugin-coupling
```

`check-rust-ui.sh` includes formatting, tests, clippy, the core/ImGui coupling
audit and the headless UI flows. A new user-visible behaviour also needs a flow in
`doppio/tests/ui-flows/`.

## Editor changes

- Add a `UiId` and a `CATALOG` entry for every interactive widget
  (`doppio/crates/ui/src/uikit/id.rs`).
- Route mutations through `Message`s and `App::update`; panels only compose
  components.
- Record an undo step with `App::commit` for every editing command.
- Keep the viewport non-blocking: render offscreen and poll the readback.
- Expose agent-facing commands as `Message`-returning actions in `main/agent.rs`.

## Plugins

Add or change plugins in the
[doppio-plugins](https://github.com/devscafecommunity/doppio-plugins) repository.
The engine owns the public SDK (`include/caffeine/plugin/`) and the host; the
archived C++ editor is reference only. See
[Writing a plugin](../plugins/writing-a-plugin.md).

## Documentation

- English lives under `caffeine-website/content/en/docs/`; Portuguese mirrors the
  same paths under `content/pt/docs/`.
- Every page starts with a title, a `doc-meta` strip and a short lede.
- Screenshots come from the headless driver, never from a desktop screenshot.
- Update the capture flow in `captures/flows/` when the UI changes.
- Run the two audits:

```bash
cd caffeine-website
python3 scripts/audit-docs.py --include-engine
python3 scripts/audit-docs-i18n.py
```

## Commit style

Use a short imperative subject and explain the *why* in the body. Do not commit
build artifacts, local configuration or generated caches. A documentation change
should update the English page, its Portuguese mirror and any images in the same
commit.
