# Fontes de tempo real e APIs — mapeadas via Chrome (31/08/2026)

> Todas testadas no navegador. Endpoints JSON/GraphQL diretos, sem raspagem de HTML.
> Coletores correspondentes em `scripts/`.

## 1. Defesa Civil de SC — GraphQL (a mais ampla) ⭐
- Endpoint: `POST https://monitoramento.defesacivil.sc.gov.br/graphql`
- Operações no bundle JS: `query Tags_data` (todas as estações + última leitura),
  `query Historic($stationCode,$startDate,$endDate,$interval)` (série histórica),
  `subscription Nowcasting` (via `wss://…/graphql`), `query Radares`.
- Cobertura: **174 estações no estado, 61 na bacia do Itajaí** — inclui as que faltavam
  (Timbó, Ibirama, Apiúna, Ascurra, Pomerode, Rio dos Cedros, Lontras, José Boiteux, Guabiruba,
  Botuverá 1 e 2, Luiz Alves) e as barragens Oeste, Sul e José Boiteux.
- Cada estação: `codigo` (DCSC-000NN), `position` (bacia, lat, lon, região, altitude),
  `rio_nivel` (m) + tendência, `chuva.acumulado` (h001/h024/h072…).
- `Historic`: intervalos `MIN_5, MIN_10, MIN_15, MIN_30, HOUR_1…HOUR_168`; campos por ponto
  `ts, rio_nivel, rio_variacao, chuva_mm, chuva_total`.
- **Limite verificado:** histórico só retorna de ~2023 em diante; consultas a 2011/2015 vêm vazias.
  Confirmado com o evento de out/2023 (Ilhota DCSC-00030 marcou 13,3 m; Indaial 8,76 m; Brusque 8,52 m em 17/11).
- Coletor: `scripts/coleta_defesacivil_sc.py` (snapshot + `--historico`).
- Camadas do mapa (tiles vetoriais, separadas): `https://tile-service.quallecontrol.com.br/table.dcsc.rios.geom`
  e `…/table.dcsc.regioes.geom`.

## 2. AlertaBlu / Defesa Civil de Blumenau — JSON estático ⭐
- `https://defesacivil.blumenau.sc.gov.br/static/data/nivel_oficial.json` — nível do Itajaí-Açu em Blumenau,
  **série horária** + faixas de condição (Normalidade/Observação/Atenção/Alerta/Emergência com cores).
- `/static/data/situacao_atual.json` — condições meteorológicas e risco de deslizamento por região/bairro.
- `/static/data/aviso.json` — aviso vigente. `/static/data/temperaturas.json` — temperaturas.
- `/static/bairros/regioes_blumenau.geojson` — polígonos das regiões (mapa).
- `/p/enchentes` (HTML) — **tabela histórica oficial: 102 enchentes (1852–2024)** com ano/data/cota.
  Baixada em `data/brutos/blumenau-enchentes-registradas-alertablu.json`.
- Coletor: `scripts/coleta_alertablu.py`.
- Descoberta-chave: os valores históricos do AlertaBlu (2011=12,60; 1983=15,34; 1984=15,46; 1880=17,10)
  são idênticos à série IBGE de Cordero → confirma que a série popular está em referência IBGE. Ver
  `REGRA_REFERENCIA_BLUMENAU` em `data/enchentes.json`.

## 3. Rio do Sul / Alto Vale — API Asthon (já no repo)
- `https://public.asthon.com.br/public/` (city_id 4214805): `stations/list`, `stations/live`, `dams`,
  `station-history`, `panel`, `shelters`, `cities/{id}/forecast/bulletin`.
- 29 estações do Alto Vale + barragens Oeste e Sul. Coletor: `scripts/coleta_rio_do_sul.py`.

## 4. ArcGIS oficial da Prefeitura de Itajaí — REST público (GeoJSON) ⭐
Raiz: `https://arcgis.itajai.sc.gov.br/server/rest/services?f=pjson` (pasta `defesacivil` exige token,
mas os serviços na raiz são públicos e servem `f=geojson`).
- **`historico_inundacoes/FeatureServer`** — 10 camadas:
  - manchas totais: `0` 1983, `1` 1984, `2` 2001, `3` 2008, `4` 2011 (32 polígonos)
  - cotas com lâmina d'água (campo `situa`): `5` 2011-set (5), `6` 2013-jul (48), `7` 2013-set (58),
    `8` 2014-jun (55), `9` 2015-out (155).
  - Baixado: `data/brutos/itajai-arcgis-inundacoes.geojson.json` (~2 MB, tudo em EPSG:4326).
  - Mais rico que os GeoJSON do GitHub GeoItajaí (mesma origem, mas aqui é a fonte oficial e reprojetada).
- **`Relevo_Ponto_Cotado_Altimetrico/MapServer/0`** — **5.237 pontos com elevação** (campo `cota`, 0,15–370 m).
  Baixado: `data/brutos/itajai-pontos-cotados-altimetricos.geojson.json`. Permite estimar cota-enchente por
  endereço em Itajaí cruzando com o nível do rio + maré (não havia cota-por-rua pública de Itajaí; isto supre).
- **`Hidrografia_Terreno_Sujeito_Inundacao/MapServer/0`** — 110 polígonos de terreno inundável.
  Baixado: `data/brutos/itajai-terreno-sujeito-inundacao.geojson.json`.
- Query padrão: `…/FeatureServer/{id}/query?where=1%3D1&outFields=*&outSR=4326&f=geojson`
  (paginar com `resultOffset`/`resultRecordCount=1000` — o Relevo tem 5.237, veio em 6 páginas).

## Downloads salvos em 31/08 (mover para `data/brutos/`)
- `defesacivil-sc-tags_data.json` — snapshot das 174 estações estaduais.
- `blumenau-enchentes-registradas-alertablu.json` — 102 enchentes de Blumenau (oficial).
- `itajai-arcgis-inundacoes.geojson.json` — 10 camadas de inundação de Itajaí.
- `itajai-pontos-cotados-altimetricos.geojson.json` — 5.237 pontos cotados.
- `itajai-terreno-sujeito-inundacao.geojson.json` — 110 polígonos.

