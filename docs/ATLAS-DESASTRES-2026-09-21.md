# Atlas de Desastres: o recorte da bacia, e o que ele diz

Recebido em 21/09/2026: dois JSONs gerados do lado do Jefferson a partir do
`BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv` (Sedec/MIDR + Ceped/UFSC,
base consolidada do S2ID), depois de o firewall do Atlas recusar a VPS e este
ambiente. Estão em `data/brutos/atlas-desastres-recorte-itajai-{acu,mirim}-2026-09-21.json`
**como vieram**. Não são saída do `scripts/atlas_desastres.py`: o filtro é
COBRADE 12xxx (inundação, enxurrada, alagamento) **sem** 13214 (chuvas intensas),
e o esquema é por rio, agrupado por mês.

## O que foi conferido

- **Códigos IBGE:** todos batem com `data/cemaden-rede-observacional-sc.json`,
  que traz o código por outro caminho. Nenhum divergente.
- **Tamanho:** Açu 93 episódios, 193 registros, 12 cidades, 1991–2025. Mirim 31
  episódios, 52 registros, 4 cidades, 1991–2019.
- **Out/2023 e nov/2023 existem no Açu** mesmo sem 13214.

## Itajaí: o roteiro que faltava

`enchentes.json` tem **zero** picos de Itajaí. O Atlas registra desastre
reconhecido na cidade nestas datas:

| data | tipologia | desabrigados | desalojados | mortos |
|---|---|---:|---:|---:|
| 1995-02-01 | enxurrada | 0 | 0 | 0 |
| 1999-01-23 | enxurrada | 0 | 350 | 0 |
| 2001-10-02 | inundação | 383 | 10 | 0 |
| 2003-11-06 | enxurrada | 16 | 16 | 1 |
| 2008-01-31 | enxurrada | 218 | 3 800 | 0 |
| 2008-02-20 | enxurrada | 0 | 25 511 | 0 |
| 2008-11-23 | enxurrada | 18 208 | 1 929 | 5 |
| 2009-07-23 | enxurrada | 0 | 0 | 0 |
| 2010-04-26 | enxurrada | 7 | 450 | 0 |
| 2011-09-09 | inundação | 3 215 | 45 630 | 1 |
| 2013-03-27 | enxurrada | 10 | 1 704 | 0 |
| 2013-05-13 | enxurrada | 1 | 40 | 0 |
| 2013-10-17 | inundação | 247 | 740 | 0 |
| 2015-10-20 | inundação | 0 | 0 | 0 |
| 2016-04-13 | enxurrada | 0 | 15 | 0 |
| 2017-06-05 | inundação | 59 | 50 | 0 |
| 2023-03-13 | alagamento | 130 | 75 | 0 |
| 2023-11-17 | inundação | 88 | 99 | 0 |

**Isto é data de decreto, não nível de rio.** Nada daqui entra em
`enchentes.json`: pico entra com estação, unidade e referência, e o Atlas não
tem nenhum dos três. O que a tabela dá é **onde procurar**: os boletins da
Defesa Civil de Itajaí desses dias, com a régua nomeada.

## Indaial depois de 2022

Nenhum registro 12xxx. A cheia de out/2023 em Indaial (DCSC-00006 cristou 8,83 m
em 12/10) foi registrada no S2ID como *chuvas intensas*, 13214, que este recorte
não inclui. É o motivo de o `atlas_desastres.py` incluir 13214 por padrão.

## Atlas × `enchentes.json`, por (cidade, mês)

| cidade | episódios com pico no repo | sem pico |
|---|---:|---:|
| Blumenau | 6 | 13 |
| Brusque | 3 | 14 |
| Gaspar | 3 | 12 |
| Indaial | 5 | 6 |
| Rio do Sul | 5 | 29 |

"Sem pico" não é erro do repositório: enxurrada de 1 desalojado não é cheia
de rio, e as listas municipais só trazem as grandes. É lista de conferência.

## Os maiores episódios da bacia (desabrigados + desalojados)

| episódio | cidades | pessoas | mortos |
|---|---:|---:|---:|
| set/2011 (Açu) | 12 | 182 662 | 3 |
| nov/2008 (Açu) | 12 | 72 375 | 72 |
| fev/2008 (Itajaí só) | 1 | 25 511 | 0 |
| out/2015 (Açu) | 4 | 18 677 | 1 |
| jun/2017 (Açu) | 4 | 15 889 | 0 |
| out/2013 (Açu) | 3 | 13 901 | 0 |

## O que falta

- O CSV bruto em `data/brutos/`, para o `atlas_desastres.py` produzir a saída
  canônica com 13214 e com teste. Os dois JSONs de hoje são de outra ferramenta
  e não se reproduzem daqui.
- Os boletins de Itajaí das datas acima, para virarem pico com régua.
