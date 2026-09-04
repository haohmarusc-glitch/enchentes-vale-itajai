# API Asthon (Defesa Civil de Rio do Sul) — vasculhada completa

Base: `https://public.asthon.com.br/public/` · `city_id=4214805` · sem autenticação.

> ## ⚠️ Nota de verificação (04/09/2026) — LEIA ANTES DE USAR
>
> Este documento chegou como **relatório de uma sessão que tinha acesso de rede ao host**. A sessão que
> o arquivou aqui **não tem** (o proxy de saída recusa `public.asthon.com.br`), então conferiu o que deu
> contra os artefatos em `data/brutos/`. O resultado:
>
> | Afirmação do relatório | Situação |
> |---|---|
> | `panel.rivers` traz os traçados em GeoJSON, 10 rios | ✅ **VERIFICADO** — arquivo em `data/brutos/rio-do-sul-rios-tracados.geojson`, 10 LineStrings, coordenadas coerentes com Rio do Sul, `fonte` preenchida em cada feature. Inclui as duas cabeceiras (Itajaí do Sul, 35 pontos; Itajaí do Oeste, 95). |
> | Cobertura é municipal, não da bacia | ✅ **VERIFICADO** — os limites são apertados em volta de Rio do Sul (o Itajaí do Sul cobre ~0,08° de latitude). **Não é o curso do rio inteiro.** |
> | `panel.stations[].band_thresholds` entrega cota por régua, "resolve o datum do Alto Vale" para 21 réguas | ❌ **NÃO VERIFICADO, e parcialmente contrariado.** A captura que existe no repo (`rio-do-sul-asthon-2026-08-31.json`, e a cópia de 01/09 do snapshot v7.1) traz `band_thresholds` em `stations_live`, mas só para **3 estações**, e **Vidal Ramos vem com a lista VAZIA** — sem cota, sem `band_label`, sem `gauge_zero`. As duas que têm cota são as **barragens** (Oeste 11,65/16,31/23,3 com zero em 339 m; Sul 15,5/21,7/31,0 com zero em 370 m): escala de reservatório, que nunca pinta faixa de cidade. A captura do `panel` com 21 réguas **não está entre os artefatos recebidos**. |
> | Rio do Sul tem 3 réguas, uma por rio (Dom Tito Buss/Açu, Ricardo Kanitz/Sul, BR 470/Oeste) | 🟡 **PARCIAL.** `stations_list` confirma **Ponte Dom Tito Buss** no Rio Itajaí-Açu e **Ponte Ricardo Kanitz** no Rio Itajaí do Sul (e ainda uma quarta, *Ponte Hannelore Hartmann Eyng*, também no Sul). **"Ponte BR 470" não aparece** nessa captura. |
>
> **Consequência prática:** nada de cota foi gravado em `data/estacoes.json` a partir deste documento.

---

> ## ❌ RESOLVIDO PELA NEGATIVA (04/09/2026) — o `panel` FOI capturado, e não tem a cota
>
> O comando acima **foi executado na VPS**, que alcança o host. A resposta encerra a hipótese: para a
> régua de Vidal Ramos (`station_id` `bd65df3e-a5e3-4760-a879-56df0fb90787`), às 11:35 de 04/09
> (−03), o `panel` devolve
>
> | campo | valor |
> |---|---|
> | `level_m` | **2,50 m** |
> | `level_sensor` | `1` — é régua de rio, não barragem nem altitude |
> | `band_thresholds` | **`null`** |
> | `attention_level` | **`null`** |
> | `overflow_cota_m` | **`null`** |
> | `river_name` | **`null`** |
>
> Ou seja: **o endpoint publica o nível e não publica cota nenhuma para essa régua.** A afirmação de
> que o `panel` "entrega `band_thresholds` para 21 réguas e resolve o datum do Alto Vale" está
> **refutada** para a única régua da bacia que nos interessava aqui — não é captura incompleta, é
> ausência do campo na fonte.
>
> **Não repetir esta consulta.** O caminho Asthon para a cota de Vidal Ramos está fechado; o que resta
> é a EPAGRI ("Rios On-Line", que classifica por faixas — ofício C5) ou a COMPDEC de Vidal Ramos
> diretamente. Ver `docs/cotas-municipais/vidal-ramos.md`.
>
> O único número público que existe fora da API continua sendo **3,50 m de transbordo** (O Município,
> 2015; a Defesa Civil local, citada na mesma matéria, diz "acima de 3 m", sem faixa) — e continua
> **não gravado**, pelo motivo de sempre: gravar uma cota faz a cidade e os 84 km a jusante saírem
> **VERDES** abaixo dela, e um verde de 84 km apoiado em número de imprensa sobre comportamento afirma
> segurança que ninguém mediu. Cinza diz "não sei", que é a verdade. Ver a discussão no README.