## Tarefas para o Claude Code
1. `scripts/coleta_defesacivil_sc.py` num cron de 10 min → acumula nível+chuva de toda a bacia; é o que
   vai calibrar os tempos de trânsito reais entre cidades.
2. Substituir os GeoJSON do GitHub GeoItajaí pelos do ArcGIS oficial (item 4) no mapa de manchas de Itajaí.
3. Tela de Itajaí "cota por endereço": cruzar `Relevo_Ponto_Cotado_Altimetrico` com nível do rio + maré,
   já que Itajaí não publica cota-por-rua como as outras cidades.
4. Reconciliar `data/enchentes.json` de Blumenau com a série oficial de 102 eventos, depois de resolver a
   referência (IBGE vs régua) — a evidência agora aponta forte para IBGE.
5. Backfill de histórico 2023→hoje via `Historic` (GraphQL) para todas as estações da bacia, base dos
   pares montante→jusante.

---

## Revisão deste documento (Claude Code, 31/08/2026)

O mapa de endpoints acima é o levantamento mais útil que o projeto recebeu: ele resolve, em
princípio, o maior buraco que existe — dez das quinze cidades sem nível ao vivo, Blumenau entre
elas. O que segue são as conferências feitas antes de usar qualquer parte dele, porque aqui um
número errado com cara de certo custa mais que número nenhum.

### ✅ Confere: a pasta `defesacivil` do ArcGIS exige token

Bate com a sondagem independente de 31/08 (`scripts/sonda_cotas_ruas2.py`): a raiz abre sem token
e a pasta responde `499 Token Required`. As contagens das camadas de `historico_inundacoes`
(48/58/55/155) também batem, uma a uma, com os arquivos do GeoItajaí que já estão em
`data/manchas/`.

### ⛔ NÃO confere: a conclusão sobre a referência de Blumenau

> *"os valores históricos do AlertaBlu (2011=12,60; 1983=15,34; 1984=15,46; 1880=17,10) são
> idênticos à série IBGE de Cordero → confirma que a série popular está em referência IBGE"*

Três dos quatro batem. **O de 2011 não** — e 2011 é justamente a evidência em que a
`REGRA_REFERENCIA_BLUMENAU` se apoia. O que `data/enchentes.json` já registra para 09/09/2011:

| Valor | Fonte | Rótulo |
|---|---|---|
| 12,80 m | Cotas-enchente ABRH / CEOPS-FURB | adotado |
| **13,00 m** | CEOPS/FURB — Ponte Adolfo Konder | divergência (é a série IBGE) |
| **12,60 m** | Imprensa | divergência |

O 12,60 do AlertaBlu é o valor que já está catalogado como **imprensa**, não o da série IBGE, que
é 13,00. Portanto a coincidência em 1983, 1984 e 1880 **não** fecha a questão: a regra bloqueante
continua valendo, e a condição de saída dela segue sendo o HidroWeb (estação 83800002, cotas de
09/07/1983 e 07/08/1984) ou a resposta da FURB.

### ⚠️ Antes de coletar do AlertaBlu: `robots.txt` e cadeia de certificado

O AlertaBlu foi recusado antes por `robots.txt` (`docs/cotas-de-ruas.md`), e a mesma régua vale
agora que a fonte interessa mais — inclusive para `/static/data/`, e principalmente para o
`/p/enchentes`, que o coletor proposto raspa. A sondagem de 30/08 também falhou ali com
`unable to get local issuer certificate`. **Desligar a verificação não é opção:** abriria a coleta
para qualquer um no caminho injetar nível de rio.

`scripts/sonda_fontes_novas.py` responde as duas coisas antes de qualquer coleta.

### ⚠️ O que falta para uma estação nova virar aviso

Nível sem cota não vira aviso — seria comparado com a cota de outra régua. Cada estação nova
precisa de: mapa `estação → cidade/rio`, cota de referência **na régua dela**, e o julgamento
sobre maré onde couber (as nove de estuário de Itajaí estão com `alerta_automatico: false`
justamente por isso). A sonda imprime os campos crus de uma estação para se saber se a cota vem
na resposta ou terá de ser levantada à parte.

### Sobre `Relevo_Ponto_Cotado_Altimetrico` (5.237 pontos)

A tarefa 3 proposta — *"cruzar com nível do rio + maré para estimar cota-enchente por endereço"* —
é a armadilha que este projeto já documentou duas vezes. O campo `cota` ali é **altura do terreno
acima do nível do mar** (0,15 a 370 m); a cota deste projeto é **nível do rio na régua**. Ligar uma
na outra exige perfil de linha d'água, que varia ao longo do rio e com a vazão. Feito por
subtração, produz exatamente o número que faz alguém dormir em casa numa noite em que devia sair.
Serve como entrada de estudo, com hidrólogo no meio — não como cota por endereço.

### Estado dos coletores que vieram junto

`coleta_defesacivil_sc.py`, `coleta_alertablu.py` e `coleta_rio_do_sul.py` são bom reconhecimento e
**não estão em produção**. Para entrarem, falta: faixa de plausibilidade no valor lido (é o defeito
que a auditoria acabou de achar em `coleta_itajai.py`), uso de `comum.baixar` (retentativa e
`Retry-After`), escrita no `ultimo.json` que o site, o bot e o aviso realmente leem — hoje escrevem
em arquivos que ninguém consome —, e limpeza dos snapshots com carimbo de hora, que num cron de 10
minutos são 144 arquivos por dia, para sempre.


## O que a sonda respondeu na VPS (31/08/2026)

`scripts/sonda_fontes_novas.py` rodou e decidiu as três perguntas. Duas respostas
contrariaram o que este documento esperava.

### Defesa Civil de SC — GraphQL ✅ para chuva, ❌ para nível

