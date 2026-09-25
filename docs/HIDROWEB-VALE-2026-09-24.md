# HidroWeb do Itajaí-Açu — picos das séries da ANA (24/09/2026)

Onze estações convencionais da ANA, exportadas do HidroWeb pelo Jefferson em 24/09/2026. Os zips
estão como vieram em `data/brutos/pesquisa-picos-2026-09-24/ana/`, e três deles vieram vazios
(83145140, 83301000, 83664000). Os picos saem de `scripts/picos_ana_vale.py` e ficam gravados em
`data/brutos/pesquisa-picos-2026-09-24/picos_ana_vale.json`, com 9 testes em `scripts/teste_picos_ana_vale.py`.

**Entraram em `enchentes.json` só os 5 maiores eventos de quatro estações, por decisão do Jefferson
(24/09/2026): Ituporanga (83250000), Ibirama (83440000), Apiúna (83500000) e Ilhota (83860000).** São
20 registros com `confianca: baixa`, o zero da ANA dito na nota, a `pendencia` "crista não medida, zero
não comparado" e sem a chave `referencia`, como os de Brusque. O chat avisa que são da régua da ANA.
O resto da lista abaixo fica só aqui.

## Como ler os números

- **Cota em metros, no zero da ANA.** Não é a régua da Defesa Civil, até alguém provar o contrário.
- **Leitura das 07h/17h é o PISO da crista.** Nas cheias grandes, a crista cai entre as duas
  leituras. Brusque mostrou isso (`docs/HIDROWEB-MIRIM-2026-09-22.md`), e Timbó mostra de novo em 2011:
  no dia da crista (09/09) não há leitura, só a média do dia.
- **Média diária fica ainda mais longe da crista.** Várias estações só têm média por décadas:
  Ilhota de 1927 a 1988, Timbó de 1929 a 1999 e Trombudo Central de 1942 a 1967.
- **Evento** é uma corrida de dias acima do limiar da estação, separada da próxima por mais de 5 dias.
  O limiar é o 15.º maior máximo anual, para cada estação dar os seus ~15 maiores eventos sem
  limiar escolhido à mão. Leituras duvidosas (status 3) e erros de digitação ficam fora.

## O que a comparação com o cadastro mostra

**Taió: desde 2015, a régua municipal e a da ANA 83050000 andam juntas, a menos de 10 cm.** São seis
eventos: out/2015 −0,10, jun/2017 +0,07, mai/2022 +0,02, 09/10/2023 +0,08, 04/11/2023 +0,04 e
nov/2023 +0,05 m. É a primeira evidência numérica sobre o zero de uma régua municipal do Açu. Isso
não derruba a decisão (b), porque diferença pequena não é prova de mesmo zero, mas muda a conversa.
Antes de 2015 a diferença some ou dispara: 1983 −1,06, set/2011 +1,02, jun/2014 −0,46 m. Em 2011 e
1983 a ANA só tem a média do dia, então a diferença não diz nada sobre o zero.

**Taió 2013: a tabela municipal provavelmente errou o mês.** Ela diz "junho de 2013, 9,38 m". A ANA
tem 6,80 m como máximo de junho e 9,70 m em 23/09/2013, e a grande cheia de 2013 no Vale foi em
setembro. O registro ganhou uma `pendencia`, e a data NÃO mudou.

**Timbó:** em 12/10/2023, a Timbó Novo (83677000) leu 7,30 m às 17h, e o pico municipal foi 7,46 m às
21h. Isso é coerente com a mesma régua e a crista caindo depois da leitura, mas é um evento só. Em
2011, a diferença de 1,36 m é a crista perdida (não há leitura no dia 09/09). Em 2014, a Câmara diz
9,58 m e a ANA leu 9,00 m às 07h de 09/06.

**Porto Itajaí (83920000, 1927–1937):** só tem médias diárias e o máximo é 2,50 m. É régua de
estuário com maré e não serve para pico de cheia em Itajaí.

