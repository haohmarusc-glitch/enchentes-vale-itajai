# Cotas de enchente por rua — análise e tarefas para o Claude Code

> Levantamento feito em 30/08/2026 a partir de fontes públicas. Objetivo: adicionar ao site a camada
> "a partir de qual nível do rio cada rua alaga" e as manchas de inundação históricas.
> Leia o `CLAUDE.md` antes. Tudo aqui segue as mesmas regras: cada cidade tem sua própria régua,
> todo dado precisa de `fonte` e `confianca`, nada é inventado.

## 0. O que a sondagem respondeu (31/08/2026)

Três sondas rodaram na VPS contra os portais (`scripts/sonda_cotas_ruas.py`, `2` e `3`). O que
mudou em relação ao levantamento original:

| Fonte | Resultado |
|---|---|
| **Rio do Sul** | ✅ **RESOLVIDO.** Não é portal Yii com tabela em HTML: é aplicação Vite, e os **554 logradouros com mínima e máxima viajam dentro do pacote** (`assets/index-<hash>.js`). Importados por `scripts/importar_cotas_rio_do_sul.py`. |
| **Itajaí — ArcGIS** | ❌ **Não é fonte aberta.** A raiz do REST abre sem token (108 serviços), mas a pasta `defesacivil` responde `499 Token Required` — é onde o app "Cotas de Inundação" busca. Vira ofício à prefeitura. |
| **Itajaí — `historico_inundacoes`** | ⚠️ **Já temos.** Dez camadas: manchas de 1983, 1984, 2001, 2008 e 2011, `cotas_2011_setembro` com lâmina, e quatro com 48/58/55/155 feições — exatamente os arquivos do GeoItajaí que já estão em `data/manchas/`. Mesma base, servida de outro jeito. |
| **Gaspar** | ⏳ Timeout de conexão nas duas tentativas. O host responde na coleta de níveis, então é instabilidade ou bloqueio ao IP da VPS: repetir. |
| **Blumenau** | 🚫 Fora por `robots.txt`, como antes. Pedir à Defesa Civil. |

### A armadilha que a sondagem revelou

O ArcGIS de Itajaí publica `Relevo_Ponto_Cotado_Altimetrico`, com um campo chamado **`cota`**, em
metros, com valores plausíveis (5,50 · 6,39 · 4,73). É **altura do terreno acima do nível do mar**.
A cota deste projeto é o **nível do rio na régua** a partir do qual a rua alaga. Mesmo nome,
grandezas opostas; ligar uma na outra exige perfil de linha d'água. Copiado sem isso, produziria o
número que faz alguém dormir em casa numa noite em que devia sair. **Não usar.**

A mesma armadilha reapareceu no KML de Brusque, por outro caminho e com outra cara — ver
"O KML do My Maps não passou", na seção de Brusque. Lá o arquivo é uma **mistura**: tem cota de
régua verdadeira e valor de outra grandeza no mesmo campo, o que é pior do que ser todo errado,
porque parte dele confere.

### O que a importação de Rio do Sul ensinou

A tabela oficial publica duas ruas alagando **abaixo do nível normal do rio** (3,11 m e 3,26 m, com
a menor cota da cidade em 4,50 m e a régua marcando 3,35 m num dia seco). Elas entraram — são dado
oficial —, mas com `usar_para_aviso: false`: aparecem na busca com a ressalva e não movem alarme.
É o mesmo mecanismo do `alerta_automatico: false` das réguas de estuário de Itajaí. Conferir com a
Defesa Civil de Rio do Sul para que virem aviso.

## 1. O que existe, por cidade

