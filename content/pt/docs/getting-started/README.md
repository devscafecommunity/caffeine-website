# Começar

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
  <span>Fonte: <a href="https://github.com/devscafecommunity/caffeine/blob/main/README.md"><code>README.md</code></a></span>
</div>

<p class="doc-lede">De um clone limpo a uma sessão Doppio a correr, com o motor
compilado uma vez e o editor Rust lançado contra <code>libcaffeine-capi</code>.</p>

<figure class="doc-figure">
  <img src="../images/editor/project-manager.png" alt="Gestor de projetos do Doppio com os separadores Create New, Open Recent e Browse Projects" loading="lazy">
  <figcaption>O gestor de projetos é o primeiro ecrã quando o Doppio arranca sem cena. Crie um projeto ou reabra um recente antes de aparecer o layout do editor.</figcaption>
</figure>

## Caminho recomendado

### 1. Clonar com submódulos

```bash
git clone --recurse-submodules git@github.com:devscafecommunity/caffeine.git
cd caffeine
```

Se o repositório foi clonado sem submódulos, inicialize-os mais tarde:

```bash
./scripts/submodules.sh
```

### 2. Compilar o motor C++ e a C ABI

O Doppio é um workspace Rust, mas carrega o motor através de
`libcaffeine-capi`. Compile primeiro o motor:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

A biblioteca fica em `build/libcaffeine-capi.so` no Linux e
`build/libcaffeine-capi.dylib` no macOS.

### 3. Executar o Doppio

```bash
cd doppio
cargo run -p doppio-ui
```

Sem argumentos, o Doppio abre o gestor de projetos. Para abrir uma cena diretamente:

```bash
cargo run -p doppio-ui -- ../assets/benchmarks/dense_outdoor.caf
```

A biblioteca da C ABI é encontrada junto à árvore de build; defina
`CAFFEINE_ENGINE_ROOT` quando o editor e o motor estiverem em locais diferentes.

### 4. Opcional: verificar o workspace

```bash
./scripts/check-rust-ui.sh
```

Este comando corre `cargo fmt --check`, os testes Rust, o clippy com warnings como
erros, a auditoria de acoplamento core/ImGui e a suite de flows headless.

## Páginas

| Página | Conteúdo |
|--------|----------|
| [Guia de build](build-guide.md) | Wrapper `scripts/build.sh`, helpers de plataforma e comandos de CI |
| [Quick start](quick-start.md) | Primeiro projeto, entidade, gravação de cena e navegação no viewport |
| [Compilar](building.md) | Opções manuais de CMake, workspace Rust e binários de teste |
| [Contribuir](contributing.md) | Regras de código, documentação e checklist de revisão |

## Requisitos

<table class="doc-table">
  <thead>
    <tr><th>Dependência</th><th>Versão</th><th>Usada por</th></tr>
  </thead>
  <tbody>
    <tr><td>CMake</td><td>3.20+</td><td>Motor, C ABI, runtime, plugins</td></tr>
    <tr><td>Compilador C++</td><td>C++20 — GCC 12+, Clang 15+, MSVC 19.3+</td><td>Motor e plugins</td></tr>
    <tr><td>SDL3</td><td>3.x</td><td>RHI, runtime, viewport</td></tr>
    <tr><td>Rust</td><td>1.88+ (edition 2021)</td><td>Workspace Doppio</td></tr>
    <tr><td>Python</td><td>3.10+</td><td>Helpers de build, auditorias de docs, scripts de captura headless</td></tr>
  </tbody>
</table>

<div class="doc-callout doc-callout--note">
  <p><strong>Nota.</strong> O motor descarrega dependências fixadas (ImGui, Bullet3,
  tinygltf e outras) durante a configuração. A primeira configuração precisa de rede;
  as seguintes funcionam offline.</p>
</div>

## Próximos passos

- Siga o [Quick start](quick-start.md) para criar um projeto e gravar uma cena.
- Leia [o driver headless](../doppio/headless-testing.md)
  para conduzir o editor sem janela.
- Abra a [referência de UI](../editor/ui-reference.md) para todos os ids de widgets catalogados.