## O que entrou, e o que ficou fora

As quatro cidades que entraram não tinham nenhum pico e têm série longa da ANA. O precedente é
Brusque (22/09/2026), com uma diferença: lá o zero da ANA tinha sido provado igual ao municipal em
2019–2021, e aqui não foi provado em nenhuma estação. Por isso a confiança é baixa, e não alta.

- **Ilhota: só a 83860000 "ILHOTA"** (1927–1988, só médias diárias, com 1983 e 1984). A Ilhota-Jusante
  (83870000, 1989–2007, com 11,52 m em 30/05/1992) e a Ilhota-Montante ficam fora. São outros zeros, e
  misturá-los numa cidade só faria a série saltar sem cheia.
- **Taió e Timbó (atualizado em 25/09/2026):** por decisão do Jefferson, entraram as cheias da ANA
  que a série municipal **não tem**. São 7 em Taió (1931, 1933, 1954, 1957, 1963, 1984 e abr/2010) e 26 em
  Timbó, com as duas estações, que têm o mesmo zero: 0 cm de diferença nos 31 dias comuns de 1998–1999.
  Todas estão marcadas como régua da ANA, com confiança baixa. Onde já havia registro municipal do mesmo
  evento, a ANA ficou fora: foram 12 casos, entre eles Taió jul/1983 (registro "1983"), Taió set/2013
  (provavelmente o "junho de 2013" da tabela) e Timbó jun/2014 (registro "2014"). A decisão (b) continua
  valendo para esses eventos, porque o valor adotado é o municipal.
- **Trombudo Central fica fora:** a série vai só até 1967 e só tem médias diárias brutas.
- **Porto Itajaí fica fora:** é régua de estuário.
- **Validador:** Apiúna e Ilhota entraram em `LISTAS_SO_COM_CHEIA_GRANDE`, porque uma lista feita só
  dos 5 maiores não tem par para as cheias médias de montante. Apiúna 29/08/1946 × Blumenau ficou
  nomeado entre os desalinhamentos conhecidos, sem correção.

## Picos por estação

### 83050000 — TAIÓ (rio Itajaí do Oeste, 1.570 km²)

Período 19/04/1929 a 30/04/2026; 35.434 dias com valor, 18.619 com leitura das 07h/17h.

| # | Data | Cota ANA | Origem |
|---|---|---|---|
| 1 | 12/07/1983 | 12,91 m | média do dia (consistida) |
| 2 | 04/10/1933 | 12,37 m | leitura 07h |
| 3 | 09/10/2023 | 12,32 m | leitura 17h |
| 4 | 01/02/1963 | 11,25 m | média do dia (consistida) |
| 5 | 23/10/2015 | 10,85 m | leitura 17h |
| 6 | 22/10/1954 | 10,65 m | média do dia (consistida) |
| 7 | 10/09/2011 | 10,63 m | média do dia (consistida) |
| 8 | 04/11/2023 | 10,32 m | leitura 17h |
| 9 | 17/11/2023 | 10,30 m | leitura 17h |
| 10 | 19/08/1957 | 10,25 m | média do dia (consistida) |
| 11 | 27/04/2010 | 9,78 m | leitura 17h |
| 12 | 23/09/2013 | 9,70 m | leitura 17h |
| 13 | 05/05/2022 | 9,68 m | leitura 07h |
| 14 | 02/05/1931 | 9,60 m | média do dia (consistida) |
| 15 | 09/08/1984 | 9,57 m | média do dia (consistida) |

Contra o cadastro (`enchentes.json`, régua municipal):