### Itajaí (Açu + Mirim) — dados abertos em GeoJSON, licença MIT ⭐
A prefeitura mantém a organização **GeoItajaí** no GitHub. O repositório `geoitajai/sie`
(licença MIT) tem o webmap `dcitajai.html` ("Defesa Civil de Itajaí, áreas atingidas por
inundações") e, em `data/`, as manchas de inundação por evento:

| Arquivo | Evento | Conteúdo |
|---|---|---|
| `enchente1983.geojson` | jul/1983 | 1 MultiPolygon, mancha total, sem atributos |
| `enchente1984.geojson` | ago/1984 | idem |
| `enchente2001.geojson` | 2001 | idem |
| `enchente2008.geojson` | nov/2008 | idem |
| `enchente2011.geojson` | set/2011 | idem |
| `inundasetembro2011.geojson` | set/2011 | 5 polígonos com `situa` = lâmina d'água (0,50 / 0,51 a 1 / 1,01 a 1,50 / 1,51 a 2 / 2,01 a 3 m) |
| `inundajulho2013.geojson` | jul/2013 | 48 polígonos, `situa` em classes (0,20 / 0,21 a 0,40 / 0,41 a 0,60) |
| `inundasetembro2013.geojson` | set/2013 | 58 polígonos |
| `inundajunho2014.geojson` | jun/2014 | 55 polígonos |
| `inundaoutubro2015.geojson` | out/2015 | 155 polígonos (0,20 / 0,21 a 0,40 / 0,41 a 0,60 / 0,51 a 1) |

URL base (raw): `https://raw.githubusercontent.com/geoitajai/sie/master/data/<arquivo>`
Repositório: `https://github.com/geoitajai/sie` — webmap de referência: `https://geoitajai.github.io/sie/dcitajai.html`

Observações:
- Os arquivos "enchenteAAAA" são a mancha total do evento; os "inundaMÊSAAAA" trazem a
  **profundidade da lâmina d'água por trecho** (`situa`), que é o dado mais útil para ruas.
- Não há cota de rio associada a cada polígono. A ligação evento → pico do rio vem de
  `data/enchentes.json` (cruzar pela data).
- "Cotas por endereço" ficam no ArcGIS da prefeitura — ver seção própria abaixo.
- Bairros historicamente atingidos: Cidade Nova, Imaruí, Nossa Senhora das Graças, Fazenda,
  São Vicente, Murta, Cordeiros, Salseiros, Canhanduba, Dom Bosco, Nova Brasília, Bambuzal,
  Itaipava (junto à BR-101). Fonte: mapeamento da Defesa Civil no evento de 2015.

### Itajaí — cotas oficiais por estação (Plano de Contingência v17, 22/12/2025) ✔
Tabela 11 do Plano de Contingência da COMPDEC define as subfases por estação (já em `data/estacoes.json` → `estacoes_defesa_civil_itajai`):

| Estação | Local | Atenção | Alerta | Emergência |
|---|---|---|---|---|
| DC-01 | Itajaí-Açu – CEPSUL | 1,16 | 1,36 | 1,56 |
| DC-02 | Itajaí-Açu – Praça da Murta | 1,60 | 2,00 | 2,50 |
| DC-03 | Mirim canal retificado – SEMASA | 1,48 | 1,85 | 2,50 |
| DC-04 | Mirim – Vitalmar | 1,50 | 1,85 | 2,25 |
| DC-05 | Mirim curso antigo – Sítio Sr. Hilário | 1,60 | 2,20 | 3,00 |
| DC-06 | Mirim curso antigo – Clube Itamirim | 1,50 | 1,85 | 2,55 |
| DC-07 | Ribeirão da Murta – Portal I | 1,00 | 1,35 | 1,65 |
| DC-08 | Ribeirão Canhanduba – Rio do Meio | 1,80 | 2,30 | 2,89 |
| DC-09 | Ribeirão da Murta – Bairro Murta | 1,12 | 1,32 | 1,52 |
| DC-10 | Mirim – Limoeiro | 8,00 | 9,00 | 10,00 |
| DC-11 | Itajaí-Açu – Santa Regina (Volta de Cima) | 3,00 | 4,00 | 5,00 |

Uso na UI: colorir cada estação de Itajaí (amarelo/laranja/vermelho) pelo nível de `data/tempo-real/ultimo.json`. Atenção: DC-10 tem régua própria (8–10 m), não comparar com as demais.

### Itajaí — arquivos oficiais de cota de inundação (Defesa Civil, página Mapas)
`https://defesacivil.itajai.sc.gov.br/mapas/` publica, para download direto:
- **Mapa de Cota de Inundação set/2011** (.zip), **set/2013** (.rar), **jul/2013 por maré** (.rar), **jun/2014** (.rar), **out/2015** (.rar) — provavelmente shapefiles/CAD com cotas; são a origem dos GeoJSON do GeoItajaí e podem trazer atributos que o GitHub não tem (cota por ponto).
- **Levantamento da Enchente de 1983, 1984, 2001, 2008, 2011** (PDF) e **Mapa das Enchentes de 1983, 1984 e 2001** (PDF).
- Plano de Contingência (PDF) — Tabela 11 acima; lista de abrigos por zona; bairros por zona de Defesa Civil.

Tarefa: `scripts/baixar_mapas_itajai.py` — baixar os 5 pacotes + PDFs para `data/manchas/itajai/oficial/`, extrair (`unrar`/`unzip`), listar camadas e atributos com `ogrinfo`/`geopandas`, converter para GeoJSON EPSG:4326 e registrar em `data/manchas/index.json` com `fonte`, `evento` e `licenca: "a confirmar"`.

### Itajaí — ArcGIS da prefeitura (cotas por endereço)
- App "Cotas de Inundação": `https://arcgis.itajai.sc.gov.br/portal/apps/webappviewer/index.html?id=131634abf81347b9a973e79746ae4ef3`
- App "Histórico de Inundações": `https://arcgis.itajai.sc.gov.br/portal/apps/experiencebuilder/experience/?id=0a0f5df570ce46a5bac16a4348752a74`
- REST: `https://arcgis.itajai.sc.gov.br/server/rest/services` — serviços públicos existem (ex.: `arcgis_urban/zoneamento/MapServer`, FeatureServer com geoJSON). Tarefa: abrir a raiz do REST no navegador, achar a pasta/serviço da Defesa Civil (cotas de inundação, histórico) e testar `…/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson`. Se responder, é a fonte de "cota por endereço" de Itajaí sem raspagem.

### Blumenau — tabela oficial de cotas por rua (AlertaBlu)
- Página: `https://alertablu.blumenau.sc.gov.br/p/cotas` (também `https://defesacivil.blumenau.sc.gov.br/p/cotas`)
  e "Ruas alagadas agora": `https://defesacivil.blumenau.sc.gov.br/p/ruas-alagadas`.
- O site bloqueia acesso automatizado (robots.txt). **Não raspar.** Opções: (a) pedir a tabela à
  Defesa Civil de Blumenau; (b) digitar manualmente a partir da página; (c) usar o que a imprensa
  reproduziu (abaixo).
- Referências da régua (Ponte Adolfo Konder): cota de inundação urbana 8,00–8,50 m; ruas mais
  baixas começam a alagar a partir de ~7,40 m.
- O mapa do AlertaBlu permite simular o nível e ver as ruas atingidas; há também mapa de rotas de
  fuga. A FURB foi contratada em 2026 para atualizar as cotas (~20 mil edificações) — quando sair,
  substitui tudo.
- Amostra de cotas publicadas (mai/2022, fonte: relação oficial reproduzida pelo ND+):

| Rua | Bairro | Cota (m) | Ponto |
|---|---|---|---|
| Rua São Rafael | Itoupava Norte | 7,40 | final da rua |
| Rua Martha Cordeiro | Fortaleza | 7,60 | ponto mais baixo |
| Rua Albert Goll | Fortaleza | 7,65 | esquina com Rua 1º de Janeiro |
| Rua São Rafael | Itoupava Norte | 7,75 | próximo ao nº 169 |
| Rua Martha Cordeiro | Fortaleza | 7,80 | esquina com Rua 1º de Janeiro |
| Rua Max Scheidemantel | Fortaleza | 7,90 | próximo ao nº 85 |
| Rua Max Aldemann | Fortaleza | 7,95 | início / ponto mais baixo |

#### Conferência pendente das cotas de Blumenau (PDF oficial de 2014)

As 1.938 cotas de Blumenau entraram com `confianca: media`, por virem da relação de 2023 via imprensa.
Existe um caminho para conferir contra documento oficial: o PDF da Prefeitura "Cotas de enchente das ruas
de Blumenau", hospedado pelo Farol Blumenau em
`https://farolblumenau.com/wp-content/uploads/2014/06/Cotas-de-enchente-das-ruas-Blumenau.pdf`
(o site bloqueia robôs — baixar no navegador, salvar em `data/brutos/`). Traz rua, bairro, cota, abrigo
(códigos E9, N2, C7…) e observação do ponto. É de 2014, então serve para **conferir**, não para
substituir: onde os dois baterem, a relação de 2023 ganha respaldo oficial; onde divergirem, vale o
mecanismo de `divergencias`, não a escolha silenciosa de um dos dois.

O caminho definitivo continua sendo a FURB, que está refazendo o levantamento em 2026 (prof. Ademar
Cordero), pela primeira vez incluindo a região da Celesc para cima (rua Bahia, Rio do Testo, sentido
Pomerode/Indaial) e compatível com GPS de celular. Entrega prevista à Defesa Civil em **novembro de 2026**.

### Gaspar — mapa de cotas por rua (CEOPS/FURB, 2016–2017)
- Estudo feito pelo CEOPS/FURB (coord. Ademar Cordeiro), rua por rua, referenciado à régua da
  ANA na empresa Círculo, usando as marcas de 2011 e, em alguns casos, 1983.
- Consulta: site da Defesa Civil de Gaspar → menu → "Mapas" → "Pesquise sua cota"
  (`https://defesacivil.gaspar.sc.gov.br/` — a tabela de estações em `/monitoramento/tabela`
  é HTML simples; verificar se o mapa de cotas também tem endpoint acessível).
- Referências: alerta a partir de 4,00 m; primeiras ruas a partir de 6,00–6,20 m; emergência
  acima de 7,00 m. A 7 m: 53 ruas (3,8%); a 9 m (como em 2011): 329 ruas (24%); a 11 m metade
  da cidade.
- Cotas publicadas: Rua Petúnia e Rua Costa Rica 6,20 m; Av. Hilberto Gaertner 6,25 m;
  Rua Sertão Verde 6,34 m; Rua Lino 6,57 m. Lista das primeiras ruas atingidas a 6,20 m:
  Av. Hilberto Gaertner, Alfazema, Alício Hugo Hostins, Amor Perfeito, Costa Rica, das Palmeiras,
  Flor de Laranjeira, Francisco Wessling, Heinrich Gorisch, Lírio, Maestro Egon Bohn, Magnólia,
  Maria da Silva, Olga Sabel, Petúnia, Rio do Sul, Sertão Verde. A ~7,4 m entram ainda: Imaruí,
  Francisco Laguna, Augusto Jacinto dos Santos, José Eberhardt, Frei Canisio.

### Brusque (Itajaí-Mirim) — planilha da Defesa Civil, atualizada após nov/2023
- A Defesa Civil de Brusque mantém planilha de cotas por rua; após a enchente de 17/11/2023
  (8,96 m) atualizou as cotas até 8,96 m e iniciou uma 2ª etapa para os pontos não atingidos.
  Não há página pública da planilha — **pedir por e-mail/ofício**.
- Régua: Ponte Estaiada. Cota de inundação da Beira-Rio: **4,80 m**. Loteamentos Beira Rio
  Lote I e II tiveram obras após a última enchente e ainda não têm cota consolidada (jul/2026).
- Cotas publicadas (lista oficial de out/2023, reproduzida por O Município em 17/11/2023):

| Rua | Cota (m) |
|---|---|
| Rua Coelho Neto | 5,64 |
| Rua Celia Zen | 6,72 |
| Rua Adelino da Silva Vale | 6,82 |
| Rua Hugo Schlosser | 7,30 |
| Rua Manoel João Flor | 7,62 |
| Rua Alemanha | 7,62 |
| Rua Francisco Sassi | 7,71 |
| Rua Beira Rio | 7,76 |
| Rua Teodoro H. Staack | 7,77 |
| Rua México | 7,80 |
| Rua Teodoro Henrique | 7,80 |
| Rua SR-005 | 7,82 |
| Rua SC 221 | 7,83 |
| Rua Francisco Heil | 7,90 |
| Rua Júlio Orthmann | 7,94 |
| Rua Padre Gracher | 7,95 |
| Rua Vitório Demarchi | 7,95 |
| Rua Francisco Staack | 7,95 |
| Rua Carlos Hort | 7,97 |
| Rua Laura Diegoli Battistotti | 8,01 |
| Rua Mathias Moritz | 8,01 |

- Pontos que alagam antes disso (5,46–5,80 m): embaixo da Ponte Estaiada, fundos dos
  loteamentos Ema I/II e Santa Mônica (Limoeiro), túnel do Terminal Urbano, Beira Rio na altura
  do Loteamento Malossi/Santa Rita. Bairros primeiro atingidos: Taboão, Pamplona, Bela Aliança,
  Santa Rita; depois Centro, Guarani, Santa Terezinha, Rio Branco, Maluche, Dom Joaquim.
- Afluente relevante: rio Guabiruba, com estação própria (nova, 2025).

#### O KML do My Maps não passou — 1.679 pontos recusados (31/08/2026)

Chegou ao projeto o KML do Google My Maps de cotas de Brusque: 3.688 marcadores em quatro pastas.
Só a pasta **"Cotas de Cheia 2011"** tem números — 1.679 pontos com um campo `cota` e coordenada.
Junto veio um conversor que gravaria todos eles com `referencia: "régua"` e `confianca: "alta"`.

Essa afirmação foi testada antes de qualquer importação, por
`scripts/analisar_kml_brusque.py`, sobre `data/brutos/brusque-mymaps-cotas.json`. **Não se
sustenta.** Três medidas, todas refazíveis rodando o script:

| Medida | Resultado |
|---|---|
| Pontos acima do pico de **2011** em Brusque (10,03 m, `confianca: alta`) | **1.076 de 1.679 = 64,1%** |
| Pontos acima do **maior pico da série** (10,50 m, ago/1984) | 920 de 1.679 = 54,8% |
| Maior valor do arquivo | **29,53 m** — 19 m acima do recorde histórico |
| Ruas em comum com a lista oficial que batem no centavo | **4 de 13** (P por acaso = 0,0001) |
| Mediana da cota, 0–2 km da régua → 4–8 km | 10,16 m → **12,43 m** |

A pasta se contradiz: chama-se "Cotas de Cheia 2011" e dois terços dos seus pontos trazem valor
acima do que o rio marcou em 2011. Se fossem níveis de régua daquela cheia, esses pontos estavam
secos.

Ao mesmo tempo, **parte do arquivo é régua de verdade**. Quatro ruas batem no centavo com a lista
oficial da Defesa Civil — Coelho Neto 5,64 · México 7,80 · Francisco Heil 7,90 · Padre Gracher 7,95 —
e em três delas o valor que bate é o **menor** daquela rua no KML. Um teste de embaralhamento
(20.000 rodadas) põe a chance de isso ser acaso em 0,0001. As outras nove ruas em comum ficam de
0,5 m a 2,3 m **acima** do nosso valor, sem deslocamento constante — então também não é uma
referência única deslocada, como o caso régua/IBGE de Blumenau.

O que sobra é uma **mistura**, sem campo que separe uma coisa da outra ponto a ponto. Importar
entregaria, a quem procura a própria rua, ou a cota certa ou um número que pode errar por até 19 m.
É a mesma armadilha do `Relevo_Ponto_Cotado_Altimetrico` de Itajaí, descrita na seção 0: um campo
chamado `cota` que não é nível de régua. A subida da mediana com a distância do rio é o
comportamento de altitude do terreno.

**Brusque fica com os 27 pontos que já tem.** O bruto ficou no repositório para a recusa ser
conferível, e `scripts/teste_analisar_kml_brusque.py` (36 testes) trava a conclusão: se alguém
apontar um importador para esse arquivo, os testes quebram.

**Um quarto motivo, que só apareceu depois.** A Defesa Civil de Brusque concluiu em **jul/2024** a 1ª
etapa de uma atualização das cotas: **357 pontos**, revistos até 8,96 m (a cheia de 17/11/2023), com 2ª
etapa em andamento. Publicada em `https://bit.ly/novascotasbrusque` (bloqueia robôs — abrir no navegador e
salvar em `data/brutos/`). O achado do estudo é que as cotas **subiram** em vários bairros por causa dos
canais extravasores da Beira-Rio: com o mesmo pico de 2011, hoje alagariam **menos** ruas. Ou seja, mesmo
a parte do KML que é régua de verdade está **desatualizada abaixo de ~7,50 m**, que é justamente a faixa
onde mora o aviso adiantado. É a camada "Cotas de cheia 2023" do próprio KML (357 pontos) — que veio
**sem número nenhum** na conversão que recebemos.

**O que resolveria:** o KML **original**. A conversão que chegou aqui preservou só `pasta`, `cota`,
`rua`, `bairro` e `coord`; o original trazia ainda `obs`, `esquina` e coordenadas UTM
(`coord_x`, `coord_y`) — que é justamente onde estaria dito o que o número significa.

#### O KML original chegou — e a camada de 2023 passou (31/08/2026) ✔

O arquivo original apareceu (`Cotas_Enchente_de_Brusque.kml.xml`, 5,97 MB). Ele resolve exatamente o
que faltava: a camada **"Cotas de cheia 2023"**, que na conversão anterior vinha sem número nenhum,
traz **dois** campos por marcador — o **nome** do marcador e um "Nível registrado no local". Somados,
dão sempre a mesma coisa:

| Ponto | Nome | Nível registrado | Soma |
|---|---|---|---|
| Bartolomeu Pruner | 7,65 | 1,31 | **8,96** |
| Dorval Luz | 8,27 | 0,69 | **8,96** |
| Vicente Schaeffer | 7,94 | 1,02 | **8,96** |

8,96 m é o pico de Brusque em 17/11/2023. Logo: o nome do marcador é a **cota da régua da Ponte
Estaiada** em que o ponto começa a alagar, e o outro campo é a **lâmina d'água** medida ali naquele
dia. A conta fecha em **338 dos 344 pontos** que publicam lâmina — 98,3%, com erro de 1 cm.

Isso é de outra natureza que a discussão do parágrafo anterior. Não é inferência sobre o que a
fonte quis dizer: é aritmética contra um pico conhecido, refazível por qualquer um com
`python3 scripts/importar_cotas_brusque.py --seco`. Por isso esta camada entra com
`confianca: alta`, enquanto os 1.938 pontos de Blumenau, que vieram por imprensa, ficaram em
`media`.

**350 pontos importados**, com `referencia: "régua"` e `data_fonte: "2023-11"`. O importador refaz a
conta a cada execução e **recusa a importação inteira** se ela deixar de fechar em 95% dos pontos —
se a fonte trocar o significado dos campos, o script para em vez de gravar número sem significado.

Seis pontos ficaram de fora, e o motivo é o mesmo em todos: **a própria conta não fecha**.

| Ponto | Conta | Erro |
|---|---|---|
| Beira Rio | 7,75 + 1,23 = 8,98 | 0,02 m |
| Gabriel Siegel | 8,60 + 0,31 = 8,91 | 0,05 m |
| Gerson Venturelli | 7,90 + 1,30 = 9,20 | 0,24 m |
| Ernesto Bianchini | 7,56 + 1,14 = 8,70 | 0,26 m |
| Francisco Sassi | 6,48 + 1,10 = 7,58 | 1,38 m |
| Beco Laguna | 8,27 + 8,27 = 16,54 | 7,58 m (o campo repete a cota) |

Quando os dois números da fonte discordam, não dá para saber qual está errado. Gravar o primeiro
seria avisar a rua na hora errada — cedo demais, ou nunca.

**Um achado de segurança, que a importação trouxe junto.** O ponto mais baixo da camada é a
**Av. Beira Rio esquina com Maria Scarpa Formonti, no Limoeiro: 3,76 m** (com 5,20 m de lâmina em
2023 — a conta fecha). Isso fica **1,04 m abaixo** da cota de atenção de Brusque, 4,80 m, que é a
menor que a cidade publica. Quer dizer: naquele ponto, a água chega mais de um metro antes de o
aviso automático tocar.

O registro entra com o número verdadeiro e aparece na tela e no bot com a ressalva, mas leva
`usar_para_aviso: false` — o mesmo mecanismo usado em duas ruas de Rio do Sul. O motivo é que a
alternativa seria baixar o limiar de aviso da cidade inteira para 3,76 m por causa de um ponto, e
ninguém aqui sabe se 3,76 m fica acima do nível normal do Mirim na Ponte Estaiada. Um aviso que
toca em dia de sol é desligado pelo usuário, e aí não toca na noite que importa. **Quem resolve
isso é a Defesa Civil de Brusque**, e é mais um argumento para o ofício que já era o pedido
pendente desta seção.

**A recusa da camada de 2011 continua de pé**, e ganhou mais uma evidência agora que dá para cruzar
as duas: por vizinho mais próximo, os oito pares a menos de 30 m um do outro diferem em **+2,04 m na
mediana, de −0,43 a +5,36 m**. Pontos a vinte metros de distância não discordam cinco metros na mesma
grandeza, e o sinal sistematicamente positivo é o que se espera de altitude de terreno.
`scripts/teste_analisar_kml_brusque.py` (38 testes) foi apertado em vez de afrouxado: nenhum registro
pode citar a pasta de 2011, todo registro vindo do KML tem de nomear a camada de 2023 e o pico contra
o qual foi conferido, e cota acima do recorde da cidade só entra dizendo na nota que está.

Alternativa melhor, ainda pendente: a planilha da Defesa Civil de Brusque, sobretudo pela 2ª etapa
do levantamento (os pontos não atingidos em 2023) e por uma cota de atenção abaixo de 4,80 m.

### Rio do Sul — API pública Asthon (tempo real) ⭐ a fazer

`public.asthon.com.br`, `city_id 4214805`: **29 estações do Alto Vale**, duas barragens e histórico
horário. Um dump está em `data/brutos/rio-do-sul-asthon-2026-08-31.json`, e
`scripts/analisar_asthon.py` diz, estação por estação, o que dá para fazer com ela. **O resultado corrige
o que esta seção dizia antes**, e a correção é do tipo que este projeto existe para fazer:

| | quantas | o quê |
|---|---|---|
| **pode virar aviso** | 5 | régua de rio com cota própria: Ponte Dom Tito Buss, Itoupava, Ribeirão do Tigre, Taboão, Valada São Paulo |
| **só para mostrar** | 10 | régua de rio sem cota, ou com cota que não é dela |
| **fora** | 13 | sem nível, leitura fora de faixa, ou barragem |

Três achados, nenhum visível na lista de nomes:

1. **Taió e Ituporanga não têm régua de cidade aqui — têm BARRAGEM.** O que a API publica é "Barragem
   Oeste Taió" e "Barragem Sul Ituporanga": nível de reservatório na escala do próprio barramento (a de
   Taió marca 9,79 m com atenção em 11,65 m). Mostrar isso como "o rio em Taió" seria número certo
   respondendo a pergunta errada. A frase anterior desta seção — "cobre Taió e Ituporanga" — estava errada.