`robots.txt` traz `Disallow:` vazio — **permissão explícita para tudo**. HTTP 200,
174 estações no estado, **61 na bacia do Itajaí**.

**Não vem cota de referência.** Os campos de uma estação, na íntegra:

```
codigo · name · timestamp · position(bacia, latitude, longitude, regiao, altitude)
data.rio: rio_nome(null) · rio_nivel · rio_nivel_tendencia(null)
data.chuva.acumulado: h001 · h024
```

Sem a cota daquela régua, **nenhuma leitura pode virar aviso** — seria comparada
com a cota de outra. Era a condição posta aqui, e não é atendida.

**E o "nível" não é a mesma grandeza entre estações.** Cruzando com as nossas
leituras do mesmo instante:

| Cidade | Nossa régua | DCSC | Diferença |
|---|---|---|---|
| Brusque | 3,21 m | 3,25 m | +0,04 |
| Rio do Sul | 5,44 m | 5,52 m | +0,08 |
| **Ilhota** | 3,25 m | **10,34 m** | **+7,09** |

As estações com sufixo `(H)` trazem 342, 385, 456, 877, 914 — altitude ou outra
coisa, não leitura de régua. Apiúna vem 81,97. É a **terceira** vez que o projeto
encontra um campo chamado "nível" ou "cota" que não é o que parece, depois do
`Relevo_Ponto_Cotado_Altimetrico` de Itajaí e do KML de Brusque.

**A chuva não tem esse problema:** milímetro é milímetro em qualquer lugar, não
depende de régua, zero nem datum. Por isso entrou — `scripts/coleta_chuva_sc.py`
coleta `chuva.acumulado` e **nem pede** `rio_nivel` na consulta, para ninguém se
tentar depois.

### Blumenau — a sonda derrubou a esperança que este documento tinha

`DCSC-00026 SDC-SC Blumenau` publica chuva (19,06 mm/24 h) e **`rio_nivel: null`**.
A Defesa Civil de SC **não resolve o nível de Blumenau**.

E o AlertaBlu continua barrado: `robots.txt` inacessível por
`CERTIFICATE_VERIFY_FAILED — unable to get local issuer certificate`, o mesmo
erro de 30/08. Como o `git pull` da mesma VPS funciona, o repositório de CAs da
máquina está bom: é o servidor de Blumenau enviando a **cadeia incompleta**, sem
o certificado intermediário. Navegador disfarça (busca pelo AIA); Python não.

**Não desligar a verificação.** O conserto honesto é baixar o intermediário que
falta e passá-lo como CA — isso completa a cadeia que o servidor deveria mandar,
e continua verificando assinatura, validade e nome do host. Enquanto isso não é
feito, Blumenau depende da página da Defesa Civil de Itajaí, que em 31/08/2026
estava publicando a estação com o carimbo **congelado há mais de três horas**
enquanto as outras treze atualizavam a cada 15–30 min.


### Correção: a defasagem de Blumenau é da estação, não do caminho (31/08/2026)

Este documento afirmava, acima, que a estação Blumenau da página de Itajaí estava
publicando com o carimbo congelado enquanto as outras treze atualizavam a cada
15–30 min, e tratava a coleta direta do AlertaBlu como o conserto.

**Conferido no navegador, contra a fonte primária: o AlertaBlu mostra o mesmo
valor com a mesma idade** — 5,11 m há 3 h, no mesmo instante em que a nossa
coleta trazia 5,11 m há 3 h. A cadência de publicação é da própria estação de
Blumenau. Não há atraso de repasse, e a nossa coleta está fiel à fonte.

O que isso muda:

* **Não existe fonte pública mais fresca de Blumenau.** A tela mostrando "há 3 h"
  está dizendo a verdade, e não há número melhor a buscar.
* **Coletar direto do AlertaBlu não melhora o frescor.** Continua valendo por ser
  fonte primária em vez de menção secundária, e pela série horária histórica —
  mas sai da fila de urgência onde este documento a tinha posto.
* **A extrapolação foi retirada.** Durante a subida de 31/08 estimei, pelo ritmo
  medido, que o nível real de Blumenau poderia estar perto de 5,9 m. Não há
  evidência nenhuma disso e o número não foi publicado em lugar nenhum. O que se
  sabe é o que a fonte diz: 5,11 m, há 3 h.

Fica de pé uma melhoria que a subida revelou: a tela precisa distinguir leitura
velha com rio **parado** de leitura velha com rio **subindo**. Hoje mostra as
duas igual, e a segunda é a que engana.


## Vidal Ramos: duas fontes, o mesmo rio (01/09/2026)

Uma leitura manual do painel da Defesa Civil de SC, feita pelo celular em 31/08 e guardada em
`data/brutos/leitura-manual-2026-08-31.json`, trouxe as três cidades que hoje não têm nível na tela:
**Taió 5,40 m · Ituporanga 1,27 m · Vidal Ramos 3,29 m** (coluna "Rio (m)", só estações `SDC-SC`; as
`(H)`/`(M)` trazem altitude em outra referência e ficaram de fora).

Vale como **evidência**, não como dado exibido: é um instante único, de uma coluna que este projeto já
tinha recusado uma vez — o `rio_nivel` do GraphQL da Defesa Civil de SC, que trazia Ilhota a 10,34 m
enquanto a nossa régua marcava 3,25 m.

Mas ela permite uma conferência que antes não dava para fazer. **Vidal Ramos aparece nas duas redes**:

| fonte | nível | quando |
|---|---|---|
| API Asthon (`data/brutos/rio-do-sul-asthon-2026-08-31.json`) | 2,93 m | 31/08 12:21 UTC |
| painel da Defesa Civil de SC (leitura manual) | 3,29 m | 31/08 22:26 UTC |

Dois painéis independentes, dez horas de intervalo, mesma ordem de grandeza e subida plausível. Não
prova que é o mesmo sensor nem o mesmo zero, mas afasta a hipótese de que a coluna "Rio (m)" das
estações `SDC-SC` seja outra grandeza — que era o medo levantado pelo caso de Ilhota.

