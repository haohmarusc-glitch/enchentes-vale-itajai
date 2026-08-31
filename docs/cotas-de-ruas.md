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

**O que resolveria:** o KML **original**. A conversão que chegou aqui preservou só `pasta`, `cota`,
`rua`, `bairro` e `coord`; o original trazia ainda `obs`, `esquina` e coordenadas UTM
(`coord_x`, `coord_y`) — que é justamente onde estaria dito o que o número significa. O original
não está mais disponível. Alternativa melhor: a planilha da Defesa Civil de Brusque, que já era o
pedido pendente desta seção.

### Rio do Sul — tabela "Cota de Cheias por Rua" com exportação
- Portal: `https://defesacivil.riodosul.sc.gov.br/` → "Cota de Cheias por Rua" (555 itens, campos
  `logradouro`, `minima`, `maxima`, botão "Exportar Dados").
  URL: `https://defesacivil.riodosul.sc.gov.br/index.php?r=soscota-rua%2Ftabela`
- O portal é JS puro; a exportação provavelmente chama um endpoint interno. **Descobrir com
  DevTools** (aba Network ao clicar em Exportar). Há também "Planilha Histórica Rio", "Atestado
  Enchente" e "Mapa Inund. e Abrigos".
- Referências: enchente a partir de ~7,00 m (abrigos abertos a 7 m); cota de alerta usual
  6,50–7,50 m.

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
