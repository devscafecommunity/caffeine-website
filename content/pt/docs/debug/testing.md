# Testes

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/tests/CMakeLists.txt"><code>tests/CMakeLists.txt</code></a></span>
</div>

<p class="doc-lede">Três camadas de teste: Catch2 para o motor, testes Rust unitários e
de integração para o Doppio, e flows de UI headless que conduzem a árvore de widgets
real sem janela. O CI corre as três.</p>

## Camadas

<table class="doc-table">
  <thead>
    <tr><th>Camada</th><th>Framework</th><th>Comando</th><th>Localização</th></tr>
  </thead>
  <tbody>
    <tr><td>Motor C++</td><td>Catch2 v3</td><td><code>ctest --output-on-failure</code></td><td><code>tests/</code>, binário <code>build/tests/CaffeineTest</code></td></tr>
    <tr><td>Editor Rust</td><td><code>cargo test</code></td><td><code>cd doppio &amp;&amp; cargo test</code></td><td><code>doppio/crates/ui/src/windows/main/tests.rs</code>, testes da crate do motor</td></tr>
    <tr><td>Flows de UI headless</td><td><code>doppio-headless</code></td><td><code>./scripts/check-rust-ui.sh</code></td><td><code>doppio/tests/ui-flows/*.json</code></td></tr>
  </tbody>
</table>

## Suite C++

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
cd build && ctest --output-on-failure
```

Corra uma tag ou teste diretamente:

```bash
./build/tests/CaffeineTest "[ecs]"
./build/tests/CaffeineTest "World *" --success
```

Os testes têm tags; `[stress]` marca os casos longos que o CI só corre num
`workflow_dispatch` manual. A suite cobre tipos do core, allocators, containers,
matemática, ECS, jobs, assets, RHI, física, áudio, animação, scripting, terreno e a
C ABI.

## Suite do editor Rust

```bash
cd doppio
cargo test
cargo test -p doppio-ui --features headless
```

A feature `headless` corre os flows comprometidos através de
`every_shipped_flow_passes`. A suite do editor cobre mensagens de `App`, estado de
painéis/docking, edições no inspector, pesquisa na hierarchy, gestos do viewport,
filtros da console, asset wizard e os grafos dos geradores.

## Flows de UI headless

```bash
./scripts/doppio-headless.sh run doppio/tests/ui-flows --format text
```

Cada flow começa numa fixture determinística, age com targets `id:`/`text:` e verifica
com `expect`. Capturas, baselines e gravação GIF/MP4 estão disponíveis para trabalho
visual. Veja [Headless testing](../doppio/headless-testing.md)
e [Automação de testes](../editor/test-automation.md).

## CI

`.github/workflows/test.yml` corre em pushes para `main`, `develop` e `feature/**`, e
em pull requests para `main`/`develop`:

1. configurar e compilar com GCC 13;
2. `./build/tests/CaffeineTest ~[stress] --success`;
3. `./scripts/check-rust-ui.sh`;
4. opcionalmente `./build/tests/CaffeineTest "[stress]" --success` em dispatch manual.

Uma alteração está pronta quando a suite C++ e as verificações Rust/headless passam.
Uma mudança visível no editor acrescenta um flow; uma mudança de comportamento do motor
acrescenta um caso Catch2.

## Escrever testes

<div class="doc-details">
  <details>
    <summary>Convenções Catch2</summary>
    <ul>
      <li>Um ficheiro por módulo: <code>tests/test_&lt;module&gt;.cpp</code>.</li>
      <li>Use <code>TEST_CASE("Behaviour", "[module]")</code> e <code>SECTION</code> para variantes.</li>
      <li>Prefira dados determinísticos; sem sleeps, janelas GPU reais ou rede.</li>
      <li>Marque casos lentos com <code>[stress]</code> para o CI padrão os saltar.</li>
    </ul>
  </details>
  <details>
    <summary>Convenções dos flows headless</summary>
    <ul>
      <li>Comece em <code>entities</code>, <code>empty</code> ou numa fixture de gerador.</li>
      <li>Use ids do catálogo, não pontos de ecrã, exceto quando o ponto é o comportamento.</li>
      <li>Faça asserções após cada ação relevante e rotule a asserção.</li>
      <li>Guarde capturas como artefactos; use baselines só para regressões visuais.</li>
    </ul>
  </details>
</div>

## Páginas relacionadas

- [Headless testing](../doppio/headless-testing.md)
- [Automação de testes](../editor/test-automation.md)
- [Compilar](../getting-started/building.md)
