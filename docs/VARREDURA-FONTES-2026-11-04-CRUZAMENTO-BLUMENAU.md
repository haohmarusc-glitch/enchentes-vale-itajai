# Cruzamento da tabela do Mendeley com `enchentes.json` — Blumenau (04/11/2026)

Tarefa C do handoff de 04/11/2026: cruzar `data/brutos/varredura-fontes-2026-11-04/mendeley-blumenau-enchentes.csv`
(transcrição da "Histórico de enchentes em Blumenau", Mendeley Data, DOI 10.17632/cj64gycsw8.2, CC BY 4.0) com os
registros de Blumenau em `enchentes.json`. **Nenhum número nem referência foi alterado.** Gerado por
`python3 scripts/cruzar_mendeley_blumenau.py` (o relatório bruto está no fim); a leitura é esta.

**Decisão do Jefferson (04/11/2026, "aprovo todas" as pendências do relatório de ganhos):** o item 2 abaixo foi
aplicado por `python3 scripts/cruzar_mendeley_blumenau.py --anotar`. Os 101 registros de Blumenau que a tabela também
tem ganharam o campo `cruzamentos` (descrito em `_meta.campos`), com a fonte, o número **como a tabela publica**,
`bate_com` (com que referência de Blumenau o número bate — ou `diferente`, nos casos de 1852 e 2022), confiança
`media`, a data da conferência e este documento. O campo é citação, não nível: `pico_m`, `referencia` e
`divergencias` ficaram como estavam, o site não o lê e o validador (`valida_cruzamentos`) cobra os campos de cada
entrada. A linha de 20/11/1862, só da tabela, continua fora. Rodar de novo não duplica (a entrada da mesma fonte é
substituída).

## O que o cruzamento diz

- **101 das 102 datas da tabela já estão no projeto**, com a mesma data. A única só na tabela é 20/11/1862 (9,00 m);
  o projeto tem 08/11/1862 (9,20 m na régua, Cordero) e "1862-11" (9,00 m, compilação) — provavelmente o mesmo evento,
  com o dia diferente. Repare que a tabela também traz 20/11/1855 na coluna Dia e 21/11 na COMPLETA: dois "dia 20" em
  novembro, um deles contestado pela própria planilha.
- **A tabela não declara régua, e mistura as três referências de Blumenau** (`CLAUDE.md`, regra bloqueante):
  - **1852–2001: valores iguais aos publicados por Cordero & Medeiros (Tabela 4, zero do IBGE).** Nos 30 registros que
    o projeto já converteu para a régua de hoje, a tabela traz exatamente o `pico_publicado_m` (IBGE = régua de hoje
    − 0,20 m): 1855, 1864–1928, 1983-07-09 (15,34), 1984 (15,46), 1990–2001. Nos 51 registros que o projeto ainda
    guarda em IBGE ou sem referência (1931–1983), a tabela traz **o mesmo número** — o que confirma que ela e o projeto
    bebem na mesma fonte, não que o número esteja em régua de hoje.
  - **2008–2011: régua antiga** (régua de hoje − 0,40 m): 24/11/2008 11,52; 29/09/2009 8,06; 26/04/2010 8,46;
    31/08/2011 8,50; 09/09/2011 **12,60** (o projeto tem 13,00 na régua de hoje; 12,60 · 12,80 · 13,00 são as três
    referências de set/2011 documentadas pela FURB).
  - **2013 em diante: régua de hoje**, igual ao projeto (12 pares), inclusive as seis cheias de out/nov 2023 e
    19/05/2024.
  - É o padrão esperado da lista da Defesa Civil de Blumenau/AlertaBlu: histórico de Cordero até 2001, leituras
    próprias depois, sem reconciliar o zero na troca de régua de 2013.
- **Dois números diferem de verdade:**
  - **29/10/1852: 10,30 m na tabela × 16,30 m publicado (Cordero) / 16,50 m na régua de hoje.** Diferença de 6 m: tudo
    indica erro de digitação na tabela (16,3 → 10,3). Sem uso.
  - **05/05/2022: 9,40 × 9,41 m.** Arredondamento; a tabela escreve 9,4.
- **1977-08-18: 9,15 m** não é o valor adotado (9,45 régua / 9,25 IBGE), mas é a divergência já cadastrada da
  compilação de 1852–2017. Confirma a divergência, não a resolve.
