# O ArcGIS de Itajaí — o que já temos, o que é novo, e a palavra "cota"

Levantamento de Jefferson (05–06/09/2026) sobre `arcgis.itajai.sc.gov.br/server/rest/services` —
**200 serviços públicos sem token**; a pasta `defesacivil` exige token, o resto da raiz é aberto.
Abaixo, o que eu **conferi contra o repositório**, porque metade já estava lá.

---

## ⛔ A armadilha central: TRÊS coisas diferentes se chamam "cota"

| o que é | faixa típica | onde aparece |
|---|---|---|
| **lâmina d'água** — quanto a água subiu NAQUELE ponto | **0 a 2,86 m**, mediana 0,60 | app "Cotas de Inundação" do ArcGIS, campo **`cota`**; campo `situa` das manchas |
| **cota de rua** — o NÍVEL DO RIO em que a rua alaga | **3,11 a 21,00 m** | `data/cotas-ruas.json`, campo `cota_m` |
| **cota altimétrica** — altura do terreno sobre um datum | **0,15 a 370 m** | `Relevo_Ponto_Cotado_Altimetrico`, `Relevo_Curva_Nivel` |

**O app da prefeitura chama a lâmina de "cota".** Se aqueles 3.434 pontos entrassem em
`cotas-ruas.json` porque "as duas têm cota", o site diria *"a sua rua alaga com o rio em 0,60 m"* — e o
rio está nesse nível quase sempre.

**A separação é medida, não estipulada.** As 4.588 cotas de rua do cadastro: Blumenau mín 7,40 ·
Gaspar 6,20 · Brusque 3,76 · Rio do Sul 3,11. **Nenhuma abaixo de 3,00 m.** As lâminas de Itajaí,
nenhuma acima de 2,86. **As duas faixas não se tocam**, e `valida_cota_de_rua_nao_e_lamina` põe o piso
no vão entre elas. Sabotagem conferida: uma lâmina de 0,60 m importada como cota reprova.

---

## O que JÁ ESTAVA no repositório (conferido feição a feição)

**As 357 manchas do `historico_inundacoes` são DUPLICATA** do que já temos pelo GeoItajaí. Comparação,
camada por camada:

| evento | ArcGIS | repo (`data/manchas/itajai/`) |
|---|---|---|
| 1983 · 1984 · 2001 · 2008 | 1 · 1 · 1 · 1 | 1 · 1 · 1 · 1 |
| 2011 (área atingida) | 32 | 32 |
| 2011-09 (lâmina) | 5 | 5 |
| 2013-07 · 2013-09 | 48 · 58 | 48 · 58 |
| **2014-06** | 55 | **55** |
| 2015-10 | 155 | 155 |

**Batem todas.** O arquivo de 1,9 MB **não foi acrescentado** — sustenta a decisão já tomada de não
trocar uma fonte pela outra.

**Duas correções ao levantamento:**
1. **2014-06 não é "evento novo"** — está em `inundajunho2014.geojson` desde o início, com as mesmas 55
   feições.
2. **Os 5.237 pontos cotados também já estão** em `data/brutos/itajai-pontos-cotados-altimetricos.geojson.json`,
   e o `_meta` de lá já avisa: *"ALTURA DO TERRENO, não cota de régua"*.

---

## O que é GENUINAMENTE NOVO e ainda falta baixar

| o quê | tamanho | por que importa |
|---|---|---|
| **3.434 lâminas por endereço** | 363 KB | **o achado.** Profundidade medida, endereço por endereço, em 4 eventos. Nenhuma outra cidade da bacia tem |
| 17.120 **curvas de nível a 1 m** | 456 MB em GeoJSON | 8.346 delas entre 1 e 10 m — resolução de modelo de terreno |
| 57.418 **lotes** (`malhacrs3857`) | — | geocodificação com precisão de LOTE, sem depender do OSM |
| 129.296 **edificações** com `numpav` | — | a orientação em enchente é **subir de andar**; saber quais têm mais de um pavimento é informação de segurança |
| `Hidrografia_Trecho_Drenagem` | — | **provável fonte dos ribeirões Murta e Canhanduba**, que hoje faltam no traçado |

