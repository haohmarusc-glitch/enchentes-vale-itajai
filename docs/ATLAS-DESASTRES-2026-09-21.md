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

## Rodada contra a base real, do lado do Jefferson (21/09/2026)

O CSV completo foi lido fora daqui, com leitor CSV de verdade. Números
relatados:

| | |
|---|---:|
| registros nacionais | 76.190 |
| colunas | 70 |
| linhas físicas | mais de 210 mil, por quebras de linha dentro de campos |
| registros de Santa Catarina | 9.108 |
| registros de Rio do Sul | 50, dos quais 39 hidrológicos |

Os 39 de Rio do Sul: 16 inundações, 14 enxurradas, 5 chuvas intensas, 4
alagamentos. Nenhum protocolo duplicado, nenhuma data inválida, nenhum IBGE
ausente. A soma do CSV reproduziu os totais que o painel do Atlas exibe para
Santa Catarina (349 óbitos; 1.298.936 desalojados e desabrigados; danos
materiais de R$ 16,36 bilhões), o que prova que a leitura pegou o arquivo
inteiro.

**Veredito, que é o mesmo deste documento:** o Atlas confirma ocorrência,
classificação COBRADE, danos e reconhecimento oficial. **Não contém altura de
rio e começa em 1991.** Não valida julho de 1983 (13,58 m) nem pico antigo
nenhum. Os treze picos de Rio do Sul continuam vindo da Exportação de Dados da
Defesa Civil municipal, e os ~70 da tabela inteira também virão de lá.

**Rio do Sul, episódios confirmados pelo Atlas:** set/2011, set/2013, out/2015,
jun/2017, mai e out/2022, jul e nov/2023, mai e jul/2024. Os de 2022 e 2024
estão na tabela municipal e ainda não em `enchentes.json`, o que reforça a
importação da tabela inteira.

**Datas que não batem ao dia, e não devem bater:** a `data_evento` do S2ID é
o começo do desastre decretado, não a crista.

| pico (tabela municipal) | Atlas | leitura |
|---|---|---|
| 17/11/2023 | 16/11/2023 | mesmo episódio; a crista foi na virada de 17 para 18 (DCSC 00:20) |
| 18/05/2024 | 19/05/2024 | mesmo episódio provável |
| 12/07/2024 | 08/07/2024 | mesmo episódio provável |

Tratar como "mesmo episódio provável", nunca como correspondência automática.
Em `enchentes.json` nov/2023 está em 18/11 com `data_na_fonte: 2023-11-17`;
o 16/11 do Atlas é anterior aos dois e não muda nada.

**O cuidado técnico que a rodada confirmou:** o arquivo tem mais linhas físicas
do que registros. `atlas_desastres.py` já lê pelo módulo `csv`, com `;`,
aspas e latin-1, e `newline=""` na abertura, exatamente por isso. Ler linha a
linha partiria os registros, e o cabeçalho do script diz isso desde o
primeiro commit.

## A camada "ocorrências oficiais" — os cinco pontos do Jefferson, em código (21/09/2026)

Decisão do Jefferson antes de integrar o Atlas, e onde cada ponto vive:

1. **Não misturar desastre com pico.** O Atlas é **evidência complementar,
   fora da série de cotas**. `atlas_correspondencias.py` lê `enchentes.json` e
   escreve só em `data/desastres/correspondencias.json`; há teste que trava
   que ele não toca `enchentes.json`, `estacoes.json` nem `transito.json`.
   Nenhuma altura mudou, nenhuma lacuna de nível foi preenchida.
2. **Correspondência por janela de ±5 dias**, guardando para cada par a data
   do pico, a data registrada no Atlas, a diferença em dias e a classificação:
   `confirmado` (|diferença| ≤ 1 dia), `provável` (≤ 5 dias), `provável (mês)`
   quando o pico só tem mês, `sem correspondência` quando nada cai na janela,
   `sem base` quando o pico só tem ano. Nunca correspondência automática.
3. **Filtro de COBRADE:** só 12100 (inundação), 12200 (enxurrada), 12300
   (alagamento) e 13214 (chuvas intensas). Vendaval, granizo e estiagem ficam
   fora da camada de enchentes.
