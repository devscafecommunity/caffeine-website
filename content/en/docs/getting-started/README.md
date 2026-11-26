# Getting started

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/README.md"><code>README.md</code></a></span>
</div>

<p class="doc-lede">From a clean clone to a running Doppio session, with the engine
built once and the Rust editor launched against <code>libcaffeine-capi</code>.</p>

<figure class="doc-figure">
  <img src="../images/editor/project-manager.png" alt="Doppio project manager with Create New, Open Recent and Browse Projects tabs" loading="lazy">
  <figcaption>The project manager is the first screen when Doppio starts without a scene. Create a project or reopen a recent one before the editor layout appears.</figcaption>
</figure>

## Recommended path

### 1. Clone with submodules

```bash
git clone --recurse-submodules git@github.com:devscafecommunity/caffeine.git
cd caffeine
```

If the repository was cloned without submodules, initialise them later:

```bash
./scripts/submodules.sh
```

### 2. Build the C++ engine and the C ABI

Doppio is a Rust workspace, but it loads the engine through
`libcaffeine-capi`. Build the engine first:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

The library lands at `build/libcaffeine-capi.so` on Linux and
`build/libcaffeine-capi.dylib` on macOS.

### 3. Run Doppio

```bash
cd doppio
cargo run -p doppio-ui
```

With no arguments, Doppio opens the project manager. To open a scene directly:

```bash
cargo run -p doppio-ui -- ../assets/benchmarks/dense_outdoor.caf
```

The C ABI library is found next to the build tree; set
`CAFFEINE_ENGINE_ROOT` when the editor and the engine are in different
locations.

### 4. Optional: check the workspace

```bash
./scripts/check-rust-ui.sh
```

This runs `cargo fmt --check`, the Rust tests, clippy with warnings denied, the
core/ImGui coupling audit and the headless flow suite.

## Pages

| Page | Contents |
|------|----------|
| [Build guide](build-guide.md) | `scripts/build.sh` wrapper, platform helpers and CI commands |
| [Quick start](quick-start.md) | First project, entity, scene save and viewport navigation |
| [Building](building.md) | Manual CMake options, Rust workspace and test binaries |
| [Contributing](contributing.md) | Coding rules, documentation rules and the review checklist |

## Requirements

<table class="doc-table">
  <thead>
    <tr><th>Dependency</th><th>Version</th><th>Used by</th></tr>
  </thead>
  <tbody>
    <tr><td>CMake</td><td>3.20+</td><td>Engine, C ABI, runtime, plugins</td></tr>
    <tr><td>C++ compiler</td><td>C++20 — GCC 12+, Clang 15+, MSVC 19.3+</td><td>Engine and plugins</td></tr>
    <tr><td>SDL3</td><td>3.x</td><td>RHI, runtime, viewport</td></tr>
    <tr><td>Rust</td><td>1.88+ (edition 2021)</td><td>Doppio workspace</td></tr>
    <tr><td>Python</td><td>3.10+</td><td>Build helpers, docs audits, headless capture scripts</td></tr>
  </tbody>
</table>

<div class="doc-callout doc-callout--note">
  <p><strong>Note.</strong> The engine fetches pinned dependencies (ImGui, Bullet3,
  tinygltf and others) during configure. The first configure needs network access;
  later builds are offline.</p>
</div>

## Next steps

- Follow [Quick start](quick-start.md) to create a project and save a scene.
- Read [the headless driver](../doppio/headless-testing.md)
  to drive the editor without a window.
- Open the [UI reference](../editor/ui-reference.md) for every catalogued widget id.