⚠️ **Acentuação corrompida na origem** (`Bernardino Jo?o Victorino`): mojibake latin1→utf8 do próprio
ArcGIS. Corrigir no processamento, nunca no download.

---

## ⛔ O que trava o terreno: o DATUM VERTICAL não está declarado

Nem `Relevo_Curva_Nivel` nem `Relevo_Ponto_Cotado_Altimetrico` dizem o datum das cotas. O CRS
horizontal é EPSG:31982 (SIRGAS 2000 / UTM 22S); **o vertical não está em lugar nenhum**.

**Sem esse número, nada disso vira "até onde a água chega".** Subtrair o nível da régua DC-01 de uma
cota altimétrica é o erro de referência que o projeto já cometeu em Ilhota, em Brusque e na série de
Blumenau.

Dois caminhos: **perguntar ao GEOItajaí/COMPDEC** o datum e o offset para o zero de cada régua DC; ou
**derivar empiricamente**, cruzando as manchas por faixa de lâmina com as curvas de nível do mesmo
evento — se a mancha de "0,41 a 0,60 m" de out/2015 acompanha a curva de 3 m, o offset sai da
comparação. O segundo é mais atraente porque os dois lados vêm do mesmo levantamento.

---

## O que isto muda no inventário de Itajaí

Continua verdade que **Itajaí é a única cidade sem cota de rua**. Mas ela tem algo que **nenhuma outra
da bacia tem: profundidade medida por endereço, em quatro eventos**. Blumenau, Brusque, Gaspar e Rio do
Sul têm o limiar; Itajaí tem o registro do que aconteceu.

**O que isso permite dizer:** *"neste endereço, em setembro de 2011, a água chegou a 60 cm"*.
**O que não permite:** prever. E **continua faltando o pico do rio de cada evento** para indexar a
biblioteca por nível — o bloqueio de `ADENDO-2026-09-05-NOITE.md`, que a busca externa não resolveu.

---

## Um TERCEIRO visualizador, ainda não identificado (08/09/2026)

Jefferson trouxe este endereço:

```
https://arcgis.itajai.sc.gov.br/portal/apps/webappviewer/index.html?id=4e097e762ffc484e84648905f0d75347
```

**É um app novo.** Os dois que o repositório já conhecia são outros:

| app | id | o que é |
|---|---|---|
| Cotas de Inundação | `131634abf81347b9a973e79746ae4ef3` | as 3.434 lâminas por endereço; busca na pasta `defesacivil`, que exige token |
| Histórico de Inundações (experiencebuilder) | `0a0f5df570ce46a5bac16a4348752a74` | consome `historico_inundacoes/FeatureServer`, já baixado inteiro |
| **este** | **`4e097e762ffc484e84648905f0d75347`** | **não identificado** |

**Não consegui abrir.** O proxy de saída deste ambiente bloqueia `arcgis.itajai.sc.gov.br`
(`CONNECT tunnel failed, response 403`) — é o mesmo bloqueio que já vale para `*.ana.gov.br`,
`defesacivil.*.sc.gov.br` e `marinha.mil.br`. Nada foi inferido do id: **id de app não diz o que o app
mostra**, e chutar aqui seria inventar uma fonte.

### A pergunta que responde isso em um minuto de navegador

Abrir o app e olhar **a lista de camadas** (ícone de camadas, no canto). Depois, o que interessa mesmo:

1. **Qual serviço REST ele consome** — F12 → aba Rede → filtrar por `rest/services`. O caminho que
   aparecer diz tudo. Se for `historico_inundacoes`, já temos o bruto inteiro e o app não acrescenta
   nada. Se for `defesacivil/...`, é o app das lâminas com outra roupa. **Se for uma pasta que não está
   em nenhuma das duas listas, é fonte nova.**
2. **Se alguma camada tem campo de NÍVEL DE RÉGUA** — não `cota`, não `situa`, não `hectares`. Um campo
   que diga *o rio estava em tantos metros neste evento*.

