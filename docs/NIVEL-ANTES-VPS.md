# Nível das réguas N horas antes de cada crista e de cada rua alagada registrada

Gerado por `scripts/nivel_antes.py --relatorio` (somente leitura). **Descritivo, não previsão nem
calibração.** Cada régua tem o seu zero: os números estão lado a lado, cada um na sua régua, e não se
comparam entre si. Só aparecem as réguas **a montante** no mesmo rio. Séries da ANA (2020–2023) só se
cruzam com séries da ANA, porque o fuso delas não foi conferido. Crista de réguas de Itajaí que sentem a
maré: máximo da média de 12,42 h (um ciclo de maré); a leitura mostrada é a do instante. Só entram como
alvo as réguas de cidades cadastradas em `data/estacoes.json`.

**Série usada:** além das séries de `data/brutos/`, a série inteira que o coletor guardou na VPS (30/08 a 05/10/2026), lida do branch `arquivo-series`, commit `54cf3b1` (cópia de 05/10/2026, 18:38 UTC). Para refazer: `git fetch origin arquivo-series && git archive FETCH_HEAD tempo-real | tar -x -C /tmp/s && python3 scripts/nivel_antes.py --series /tmp/s/tempo-real --relatorio docs/NIVEL-ANTES-VPS.md --origem ...`. As publicações 'Brusque' e 'Rio do Sul Estação MKS' vinham da página antiga de Itajaí: conferidas contra a DCSC-00019 (crista de 12/09: 01:55 × 02:01, 4,62 m nas duas) e a Asthon (01/09: 05:45 × 05:21), sem o atraso de 3 h da publicação 'Blumenau', que fica de fora.

## Ruas alagadas registradas à mão

Nenhum registro ainda em `data/ruas-alagadas.json`. Como registrar durante a cheia:
`docs/REGISTRO-RUAS-ALAGADAS.md`.

## Cristas das réguas

### ANA 83800002 Blumenau — crista de 6,82 m

Referência: **21/jan/2021 22:15**, leitura 6,82 m na régua desta estação
(telemetria da ANA: fuso não conferido; as horas só se comparam entre séries da ANA)

- **ANA 83050000 Taió** (a montante): 3 h antes: 6,25 m · 6 h antes: 6,16 m · 12 h antes: 5,94 m; crista própria 6,90 m às 22/jan 15:45 (17,5 h depois)

### ANA 83800002 Blumenau — crista de 1,63 m

Referência: **30/abr/2022 16:45**, leitura 1,63 m na régua desta estação
(telemetria da ANA: fuso não conferido; as horas só se comparam entre séries da ANA)

- **ANA 83050000 Taió** (a montante): 3 h antes: 0,94 m · 6 h antes: 0,93 m · 12 h antes: 0,90 m

### ANA 83800002 Blumenau — crista de 9,40 m

Referência: **05/mai/2022 02:15**, leitura 9,40 m na régua desta estação
(telemetria da ANA: fuso não conferido; as horas só se comparam entre séries da ANA)

- **ANA 83050000 Taió** (a montante): 3 h antes: 9,40 m · 6 h antes: 9,26 m · 12 h antes: 8,74 m; crista própria 9,48 m às 05/mai 04:15 (2,0 h depois)

### ANA 83300200 Rio do Sul — crista de 13,14 m

Referência: **18/nov/2023 01:45**, leitura 13,14 m na régua desta estação
(telemetria da ANA: fuso não conferido; as horas só se comparam entre séries da ANA)

- **ANA 83050000 Taió** (a montante): 3 h antes: 10,31 m · 6 h antes: 10,30 m · 12 h antes: 10,13 m; crista própria 10,32 m às 17/nov 21:15 (4,5 h antes)

### DC-05 Rio Itajaí-Mirim (curso antigo) - Propriedade privada — crista de 2,60 m

Referência: **01/set/2026 06:10**, leitura 2,60 m na régua desta estação
(tábua da Marinha: preamar às 01/set 04:44, 0,98 m sobre o zero da carta náutica — não é régua de rio)

- **Asthon Vidal Ramos** (a montante): 3 h antes: 3,32 m · 6 h antes: 3,64 m · 12 h antes: 3,31 m; crista própria 3,87 m às 31/ago 22:30 (7,7 h antes)
- **Brusque** (a montante): 3 h antes: 4,43 m · 6 h antes: 4,46 m · 12 h antes: 3,29 m; crista própria 4,87 m às 01/set 09:45 (3,6 h depois)

### DC-03 Rio Itajaí-Mirim (canal retificado) - Captação SEMASA — crista de 1,67 m

Referência: **01/set/2026 08:30**, leitura 1,67 m na régua desta estação
(tábua da Marinha: baixa-mar às 01/set 11:51, 0,29 m sobre o zero da carta náutica — não é régua de rio)

- **Asthon Vidal Ramos** (a montante): 3 h antes: 3,16 m · 6 h antes: 3,38 m · 12 h antes: 3,48 m; crista própria 3,87 m às 31/ago 22:30 (10,0 h antes)
- **Brusque** (a montante): 3 h antes: 4,40 m · 6 h antes: 4,47 m · 12 h antes: 3,57 m; crista própria 4,87 m às 01/set 09:45 (1,2 h depois)

### Brusque — crista de 4,87 m

Referência: **01/set/2026 09:45**, leitura 4,87 m na régua desta estação

- **Asthon Vidal Ramos** (a montante): 3 h antes: 3,11 m · 6 h antes: 3,26 m · 12 h antes: 3,80 m; crista própria 3,87 m às 31/ago 22:30 (11,2 h antes)

### DC-04 Rio Itajaí-Mirim (canal retificado e curso antigo) - Vitalmar Pescados — crista de 1,17 m

Referência: **01/set/2026 10:00**, leitura 1,17 m na régua desta estação
(tábua da Marinha: baixa-mar às 01/set 11:51, 0,29 m sobre o zero da carta náutica — não é régua de rio)

- **Asthon Vidal Ramos** (a montante): 3 h antes: 3,09 m · 6 h antes: 3,24 m · 12 h antes: 3,85 m; crista própria 3,87 m às 31/ago 22:30 (11,5 h antes)
- **Brusque** (a montante): 3 h antes: 4,59 m · 6 h antes: 4,40 m · 12 h antes: 3,97 m; crista própria 4,87 m às 01/set 09:45 (0,2 h antes)

### DC-06 Rio Itajaí-Mirim (curso antigo) - Itamirim Clube de Campo — crista de 1,15 m

Referência: **01/set/2026 10:20**, leitura 1,15 m na régua desta estação
(tábua da Marinha: baixa-mar às 01/set 11:51, 0,29 m sobre o zero da carta náutica — não é régua de rio)

- **Asthon Vidal Ramos** (a montante): 3 h antes: 3,08 m · 6 h antes: 3,21 m · 12 h antes: 3,87 m; crista própria 3,87 m às 31/ago 22:30 (11,8 h antes)
- **Brusque** (a montante): 3 h antes: 4,62 m · 6 h antes: 4,38 m · 12 h antes: 4,04 m; crista própria 4,87 m às 01/set 09:45 (0,6 h antes)

### DC-10 Rio Itajaí-Mirim – Bairro Limoeiro — crista de 8,32 m

Referência: **01/set/2026 11:10**, leitura 8,32 m na régua desta estação
(tábua da Marinha: baixa-mar às 01/set 11:51, 0,29 m sobre o zero da carta náutica — não é régua de rio)

- **Asthon Vidal Ramos** (a montante): 3 h antes: 3,05 m · 6 h antes: 3,17 m · 12 h antes: 3,85 m; crista própria 3,87 m às 31/ago 22:30 (12,7 h antes)
- **Brusque** (a montante): 3 h antes: 4,76 m · 6 h antes: 4,38 m · 12 h antes: 4,29 m; crista própria 4,87 m às 01/set 09:45 (1,4 h antes)

### DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima) — crista de 4,01 m

Referência: **01/set/2026 12:30**, leitura 4,01 m na régua desta estação
(tábua da Marinha: baixa-mar às 01/set 11:51, 0,29 m sobre o zero da carta náutica — não é régua de rio)

- **Asthon Rio do Sul (Ponte Dom Tito Buss)** (a montante): 3 h antes: 6,65 m · 6 h antes: 6,77 m · 12 h antes: 6,45 m; crista própria 6,78 m às 01/set 05:21 (7,1 h antes)
- **Rio do Sul Estação MKS** (a montante): 3 h antes: 6,97 m · 6 h antes: 7,06 m · 12 h antes: 6,71 m; crista própria 7,06 m às 01/set 05:45 (6,8 h antes)
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 7,57 m · 6 h antes: sem leitura · 12 h antes: sem leitura

### DC-04 Rio Itajaí-Mirim (canal retificado e curso antigo) - Vitalmar Pescados — crista de 1,38 m

Referência: **06/set/2026 19:00**, leitura 1,38 m na régua desta estação
(tábua da Marinha: baixa-mar às 06/set 18:44, 0,40 m sobre o zero da carta náutica — não é régua de rio)

- **Asthon Vidal Ramos** (a montante): 3 h antes: 2,45 m · 6 h antes: 2,45 m · 12 h antes: 2,47 m
- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,44 m · 6 h antes: 2,45 m · 12 h antes: 2,47 m
- **Vidal Ramos (Asthon)** (a montante): 3 h antes: 2,45 m · 6 h antes: 2,44 m · 12 h antes: 2,47 m
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 2,79 m · 6 h antes: 2,81 m · 12 h antes: 2,83 m
- **Brusque** (a montante): 3 h antes: 1,33 m · 6 h antes: 1,34 m · 12 h antes: 1,36 m
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 1,34 m · 6 h antes: 1,34 m · 12 h antes: 1,36 m

