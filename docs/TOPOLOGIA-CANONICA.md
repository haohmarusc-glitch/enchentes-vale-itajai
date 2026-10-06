# TOPOLOGIA CANÔNICA — a bacia do Itajaí é uma ÁRVORE, não uma fila

**Este documento é a fonte única sobre a TOPOLOGIA da bacia.** Se o código, outro
doc ou uma figura discordarem dele sobre quem está a montante/jusante de quem,
**ele vence** — e o `estacoes.json` (o dado) manda no resto. Verificado em mapa +
Overpass em 02/09/2026 (marcador OSM na coordenada de cada estação, lendo o rótulo
da via de água sob ele; e `way["waterway"]["name"](around:1000,lat,lon)`).

A regra que sustenta tudo: **distância em linha reta não ordena rio ramificado.**
Antes de assumir cadeia linear em qualquer rio, verificar a ramificação.

## Itajaí-Açu — árvore

```
Itajaí do OESTE (Taió)  ‖  Itajaí do SUL (Ituporanga)   ← cabeceiras PARALELAS
              └───────────┬───────────┘
                     RIO DO SUL          ← aqui NASCE o Itajaí-Açu (começo do tronco)
                                           -27.2160314, -49.6483391  **
                          │
                       LONTRAS            (tronco — jusante imediato de Rio do Sul)
                          │
                          │ ← entra o Rio Hercílio / Itajaí do Norte ***
                          │     [IBIRAMA = afluente lateral, NÃO elo do tronco]
                       ASCURRA            (tronco)
                          │
                       INDAIAL
                          │ ← entra o Rio Benedito (Timbó), 4,6 km abaixo da régua de Indaial *
                       BLUMENAU → GASPAR
                          │ ← entra o Rio Luís Alves, perto de Ilhota *
                        ILHOTA
                          │ ← entra o ITAJAÍ-MIRIM (que é ramificado; ver abaixo)
                        ITAJAÍ → foz (Atlântico)
```

**\*** **Benedito: medido em 06/10/2026.** No OSM, o way "Rio Benedito" termina no nó
1575465793, que também é a ponta de dois ways do "Rio Itajaí-Açu". O nó está em
−26,89134, −49,23557, no centro urbano de Indaial. Pela água, fica **4,6 km abaixo da régua de Indaial** (DCSC-00006)
e 26,3 km acima da de Blumenau. `achar_confluencias.py --gravar` gravou isso em
`_topologia.afluentes_rios`, por decisão do Jefferson. Método e incertezas:
`docs/TRACADOS-AFLUENTES-2026-10-06.md`. Isso **corrige** a leitura de 05/09/2026
("a montante de Indaial"): o AIBH fala do trecho "entre os **municípios** de Ascurra e Indaial, a
montante da confluência" — ele não situa a confluência em relação à régua. A JICA (seção 3.1) diz
"Benedito River in Indaial city". As duas fontes concordam com a medição.
O **Luís Alves** continua sem ponto exato: falta o traçado dele. Não se inventa o lado.

**\*\*** A **coordenada da confluência** (04/09/2026, em
`_topologia.confluencia_cabeceiras`). Não é medição nossa de "onde os traçados
passam mais perto": no arquivo da Defesa Civil de Rio do Sul (API Asthon) os
três traçados — Itajaí do Sul, Itajaí do Oeste e Itajaí-Açu — **terminam e
começam no MESMO vértice, ao dígito** (0,0 m). A junção é declarada pela
topologia da fonte. `scripts/achar_confluencia_cabeceiras.py` reproduz, e
**recusa** se o vértice deixar de ser compartilhado — devolver "o ponto mais
próximo" seria inventar precisão que a fonte não deu.

O que faz isso valer como confirmação, e não como "o arquivo disse": o **rumo de
chegada** de cada cabeceira bate com a geografia levantada aqui por OUTRA fonte
(OSM/Overpass, 02/09) — o Itajaí do **Sul** chega pelo **sul** (vem de
Ituporanga), o Itajaí do **Oeste** pelo **oeste** (vem de Taió). Duas fontes
independentes concordando. Rumo trocado é recusa também: significaria arquivo
com os nomes invertidos **ou** esta topologia errada, e nenhuma das duas se
resolve gravando.

Ressalva que não pode sumir: a cobertura daquele arquivo é só o trecho perto de
Rio do Sul (Sul 10,6 km, Oeste 9,9 km). Serve para o **ponto**, não como
**traçado de mapa** — por isso fica em `data/brutos/`, não em `data/rios/`.