4. **Importador robusto** — já era o do `atlas_desastres.py`: módulo `csv`
   com `;`, aspas, latin-1, quebra de linha dentro do campo, decimal com
   ponto, `DD/MM/AAAA`, protocolo único. `wc -l` engana: ~211 mil linhas
   físicas para 76.190 registros.
5. **Ficha da fonte:** `ficha_da_fonte()` grava em `data/desastres/fonte.json`
   a versão (v1.1), a cobertura (1991–2025), a data de publicação
   (06/08/2026), o nome original do arquivo e a data da importação. Só nasce
   na rodada canônica com o CSV bruto; os recortes recebidos não trazem isso.

### Resultado contra os recortes recebidos (219 picos × 245 ocorrências)

| cidade | confirmado | provável | provável (mês) | sem correspondência |
|---|---|---|---|---|
| Blumenau | 4 | 3 | 0 | 109 |
| Gaspar | 2 | 1 | 0 | 45 |
| Indaial | 3 | 1 | 0 | 12 |
| Rio do Sul | 0 | 0 | 4 | 9 |
| Brusque | 0 | 0 | 2 | 20 |

Blumenau e Brusque têm ainda um pico só com ano (`sem base`). Taió e Timbó,
um pico cada, sem correspondência.

**Confirmados:** nov/2008 em Blumenau, Gaspar e Indaial; out/2001, abr/2010 e
mai/2024 em Blumenau; mai/1992 e fev/1997 em Gaspar; set/2011 e mai/2022 em
Indaial.

**Por que 109 "sem correspondência" em Blumenau é o esperado, não um erro:**
a série de Blumenau começa em 1852 e o Atlas em 1991; a maior parte dos picos
é anterior à base. E os recortes recebidos **excluem 13214**, então out/2023
e outras cheias registradas como *chuvas intensas* não pareiam — a rodada
canônica com o CSV bruto (que inclui 13214 por padrão) deve subir esses
números. Rio do Sul só pareia por mês porque os picos antigos de lá estão sem
dia; os três episódios de 2023–2024 com dia (17/11/2023, 18/05/2024,
12/07/2024) esperam a importação da tabela municipal inteira.

Comando: `python3 scripts/atlas_correspondencias.py <recortes...> --escrever`.

## Os 13 picos de Rio do Sul, um a um, contra o Atlas (21/09/2026, noite)

Pedido do Jefferson: cruzar cada pico municipal com o Atlas numa janela de
±5 dias e classificar como **confirmado, provável, divergente ou fora da
cobertura**, com julho de 1983 fora da cobertura porque o Atlas começa em 1991.
Feito em `atlas_correspondencias.py`; a saída é `data/desastres/correspondencias.json`.
Nenhuma altura mudou.

| pico (Rio do Sul) | m | classificação | Atlas | leitura |
|---|---|---|---|---|
| 1911-10 | 12,20 | fora da cobertura | — | anterior a 1991 |
| 1954-10 | 10,70 | fora da cobertura | — | idem |
| 1957-08 | 10,65 | fora da cobertura | — | idem |
| 1983-05 | 7,35 | fora da cobertura | — | idem |
| **1983-07** | **13,58** | **fora da cobertura** | — | o Atlas não confirma nem nega a maior cheia da série |
| 1983-09 | 7,60 | fora da cobertura | — | idem |
| 1984-08 | 12,80 | fora da cobertura | — | idem |
| 2011-09 | 12,96 | provável (mês) | 08/09 enxurrada (Registro) **e** 12/09 inundação (Reconhecido) | duas ocorrências no mês; as duas ficam na linha |
| 2013-09 | 10,39 | provável (mês) | 26/09 inundação, Reconhecido | 690 desabrigados, 8 010 desalojados |
| 2015-10 | 10,71 | provável (mês) | 23/10 inundação, Reconhecido | 866 desabrigados, 17 636 desalojados |
| 2017-06 | 10,89 | provável (mês) | 01/06 inundação, Reconhecido | 1 090 desabrigados, 14 632 desalojados |
| 2023-10-13 | 11,86 | sem correspondência **no recorte** | — | ver abaixo |
| 2023-11-18 | 13,04 | sem correspondência **no recorte** | — | ver abaixo |