**O que continua faltando para virar aviso:** a cota daquela régua. Vidal Ramos, Taió e Ituporanga não
têm nenhuma em `estacoes.json`, e sem ela um número na tela é só um número. Taió e Ituporanga têm o
agravante de a Asthon publicar só as BARRAGENS delas, em escala de reservatório — ver
`scripts/analisar_asthon.py`.


## AlertaBlu: o argumento de conformidade chegou, a verificação não (01/09/2026)

Um documento de mapeamento de fontes trouxe um argumento a favor de coletar do AlertaBlu, e ele é
bom: o coletor buscaria só **assets de dados** — `/static/data/nivel_oficial.json`,
`/static/data/situacao_atual.json`, `/static/data/aviso.json` — mais a página pública
`/p/enchentes`. O que o `robots.txt` de sites assim costuma restringir são as **páginas renderizadas**
do painel, e `/static/` normalmente fica fora de qualquer `Disallow`.

O próprio documento marca a verificação como pendente, e é essa a razão de o coletor continuar fora.
**Argumento sobre o que o `robots.txt` provavelmente diz não é o `robots.txt`.** Um site que este
projeto já recusou uma vez não volta a ser coletado por raciocínio plausível — volta por leitura.

E há **dois** bloqueios, não um. O documento trata só do primeiro:

1. **`robots.txt` não lido.** Nunca conseguimos abrir o arquivo para ver o texto literal nem um
   eventual `Crawl-delay`.
2. **Cadeia de certificado incompleta.** A sonda de 31/08 falhou com
   `CERTIFICATE_VERIFY_FAILED — unable to get local issuer certificate`; o servidor de Blumenau não
   envia o intermediário. O navegador disfarça (busca pelo AIA), o Python não. **Não desligar a
   verificação** — abriria a coleta para qualquer um no caminho injetar nível de rio. O conserto é
   baixar o intermediário que falta e passá-lo como CA.

O segundo bloqueio é justamente o que impede o primeiro de ser resolvido pelo caminho óbvio: sem
cadeia, o `curl` não busca nem o `robots.txt`.

**Os dois comandos que destravam, na VPS:**

```bash
# 1) o texto literal do robots.txt
curl -sS https://defesacivil.blumenau.sc.gov.br/robots.txt

# 2) se falhar por certificado, ver o que o servidor manda e de quem falta o intermediário
echo | openssl s_client -connect defesacivil.blumenau.sc.gov.br:443 \
  -servername defesacivil.blumenau.sc.gov.br 2>/dev/null | grep -E "^ *[0-9]+ s:|^ *i:|Verify return"
```

Registrar aqui o resultado — data e trecho literal — para a conformidade ficar **documentada, não
presumida**. Se `/static/` e `/p/enchentes` não aparecerem em `Disallow`, o coletor entra; e o
`User-Agent` identificado e o cron de 10 min que o documento já prevê são as boas práticas certas
para acompanhá-lo.

### O que muda quando entrar

Menos do que parece para o **nível**: a correção de 31/08 mostrou que o AlertaBlu publica o mesmo
valor com a mesma idade que já recebemos pela página da Defesa Civil de Itajaí — 5,11 m há 3 h, nos
dois. A defasagem é da estação, não do caminho.

O que muda de verdade é a **tabela histórica de `/p/enchentes`**: 102 enchentes de 1852 a 2024, da
fonte municipal oficial. Ver `docs/fontes-academicas.md` para o que ela já complicou — o valor de
set/2011 que ela publica não é o que a regra de referência de Blumenau pressupõe.


## Gaspar: o host não responde de fora da região (01/09/2026)

`defesacivil.gaspar.sc.gov.br` **resolve no DNS e não aceita conexão** de uma VPS na
Finlândia. Três tentativas, duas datas, com a causa isolada em 01/09:

```
getent ahosts defesacivil.gaspar.sc.gov.br   → 186.250.184.3   (só IPv4, sem AAAA)
curl -4 ... /robots.txt                      → timeout de conexão em 15 s
curl -4 ... /                                → timeout de conexão em 15 s
```

Não é IPv6 (não há registro AAAA), não é DNS (resolve), não é TLS (a conexão não chega a
ser estabelecida) e não é o nosso cliente HTTP (o `curl` cru falha igual). O pacote sai e
não volta: ou o host recusa tráfego de fora do Brasil, ou está fora para quem vem daqui.

**Nenhuma mudança de código conserta isso**, e o `coleta_gaspar.py` faz o certo ao recusar:
erro de rede não vira permissão.

**O caminho que funciona** é o mesmo do KML de Brusque e do PDF de Blumenau: o navegador de
quem mora na região alcança a página. Salvar o HTML e passar em `--arquivo` faz o parser
rodar sem tocar na rede — e, como não há requisição, também não há `robots.txt` a consultar.

```
python3 scripts/coleta_gaspar.py --arquivo pagina-salva.html --cotas
```

Vale lembrar o que isso resolve e o que não resolve: mesmo com a página em mãos, se a tabela
publicar só o nível atual, **as cotas de régua de Gaspar continuam faltando** — e aí vêm por
ofício à Defesa Civil ou pelo Plano de Contingência, como foi com as onze estações de Itajaí.


### A tabela chegou pelo navegador, e a resposta é "não tem cota" (01/09/2026)

A página foi salva do navegador de quem está na região e está em
`data/brutos/gaspar-monitoramento-2026-08-31.html`. O parser leu:

| | |
|---|---|
| **Rio Itajaí Açu Gaspar** | **3,85 m** · 31/08 22:59 · fonte "DC. Gaspar" |
| Ribeirão Belchior Central | 1,68 m · 31/08 23:24 |
| seis pluviômetros | 82 a 108 mm em 24 h |
| Barragens Norte, Oeste e Sul | 265,90 · 351,81 · 392,62 m — cota de reservatório acima do mar, marcadas como fora da faixa de nível de rio |

