# Contribuir

<div class="doc-meta">
  <span class="doc-badge doc-badge--stable">Stable</span>
  <span class="doc-badge">Engine</span>
  <span class="doc-badge">Doppio</span>
  <span>Verificado em: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">As regras que mantêm o motor, o editor Rust e a documentação
consistentes, mais os comandos exatos que um pull request tem de passar.</p>

## Regras base

1. **C++20**, CMake 3.20+ e SDL3 no motor; **Rust 2021 + Iced 0.14** no Doppio.
   Siga o estilo do ficheiro que edita.
2. **Diffs mínimos** — uma preocupação por alteração; sem refactors oportunistas.
3. **Testes primeiro** — adicione ou atualize um teste quando o comportamento muda.
4. **Sem código de frontend no core** — `caffeine-core` não tem ImGui, painéis nem
   estado do editor. Os frontends comunicam por `libcaffeine-capi`.
5. **Sem código de plugins no motor** — os plugins vivem em `doppio-plugins`.
6. **A documentação é HTML-first** — veja [`DOCS_STYLE.md`](https://github.com/devscafecommunity/caffeine/blob/main/caffeine-website/DOCS_STYLE.md).

## Fluxo de trabalho

```bash
./scripts/submodules.sh
./scripts/build.sh release
cd doppio && cargo build -p doppio-ui
```

Antes de abrir um pull request:

```bash
cd build && ctest --output-on-failure
cd ../doppio && cargo test
cd .. && ./scripts/check-rust-ui.sh
git diff --check
cmake --build build --target audit-plugin-coupling
```

`check-rust-ui.sh` inclui formatação, testes, clippy, a auditoria de acoplamento
core/ImGui e os flows de UI headless. Um novo comportamento visível ao utilizador
também precisa de um flow em `doppio/tests/ui-flows/`.

## Alterações ao editor

- Adicione um `UiId` e uma entrada em `CATALOG` para cada widget interativo
  (`doppio/crates/ui/src/uikit/id.rs`).
- As mutações passam por `Message` e `App::update`; os painéis apenas compõem
  componentes.
- Registe um passo de undo com `App::commit` em cada comando de edição.
- Mantenha o viewport não bloqueante: render offscreen e polling do readback.
- Exponha comandos para agentes como ações que devolvem `Message` em `main/agent.rs`.

## Plugins

Adicione ou altere plugins no repositório
[doppio-plugins](https://github.com/devscafecommunity/doppio-plugins). O motor é dono
do SDK público (`include/caffeine/plugin/`) e do host; o editor C++ arquivado é apenas
referência. Veja [Escrever um plugin](../plugins/writing-a-plugin.md).

## Documentação

- O inglês vive em `caffeine-website/content/en/docs/`; o português espelha os mesmos
  caminhos em `content/pt/docs/`.
- Cada página começa com título, uma faixa `doc-meta` e um lede curto.
- As capturas vêm do driver headless, nunca de um screenshot do desktop.
- Atualize o flow de captura em `captures/flows/` quando a UI mudar.
- Corra as duas auditorias:

```bash
cd caffeine-website
python3 scripts/audit-docs.py --include-engine
python3 scripts/audit-docs-i18n.py
```

## Estilo de commits

Use um assunto imperativo curto e explique o *porquê* no corpo. Não faça commit de
artefactos de build, configuração local ou caches geradas. Uma alteração de
documentação deve atualizar a página inglesa, o espelho português e as imagens no
mesmo commit.
