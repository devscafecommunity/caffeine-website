# Testing

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Doppio</span>
  <span>Last verified: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Source: <a href="https://github.com/devscafecommunity/caffeine/blob/main/tests/CMakeLists.txt"><code>tests/CMakeLists.txt</code></a></span>
</div>

<p class="doc-lede">Three test layers: Catch2 for the engine, Rust unit/integration
tests for Doppio, and headless UI flows that drive the real widget tree without a
window. CI runs all three.</p>

## Layers

<table class="doc-table">
  <thead>
    <tr><th>Layer</th><th>Framework</th><th>Command</th><th>Location</th></tr>
  </thead>
  <tbody>
    <tr><td>C++ engine</td><td>Catch2 v3</td><td><code>ctest --output-on-failure</code></td><td><code>tests/</code>, binary <code>build/tests/CaffeineTest</code></td></tr>
    <tr><td>Rust editor</td><td><code>cargo test</code></td><td><code>cd doppio &amp;&amp; cargo test</code></td><td><code>doppio/crates/ui/src/windows/main/tests.rs</code>, engine crate tests</td></tr>
    <tr><td>Headless UI flows</td><td><code>doppio-headless</code></td><td><code>./scripts/check-rust-ui.sh</code></td><td><code>doppio/tests/ui-flows/*.json</code></td></tr>
  </tbody>
</table>

## C++ suite

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
cd build && ctest --output-on-failure
```

Run one tag or test directly:

```bash
./build/tests/CaffeineTest "[ecs]"
./build/tests/CaffeineTest "World *" --success
```

Tests are tagged; `[stress]` marks the long-running cases that CI runs only on a
manual `workflow_dispatch`. The suite covers core types, allocators, containers, math,
ECS, jobs, assets, RHI, physics, audio, animation, scripting, terrain and the C ABI.

## Rust editor suite

```bash
cd doppio
cargo test
cargo test -p doppio-ui --features headless
```

The `headless` feature runs the committed flows through
`every_shipped_flow_passes`. The editor suite covers `App` messages, pane/docking
state, inspector edits, hierarchy search, viewport gestures, console filters, asset
wizard and the generator graphs.

## Headless UI flows

```bash
./scripts/doppio-headless.sh run doppio/tests/ui-flows --format text
```

Each flow starts from a deterministic fixture, acts with `id:`/`text:` targets and
asserts with `expect`. Screenshots, baselines and GIF/MP4 recording are available for
visual work. See [Headless testing](../doppio/headless-testing.md)
and [Test automation](../editor/test-automation.md).

## CI

`.github/workflows/test.yml` runs on pushes to `main`, `develop` and `feature/**`, and
on pull requests to `main`/`develop`:

1. configure and build with GCC 13;
2. `./build/tests/CaffeineTest ~[stress] --success`;
3. `./scripts/check-rust-ui.sh`;
4. optionally `./build/tests/CaffeineTest "[stress]" --success` on manual dispatch.

A change is ready when both the C++ suite and the Rust/headless checks pass. A
user-visible editor change adds a flow; an engine behaviour change adds a Catch2 case.

## Writing tests

<div class="doc-details">
  <details>
    <summary>Catch2 conventions</summary>
    <ul>
      <li>File per module: <code>tests/test_&lt;module&gt;.cpp</code>.</li>
      <li>Use <code>TEST_CASE("Behaviour", "[module]")</code> and <code>SECTION</code> for variants.</li>
      <li>Prefer deterministic data; no sleeps, real GPU windows or network.</li>
      <li>Tag slow cases <code>[stress]</code> so the default CI run skips them.</li>
    </ul>
  </details>
  <details>
    <summary>Headless flow conventions</summary>
    <ul>
      <li>Start from <code>entities</code>, <code>empty</code> or a generator fixture.</li>
      <li>Use catalogue ids, not screen points, unless the point is the behaviour.</li>
      <li>Assert after each meaningful action and label the assertion.</li>
      <li>Keep screenshots as artifacts; use baselines only for visual regressions.</li>
    </ul>
  </details>
</div>

## Related pages

- [Headless testing](../doppio/headless-testing.md)
- [Test automation](../editor/test-automation.md)
- [Building](../getting-started/building.md)