### Por que a pergunta 2 é a que vale

É exatamente o bloqueio do `ADENDO-2026-09-05-NOITE.md`: temos as manchas de Itajaí e temos a lâmina por
endereço, e **não temos o pico do rio de cada evento na régua que o site lê hoje**. Sem esse número, a
biblioteca de manchas não pode ser indexada por nível — ou seja, o site não pode dizer *"com o rio no
nível de agora, a mancha parecida é a de 2013"*.

⚠️ **E a armadilha de sempre:** se aparecer um campo com números entre 0 e 3, é **lâmina**, não cota de
régua. O app da própria prefeitura chama a lâmina de "cota". Um valor só entra como nível de régua se o
documento disser **de qual régua** ele é — a mesma regra que o PLANCON acabou de cobrar caro.

---

## A coleta de 08/09/2026 02:01 FALHOU INTEIRA — e o relatório não diz isso

Jefferson trouxe `COLETA_ARCGIS_ITAJAI.md`, relatório de uma coleta automatizada contra o ArcGIS de
Itajaí. **Zero registros foram baixados.** Os seis arquivos que ela produziu são, todos:

```
historico_inundacoes_ERROR.json
inundacao_cotas_ERROR.json
item_03542d8f541c4392bc542b01ca979c6d_data_ERROR.json
item_03542d8f541c4392bc542b01ca979c6d_metadata_ERROR.json
item_131634abf81347b9a973e79746ae4ef3_data_ERROR.json
item_131634abf81347b9a973e79746ae4ef3_metadata_ERROR.json
```

E a tabela de camadas do relatório tem **cabeçalho e nenhuma linha**.

### Por que isto está registrado aqui em vez de arquivado como levantamento

Porque o texto ao redor dos erros afirma o contrário deles:

| o relatório diz | o que os arquivos mostram |
|---|---|
| "Serviço histórico oficial … O serviço declara EPSG:4326, limite de 1000 registros e dez camadas" | `historico_inundacoes_ERROR.json` — o serviço não respondeu |
| "Os arquivos `*_metadata.json` preservam esquema, campos e metadados das camadas" | não existe nenhum `*_metadata.json`; existem `*_metadata_ERROR.json` |
| "Os arquivos `*_features.json` preservam atributos e geometrias" | não existe nenhum `*_features.json` |
| "## Conteúdo histórico confirmado" + a lista das dez camadas | **nada foi confirmado nesta rodada** |

A lista das dez camadas (1983, 1984, 2001, 2008, 2011, cotas set/2011, jul/2013, set/2013, jun/2014,
out/2015) **bate exatamente com o que este repositório já tem** desde 06/09. Ou seja: é conhecimento
anterior reapresentado como achado da rodada. **Uma coleta que falhou não "confirma" nada** — e um
relatório que descreve arquivos de erro como se fossem os dados é a mesma mentira silenciosa que este
projeto já pagou caro em outras frentes (o `2>/dev/null` que escondeu um `NameError`, o fixture
escrito à mão que divergia do real).

**Nada deste relatório entrou em `data/`.** Não havia o que entrar.

### E ele não olhou o app que motivou a coleta

O app que Jefferson tinha mandado uma hora antes é `webappviewer/…?id=4e097e762ffc484e84648905f0d75347`.
**Esse id não aparece em lugar nenhum do relatório.** Os alvos foram outros dois:

| id no relatório | o que é |
|---|---|
| `131634abf81347b9a973e79746ae4ef3` | Web AppBuilder — **já catalogado**, é o "Cotas de Inundação" |
| `03542d8f541c4392bc542b01ca979c6d` | Experience Builder, página `page_3`, view `view_2` — **não catalogado**; o experiencebuilder que conhecíamos é o `0a0f5df570ce46a5bac16a4348752a74` |

Então há agora **dois ids não identificados**: o `4e097e76…` e o `03542d8f…`. **Possibilidade que não dá
para verificar daqui** (o proxy bloqueia o domínio): `03542d8f…` pode ser o *item de web map* que o app
`4e097e76…` consome — id de app e id de item são coisas diferentes no ArcGIS. É hipótese, não achado.