**\*\*\*** A ordem entre **Lontras** e a confluência do Norte vem do JICA 2011: a
Tabela 3.6.2 lista os trechos "Indaial → confluência do Norte", "confluência do
Norte → jusante de Lontras" e "Lontras → Rio do Sul" — lendo de jusante para
montante, o Norte entra **ABAIXO de Lontras**, e a seção 3.1 diz que o encontro
se dá "in Ibirama city". Nosso `afluentes_laterais` ainda registra Ibirama como
`entra_perto_de: rio-do-sul`, o que é grosseiro mas não falso: a confluência fica
entre Lontras e Ascurra. **Pendência**: apertar esse campo para o ponto real
quando houver coordenada — não foi trocado agora porque a ordem da tabela de
declividade é inferência de leitura, não uma afirmação literal de confluência.

**A única sequência que a UI pode afirmar** (`_topologia.tronco_sequencia`):

`Rio do Sul → Lontras → Ascurra → Indaial → Blumenau → Gaspar → Ilhota → Itajaí`

Fora dela:
- **Taió e Ituporanga são cabeceiras paralelas** — nenhuma vem "antes" da outra;
  as duas alimentam Rio do Sul. Um pico em Rio do Sul depende da SOMA Oeste + Sul.
- **Ibirama fica no Rio Hercílio** (afluente). O pico dele ENTRA no tronco perto de
  Rio do Sul, não desce por Indaial. Correlacionar Ibirama→Indaial isolado
  subestima (provável parte do r²=0,21 do `coleta_niveis.py`).
- **Lontras entrou no tronco** (04/09/2026), entre Rio do Sul e Ascurra. Duas fontes
  independentes: o JICA 2011 (Tabela 3.6.2) lista os trechos "confluência do Norte →
  jusante de Lontras" e "Lontras → Rio do Sul"; o levantamento municipal a descreve como
  jusante imediato de Rio do Sul. A obra estadual de Melhorias Fluviais leva o nome do
  trecho "Rio do Sul–Lontras".
- **Timbó (Rio Benedito) e Rio dos Cedros entraram como afluentes laterais** (04/09/2026).
  O Benedito desagua perto de Indaial (AIBH 2021 + JICA seção 3.1); o Rio dos Cedros
  desagua no Benedito — o PLANCON de Timbó monitora "o Benedito OU o Cedros", o que
  confirma que os dois chegam lá. Timbó SAIU de `afluentes_monitorados` ao entrar na
  árvore: estar nos dois lugares é o que o validador proíbe, e ramo + afluente lateral diz
  o mesmo com mais precisão. Continua valendo que **o pico de Timbó ocorre JUNTO com o de
  Rio do Sul** no hidrograma de projeto da JICA — a chuva cai na sub-bacia do Benedito,
  não é a mesma cheia descendo o Açu, e encadear tempo por Timbó dá errado.
- **Trombudo Central entrou SEM posição na árvore** (04/09/2026). A fonte diz em que RIO a
  cidade está (Rio Trombudo), mas não onde esse rio encontra o eixo — e aqui não se inventa
  o lado, a mesma regra que mantém o Luís Alves "a confirmar". Fica fora de
  `afluentes_laterais`, e o diagrama a mostra em "Outros pontos". Cuidado com o homônimo: o
  bairro Barra do Trombudo, em Rio do Sul, é outro lugar.
  **Atualização de 06/10/2026:** o traçado do OSM liga o Rio Trombudo ao **Itajaí do Oeste** por
  um nó comum (534975895, em −27,24510, −49,69070, 6,3 km acima da confluência com o Sul). A
  ligação está em `rio_chega_a` da cidade, com fonte e incerteza, por decisão do Jefferson.
  A cidade continua **sem posição na árvore** (`posicao_na_arvore: null`, travado por
  `valida_rio_chega_a`): ligação geométrica do OSM não é fonte hidrológica.
- **Apiúna saiu do eixo**: a estação estadual DCSC-00178 é de altitude ("(H)",
  reporta ~82 m) e cai em área de mata sem curso d'água — não é régua de rio.
  Fica em `_topologia.nao_e_regua_de_rio`. Ascurra (DCSC-00003, confirmada no
  tronco por Overpass) ocupa o lugar dela na sequência.

## Itajaí-Mirim — árvore desde 04/10/2026 (Guabiruba é afluente lateral)

Até 04/10/2026 as cidades do Mirim eram uma fila (`ordem` 1..N), com Guabiruba entre
Botuverá e Brusque. Estava errado: a régua de Guabiruba (DCSC-00029) fica no
**ribeirão Guabiruba**, afluente que entra no Mirim perto de Brusque, e a água de
Botuverá não passa por ela. Por decisão do Jefferson (04/10/2026), o Mirim ganhou
`_topologia`:

- **tronco:** Vidal Ramos → Botuverá → Brusque → Itajaí (`ramo: mirim_tronco`);
- **cabeceiras paralelas:** nenhuma;
- **afluente lateral:** Guabiruba, pelo Ribeirão Guabiruba, "entra perto de Brusque"
  (`ramo: ribeirao_guabiruba`). O ponto exato da confluência não tem fonte.

