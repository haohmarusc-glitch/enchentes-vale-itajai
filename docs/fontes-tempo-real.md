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