**Por que nenhum "confirmado" nem "divergente" em Rio do Sul:** os picos até
2017 só têm mês em `enchentes.json` (a fonte municipal deu o mês), então a
melhor classe possível é "provável (mês)". Os dois de 2023 têm dia, mas os
recortes recebidos **excluem o COBRADE 13214**, e é como chuvas intensas que o
S2ID registrou nov/2023 em Rio do Sul (a rodada contra a base inteira viu o
16/11/2023). Com o CSV bruto, 18/11/2023 vira **provável, diferença −2 dias**.
Out/2023 não apareceu para Rio do Sul nem na base inteira; fica como está.

**O que mudou no cruzamento por causa deste pedido**

- Classe **fora da cobertura**: pico anterior ao início da base (ou posterior
  ao fim), lido do `periodo` que o recorte declara; sem declaração, 1991–2025.
  Deixa de se chamar "sem correspondência", porque não é. Em Blumenau, 93 dos
  109 "sem correspondência" de antes eram isto.
- Classe **divergente**: há ocorrência na mesma cidade entre 6 e 30 dias do
  pico. Não vira par; a linha diz qual e a quantos dias. Três casos:
  Blumenau 31/08/2011 (8,50 m) × Atlas 11/09/2011, +11 dias; Blumenau
  23/09/2013 (10,51 m) × 02/10/2013, +9; Gaspar 31/08/2011 (6,75 m) ×
  08/09/2011, +8. Os dois de ago/2011 são o mesmo padrão: o decreto veio com a
  cheia de setembro, e o pico de fim de agosto ficou sem decreto próprio.
- **Mais de uma ocorrência na janela:** a linha leva a mais próxima e guarda as
  outras em `outras_no_periodo`. Set/2011 em Rio do Sul é o caso.
- **Lacunas**, o caminho inverso: ocorrência oficial sem pico cadastrado por
  perto. É onde procurar boletim com régua, nunca registro.

### Resultado geral, com as classes novas (219 picos × 245 ocorrências)

| cidade | confirmado | provável | provável (mês) | divergente | sem corresp. | fora da cobertura | sem base |
|---|---|---|---|---|---|---|---|
| Blumenau | 4 | 3 | 0 | 2 | 14 | 93 | 1 |
| Gaspar | 2 | 1 | 0 | 1 | 6 | 38 | 0 |
| Indaial | 3 | 1 | 0 | 0 | 3 | 9 | 0 |
| Rio do Sul | 0 | 0 | 4 | 0 | 2 | 7 | 0 |
| Brusque | 0 | 0 | 2 | 0 | 19 | 1 | 1 |
| Taió, Timbó | 0 | 0 | 0 | 0 | 1 + 1 | 0 | 0 |

Os 19 de Brusque sem correspondência são quase todos de 2019–2024, do portal
municipal; o recorte do Mirim para em 2019. Nada a concluir deles ainda.

### Lacunas: 192 ocorrências sem pico por perto, 29 em Rio do Sul

As de Rio do Sul com mais gente afetada, e portanto as primeiras a procurar na
tabela municipal inteira (~70 linhas, que ainda não foi importada):

| Atlas | tipo | status | desabrigados | desalojados |
|---|---|---|---|---|
| 2014-07-21 | inundação | Reconhecido | 508 | 6 498 |
| 2001-10-01 | enxurrada | Registro | 2 885 | 0 |
| 2022-05-03 | inundação | Reconhecido | 447 | 2 300 |
| 2014-06-11 | inundação | Registro | 151 | 1 016 |
| 1998-04-28 | inundação | Registro | 0 | 763 |
| 2014-10-10 | inundação | Registro | 88 | 678 |
| 2010-04-27 | enxurrada | Registro | 147 | 453 |
| 1997-10-11 | inundação | Registro | 362 | 6 |