2. **Quatro estações leem centenas de metros:** Mirim Doce 349,08 · Salete (H) 400,4 · Petrolândia 450,74 ·
   Atalanta (H) 454,12. Não é nível de rio. É o mesmo problema já visto no monitoramento da Defesa Civil
   de SC, e a resposta é a mesma: fora.
3. **Cinco réguas trazem a mesma cota, 4,50 / 5,50 / 6,50** — as faixas oficiais de Rio do Sul —, em rios
   diferentes e até em outro município (Laurentino). Uma delas está certa, a de Dom Tito Buss; as outras
   quatro são a cota de Rio do Sul copiada até que alguém confirme. Aplicar a cota de uma régua a outra
   cria alarme onde não há e cala onde há.

**O que sobra de bom: Vidal Ramos.** É régua de rio, no município de Vidal Ramos, cabeceira do
Itajaí-Mirim — uma das cidades sem nível nenhum na tela hoje. Só que **sem cota**: dá para mostrar, nunca
para disparar. Taió e Ituporanga continuam sem nível de cidade.

**A confirmação que dá crédito ao resto:** as faixas de Dom Tito Buss na API são exatamente as que já
estão em `estacoes.json` (atenção 4,50 · alerta 5,50 · a terceira, que lá se chama "emergência" e aqui
"inundação", 6,50). Duas fontes independentes, mesmo número.