**Nenhuma faixa de cota.** A tabela tem dez colunas — Estação, Fonte, Coleta, Nível e cinco de
chuva — e nenhuma delas é limiar. O que a página publica é leitura, não referência.

Então está respondido: **as cotas de régua de Gaspar não estão nesta página** e precisam vir da
Defesa Civil, por ofício ou pelo Plano de Contingência do município — que o próprio menu do site
publica em `/plano-de-contingencia`, e que é o caminho mais curto por ser o mesmo salvar-do-
navegador.

#### O que a página real ensinou sobre o parser

A primeira versão leu **zero estações** dela, e passava em todos os testes. Duas suposições
minhas, as duas erradas:

* **o nível vem sem unidade** — `<td>3,85</td>`, não "3,85 m". Eu tinha tornado o "m"
  obrigatório justamente para separar nível de porcentagem, e a regra que protegia de um erro
  causou outro;
* **a data vem sem ano** — "31/08 22:59".

A correção não foi afrouxar a regex: foi **ler pela coluna do cabeçalho**. Assim chuva fica na
coluna de chuva e nível na de nível, sem nada deduzido do formato do número — e o risco original
(a porcentagem virar nível) some junto, estruturalmente. O ano ausente é resolvido pela única
leitura possível para uma medição já feita: o ano corrente, ou o anterior se isso jogaria a
data no futuro.

A página está no repositório como fixture, e os testes rodam contra ela. Exemplo inventado passa
enquanto a fonte muda embaixo dele — foi exatamente o que aconteceu aqui.

## Gaspar pela rede estadual: por que o número existe e não pode ser usado (01/09/2026)

Chegou a proposta de contornar o host do município lendo Gaspar pela rede estadual — a estação
`DCSC-00005` no GraphQL da Defesa Civil de SC. Faz sentido como ideia: Gaspar ganhou cota de régua
(5,00 / 6,00 / 7,00 m, do Plano de Contingência) e é a única cidade do eixo com cota e sem leitura.

**Três coisas, medidas, dizem que ainda não dá.**

**1. No instante em que foi testada, a estação não devolveu nível.** O snapshot estadual de
01/09/2026 03:09Z registra: *"Gaspar (DCSC-00005) e Blumenau (DCSC-00026) NÃO retornaram valor de
nível neste instante"*. Chuva veio (77,2 mm/24h em Gaspar); nível, não. A premissa da proposta não
se sustentou na primeira medição.

**2. E a proposta em shell não avisaria disso.** O filtro era

```sh
jq -r '... | select(.codigo=="DCSC-00005") | "..."' || { echo "!! Não achei ..."; }
```

`jq` sai com **código 0** quando o `select` não casa com nada. Conferido:

```
$ jq -r '.[] | select(.codigo=="DCSC-00005") | "achei"' fake.json
$ echo $?
0
```

Ou seja: o `||` nunca roda, a saída é **nenhuma linha**, e logo abaixo o script imprime alegremente
`snapshot salvo em ...`. No caso real das 03:09Z — que é o caso provável, porque a estação
frequentemente não traz nível — quem rodasse concluiria que deu certo. **Fonte que falha calada é
pior que fonte fora do ar**, porque a segunda a gente percebe.

**3. E se devolvesse, o número não poderia ser comparado com as faixas 5/6/7.** O `rio_nivel` da
rede estadual não está num zero só, e agora há duas medições da mesma cidade quase no mesmo instante:

| Data | Estação estadual | Estadual | Nossa régua (DC-11 Santa Regina) | Diferença |
|---|---|---|---|---|
| 31/08/2026 | `DCSC-00030` Ilhota | 10,34 m | 3,25 m | **7,09 m** |
| 01/09/2026 | `DCSC-00030` Ilhota | 10,67 m | 3,34 m | **7,33 m** |

Não é defasagem de horário — uma régua sobe centímetros por hora numa cheia, não sete metros. E não
é a rede inteira estar errada: **Brusque bate** (estadual 4,48 × nossa 4,42). A rede concorda em
algumas estações e está 7 m fora em outras, que é exatamente o que "não é a mesma grandeza entre
estações" significa, e o que o `coleta_chuva_sc.py` já registrava.

**Por que isso seria grave justamente em Gaspar.** As faixas são 5 / 6 / 7 m. Um deslocamento do
tamanho do de Ilhota **cobre a escala inteira**: mostraria RESPOSTA com o rio no leito ou, para o
outro lado, normalidade com a água na rua. A segunda mata. E não há como saber qual seria, porque
**nunca houve um par** — nível estadual de Gaspar e leitura da tabela do município no mesmo instante.

**O que destrava.** Esse par, e só ele. `scripts/gaspar_estadual.py` existe para juntá-lo: quando os
dois lados tiverem leitura ao mesmo tempo, ele imprime a diferença. Um par não fecha a questão — o
deslocamento tem de se repetir em níveis diferentes antes de virar constante e ser escrito em
`DESLOCAMENTO_CONHECIDO_M`, num commit que registre os pares aqui. Enquanto essa constante for
`None`, o script se recusa a propor o valor para aviso, não escreve em `data/tempo-real/ultimo.json`
e não alimenta o `alerta_cotas.py`. Há teste travando cada uma dessas três coisas.

**O que já dá para usar agora:** a **chuva** da mesma estação. Milímetro é milímetro em qualquer
lugar — não depende de régua, de zero nem de datum. Em 01/09/2026 a rede dava Ilhota 107,6 mm/24h,
Gaspar 77,2 e Blumenau 22,0. É a assimetria que explica a cheia descendo pelo baixo vale.

### Duas falhas do próprio `gaspar_estadual.py`, achadas na primeira execução na VPS

A primeira versão rodou e disse `SEM LEITURA` dos dois lados. Um dos dois estava errado.

