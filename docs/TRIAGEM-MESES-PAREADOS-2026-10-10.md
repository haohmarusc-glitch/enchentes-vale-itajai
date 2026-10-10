# Triagem dos avisos "sem evento no mesmo mês" — 10/10/2026

O `validar_dados.py` (`valida_meses_pareados`) avisa quando uma cheia de uma cidade do tronco não tem cheia da
cidade de baixo no mesmo mês. Em 10/10/2026 eram **36 avisos**. Cada um foi cruzado com o Atlas Digital de
Desastres (`data/desastres/eventos.json`, 1991–2025, decretos e registros oficiais por município) e com a data das
outras cheias do mesmo ano.

**Nada foi alterado em `enchentes.json`.** Este documento só separa o que é provavelmente certo do que merece
conferência na fonte.

## Resumo

| grupo | avisos | o que indica | ação |
|---|---|---|---|
| A. Cheia de Rio do Sul confirmada pelo Atlas só em Rio do Sul | 14 | cheia do Alto Vale que não chegou à cota das cidades de baixo, ou que lá não gerou decreto | nenhuma: a data de Rio do Sul tem apoio oficial |
| B. Sem dado no Atlas (antes de 1991, ou Atlas vazio nas duas cidades) | 19 | não dá para separar evento distinto de data errada | só com a fonte original de cada registro |
| C. Registro que falta na cidade de baixo | 1 (Vidal Ramos → Botuverá; o caso de Brusque sai do D.2) | o evento existe nas duas cidades; a de baixo não tem registro | candidato a cadastro, por decisão |
| D. Possível erro de mês | 2 | mesmo dia, mês vizinho, em fontes diferentes | conferir na fonte |

## A. Confirmados pelo Atlas só em Rio do Sul (14 avisos, 8 cheias)

| Rio do Sul | Atlas em Rio do Sul | cidades de baixo sem registro (e sem Atlas no mês) |
|---|---|---|
| 1997-10 | 11/10/1997, inundação | Blumenau |
| 2011-08 | 09/08/2011, enxurrada | Indaial, Itajaí |
| 2014-06 | 11/06/2014, inundação | Indaial |
| 2014-10 | 10/10/2014, inundação | Indaial, Blumenau |
| 2022-06 | 22/06/2022, chuvas intensas | Indaial, Blumenau |
| 2022-10 | 10/10/2022, inundação | Indaial, Blumenau |
| 2023-07 | 13/07/2023, inundação | Lontras, Blumenau |
| 2024-07-12 | 08/07/2024, chuvas intensas | Lontras, Blumenau |

A cheia que enche Rio do Sul nem sempre passa da cota em Indaial ou Blumenau. O aviso é verdadeiro (não há par), mas
a data de cima tem apoio oficial.

## C. Registro que falta na cidade de baixo

1. **Brusque, dezembro de 2023.** O Boletim Hidrometeorológico 001/2024 (SDE/SC, ed. 57, p. 14, Tabela 1 — o bruto
   já está em `data/brutos/pesquisa-picos-2026-09-24/rodada4/`) traz, na mesma tabela:
   - **Botuverá 3,58 m em 03/12/2023 às 23h00**, "Emergência" — é o registro que o validador acusa, e ele está certo;
   - **Brusque 3,88 m em 04/12/2023 às 05h00**, "Emergência", estação da DCSC.

   A régua de Brusque é a DCSC-00019 desde 03/10/2026 (`regua_das_cotas_id`). Brusque não tem registro em dezembro
   de 2023: a lista de 2019–2024 da Rádio Cidade/Prefeitura não traz essa cheia. **Candidato a cadastro**:
   - 3,88 m em 04/12/2023 05:00, confiança baixa, como os demais máximos de boletim estadual;
   - antes, conferir no PDF que a estação do boletim é a DCSC-00019 (o boletim diz só "Demais estações: DCSC").

   Só entra por decisão do Jefferson.
2. **Botuverá, novembro de 2023.** Vidal Ramos tem 4,86 m em 17/11/2023 (Boletim 011/2023), e o Atlas registra
   chuvas intensas em Botuverá em 16/11/2023. Botuverá não tem registro em novembro de 2023. É candidato a busca:
   não há número de Botuverá nesse boletim já baixado.

## D. Possível erro de mês (conferir na fonte)

1. **Indaial 09/11/1927 (6,55 m) × Blumenau 09/10/1927 (12,50 m na régua; 12,30 m publicado no IBGE).** Mesmo dia
   9, meses vizinhos, as duas séries de trabalhos do Prof. Ademar Cordero:
   - Indaial vem do PDF "cotas de enchente" da Defesa Civil de Indaial;
   - Blumenau vem da Tabela 4 de Cordero & Medeiros, via Itajaípedia.

   Uma das duas pode ter o mês trocado, ou foram duas cheias. A análise do histórico de Gaspar (C10) já usava
   "Indaial, 09/11/1927" como evento conhecido. Conferir nas duas fontes antes de mexer.
2. **Botuverá 03/12/2023 × Brusque 03/11/2023**: o validador acusa "mesmo dia", mas **não é erro**. O boletim de
   dezembro confirma 03/12 em Botuverá (ver C.1).

## B. Sem como decidir agora (19 avisos)

| cidade de cima | data | cidade de baixo |
|---|---|---|
| Rio do Sul | 1927-06 | Indaial, Blumenau |
| Rio do Sul | 1933-09, 1939-08, 1948-10, 1953-10 | Blumenau |
| Rio do Sul | 1957-07, 1957-09, 1983-09 | Indaial |
| Rio do Sul | 2011-07 | Indaial, Blumenau, Itajaí |
| Rio do Sul | 2015-09 | Indaial, Blumenau |
| Rio do Sul | 2023-10-13 | Lontras (Atlas de Lontras em 04/10/2023) |
| Apiúna | 1946-08-29 | Blumenau |
| Indaial | 2014-09-08 | Blumenau |
| Blumenau, Gaspar | 2011-08-31 | Itajaí (que só tem 09/09/2011) |

- **Rio do Sul 1953-10 × Blumenau 01/11/1953:** pode ser a virada do mês (a série de Rio do Sul é mensal).
- **Rio do Sul 1933-09 × Blumenau 04/10/1933:** idem.
- **Itajaí:** tem só dois registros no cadastro; a ausência ali é do cadastro, não da cheia.

## Como refazer

```bash
cd scripts && python3 validar_dados.py 2>&1 | grep "não tem evento de" > /tmp/meses.txt
# cruzar cada (cidade, mês) com data/desastres/eventos.json, campo data_evento e municipio
```
