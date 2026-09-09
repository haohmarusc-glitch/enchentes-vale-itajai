# Ituporanga — Itajaí do Sul (Ponte Vitório Sens)

**Prefeitura / Defesa Civil:** https://ituporanga.sc.gov.br/secretaria/view/15/defesa-civil
**Coordenador:** Elias Sieves · (47) 9148-1378 · 199
**Estação no monitor:** DCSC-00039 (datum estadual bruto, `usar_para_cota: false`)
**Régua municipal:** Ponte Vitório Sens (leitura diária compartilhada com a estadual)
**Consulta:** 8 e 9 de setembro de 2026
**Emergência:** 199. Este arquivo não substitui aviso oficial.

## Por que `cotas_m` está vazio

A SPDC/SC publica atenção > 1,40 / alerta > 1,90 / emergência > 2,60 m para
Ituporanga, mas para a estação **83250000** (ANA/EPAGRI), a 9,6 km — outra régua.
A tela lê a DCSC-00039. Ver `cotas_m_por_que_vazio` em `estacoes.json`.

## Ferramentas de 2026 (Google My Maps), lidas em 08/09/2026

| Mapa | `mid` | O que traz | Ressalva |
|---|---|---|---|
| Cotas de cheias ruas (Prefeitura, 07/10/2023) | `1o9xZ2BceCkPzaqQQ2m0HIn0ixHVOJcU` | 60 pontos, 3,38 a 10,48 m | um ponto de 27,77 m é lixo |
| Cotas com Manchas de Inundação | `19tpP2Tfsl58ue6GtY5ihBfK3MLkiUrA` | 78.547 polígonos, COTA 3,00 a 6,50 de 0,5 em 0,5 m (34 MB) | linkado pela URL `/edit` — pode ser editável por qualquer um |

KML: `https://www.google.com/maps/d/kml?mid=<mid>&forcekml=1`. Snapshot congelado na VPS em
09/09/2026: ruas 20.145 bytes, sha256 `7094bb127dd76d0c…`; manchas 33.999.491 bytes, sha256
`38c4501c9c08242a…` (hashes completos em `docs/pendencias-navegador-e-oficios.md`, A3). Nenhum dos dois traz faixa de acionamento; as cotas de rua só
entram quando se souber a régua delas.

## O que os 60 pontos de cota de rua dizem (09/09/2026)

Transcrição em `data/brutos/ituporanga-mymaps-ruas-2026-09-09-transcricao.tsv`;
análise em `scripts/analisar_ruas_ituporanga.py` (não grava nada).

| Pergunta | Resposta |
|---|---|
| Quantos pontos | 60; **59** são cota de rio plausível |
| Lixo | "Prefeitura Garagem" = **27,77 m** — digitação ou altitude na coluna errada. Avisar a DC |
| Faixa | **3,38 a 10,48 m**, mediana 5,64 |
| Acima do teto do mapa de manchas (6,50 m) | **22 pontos** — para essas ruas há cota e não há mancha |
| Os 3,25 m do secretário | ficam **abaixo da menor cota de rua** (3,38 m) e acima da primeira mancha (3,00 m) |
| Perímetro | todos a menos de 5 km do centroide: uma cidade só |
| Outro curso d'água | um ponto cita a **Ponte do Rio Gabiroba** (5,03 m) — mesma régua? a fonte não diz |

Nada disso entra em `cotas-ruas.json`: a régua não está nomeada (provavelmente a
Ponte Vitório Sens) e a leitura ao vivo é a DCSC-00039, em outro datum. Com a
régua e o zero ditos pela Defesa Civil, a importação é meia hora.

## Segunda rodada (09/09/2026)

- A escala estadual **1,40 / 1,90 / 2,60 m** (estação **83250000**, ANA/EPAGRI) ganhou fonte citável:
  Defesa Civil de SC, *Operação de Barragens* (out/2024),
  https://www.defesacivil.sc.gov.br/wp-content/uploads/2024/10/Operacao-de-Barragens.pdf.
  Não muda nada: é a mesma escala de **outra** régua, já recusada.
- **Página municipal "Nível do Rio":** https://www.ituporanga.sc.gov.br/nivel-rio. Se for a leitura da
  Ponte Vitório Sens, e se as 59 cotas de rua forem dessa régua, as duas **pareiam sem precisar do
  zero** — o zero só importa entre réguas diferentes. Teste: abrir, salvar o HTML, ver que régua nomeia.
- Notícia 4935: estação **meteorológica** instalada na Ponte Vitório Sens — história do ponto, não nível.
- Abertos: zero da régua da ponte; se a Ponte do Rio Gabiroba (5,03 m) está na mesma régua das outras 58.

## Página municipal `nivel-rio`, lida em 09/09/2026

"Rio Itajaí do Sul — Nível do Rio (Centro): **1,46 m**", última leitura 09/09/2026 07:00.
"Centro" é bairro, não régua: parear com as 60 cotas de rua seria vínculo por nome de lugar, a
armadilha do Salseiro. **Não pareia.** E com 1,46 m a página exibe "Nível de Criticidade:
Atenção", enquanto as manchas começam em 3,00 m e a menor cota de rua é 3,38 m. Ou o rótulo está
travado no HTML, ou é de outra escala. Hipótese (não conclusão): 1,46 ≥ 1,40, a atenção da escala
**estadual** da 83250000 — a página pode aplicar a escala estadual ao "Centro", ou o "Centro" pode
ser a própria 83250000. Terceira escala de Ituporanga sem régua nomeada: **não adotar nenhuma.**

O que a página dá de bom: **Download CSV com 8.433 registros**, duas leituras por dia (07:00 e
17:00), ~11 anos — a baixar para `data/brutos/` e cruzar com Rio do Sul —, e o log completo da
Barragem Sul com comportas. Cadência: a 2×/dia, com `MIN_VELHA` de 180 min, a cidade pintaria por
poucos minutos e ficaria cinza o resto do dia.

### Barragem Sul: o log fecha a divergência de ontem, e acha um erro

Montante **17 m às 07:00 de 08/09** e **15 m às 17:00** do mesmo dia: o reservatório esvaziava
~2 m/dia com as 5 comportas abertas. Os 15,00 da Asthon e os 17,73 do feed estadual são a **mesma
régua em horas diferentes**, com o feed estadual atrasado — não são três datums. Mas o registro de
**09/09 07:00 marca montante 3 m** depois de 15 m: queda de 12 m numa noite é erro de digitação.
Vale avisar Ituporanga.

## Pistas que se cercam (nenhuma é faixa)

- primeira mancha: 3,00 m
- menor cota de rua: 3,38 m
- "primeira cota considerada crítica para alagamentos": 3,25 m, na região da
  antiga Lanchonete São Jorge (secretário de Planejamento Vilmar Schwambach,
  Rádio Educadora 90.3)

Pedir à Defesa Civil a tabela atenção/alerta/emergência amarrada à Ponte
Vitório Sens e o zero da régua.