**Antes de coletar:** checar `robots.txt` e os termos de uso, como em toda fonte nova — o que não dá para
fazer a partir do dump. E uma leitura só vira aviso se vier com a cota **daquela** estação, que é o que
`analisar_asthon.py` decide.

#### A lista de 555 ruas está completa e conferida ✔

Havia duas leituras independentes da mesma tabela oficial: a nossa, raspada do portal (554 ruas,
`confianca: alta`, com mínima e máxima), e a transcrição integral da NSC Total de 14/08/2026 (545 ruas,
só a mínima), agora em `data/brutos/rio-do-sul-nsc-2026-08-14.json`.

`scripts/conferir_rio_do_sul_nsc.py` cruza as duas: **das 538 ruas que as duas publicam com o mesmo nome,
538 trazem a cota idêntica ao centavo. Zero divergências.** Outras seis "só da NSC" são a mesma rua com
outra grafia (Amábile/Amabilio Testoni, Menegetti/Meneghetti, Guaiâniazes/Guaianazes, Gutenberg/Gutemberg,
Frankenberger/Frankemberger, Jurací/Juracy Dalfovo), com cota igual.

E **uma rua só a NSC tinha: Visconde de Cairu, 19,01 m.** Não é grafia de outra — temos "Visconde de Mauá"
a 10,89 m, e "Hilberto Bruch" a 19,01 m, que a NSC publica separadamente. O portal declara **555** itens e
tínhamos 554: era esta. Entrou com a fonte da NSC e `confianca: media` (não `alta`, porque não veio do
portal) e sem cota máxima, que o jornal não publicou. Rio do Sul está em 555.