Mai/2022 já está na tabela municipal (a rodada contra a base inteira anotou),
e não em `enchentes.json`: é a prova de que o importador da tabela inteira
fecha lacunas de verdade. Jul/2014, com 6 498 desalojados, não estava na lista
de picos que a Defesa Civil municipal deu por mês: procurar na tabela.

Itajaí tem 22 lacunas, todas, porque tem zero picos. Continua sendo o lugar
onde procurar, e continua sem número.

### O plano de oito pontos do Jefferson, e o estado de cada um

| ponto | estado |
|---|---|
| 1. Cruzar os 13 picos de Rio do Sul, ±5 dias, quatro classes | **feito**, tabela acima |
| 2. Importador seguro (latin-1, `;`, multilinha, só SC/Vale, protocolo único, dry-run) | `atlas_desastres.py` já faz tudo menos o dry-run; o `--dry-run` fica para a rodada com o CSV bruto, que é quando ele importa |
| 3. Tabela separada de ocorrências | o projeto não tem banco: é `data/desastres/eventos.json` (saída do script, com protocolo, IBGE, data, COBRADE, status, danos humanos, danos materiais e prejuízos) mais `fonte.json` com versão e data. Ainda não gerado: depende do CSV bruto |
| 4. Enriquecer a página de cada enchente | pendente; `correspondencias.json` já tem o que a tela precisa ("Atlas: chuva intensa em 16/11/2023, reconhecida, provável, −2 dias") |
| 5. Linha do tempo regional | pendente; o recorte já agrupa por mês com `municipios_ordem_montante_jusante` |
| 6. Estatísticas históricas | pendente; só com a base inteira faz sentido |
| 7. Verificações automáticas | protocolo duplicado, município desconhecido, data inválida e quebra de codificação já travam; **faltam** evento fora de 1991–2025, valor negativo e versão diferente da anterior |
| 8. Lacunas nos dois sentidos | **feito**: `lacunas` no JSON; pico sem Atlas segue pico, com "sem correspondência" |

Regra que não mudou: nunca inventar altura usando danos ou COBRADE.

## `--dry-run` e as três verificações que faltavam (21/09/2026, noite)

Do "Plano seguro" do Jefferson, seção 1 e ponto 7 do plano de oito pontos.
Tudo em `atlas_desastres.py`; nenhum dado mudou.

- **`--dry-run`**: lê, filtra, verifica e imprime o resumo inteiro (fonte,
  versão, cobertura, contagem por tipo, maiores episódios) **sem gravar nada**
  em `data/desastres/`. Teste trava que o diretório nem é criado. É a rodada
  que o plano pede antes da importação de verdade:

  ```
  python3 scripts/atlas_desastres.py --arquivo data/brutos/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv --dry-run
  ```

- **Evento fora da cobertura declarada**: a cobertura sai do nome do arquivo
  (`BD_Atlas_1991_2025_…` → 1991–2025; sem nome no padrão, 1991–2025 por
  constante). Registro com `data_evento` fora dela é erro de dado ou base
  diferente da declarada: **descartado com aviso** que lista os protocolos,
  como já era com data inválida. Não entra em silêncio.
- **Valor negativo**: `numero()` falha alto. Dano negativo não existe; aceitar
  esconderia arquivo corrompido ou coluna trocada. Mesmo espírito do "texto não
  vira 0".
- **Versão diferente da anterior**: `versao_mudou()` compara a ficha nova com
  o `fonte.json` gravado (nome, versão, publicação e sha256) e avisa alto o
  que mudou, para que ninguém compare saída de v1.1 com v1.2 achando que é a
  mesma coisa. Mesmo nome com conteúdo diferente também avisa (sha256). Não
  bloqueia: base nova é esperada. Primeira rodada e mesma base ficam caladas.

Já existiam e continuam: protocolo duplicado (entra uma vez), município fora
do recorte, data inválida, quebra de codificação (latin-1 fixo, `csv` com
aspas e quebra interna). **Nove testes novos**, incluindo o `main()` rodado
de ponta a ponta com e sem `--dry-run`.

## A rodada canônica: o CSV bruto na VPS, e o cruzamento com a base inteira (21/09/2026, manhã)