---

## Endpoints (relatado, 03/09/2026)
22 nomes testados; 6 respondem.

| Endpoint | Retorno |
|---|---|
| `stations/list` | 27 estações |
| `stations/live` | 27 leituras ao vivo |
| **`panel`** | `{city_id, city, stations, rivers}` — o mais rico |
| `dams` | 2 barragens (Oeste e Sul) |
| **`shelters`** | 23 abrigos com status operacional |
| `cities/{id}/forecast/bulletin` | boletim (vazio no momento) |
| `city-site/cota-advisory` | aviso de cota |

Sem resposta: `news`, `alerts`, `contacts`, `rainfall`, `weather`, `forecast`, `history/levels`,
`reports`, `documents`, `risk-areas`, `cotas`, `streets`, `thresholds`, `city-site/{home,menu,links,config}`.

## Campos de cada estação no `panel` (relatado)
`station_id, name, station_type_id, latitude, longitude, river_name, river_position, level_sensor,
rainfall_sensor, overflow_cota_m, band_thresholds, attention_level, observation_level, band_key,
band_label, band_color, band_ordinal, band_is_overflow, level_status, level_m, rainfall_1h, rainfall_2h,
rainfall_24h, is_raining, last_reading_at`

Destaques a confirmar na captura: **`river_name`** e **`river_position`** (a fonte já diz a ordem da
estação no rio — se confirmado, poupa o cálculo de ordenação por coordenada) e `level_sensor`/
`rainfall_sensor` (o que a estação mede — mesmo papel do `tem_nivel_do_rio` da DC-SC).

## Traçados dos rios — ✅ o que entrou no repo
`data/brutos/rio-do-sul-rios-tracados.geojson`, 10 LineStrings:

| Rio | Pontos | Classe |
|---|---|---|
| Ribeirão do Tigre | 756 | — |
| Rio Itajaí-Açu | 239 | — |
| Rio Itoupava | 147 | Rio |
| Rio das Cobras | 138 | Rio |
| Ribeirão Fundo do Canoas | 119 | Ribeirão |
| Ribeirão Matador | 102 | Ribeirão |
| **Rio Itajaí do Oeste** | 95 | — |
| Ribeirão Taboão | 77 | Ribeirão |
| **Rio Itajaí do Sul** | 35 | Rio |
| Rio Trombudo | 27 | Rio |

**Por que ficou em `data/brutos/` e não em `data/rios/`:** os arquivos de `data/rios/` são o traçado que o
mapa desenha como sendo *o rio*. Estes cobrem só o trecho **dentro/perto de Rio do Sul** — o Itajaí do Sul
com 35 pontos não é o curso que vem de Ituporanga, é um pedaço dele. Desenhar esse pedaço como "o Itajaí
do Sul" afirmaria uma geografia errada na tela. Para virar traçado de mapa, precisa ser completado (Overpass,
como os outros) ou desenhado explicitamente rotulado como "trecho em Rio do Sul".

**O que já destrava, mesmo assim:** dá para achar a **confluência** Oeste × Sul × Açu em Rio do Sul por
geometria (é onde os três se tocam), que é o que `scripts/achar_confluencias.py` faz — e a confluência
está dentro da cobertura municipal, então o pedaço basta para isso.

## Abrigos de Rio do Sul (relatado, não verificado aqui)
`shelters` → 23 abrigos, com `status`, `occupancy_current`, `vacancies`, `status_changed_at`, capacidade
total 1.776. Diferente de Itajaí (cadastro puro): aqui há **estado operacional com carimbo de tempo**.

**A regra de exibição não muda:** o site pode dizer "a Defesa Civil informa este abrigo como fechado,
atualizado em ‹data›", com fonte e idade à vista — **nunca** "vá para este abrigo". Quem ativa abrigo e
manda evacuar é a Defesa Civil (199). O `status_changed_at` de 25/08 na captura relatada mostra por que a
idade importa: o dado pode estar dias velho.
