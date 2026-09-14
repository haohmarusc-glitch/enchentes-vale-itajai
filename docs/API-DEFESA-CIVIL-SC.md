<!-- Levantado pelo Jefferson em 13/09/2026, a partir do bundle do próprio site. Trazido para o
     repo sem alteração de conteúdo; os blocos marcados "NOTA DO REPO" foram acrescentados aqui. -->

# API da Defesa Civil de SC — monitoramento.defesacivil.sc.gov.br

Levantamento feito em 13/09/2026 a partir do bundle do próprio site.

## Endpoint

```
POST https://monitoramento.defesacivil.sc.gov.br/graphql
Content-Type: application/json
```

**Sem autenticação.** Não precisa de token, cookie nem chave.

### A regra que derruba quase toda tentativa

O servidor rejeita qualquer requisição cujo `operationName` não seja um dos
quatro nomes que o próprio site usa, respondendo `{"errors":[{"message":"Operação bloqueada."}]}`:

| operationName | o que devolve |
|---|---|
| `Tags_data` | leitura atual de todas as estações |
| `Historic` | série histórica de uma estação |
| `Radares` | imagens de radar |
| `Nowcasting` | subscription |

Os **campos** dentro da query são livres (dá para pedir mais do que o site pede —
foi assim que apareceram os alarmes). O que não pode mudar é o nome da operação
e o `client`, que tem de ser a string `"secretaria-de-defesa-civil"`.

Introspection (`__schema`, `__type`) está **aberta** e não sofre esse bloqueio.

---

## 1. `Tags_data` — leitura atual

```graphql
query Tags_data {
  tags_data(clients: ["secretaria-de-defesa-civil"]) {
    qualle_meteorologia {
      codigo type timestamp
      name     { prefix general local }
      position { bacia regiao latitude longitude altitude }
      data {
        rio {
          rio_nivel { value } rio_nivel_tendencia { value } rio_vazao { value }
          rio_alarmes {
            inundacao { ativo{value} status{value}
                        atencao{value} alerta{value} emergencia{value} }
            estiagem  { atencao{value} alerta{value} emergencia{value} }
          }
        }
        chuva { acumulado { h001{value} h024{value} h168{value} } }
      }
    }
  }
}
```

**174 estações** no total; **97** com nível de rio. Tipos: `Hidro`, `Meteo`,
`Pluvio`, `Barragem`. A bacia `SC - Rio Itajaí` tem 61 estações
(66 contando a região "Vale do Itajaí").

### `rio_alarmes` — o que é e o que não é

`atencao`, `alerta` e `emergencia` **não são as cotas em metros**. São flags
0/1 dizendo em que faixa a estação está *agora*. Ou seja: a API não publica a
tabela de cotas, mas publica a **classificação pronta** — o que resolve o
problema da régua colorida sem precisar da cota.

Amostra real de 13/09/2026 23:01:

| estação | nível | atenção | alerta | emergência | status |
|---|---|---|---|---|---|
| DCSC-00013 Rio do Sul | 5,46 | 1 | 0 | 0 | 2 |
| DCSC-00031 Laurentino | 5,49 | 1 | 0 | 0 | 2 |
| DCSC-00032 Lontras | 5,50 | 1 | 0 | 0 | 2 |
| DCSC-00020 Ibirama | 2,67 | 1 | 0 | 0 | 2 |
| DCSC-00018 Botuverá 1 | 3,19 | 1 | 0 | 0 | 2 |
| DCSC-00021 José Boiteux | 3,06 | 0 | 1 | 0 | 1 |
| DCSC-00039 Ituporanga | 3,42 | 0 | 1 | 0 | 1 |

O campo `status` acompanha a faixa (2 junto de `atencao`, 1 junto de `alerta`),
mas a numeração parece invertida em relação à severidade — **confirmar antes de
usar `status` sozinho**. O caminho seguro é ler as três flags.

### Cuidado com a unidade de `rio_nivel`

Vem misturado. Parte das estações informa **régua** (Indaial 6,39; Vidal Ramos 2,54;
Brusque 1,77) e parte informa **cota absoluta em metros acima do nível do mar**
(Rio do Campo 576,22; Atalanta 453,42; Mirim Doce 348,86). `unit` volta `null`.
Uma heurística prática: valor acima de ~100 é cota absoluta, não régua.

---

## 2. `Historic` — série histórica (o desbloqueio do Indaial)

