# Tábua de Marés 2026 do Porto de Itajaí (Marinha, CHM/DHN)

Data: 09/09/2026. Bruto: `data/brutos/chm-tabua-mare-itajai-2026.pdf` (60 KB, páginas 166–168 da
Tábua de Marés 2026; sha256 `0da7287be13187f787c7f7cf2c3b9e91bad530caddb99b52b60a42c55d0f62b2`),
enviado pelo Jefferson — o host da Marinha não responde deste ambiente. Importador:
`scripts/importar_mare_chm.py`.

## O que o PDF diz de si mesmo

"PORTO DE ITAJAÍ (ESTADO DE SANTA CATARINA) - 2026 · Latitude 26° 54'.3 S · Longitude 48° 39'.2 W ·
Fuso UTC −03.0 horas · CHM 78 Componentes · Nível Médio 0.6 m · Carta 1841". Um bloco por dia, e por
extremo "HHMM ALT(m)". As duas colunas de meio mês saem intercaladas no texto extraído (01, 17, 02,
18…); o importador ordena por data.

## O que entrou em `data/mare-itajai.json`

| | |
|---|---|
| Extremos no PDF | 1.812, em 365 dias |
| Preamares | **876** |
| Baixa-mares | **878** |
| Descartados | 58 estofos (pontos que não são nem pico nem vale em relação aos vizinhos) |
| Cobertura | 01/01/2026 a 31/12/2026 |

A regra de classificação é a mesma do importador da UNIVALI: pico se não for menor que os dois
vizinhos, vale se não for maior; o que não é nenhum dos dois é descartado, não adivinhado.

**A altura entrou, com o datum escrito.** `altura_m` é em metros sobre o **Nível de Redução** da
carta 1841 (o datum da DHN). Não é régua de rio nenhum; os 0,6 m de "Nível Médio" são a altura do
nível médio do mar sobre o NR, não uma conversão para régua fluvial. O painel da foz usa o
**horário** da preamar; a altura é contexto e nunca se compara com cota de régua.

## Cruzamento com a tábua anterior (UNIVALI, setembro de 2026)

Antes de substituir, o importador pareou cada extremo de setembro da Marinha com o mais próximo
da planilha da UNIVALI (previsão harmônica do Laboratório de Oceanografia Física):

| | pareadas | mediana | máximo |
|---|---|---|---|
| preamares | 66 | **14 min** | 56 min |
| baixa-mares | 67 | **12 min** | 122 min |

Duas previsões harmônicas independentes do mesmo porto concordando em ~14 min é o esperado
(conjuntos de componentes diferentes). O que este cruzamento descartaria é erro de **fuso** — seria
um desvio sistemático de 60 min, e não há. O máximo de 122 min numa baixa-mar é um estofo
pareado com o vizinho errado, não um desvio real.

## O que muda na tela

Nada de imediato: setembro já estava coberto. No dia 1º de outubro o painel de maré da foz
continuaria funcionando, o que sem esta tábua não aconteceria. O validador parou de avisar
("baixamares vai até 30/09").

## O que fica

- Tábua de **2027**: a Marinha publica no fim do ano; repetir o `curl` da pendência A4 (ou o envio
  do PDF) e rodar `importar_mare_chm.py --pdf`. O validador avisa de novo quando faltarem 30 dias.
- `coleta_mares.py` (endpoint da Defesa Civil de Itajaí) continua vazio; se voltar, substitui esta
  tábua pela oficial da DC — comportamento esperado, registrado em `_meta`.