- **28 registros só no projeto**, em três grupos: (a) cheias de Cordero entre 8 e 9,3 m que a tabela não listou (1940,
  1951, 1954-10-22, 1958, 1960, 1965, 1973-06-28, 1974, 1976-06-06, 1982-11-16, 1992-06-01, 1995) — a tabela diz
  "acima de ~8 m", mas não é completa; (b) cristas secundárias do projeto (jul–ago/1983, 08/09/2011, 06/10/2009,
  08/10/2023) e registros só com ano/mês; (c) o que é posterior a 19/05/2024 ou abaixo de 8 m (2021, 2026).

## O que fazer com isso (decisão do Jefferson)

1. **Nada a cadastrar.** A tabela não traz cheia que o projeto não tenha, salvo a data 20/11/1862, que contradiz a data
   de Cordero (08/11) sem dizer a fonte.
2. **Pode entrar como fonte de cruzamento** nos registros de Blumenau, com confiança `media`: "a compilação
   do Senac (Mendeley, CC BY 4.0) traz o mesmo número". Não acrescenta certeza sobre a régua — ela repete Cordero.
   **Aplicado em 04/11/2026** (campo `cruzamentos`, ver o alto deste documento).
3. **Os 51 registros de 1931–1983 continuam em disputa** (`REGRA_REFERENCIA_BLUMENAU`): a tabela não ajuda a
   desempatar Tabela 4 × planilha do Cordero, porque copia a Tabela 4.
4. Se um dia a tabela for citada na tela ou no chat, dizer que ela mistura referências e não informar os números dela
   como régua de hoje.

## Relatório gerado

## Cruzamento: tabela do Mendeley × `enchentes.json` (Blumenau)

Tabela: 102 linhas · projeto: 129 registros de Blumenau · pares pela mesma data: 101 · data próxima (≤ 3 dias): 0 · só na tabela: 1 · só no projeto: 28.

**Anomalias da transcrição:**
- linha 3: Ano/Mês/Dia = 20/11/1855 mas COMPLETA = 21/11/1855
- linha 6: Ano/Mês/Dia = 27/11/1868 mas COMPLETA = 27/11/2868

### Pares (mesma data)