### Rio do Sul — tabela "Cota de Cheias por Rua" com exportação
- Portal: `https://defesacivil.riodosul.sc.gov.br/` → "Cota de Cheias por Rua" (555 itens, campos
  `logradouro`, `minima`, `maxima`, botão "Exportar Dados").
  URL: `https://defesacivil.riodosul.sc.gov.br/index.php?r=soscota-rua%2Ftabela`
- O portal é JS puro; a exportação provavelmente chama um endpoint interno. **Descobrir com
  DevTools** (aba Network ao clicar em Exportar). Há também "Planilha Histórica Rio", "Atestado
  Enchente" e "Mapa Inund. e Abrigos".
- Referências: enchente a partir de ~7,00 m (abrigos abertos a 7 m); cota de alerta usual
  6,50–7,50 m.

#### Gaspar — Google My Maps da Defesa Civil: 1.613 pontos importados (31/08/2026) ✔

`cotas_enchente_gaspar_01042020`, uma pasta só, 1.615 pontos, cada um com cota, rua (`refer_1`), rua
transversal ou número (`refer_2`), bairro, UTM e lat/lon.

O arquivo chegou com a mesma armadilha do de Brusque: uma conversão pronta que já gravava tudo como
`referencia: "régua"`, sem uma linha de evidência. **A afirmação foi testada antes de importar**, por
`scripts/analisar_kml_gaspar.py`, com o mesmo instrumento que recusou a camada de 2011 de Brusque. Desta
vez ela passou, e por dois caminhos independentes.

