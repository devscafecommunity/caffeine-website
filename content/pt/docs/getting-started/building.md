# Compilar

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">Configuração manual de CMake para o motor e a C ABI, o workspace
Rust que compila o Doppio, e os comandos de teste usados por CI e agentes.</p>

## Motor (C++20 + CMake)

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

Para trabalho no editor, compile apenas a C ABI depois de alterar o motor:

```bash
cmake --build build --target caffeine-capi -j
```

### Artefactos

<table class="doc-table">
  <thead>
    <tr><th>Alvo</th><th>Saída</th><th>Função</th></tr>
  </thead>
  <tbody>
    <tr><td><code>caffeine-core</code></td><td><code>build/libcaffeine-core.a</code></td><td>Biblioteca do motor sem ImGui nem código de editor.</td></tr>
    <tr><td><code>caffeine-capi</code></td><td><code>build/libcaffeine-capi.so</code> / <code>.dylib</code> / <code>.dll</code></td><td>C ABI estável carregada pelo Doppio e por frontends externos.</td></tr>
    <tr><td><code>caffeine-runtime</code></td><td><code>build/caffeine-runtime</code></td><td>Runtime autónomo em ImGui para cenas.</td></tr>
    <tr><td><code>caffeine-combined</code></td><td><code>build/caffeine-combined</code></td><td>Build combinada com a camada de suporte ao editor.</td></tr>
    <tr><td><code>caffeine-render-snapshot</code></td><td><code>build/caffeine-render-snapshot</code></td><td>Renderizador de cenas de referência para imagens de regressão visual.</td></tr>
    <tr><td><code>caf-encode</code></td><td><code>build/caf-encode</code></td><td>Encoder CAF legado; prefira a CLI <code>caf-pack</code>.</td></tr>
    <tr><td>Plugins Doppio</td><td><code>build/plugins/*.so</code></td><td>Todos os plugins do submódulo <code>doppio-plugins</code>, carregados a pedido.</td></tr>
  </tbody>
</table>

## Doppio (Rust 2021 + Iced 0.14)

Compile primeiro a C ABI e depois o workspace:

```bash
cd doppio
cargo build -p doppio-ui
cargo run -p doppio-ui
```

Os binários ficam em `doppio/target/<profile>/doppio` e
`doppio/target/<profile>/doppio-headless` (este último requer a feature
`headless`). O perfil release é o usado pelo launcher:

```bash
cd doppio
cargo build --release -p doppio-ui
```

## Opções comuns de CMake

<table class="doc-table">
  <thead>
    <tr><th>Opção</th><th>Padrão</th><th>Efeito</th></tr>
  </thead>
  <tbody>
    <tr><td><code>CAFFEINE_BUILD_HEADLESS</code></td><td><code>OFF</code></td><td>Compila <code>caffeine-core</code> sem SDL3 nem RHI para servidores e CI.</td></tr>
    <tr><td><code>CAFFEINE_ENABLE_SCRIPTING</code></td><td><code>ON</code></td><td>Lua 5.4 + sol2 e o sistema de scripts.</td></tr>
    <tr><td><code>CAFFEINE_ENABLE_BULLET3</code></td><td><code>ON</code></td><td>Física de corpos rígidos com Bullet3.</td></tr>
    <tr><td><code>CAFFEINE_BUILD_DOPPIO_PLUGINS</code></td><td><code>ON</code></td><td>Compila todos os plugins de <code>doppio-plugins</code> para <code>build/plugins</code>; use <code>OFF</code> em builds mínimas ou headless.</td></tr>
    <tr><td><code>CMAKE_BUILD_TYPE</code></td><td><code>Debug</code></td><td>Use <code>Release</code> para trabalho no editor e benchmarks.</td></tr>
  </tbody>
</table>

<div class="doc-callout doc-callout--note">
  <p><strong>Nota.</strong> Se o submódulo <code>doppio-plugins</code> faltar, a
  configuração falha com uma mensagem explícita. Corra
  <code>./scripts/submodules.sh</code> ou passe
  <code>-DCAFFEINE_BUILD_DOPPIO_PLUGINS=OFF</code>.</p>
</div>

## Testes

### Motor C++

```bash
cd build
ctest --output-on-failure
```

O binário Catch2 é `build/tests/CaffeineTest`; corra uma tag ou teste diretamente:

```bash
./build/tests/CaffeineTest "[ecs]"
```

### Editor Rust

```bash
cd doppio
cargo test -p doppio-ui
cargo test -p doppio-ui --features headless
```

A feature headless corre os flows de UI em `doppio/tests/ui-flows/`. A verificação
combinada usada em CI é:

```bash
./scripts/check-rust-ui.sh
```

### Driver headless

```bash
./scripts/doppio-headless.sh widgets
./scripts/doppio-headless.sh run doppio/tests/ui-flows --format text
```

Veja [o guia headless](../doppio/headless-testing.md)
para a referência de ações, capturas, baselines e gravação GIF/MP4.

## Helpers de plataforma

| Comando | Plataforma | O que faz |
|---------|------------|-----------|
| `./scripts/build.sh debug` | Linux/macOS | Configura e compila Debug |
| `./scripts/build.sh release` | Linux/macOS | Configura e compila Release |
| `./scripts/build.sh test` | Linux/macOS | Build Debug seguida de `ctest` |
| `./scripts/build.sh rebuild` | Linux/macOS | Remove `build/`, configura e compila |
| `./scripts/build.sh clean` | Linux/macOS | Remove `build/` |
| `scripts\build.bat` | Windows | Helper de build para Windows |
| `./scripts/build.fish` | Fish shell | Variante para Fish |
| `./scripts/build-launcher.sh` | Linux/macOS | Compila o launcher Rust |

## Limpeza

```bash
rm -rf build doppio/target
```

Reconfigure depois de apagar `build/`. As caches do Cargo podem ser apagadas, mas
tornam o próximo build Rust mais lento.