| Cadastro | Par | ANA | Diferença (cadastro − ANA) |
|---|---|---|---|
| 1983: 11,85 m | ano | 12/07/1983: 12,91 m (média do dia (consistida)) | −1,06 m |
| 09/2011: 11,65 m | mes | 10/09/2011: 10,63 m (média do dia (consistida)) | +1,02 m |
| 06/2013: 9,38 m | mes | 22/06/2013: 6,80 m (leitura 07h) | +2,58 m |
| 06/2014: 8,91 m | mes | 09/06/2014: 9,37 m (leitura 17h) | −0,46 m |
| 10/2015: 10,75 m | mes | 23/10/2015: 10,85 m (leitura 17h) | −0,10 m |
| 06/2017: 8,18 m | mes | 03/06/2017: 8,11 m (leitura 07h) | +0,07 m |
| 05/2022: 9,70 m | mes | 05/05/2022: 9,68 m (leitura 07h) | +0,02 m |
| 09/10/2023: 12,40 m | dia | 09/10/2023: 12,32 m (leitura 17h) | +0,08 m |
| 11/2023: 10,37 m | mes | 04/11/2023: 10,32 m (leitura 17h) | +0,05 m |
| 04/11/2023: 10,36 m | dia | 04/11/2023: 10,32 m (leitura 17h) | +0,04 m |

### 83070000 — TROMBUDO CENTRAL (rio Trombudo, 561 km²)

Período 02/06/1942 a 31/08/1967; 9.222 dias com valor, 0 com leitura das 07h/17h.

| # | Data | Cota ANA | Origem |
|---|---|---|---|
| 1 | 21/10/1954 | 8,02 m | média do dia (bruta) |
| 2 | 18/08/1957 | 7,54 m | média do dia (bruta) |
| 3 | 31/01/1963 | 7,45 m | média do dia (bruta) |
| 4 | 17/02/1966 | 7,14 m | média do dia (bruta) |
| 5 | 24/03/1963 | 6,67 m | média do dia (bruta) |
| 6 | 02/11/1961 | 6,65 m | média do dia (bruta) |
| 7 | 28/09/1963 | 6,55 m | média do dia (bruta) |
| 8 | 02/08/1957 | 6,35 m | média do dia (bruta) |
| 9 | 31/10/1953 | 6,28 m | média do dia (bruta) |
| 10 | 02/08/1948 | 5,83 m | média do dia (bruta) |
| 11 | 06/09/1965 | 5,81 m | média do dia (bruta) |
| 12 | 11/09/1961 | 5,78 m | média do dia (bruta) |
| 13 | 20/08/1965 | 5,77 m | média do dia (bruta) |
| 14 | 18/05/1955 | 5,43 m | média do dia (bruta) |
| 15 | 18/10/1951 | 5,35 m | média do dia (bruta) |

### 83250000 — ITUPORANGA (rio Itajaí do Sul, 1.650 km²)

Período 20/04/1929 a 30/04/2026; 35.440 dias com valor, 12.386 com leitura das 07h/17h.

| # | Data | Cota ANA | Origem |
|---|---|---|---|
| 1 | 09/09/2011 | 7,63 m | leitura 07h |
| 2 | 17/11/2023 | 6,88 m | leitura 17h |
| 3 | 11/07/1983 | 6,65 m | média do dia (consistida) |
| 4 | 07/08/1984 | 5,74 m | média do dia (consistida) |
| 5 | 27/09/1963 | 5,65 m | média do dia (consistida) |
| 6 | 01/08/1983 | 5,40 m | média do dia (consistida) |
| 7 | 02/08/1943 | 5,35 m | média do dia (consistida) |
| 8 | 01/02/1963 | 5,20 m | média do dia (consistida) |
| 9 | 12/10/2023 | 5,10 m | leitura 17h |
| 10 | 21/10/1954 | 5,04 m | média do dia (consistida) |
| 11 | 01/11/1961 | 5,00 m | média do dia (consistida) |
| 12 | 18/08/1957 | 4,98 m | média do dia (consistida) |
| 13 | 21/10/2015 | 4,98 m | leitura 17h |
| 14 | 02/08/1948 | 4,80 m | média do dia (consistida) |
| 15 | 05/06/2017 | 4,66 m | leitura 07h |

### 83440000 — IBIRAMA (rio Itajaí do Norte (Hercílio), 3.330 km²)