### "Tabela 13" no "Próximo alvo" é caçada encerrada, e no lugar errado

O relatório propõe procurar no ArcGIS "a possível Tabela 13 / conjunto das 11 réguas". Isso já foi
respondido em 08/09 pela fonte primária, e a resposta muda o alvo:

- o PDF do PLANCON **v17** tem 68 páginas e **doze tabelas**; a de níveis é a **Tabela 11, página 23**;
  **não existe Tabela 13 nele**, e os onze valores já cadastrados batem 11 de 11;
- a "Tabela 13" é de **outra EDIÇÃO do PLANCON** — um documento, não uma camada de ArcGIS;
- e naquela edição a **DC-09 é outro rio** ("Ribeirão Ariribá" contra "Ribeirão da Murta" na v17), o que
  significa que as estações foram **remanejadas entre edições**.

Procurar essa tabela no ArcGIS não acha nada e, se achasse algo parecido, o risco seria pior: amarrar
cota de uma edição antiga a estação que mudou de curso d'água.

### O que o relatório acerta, e vale repetir

> *"Não se deve interpretar automaticamente classes/polígonos de inundação como nível de régua fluvial;
> a associação precisa vir de fonte explícita."*

Exatamente a regra da casa, e exatamente o motivo de as manchas de Itajaí ainda não poderem ser
indexadas por nível.

### O que falta para a coleta valer alguma coisa

**Os seis `*_ERROR.json`.** Só o `.md` foi trazido, e é o `.md` que não diz *por que* falhou. Os erros
distinguem coisas que exigem respostas opostas:

| se o erro for | então |
|---|---|
| `499 Token Required` | é a pasta `defesacivil`, fechada — vira ofício, não código (já sabido desde 06/09) |
| `403` / bloqueio de saída | é o ambiente de quem rodou, não o servidor — refazer de outra rede |
| 404 / URL errada | os ids ou o caminho do REST estão errados — corrigir e repetir |
| timeout | paginar e repetir |

Sem esses arquivos não dá para escolher entre um ofício e um retry, que são coisas muito diferentes.

---

## O `coleta_inundacoes_itajai.mjs` (08/09/2026) — revisão

Jefferson trouxe um script Node que baixa as dez camadas do `historico_inundacoes`. Não pude rodá-lo
(o proxy bloqueia o domínio), mas ele é **testável sem rede**: os dados que ele buscaria já estão em
`data/brutos/itajai-arcgis-inundacoes.geojson.json` desde 06/09, com as 357 feições e todos os
atributos. Foi assim que a conferência abaixo foi feita.

### Primeiro: ele refaz algo que já existe e já rodou

`scripts/baixar_itajai_arcgis.py` baixa exatamente estas dez camadas, rodou com sucesso em 06/09, e
tem o que o `.mjs` não tem — verificação de `robots.txt`, `User-Agent` com o nome do projeto (regra do
`CLAUDE.md`, vale para **todos** os scripts), espera entre requisições e teto de páginas. **Rodar o
`.mjs` não traz camada nova.** E mesmo que trouxesse, a decisão de 06/09 continua: **não trocar as
manchas do GeoItajaí pelas do ArcGIS** — mesma geometria, e as nossas têm licença MIT declarada.

### O que ele acerta, e foi conferido nos dados reais

**`Shape__Area` está em m², e dividir por 10 000 dá hectares que batem com o campo publicado:**

| camada | soma `Shape__Area`/10⁴ | campo publicado | |
|---|---:|---:|---|
| 0 · 1983 | 7.085,73 ha | 7.085,69 (`hectares`) | bate |
| 1 · 1984 | 7.011,24 ha | 7.015,30 (`sum_hectar`) | 0,06% — dentro da tolerância |
| 2 · 2001 | 3.424,89 ha | 3.424,89 (`sum_hectar`) | exato |

Então a função `hectares()` dele produz número com significado. **Mas o script nunca faz essa
conferência**: ele declara `campoArea` por camada e **não usa o campo em lugar nenhum**. A única
autoverificação disponível de graça ficou de fora.

