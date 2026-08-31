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
