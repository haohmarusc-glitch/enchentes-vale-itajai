# A Salseiro pelo portal de Brusque — oito anos de 15 em 15 minutos, e o primeiro trânsito com hora

**08/09/2026.** O Jefferson baixou pelo botão *histórico* da página
`defesacivil.brusque.sc.gov.br/estacao/ver/31` (SALSEIRO — Vidal Ramos, fonte
declarada ANA, estação 83892990), em janelas de um ano, **dez arquivos `.xls`**
que são HTML. Verbatim, com nomes originais, em
`data/brutos/brusque-dc-salseiro-31-historico-2018-2026.tar.gz` (760 KB; 20 MB
abertos). Leitor: `scripts/analisar_salseiro_brusque.py`.

| | |
|---|---|
| cobertura | **22/05/2018 → 18/04/2026**, 226.910 carimbos |
| passo | 15 min (223.871 de 226.909 intervalos) |
| com valor | 115.494 (**51%**) — o resto é `0,00` |
| máximo | **4,83 m em 17/11/2023 13:30** |
| colunas | `historico` e `manual` são sempre 0; `chuva` tem 1 valor em 226.910. Na prática, só `cota` existe |
| arquivo `_2` | 233 bytes, só cabeçalho: é o mesmo vazio do #233 — a estação **parou em 18/04/2026 10:00**, exatamente a última leitura que a página mostra em verde |

## ⚠️ A armadilha: `0,00` é leitura ausente, não rio seco

Na primeira linha do arquivo: `1,20 → 0,00 → 0,00 → 0,00 → 0,00 → 1,19`. O Mirim
não secou e voltou em uma hora. **Entre 40% e 57% das linhas de cada arquivo
são zero.** Um `min()` ingênuo diria que o rio seca toda semana; uma média
ingênua entregaria metade do nível. No leitor, zero vira `None`, com teste que
usa exatamente essa primeira linha.

Há **156 buracos de pelo menos um dia**; o maior tem **35 dias** (30/04 →
05/06/2020). Isso importa para o que vem abaixo.

## O que esta estação é — e não é

A SALSEIRO **não é a régua de Vidal Ramos**: 6,8 km da sede, e a diferença
contra a nossa régua foi **medida em 0,70 m** (#233). Está em
`codigo_ana_nao_e`, e o 4,83 m de 2023 **não** é nível de Vidal Ramos.

**Mas para tempo de trânsito o que importa é a hora do pico, não o metro.** O
Jefferson apontou isso, e é o ponto mais forte da fonte: como **relógio a
montante do Mirim**, a Salseiro vale — e é a primeira série do projeto com
resolução de minutos. A ANA, no mesmo dia, provou entregar só dia.

## O primeiro par com hora nas duas pontas

`enchentes.json` tem **dois** registros com `hora`, ambos de Brusque. Cruzando:

| pico de Brusque | Salseiro na janela anterior | trânsito |
|---|---|---|
| **15/12/2020 20:45**, 4,95 m | **2,73 m às 13:15** | **7,5 h** |
| 23/06/2022 00:45, 5,46 m | **sem leitura nenhuma** na janela | — |

**7,5 h é teto plausível, não medida fechada:** 57% da janela de 48 h anterior
ao pico de Brusque está ausente na Salseiro. O 2,73 m é o maior valor que
**sobreviveu**; pode haver um maior dentro de um buraco, e aí o trânsito real
seria menor. E é **um** evento — `calibrar_transito.py` exige três, entre duas
*cidades* de `enchentes.json`, e a Salseiro não é cidade.

Por isso o registro foi para `transito.json._meta.medicoes`, com as ressalvas
por extenso, e **não** para `horas_min/horas_max`. O elo Brusque → Itajaí
continua 6–6 h, confiança baixa, como estava.

## O segundo par está a uma pergunta de distância

| data | Brusque (base) | Salseiro | falta |
|---|---|---|---|
| **17/11/2023** | **8,96 m**, sem hora | **4,83 m às 13:30** — acima da *emergência* da própria Salseiro (4,50) | a **hora** do pico em Brusque |
| 13/10/2023 | 6,91 m, sem hora | 29/10 3,47 m — data não bate | conferir a data de Brusque |

A hora de Brusque em 17/11/2023 deve estar em boletim da Defesa Civil de
Brusque ou na imprensa daquele dia. Com ela, o projeto passa a ter **dois**
pares; com o terceiro, `calibrar_transito.py` finalmente tem o que calibrar.

## Um bug meu, achado por esta fonte

O auditor (`auditar_lacunas.py`) contava hora procurando `":"` no campo
`data` — que é ISO e nunca tem dois-pontos. O resultado era **0 por
construção**. Repeti "196 picos, zero com hora" o dia inteiro em cima disso.
Eram **2**, e é o campo `hora` (que `calibrar_transito.py` já lia certo).
Corrigido; a auditoria regenerada diz 2.

## O que esta fonte NÃO resolve

- **A cheia de 31/08–01/09/2026**, a que o projeto mais estudou hoje: a estação
  parou em 18/04/2026. Não há Salseiro para ela.
- **Nível de Vidal Ramos.** Nunca.
- **Os elos vidal-ramos → botuvera e botuvera → brusque** continuam sem fonte:
  este par pula Botuverá e Guabiruba. As estações **18** (Botuverá) e **4**
  (Ponte Estaiada) do mesmo portal, baixadas do mesmo jeito, fechariam a
  cadeia — com a Ponte Estaiada tendo o par com a nossa leitura **provado** em
  07/09/2026.

## Adendo de 09/09/2026 — o máximo do portal era um sobrevivente

A série telemétrica da **ANA** para a mesma estação (83892990, `sonda_ana_api.py --gravar`,
bruto na VPS) tem **668 de 672 leituras** na semana de 11 a 17/11/2023 e põe a crista em
**5,23 m às 09:15 de 17/11**. O portal de Brusque está **em branco de 16/11 18:00 a 17/11
13:00** (19 h: a subida e a crista); os **4,83 m às 13:30** da tabela acima são o primeiro
valor que sobreviveu, já na descida. Onde as duas séries se sobrepõem, batem (portal 3,83 m
às 22:00; ANA 3,76 m às 23:00). O "máximo" desta fonte passa a ser lido como **máximo
sobrevivente**, não crista. Detalhe e próxima rodada em `docs/ANA-API-2026-09-08.md`.
Para o par de 15/12/2020, a janela da ANA (`--data 2020-12-15`) pode preencher os 57 % de
buraco e fechar a hora do pico a montante.
