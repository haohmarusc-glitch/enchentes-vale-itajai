# O trecho que faltava no Itajaí do Oeste, rio abaixo de Taió (08/10/2026)

## O problema

A auditoria dos vínculos (`docs/VINCULOS-DOS-TRACADOS.md`, 07/10/2026) mediu uma **falha de 2,1 km** no traçado
do Oeste, cerca de 10 km rio abaixo de Taió. Duas vias do OSM, ambas "Rio Itajaí do Oeste", não se tocavam:

| via | ponta |
|---|---|
| 1207901002 (rio acima) | termina em −27,14508, −49,91523 |
| 238628752 (rio abaixo) | começa em −27,14841, −49,89417 |

No Monitor, o rio parava e voltava uns 2 km adiante.

## A busca

A consulta que gerou o tronco pedia o rio **pelo nome**, então o trecho do meio tinha outro nome, nenhum nome
ou outra marcação. O `scripts/baixar_vao_oeste.py` pede ao Overpass **todo** curso d'água numa caixa em volta
da falha, sem filtrar por nome, e emenda as vias pelas pontas que se tocam, como o `baixar_vao_canhanduba.py`.
Ele roda no Actions (`baixar-vao-oeste.yml`), porque o Overpass não responde ao ambiente das sessões, e publica
o resultado no branch `vao-oeste`.

- **1ª rodada:** os três espelhos falharam: conexão recusada no principal e HTTP 500 no último. Nada gravado.
- **2ª rodada (base OSM de 08/10/2026 10:21 UTC):** 84 cursos na caixa (5 rios e 79 córregos). Entre os cursos
  sem nome, os ribeirões e o Rio Franzoí, a emenda achada foi **uma via só**.

| | |
|---|---|
| via | **1207901475**, `waterway=river`, `name=Rio Itajaí` |
| comprimento | 5.978 m, para 2.122 m em linha reta |
| pontas | começa e termina **nos mesmos nós** das duas vias do Oeste (0 m) |
| sinuosidade | 2,82; as vias vizinhas do Oeste têm de 2,0 a 2,97 (janelas de 6 km rio abaixo: 2,7 · 2,7 · 2,0) |
| área de água | a caixa tem uma relação `water=river` (7946011), o leito do rio |

É o canal do Oeste, com o nome incompleto no OSM ("Rio Itajaí", sem "do Oeste").

## Como entrou

- O `converter_tracado_rios.py` emenda a via no `data/rios/itajai-acu.geojson` **pelo número**
  (`EMENDAS`, antes `EMENDAS_DO_TRONCO`), nunca pelo nome. "Rio Itajaí" não vira nome aceito para outra via.
- Se a via vier com outro nome, a conversão aborta e pede nova conferência.
- O arquivo registra a emenda em `properties.emendas` e o bruto novo em `properties.origem`.
- Sem o bruto `data/brutos/vao-oeste-osm.json`, o tronco volta a ser o de antes. Rodar o conversor sem ele
  reproduz o arquivo anterior byte a byte.

## O que muda na tela

- O Oeste fica contínuo de Taió a Rio do Sul: 122 → 123 trechos no traçado do Açu.
- O quadro do mapa não muda: a caixa do tronco é a mesma, ao grau.
- A cor não muda de regra. No tronco, cada ponto segue a cidade mais próxima ao longo da sequência de cidades,
  então o trecho novo tem a mesma cor do Oeste em volta, a da régua de Taió.
- A trava do Monitor, a fumaça, a varredura, a auditoria e a colisão passaram.

Antes (em cima) e depois (embaixo), no Monitor de Taió, 1366 px:
`docs/prints/vao-oeste-2026-10-08/antes-depois-1366.png`.

## O que não faz

- Não desenha reta.
- Não muda vínculo, cota nem classificação.
- Não mexe em arquivo protegido do Monitor.