**Procurava no arquivo errado.** `nivel_do_municipio()` lia `data/tempo-real/ultimo.json` — o
arquivo da coleta geral, onde Gaspar **não está**, que é exatamente a lacuna que motivou o script.
A leitura do município mora em `data/tempo-real/ultimo_gaspar.json`, que o `coleta_gaspar.py`
escreve, com a régua sob o rótulo `Rio Itajaí Açu Gaspar`. Havia **3,85 m** guardados no
repositório e o script dizia que não havia nada. Corrigido, com teste que falha se alguém apontar
de volta para o `ultimo.json` — ler dali traria o nível de *outra* cidade para o par de calibração.

**E a pior: pareava leituras a horas de distância.** Na execução real o lado estadual carimbou
`2026-09-01T03:24:30Z` e o do município, `2026-08-31T22:59` — **266 minutos** de intervalo. Com o
arquivo certo, a versão antiga teria subtraído os dois e impresso uma diferença como se fosse
deslocamento de régua. Numa cheia o rio sobe nesse tempo: o número seria parte régua, parte subida,
sem como separar — um valor que **parece medido e não é**, que é a única coisa que este script
existe para impedir.

Agora há `JANELA_MAXIMA_MIN = 30`. O par fora dela é **recusado**, com o intervalo dito na saída.
Trinta minutos porque a 20 cm/h — subida forte no médio Itajaí — a parcela de subida fica em ~10 cm,
uma ordem de grandeza abaixo do `LIMITE_DE_COERENCIA_M` de 1,00 m; há teste que trava essa relação.
Par com horário faltando de um lado também é recusado: sem carimbo não dá para afirmar "mesmo
instante".

**O que a execução também mostrou sobre a fonte.** A estação `DCSC-00005` respondeu com carimbo
fresco (`03:24:30Z`) e **sem valor de nível** — segunda observação independente, depois da de
03:09Z, e uma terceira às 03:33Z fez o mesmo. A metadados do GraphQL estadual **declara** sensor de
rio (`rio_nivel.value=true`, visto na coleta de resgate de 01/09/2026): a estação de Gaspar **não é
pluviômetro puro**, tem canal de régua previsto. Mas o **valor** de nível veio nulo nas três: na
prática ela publica chuva e não publica régua. Enquanto o número não vier, o caminho estadual não
serve como nível ao vivo — sobra o ofício à Defesa Civil de Gaspar pedindo um endpoint estável, e o
`gaspar_estadual.py` só juntará o par de calibração no dia em que a régua estadual devolver valor.

### A evidência do portão de Gaspar mudou de perna (01/09/2026)

Uma revisão de `coleta_itajai.py` chegou com uma linha só de diferença:

```diff
-    (r"^DC-11\b", "itajai-acu", "ilhota"),
+    (r"^DC-11\b", "itajai-acu", "itajai"),  # Santa Regina/Volta de Cima = bairro de Itajaí (montante)
```

Ela vem sem fonte geográfica, e **não foi aplicada** — ver a pendência da DC-11 no README. Mas obrigou
a revisar o que dependia da atribuição, e algo dependia.

O portão do `gaspar_estadual.py` estava apoiado no par **Ilhota (DCSC-00030) × nossa DC-11**: 10,67 m
contra 3,34 m. Esse par só prova zero diferente **se as duas leituras forem da mesma cidade**. Com o
município da DC-11 em aberto, ele pode estar comparando dois lugares distintos — e aí não prova nada.
A conclusão continuava certa; uma das pernas dela, não.

**A perna nova não depende de município nenhum.** É a mesma estrutura, nomeada igual nas duas fontes,
no mesmo intervalo de horas:

| Estrutura | Tabela do município de Gaspar | Rede estadual | Diferença |
|---|---|---|---|
| Barragem Sul Ituporanga | 392,62 m | **22,79 m** (`DCSC-00038`) | **369,83 m** |
| Barragem Oeste Taió | 351,81 m | **12,97 m** (`DCSC-00040`) | **338,84 m** |

Cota do reservatório acima do mar contra altura na escala do próprio barramento. Não há "mas será que
é o mesmo lugar?" a levantar: é o mesmo barramento, com o mesmo nome, nos dois arquivos. E a rede
estadual **concorda** com a nossa em outras estações (Brusque 4,48 × 4,42) — que é exatamente o que
"não é a mesma grandeza **entre estações**" significa: não dá para saber, estação a estação, qual das
duas coisas se está lendo.

O par de Ilhota ficou em `EVIDENCIA_CONTESTADA`, marcado, e há teste garantindo que o motivo impresso
ao recusar **não o cita**. Justificar a recusa com o argumento que caiu seria manter a decisão certa
pela razão errada — e a próxima pessoa a ler descobriria isso do pior jeito.

## EPAGRI/CIRAM — boletim de hidrologia: fonte nova, com códigos ANA e três armadilhas (01/09/2026)

Chegou o **Boletim n° 150/2026 da Equipe de Hidrologia da EPAGRI/CIRAM**, de 31/08/2026. Guardado em
`data/brutos/epagri-ciram-boletim-150-2026-08-31.pdf`. É a quarta rede a aparecer no projeto, depois da
Defesa Civil de Itajaí, da Defesa Civil de SC e da Asthon — e a primeira que publica **código ANA**.

### O que ele traz de novo

| Código | Município | Estação | 31/08 | Bacia no boletim |
|---|---|---|---|---|
| `83105000` | Alfredo Wagner | Saltinho | 115 cm | Itajaí-Açu |
| `83892990` | Vidal Ramos | Salseiro | 254 cm | Itajaí-Açu |
| `83029900` | Taió | Barragem Taió Montante | (só chuva) | Itajaí-Açu |

Nenhum dos três está no nosso cadastro. Contato: `sshidrosc@epagri.sc.gov.br`; o rodapé aponta um
"Rios On-Line", que pode ser a versão viva do que o PDF congela.