Período 01/12/1928 a 31/12/2021; 33.999 dias com valor, 11.294 com leitura das 07h/17h.

| # | Data | Cota ANA | Origem |
|---|---|---|---|
| 1 | 08/07/1983 | 6,90 m | média do dia (consistida) |
| 2 | 21/12/1980 | 6,41 m | média do dia (consistida) |
| 3 | 29/05/1992 | 5,85 m | leitura 17h |
| 4 | 20/05/1983 | 5,65 m | média do dia (consistida) |
| 5 | 28/03/1989 | 5,54 m | leitura 07h |
| 6 | 06/08/1984 | 5,52 m | média do dia (consistida) |
| 7 | 24/05/1988 | 5,44 m | média do dia (consistida) |
| 8 | 24/09/1935 | 5,04 m | média do dia (consistida) |
| 9 | 01/07/1992 | 4,98 m | leitura 07h |
| 10 | 18/08/1957 | 4,96 m | média do dia (consistida) |
| 11 | 02/10/1975 | 4,85 m | média do dia (consistida) |
| 12 | 04/03/1983 | 4,82 m | média do dia (consistida) |
| 13 | 25/06/1973 | 4,80 m | média do dia (consistida) |
| 14 | 26/11/1939 | 4,79 m | média do dia (consistida) |
| 15 | 08/10/1979 | 4,76 m | média do dia (consistida) |

### 83500000 — APIÚNA - RÉGUA NOVA (rio Itajaí-Açu, 9.070 km²)

Período 01/01/1946 a 30/04/2026; 11.293 dias com valor, 10.530 com leitura das 07h/17h.

| # | Data | Cota ANA | Origem |
|---|---|---|---|
| 1 | 09/09/2011 | 8,08 m | leitura 07h |
| 2 | 12/10/2023 | 7,26 m | leitura 17h |
| 3 | 17/11/2023 | 7,18 m | leitura 07h |
| 4 | 22/09/2013 | 7,14 m | leitura 17h |
| 5 | 29/08/1946 | 6,99 m | leitura 17h |
| 6 | 22/10/2015 | 6,98 m | leitura 17h |
| 7 | 01/10/2001 | 6,72 m | leitura 17h |
| 8 | 04/05/2022 | 6,50 m | leitura 17h |
| 9 | 08/12/2010 | 6,24 m | leitura 17h |
| 10 | 06/06/2017 | 6,14 m | leitura 07h |
| 11 | 08/06/2014 | 6,12 m | leitura 17h |
| 12 | 19/05/2024 | 6,10 m | leitura 07h |
| 13 | 30/08/2011 | 6,06 m | leitura 17h |
| 14 | 03/11/2023 | 5,98 m | leitura 17h |
| 15 | 28/06/2014 | 5,84 m | leitura 17h |

### 83680000 — TIMBÓ (rio Benedito, 1.600 km²)

Período 01/01/1929 a 31/01/1999; 22.251 dias com valor, 215 com leitura das 07h/17h.

| # | Data | Cota ANA | Origem |
|---|---|---|---|
| 1 | 07/08/1984 | 7,97 m | média do dia (consistida) |
| 2 | 12/07/1983 | 7,48 m | média do dia (consistida) |
| 3 | 23/03/1974 | 7,24 m | média do dia (consistida) |
| 4 | 21/12/1980 | 7,03 m | média do dia (consistida) |
| 5 | 20/05/1983 | 7,00 m | média do dia (consistida) |
| 6 | 15/05/1965 | 6,83 m | média do dia (consistida) |
| 7 | 17/05/1948 | 6,70 m | média do dia (consistida) |
| 8 | 14/08/1998 | 6,65 m | leitura 07h |
| 9 | 15/02/1948 | 6,61 m | média do dia (consistida) |
| 10 | 01/11/1961 | 6,59 m | média do dia (consistida) |
| 11 | 26/12/1978 | 6,42 m | média do dia (consistida) |
| 12 | 24/09/1935 | 6,34 m | média do dia (consistida) |
| 13 | 28/08/1973 | 6,33 m | média do dia (consistida) |
| 14 | 28/11/1960 | 6,15 m | média do dia (consistida) |
| 15 | 02/02/1946 | 6,10 m | média do dia (consistida) |

