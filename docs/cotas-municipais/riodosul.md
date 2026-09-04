# Rio do Sul — API Asthon, cotas e manchas

**Portal:** https://defesacivil.riodosul.sc.gov.br/  
**IBGE:** `4214805`  
**Estação no monitor:** DCSC-00013 · ANA 83300200 · início do tronco do Itajaí-Açu  
**Leitura conferida:** 3–4 de setembro de 2026 (~21:30–21:33)  
**Emergência:** 199. Este arquivo não substitui aviso oficial.

O site novo é SPA (Asthon). O Yii antigo ainda responde em rotas `index.php?r=…`.

---

## Nível agora (painel)

Faixa no topo: **ATENÇÃO · 5,33 m**.

| Régua | Nível | Chuva | Papel no painel |
|---|---|---|---|
| Ponte Dom Tito Buss (referência) | **5,33 m** | 0 mm | `is_reference`, gráfico + chuva |
| Ponte Dom Tito Buss — DCSC | 5,50 m | — | mesma ponte, sensor estadual |
| Ponte BR-470 | 5,31 m | — | no painel |
| Ponte Ricardo Kanitz | 5,55 m | — | no painel (Itajaí do Oeste / Bonfim) |
| Ponte Hannelore Hartmann Eyng | 5,59 m | 0 mm | Itajaí do Sul (fora do card principal) |

Câmera ao vivo: Elevado José Thomé.

---

## Cotas oficiais da régua da cidade

A API devolve as mesmas faixas no campo `band_thresholds` de cada estação urbana:

| Faixa | Cota | Cor no painel |
|---|---|---|
| Atenção | **4,50 m** | amarelo `#eab308` |
| Alerta | **5,50 m** | laranja `#f97316` |
| Emergência / overflow | **6,50 m** | vermelho `#ef4444` (`is_overflow`) |

O gráfico da home ainda marca um traço em **8,00 m** (escala, não faixa de acionamento).  
Abrigos abrem a **7,00 m** (acima da emergência cadastrada) — o aviso automático que para em 6,50 m sai *antes* da abertura.

Há obra estadual de Melhorias Fluviais Rio do Sul–Lontras (rebaixamento + comporta), em licitação em 2026. Essas cotas valem para o rio de hoje.

```json
"cotas_m": {
  "atencao": 4.5,
  "alerta": 5.5,
  "inundacao": 6.5,
  "abrigos": 7.0
}
```

Já está no `estacoes.json` do monitor (sem `abrigos`).

---

## API pública (sem login)

Base: `https://public.asthon.com.br/public`  
Query: `city_id=4214805&_v=2`

| Endpoint | Uso |
|---|---|
| `/stations/live` | nível, chuva, `band_thresholds`, `overflow_cota_m`, `band_label` |
| `/city-site/stations` | lista das 5 réguas + `cota_ref` (nome do ponto / lat lon) |
| `/stations/list` | catálogo |
| `/station-history?station_id=…&fields=level\|rain&resolution=hourly&start=&end=` | série |
| `/dams` | Barragem Oeste (Taió) e Barragem Sul (Ituporanga) no painel da cidade |
| `/panel` | payload do dashboard |
| `/cities/4214805/forecast/bulletin` | boletim |
| `/shelters` | abrigos |
| `/city-news` | comunicados |
| `/state-bulletins?uf=SC` | DC-SC |
| `/city-site/cota-advisory` | hoje veio `advisory: null` |

Estação de referência (Dom Tito Buss):

```
f6360951-219f-4859-935f-b2e2d13962f1
```

Histórico (exemplo últimas 24 h, nível horário):

```
GET https://public.asthon.com.br/public/station-history?station_id=f6360951-219f-4859-935f-b2e2d13962f1&start=2026-09-03T00:00:00.000Z&end=2026-09-04T00:00:00.000Z&fields=level&resolution=hourly&_v=2
```

`/stations/live?city_id=4214805` devolve **27 estações** (região, não só o município). Filtrar pelos 5 `station_id` acima.

Amostra `band_thresholds` (Dom Tito Buss):

```json
[
  {"band_key": "atencao", "label": "Atenção", "cota_m": 4.5, "is_overflow": false},
  {"band_key": "alerta", "label": "Alerta", "cota_m": 5.5, "is_overflow": false},
  {"band_key": "emergencia", "label": "Emergência", "cota_m": 6.5, "is_overflow": true}
]
```

`overflow_cota_m` = 6,5.

---

## Barragens no mesmo painel (outra escala)

| Barragem | `nivel_m` agora | Emergência de reservatório | Comportas |
|---|---|---|---|
| Oeste — Taió | 17,0 m (régua da barragem) | **23,30 m** | 7/7 abertas |
| Sul — Ituporanga | 25,6 m | **31,00 m** | 4/5 abertas |

Não pintar a cidade com `montante` / `nivel_m` da barragem. É o mesmo erro de misturar Taió-cidade (5 m) com Taió-barragem (17 m).

---

## Cotas de rua e manchas

Menu do portal:

- **Cotas de Cheia por Rua** — 555 logradouros (mínima / máxima). Yii ainda no ar:  
  https://defesacivil.riodosul.sc.gov.br/index.php?r=soscota-rua%2Ftabela  
  Primeiras vias da lista (mínima mais baixa): Pouso Redondo 3,11–7,48; SD 1604 3,26–12,47. Várias ruas começam a molhar **antes** da emergência da régua (6,50).
- **Histórico de Cheias**
- **Manchas de Inundação** (mapa no portal)
- **Pontos de Alagamento**
- **Áreas de Risco**
- **Transenchentes**

O My Maps de pesquisa citado no levantamento geral **não** é o da COMPDEC. Usar o mapa do próprio portal.

---

## Como ligar no coletor

1. GET `/stations/live?city_id=4214805&_v=2` a cada 5 min.  
2. Pegar `f6360951-…` (Dom Tito Buss) → `level_m`, `last_reading_at`, `band_label`.  
3. Faixas estáticas 4,50 / 5,50 / 6,50 (já vêm no JSON).  
4. Opcional: Kanitz e BR-470 no mesmo card.  
5. Barragens: endpoint `/dams`, card separado.  
6. Rua: tabela Yii ou export já no repo (555 pontos).

A URL antiga `index.php?r=externo%2Fmetragem` ainda aparece no `estacoes.json`; o painel vivo agora é Asthon.