**O prêmio é o código ANA.** Vidal Ramos, Taió e Ituporanga estão com `codigo_ana: null` ou não
verificado, e é o código que destrava a série histórica no HidroWeb — que é o que falta para essas
cidades terem cota. Se a estação da EPAGRI for a mesma que já lemos, o `null` fecha.

### Armadilha 1 — os níveis estão em CENTÍMETROS

`254` é 2,54 m. O boletim escreve `(cm)` no cabeçalho de cada bloco e nunca repete a unidade nas
linhas. Um coletor que leia o número cru e grave em metros põe **254 m** no lugar de 2,54 m — e o
`nivel_plausivel()` do `comum.py` (0 < v < 25) pegaria esse caso, mas não pegaria um `115` virando
115 m se alguém afrouxar o teto. A chuva, no mesmo PDF, está em mm.

### Armadilha 2 — é foto das 06:00, não tempo real

O boletim diz, na primeira linha, que **"das 15 monitoradas, 15 encontram-se na condição de
normalidade"**. Isso é verdade às 06:00 de 31/08 e para as estações DELE. Às 23:35 do mesmo dia,
Rio do Sul estava em 6,56 m — **acima da cota de inundação de 6,50 m**. Não há contradição: são
estações diferentes, num horário 17 h anterior. Mas o registro fica, porque a frase "15 de 15 em
normalidade" é exatamente o tipo de coisa que, colada numa tela sem a hora, tranquiliza no dia errado.
**Este boletim nunca pode aparecer como estado atual.**

### Armadilha 3 — "Vidal Ramos / Salseiro" não é atribuível ainda

É tentador preencher `codigo_ana: "83892990"` em Vidal Ramos e seguir. **Não dá**, e a razão é a mesma
da DC-11, de uma hora antes: mesmo município não é mesma estação.

- A nossa estação de Vidal Ramos, pela Asthon, chama-se **"Vidal Ramos"**, fica em
  `-27.38547, -49.35812`, e tem `owner_id: "DCSC"` — ou seja, Asthon e Defesa Civil de SC são a
  **mesma régua**, o que confirma o que o README já dizia.
- A da EPAGRI chama-se **"Salseiro"**, e o boletim não publica coordenada.
- Nomes diferentes, mesmo município. Um município tem mais de uma régua — Itajaí tem onze.

E o teste que resolveria não pode ser feito com o que há: a EPAGRI leu **06:00** (254 cm) e a nossa
leitura mais próxima naquele dia é **12:21** (2,93 m, Asthon). Seis horas, com o rio subindo. Comparar
os dois daria um "deslocamento" que é parte régua e parte subida — a mesma armadilha que o
`JANELA_MAXIMA_MIN` do `gaspar_estadual.py` recusa. Resolve com coordenada da estação (pedir à EPAGRI)
ou com duas leituras a menos de 30 min uma da outra.

**Cuidado com o nome:** "Salseiros" também é um **bairro de Itajaí**, na lista de bairros
historicamente atingidos, 100 km rio abaixo. São coisas diferentes.

### E ele também não dispara aviso

O **boletim em PDF** não publica cota de referência por estação — serve para série e para código, não
para decidir faixa. Mas isso vale só para o PDF: o **Rios On-Line classifica cada estação em faixas**
(ver seção abaixo), então os limiares existem do lado da EPAGRI. Não os temos ainda; o PDF não os traz.

### O "Rios On-Line": endpoint mapeado pelo navegador, e por que ele não abre (01/09/2026)

A versão viva do boletim é `https://ciram.epagri.sc.gov.br/rios-online/` — Angular + Leaflet, sem um
dado no HTML. Investigada pelo navegador (o host não responde do ambiente de dev, e o site ainda arma
uma trava de `debugger` contra o DevTools — desarma com Ctrl+F8). O que ficou apurado:

**O `robots.txt` libera.** Só `/wp-admin/` está bloqueado; `/rios-online/` e a API estão livres. O
WordPress do host expõe só `wp/v2` e plugins de tema no `wp-json` — **nenhum namespace de hidrologia**.
Os dados vêm de um serviço à parte.

**Os endpoints:**

| O quê | Endpoint | Estado |
|---|---|---|
| Estações (o alvo) | `POST .../api/rios-online-server/webresources/monitoramentohidrologia/estacoesMapa` | **exige credencial** |
| Bacias | `GET .../api/rios-online-server/cache/bacias.txt` | **aberto** — Itajaí-Açú = código **8** |
| Tiles | `https://maps.epagri.sc.gov.br/tile/{z}/{x}/{y}.png` | aberto |

**Onde trava, com precisão.** O `estacoesMapa` responde 401 sem credencial, 406 com Content-Type
errado, e **401 mesmo no replay same-origin** (que reenvia o cookie). Ou seja: a credencial **não é o
cookie** — é um header `Authorization` que o app Angular injeta em tempo de execução. Lê-lo exigiria
abrir o bundle `main.<hash>.js` e achar a construção do header (o hash de 01/09 era `822c10b5600d8764`).

**O que o painel confirmou, e é o achado que muda a leitura desta fonte:** os ícones de status provam
que a EPAGRI **classifica cada estação em faixas** — `Enchente: Emergência / Alerta / Atenção`,
`Normal`, `Estiagem: Atenção / Alerta / Emergência` — com **tendência** `Subindo / Descendo / Parado`.
Os limiares existem na fonte. Se o `estacoesMapa` devolver os *thresholds*, e não só a cor, essa é a
**cota de referência que falta para Taió, Ituporanga e Vidal Ramos** — mais do que a coordenada.

**O caminho a partir daqui — e a recomendação.** Duas opções, e a segunda é a mais limpa para um órgão
público:

1. *Ler o bundle na VPS.* O `robots.txt` permite. `curl` o `main.<hash>.js` e procurar como o header
   `Authorization` é montado (token fixo do app, ou uma chamada de login prévia). Funciona, mas o
   endpoint é interno de uma app que resiste a inspeção: pode mudar de nome no próximo build, sem aviso.
   Um coletor apoiado nisso é frágil por construção.