### 83677000 — TIMBÓ NOVO (rio Benedito, 1.600 km²)

Período 01/09/1989 a 31/03/2026; 13.284 dias com valor, 12.519 com leitura das 07h/17h.

| # | Data | Cota ANA | Origem |
|---|---|---|---|
| 1 | 29/05/1992 | 9,10 m | leitura 17h |
| 2 | 09/06/2014 | 9,00 m | leitura 07h |
| 3 | 08/09/2011 | 8,50 m | leitura 17h |
| 4 | 23/11/2008 | 8,15 m | leitura 17h |
| 5 | 01/10/2001 | 7,95 m | leitura 17h |
| 6 | 21/01/2021 | 7,59 m | leitura 17h |
| 7 | 03/11/2023 | 7,46 m | leitura 17h |
| 8 | 12/10/2023 | 7,30 m | leitura 17h |
| 9 | 23/10/2015 | 7,20 m | leitura 07h |
| 10 | 04/05/2022 | 7,10 m | leitura 17h |
| 11 | 16/02/2000 | 6,99 m | leitura 07h |
| 12 | 12/05/1994 | 6,95 m | leitura 07h |
| 13 | 26/04/2010 | 6,90 m | leitura 17h |
| 14 | 11/03/2011 | 6,84 m | leitura 07h |
| 15 | 23/09/2013 | 6,72 m | leitura 07h |

Contra o cadastro (`enchentes.json`, régua municipal):

| Cadastro | Par | ANA | Diferença (cadastro − ANA) |
|---|---|---|---|
| 09/09/2011: 9,86 m | dia | 08/09/2011: 8,50 m (leitura 17h) | +1,36 m |
| 2014: 9,58 m | ano | 09/06/2014: 9,00 m (leitura 07h) | +0,58 m |
| 12/10/2023: 7,46 m | dia | 12/10/2023: 7,30 m (leitura 17h) | +0,16 m |

### 83860000 — ILHOTA (rio Itajaí-Açu, 12.700 km²)

Período 01/10/1927 a 31/01/1988; 21.942 dias com valor, 0 com leitura das 07h/17h.

| # | Data | Cota ANA | Origem |
|---|---|---|---|
| 1 | 10/07/1983 | 10,45 m | média do dia (consistida) |
| 2 | 08/08/1984 | 10,06 m | média do dia (consistida) |
| 3 | 03/08/1943 | 8,62 m | média do dia (consistida) |
| 4 | 23/10/1954 | 8,62 m | média do dia (consistida) |
| 5 | 03/11/1961 | 8,60 m | média do dia (consistida) |
| 6 | 29/08/1973 | 8,56 m | média do dia (consistida) |
| 7 | 18/05/1948 | 8,54 m | média do dia (consistida) |
| 8 | 22/12/1980 | 8,52 m | média do dia (consistida) |
| 9 | 19/08/1957 | 8,50 m | média do dia (consistida) |
| 10 | 03/10/1975 | 8,44 m | média do dia (consistida) |
| 11 | 02/08/1983 | 8,42 m | média do dia (consistida) |
| 12 | 04/10/1933 | 8,40 m | média do dia (consistida) |
| 13 | 21/05/1983 | 8,31 m | média do dia (consistida) |
| 14 | 29/08/1972 | 8,28 m | média do dia (consistida) |
| 15 | 02/05/1931 | 8,25 m | média do dia (consistida) |

### 83859998 — ILHOTA - MONTANTE (rio Itajaí-Açu, 12.700 km²)

Período 10/12/1987 a 30/06/1989; 325 dias com valor, 0 com leitura das 07h/17h.