O Jefferson baixou o CSV no navegador e rodou `atlas_desastres.py --arquivo`
na VPS, com 13214 incluído. O que saiu, e está commitado em `data/desastres/`:

| arquivo | conteúdo |
|---|---|
| `fonte.json` | `BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv`, versão 1.1, cobertura 1991–2025, publicação 2026-08-06, 86 134 318 bytes, sha256, importado em 2026-09-21T10:53Z |
| `eventos.json` / `.csv` | **507 ocorrências** nas vinte cidades: 215 enxurradas, 193 chuvas intensas, 81 inundações, 18 alagamentos; de 15/10/1991 a 31/12/2025 |
| `episodios.json` / `.csv` | 166 episódios (janela de 7 dias entre cidades) |

O recorte recebido antes tinha 245 ocorrências em 16 cidades, sem 13214. A
base inteira dobra a contagem, e a diferença é quase toda *chuvas intensas*
mais cinco cidades que entram (Benedito Novo, Ituporanga, Pomerode, Taió e
Timbó). Ibirama estava no recorte recebido e fica fora do nosso, por
`FORA_DO_RECORTE`: ausência ali é recorte, não ausência de desastre.

### Cruzamento: 219 picos × 507 ocorrências

| cidade | confirmado | provável | provável (mês) | divergente | sem corresp. | fora da cobertura | sem base |
|---|---|---|---|---|---|---|---|
| Blumenau | 4 | 3 | 0 | 4 | 12 | 93 | 1 |
| Brusque | 8 | 5 | 2 | 5 | 1 | 1 | 1 |
| Gaspar | 2 | 1 | 0 | 2 | 5 | 38 | 0 |
| Indaial | 3 | 1 | 0 | 0 | 3 | 9 | 0 |
| Rio do Sul | 0 | 1 | 4 | 0 | 1 | 7 | 0 |
| Taió | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| Timbó | 1 | 0 | 0 | 0 | 0 | 0 | 0 |

**O que o 13214 mudou, como previsto:**

- **Rio do Sul 18/11/2023 (13,04 m)** saiu de "sem correspondência no recorte"
  para **provável, −2 dias**: chuvas intensas reconhecida em 16/11/2023, 1 838
  desabrigados e 18 969 desalojados. Era o que a rodada anterior tinha anotado
  à mão.
- **Brusque** saiu de 19 "sem correspondência" para 1: 8 confirmados e 5
  prováveis, quase todos chuvas intensas de 2019–2024. O recorte do Mirim
  parava em 2019.
- **Taió 09/10/2023 (12,40 m)** → provável, −5 dias, chuvas intensas
  reconhecida em 04/10. **Timbó 09/09/2011 (9,86 m)** → confirmado.

**O que o 13214 NÃO mudou, e é achado:**

- **Rio do Sul 13/10/2023 (11,86 m) continua sem correspondência.** A base
  inteira não tem registro nenhum de Rio do Sul em out/2023, embora Taió,
  Blumenau, Gaspar, Indaial e Brusque tenham decreto de 03 e 04/10. Um pico de
  11,86 m sem decreto no S2ID é dado sobre o município, não sobre o rio. O pico
  fica.
- **Blumenau 17/11/2023 (9,14 m) também sem correspondência**: Blumenau não tem
  registro de nov/2023 no Atlas, e Itajaí tem (inundação reconhecida em 17/11).
- **Blumenau 13/10/2023 (10,61 m) é divergente**: o decreto de Blumenau é de
  04/10 e a crista foi em 13/10, nove dias depois. É o exemplo mais limpo de
  que a `data_evento` do S2ID é o começo do desastre, não o pico. Gaspar
  (12/10 × 03/10) e Brusque (13/10 × 04/10) mostram a mesma coisa: **out/2023
  é um episódio de nove dias entre decreto e crista** no vale inteiro.
- **Blumenau 29/05/1992 (12,80 m, IBGE) sem correspondência**, e Gaspar
  29/05/1992 confirmado. Subnotificação da base nos anos 1990: o cabeçalho do
  script já avisa (29% dos municípios em 2013).

