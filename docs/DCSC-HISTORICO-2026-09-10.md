# Histórico da rede estadual (DCSC) — o que chegou em 10/09/2026 e o que ele diz

Treze zips (`historico-dcsc/DCSC000NN.zip`) baixados pelo Jefferson no PC com um script próprio
(ainda fora do repo), a query GraphQL `historic` de `monitoramento.defesacivil.sc.gov.br`, em janelas
de 14 dias desde 1980. Consolidado por `scripts/consolidar_historico_dcsc.py`; resumo citável em
`data/brutos/dcsc-historico-resumo-2026-09-10.json`; séries inteiras (129 MB) em `data/series/dcsc/`,
fora do git.

## O que tem

| estação | cidade | leituras | de | até | observação |
|---|---|---:|---|---|---|
| DCSC-00003 | Ascurra | 156.471 | 12/04/2023 | 09/09/2026 | 22 leituras > 30 m (581,0) descartadas |
| DCSC-00005 | Gaspar | 196.662 | 09/12/2022 | 09/09/2026 | `rio_nivel` 0,00 o tempo todo — não mede nível (já sabido) |
| DCSC-00006 | Indaial | 200.028 | 18/11/2022 | 09/09/2026 | |
| DCSC-00013 | Rio do Sul | 204.313 | 20/10/2022 | 09/09/2026 | |
| DCSC-00018 | Botuverá | 200.889 | 14/11/2022 | 09/09/2026 | |
| DCSC-00019 | Brusque | 200.476 | 14/11/2022 | 09/09/2026 | 4 picos de sensor (12,38 m em 15/05/2024 entre vizinhas de 1,5 m) |
| DCSC-00020 | Ibirama | 204.210 | 20/10/2022 | 09/09/2026 | 1 leitura 21.474.836,47 (2^31/100) descartada |
| DCSC-00024 | Vidal Ramos | 199.012 | 25/11/2022 | 09/09/2026 | 1 pico solto (9,23 m) |
| DCSC-00026 | Blumenau | 182.237 | 13/12/2022 | 09/09/2026 | estação Meteo: chuva, vento, pressão; sem nível |
| DCSC-00029 | Guabiruba | 199.339 | 23/11/2022 | 09/09/2026 | altitude desde 04/2026 (28,7 m); 23 leituras > 30 m |
| DCSC-00030 | Ilhota | 196.685 | 13/12/2022 | 09/09/2026 | 1 pico solto (17,98 m) |
| DCSC-00039 | Ituporanga | 185.453 | 28/02/2023 | 09/09/2026 | 726 sentinelas `-35` |
| DCSC-00041 | Taió | **0** | — | — | **o download parou em 31/05/2005**, antes de a série existir |

Cadência de 10 min. Todas as estações têm o mesmo buraco de 173,9 h (uma semana da rede inteira),
mais dois ou três menores.

## Fuso: `ts` é hora de Brasília — provado, não presumido

1. A janela pedida com `startDate = 2026-09-01T00:00Z` devolve como primeiro item
   `ts = 2026-08-31T21:10` — 00:00 UTC é 21:00 em Brasília.
2. A crista de 01/09/2026 em Rio do Sul: DCSC-00013 às **05:20** (7,07 m); Asthon da Ponte Dom Tito
   Buss às **05:08 hora local** (6,79 m; `data/brutos/asthon-historico/ponte_dom_tito_buss.csv`, que
   tem as duas colunas). Se `ts` fosse UTC, a DCSC cristaria três horas antes da Asthon.

É o contrato do `medido_em` do projeto (CLAUDE.md), então o CSV grava `ts` como está. A API AO VIVO
(`Tags_data`, `coleta_nivel_sc.py`) manda UTC com fuso — são endpoints diferentes, e a regra "toda
fonte nova grava Brasília sem fuso" continua valendo para as duas.

## Cristas candidatas contra o que o repo já tem

Datum de cada estação é o bruto estadual (`usar_para_cota=false`). Nada abaixo entra em
`enchentes.json` sem decisão do Jefferson.

| cidade · evento | DCSC (crista, hora local) | `enchentes.json` | diferença |
|---|---|---|---|
| Rio do Sul · 18/11/2023 | 13,18 m às 00:20 | 13,04 m (GCD, sem hora) | +0,14 |
| Rio do Sul · out/2023 | 11,05 (09/10 13:20) e 11,94 (13/10 04:30) | 11,86 em **07/10** (GCD) | data não bate |
| Brusque · 05/10/2023 | 6,50 m às 00:40 | 6,85 (Rádio Cidade) | **−0,35** |
| Brusque · 12–13/10/2023 | 6,63 m às 21:40 | 6,91 (13/10) | **−0,28** |
| Brusque · 17/11/2023 | 8,63 m às 21:30 | 8,96 (DC Brusque, revisão de 2024) | **−0,33** |
| Brusque · 19/05/2024 | 7,27 m às 08:10 | — | |
| Indaial · 12/10/2023 | 8,83 m às 16:50 | — (Indaial sem registro desde 2022) | |
| Botuverá · 17/11/2023 | 10,41 m às 13:40 (platô de 1 leitura) | — | |
| Ilhota · 13/10/2023 | 13,31 m às 04:10 | — | |
| Ibirama · 07/10/2023 | 4,73 m às 17:50 | — | |
| Ituporanga · 26/12/2025 | 8,43 m às 14:40 (platô de 1 leitura) | — | |

**Brusque pede atenção.** A DCSC-00019 lê ~0,30 m ABAIXO dos números da Defesa Civil/imprensa nas
três cheias de 2023, com deslocamento quase constante (0,35 / 0,28 / 0,33). Em 07/09/2026 o par
DCSC-00019 = Ponte Estaiada foi provado com três leituras iguais (1,27 / 1,27 / 1,28). As duas coisas
só fecham se o datum da DCSC-00019 mudou entre 2023 e 2026, ou se os 8,96 de 2023 vieram de outra
leitura (régua manual) — e o 8,96 é a base das 357 cotas de rua da camada 2023. Pergunta para a
Defesa Civil de Brusque, não conclusão: **"o 8,96 m de 17/11/2023 foi lido na mesma estação que hoje
publica a Ponte Estaiada – DCSC, e houve ajuste de zero desde então?"**

## O que falta

- **Taió (DCSC-00041)**: retomar o download a partir de 2022-06-01 (a série de todos começa entre
  out/2022 e abr/2023; as janelas de 1980 a 2022 vêm vazias e só custam tempo).
- **As outras estações da cadeia** que o `coleta_nivel_sc.CADEIA` lista e não vieram, em ordem de
  valor: 00032 Lontras, 00023 Timbó, 00011 Rio dos Cedros, 00040 Barragem Oeste, 00038 Barragem Sul,
  00025 Agrolândia, 00033 Pouso Redondo, 00031 Laurentino, 00001 Agronômica, 00043 Presidente
  Getúlio, 00021 José Boiteux, 00004 Benedito Novo, 00028 Doutor Pedrinho, 00007 Pomerode, 00027
  Botuverá-2, 00163 Ilhota Arraial dos Cunhas. Também a partir de 2022-06-01.
- **O script de download** entra no repo (`scripts/`), com a query e a allowlist documentadas em
  `docs/API-DCSC-CAMPOS-NOVOS.md`.
- **Onde as séries moram**: na VPS, em `data/series/dcsc/`, regeradas por este script a partir dos
  zips; o repo guarda só o resumo. Cruzar com `data/tempo-real/*.ndjson` da nossa coleta (mesma rede,
  mesmo fuso) fecha a série de 2026 sem buraco.
