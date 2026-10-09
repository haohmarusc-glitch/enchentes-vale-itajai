# Tábua de maré do porto de Itajaí: a previsão harmônica da UNIVALI (08/10/2026)

Decisão do Jefferson, 08/10/2026: "ajustar a fonte da maré para UNIVALI, a tábua que o Mauro mandou; está como
Marinha".

## O que aconteceu

| data | o quê |
|---|---|
| 03/09/2026 | Reunião com o Prof. Mauro Michelena Andrade (LOF/UNIVALI). Márcio Piazera manda a previsão de **setembro** (planilha de extremos). Entra como tábua interina, só horário (datum IBGE). |
| 09/09/2026 | A planilha acabaria em 30/09: a tábua passa para a da **Marinha** (CHM/DHN, ano inteiro, altura sobre o NR). Os textos do site e do chat passam a dizer "tábua da Marinha". |
| 23/09/2026 | Márcio Piazera manda `mare_astronomica_2026.xlsx`: a previsão do **ano inteiro**, a cada 5 min. |
| 07/10/2026 | O Prof. Mauro, com acesso ao site, escreve: "Já vi que você incluiu os dados da tábua de marés" — e o site creditava a Marinha. |
| 08/10/2026 | Esta troca: a UNIVALI volta a ser a fonte; a Marinha fica como referência de cruzamento. |

## A planilha

| | |
|---|---|
| Arquivo | `data/brutos/univali-mare-astronomica-2026.xlsx` (sha256 `59be6f37…9430a1`, 3,1 MB) |
| Estação | Marégrafo UNIVALI / Porto de Itajaí / Cabeçudas Iate Clube, lat −26,92872, lon −48,62797 |
| Fuso | UTC−3, como o e-mail declara; `quando` sai em horário local sem fuso, o contrato do site |
| Conteúdo | `data | hora | sl_fit`: 105.120 linhas, uma a cada 5 min, 01/01/2026 00:00 a 31/12/2026 23:55, sem lacunas |
| Referência vertical | **não declarada**. Média anual 0,835 m; mín. 0,077; máx. 1,559 |

## O que entrou em `data/mare-itajai.json`

Preamar e baixa-mar são os máximos e mínimos locais da curva. Uma maré mista tem ondulações de poucos
centímetros no estofo (um "pico" de 5 mm dentro de um platô), que ninguém chama de maré alta e que a Tábua da
Marinha também não publica: pares adjacentes com amplitude menor que **2 cm** saem aos pares, preservando a
alternância.

| | |
|---|---|
| Extremos na curva | 1.794 |
| Pares de ondulação tirados | 46 |
| **Preamares** | **851** (Marinha: 876) |
| **Baixa-mares** | **851** (Marinha: 878) |
| Altura | **não entra** (`referencia_altura: null`) |

## Cruzamento com a Tábua da Marinha (antes de substituir)

| | pareadas | mediana | p90 | máximo |
|---|---|---|---|---|
| preamares | 840 | **−11 min** | 28 min | 164 min |
| baixa-mares | 840 | **−7 min** | 30 min | 173 min |

A UNIVALI prevê os extremos uns 10 minutos antes da Marinha, com conjuntos de componentes diferentes; é o
esperado. O que o cruzamento descartaria é erro de **fuso** (desvio sistemático de 60 min), e não há. Os máximos
de 2–3 h são extremos secundários que uma fonte publica e a outra não, pareados com o vizinho errado.

**Altura:** o `sl_fit` fica em média **0,25 m acima** da altura da Marinha (que é sobre o Nível de Redução da carta
1841). São zeros diferentes; a planilha de setembro vinha em datum IBGE. Sem a referência escrita pela fonte, a
altura não entra — regra do projeto desde a maré medida do CIRAM (07/10/2026): número só com referência
identificada.

**As análises que precisam da curva de altura** (`analisar_chegada_itajai.py`, `nivel_antes.py` — e, por ele,
`ruas_alagadas.py` —, `estimar_zero_reguas_itajai.py`, `simular_avisos_mare.py`) leem a tábua da Marinha num
arquivo de referência, `data/mare-itajai-chm.json`, com a altura sobre o NR. `importar_mare_chm.py` grava esse
arquivo sempre (é idêntico, extremo a extremo, à tábua que o site usou de 09/09 a 08/10, então os relatórios
já gravados nos docs se reproduzem) e só toca a tábua do site com `--substituir`. Site e chat não leem a
referência — `teste_importar_mare_univali.py` trava isso.

## O que muda na tela e no chat

- `fonte_curta`: "Laboratório de Oceanografia Física da UNIVALI — previsão harmônica, marégrafo de Cabeçudas (porto
  de Itajaí)". A tela da foz, o painel da maré, a simulação de chegada, o painel da maré medida e o Monitor já
  liam esse campo.
- O chat ("como está a maré?") passa a dizer a fonte do arquivo, não "tábua da Marinha"; a frase sem cobertura
  também. O glossário, o catálogo de capacidades e o aviso da foz deixam de nomear a Marinha.
- A simulação de chegada: a coluna de altura diz "Altura (a tábua não traz)" e a nota explica por quê; a
  referência de altura, quando existir, vem de `_meta.referencia_altura`, nunca de texto fixo ("NR" estava
  escrito à mão).
- `fontes_gerais.mare_itajai` em `estacoes.json` (a "fonte de origem" da tela da foz) passa a descrever a UNIVALI.
- Horários mudam em minutos (ex.: 06/10 à tarde, preamar 23:05 em vez de 22:59; baixa-mar 18:35 em vez de 18:49).

## O que não muda

- Nenhuma régua, cota, faixa ou aviso. A maré continua sendo só horário cruzado com a janela de chegada.
- A maré **medida** do CIRAM (Balneário Camboriú) continua à parte, com referência pendente.
- O Monitor não foi tocado: a linha "m sobre o nível de redução da carta náutica" só aparece com altura, e agora
  não há altura.

## Quando a planilha de 2027 vier

`python3 scripts/importar_mare_univali.py --arquivo <planilha> --verificar`, conferir o cruzamento e rodar sem
`--verificar`. O validador avisa 30 dias antes de a tábua acabar.