| data | tabela (m) | projeto `pico_m` (ref.) | publicado | bate com |
|---|---|---|---|---|
| 1852-10-29 | 10,30 | 16,50 (régua) | 16,30 | **diferente** |
| 1855-11-20 | 13,30 | 13,50 (régua) | 13,30 | IBGE (régua + 0,20 m) |
| 1864-09-17 | 10,00 | 10,20 (régua) | 10,00 | IBGE (régua + 0,20 m) |
| 1868-11-27 | 13,30 | 13,50 (régua) | 13,30 | IBGE (régua + 0,20 m) |
| 1869-10-21 | 11,00 | 11,20 (régua) | 11,00 | IBGE (régua + 0,20 m) |
| 1870-10-11 | 10,00 | 10,20 (régua) | 10,00 | IBGE (régua + 0,20 m) |
| 1880-09-23 | 17,10 | 17,30 (régua) | 17,10 | IBGE (régua + 0,20 m) |
| 1888-09-23 | 12,80 | 13,00 (régua) | 12,80 | IBGE (régua + 0,20 m) |
| 1891-06-18 | 13,80 | 14,00 (régua) | 13,80 | IBGE (régua + 0,20 m) |
| 1898-12-25 | 11,30 | 11,50 (régua) | 11,30 | IBGE (régua + 0,20 m) |
| 1898-05-01 | 12,80 | 13,00 (régua) | 12,80 | IBGE (régua + 0,20 m) |
| 1900-10-02 | 12,80 | 13,00 (régua) | 12,80 | IBGE (régua + 0,20 m) |
| 1911-10-29 | 9,86 | 10,06 (régua) | 9,86 | IBGE (régua + 0,20 m) |
| 1911-10-02 | 16,90 | 17,10 (régua) | 16,90 | IBGE (régua + 0,20 m) |
| 1923-06-20 | 9,00 | 9,20 (régua) | 9,00 | IBGE (régua + 0,20 m) |
| 1925-05-14 | 10,30 | 10,50 (régua) | 10,30 | IBGE (régua + 0,20 m) |
| 1926-01-14 | 9,50 | 9,70 (régua) | 9,50 | IBGE (régua + 0,20 m) |
| 1927-10-09 | 12,30 | 12,50 (régua) | 12,30 | IBGE (régua + 0,20 m) |
| 1928-09-17 | 10,30 | 10,50 (régua) | 10,30 | IBGE (régua + 0,20 m) |
| 1928-08-15 | 10,82 | 11,02 (régua) | 10,82 | IBGE (régua + 0,20 m) |
| 1928-06-18 | 11,76 | 11,96 (régua) | 11,76 | IBGE (régua + 0,20 m) |
| 1928-05-31 | 8,20 | 8,40 (régua) | 8,20 | IBGE (régua + 0,20 m) |
| 1931-09-18 | 11,53 | 11,53 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1931-09-14 | 11,25 | 11,25 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1931-05-02 | 11,05 | 11,05 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1932-05-25 | 9,75 | 9,75 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1933-10-04 | 11,85 | 11,85 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1935-09-24 | 11,65 | 11,65 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1936-08-06 | 10,40 | 10,40 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1939-11-27 | 11,45 | 11,45 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1943-08-03 | 10,50 | 10,50 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1946-02-02 | 9,45 | 9,45 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1948-05-17 | 11,85 | 11,85 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1950-10-17 | 9,45 | 9,45 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1953-11-01 | 9,65 | 9,65 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1954-11-22 | 12,53 | 12,53 (null) | — | igual ao projeto, que está em referência null |
| 1954-05-08 | 9,56 | 9,56 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1955-05-20 | 10,61 | 10,61 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1957-09-16 | 9,44 | 9,44 (null) | — | igual ao projeto, que está em referência null |
| 1957-08-18 | 13,07 | 13,07 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1957-08-02 | 10,60 | 10,60 (null) | — | igual ao projeto, que está em referência null |
| 1957-07-20 | 9,28 | 9,28 (null) | — | igual ao projeto, que está em referência null |
| 1961-11-01 | 12,49 | 12,49 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1961-09-30 | 9,63 | 9,63 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1961-09-12 | 10,35 | 10,35 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1962-09-21 | 9,29 | 9,29 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1962-09-09 | 8,94 | 8,94 (null) | — | igual ao projeto, que está em referência null |
| 1963-09-29 | 9,67 | 9,67 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1966-02-13 | 10,07 | 10,07 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1967-02-18 | 10,50 | 10,50 (null) | — | igual ao projeto, que está em referência null |
| 1969-04-06 | 10,14 | 10,14 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1971-06-09 | 10,35 | 10,35 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1972-08-29 | 11,35 | 11,35 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1972-08-17 | 10,70 | 10,70 (null) | — | igual ao projeto, que está em referência null |
| 1973-08-29 | 12,35 | 12,35 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1973-07-28 | 9,35 | 9,35 (null) | — | igual ao projeto, que está em referência null |
| 1973-07-22 | 9,30 | 9,30 (null) | — | igual ao projeto, que está em referência null |
| 1973-07-03 | 9,00 | 9,00 (null) | — | igual ao projeto, que está em referência null |
| 1973-06-25 | 11,30 | 11,30 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1975-12-13 | 8,50 | 8,50 (null) | — | igual ao projeto, que está em referência null |
| 1975-10-04 | 12,63 | 12,63 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1976-05-29 | 10,85 | 10,85 (null) | — | igual ao projeto, que está em referência null |
| 1976-05-15 | 8,30 | 8,30 (null) | — | igual ao projeto, que está em referência null |
| 1977-08-18 | 9,15 | 9,45 (régua) | 9,25 | divergência já cadastrada |
| 1978-12-26 | 11,50 | 11,50 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1979-10-09 | 10,45 | 10,45 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1979-05-10 | 9,45 | 9,45 (null) | — | igual ao projeto, que está em referência null |
| 1980-12-22 | 13,27 | 13,27 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1980-07-31 | 8,40 | 8,40 (null) | — | igual ao projeto, que está em referência null |
| 1982-11-15 | 8,65 | 8,65 (null) | — | igual ao projeto, que está em referência null |
| 1983-09-24 | 11,75 | 11,75 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1983-07-09 | 15,34 | 15,54 (régua) | 15,34 | IBGE (régua + 0,20 m) |
| 1983-05-20 | 12,52 | 12,52 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1983-03-04 | 10,60 | 10,60 (IBGE (régua + 0,20 m)) | — | igual ao projeto, que está em IBGE (régua + 0,20 m) |
| 1984-08-07 | 15,46 | 15,66 (régua) | 15,46 | IBGE (régua + 0,20 m) |
| 1990-07-21 | 8,82 | 9,02 (régua) | 8,82 | IBGE (régua + 0,20 m) |
| 1992-07-01 | 10,62 | 10,82 (régua) | 10,62 | IBGE (régua + 0,20 m) |
| 1992-05-29 | 12,80 | 13,00 (régua) | 12,80 | IBGE (régua + 0,20 m) |
| 1997-02-01 | 9,44 | 9,64 (régua) | 9,44 | IBGE (régua + 0,20 m) |
| 1998-04-28 | 8,24 | 8,44 (régua) | 8,24 | IBGE (régua + 0,20 m) |
| 1999-07-03 | 8,26 | 8,46 (régua) | 8,26 | IBGE (régua + 0,20 m) |
| 2001-10-01 | 11,02 | 11,22 (régua) | 11,02 | IBGE (régua + 0,20 m) |
| 2008-11-24 | 11,52 | 11,92 (régua) | 11,52 | régua antiga |
| 2009-09-29 | 8,06 | 8,46 (régua) | 8,06 | régua antiga |
| 2010-04-26 | 8,46 | 8,86 (régua) | 8,46 | régua antiga |
| 2011-09-09 | 12,60 | 13,00 (régua) | 12,80 | régua antiga |
| 2011-08-31 | 8,50 | 8,90 (régua) | 8,50 | régua antiga |
| 2013-09-23 | 10,51 | 10,51 (null) | — | igual ao projeto, que está em referência null |
| 2014-06-29 | 8,13 | 8,13 (régua) | — | régua de hoje |
| 2014-06-09 | 10,18 | 10,18 (régua) | — | régua de hoje |
| 2015-10-23 | 10,03 | 10,03 (régua) | — | régua de hoje |
| 2017-06-06 | 8,52 | 8,52 (régua) | — | régua de hoje |
| 2017-06-01 | 8,71 | 8,71 (régua) | — | régua de hoje |
| 2022-05-05 | 9,40 | 9,41 (régua) | — | **diferente** |
| 2023-11-17 | 9,14 | 9,14 (régua) | — | régua de hoje |
| 2023-11-03 | 9,50 | 9,50 (régua) | — | régua de hoje |
| 2023-10-29 | 8,38 | 8,38 (régua) | — | régua de hoje |
| 2023-10-12 | 10,76 | 10,76 (régua) | — | régua de hoje |
| 2023-10-09 | 10,19 | 10,19 (régua) | — | régua de hoje |
| 2023-10-05 | 8,78 | 8,78 (régua) | — | régua de hoje |
| 2024-05-19 | 8,67 | 8,67 (régua) | — | régua de hoje |

