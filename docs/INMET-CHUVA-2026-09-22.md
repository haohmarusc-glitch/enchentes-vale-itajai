# Chuva horária do INMET, 2006–2026: os três arquivos do Jefferson, conferidos (22/09/2026)

No mesmo dia em que a LAI C8 foi respondida (`docs/LAI-INMET-2026-09-22.md`), o Jefferson
baixou do portal do INMET (portal.inmet.gov.br/dadoshistoricos) a precipitação horária das
**quatro** estações automáticas que o INMET conta na bacia — A817 Indaial, A861 Rio do Campo,
A863 Ituporanga, A868 Itajaí — e entregou três arquivos: a horária, uma diária derivada e um
JSON de acumulados por evento do Atlas de Desastres. Este documento diz o que são, o que foi
conferido aqui, e o que eles respondem.

**Nada entrou em `enchentes.json`, `estacoes.json` ou `transito.json`.** Chuva é contexto:
nunca cota, nunca aviso. O que muda é que duas pendências ganham medida em vez de relato.

## Os arquivos

| arquivo em `data/brutos/` | tamanho | conteúdo |
|---|---|---|
| `inmet-chuva-horaria-2006-2026.csv.gz` | 1,7 MB (18,4 MB aberto), 642 716 linhas | `codigo,ts_utc,prec_mm,suspeito` — uma linha por estação e hora, carimbo UTC, `prec_mm` vazio = sem dado |
| `inmet-chuva-diaria-2006-2026.csv` | 616 KB, 26 787 linhas | `codigo,data_local,prec_mm,horas_validas` — dia em UTC−3 fixo |
| `inmet-chuva-eventos-atlas-2026-09-22.json` | 247 KB | 124 eventos (chave `rio-ano-mês`), 81 com dado; por evento: 24 h, 72 h, 7 d, 30 d, máximo horário em 7 d, e o mesmo por registro do Atlas (72 h, 7 d) |

sha256 dos arquivos como chegaram (a horária, descomprimida):

```
efca320ca4fca5a5dc75f624788874672332465c6f0b26c9dd8388c8ade9b5be  chuva_eventos_atlas.json
c9163d5f1c60c03ea1aee930ae0d7cc12e45bad70f6f17a5792353eb4841492b  inmet_chuva_diaria_2006_2026.csv
dc9cf40c0fc823c2676f4fe0f631fbe60ea78f547018032ba4a12dec0fe78082  inmet_chuva_horaria_2006_2026.csv
```

A horária foi comprimida aqui (`gzip -9`) porque 18 MB é três vezes o maior arquivo do
repositório; o hash acima é o do conteúdo, e `zcat … | sha256sum` o reproduz.

Fonte, nas palavras da LAI: dados **brutos, não consistidos**; o INMET isola dado suspeito
antes de publicar e não põe flag; falha vem como `9999`, `Null` ou branco. A coluna
`suspeito` é marcação do **Jefferson**, não do INMET (ver abaixo).

## O que foi conferido aqui, e como

`scripts/inmet_chuva.py` lê a horária e recalcula os outros dois; `scripts/teste_inmet_chuva.py`
trava os números deste documento (23 testes). Resultado de `python3 inmet_chuva.py --conferir`:

- **Diária: 26 787 linhas iguais, 0 diferentes.** Regra que reproduz: dia local = `ts_utc − 3 h`,
  fixo; hora com `suspeito ≠ 0` descartada. Sem descartar as suspeitas, 573 linhas diferem
  (só na contagem de horas válidas, nunca no volume).
- **JSON de eventos: 1 054 valores iguais em milímetros E em cobertura, 0 diferentes;** os 26
  `null` do JSON são janelas com cobertura zero, e aqui também dão vazio. Janela: termina às
  00h local do dia seguinte à `data_ancora`, `[fim − N h, fim)`.
- **`suspeito` é uma regra, e a regra se recalcula:** todas as horas marcadas são `0,0`, e são
  exatamente os zeros que pertencem a uma sequência de zeros que se estende por ≥ 20 dias
  (hora sem dado no meio não quebra a sequência). É o retrato de pluviômetro entupido ou
  parado, que o INMET publica como zero. `zeros_travados()` reconstrói a marca e o teste
  exige igualdade nas quatro estações. Horas marcadas: A817 472, A861 8 776, A863 179, A868 1 058.