2. *Pedir à EPAGRI.* E-mail a `sshidrosc@epagri.sc.gov.br` pedindo acesso documentado à API, citando o
   projeto. Resolve o header **e** já traz a relação código ANA ↔ coordenada de bandeja — o que mata a
   dúvida do Salseiro de uma vez. É o **ofício C5**, redigido em `docs/pendencias-navegador-e-oficios.md`.

Enquanto o acesso não vier, **nada é atribuído**: o `codigo_ana` `83892990` não vai para `vidal-ramos`
até a coordenada bater contra `-27.38547, -49.35812`. A regra é a mesma que barrou a DC-11: coordenada,
não nome.

### A norma da EPAGRI, lida por inteiro (RN de dez/2024): o que é aberto e o que é ofício (02/09/2026)

Chegou a norma oficial — *Normas e Procedimentos para o Fornecimento de Dados, Declarações e Laudos
Ambientais* (Deliberação DEX 05/2024, EPAGRI/Ciram). Ela reordena o que sabíamos das fontes da EPAGRI:

- **Existe download GRATUITO e imediato**, só com cadastro (pessoa física serve), em
  `https://ciram.epagri.sc.gov.br/dadosambientaispublicos/` — dados **horários brutos dos últimos 24
  meses**. As variáveis liberadas nesse download são: temperatura, umidade, vento, pressão,
  **precipitação** e **altura da maré**. Para o resto (inclusive **nível do rio**) e para além dos 24
  meses, é solicitação (item 3).
- **Achado que muda a tela do Itajaí:** a **altura de maré** da EPAGRI é um dado ABERTO (Anexo I:
  5 min e horária), não precisa de ofício. Hoje o `PainelMare` mostra só maré **prevista** (tábua, via
  `coleta_mares.py`) porque o marégrafo de Cabeçudas não publica — mas se houver uma PCD maregráfica da
  EPAGRI no estuário de Itajaí, esse portal dá maré **medida**. Antes de usar: confirmar por
  **coordenada** que a PCD está no porto/estuário de Itajaí (regra do projeto), e conferir o fuso do
  arquivo (a norma não declara; abrir o CSV e checar contra uma leitura conhecida). Enquanto não
  confirmado, a maré segue **prevista** — não trocar por suposição.
- **Nível do rio NÃO está no download imediato** — confirma que o ofício C9/C5 (acesso programático ao
  Rios On-Line, com código ANA ↔ coordenada e as faixas) continua sendo o caminho certo para o nível.
- **Séries temporais por e-mail** (`dadosciram@epagri.sc.gov.br`) são o canal PAGO por padrão (Anexo IV:
  R$ 11,86 + R$ 0,48/dado). Acadêmico tem isenção (item 4.1), **mas** o Anexo II exige carta timbrada
  assinada pelo **orientador/chefe de departamento** — que o projeto não tem. Por isso o enquadramento
  comunitário do C9, dirigido à **Sala de Situação** (`sshidrosc@`), foi a escolha deliberada e correta:
  desvia dos dois pedágios (nota fiscal e ofício de orientador) caindo no canal de acesso ao painel.
- **Regra de repasse:** a EPAGRI **não permite repasse a terceiros** e exige citação da fonte. Um site
  público que republica a série da EPAGRI precisa dessa autorização explícita — mais um motivo para o
  pedido formal do C9 pedir o *acesso ao painel/tempo real*, não a série temporal para redistribuir.

Norma guardada como referência; o quadro de status dos ofícios está em `docs/oficios-prontos.md`.

## Traçado dos rios para o mapa geográfico — OpenStreetMap (01/09/2026)

O mapa geográfico da tela do rio (fase 2b, no espírito do Kikikuru) usa o traçado dos rios do
**OpenStreetMap**, sob licença **ODbL** (crédito na tela e no GeoJSON). O egress do ambiente de dev
não alcança o Overpass; baixado na VPS.

**Bruto:** `data/brutos/tracado-rios-osm.json` (resposta `out geom;` do Overpass).
**Convertido por:** `scripts/converter_tracado_rios.py` → `data/rios/itajai-acu.geojson` e
`itajai-mirim.geojson` (um MultiLineString por rio, em [lon, lat]).

**Como regenerar (na VPS):**
```bash
UA='enchentes-vale-itajai/0.1 (+github.com/haohmarusc-glitch/enchentes-vale-itajai)'
curl -s -A "$UA" 'https://overpass-api.de/api/interpreter' \
  --data-urlencode 'data=[out:json][timeout:120];
    (
      way["waterway"="river"]["name"="Rio Itajaí-Açu"](-27.8,-50.2,-26.4,-48.4);
      way["waterway"="river"]["name"="Rio Itajaí do Oeste"](-27.8,-50.2,-26.4,-48.4);
      way["waterway"="river"]["name"="Rio Itajaí-Mirim"](-27.8,-50.2,-26.4,-48.4);
    );
    out geom;' > data/brutos/tracado-rios-osm.json
python3 scripts/converter_tracado_rios.py
```

**Decisões e limites registrados:**
- O Açu do site = **Rio Itajaí-Açu + Rio Itajaí do Oeste** (a cabeceira de Taió, que troca de nome
  na confluência de Rio do Sul). Assim a linha cobre o diagrama de Taió à foz.
- A **outra cabeceira, o Itajaí do Sul (Ituporanga), fica de fora** por enquanto — o eixo do
  diagrama do Açu segue Taió → Rio do Sul. Por isso **Ituporanga não tem marcador no mapa**.
- **Coordenadas das cidades** (`estacoes.json → cidade.coordenadas`, `[lat, lon]`): sede municipal
  aproximada (OSM/IBGE); Vidal Ramos exata da Asthon. Servem só para POSICIONAR o marcador, que
  **encaixa no ponto mais próximo do traçado** — imprecisão de sede não tira o ponto do rio. Não é
  dado de nível.
