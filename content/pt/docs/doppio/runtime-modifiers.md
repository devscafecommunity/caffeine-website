# Modificadores em tempo de execução para materiais gerados

As texturas e os materiais são gerados, por isso o PNG cozinhado (baked) não é o único produto: o mesmo material pode
reagir ao mundo **sem voltar a fazer o bake dos mapas**. Um modificador são alguns números que o shader aplica por cima do
material, de modo que um script pode molhar uma rocha quando chove, cobrir um telhado de neve ou envelhecer uma parede.

| Modifier | Intervalo | Efeito |
|---|---|---|
| **Tint** | cor, branco = nenhum | multiplica o albedo (mudança de estação, cor de equipa) |
| **Wetness** | 0 seco .. 1 encharcado | albedo mais escuro e uma película brilhante (roughness baixa) |
| **Snow** | 0 nenhuma .. 1 tudo o que está virado para cima | cobertura branca e rugosa nas faces voltadas para cima; quanto mais neve, mais longe desce pelas encostas |
| **Age** | 0 novo .. 1 velho | desbotado, mais escuro, mais rugoso |

## Onde vivem

* No **material** (chaves `.mat` `mod_tint`, `mod_wetness`, `mod_snow`, `mod_age`; `MaterialSurface`,
  C ABI **v10**, a secção *Run-time modifiers* do painel Material): os valores por defeito com que um material é distribuído.
* Na **entidade** (campos **Tint**, **Wetness**, **Snow**, **Age** do Mesh Renderer, guardados com a cena): os
  valores que um jogo altera em tempo de execução. São campos refletidos normais, por isso os scripts leem-nos e escrevem-nos como
  quaisquer outros (`Mesh Renderer`, `Wetness`, 0..1), tal como o Inspector e a ponte de agentes.
* O renderer **combina** ambos: as tints multiplicam-se, as quantidades somam-se e são limitadas a 0..1. As entidades que partilham um
  material e uma mesh continuam a fazer batch apenas quando os seus modificadores são iguais.

As cenas guardadas antes de os campos existirem carregam com modificadores neutros.

## O que ainda não existe

* Os modificadores que precisam de mapas novos (decalques de dano, musgo a crescer nas fendas) continuam a precisar do grafo do gerador em
  tempo de execução; o grafo e o seu esquema de parâmetros ainda não são distribuídos com o resultado do bake.
* O vento e a translucência da folhagem (`wind_*`, `translucency`) são apenas do material, não por entidade.