```graphql
query Historic($stationCode: String!, $startDate: String!, $endDate: String!, $interval: QueryInterval) {
  historic(system: Qualle_Hidrometeorologia, client: "secretaria-de-defesa-civil",
           stationCode: $stationCode, startDate: $startDate, endDate: $endDate,
           interval: $interval, opts: { ordenacao: ASC })
}
```

Variáveis: datas em ISO-8601 UTC. `interval` ∈ `MIN_5, MIN_10, MIN_15, MIN_30,
HOUR_1, HOUR_3, HOUR_6, HOUR_12, HOUR_24, HOUR_48, HOUR_72, HOUR_96, HOUR_168`.

Resposta (`JSON` escalar): `{ items: [...], totalCount: n }`, cada item:

```json
{"ts":"2026-09-05T22:00:00.000","codigo":"DCSC-00006",
 "rio_nivel":6.14,"rio_variacao":0,
 "chuva_mm":0.08,"chuva_total":0.08,"chuva_taxa_med":0.125,"chuva_taxa_max":1.3,
 "bateria_v":12.375}
```

**DCSC-00006 (Indaial) responde normalmente** — era exatamente o ponto que estava
travado. Teste feito: 30 dias em `HOUR_1` = 743 pontos; 30 dias em `MIN_5` = 8.631 pontos.

### Os dois limites (medidos, não documentados)

1. **Janela por requisição:** até ~70 dias passa, 90 dias é recusado. Use ≤ 60 dias por chamada.
2. **Profundidade:** `startDate` só pode ir até **~89 dias atrás**. A partir de 90
   dias tudo volta `Operação bloqueada`, seja qual for o tamanho da janela.
   Janelas inteiramente no passado funcionam (ex.: −60 a −30 dias), desde que
   dentro dos 89 dias.
3. Rajadas são bloqueadas. Dê ~1 s entre chamadas.

**Consequência para o projeto:** a API é uma janela móvel de 90 dias, não um
arquivo histórico. As enchentes de 1983, 1984, 2008, 2011 e 2023 **não estão
aqui** — continuam dependendo da ANA/Hidroweb, do CEOPS/FURB e do ArcGIS da
Prefeitura de Itajaí. O jeito de ter histórico longo é começar a coletar agora e
acumular (é o que o `scripts/coletar_dcsc.py` faz, com append sem duplicar).

---

## 3. Outras fontes que o site usa

- `https://tile-service.quallecontrol.com.br/table.dcsc.rios.geom` — geometria dos rios (vector tiles)
- `https://tile-service.quallecontrol.com.br/table.dcsc.regioes.geom` — geometria das regiões
- `https://monitoramento.defesacivil.sc.gov.br/api/radares/imagens/` — imagens de radar
- Basemap: CARTO Voyager

---

## Exemplo mínimo (curl)

```bash
curl -s https://monitoramento.defesacivil.sc.gov.br/graphql \
  -H 'content-type: application/json' \
  -d '{"operationName":"Historic",
       "query":"query Historic($stationCode: String!, $startDate: String!, $endDate: String!, $interval: QueryInterval) { historic(system: Qualle_Hidrometeorologia, client: \"secretaria-de-defesa-civil\", stationCode: $stationCode, startDate: $startDate, endDate: $endDate, interval: $interval, opts: { ordenacao: ASC }) }",
       "variables":{"stationCode":"DCSC-00006",
                    "startDate":"2026-09-06T00:00:00.000Z",
                    "endDate":"2026-09-13T23:00:00.000Z",
                    "interval":"HOUR_1"}}'
```

---

## NOTA DO REPO — o que já existe aqui e o que esta API destrava

| já no repo | o que faz |
|---|---|
| `scripts/coleta_nivel_sc.py` | leitura ao vivo (`Tags_data`), com as sete armadilhas tratadas |
| `scripts/coleta_chuva_sc.py` | chuva da mesma fonte |
| `scripts/baixar_historico_dcsc.py` | **novo (13/09)** — baixa as janelas da `Historic` |
| `scripts/consolidar_historico_dcsc.py` | interpreta as janelas e escreve `data/series/dcsc/*.csv` |
| `docs/API-DCSC-CAMPOS-NOVOS.md` | investigação de `type` e `tem_nivel_do_rio` (03/09) |

O baixador grava a resposta **crua**, no formato que o consolidador já lê, e o consolidador é o
único lugar que interpreta (sentinelas, picos de sensor, cristas). De propósito: duas leituras
independentes do mesmo dado acabam divergindo, e a divergência aparece numa cheia.