**1. As quatro ruas em comum batem todas, ao centavo, e sempre no menor valor da rua.**

| Rua | Nosso cadastro (CEOPS/FURB) | KML (faixa da rua) | |
|---|---|---|---|
| Rua Petúnia | 6,20 | 6,20 – 6,57 | bate no menor |
| Rua Costa Rica | 6,20 | 6,20 – 6,20 | bate no menor |
| Av. Hilberto Gaertner | 6,25 | 6,25 – 8,30 | bate no menor |
| Rua Sertão Verde | 6,34 | 6,34 – 7,75 | bate no menor |

O menor valor da rua é exatamente onde a água chega primeiro — é a grandeza que o nosso cadastro guarda.
Em Brusque foram 4 acertos em 13 ruas, com as outras nove divergindo de 0,5 a 2,3 m sem deslocamento
constante; aqui **não há uma divergência sequer**.

**2. A ordem das duas listas publicadas se reproduz.** O estudo do CEOPS, pela imprensa, nomeia 17 ruas
atingidas primeiro (a partir de ~6,20 m) e 5 que entram depois (~7,4 m) — sem número por rua, só a ordem.
No KML as medianas saem **6,63 m** e **7,07 m**, na ordem certa, com **P por acaso = 0,0014**. Nada no
arquivo diz a que grupo cada rua pertence: se o campo `cota` fosse altitude de terreno, ou régua com outro
zero, não teria por que respeitar essa separação.

