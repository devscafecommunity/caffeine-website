# Development history

<div class="doc-meta">
  <span class="doc-badge doc-badge--historical">Historical</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Doppio</span>
  <span>Last updated: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">How the engine and editor arrived at their current shape. This
page is a historical index, not a status report: phase labels and "planned" markers
describe the plan at the time, not today's implementation.</p>

<div class="doc-callout doc-callout--note">
  <p><strong>Current status lives elsewhere.</strong> Use the
  <a href="README.md">documentation index</a> and the module pages for what exists
  now. For release notes, see <a href="releases/changelog.md">Changelog</a>.</p>
</div>

## Timeline

<table class="doc-table">
  <thead>
    <tr><th>When</th><th>Milestone</th><th>Record</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>Foundation</td>
      <td>Fixed-width types, allocators, containers, vectors/matrices and the first Catch2 suites.</td>
      <td><a href="core/types.md">Core types</a>, <a href="memory/allocators.md">Allocators</a>, <a href="math/vectors.md">Math</a></td>
    </tr>
    <tr>
      <td>Runtime base</td>
      <td>Timer, fixed-step game loop, job system, input and debug tooling.</td>
      <td><a href="core/game-loop.md">Game loop</a>, <a href="concurrency/job-system.md">Job system</a>, <a href="debug/debug-tools.md">Debug tools</a></td>
    </tr>
    <tr>
      <td>RHI and 2D</td>
      <td>SDL3 GPU abstraction, batch renderer, 2D camera, asset manager and the CAF format.</td>
      <td><a href="rendering/rhi.md">RHI</a>, <a href="rendering/batch-renderer.md">Batch renderer</a>, <a href="assets/caf-format.md">CAF format</a></td>
    </tr>
    <tr>
      <td>ECS and systems</td>
      <td>Archetype ECS, scene stack, events, physics, animation, audio and the retained UI.</td>
      <td><a href="ecs/core.md">ECS</a>, <a href="physics/physics-2d.md">Physics 2D</a>, <a href="audio/audio-system.md">Audio</a></td>
    </tr>
    <tr>
      <td>3D transition</td>
      <td>Quaternions, mesh loading, 3D camera, spatial partitioning, skeletal animation.</td>
      <td><a href="math/quaternions.md">Quaternions</a>, <a href="rendering/camera-3d.md">Camera 3D</a>, <a href="physics/spatial-partitioning.md">Spatial partitioning</a></td>
    </tr>
    <tr>
      <td>Doppio</td>
      <td>From the ImGui C++ editor to the Rust/Iced workspace, the five-pane layout and the C ABI boundary.</td>
      <td><a href="editor/scene-editor.md">Scene editor</a>, <a href="doppio/rust-ui.md">Rust UI notes</a>, <a href="plans/2026-05-24-doppio-ui-test-framework.md">UI test framework plan</a></td>
    </tr>
    <tr>
      <td>Rendering push</td>
      <td>PBR, HDR post-processing, TAA, shadows, reflections, volumetric lighting and GPU readback viewport.</td>
      <td><a href="plans/2026-09-21-rendering-roadmap.md">Rendering roadmap</a>, <a href="plans/2026-10-02-forward-pbr-post-session.md">Forward PBR session</a>, <a href="rendering/materials-pbr.md">PBR materials</a></td>
    </tr>
    <tr>
      <td>Content tools</td>
      <td>Material Generator, Texture Generator, Texture Set painter, Nature, Water and Terrain generators.</td>
      <td><a href="doppio/material-pipeline.md">Material pipeline</a>, <a href="doppio/texture-generator-guide.md">Texture guide</a>, <a href="doppio/terrain-generator-guide.md">Terrain guide</a></td>
    </tr>
    <tr>
      <td>Headless testing</td>
      <td>Scripted UI flows, annotated screenshots, baselines and GIF/MP4 recording with no window.</td>
      <td><a href="doppio/headless-testing.md">Headless driver</a>, <a href="editor/test-automation.md">Test automation</a></td>
    </tr>
  </tbody>
</table>

## Planning tracks

| Track | Pages |
|---|---|
| Fundamental pillars | [Engine pillars roadmap](plans/2026-09-22-engine-pillars-roadmap.md) |
| Rendering | [Rendering roadmap](plans/2026-09-21-rendering-roadmap.md) |
| Editor milestones M1–M4 | [Milestones](plans/milestones/README.md) |
| Terrain module plan | [Terrain milestones](plans/milestones/terrain/README.md) |
| Session archive | [Archive](plans/archive/README.md) |

## Conventions that survived

- **Data-oriented design** — contiguous component storage, cache-friendly iteration.
- **No RTTI, no exceptions on hot paths** — errors are return values.
- **Custom allocators** — no loose `new`/`delete` in engine code.
- **C ABI for frontends** — the editor is replaceable; Doppio is one frontend.
- **Tests for behaviour** — Catch2 for the engine, headless flows for the editor.

## Full commit history

The chronological record is the Git history of the repository. Release-level notes
live in [Changelog](releases/changelog.md); session notes under `plans/` capture the
reasoning behind larger changes.