### ⚠️ A unidade de `rio_nivel` é o risco desta fonte

A própria API mistura **régua** com **cota absoluta acima do nível do mar** e devolve `unit: null`.
Na amostra de 13/09: Indaial 6,39 e Brusque 1,77 são régua; Rio do Campo 576,22 e Atalanta 453,42
são altitude. O `coleta_nivel_sc.py` descarta acima de 30 m — mas **Ilhota 9,96 m e Guabiruba
24,83 m passam pelo filtro e ninguém conferiu em que zero estão**.

Vale aqui a regra nº 1 do projeto: uma cota só pinta quando está amarrada à MESMA régua da
leitura. Nível da rede estadual sai com `usar_para_cota=False` até um offset ser calibrado por
estação — e um ponto só não basta (o caso Brusque, em 01/09: "offset ~0" às 17 h virou 1,9 m de
diferença às 23 h).

### `rio_alarmes` — a saída para pintar sem ter a cota

O campo publica, por estação, as flags `atencao`/`alerta`/`emergencia` **já classificadas pela
Defesa Civil de SC, no datum dela**. Isso contorna o problema acima sem violá-lo: não se compara
metro com metro nem se inventa cota — mostra-se a faixa que a fonte declara, dizendo de quem é.
É a rota mais curta para as cidades que hoje ficam cinzas por falta de cota casada com a régua.

**Coletado desde 14/09/2026** (`coleta_nivel_sc.classificar_alarmes`, aprovado pelo Jefferson com
condições): a `QUERY_CAMPOS_NOVOS` pede `rio_alarmes.inundacao`; cada leitura de
`ultimo_nivel_sc.json` ganha `classificacao_estadual` com `faixa` ∈ {atencao, alerta, emergencia}
ou `null`, mais o bruto (`ativo`, as três flags, `status`) e um `motivo` quando não há faixa.
Regras: `ativo = true` obrigatório; no máximo UMA flag ligada (duas = contraditório = `null`);
**"normal" não é afirmado** enquanto a semântica de `ativo` sem flag e a numeração de `status` não
forem validadas com dados reais na VPS. O site mostra a faixa no painel "Nível bruto — rede
estadual", rotulada como **classificação da Defesa Civil de SC**, só com leitura recente; nada disto
entra em `leituras`, então o bot de cotas não dispara por isto. A série `nivel-sc-AAAA-MM.ndjson`
guarda `faixa_estadual` por leitura — é com ela que se valida a semântica.

**Achado da primeira execução real (14/09/2026, 22:03 BRT, VPS):** a query enriquecida de 03/09
respondia **HTTP 400** e o coletor caía em silêncio para a query de 01/09 — ou seja, `type`,
`tem_nivel_do_rio` e agora `rio_alarmes` nunca tinham chegado; a classificação por dicionário
(`NAO_MEDE_NIVEL`/`SUSPEITAS`) foi o que valeu o tempo todo. Causa de forma: `rio_nome` e
`rio_area_drenagem` são objetos e exigem `{ value }` (é assim no script de 13/09, que funcionou), e
`filter { relacao { … } }` não existe no levantamento por introspecção. A query foi alinhada à
forma provada e o `filter` saiu. **Confirmar na próxima execução**: o aviso "query enriquecida …
recusada" NÃO pode aparecer; se aparecer, o 400 tem outra causa e a `Historic` de introspecção decide.

**Validação pendente na VPS (antes de pintar o mapa):** rodar `python3 scripts/coleta_nivel_sc.py`
e conferir em `ultimo_nivel_sc.json` (a) se estações em NORMAL no site oficial vêm com `ativo: true`
e nenhuma flag (então "normal" pode ser afirmado) ou com `ativo: false`; (b) a tabela `status` ×
flag em várias estações; (c) que nenhuma leitura veio `contraditório`.

Uma ressalva antes de usar: o campo `status` acompanha a faixa mas parece numerado ao contrário
da severidade. Ler as três flags, nunca o `status` sozinho.

### Não é arquivo histórico

Janela móvel de ~90 dias. 1983, 1984, 2008, 2011 e 2023 **não estão aqui**. Série longa só
acumulando — o baixador é idempotente e nunca rebaixa janela que já está no disco, justamente
para rodar em cron sem repetir trabalho nem abrir buraco.