**O que não fecha, e por que não decide.** A mesma matéria diz que a 7 m alagam 53 ruas e a 9 m alagam 329.
Contando as ruas do KML pela mínima de cada uma, dão 18 e 158 — cerca de metade. **Não é deslocamento de
escala**: o limiar que daria 53 ruas seria 7,82 m e o que daria 329 seria 10,91 m, dois desvios diferentes,
enquanto um deslocamento constante seria o mesmo nos dois. As explicações prováveis são de contagem: a
matéria conta ruas da cidade inteira (53 é 3,8% de ~1.390 ruas) e este mapa tem 408; e o mapa é de abril de
2020, quatro anos depois do estudo. Nenhuma delas toca na única pergunta que decide a importação — se os
números estão na mesma régua —, e essa os itens 1 e 2 respondem.

**1.613 pontos importados**, com `referencia: "régua"`, `confianca: alta` e `data_fonte: "2020-04"`.
Gaspar vai de 23 para 1.618 registros. `scripts/importar_cotas_gaspar.py` roda a análise de novo antes de
gravar e **recusa a importação se o veredito mudar** — a prova não fica num documento, fica no caminho da
execução.

**O que a importação substituiu.** Dezoito registros de Gaspar estavam com `cota_m: null` — a fonte
anterior (imprensa, sobre este mesmo estudo) citava a rua sem publicar o número. Foram trocados pelos
numerados, e não somados a eles: a mesma busca não pode devolver "alaga a partir de 6,46 m" e "cota não
publicada" para a mesma rua. Os **cinco registros com número não saíram**, mesmo repetindo valores que a
fonte oficial traz — são eles a prova de escala, e apagá-los deixaria a conferência sem contra o que rodar
da próxima vez.

**Uma pendência pequena que ficou.** Nosso cadastro tem "Rua Lino" a 6,57 m, do estudo pela imprensa; o KML
tem "Rua Lírio" com mínima de **exatamente 6,57 m** e não tem nenhuma "Rua Lino". É provável que sejam a
mesma rua, com erro de transcrição em algum ponto da cadeia — mas "é provável" não apaga registro. Os dois
ficam, e a pergunta vai junto no contato com a Defesa Civil de Gaspar.