⚠️ E `campoArea: "areas"` na camada 4 (2011) **não é hectare**: soma 69.946.176,72, que é m². Está
declarado ao lado de `hectares` e `sum_hectar`, que são hectares. Somar os 32 polígonos também não
vale — **eles se sobrepõem**, o que `analisar_itajai_arcgis.py` já registrava.

### O que ele traz de genuinamente novo: `porFaixa` — e a armadilha dentro dele

Hectares por faixa de lâmina é coisa que o repositório não tinha. Foi incorporado ao
`analisar_itajai_arcgis.py` (seção 4), com uma guarda que o original não tem:

```
2015-10: 155 polígonos ·     29.2 ha
             0,20 m :     20.1 ha
      0,21 a 0,40 m :      7.5 ha
      0,41 a 0,60 m :      1.0 ha
         0,51 a 1 m :      0.6 ha
     ⚠️  "0,51 a 1" e "0,41 a 0,60" se sobrepõem — NÃO somar como classes
```

**A camada de out/2015 publica as duas faixas ao mesmo tempo.** Entre 0,51 e 0,60 m as duas valem, e
`porFaixa` devolveria um dicionário em que elas parecem categorias exclusivas — que é o que um gráfico
de barras assume sem perguntar. A mesma área contada duas vezes, apresentada como repartição de um
todo.

E os rótulos de valor único (`"0,20"`, `"0,50"`) **não viram intervalo**: o serviço não diz se são "até
0,20" ou "exatamente 0,20". Chutar o limite de baixo inventaria área. `limites_da_faixa` devolve `None`
para eles, de propósito, com teste travando.

### A palavra "cotas" nos nomes de arquivo

O script grava as camadas 5 a 9 como `05_cotas_2011_setembro.geojson`, `06_cotas_2013_julho.geojson`…
O próprio script sabe que elas são lâmina — o campo `tipo` diz `"lamina"` corretamente. **O nome do
arquivo contradiz o campo.** Neste projeto essa é a ambiguidade mais cara que existe: a Prefeitura
chama a lâmina de "cota", e há um validador (`valida_cota_de_rua_nao_e_lamina`) que existe só por causa
disso. Um arquivo chamado `cotas_2011_setembro` está a um descuido de virar linha em `cotas-ruas.json`,
onde diria *"sua rua alaga com o rio em 0,60 m"*. **Renomear os slugs para `lamina_...`.**

Trava conferida: nenhum rótulo de lâmina passa de 3,00 m, e a menor cota de rua do cadastro é 3,11 m
(Rio do Sul). As duas faixas não se tocam — e há teste novo garantindo que continuem não se tocando.

### ⚠️ O achado mais sério do script não é sobre o script

O cabeçalho dele avisa:

> *"este serviço expõe capabilities de escrita (Create, Update, Delete, Editing). Este script usa
> SOMENTE /query (leitura). Não adicione nada que escreva."*

**Não foi possível verificar daqui** (o proxy bloqueia o domínio), e não consta em nenhum lugar deste
repositório. Se for verdade, um FeatureServer público com edição habilitada significa que **qualquer
pessoa poderia alterar ou apagar as manchas históricas de inundação de Itajaí** — o registro de onde a
água chegou em 1983, 1984, 2001, 2008 e 2011.

**O que fazer:** comunicar ao GEOItajaí/COMPDEC. **O que NÃO fazer, em nenhuma hipótese: testar.**
Não se sonda endpoint de escrita em serviço de produção alheio para confirmar a hipótese — verificar
lendo o `?f=json` do serviço, que lista as capabilities sem exercer nenhuma, é suficiente e é o
caminho. A instrução do script — só `/query`, nunca escrever — está certa e fica valendo aqui.

Nota lateral: se a edição é mesmo aberta, o bruto de 06/09 deixa de ser só cópia de conveniência e
passa a ser **cópia de segurança de um acervo que pode ser alterado na origem**. Mais uma razão para
não trocar as nossas manchas pelas de lá.