| # | Data | Cota ANA | Origem |
|---|---|---|---|
| 1 | 06/05/1989 | 8,67 m | média do dia (consistida) |
| 2 | 06/01/1989 | 7,81 m | média do dia (consistida) |
| 3 | 02/02/1989 | 7,15 m | média do dia (consistida) |
| 4 | 24/02/1989 | 6,75 m | média do dia (consistida) |
| 5 | 22/09/1988 | 6,53 m | média do dia (consistida) |
| 6 | 27/10/1988 | 6,33 m | média do dia (consistida) |
| 7 | 03/04/1989 | 6,05 m | média do dia (consistida) |
| 8 | 25/06/1989 | 5,59 m | média do dia (consistida) |
| 9 | 08/03/1989 | 5,53 m | média do dia (consistida) |
| 10 | 07/06/1989 | 5,47 m | média do dia (consistida) |
| 11 | 28/03/1989 | 5,35 m | média do dia (consistida) |
| 12 | 22/12/1987 | 5,34 m | média do dia (consistida) |

### 83870000 — ILHOTA-JUSANTE (rio Itajaí-Açu, 12.357 km²)

Período 01/01/1989 a 31/10/2007; 6.847 dias com valor, 6.160 com leitura das 07h/17h.

| # | Data | Cota ANA | Origem |
|---|---|---|---|
| 1 | 30/05/1992 | 11,52 m | leitura 17h |
| 2 | 02/07/1992 | 10,00 m | leitura 07h |
| 3 | 02/10/2001 | 9,70 m | leitura 07h |
| 4 | 21/07/1990 | 9,48 m | leitura 17h |
| 5 | 01/02/1997 | 9,43 m | leitura 17h |
| 6 | 12/10/1990 | 9,20 m | leitura 07h |
| 7 | 25/12/1998 | 8,92 m | leitura 17h |
| 8 | 14/09/1989 | 8,90 m | leitura 07h |
| 9 | 20/01/1990 | 8,86 m | leitura 07h |
| 10 | 12/05/1994 | 8,86 m | média do dia (consistida) |
| 11 | 07/06/1990 | 8,80 m | leitura 07h |
| 12 | 06/05/1989 | 8,74 m | leitura 07h |
| 13 | 24/09/1993 | 8,70 m | leitura 17h |
| 14 | 04/07/1999 | 8,58 m | leitura 07h |
| 15 | 10/01/1995 | 8,48 m | leitura 17h |

### 83920000 — PORTO ITAJAÍ (rio Itajaí-Açu, 15.200 km²)

Período 12/09/1927 a 30/11/1937; 3.670 dias com valor, 0 com leitura das 07h/17h.

| # | Data | Cota ANA | Origem |
|---|---|---|---|
| 1 | 27/04/1933 | 2,50 m | média do dia (bruta) |
| 2 | 17/09/1930 | 2,00 m | média do dia (bruta) |
| 3 | 04/10/1935 | 1,99 m | média do dia (bruta) |
| 4 | 31/03/1929 | 1,98 m | média do dia (bruta) |
| 5 | 01/11/1932 | 1,94 m | média do dia (bruta) |
| 6 | 03/05/1931 | 1,93 m | média do dia (bruta) |
| 7 | 09/08/1936 | 1,93 m | média do dia (bruta) |
| 8 | 03/09/1930 | 1,92 m | média do dia (bruta) |
| 9 | 08/08/1932 | 1,92 m | média do dia (bruta) |
| 10 | 30/05/1929 | 1,90 m | média do dia (bruta) |
| 11 | 08/11/1929 | 1,90 m | média do dia (bruta) |
| 12 | 04/07/1930 | 1,90 m | média do dia (bruta) |
| 13 | 25/09/1933 | 1,90 m | média do dia (bruta) |
| 14 | 14/07/1933 | 1,89 m | média do dia (bruta) |
| 15 | 09/06/1932 | 1,88 m | média do dia (bruta) |