**Divergentes: 11.** Além dos três de antes, entraram oito, todos chuvas
intensas de 2021–2023 em Blumenau, Brusque e Gaspar, com diferença de 6 a 21
dias. Nenhum vira par. Brusque 23/06/2022 (5,46 m) × 02/06 tem 21 dias: pode
ser o segundo pico de um junho chuvoso, ou outro episódio. Fica para olho.

### Lacunas: 378 ocorrências oficiais sem pico por perto

| cidade | lacunas | | cidade | lacunas |
|---|---|---|---|---|
| Brusque | 37 | | Ilhota | 20 |
| Ascurra | 36 | | Indaial | 18 |
| Rio do Sul | 33 | | Timbó | 16 |
| Gaspar | 31 | | Lontras | 15 |
| Itajaí | 30 | | Vidal Ramos | 14 |
| Ituporanga | 25 | | Guabiruba | 12 |
| Taió | 23 | | | |
| Apiúna | 21 | | | |
| Blumenau | 21 | | | |

As maiores, por gente afetada:

| cidade | Atlas | tipo | status | desabrigados | desalojados |
|---|---|---|---|---|---|
| **Itajaí** | 2011-09-09 | inundação | Registro | 3 215 | 45 630 |
| **Itajaí** | 2008-02-20 | enxurrada | Registro | 0 | 25 511 |
| Gaspar | 2011-09-08 | inundação | Registro | 558 | 23 039 |
| **Itajaí** | 2008-11-23 | enxurrada | Registro | 18 208 | 1 929 |
| Blumenau | 2023-10-04 | chuvas intensas | Reconhecido | 239 | 14 929 |
| Rio do Sul | 2014-07-21 | inundação | Reconhecido | 508 | 6 498 |
| Ilhota | 2008-11-24 | enxurrada | Registro | 1 300 | 3 500 |

**Itajaí tem 30 ocorrências e zero picos.** As três maiores lacunas do vale
são de Itajaí. Continua sendo o lugar onde procurar boletim com régua
nomeada, e continua sem número: nada disto vira pico.

**Gaspar set/2011 é lacuna com 23 039 desalojados** porque o pico de Gaspar em
`enchentes.json` é 31/08/2011 (6,75 m, divergente, +8 dias) e não há pico de
setembro. Ou a fonte de Gaspar registrou a crista de agosto e não a de
setembro, ou são duas cheias. Conferir na página oficial de Gaspar (71
registros), que já está na fila.

**Blumenau 04/10/2023 é lacuna com 14 929 desalojados** só porque o pico de
13/10 caiu em "divergente" (nove dias): é o mesmo episódio. A lacuna aqui é
artefato da janela de cinco dias, e a leitura humana resolve. Não alargar a
janela por causa disto: alargar mistura episódios em Brusque.

Regra que não mudou: nunca inventar altura usando danos ou COBRADE.

## Refeito com os 65 de Rio do Sul (21/09/2026, meio-dia)

Depois da importação dos 52 picos da tabela municipal (decisão do Jefferson),
o cruzamento foi refeito: **271 picos × 507 ocorrências**. Só Rio do Sul mudou:

| | antes (13 picos) | depois (65 picos) |
|---|---|---|
| confirmado | 0 | 1 (18/05/2024 × 19/05, chuvas intensas reconhecida) |
| provável | 1 | 2 (18/11/2023; 12/07/2024 × 08/07) |
| provável (mês) | 4 | 19 |
| sem correspondência | 1 | 12 (1992-05, 2004-09, 2005-05, 2005-09, 2007-11, 2011-07, 2015-09, 2016-10, 2018-05, 2019-12, 2020-09, 13/10/2023) |
| fora da cobertura | 7 | 31 |
| lacunas de Rio do Sul | 33 | 16 |

**Jul/2014 continua lacuna** (6 498 desalojados): a tabela municipal não tem
julho de 2014. Fev/2018, set/2018, mai/2019 e dez/2020 são lacunas novas de se
olhar: têm decreto e não têm linha na tabela. Nada disso vira pico.