**Gaspar continua sem cota em `estacoes.json`** e sem estação de tempo real coletada, então nenhuma dessas
1.613 cotas dispara aviso: elas respondem "a partir de que nível a minha rua alaga", e não "o rio está
chegando lá". O validador avisa isso a cada execução. Conseguir a régua e as cotas de referência de Gaspar
é o que falta para a cidade entrar no aviso por Telegram.

### Indaial, Ilhota, Timbó, Ibirama, Taió, Vidal Ramos, Botuverá
- Nada aberto localizado. Indaial tem portal da Defesa Civil em `indaial.atende.net`.
  Tratar como pendência de contato.

### Universidades
- UFSC (TCC 2025) consolidou em QGIS polígonos/pontos de inundação fornecidos pelas Defesas
  Civis de Blumenau, Brusque, Gaspar, Itajaí e Rio do Sul. Vale pedir os arquivos ao autor.
- LabGeo/FURB: GeoServer com carta-enchente de Blumenau 2011 (12,8 m) em WMS. Pedido enviado.

## 2. Modelo de dados a criar

### `data/cotas-ruas.json`
```json
{
  "_meta": {
    "descricao": "Nível do rio (régua local) a partir do qual cada rua/ponto alaga.",
    "campos": {
      "cidade": "id de data/estacoes.json",
      "rio": "itajai-acu | itajai-mirim",
      "rua": "nome oficial",
      "bairro": "opcional",
      "ponto": "trecho/esquina/número, quando a fonte informa",
      "cota_m": "nível do rio na régua da cidade",
      "fonte": "URL ou documento",
      "data_fonte": "AAAA-MM-DD da publicação",
      "confianca": "alta | media | baixa"
    }
  },
  "cotas": []
}
```
Popular com todas as tabelas da seção 1 (Blumenau, Gaspar, Brusque). Confiança: `media`
(oficial reproduzido pela imprensa). Quando vier a tabela oficial, sobrescrever com `alta`.

### `data/manchas/` (GeoJSON)
- `scripts/baixar_manchas_itajai.py`: baixa os 10 arquivos do GeoItajaí para `data/manchas/itajai/`,
  gera `data/manchas/index.json` com `{cidade, evento, data, arquivo, tem_lamina, licenca: "MIT", fonte}`
  e, para os arquivos com `situa`, normaliza a classe para `lamina_min_m` / `lamina_max_m`.
- Cruzar cada evento com o pico correspondente em `data/enchentes.json` (adicionar os picos de
  Itajaí que faltam: 1983, 1984, 2001, 2008, 2011, jul/2013, set/2013, jun/2014, out/2015 —
  buscar na Defesa Civil de Itajaí).

## 3. Telas / componentes

1. **Busca "minha rua"** (por cidade): campo de texto com autocomplete sobre `cotas-ruas.json`;
   retorna a cota, o nível atual da cidade (`data/tempo-real/ultimo.json`) e a diferença
   ("faltam 2,3 m para sua rua"). Mostrar sempre a régua de referência da cidade.
2. **Simulador de nível**: slider por cidade; lista as ruas com `cota_m <= nível` ordenadas.
   Rodapé com contagem ("a 7 m, N ruas conhecidas").
3. **Mapa de manchas (Itajaí)**: Leaflet + GeoJSON; seletor de evento; cor por lâmina d'água;
   legenda com o pico do rio naquele evento; crédito "GeoItajaí / Prefeitura de Itajaí (MIT)".
4. Na tela do rio, ao lado de cada cidade, badge "N ruas alagam a partir de X m" quando houver dados.

## 4. Tarefas, em ordem

1. Criar `data/cotas-ruas.json` com as tabelas da seção 1 (Blumenau, Gaspar, Brusque). ✔ dados neste arquivo
2. `scripts/baixar_manchas_itajai.py` + `data/manchas/index.json`.
3. Componente de busca por rua + simulador (item 3.1 e 3.2).
4. Mapa Leaflet com as manchas de Itajaí (3.3). Adicionar `leaflet` e `react-leaflet` ao `web/`.
5. Investigar endpoints: REST do ArcGIS de Itajaí (cotas por endereço), exportação de Rio do Sul
   (DevTools; há também PDFs por rua em `index.php?r=soscota-rua%2Findex`), mapa de cotas de Gaspar.
5b. `scripts/baixar_mapas_itajai.py` (seção Itajaí — arquivos oficiais). Registrar o que achar em `docs/cotas-de-ruas.md` (esta seção).
6. Pendências de contato (não são código): tabela completa de Blumenau (Defesa Civil), planilha de
   Brusque (Defesa Civil), arquivos QGIS do TCC da UFSC, WMS do LabGeo.

## 5. Avisos obrigatórios na interface
- "Cotas são aproximadas e podem estar desatualizadas; obras e novas enchentes mudam os valores."
- "Cada cidade usa sua própria régua. 7 m em Gaspar não é 7 m em Blumenau."
- "Em emergência, ligue 199. Siga a Defesa Civil da sua cidade."
