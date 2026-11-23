# Photon — GI híbrido nativo por radiance cascades

<div class="doc-meta">
  <span class="doc-badge doc-badge--beta">Beta</span>
  <span class="doc-badge">Engine</span>
  <span>Last updated: <time datetime="2026-11-18">2026-11-18</time></span>
</div>

<p class="doc-lede">Iluminação global em tempo real sem ray tracing por hardware: radiance cascades ancoradas ao ecrã, merge de intervalos e far field de céu/ambiente.</p>

O Photon é um **sistema nativo da engine**: é compilado em `caffeine-core` e usado pelo
editor e pelo runtime. Não é carregado como plugin. Fornece iluminação global em tempo
real sem hardware de ray tracing.

<figure class="doc-figure">
  <img src="../images/captures/photon-gi.png" alt="Iluminação indireta do Photon no runtime" loading="lazy">
  <figcaption>Iluminação indireta do Photon no runtime</figcaption>
</figure>


## Estado

| Parte do Photon | Estado |
|-----------------|--------|
| Campo próximo ancorado ao ecrã | **Implementado**: cascatas alinhadas ao mundo traçadas contra o buffer de profundidade, fundidas da frente para trás, resolvidas em SH-L1 |
| Campo distante | **Implementado**: quatro níveis de clipmap de voxels com probes, os triângulos de toda a cena voxelizados (terreno, malhas com esqueleto e recortadas incluídos) |
| Regiões sujas | **Implementado**: um objeto em movimento revoxeliza só as caixas onde esteve e onde está |
| Luz direta na GI | **Implementado**: sol, luzes de ponto e focos injetados nos voxels, com sombra pelo volume de materiais |
| Realimentação multi-bounce | **Implementado**: a irradiância anterior volta a entrar com um limite e um histórico reprojetado |
| Ganho do ressalto | **Implementado**: escala a luz que os voxels guardam |
| Vetores de movimento | Ainda não: o histórico reprojeta com a matriz anterior |
| Passe de reflexos glossy | Ainda não |
| Denoiser temporal | Fornecido pelo TAA do motor: o Photon corre antes dele |

O guia completo, com o separador Photon, as predefinições, as estatísticas e a C ABI, é
[Photon: iluminação global no Doppio](../doppio/photon-guide.md).

## Utilização

1. Abra uma cena com uma Camera 3D e geometria.
2. Abra **View → Photon (Global Illumination)**.
3. Prima **Add Photon GI** se a cena ainda não tiver o componente.
4. Escolha uma predefinição e ajuste **Radius**, **Sky**, **Bounce gain** e os interruptores da geometria dos voxels.
5. Mude **Debug → GI only** para inspecionar o resultado, e leia o cartão **Voxel volume** para ver o que o campo distante está a fazer.

O componente é `ECS::PhotonGIComponent`; o Inspetor mostra os mesmos campos.


## Oclusão de ambiente pré-processada (sem RTX)

A secção nativa **Baked ambient occlusion** pré-calcula AO estática para o material
do mesh selecionado:

1. Selecione uma entidade com mesh estática (ou use **Bake scene**).
2. Escolha resolução (256/512/1024), raios, distância máxima e bias.
3. Prima **Bake selected mesh**.

O baker usa **compute na GPU** quando o render device expõe compute e
recorre ao BVH CPU caso contrário. A CPU só rasteriza UVs e constrói a lista de
triângulos; os testes de raio pesados correm na GPU. Cenas com mais de 8192
triângulos usam o caminho CPU.

O baker:

- recolhe todos os triângulos estáticos da cena como oclusores,
- rasteriza o mesh alvo em espaço UV,
- lança raios com peso cosseno,
- escreve um **PNG ORM** com AO no R (roughness/metallic preservados em G/B),
- atualiza `orm_map` e `ao_strength` do material.

O shader da engine já usa ORM.R como oclusão de ambiente, por isso o resultado é
aplicado **sem hardware de ray tracing** e sem ruído de screen-space. Refaça o bake
depois de alterar geometria estática.

> O AO pré-processado é para meshes estáticas. Objetos em movimento devem continuar
> a usar o passe screen-space do Photon. Meshes com UVs sobrepostas fazem média das
> faces; use UVs únicas para AO por face.

## Resolução de problemas do bake

| Mensagem | Causa / correção |
|----------|------------------|
| **Select a mesh entity in the Hierarchy** | O bake usa uma mesh (`MeshFilterComponent`). Selecione uma entidade com mesh, não o environment ou uma luz. |
| **Selected entity has no mesh** | A entidade não tem `MeshFilterComponent` ou o caminho da mesh custom é inválido. |
| **Mesh has no usable UV coverage** | A mesh não tem UVs ou todas são degeneradas. Faça unwrap antes do bake. |
| **Could not read material** | `customMaterialPath` aponta para um `.mat` inexistente ou inválido. Corrija o caminho ou limpe-o para o baker criar um novo material. |
| **Bake scene: N failed** | Veja o estado/log; a primeira entidade falhada e o motivo são mostrados. As restantes são assadas normalmente. |
| **GPU compute unavailable** | O device não expõe compute; o baker usa automaticamente o BVH CPU. |
| **ORM gerado mas o viewport não muda** | O material tem de estar atribuído à mesh e o caminho ORM tem de resolver dentro do projeto. Volte a selecionar a entidade ou recarregue o material. |

O bake é enfileirado pelo painel e executado **entre frames** (depois de o frame do
editor ser submetido). Assim o command buffer da GPU fica independente do frame em
curso.

## Performance

- Low: 4 raios × 2 passos por intervalo
- Medium: 8 raios × 2 passos
- High: 12 raios × 3 passos

O Photon corre **antes do TAA**, por isso o resolve temporal limpa o padrão
estocástico. Comece em Balanced para edição e use High/Cinematic para capturas.


## Limitações

- O Photon ainda não tem vetores de movimento: o histórico reprojeta com a matriz anterior, por
  isso objetos rápidos podem deixar rasto.
- O terreno conta com uma só cor de terra no volume de voxels, e uma malha recortada conta como
  um bloco sólido quando o seu interruptor está ligado.
- A oclusão em screen-space pode vazar em geometria fina; use um **Radius** menor.
- Os reflexos glossy ainda não fazem parte do Photon.

## Relacionado

- [Photon: iluminação global no Doppio](../doppio/photon-guide.md)
- [Scene viewport](scene-viewport.md)
- [Workspace e tema](workspace-and-theme.md)
- [Catálogo de plugins](../plugins/README.md)
