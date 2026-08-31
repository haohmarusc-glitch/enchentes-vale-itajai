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