### DCSC-00018 SDC-SC Botuverá 1 — crista de 5,44 m

Referência: **11/set/2026 19:16**, leitura 5,44 m na régua desta estação

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 3,34 m · 6 h antes: 3,16 m · 12 h antes: 2,71 m; crista própria 3,41 m às 11/set 14:31 (4,8 h antes)
- **Vidal Ramos (Asthon)** (a montante): 3 h antes: sem leitura · 6 h antes: 2,94 m · 12 h antes: 2,74 m; crista própria 3,38 m às 11/set 15:06 (4,2 h antes) — na borda dos dados

### DCSC-00013 SDC-SC Rio do Sul — crista de 6,05 m

Referência: **11/set/2026 23:31**, leitura 6,05 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,13 m · 6 h antes: 1,21 m · 12 h antes: sem leitura
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,19 m · 6 h antes: 5,23 m · 12 h antes: sem leitura; crista própria 6,95 m às 12/set 04:46 (5,3 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,15 m · 6 h antes: 5,18 m · 12 h antes: 2,92 m; crista própria 6,95 m às 12/set 04:13 (4,7 h depois)

### Rio do Sul, Ponte Dom Tito Buss (Asthon) — crista de 5,89 m

Referência: **11/set/2026 23:42**, leitura 5,89 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,13 m · 6 h antes: 1,21 m · 12 h antes: sem leitura
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,26 m · 6 h antes: 5,32 m · 12 h antes: sem leitura; crista própria 6,95 m às 12/set 04:46 (5,1 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,22 m · 6 h antes: 5,27 m · 12 h antes: 2,96 m; crista própria 6,95 m às 12/set 04:13 (4,5 h depois)

### DCSC-00003 SDC-SC Ascurra — crista de 10,46 m

Referência: **11/set/2026 23:46**, leitura 10,46 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,13 m · 6 h antes: 1,21 m · 12 h antes: sem leitura
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,26 m · 6 h antes: 5,32 m · 12 h antes: sem leitura; crista própria 6,95 m às 12/set 04:46 (5,0 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,22 m · 6 h antes: 5,27 m · 12 h antes: 2,96 m; crista própria 6,95 m às 12/set 04:13 (4,4 h depois)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 5,94 m · 6 h antes: 5,48 m · 12 h antes: 4,07 m; crista própria 6,05 m às 11/set 23:31 (0,2 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 5,76 m · 6 h antes: 5,32 m · 12 h antes: 3,93 m; crista própria 5,89 m às 11/set 23:42 (0,1 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 5,16 m · 6 h antes: 4,73 m · 12 h antes: 3,78 m; crista própria 6,00 m às 12/set 08:46 (9,0 h depois)

### DCSC-00006 SDC-SC Indaial — crista de 7,61 m

Referência: **12/set/2026 00:46**, leitura 7,61 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,11 m · 6 h antes: 1,18 m · 12 h antes: 1,19 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,46 m · 6 h antes: 5,69 m · 12 h antes: 3,20 m; crista própria 6,95 m às 12/set 04:46 (4,0 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,43 m · 6 h antes: 5,63 m · 12 h antes: 3,14 m; crista própria 6,95 m às 12/set 04:13 (3,4 h depois)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,01 m · 6 h antes: 5,69 m · 12 h antes: 4,28 m; crista própria 6,05 m às 11/set 23:31 (1,3 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 5,84 m · 6 h antes: 5,52 m · 12 h antes: 4,12 m; crista própria 5,89 m às 11/set 23:42 (1,1 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 5,28 m · 6 h antes: 4,88 m · 12 h antes: 4,17 m; crista própria 6,00 m às 12/set 08:46 (8,0 h depois)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 10,35 m · 6 h antes: 9,94 m · 12 h antes: 7,57 m; crista própria 10,46 m às 11/set 23:46 (1,0 h antes)

### Brusque — crista de 4,62 m

Referência: **12/set/2026 01:55**, leitura 4,62 m na régua desta estação

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,93 m · 6 h antes: 3,14 m · 12 h antes: 3,37 m; crista própria 3,41 m às 11/set 14:31 (11,4 h antes)
- **Vidal Ramos (Asthon)** (a montante): 3 h antes: sem leitura · 6 h antes: sem leitura · 12 h antes: 3,33 m; crista própria 3,38 m às 11/set 15:06 (10,8 h antes) — na borda dos dados
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,93 m · 6 h antes: 5,36 m · 12 h antes: 4,28 m; crista própria 5,44 m às 11/set 19:16 (6,6 h antes)

### DCSC-00019 SDC-SC Brusque — crista de 4,62 m

Referência: **12/set/2026 02:01**, leitura 4,62 m na régua desta estação

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,93 m · 6 h antes: 3,14 m · 12 h antes: 3,37 m; crista própria 3,41 m às 11/set 14:31 (11,5 h antes)
- **Vidal Ramos (Asthon)** (a montante): 3 h antes: sem leitura · 6 h antes: sem leitura · 12 h antes: 3,33 m; crista própria 3,38 m às 11/set 15:06 (10,9 h antes) — na borda dos dados
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,93 m · 6 h antes: 5,36 m · 12 h antes: 4,28 m; crista própria 5,44 m às 11/set 19:16 (6,8 h antes)

### DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva — crista de 1,84 m

Referência: **12/set/2026 03:01**, leitura 1,84 m na régua desta estação
(tábua da Marinha: preamar às 12/set 02:17, 1,13 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,09 m · 6 h antes: 1,11 m · 12 h antes: 1,29 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,75 m · 6 h antes: 6,32 m · 12 h antes: 4,11 m; crista própria 6,95 m às 12/set 04:46 (1,8 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,73 m · 6 h antes: 6,28 m · 12 h antes: 4,04 m; crista própria 6,95 m às 12/set 04:13 (1,2 h depois)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,05 m · 6 h antes: 5,96 m · 12 h antes: 4,82 m; crista própria 6,05 m às 11/set 23:31 (3,5 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 5,88 m · 6 h antes: 5,79 m · 12 h antes: 4,66 m; crista própria 5,89 m às 11/set 23:42 (3,3 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 5,51 m · 6 h antes: 5,20 m · 12 h antes: 4,48 m; crista própria 6,00 m às 12/set 08:46 (5,8 h depois)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 10,46 m · 6 h antes: 10,24 m · 12 h antes: 8,84 m; crista própria 10,46 m às 11/set 23:46 (3,2 h antes)
- **DCSC-00006 SDC-SC Indaial** (a montante): 3 h antes: 7,60 m · 6 h antes: 7,45 m · 12 h antes: 6,24 m; crista própria 7,61 m às 12/set 00:46 (2,2 h antes)
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 7,30 m · 6 h antes: 6,32 m · 12 h antes: sem leitura; crista própria 7,86 m às 12/set 05:00 (2,0 h depois)
- **DCSC-00030 SDC-SC Ilhota** (a montante): 3 h antes: 11,00 m · 6 h antes: 10,25 m · 12 h antes: 9,99 m; crista própria 11,64 m às 12/set 07:46 (4,8 h depois)

### DC-10 Rio Itajaí-Mirim – Bairro Limoeiro — crista de 8,04 m

Referência: **12/set/2026 03:10**, leitura 8,04 m na régua desta estação
(tábua da Marinha: preamar às 12/set 02:17, 1,13 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,89 m · 6 h antes: 3,03 m · 12 h antes: 3,35 m; crista própria 3,41 m às 11/set 14:31 (12,6 h antes)
- **Vidal Ramos (Asthon)** (a montante): 3 h antes: sem leitura · 6 h antes: sem leitura · 12 h antes: 3,38 m; crista própria 3,38 m às 11/set 15:06 (12,1 h antes) — na borda dos dados
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,80 m · 6 h antes: 5,14 m · 12 h antes: 4,46 m; crista própria 5,44 m às 11/set 19:16 (7,9 h antes)
- **Brusque** (a montante): 3 h antes: 4,49 m · 6 h antes: 4,28 m · 12 h antes: 2,96 m; crista própria 4,62 m às 12/set 01:55 (1,2 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 4,51 m · 6 h antes: 4,29 m · 12 h antes: 3,02 m; crista própria 4,62 m às 12/set 02:01 (1,1 h antes)

### Blumenau (AlertaBlu) — crista de 7,86 m

Referência: **12/set/2026 05:00**, leitura 7,86 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,09 m · 6 h antes: 1,09 m · 12 h antes: 1,21 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,88 m · 6 h antes: 6,63 m · 12 h antes: 5,03 m; crista própria 6,95 m às 12/set 04:46 (0,2 h antes)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,88 m · 6 h antes: 6,61 m · 12 h antes: 4,97 m; crista própria 6,95 m às 12/set 04:13 (0,8 h antes)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,03 m · 6 h antes: 6,04 m · 12 h antes: 5,29 m; crista própria 6,05 m às 11/set 23:31 (5,5 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 5,87 m · 6 h antes: 5,88 m · 12 h antes: 5,16 m; crista própria 5,89 m às 11/set 23:42 (5,3 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 5,18 m · 6 h antes: 5,22 m · 12 h antes: 4,67 m; crista própria 6,00 m às 12/set 08:46 (3,8 h depois)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 10,39 m · 6 h antes: 10,43 m · 12 h antes: 9,56 m; crista própria 10,46 m às 11/set 23:46 (5,2 h antes)
- **DCSC-00006 SDC-SC Indaial** (a montante): 3 h antes: 7,60 m · 6 h antes: 7,57 m · 12 h antes: 6,85 m; crista própria 7,61 m às 12/set 00:46 (4,2 h antes)

### DC-05 Rio Itajaí-Mirim (curso antigo) - Propriedade privada — crista de 2,42 m

Referência: **12/set/2026 05:01**, leitura 2,42 m na régua desta estação
(tábua da Marinha: baixa-mar às 12/set 07:21, 0,10 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,85 m · 6 h antes: 2,93 m · 12 h antes: 3,37 m; crista própria 3,41 m às 11/set 14:31 (14,5 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,57 m · 6 h antes: 4,93 m · 12 h antes: 4,63 m; crista própria 5,44 m às 11/set 19:16 (9,7 h antes)
- **Brusque** (a montante): 3 h antes: 4,61 m · 6 h antes: 4,38 m · 12 h antes: 3,51 m; crista própria 4,62 m às 12/set 01:55 (3,1 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 4,62 m · 6 h antes: 4,38 m · 12 h antes: 3,50 m; crista própria 4,62 m às 12/set 02:01 (3,0 h antes)

### DC-04 Rio Itajaí-Mirim (canal retificado e curso antigo) - Vitalmar Pescados — crista de 1,54 m

Referência: **12/set/2026 06:31**, leitura 1,54 m na régua desta estação
(tábua da Marinha: baixa-mar às 12/set 07:21, 0,10 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,81 m · 6 h antes: 2,87 m · 12 h antes: 3,28 m; crista própria 3,41 m às 11/set 14:31 (16,0 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,39 m · 6 h antes: 4,76 m · 12 h antes: 5,33 m; crista própria 5,44 m às 11/set 19:16 (11,2 h antes)
- **Brusque** (a montante): 3 h antes: 4,50 m · 6 h antes: 4,55 m · 12 h antes: 3,84 m; crista própria 4,62 m às 12/set 01:55 (4,6 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 4,50 m · 6 h antes: 4,55 m · 12 h antes: 3,83 m; crista própria 4,62 m às 12/set 02:01 (4,5 h antes)

### DCSC-00030 SDC-SC Ilhota — crista de 11,64 m

Referência: **12/set/2026 07:46**, leitura 11,64 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,07 m · 6 h antes: 1,09 m · 12 h antes: 1,14 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,95 m · 6 h antes: 6,88 m · 12 h antes: 5,98 m; crista própria 6,95 m às 12/set 04:46 (3,0 h antes)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,95 m · 6 h antes: 6,87 m · 12 h antes: 5,94 m; crista própria 6,95 m às 12/set 04:13 (3,6 h antes)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 5,97 m · 6 h antes: 6,04 m · 12 h antes: 5,83 m; crista própria 6,05 m às 11/set 23:31 (8,3 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 5,79 m · 6 h antes: 5,86 m · 12 h antes: 5,66 m; crista própria 5,89 m às 11/set 23:42 (8,1 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 5,84 m · 6 h antes: 5,65 m · 12 h antes: 5,02 m; crista própria 6,00 m às 12/set 08:46 (1,0 h depois)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 10,12 m · 6 h antes: 10,40 m · 12 h antes: 10,06 m; crista própria 10,46 m às 11/set 23:46 (8,0 h antes)
- **DCSC-00006 SDC-SC Indaial** (a montante): 3 h antes: 7,50 m · 6 h antes: 7,63 m · 12 h antes: 7,35 m; crista própria 7,61 m às 12/set 00:46 (7,0 h antes)
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 7,85 m · 6 h antes: 7,61 m · 12 h antes: 5,65 m; crista própria 7,86 m às 12/set 05:00 (2,8 h antes)

### DC-06 Rio Itajaí-Mirim (curso antigo) - Itamirim Clube de Campo — crista de 1,10 m

Referência: **12/set/2026 08:10**, leitura 1,10 m na régua desta estação
(tábua da Marinha: preamar às 12/set 08:06, 0,11 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,75 m · 6 h antes: 2,83 m · 12 h antes: 3,14 m; crista própria 3,41 m às 11/set 14:31 (17,6 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,20 m · 6 h antes: 4,52 m · 12 h antes: 5,29 m; crista própria 5,44 m às 11/set 19:16 (12,9 h antes)
- **Brusque** (a montante): 3 h antes: 4,24 m · 6 h antes: 4,61 m · 12 h antes: 4,16 m; crista própria 4,62 m às 12/set 01:55 (6,2 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 4,20 m · 6 h antes: 4,62 m · 12 h antes: 4,19 m; crista própria 4,62 m às 12/set 02:01 (6,1 h antes)

### DC-03 Rio Itajaí-Mirim (canal retificado) - Captação SEMASA — crista de 1,42 m

Referência: **12/set/2026 08:20**, leitura 1,42 m na régua desta estação
(tábua da Marinha: preamar às 12/set 08:06, 0,11 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,75 m · 6 h antes: 2,83 m · 12 h antes: 3,14 m; crista própria 3,41 m às 11/set 14:31 (17,8 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,20 m · 6 h antes: 4,52 m · 12 h antes: 5,29 m; crista própria 5,44 m às 11/set 19:16 (13,1 h antes)
- **Brusque** (a montante): 3 h antes: 4,21 m · 6 h antes: 4,61 m · 12 h antes: 4,19 m; crista própria 4,62 m às 12/set 01:55 (6,4 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 4,20 m · 6 h antes: 4,62 m · 12 h antes: 4,19 m; crista própria 4,62 m às 12/set 02:01 (6,3 h antes)

### DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima) — crista de 4,17 m

Referência: **12/set/2026 08:20**, leitura 4,17 m na régua desta estação
(tábua da Marinha: preamar às 12/set 08:06, 0,11 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,06 m · 6 h antes: 1,07 m · 12 h antes: 1,13 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,96 m · 6 h antes: 6,90 m · 12 h antes: 6,13 m; crista própria 6,95 m às 12/set 04:46 (3,6 h antes)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,95 m · 6 h antes: 6,89 m · 12 h antes: 6,08 m; crista própria 6,95 m às 12/set 04:13 (4,1 h antes)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 5,95 m · 6 h antes: 6,02 m · 12 h antes: 5,88 m; crista própria 6,05 m às 11/set 23:31 (8,8 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 5,79 m · 6 h antes: 5,85 m · 12 h antes: 5,73 m; crista própria 5,89 m às 11/set 23:42 (8,6 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 5,08 m · 6 h antes: 5,17 m · 12 h antes: 5,12 m; crista própria 6,00 m às 12/set 08:46 (0,4 h depois)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 10,06 m · 6 h antes: 10,37 m · 12 h antes: 10,11 m; crista própria 10,46 m às 11/set 23:46 (8,6 h antes)
- **DCSC-00006 SDC-SC Indaial** (a montante): 3 h antes: 7,46 m · 6 h antes: 7,60 m · 12 h antes: 7,38 m; crista própria 7,61 m às 12/set 00:46 (7,6 h antes)
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 7,86 m · 6 h antes: 7,68 m · 12 h antes: 5,96 m; crista própria 7,86 m às 12/set 05:00 (3,3 h antes)
- **DCSC-00030 SDC-SC Ilhota** (a montante): 3 h antes: 11,71 m · 6 h antes: 11,45 m · 12 h antes: 10,08 m; crista própria 11,64 m às 12/set 07:46 (0,6 h antes)

### DCSC-00032 SDC-SC Lontras — crista de 6,00 m

Referência: **12/set/2026 08:46**, leitura 6,00 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,06 m · 6 h antes: 1,07 m · 12 h antes: 1,13 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,95 m · 6 h antes: 6,92 m · 12 h antes: 6,26 m; crista própria 6,95 m às 12/set 04:46 (4,0 h antes)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,95 m · 6 h antes: 6,92 m · 12 h antes: 6,22 m; crista própria 6,95 m às 12/set 04:13 (4,6 h antes)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 5,95 m · 6 h antes: 6,01 m · 12 h antes: 5,94 m; crista própria 6,05 m às 11/set 23:31 (9,3 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 5,77 m · 6 h antes: 5,84 m · 12 h antes: 5,76 m; crista própria 5,89 m às 11/set 23:42 (9,1 h antes)

### Gaspar — Rio Itajaí-Açu (Defesa Civil de Gaspar) — crista de 5,21 m

Referência: **18/set/2026 14:51**, leitura 5,21 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,50 m · 6 h antes: 1,50 m · 12 h antes: 1,52 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 5,59 m · 6 h antes: 5,64 m · 12 h antes: 5,74 m; crista própria 6,08 m às 15/set 16:46 (70,1 h antes)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 5,59 m · 6 h antes: 5,64 m · 12 h antes: 5,73 m; crista própria 6,08 m às 15/set 17:58 (68,9 h antes)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 4,00 m · 6 h antes: 4,02 m · 12 h antes: 4,06 m
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 3,87 m · 6 h antes: 3,88 m · 12 h antes: 3,92 m
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 4,31 m · 6 h antes: 4,33 m · 12 h antes: 4,35 m
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 7,30 m · 6 h antes: 7,39 m · 12 h antes: 7,41 m
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 7,30 m · 6 h antes: 7,39 m · 12 h antes: 7,41 m
- **DCSC-00006 SDC-SC Indaial** (a montante): 3 h antes: 5,85 m · 6 h antes: 5,87 m · 12 h antes: 5,90 m
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 2,67 m · 6 h antes: 2,70 m · 12 h antes: 2,74 m

### DCSC-00018 SDC-SC Botuverá 1 — crista de 5,21 m

Referência: **22/set/2026 01:45**, leitura 5,21 m na régua desta estação

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 3,58 m · 6 h antes: 3,86 m · 12 h antes: 2,56 m; crista própria 3,73 m às 21/set 20:00 (5,8 h antes)

### DCSC-00003 SDC-SC Ascurra — crista de 9,42 m

Referência: **22/set/2026 07:45**, leitura 9,42 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,29 m · 6 h antes: 1,50 m · 12 h antes: 1,94 m; crista própria 3,10 m às 20/set 06:16 (49,5 h antes)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 5,59 m · 6 h antes: 4,86 m · 12 h antes: 2,96 m; crista própria 6,57 m às 22/set 17:01 (9,3 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 5,54 m · 6 h antes: 4,81 m · 12 h antes: 2,92 m; crista própria 6,57 m às 22/set 17:13 (9,5 h depois)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,30 m · 6 h antes: 5,92 m · 12 h antes: 4,23 m; crista própria 6,48 m às 22/set 08:30 (0,8 h depois)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,13 m · 6 h antes: 5,75 m · 12 h antes: 4,08 m; crista própria 6,30 m às 22/set 08:57 (1,2 h depois)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 5,21 m · 6 h antes: 4,75 m · 12 h antes: 3,92 m; crista própria 6,21 m às 22/set 22:16 (14,5 h depois)

### Ascurra — Ponte do Beber (DCSC-00003) — crista de 9,42 m

Referência: **22/set/2026 07:59**, leitura 9,42 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,29 m · 6 h antes: 1,48 m · 12 h antes: 1,94 m; crista própria 3,10 m às 20/set 06:16 (49,7 h antes)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 5,63 m · 6 h antes: 4,94 m · 12 h antes: 3,00 m; crista própria 6,57 m às 22/set 17:01 (9,0 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 5,59 m · 6 h antes: 4,89 m · 12 h antes: 2,97 m; crista própria 6,57 m às 22/set 17:13 (9,2 h depois)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,32 m · 6 h antes: 5,96 m · 12 h antes: 4,28 m; crista própria 6,48 m às 22/set 08:30 (0,5 h depois)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,14 m · 6 h antes: 5,80 m · 12 h antes: 4,13 m; crista própria 6,30 m às 22/set 08:57 (1,0 h depois)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 5,25 m · 6 h antes: 4,80 m · 12 h antes: 3,94 m; crista própria 6,21 m às 22/set 22:16 (14,3 h depois)

### DCSC-00006 SDC-SC Indaial — crista de 7,00 m

Referência: **22/set/2026 08:15**, leitura 7,00 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,29 m · 6 h antes: 1,44 m · 12 h antes: 1,93 m; crista própria 3,10 m às 20/set 06:16 (50,0 h antes)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 5,67 m · 6 h antes: 5,01 m · 12 h antes: 3,04 m; crista própria 6,57 m às 22/set 17:01 (8,8 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 5,64 m · 6 h antes: 4,97 m · 12 h antes: 3,01 m; crista própria 6,57 m às 22/set 17:13 (9,0 h depois)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,34 m · 6 h antes: 6,01 m · 12 h antes: 4,32 m; crista própria 6,48 m às 22/set 08:30 (0,3 h depois)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,16 m · 6 h antes: 5,84 m · 12 h antes: 4,17 m; crista própria 6,30 m às 22/set 08:57 (0,7 h depois)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 5,28 m · 6 h antes: 4,84 m · 12 h antes: 3,96 m; crista própria 6,21 m às 22/set 22:16 (14,0 h depois)
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 9,31 m · 6 h antes: 8,88 m · 12 h antes: 7,86 m; crista própria 9,42 m às 22/set 07:59 (0,3 h antes)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 9,31 m · 6 h antes: 8,88 m · 12 h antes: 7,85 m; crista própria 9,42 m às 22/set 07:45 (0,5 h antes)

### DCSC-00013 SDC-SC Rio do Sul — crista de 6,48 m

Referência: **22/set/2026 08:30**, leitura 6,48 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,27 m · 6 h antes: 1,43 m · 12 h antes: 1,89 m; crista própria 3,10 m às 20/set 06:16 (50,2 h antes)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 5,71 m · 6 h antes: 5,07 m · 12 h antes: 3,10 m; crista própria 6,57 m às 22/set 17:01 (8,5 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 5,68 m · 6 h antes: 5,04 m · 12 h antes: 3,06 m; crista própria 6,57 m às 22/set 17:13 (8,7 h depois)

### Rio do Sul, Ponte Dom Tito Buss (Asthon) — crista de 6,30 m

Referência: **22/set/2026 08:57**, leitura 6,30 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,27 m · 6 h antes: 1,37 m · 12 h antes: 1,79 m; crista própria 3,10 m às 20/set 06:16 (50,7 h antes)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 5,78 m · 6 h antes: 5,21 m · 12 h antes: 3,21 m; crista própria 6,57 m às 22/set 17:01 (8,1 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 5,77 m · 6 h antes: 5,17 m · 12 h antes: 3,17 m; crista própria 6,57 m às 22/set 17:13 (8,3 h depois)

### DCSC-00019 SDC-SC Brusque — crista de 4,09 m

Referência: **22/set/2026 10:30**, leitura 4,09 m na régua desta estação

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 3,04 m · 6 h antes: 3,22 m · 12 h antes: 3,57 m; crista própria 3,73 m às 21/set 20:00 (14,5 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,75 m · 6 h antes: 5,05 m · 12 h antes: 3,49 m; crista própria 5,21 m às 22/set 01:45 (8,7 h antes)

### Gaspar — Rio Itajaí-Açu (Defesa Civil de Gaspar) — crista de 4,22 m

Referência: **22/set/2026 11:14**, leitura 4,22 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,24 m · 6 h antes: 1,29 m · 12 h antes: 1,60 m; crista própria 3,10 m às 20/set 06:16 (53,0 h antes)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,07 m · 6 h antes: 5,67 m · 12 h antes: 3,90 m; crista própria 6,57 m às 22/set 17:01 (5,8 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,06 m · 6 h antes: 5,64 m · 12 h antes: 3,85 m; crista própria 6,57 m às 22/set 17:13 (6,0 h depois)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,48 m · 6 h antes: 6,34 m · 12 h antes: 5,26 m; crista própria 6,48 m às 22/set 08:30 (2,7 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,29 m · 6 h antes: 6,16 m · 12 h antes: 5,10 m; crista própria 6,30 m às 22/set 08:57 (2,3 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 5,71 m · 6 h antes: 5,28 m · 12 h antes: 4,28 m; crista própria 6,21 m às 22/set 22:16 (11,0 h depois)
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 9,41 m · 6 h antes: 9,31 m · 12 h antes: 8,31 m; crista própria 9,42 m às 22/set 07:59 (3,2 h antes)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 9,42 m · 6 h antes: 9,31 m · 12 h antes: 8,31 m; crista própria 9,42 m às 22/set 07:45 (3,5 h antes)
- **DCSC-00006 SDC-SC Indaial** (a montante): 3 h antes: 7,00 m · 6 h antes: 6,93 m · 12 h antes: 6,40 m; crista própria 7,00 m às 22/set 08:15 (3,0 h antes)
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 6,40 m · 6 h antes: 5,99 m · 12 h antes: 4,34 m; crista própria 6,62 m às 22/set 12:00 (0,8 h depois)

### Blumenau (AlertaBlu) — crista de 6,62 m

Referência: **22/set/2026 12:00**, leitura 6,62 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,22 m · 6 h antes: 1,27 m · 12 h antes: 1,63 m; crista própria 3,10 m às 20/set 06:16 (53,7 h antes)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,15 m · 6 h antes: 5,78 m · 12 h antes: 4,21 m; crista própria 6,57 m às 22/set 17:01 (5,0 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,14 m · 6 h antes: 5,77 m · 12 h antes: 4,16 m; crista própria 6,57 m às 22/set 17:13 (5,2 h depois)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,48 m · 6 h antes: 6,38 m · 12 h antes: 5,50 m; crista própria 6,48 m às 22/set 08:30 (3,5 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,30 m · 6 h antes: 6,22 m · 12 h antes: 5,34 m; crista própria 6,30 m às 22/set 08:57 (3,0 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 5,78 m · 6 h antes: 5,40 m · 12 h antes: 4,44 m; crista própria 6,21 m às 22/set 22:16 (10,3 h depois)
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 9,37 m · 6 h antes: 9,36 m · 12 h antes: 8,45 m; crista própria 9,42 m às 22/set 07:59 (4,0 h antes)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 9,37 m · 6 h antes: 9,37 m · 12 h antes: 8,45 m; crista própria 9,42 m às 22/set 07:45 (4,2 h antes)
- **DCSC-00006 SDC-SC Indaial** (a montante): 3 h antes: 6,99 m · 6 h antes: 6,96 m · 12 h antes: 6,47 m; crista própria 7,00 m às 22/set 08:15 (3,7 h antes)

### DC-10 Rio Itajaí-Mirim – Bairro Limoeiro — crista de 7,28 m

Referência: **22/set/2026 12:40**, leitura 7,28 m na régua desta estação
(tábua da Marinha: preamar às 22/set 12:10, 0,88 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,97 m · 6 h antes: 3,07 m · 12 h antes: 3,66 m; crista própria 3,73 m às 21/set 20:00 (16,7 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,41 m · 6 h antes: 4,89 m · 12 h antes: 4,92 m; crista própria 5,21 m às 22/set 01:45 (10,9 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 4,08 m · 6 h antes: 3,58 m · 12 h antes: 2,88 m; crista própria 4,09 m às 22/set 10:30 (2,2 h antes)

### DCSC-00030 SDC-SC Ilhota — crista de 11,12 m

Referência: **22/set/2026 16:01**, leitura 11,12 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,20 m · 6 h antes: 1,22 m · 12 h antes: 1,33 m; crista própria 3,10 m às 20/set 06:16 (57,8 h antes)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,45 m · 6 h antes: 6,25 m · 12 h antes: 5,42 m; crista própria 6,57 m às 22/set 17:01 (1,0 h depois)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,45 m · 6 h antes: 6,23 m · 12 h antes: 5,39 m; crista própria 6,57 m às 22/set 17:13 (1,2 h depois)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,41 m · 6 h antes: 6,47 m · 12 h antes: 6,23 m; crista própria 6,48 m às 22/set 08:30 (7,5 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,23 m · 6 h antes: 6,29 m · 12 h antes: 6,07 m; crista própria 6,30 m às 22/set 08:57 (7,1 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 6,01 m · 6 h antes: 5,86 m · 12 h antes: 5,09 m; crista própria 6,21 m às 22/set 22:16 (6,2 h depois)
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 9,19 m · 6 h antes: 9,29 m · 12 h antes: 9,17 m; crista própria 9,42 m às 22/set 07:59 (8,0 h antes)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 9,19 m · 6 h antes: 9,29 m · 12 h antes: 9,18 m; crista própria 9,42 m às 22/set 07:45 (8,3 h antes)
- **DCSC-00006 SDC-SC Indaial** (a montante): 3 h antes: 6,89 m · 6 h antes: 7,00 m · 12 h antes: 6,84 m; crista própria 7,00 m às 22/set 08:15 (7,8 h antes)
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 6,58 m · 6 h antes: 6,55 m · 12 h antes: 5,74 m; crista própria 6,62 m às 22/set 12:00 (4,0 h antes)

### DC-05 Rio Itajaí-Mirim (curso antigo) - Propriedade privada — crista de 2,00 m

Referência: **22/set/2026 16:41**, leitura 2,00 m na régua desta estação
(tábua da Marinha: baixa-mar às 22/set 19:12, 0,38 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,88 m · 6 h antes: 2,95 m · 12 h antes: 3,20 m; crista própria 3,73 m às 21/set 20:00 (20,7 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,02 m · 6 h antes: 4,27 m · 12 h antes: 5,05 m; crista própria 5,21 m às 22/set 01:45 (14,9 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 3,79 m · 6 h antes: 4,09 m · 12 h antes: 2,87 m; crista própria 4,09 m às 22/set 10:30 (6,2 h antes)

### DC-03 Rio Itajaí-Mirim (canal retificado) - Captação SEMASA — crista de 1,42 m

Referência: **22/set/2026 17:20**, leitura 1,42 m na régua desta estação
(tábua da Marinha: baixa-mar às 22/set 19:12, 0,38 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,87 m · 6 h antes: 2,93 m · 12 h antes: 3,17 m; crista própria 3,73 m às 21/set 20:00 (21,3 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 3,98 m · 6 h antes: 4,23 m · 12 h antes: 5,08 m; crista própria 5,21 m às 22/set 01:45 (15,6 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 3,69 m · 6 h antes: 4,08 m · 12 h antes: 2,94 m; crista própria 4,09 m às 22/set 10:30 (6,8 h antes)

### DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima) — crista de 3,89 m

Referência: **22/set/2026 17:40**, leitura 3,89 m na régua desta estação
(tábua da Marinha: baixa-mar às 22/set 19:12, 0,38 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,18 m · 6 h antes: 1,20 m · 12 h antes: 1,27 m; crista própria 3,10 m às 20/set 06:16 (59,4 h antes)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,53 m · 6 h antes: 6,38 m · 12 h antes: 5,75 m; crista própria 6,57 m às 22/set 17:01 (0,6 h antes)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,52 m · 6 h antes: 6,37 m · 12 h antes: 5,73 m; crista própria 6,57 m às 22/set 17:13 (0,4 h antes)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,37 m · 6 h antes: 6,43 m · 12 h antes: 6,36 m; crista própria 6,48 m às 22/set 08:30 (9,2 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,16 m · 6 h antes: 6,25 m · 12 h antes: 6,16 m; crista própria 6,30 m às 22/set 08:57 (8,7 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 6,09 m · 6 h antes: 5,95 m · 12 h antes: 5,36 m; crista própria 6,21 m às 22/set 22:16 (4,6 h depois)
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 9,09 m · 6 h antes: 9,24 m · 12 h antes: 9,35 m; crista própria 9,42 m às 22/set 07:59 (9,7 h antes)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 9,09 m · 6 h antes: 9,24 m · 12 h antes: 9,35 m; crista própria 9,42 m às 22/set 07:45 (9,9 h antes)
- **DCSC-00006 SDC-SC Indaial** (a montante): 3 h antes: 6,87 m · 6 h antes: 6,93 m · 12 h antes: 6,94 m; crista própria 7,00 m às 22/set 08:15 (9,4 h antes)
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 6,49 m · 6 h antes: 6,61 m · 12 h antes: 6,07 m; crista própria 6,62 m às 22/set 12:00 (5,7 h antes)
- **DCSC-00030 SDC-SC Ilhota** (a montante): 3 h antes: 11,08 m · 6 h antes: 10,97 m · 12 h antes: 10,39 m; crista própria 11,12 m às 22/set 16:01 (1,6 h antes)

### DC-06 Rio Itajaí-Mirim (curso antigo) - Itamirim Clube de Campo — crista de 1,00 m

Referência: **22/set/2026 20:50**, leitura 1,00 m na régua desta estação
(tábua da Marinha: baixa-mar às 22/set 19:12, 0,38 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,82 m · 6 h antes: 2,85 m · 12 h antes: 3,00 m; crista própria 3,73 m às 21/set 20:00 (24,8 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 3,81 m · 6 h antes: 3,95 m · 12 h antes: 4,54 m; crista própria 5,21 m às 22/set 01:45 (19,1 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 3,08 m · 6 h antes: 3,58 m · 12 h antes: 4,01 m; crista própria 4,09 m às 22/set 10:30 (10,3 h antes)

### DC-04 Rio Itajaí-Mirim (canal retificado e curso antigo) - Vitalmar Pescados — crista de 1,62 m

Referência: **22/set/2026 21:01**, leitura 1,62 m na régua desta estação
(tábua da Marinha: baixa-mar às 22/set 19:12, 0,38 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,84 m · 6 h antes: 2,85 m · 12 h antes: 2,99 m; crista própria 3,73 m às 21/set 20:00 (25,0 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 3,79 m · 6 h antes: 3,93 m · 12 h antes: 4,50 m; crista própria 5,21 m às 22/set 01:45 (19,3 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 3,04 m · 6 h antes: 3,54 m · 12 h antes: 4,05 m; crista própria 4,09 m às 22/set 10:30 (10,5 h antes)

### DCSC-00032 SDC-SC Lontras — crista de 6,21 m

Referência: **22/set/2026 22:16**, leitura 6,21 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,16 m · 6 h antes: 1,16 m · 12 h antes: 1,22 m; crista própria 3,10 m às 20/set 06:16 (64,0 h antes)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,56 m · 6 h antes: 6,56 m · 12 h antes: 6,26 m; crista própria 6,57 m às 22/set 17:01 (5,3 h antes)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,56 m · 6 h antes: 6,56 m · 12 h antes: 6,25 m; crista própria 6,57 m às 22/set 17:13 (5,1 h antes)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,23 m · 6 h antes: 6,33 m · 12 h antes: 6,47 m; crista própria 6,48 m às 22/set 08:30 (13,8 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,06 m · 6 h antes: 6,14 m · 12 h antes: 6,27 m; crista própria 6,30 m às 22/set 08:57 (13,3 h antes)

### DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva — crista de 1,65 m

Referência: **23/set/2026 00:51**, leitura 1,65 m na régua desta estação
(tábua da Marinha: preamar às 23/set 00:31, 0,92 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,14 m · 6 h antes: 1,16 m · 12 h antes: 1,20 m; crista própria 3,10 m às 20/set 06:16 (66,6 h antes)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 6,47 m · 6 h antes: 6,57 m · 12 h antes: 6,44 m; crista própria 6,57 m às 22/set 17:01 (7,8 h antes)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 6,48 m · 6 h antes: 6,56 m · 12 h antes: 6,45 m; crista própria 6,57 m às 22/set 17:13 (7,6 h antes)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,14 m · 6 h antes: 6,25 m · 12 h antes: 6,41 m; crista própria 6,48 m às 22/set 08:30 (16,3 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 5,96 m · 6 h antes: 6,07 m · 12 h antes: 6,23 m; crista própria 6,30 m às 22/set 08:57 (15,9 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 6,21 m · 6 h antes: 6,18 m · 12 h antes: 6,00 m; crista própria 6,21 m às 22/set 22:16 (2,6 h antes)
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 8,78 m · 6 h antes: 8,94 m · 12 h antes: 9,20 m; crista própria 9,42 m às 22/set 07:59 (16,9 h antes)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 8,78 m · 6 h antes: 8,94 m · 12 h antes: 9,21 m; crista própria 9,42 m às 22/set 07:45 (17,1 h antes)
- **DCSC-00006 SDC-SC Indaial** (a montante): 3 h antes: 6,67 m · 6 h antes: 6,75 m · 12 h antes: 6,90 m; crista própria 7,00 m às 22/set 08:15 (16,6 h antes)
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 5,75 m · 6 h antes: 6,08 m · 12 h antes: 6,58 m; crista própria 6,62 m às 22/set 12:00 (12,9 h antes)
- **DCSC-00030 SDC-SC Ilhota** (a montante): 3 h antes: 10,80 m · 6 h antes: 10,98 m · 12 h antes: 11,05 m; crista própria 11,12 m às 22/set 16:01 (8,8 h antes)

### DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL — crista de 1,78 m

Referência: **23/set/2026 13:52**, leitura 1,78 m na régua desta estação
(tábua da Marinha: preamar às 23/set 12:40, 0,96 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 2,21 m · 6 h antes: 1,13 m · 12 h antes: 1,14 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 5,33 m · 6 h antes: 5,66 m · 12 h antes: 6,22 m; crista própria 6,57 m às 22/set 17:01 (20,9 h antes)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 5,31 m · 6 h antes: 5,64 m · 12 h antes: 6,21 m; crista própria 6,57 m às 22/set 17:13 (20,7 h antes)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 5,69 m · 6 h antes: 5,79 m · 12 h antes: 5,99 m; crista própria 6,48 m às 22/set 08:30 (29,4 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 5,53 m · 6 h antes: 5,61 m · 12 h antes: 5,81 m; crista própria 6,30 m às 22/set 08:57 (28,9 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 6,16 m · 6 h antes: 6,18 m · 12 h antes: 6,21 m; crista própria 6,21 m às 22/set 22:16 (15,6 h antes)
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 8,34 m · 6 h antes: 8,42 m · 12 h antes: 8,63 m; crista própria 9,42 m às 22/set 07:59 (29,9 h antes)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 8,33 m · 6 h antes: 8,42 m · 12 h antes: 8,63 m; crista própria 9,42 m às 22/set 07:45 (30,1 h antes)
- **DCSC-00006 SDC-SC Indaial** (a montante): 3 h antes: 6,41 m · 6 h antes: 6,47 m · 12 h antes: 6,59 m; crista própria 7,00 m às 22/set 08:15 (29,6 h antes)
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 4,62 m · 6 h antes: 4,87 m · 12 h antes: 5,37 m; crista própria 6,62 m às 22/set 12:00 (25,9 h antes)
- **DCSC-00030 SDC-SC Ilhota** (a montante): 3 h antes: 10,27 m · 6 h antes: 10,23 m · 12 h antes: 10,82 m; crista própria 11,12 m às 22/set 16:01 (21,9 h antes)

### DCSC-00003 SDC-SC Ascurra — crista de 8,24 m

Referência: **28/set/2026 22:01**, leitura 8,24 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,04 m · 6 h antes: 1,85 m · 12 h antes: 3,98 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 4,72 m · 6 h antes: 5,31 m · 12 h antes: 5,23 m; crista própria 5,71 m às 26/set 03:01 (67,0 h antes)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 4,74 m · 6 h antes: 5,31 m · 12 h antes: 5,23 m; crista própria 5,70 m às 26/set 05:44 (64,3 h antes)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 5,60 m · 6 h antes: 5,59 m · 12 h antes: 5,34 m
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 5,43 m · 6 h antes: 5,42 m · 12 h antes: 5,16 m
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 4,73 m · 6 h antes: 4,67 m · 12 h antes: 4,66 m

### Ascurra — Ponte do Beber (DCSC-00003) — crista de 8,25 m

Referência: **28/set/2026 22:46**, leitura 8,25 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,04 m · 6 h antes: 1,29 m · 12 h antes: 3,96 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 4,62 m · 6 h antes: 5,14 m · 12 h antes: 5,26 m; crista própria 5,71 m às 26/set 03:01 (67,7 h antes)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 4,62 m · 6 h antes: 5,17 m · 12 h antes: 5,26 m; crista própria 5,70 m às 26/set 05:44 (65,0 h antes)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 5,54 m · 6 h antes: 5,63 m · 12 h antes: 5,34 m
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 5,37 m · 6 h antes: 5,45 m · 12 h antes: 5,17 m
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 4,72 m · 6 h antes: 4,69 m · 12 h antes: 4,66 m

### Blumenau (AlertaBlu) — crista de 3,87 m

Referência: **29/set/2026 06:00**, leitura 3,87 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 1,01 m · 6 h antes: 1,02 m · 12 h antes: 1,06 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 3,81 m · 6 h antes: 4,14 m · 12 h antes: 4,89 m
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 3,82 m · 6 h antes: 4,14 m · 12 h antes: 4,92 m
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 4,74 m · 6 h antes: 5,02 m · 12 h antes: 5,63 m
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 4,56 m · 6 h antes: 4,84 m · 12 h antes: 5,47 m
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 4,22 m · 6 h antes: 4,43 m · 12 h antes: 4,73 m
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 8,09 m · 6 h antes: 8,23 m · 12 h antes: 8,19 m; crista própria 8,25 m às 28/set 22:46 (7,2 h antes)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 8,09 m · 6 h antes: 8,23 m · 12 h antes: 8,19 m; crista própria 8,24 m às 28/set 22:01 (8,0 h antes)

### DCSC-00018 SDC-SC Botuverá 1 — crista de 5,38 m

Referência: **01/out/2026 04:46**, leitura 5,38 m na régua desta estação

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 3,43 m · 6 h antes: 4,04 m · 12 h antes: 2,60 m; crista própria 4,20 m às 30/set 23:31 (5,2 h antes)

### DCSC-00013 SDC-SC Rio do Sul — crista de 6,51 m

Referência: **01/out/2026 07:30**, leitura 6,51 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 2,85 m · 6 h antes: 2,92 m · 12 h antes: 2,52 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 4,67 m · 6 h antes: 4,68 m · 12 h antes: 4,74 m
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 4,67 m · 6 h antes: 4,67 m · 12 h antes: 4,74 m

### Rio do Sul, Ponte Dom Tito Buss (Asthon) — crista de 6,35 m

Referência: **01/out/2026 08:13**, leitura 6,35 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 2,87 m · 6 h antes: 2,90 m · 12 h antes: 2,60 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 4,67 m · 6 h antes: 4,66 m · 12 h antes: 4,74 m
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 4,67 m · 6 h antes: 4,66 m · 12 h antes: 4,74 m

### DCSC-00032 SDC-SC Lontras — crista de 5,26 m (na borda dos dados: piso)

Referência: **01/out/2026 08:45**, leitura 5,26 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 2,85 m · 6 h antes: 2,87 m · 12 h antes: 2,65 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 4,67 m · 6 h antes: 4,66 m · 12 h antes: 4,74 m
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 4,67 m · 6 h antes: 4,65 m · 12 h antes: 4,74 m
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,46 m · 6 h antes: 6,17 m · 12 h antes: 4,91 m; crista própria 6,51 m às 01/out 07:30 (1,2 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,29 m · 6 h antes: 6,01 m · 12 h antes: 4,78 m; crista própria 6,35 m às 01/out 08:13 (0,5 h antes)

### DCSC-00003 SDC-SC Ascurra — crista de 8,77 m

Referência: **01/out/2026 11:46**, leitura 8,77 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 2,79 m · 6 h antes: 2,85 m · 12 h antes: 2,88 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 4,67 m · 6 h antes: 4,67 m · 12 h antes: 4,72 m
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 4,67 m · 6 h antes: 4,67 m · 12 h antes: 4,71 m
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,51 m · 6 h antes: 6,46 m · 12 h antes: 5,42 m; crista própria 6,51 m às 01/out 07:30 (4,3 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,34 m · 6 h antes: 6,29 m · 12 h antes: 5,26 m; crista própria 6,35 m às 01/out 08:13 (3,5 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: 5,26 m · 6 h antes: 5,17 m · 12 h antes: 4,36 m; crista própria 5,26 m às 01/out 08:45 (3,0 h antes) — na borda dos dados

### DCSC-00019 SDC-SC Brusque — crista de 3,75 m

Referência: **01/out/2026 12:01**, leitura 3,75 m na régua desta estação

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 3,08 m · 6 h antes: 3,32 m · 12 h antes: 4,14 m; crista própria 4,20 m às 30/set 23:31 (12,5 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,59 m · 6 h antes: 5,10 m · 12 h antes: 3,60 m; crista própria 5,38 m às 01/out 04:46 (7,2 h antes)

### Ascurra — Ponte do Beber (DCSC-00003) — crista de 8,77 m

Referência: **01/out/2026 12:16**, leitura 8,77 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 2,77 m · 6 h antes: 2,85 m · 12 h antes: 2,90 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 4,67 m · 6 h antes: 4,67 m · 12 h antes: 4,70 m
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 4,68 m · 6 h antes: 4,68 m · 12 h antes: 4,70 m
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,51 m · 6 h antes: 6,48 m · 12 h antes: 5,61 m; crista própria 6,51 m às 01/out 07:30 (4,8 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,34 m · 6 h antes: 6,30 m · 12 h antes: 5,43 m; crista própria 6,35 m às 01/out 08:13 (4,0 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: sem leitura · 6 h antes: 5,19 m · 12 h antes: 4,42 m; crista própria 5,26 m às 01/out 08:45 (3,5 h antes) — na borda dos dados

### Gaspar — Rio Itajaí-Açu (Defesa Civil de Gaspar) — crista de 2,54 m

Referência: **01/out/2026 13:19**, leitura 2,54 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 2,77 m · 6 h antes: 2,81 m · 12 h antes: 2,92 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 4,69 m · 6 h antes: 4,67 m · 12 h antes: 4,68 m
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 4,67 m · 6 h antes: 4,68 m · 12 h antes: 4,67 m
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,49 m · 6 h antes: 6,51 m · 12 h antes: 5,88 m; crista própria 6,51 m às 01/out 07:30 (5,8 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,33 m · 6 h antes: 6,33 m · 12 h antes: 5,71 m; crista própria 6,35 m às 01/out 08:13 (5,1 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: sem leitura · 6 h antes: 5,23 m · 12 h antes: 4,61 m; crista própria 5,26 m às 01/out 08:45 (4,6 h antes) — na borda dos dados
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 8,72 m · 6 h antes: 8,62 m · 12 h antes: 8,00 m; crista própria 8,77 m às 01/out 12:16 (1,0 h antes)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 8,72 m · 6 h antes: 8,62 m · 12 h antes: 8,00 m; crista própria 8,77 m às 01/out 11:46 (1,5 h antes)
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 4,06 m · 6 h antes: 3,70 m · 12 h antes: 3,38 m; crista própria 4,53 m às 01/out 20:00 (6,7 h depois)

### DC-10 Rio Itajaí-Mirim – Bairro Limoeiro — crista de 6,64 m

Referência: **01/out/2026 13:50**, leitura 6,64 m na régua desta estação
(tábua da Marinha: baixa-mar às 01/out 14:08, 0,52 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 3,03 m · 6 h antes: 3,20 m · 12 h antes: 3,43 m; crista própria 4,20 m às 30/set 23:31 (14,3 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,56 m · 6 h antes: 4,71 m · 12 h antes: 3,62 m; crista própria 5,38 m às 01/out 04:46 (9,1 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 3,63 m · 6 h antes: 2,54 m · 12 h antes: 2,33 m; crista própria 3,75 m às 01/out 12:01 (1,8 h antes)

### DC-03 Rio Itajaí-Mirim (canal retificado) - Captação SEMASA — crista de 1,10 m

Referência: **01/out/2026 16:40**, leitura 1,10 m na régua desta estação
(tábua da Marinha: preamar às 01/out 17:04, 0,75 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,96 m · 6 h antes: 3,03 m · 12 h antes: 3,28 m; crista própria 4,20 m às 30/set 23:31 (17,1 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 4,37 m · 6 h antes: 4,56 m · 12 h antes: 5,38 m; crista própria 5,38 m às 01/out 04:46 (11,9 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 3,56 m · 6 h antes: 3,63 m · 12 h antes: 2,29 m; crista própria 3,75 m às 01/out 12:01 (4,6 h antes)

### DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima) — crista de 3,21 m

Referência: **01/out/2026 18:00**, leitura 3,21 m na régua desta estação
(tábua da Marinha: preamar às 01/out 17:04, 0,75 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 2,71 m · 6 h antes: 2,77 m · 12 h antes: 2,85 m; crista própria 4,37 m às 02/out 14:31 (20,5 h depois)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 4,64 m · 6 h antes: 4,69 m · 12 h antes: 4,67 m
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 4,63 m · 6 h antes: 4,69 m · 12 h antes: 4,68 m
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,37 m · 6 h antes: 6,46 m · 12 h antes: 6,46 m; crista própria 6,51 m às 01/out 07:30 (10,5 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,15 m · 6 h antes: 6,30 m · 12 h antes: 6,30 m; crista própria 6,35 m às 01/out 08:13 (9,8 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: sem leitura · 6 h antes: sem leitura · 12 h antes: 5,17 m; crista própria 5,26 m às 01/out 08:45 (9,2 h antes) — na borda dos dados
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 8,74 m · 6 h antes: 8,77 m · 12 h antes: 8,47 m; crista própria 8,77 m às 01/out 12:16 (5,7 h antes)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 8,74 m · 6 h antes: 8,77 m · 12 h antes: 8,47 m; crista própria 8,77 m às 01/out 11:46 (6,2 h antes)
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 4,44 m · 6 h antes: 4,25 m · 12 h antes: 3,57 m; crista própria 4,53 m às 01/out 20:00 (2,0 h depois)
- **DCSC-00030 SDC-SC Ilhota** (a montante): 3 h antes: 9,94 m · 6 h antes: 9,85 m · 12 h antes: 9,83 m; crista própria 10,15 m às 01/out 19:01 (1,0 h depois)

### DCSC-00030 SDC-SC Ilhota — crista de 10,15 m

Referência: **01/out/2026 19:01**, leitura 10,15 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 2,69 m · 6 h antes: 2,73 m · 12 h antes: 2,83 m; crista própria 4,37 m às 02/out 14:31 (19,5 h depois)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 4,63 m · 6 h antes: 4,68 m · 12 h antes: 4,67 m
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 4,62 m · 6 h antes: 4,68 m · 12 h antes: 4,68 m
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,32 m · 6 h antes: 6,43 m · 12 h antes: 6,51 m; crista própria 6,51 m às 01/out 07:30 (11,5 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,15 m · 6 h antes: 6,26 m · 12 h antes: 6,33 m; crista própria 6,35 m às 01/out 08:13 (10,8 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: sem leitura · 6 h antes: sem leitura · 12 h antes: 5,23 m; crista própria 5,26 m às 01/out 08:45 (10,3 h antes) — na borda dos dados
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 8,76 m · 6 h antes: 8,76 m · 12 h antes: 8,59 m; crista própria 8,77 m às 01/out 12:16 (6,8 h antes)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 8,76 m · 6 h antes: 8,76 m · 12 h antes: 8,60 m; crista própria 8,77 m às 01/out 11:46 (7,3 h antes)
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 4,48 m · 6 h antes: 4,34 m · 12 h antes: 3,66 m; crista própria 4,53 m às 01/out 20:00 (1,0 h depois)

### Blumenau (AlertaBlu) — crista de 4,53 m

Referência: **01/out/2026 20:00**, leitura 4,53 m na régua desta estação

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 2,69 m · 6 h antes: 2,71 m · 12 h antes: 2,79 m; crista própria 4,37 m às 02/out 14:31 (18,5 h depois)
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 4,71 m · 6 h antes: 4,66 m · 12 h antes: 4,67 m
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 4,70 m · 6 h antes: 4,66 m · 12 h antes: 4,67 m
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 6,27 m · 6 h antes: 6,40 m · 12 h antes: 6,51 m; crista própria 6,51 m às 01/out 07:30 (12,5 h antes)
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 6,13 m · 6 h antes: 6,23 m · 12 h antes: 6,34 m; crista própria 6,35 m às 01/out 08:13 (11,8 h antes)
- **DCSC-00032 SDC-SC Lontras** (a montante): 3 h antes: sem leitura · 6 h antes: sem leitura · 12 h antes: 5,25 m; crista própria 5,26 m às 01/out 08:45 (11,2 h antes) — na borda dos dados
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 8,73 m · 6 h antes: 8,75 m · 12 h antes: 8,68 m; crista própria 8,77 m às 01/out 12:16 (7,7 h antes)
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 8,73 m · 6 h antes: 8,75 m · 12 h antes: 8,68 m; crista própria 8,77 m às 01/out 11:46 (8,2 h antes)

### DC-04 Rio Itajaí-Mirim (canal retificado e curso antigo) - Vitalmar Pescados — crista de 1,46 m

Referência: **02/out/2026 09:01**, leitura 1,46 m na régua desta estação
(tábua da Marinha: baixa-mar às 02/out 09:19, 0,63 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,76 m · 6 h antes: 2,77 m · 12 h antes: 2,83 m; crista própria 4,20 m às 30/set 23:31 (33,5 h antes)
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 3,74 m · 6 h antes: 3,79 m · 12 h antes: 3,96 m; crista própria 5,38 m às 01/out 04:46 (28,2 h antes)
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 2,29 m · 6 h antes: 2,40 m · 12 h antes: 2,81 m; crista própria 3,75 m às 01/out 12:01 (21,0 h antes)

### DCSC-00018 SDC-SC Botuverá 1 — crista de 3,85 m

Referência: **04/out/2026 14:16**, leitura 3,85 m na régua desta estação

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,75 m · 6 h antes: 2,98 m · 12 h antes: 2,60 m

### DC-10 Rio Itajaí-Mirim – Bairro Limoeiro — crista de 4,34 m

Referência: **05/out/2026 00:30**, leitura 4,34 m na régua desta estação
(tábua da Marinha: preamar às 05/out 00:46, 0,60 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,60 m · 6 h antes: 2,58 m · 12 h antes: 2,71 m
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 3,48 m · 6 h antes: 3,58 m · 12 h antes: 3,50 m; crista própria 3,85 m às 04/out 14:16 (10,2 h antes)
- **Brusque — Ponte Estaiada (DCSC-00019)** (a montante): 3 h antes: 2,04 m · 6 h antes: 1,78 m · 12 h antes: 1,79 m
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 2,04 m · 6 h antes: 1,78 m · 12 h antes: 1,79 m

### DC-04 Rio Itajaí-Mirim (canal retificado e curso antigo) - Vitalmar Pescados — crista de 1,32 m (na borda dos dados: piso)

Referência: **05/out/2026 15:21**, leitura 1,32 m na régua desta estação
(tábua da Marinha: baixa-mar às 05/out 18:17, 0,44 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00024 SDC-SC Vidal Ramos** (a montante): 3 h antes: 2,56 m · 6 h antes: 2,58 m · 12 h antes: 2,58 m
- **DCSC-00018 SDC-SC Botuverá 1** (a montante): 3 h antes: 3,28 m · 6 h antes: 3,31 m · 12 h antes: 3,37 m; crista própria 3,85 m às 04/out 14:16 (25,1 h antes)
- **Brusque — Ponte Estaiada (DCSC-00019)** (a montante): 3 h antes: 1,68 m · 6 h antes: 1,71 m · 12 h antes: 1,85 m
- **DCSC-00019 SDC-SC Brusque** (a montante): 3 h antes: 1,68 m · 6 h antes: 1,71 m · 12 h antes: 1,85 m

### DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL — crista de 1,20 m (na borda dos dados: piso)

Referência: **05/out/2026 15:21**, leitura 1,20 m na régua desta estação
(tábua da Marinha: baixa-mar às 05/out 18:17, 0,44 m sobre o zero da carta náutica — não é régua de rio)

- **DCSC-00039 SDC-SC Ituporanga** (a montante): 3 h antes: 3,90 m · 6 h antes: 3,90 m · 12 h antes: 3,96 m
- **DCSC-00041 SDC-SC Taió** (a montante): 3 h antes: 4,73 m · 6 h antes: 4,83 m · 12 h antes: 5,02 m; crista própria 5,72 m às 03/out 00:01 (63,3 h antes)
- **Taió — Rio Itajaí do Oeste, Centro** (a montante): 3 h antes: 4,72 m · 6 h antes: 4,83 m · 12 h antes: 5,01 m; crista própria 5,72 m às 02/out 23:25 (63,9 h antes)
- **DCSC-00013 SDC-SC Rio do Sul** (a montante): 3 h antes: 5,45 m · 6 h antes: 5,51 m · 12 h antes: 5,63 m
- **Rio do Sul, Ponte Dom Tito Buss (Asthon)** (a montante): 3 h antes: 5,30 m · 6 h antes: 5,36 m · 12 h antes: 5,47 m
- **Ascurra — Ponte do Beber (DCSC-00003)** (a montante): 3 h antes: 7,84 m · 6 h antes: 7,83 m · 12 h antes: 7,97 m
- **DCSC-00003 SDC-SC Ascurra** (a montante): 3 h antes: 7,84 m · 6 h antes: 7,83 m · 12 h antes: 7,97 m
- **Blumenau (AlertaBlu)** (a montante): 3 h antes: 3,34 m · 6 h antes: 3,36 m · 12 h antes: 3,54 m
- **DCSC-00030 SDC-SC Ilhota** (a montante): 3 h antes: 9,66 m · 6 h antes: 9,23 m · 12 h antes: 9,38 m

## Cristas sem régua a montante com leitura nessas horas

A conta não dá para fazer nelas com as séries do repositório (com `--series`, a série inteira da VPS
pode cobrir algumas, como Brusque para as réguas do Itajaí-Mirim em Itajaí).

- ANA 83892990 Salseiro (Vidal Ramos): crista de 2,73 m, 15/dez/2020 13:15
- ANA 83050000 Taió: crista de 6,90 m, 22/jan/2021 15:45
- ANA 83050000 Taió: crista de 9,48 m, 05/mai/2022 04:15
- ANA 83050000 Taió: crista de 12,13 m, 09/out/2023 13:45
- ANA 83050000 Taió: crista de 10,92 m, 12/out/2023 23:45
- ANA 83029900 Barragem Taió Montante: crista de 2,92 m (na borda dos dados: piso), 16/nov/2023 22:45
- ANA 83892990 Salseiro (Vidal Ramos): crista de 5,20 m, 17/nov/2023 09:45
- ANA 83050000 Taió: crista de 10,32 m, 17/nov/2023 21:15
- ANA 83892990 Salseiro (Vidal Ramos): crista de 3,30 m, 22/nov/2023 22:00
- ANA 83050000 Taió: crista de 6,87 m, 23/nov/2023 03:15
- Asthon Vidal Ramos: crista de 3,13 m, 29/jul/2026 11:56
- Asthon Rio do Sul (Ponte Dom Tito Buss): crista de 4,51 m, 29/jul/2026 23:49
- Asthon Vidal Ramos: crista de 3,00 m, 07/ago/2026 04:56
- Asthon Rio do Sul (Ponte Dom Tito Buss): crista de 4,10 m, 10/ago/2026 09:01
- Asthon Vidal Ramos: crista de 3,42 m, 13/ago/2026 23:54
- Asthon Rio do Sul (Ponte Dom Tito Buss): crista de 5,27 m, 18/ago/2026 07:24
- Asthon Vidal Ramos: crista de 3,53 m, 29/ago/2026 11:28
- DC-07 Ribeirão da Murta - Portal: crista de 1,47 m, 31/ago/2026 11:13
- DC-08 Ribeirão Canhanduba - Rua Benjamin Dagnoni: crista de 2,80 m, 31/ago/2026 16:30
- Asthon Vidal Ramos: crista de 3,87 m, 31/ago/2026 22:30
- Asthon Rio do Sul (Ponte Dom Tito Buss): crista de 6,78 m, 01/set/2026 05:21
- Rio do Sul Estação MKS: crista de 7,06 m, 01/set/2026 05:45
- DC-09 Ribeirão da Murta - Ponte da Rua Lidia Puel Peixer: crista de 1,45 m, 01/set/2026 10:00
- DCSC-00041 SDC-SC Taió: crista de 5,77 m, 04/set/2026 14:31
- Asthon Vidal Ramos: crista de 3,00 m (na borda dos dados: piso), 10/set/2026 05:20
- DC-07 Ribeirão da Murta - Portal: crista de 1,08 m, 10/set/2026 05:40
- Defesa Civil de Taió: crista de 5,46 m, 10/set/2026 13:00
- DCSC-00024 SDC-SC Vidal Ramos: crista de 3,41 m, 11/set/2026 14:31
- Vidal Ramos (Asthon): crista de 3,38 m (na borda dos dados: piso), 11/set/2026 15:06
- DCSC-00020 SDC-SC Ibirama: crista de 4,16 m, 11/set/2026 20:16
- DCSC-00011 SDC-SC Rio dos Cedros 1: crista de 3,06 m, 11/set/2026 22:16
- DC-08 Ribeirão Canhanduba - Rua Benjamin Dagnoni: crista de 2,41 m, 11/set/2026 23:20
- DCSC-00023 SDC-SC Timbó 1: crista de 5,52 m, 12/set/2026 02:31
- Taió — Rio Itajaí do Oeste, Centro: crista de 6,95 m, 12/set/2026 04:13
- DCSC-00041 SDC-SC Taió: crista de 6,95 m, 12/set/2026 04:46
- DC-09 Ribeirão da Murta - Ponte da Rua Lidia Puel Peixer: crista de 1,48 m, 12/set/2026 08:30
- DCSC-00039 SDC-SC Ituporanga: crista de 3,88 m, 14/set/2026 18:00
- DCSC-00041 SDC-SC Taió: crista de 6,08 m, 15/set/2026 16:46
- Taió — Rio Itajaí do Oeste, Centro: crista de 6,08 m, 15/set/2026 17:58
- DCSC-00039 SDC-SC Ituporanga: crista de 3,10 m, 20/set/2026 06:16
- DCSC-00024 SDC-SC Vidal Ramos: crista de 3,73 m, 21/set/2026 20:00
- DC-07 Ribeirão da Murta - Portal: crista de 1,29 m, 21/set/2026 22:10
- DCSC-00011 SDC-SC Rio dos Cedros 1: crista de 3,63 m, 22/set/2026 01:15
- DC-08 Ribeirão Canhanduba - Rua Benjamin Dagnoni: crista de 2,66 m, 22/set/2026 03:00
- DCSC-00020 SDC-SC Ibirama: crista de 3,35 m, 22/set/2026 04:01
- DCSC-00023 SDC-SC Timbó 1: crista de 5,47 m, 22/set/2026 07:45
- DCSC-00041 SDC-SC Taió: crista de 6,57 m, 22/set/2026 17:01
- Taió — Rio Itajaí do Oeste, Centro: crista de 6,57 m, 22/set/2026 17:13
- DC-09 Ribeirão da Murta - Ponte da Rua Lidia Puel Peixer: crista de 1,39 m, 22/set/2026 20:50
- DCSC-00039 SDC-SC Ituporanga: crista de 4,24 m, 24/set/2026 17:31
- DCSC-00041 SDC-SC Taió: crista de 5,71 m, 26/set/2026 03:01
- Taió — Rio Itajaí do Oeste, Centro: crista de 5,70 m, 26/set/2026 05:44
- DCSC-00023 SDC-SC Timbó 1: crista de 2,04 m, 29/set/2026 00:31
- DCSC-00024 SDC-SC Vidal Ramos: crista de 4,20 m, 30/set/2026 23:31
- DC-08 Ribeirão Canhanduba - Rua Benjamin Dagnoni: crista de 1,57 m, 01/out/2026 02:10
- DCSC-00039 SDC-SC Ituporanga: crista de 4,37 m, 02/out/2026 14:31
- Taió — Rio Itajaí do Oeste, Centro: crista de 5,72 m, 02/out/2026 23:25
- DCSC-00041 SDC-SC Taió: crista de 5,72 m, 03/out/2026 00:01
- DCSC-00011 SDC-SC Rio dos Cedros 1: crista de 1,58 m, 03/out/2026 01:16