### Data próxima (mesmo evento, dia diferente?)

| tabela | projeto | tabela (m) | projeto (m) | bate com |
|---|---|---|---|---|

### Só na tabela

| data | cota (m) | categoria |
|---|---|---|
| 1862-11-20 | 9,00 |  |

### Só no projeto

| data | `pico_m` (ref.) | confiança |
|---|---|---|
| 1862-11 | 9,00 (null) | media |
| 1862-11-08 | 9,20 (régua) | alta |
| 1888-01 | 12,80 (null) | media |
| 1928-07-18 | 11,96 (régua) | alta |
| 1940-08-26 | 8,55 (IBGE (régua + 0,20 m)) | alta |
| 1951-10-19 | 9,00 (IBGE (régua + 0,20 m)) | alta |
| 1954-10-22 | 12,53 (IBGE (régua + 0,20 m)) | alta |
| 1958-03-16 | 9,31 (IBGE (régua + 0,20 m)) | alta |
| 1960-08-19 | 8,29 (IBGE (régua + 0,20 m)) | alta |
| 1965-08-21 | 9,22 (IBGE (régua + 0,20 m)) | alta |
| 1973-06-28 | 9,35 (IBGE (régua + 0,20 m)) | alta |
| 1974-07-24 | 9,00 (IBGE (régua + 0,20 m)) | alta |
| 1976-06-06 | 9,00 (IBGE (régua + 0,20 m)) | alta |
| 1982-11-16 | 8,15 (IBGE (régua + 0,20 m)) | alta |
| 1983-07-18 | 10,95 (null) | media |
| 1983-07-27 | 10,38 (null) | media |
| 1983-07-29 | 11,08 (null) | media |
| 1983-08-02 | 11,20 (null) | media |
| 1992-06-01 | 10,82 (régua) | alta |
| 1995-01-10 | 8,51 (régua) | alta |
| 2009-10-06 | 8,17 (null) | media |
| 2011-09-08 | 11,60 (null) | media |
| 2013 | 10,51 (null) | baixa |
| 2021-01-21 | 6,82 (régua) | alta |
| 2023-10-08 | 9,49 (régua) | media |
| 2026-07-12 | 5,65 (null) | media |
| 2026-09-01 | 7,58 (régua) | alta |
| 2026-09-12 | 7,87 (régua) | alta |

### Com que referência a tabela bate

| bate com | pares |
|---|---|
| igual ao projeto, que está em IBGE (régua + 0,20 m) | 34 |
| IBGE (régua + 0,20 m) | 30 |
| igual ao projeto, que está em referência null | 17 |
| régua de hoje | 12 |
| régua antiga | 5 |
| diferente | 2 |
| divergência já cadastrada | 1 |