- **Protocolos do Atlas:** o JSON cita 245 registros (o recorte de 21/09,
  `data/brutos/atlas-desastres-recorte-itajai-acu-2026-09-21.json`); **238** estão na base
  canônica `data/desastres/eventos.json` e **7 não** — todos de **Ibirama** (IBGE 4206900), que a
  base canônica de 20 municípios não inclui (`atlas_desastres.py` anota o código como "ainda
  não conferido aqui"). Não é erro do JSON: é um município a mais no recorte de 21/09.

Convenções que ficam ditas, porque o código as assume:

- **Sem horário de verão.** Santa Catarina teve horário de verão até 2019 (out–fev). Os três
  arquivos usam UTC−3 fixo, e o script também, para reproduzi-los. Nesses meses, "00h local"
  está 1 h deslocado. Para acumulados de dias, é ruído; para "hora do máximo", é 1 h.
- **Cobertura junto do número.** Acumulado ignora hora sem dado e por isso **subestima**
  quando a cobertura é < 1. Nenhum número abaixo vai sem a cobertura.
- **A âncora do evento é a data com mais registros no mês, não a data da chuva.** Decreto
  vem depois da água. Exemplo: `itajai-acu-2011-09` ancora em 12/09 e dá **72 h = 0,2 mm** com
  **7 d = 217 mm** em Indaial — a chuva foi de 7 a 9/09. Para ler um evento, use `7d` ou o
  bloco `por_registro`, nunca `24h`/`72h` do evento sozinhos.

## Estado das estações, lido dos dados

| estação | primeiro dado | último dado válido | anos ruins (cobertura) |
|---|---|---|---|
| A817 Indaial | 02/07/2006 15:00Z | **31/05/2025 23:00Z** | 2021 0,50 · 2022 0,17 · 2025 0,19 · 2026 0 |
| A861 Rio do Campo | 11/03/2008 14:00Z | 31/08/2025 23:00Z | 2008 0,58 · 2009 0,27 · 2011 0,45 · 2020 0,41 · 2022 0,33 · 2026 0 |
| A863 Ituporanga | 05/03/2008 20:00Z | 31/08/2026 23:00Z | 2021 0,23 |
| A868 Itajaí | 25/06/2010 18:00Z | 31/08/2026 23:00Z | 2021 0,00 |

- A "Pane" que a LAI declara para Indaial começa, nos dados, em **junho de 2025**. Antes disso a
  estação já tinha dois anos quase mudos (2021–2022).
- **Rio do Campo é a estação menos confiável**: 8 776 horas de zero travado, e cobertura abaixo
  de 0,5 em cinco anos. Nos eventos de out/2023, nov/2023 e jan/2024 ela não tem hora válida.
- **2021 é um ano cego** em três das quatro (Itajaí zero, Ituporanga 0,23, Indaial 0,50).
- Nenhuma delas fica em Blumenau, Rio do Sul, Gaspar, Brusque ou no Mirim. O INMET mede
  cabeceiras (Ituporanga no Itajaí do Sul, Rio do Campo no Itajaí do Oeste), o médio vale em
  Indaial (parado) e a foz.

## Novembro de 2008: a pendência do JICA ganha medida

O relatório de 2008 (`docs/ANALISE-2008-ITAJAI.md`) atribui ao JICA **236 mm em quatro dias
na sub-bacia do Itajaí-Açu** (21–24/11) e 160 mm na do Mirim; a auditoria do JICA feita aqui
(`docs/AUDITORIA-JICA-2011.md`) leu do mesmo estudo **121–144 mm de média de bacia em 4 dias**
e **575–576 mm em Blumenau**. Ficou como "não é a mesma grandeza". Agora há medida:

| janela (hora local) | A817 Indaial | A863 Ituporanga | A861 Rio do Campo |
|---|---|---|---|
| 21–24/11 (4 dias) | **246,6 mm** (cob 1,00) | 46,4 mm (1,00) | sem dado |
| 20–24/11 (5 dias) | 259,8 mm (1,00) | 46,6 mm (1,00) | sem dado |
| 23/11 (o maior dia) | **145,2 mm** (1,00) | — | — |
| novembro inteiro | **567,4 mm** (1,00) | 188,8 mm (1,00) | 0,2 mm (1 h válida em 720) |

Indaial, dia a dia, 19–26/11: 24,0 · 13,2 · 23,0 · 53,2 · **145,2** · 25,2 · 27,2 · 14,6 mm.
Máximo horário da semana: 17,2 mm às 09h de 23/11.

Leitura, sem fechar a pendência:

1. **Os 236 mm do JICA para a sub-bacia do Açu são compatíveis com um ponto do médio vale**:
   Indaial deu 246,6 mm nos mesmos quatro dias, a 20 km de Blumenau.
2. **Os 121–144 mm de "média de bacia" também são compatíveis** com uma bacia em que a
   cabeceira ficou quase seca: Ituporanga teve 46 mm nos quatro dias. Média de bacia dilui.
3. **Os 575 mm em Blumenau são 2,3 vezes Indaial.** A chuva foi litorânea e concentrada; o
   relatório de 2008 diz que Blumenau passou de 1 000 mm no mês, e Indaial fechou em 567.
4. Logo os dois números do JICA **deixam de parecer contraditórios**: um é ponto ou sub-bacia
   do médio vale, o outro é média da bacia inteira. O que continua em aberto é **qual área e
   qual janela o JICA usou para cada um**, e isso só a releitura do estudo resolve. A pendência
   fica, com âncoras medidas.

A861 não ajuda em 2008: instalada em março, praticamente não transmitiu no ano (cobertura 0,58,
e em novembro 1 hora válida). A868 Itajaí não existia (junho de 2010).

## Rio do Sul: o `chuva_mm` da tabela municipal contra o INMET

A tabela municipal de Rio do Sul dá `chuva_mm` e `dias_de_chuva` por pico sem dizer onde mediu.
Desde março de 2008 há 17 registros com o campo; 15 só têm o mês. Para os dois com dia, a
janela é `dias_de_chuva` (mínimo 3) até o dia do pico; para os outros, o mês inteiro — que é
sempre MAIOR que o volume do evento, por construção.

| pico | nível | `chuva_mm` (dias) | janela | A863 Ituporanga | A817 Indaial |
|---|---|---|---|---|---|
| 2009-09 | 8,55 | 292,0 (13) | mês | 313,0 (1,00) | 272,0 (1,00) |
| 2010-04 | 7,53 | 254,0 (7) | mês | 173,0 (1,00) | 245,0 (1,00) |
| 2011-07 | 6,50 | 72,2 (3) | mês | 229,4 (1,00) | 198,6 (1,00) |
| 2011-08 | 8,83 | 143,4 (5) | mês | 318,0 (1,00) | 319,2 (1,00) |
| 2014-06 | 9,42 | 152,6 (6) | mês | 238,2 (1,00) | sem dado (0,02) |
| 2014-10 | 8,16 | 147,4 (8) | mês | 129,6 (1,00) | 58,6 (1,00) |
| 2015-09 | 7,23 | 70,4 (2) | mês | 308,0 (1,00) | 148,4 (0,93) |
| 2016-10 | 6,68 | 131,0 (4) | mês | 212,2 (1,00) | 216,6 (0,99) |
| 2018-05 | 7,55 | 114,6 (4) | mês | 29,0 (1,00) | 39,2 (1,00) |
| 2019-12 | 6,89 | 85,6 (1) | mês | 57,0 (1,00) | 83,4 (0,95) |
| 2020-09 | 6,46 | 50,2 (1) | mês | 118,6 (1,00) | 51,6 (1,00) |
| 2022-05 | 9,34 | 165,0 (2) | mês | 250,6 (1,00) | sem dado |
| 2022-06 | 6,72 | 84,2 (3) | mês | 174,0 (1,00) | sem dado |
| 2022-10 | 7,47 | 76,8 (3) | mês | 273,2 (1,00) | 7,2 (0,08) |
| 2023-07 | 7,30 | 92,2 (3) | mês | 149,0 (1,00) | 142,4 (1,00) |
| 2024-05-18 | 8,97 | 175,4 (3) | 3 d até 18/05 | 102,6 (1,00) | 77,6 (1,00) |
| 2024-07-12 | 7,49 | 51,4 (2) | 3 d até 12/07 | 48,2 (0,82) | 55,0 (1,00) |

Leitura:

- **Nenhuma contradição.** O volume municipal fica sempre na mesma ordem de grandeza do que
  as cabeceiras mediram, e quase sempre abaixo do mês inteiro, como deve.
- Onde a janela é comparável, bate: **jul/2024, 51,4 × 48,2 mm** (Ituporanga, 3 dias);
  **abr/2010, 254 × 245** (Indaial, mês, com 7 dias de chuva declarados); **out/2014, 147 × 130**.
- **Mai/2018 é o caso a olhar**: 114,6 mm em 4 dias na tabela municipal, contra 29 e 39 mm no
  mês inteiro nas duas estações do INMET. Ou choveu em Rio do Sul o que não choveu em
  Ituporanga nem em Indaial, ou a linha da tabela tem outro mês. Não é erro provado; é a
  única linha em que o INMET não sustenta a ordem de grandeza.
- **Mai/2024: 175 mm em 3 dias na tabela, 103 mm em Ituporanga** — o pluviômetro municipal
  mediu mais que a cabeceira; plausível para chuva do médio Alto Vale.
- O campo **continua da fonte municipal**, com a fonte municipal. Isto foi conferência de
  plausibilidade, não substituição: instrumento diferente, lugar diferente, janela diferente.

## Os maiores acumulados de sete dias, contra as cristas do cadastro

Sete dias terminando na âncora do evento; só janelas com cobertura ≥ 0,9. Picos do cadastro no
mesmo mês (cada cidade na própria régua; Blumenau na referência que o registro traz).

**A817 Indaial**

| 7 d | 72 h | evento | picos no mês |
|---|---|---|---|
| 259,0 | 221,4 | mirim-2008-11 (âncora 23/11) | Blumenau 11,52 · Brusque 8,5 · Indaial 5,04 |
| 223,8 | 127,0 | acu-2010-04 | Blumenau 8,46 · Rio do Sul 7,53 |
| 218,6 | 162,8 | mirim-2011-09 (09/09) | Blumenau 11,60/12,80 · Rio do Sul 12,96 · Brusque 10,03 · Indaial 7,76 |
| 217,6 | 120,2 | acu-2023-10 | Blumenau 10,61 · Rio do Sul 11,86 · Brusque 6,91 |
| 192,4 | 111,0 | acu-2018-03 | nenhum |
| 178,4 | 103,4 | acu-2010-01 | nenhum |
| 175,4 | 22,0 | acu-2021-01 | Blumenau 6,82 · Brusque 4,82 |
| 167,0 | 93,0 | acu-2017-06 | Blumenau 8,71 · Rio do Sul 10,89 |

**A863 Ituporanga**

| 7 d | 72 h | evento | picos no mês |
|---|---|---|---|
| 220,0 | 118,4 | mirim-2013-09 | Blumenau 10,51 · Rio do Sul 10,39 · Indaial 6,46 |
| 207,8 | 165,8 | mirim-2011-09 (09/09) | (set/2011, acima) |
| 202,2 | 184,0 | acu-2022-05 | Blumenau 9,41 · Rio do Sul 9,34 · Indaial 6,0 |
| 197,0 | 14,8 | mirim-2018-01 | nenhum |
| 168,8 | 72,2 | acu-2010-04 | Blumenau 8,46 · Rio do Sul 7,53 |
| 137,6 | 69,4 | acu-2020-12 | Brusque 4,95/5,3 |
| 133,8 | 109,8 | acu-2024-05 | Blumenau 8,67 · Rio do Sul 8,97 · Brusque 7,58 |
| 130,6 | 113,6 | acu-2009-09 | Rio do Sul 8,55 |

**A868 Itajaí**

| 7 d | 72 h | evento | picos no mês |
|---|---|---|---|
| 212,6 | 171,2 | mirim-2011-09 (09/09) | (set/2011, acima) |
| 173,6 | 23,4 | acu-2020-02 | nenhum |
| 170,8 | 2,4 | acu-2014-06 | Blumenau 10,18 · Rio do Sul 9,42 |
| 168,8 | 164,2 | acu-2025-01 | nenhum |
| 166,6 | 103,0 | acu-2017-06 | Blumenau 8,71 · Rio do Sul 10,89 |
| 166,0 | 81,0 | acu-2018-03 | nenhum |
| 141,2 | 140,4 | acu-2022-11 | nenhum |
| 128,0 | 91,0 | acu-2016-03 | nenhum |

O que estas tabelas dizem, e o que não dizem: **chuva alta sem pico no cadastro** (mar/2018,
jan/2010, jan/2025, nov/2022) é ou lacuna do cadastro ou chuva que não virou cheia — a tabela
não distingue, e o Atlas registrou decreto nos quatro casos. **Nov/2023**, a maior cheia
recente de Rio do Sul, não aparece em Indaial (88 mm em 7 d) e aparece em Ituporanga com
**276 mm em 13–18/11** (cobertura 0,89, fora do corte da tabela): a chuva foi de cabeceira, e
Rio do Sul recebeu o que Ituporanga mediu. Em out/2023 Ituporanga **não tem dado** e Indaial
tem 218 mm — a cheia que subiu 11,86 m em Rio do Sul não tem a cabeceira medida pelo INMET.

## O que não entra, e o que pode vir depois

- Nada em `enchentes.json`. Se um dia o Jefferson quiser um campo de chuva medida ao lado do
  `chuva_mm` municipal, ele nasce com estação, janela e cobertura no nome — nunca como
  substituto, e por decisão dele.
- O INMET **não entra no tempo real** (LAI C8: API só com ACT), e estes arquivos param em
  31/08/2026. São histórico.
- Uso do script: `python3 scripts/inmet_chuva.py --conferir` (reproduz tudo),
  `--estado` (último dado válido e cobertura por ano),
  `--acumulado A817 2008-11-25T00:00 --horas 24 96 720` (uma janela qualquer, hora de Brasília).
