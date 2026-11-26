# Building

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Doppio</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">Manual CMake configuration for the engine and C ABI, the Rust
workspace that builds Doppio, and the test commands used by CI and agents.</p>

## Engine (C++20 + CMake)

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

For editor work, build only the C ABI after a source change:

```bash
cmake --build build --target caffeine-capi -j
```

### Artifacts

<table class="doc-table">
  <thead>
    <tr><th>Target</th><th>Output</th><th>Purpose</th></tr>
  </thead>
  <tbody>
    <tr><td><code>caffeine-core</code></td><td><code>build/libcaffeine-core.a</code></td><td>Engine library without ImGui or editor code.</td></tr>
    <tr><td><code>caffeine-capi</code></td><td><code>build/libcaffeine-capi.so</code> / <code>.dylib</code> / <code>.dll</code></td><td>Stable C ABI loaded by Doppio and external frontends.</td></tr>
    <tr><td><code>caffeine-runtime</code></td><td><code>build/caffeine-runtime</code></td><td>Standalone ImGui runtime host for scenes.</td></tr>
    <tr><td><code>caffeine-combined</code></td><td><code>build/caffeine-combined</code></td><td>Combined runtime build with the editor-support shim.</td></tr>
    <tr><td><code>caffeine-render-snapshot</code></td><td><code>build/caffeine-render-snapshot</code></td><td>Reference-scene renderer for visual regression images.</td></tr>
    <tr><td><code>caf-encode</code></td><td><code>build/caf-encode</code></td><td>Legacy CAF encoder; prefer the <code>caf-pack</code> CLI.</td></tr>
    <tr><td>Doppio plugins</td><td><code>build/plugins/*.so</code></td><td>Every plugin from the <code>doppio-plugins</code> submodule, loaded on demand.</td></tr>
  </tbody>
</table>

## Doppio (Rust 2021 + Iced 0.14)

Build the C ABI first, then the workspace:

```bash
cd doppio
cargo build -p doppio-ui
cargo run -p doppio-ui
```

The binaries are written to `doppio/target/<profile>/doppio` and
`doppio/target/<profile>/doppio-headless` (the latter requires the `headless`
feature). The release profile is the one used by the launcher:

```bash
cd doppio
cargo build --release -p doppio-ui
```

## Common CMake options

<table class="doc-table">
  <thead>
    <tr><th>Option</th><th>Default</th><th>Effect</th></tr>
  </thead>
  <tbody>
    <tr><td><code>CAFFEINE_BUILD_HEADLESS</code></td><td><code>OFF</code></td><td>Builds <code>caffeine-core</code> without SDL3 or RHI for servers and CI.</td></tr>
    <tr><td><code>CAFFEINE_ENABLE_SCRIPTING</code></td><td><code>ON</code></td><td>Lua 5.4 + sol2 bindings and the script system.</td></tr>
    <tr><td><code>CAFFEINE_ENABLE_BULLET3</code></td><td><code>ON</code></td><td>Bullet3 rigid-body physics.</td></tr>
    <tr><td><code>CAFFEINE_BUILD_DOPPIO_PLUGINS</code></td><td><code>ON</code></td><td>Builds every plugin from <code>doppio-plugins</code> into <code>build/plugins</code>; set <code>OFF</code> for minimal or headless builds.</td></tr>
    <tr><td><code>CMAKE_BUILD_TYPE</code></td><td><code>Debug</code></td><td>Use <code>Release</code> for editor and benchmark work.</td></tr>
  </tbody>
</table>

<div class="doc-callout doc-callout--note">
  <p><strong>Note.</strong> If the <code>doppio-plugins</code> submodule is missing,
  configure fails with an explicit message. Run <code>./scripts/submodules.sh</code>
  or pass <code>-DCAFFEINE_BUILD_DOPPIO_PLUGINS=OFF</code>.</p>
</div>

## Tests

### C++ engine

```bash
cd build
ctest --output-on-failure
```

The Catch2 binary is `build/tests/CaffeineTest`; run a single tag or test directly:

```bash
./build/tests/CaffeineTest "[ecs]"
```

### Rust editor

```bash
cd doppio
cargo test -p doppio-ui
cargo test -p doppio-ui --features headless
```

The headless feature runs the committed UI flows in
`doppio/tests/ui-flows/`. The combined check used by CI is:

```bash
./scripts/check-rust-ui.sh
```

### Headless driver

```bash
./scripts/doppio-headless.sh widgets
./scripts/doppio-headless.sh run doppio/tests/ui-flows --format text
```

See [the headless guide](../doppio/headless-testing.md)
for the full action reference, screenshots, baselines and GIF/MP4 recording.

## Platform helpers

| Command | Platform | What it does |
|---------|----------|--------------|
| `./scripts/build.sh debug` | Linux/macOS | Configure and build Debug |
| `./scripts/build.sh release` | Linux/macOS | Configure and build Release |
| `./scripts/build.sh test` | Linux/macOS | Debug build followed by `ctest` |
| `./scripts/build.sh rebuild` | Linux/macOS | Remove `build/`, configure and build |
| `./scripts/build.sh clean` | Linux/macOS | Remove `build/` |
| `scripts\build.bat` | Windows | Windows build helper |
| `./scripts/build.fish` | Fish shell | Fish variant |
| `./scripts/build-launcher.sh` | Linux/macOS | Builds the Rust launcher |

## Cleaning

```bash
rm -rf build doppio/target
```

Reconfigure after deleting `build/`. Cargo caches are safe to delete but make the
next Rust build slower.