Proposta e efeitos em `docs/PROPOSTAS-AUDITORIA-2026-10-03.md`, item 2. O Monitor
passa a mostrar o Mirim em Tronco e Afluentes; nenhum arquivo protegido mudou.

Além dessa árvore das cidades, a ramificação do Mirim aparece entre as **réguas
DC de Itajaí**, na foz (hidráulica, fora da `_topologia`):

- **DC-10 Limoeiro** (tronco do Mirim) → divide-se em dois braços paralelos que se
  reencontram perto da foz:
  - **curso antigo:** DC-05 Sítio Hilário → DC-06 Itamirim
  - **canal retificado:** DC-03 SEMASA → DC-04 Vitalmar (reunião dos braços ≡ DC-06)

Isso já está em `estacoes_tempo_real` (campo do título: "(curso antigo)" /
"(canal retificado)") e na tela de Itajaí (`agruparPorCurso` / `dividirEmBracos`).

## Contrato no `estacoes.json` (vocabulário do `main`)

- `ordem`: sequência montante→jusante **só em rio não ramificado**. Desde 04/10/2026
  os dois rios são ramificados, e `ordem` é **`null`** em todas as cidades — usar
  ordem global afirmaria uma fila inexistente.
- `ramo`: em rio ramificado, o braço da cidade — Açu: `itajai_do_oeste | itajai_do_sul
  | itajai_do_norte | tronco_acu | …`; Mirim: `mirim_tronco | ribeirao_guabiruba`.
  O ramo do tronco de cada rio está em `validar_dados.TRONCO_DO_RIO`. Só se compara
  posição DENTRO do mesmo ramo.
- `ordem_no_ramo`: posição montante→jusante dentro do ramo (1 = mais a montante).
- `codigo_dcsc`: liga a cidade à estação estadual (por coordenada), `DCSC-NNNNN`.
- `_topologia`: `tronco_sequencia`, `cabeceiras_paralelas`, `afluentes_laterais`,
  `nao_e_regua_de_rio`.

## O que TRAVA isso (a lição que custou versões)

Documentar a topologia **não impediu** o JSON de ficar errado por versões seguidas.
O que impede é o validador **abortar**. `scripts/validar_dados.py` agora falha se:

1. Aparecer `ordem` global (não-null) em rio ramificado.
2. Faltar `ramo`/`ordem_no_ramo` no Açu, ou `ordem_no_ramo` não for 1..N por ramo.
3. `tronco_sequencia` não bater com as cidades de `ramo: tronco_acu`.
4. Um `codigo_dcsc` esperado sumir ou trocar (a cidade ligada a uma estação
   estadual conhecida não pode desaparecer em silêncio).
5. Uma régua com `alerta_automatico: false` não disser o motivo (ela não pode
   virar faixa de perigo enganosa).

`scripts/teste_validar_dados.py` trava cada uma dessas — mudar a regra sem querer
fica vermelho. Rode `python3 scripts/validar_dados.py` antes de todo commit em
`data/`.

## Pendências (não bloqueiam a topologia)

- **Ponto exato** onde o Luís Alves entra (antes/depois da régua de Ilhota). O
  `scripts/achar_confluencias.py` resolve por geometria (grafo do tronco + Dijkstra), mas falta o
  `luiz-alves.geojson`. Até lá, `_topologia.afluentes_rios` fica "a confirmar por coordenada". O
  Benedito foi medido e gravado em 06/10/2026 (nota \* acima).
- Distância **ao longo do rio** no `transito.json` — **medida** (02/09/2026) por
  `scripts/medir_distancia_rio.py`, montando os segmentos do OSM num grafo e
  caminhando pela água. Gravada como `km_rio` (contexto/QA, **não** muda os
  tempos, que seguem do JICA) onde as duas pontas estão no traçado: Rio do Sul→
  Indaial 85,8 km, Gaspar→Ilhota 16,9 km, Ilhota→Itajaí 33,2 km — sinuosidade de
  **1,2 a 2,0×** a reta, velocidade implícita 3–9 km/h (coerente com o JICA).
  Fica de fora quem está longe do traçado (Blumenau, coordenada da estação ~3 km
  do talvegue) ou em braço não mapeado (Taió/Ituporanga, cabeceiras).
- ~~Trazer a estrutura de árvore ao `/rios` do bot~~ — **feito** (02/09/2026):
  `resposta_rios` mostra o Açu em três blocos (cabeceiras / tronco / afluentes),
  como a tela; o Mirim segue em fila. Travado por `teste_bot.py`.
- Chuva de Apiúna: os mapeamentos (CEMADEN, DCSC-00178) foram removidos com a
  saída do município do eixo; se um dia quiser mostrar chuva de ponto fora do
  eixo, é uma feature à parte.
- Coordenadas das 11 réguas DC: divergência do documento de rota × Mapa.php
  registrada em `docs/coordenadas-dc-itajai.md` (mantidos os marcadores do Mapa.php).
