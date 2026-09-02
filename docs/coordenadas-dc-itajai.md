# Coordenadas das 11 réguas DC de Itajaí — busca no ArcGIS (02/09/2026)

> **✅ ATUALIZAÇÃO (02/09/2026): as 11 coordenadas foram ENCONTRADAS** — não no ArcGIS (que segue
> atrás de token, abaixo), mas nos **marcadores Leaflet da página `Mapa.php` da Defesa Civil de Itajaí**
> (`defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php`), lidas do HTML. Preenchidas em
> `data/estacoes.json` → `estacoes_tempo_real` por `scripts/preencher_coordenadas_dc.py` (com
> `fonte_coordenada` e teste travando a coerência: DC-01/CEPSUL a mais perto da foz, DC-10/Limoeiro a mais
> longe). **Destrava a ordenação do Mirim** (próximo passo: `scripts/ordenar_estacoes_itajai.py` projetando
> no traçado, para desempatar DC-04×DC-06). O resto desta seção fica como registro histórico da busca.


Objetivo: preencher `coordenadas` das réguas DC-01..DC-11 em `data/estacoes.json` para ordenar o
Itajaí-Mirim (e os demais) **pela descida do rio em direção ao mar**, em vez de por descrição.

## Resultado: ❌ as réguas NÃO estão no ArcGIS público — estão atrás de token

Varredura completa do ArcGIS da Prefeitura (`arcgis.itajai.sc.gov.br/server/rest/services`), pelo
navegador:

- **Raiz** (200 serviços): filtrada por `estac|telemetr|pluvio|regua|sensor|pcd|monitora|alerta|defesa`
  → **zero** estação de medição. Os `Hidrografia_*` são feições (área úmida, barragem, canal, ilha,
  massa d'água, oceano), não réguas.
- **Pasta `defesacivil`**: existe, mas **"Token Required"**. É quase certo que as réguas estão aqui.
- **Pasta `Hosted`** (621 serviços): busca por `telemetr|estac|régua|fluvi|maregraf|linimetr|hidrolog|
  nivel_rio|DC-\d` → **zero**. Os `Cotas_Inundação_*` são as manchas por evento (já temos); `Cota_20`
  é curva de nível topográfica, não régua.

**Conclusão:** a camada de estações da Defesa Civil está fechada por token. A régua DC segue **sem
coordenada em fonte pública**, então a ordenação por descida do rio **não pode ser feita sem inventar**
— e o projeto não inventa coordenada.

### Caminhos para obter as coordenadas (em ordem)
1. **Ofício C2 (GEOItajaí)** — enviado 31/08; **complementar** pedindo explicitamente lat/lon das 11
   réguas DC-01..DC-11.
2. **GPS em campo** — 11 pontos em Itajaí, ~meia manhã; resolve de vez e com precisão.
3. **Reunião Univali (03/09)** — perguntar se têm as coordenadas das réguas da DC.

Enquanto não vierem, o `/rios` mostra o Mirim na ordem do cadastro (cidade→rio), e as réguas de Itajaí
saem por código (DC-03..DC-10). A ordem física real (descida ao mar) fica pendente da coordenada.

> **Nota hidrográfica** (por descrição do Plano da COMPDEC, Tabela 11 — NÃO por coordenada, a confirmar):
> em Itajaí o Mirim se divide em dois braços paralelos até o estuário. DC-10 (Limoeiro) é o ponto mais a
> montante; depois o rio se separa em **curso antigo** (DC-05 Sítio Sr. Hilário, DC-06 Clube Itamirim) e
> **canal retificado** (DC-03 Captação SEMASA, DC-04 Vitalmar Pescados, junto ao estuário). Dois canais
> paralelos: "quem vem antes de quem" só a coordenada resolve.

## 🎁 Achado colateral: 45 abrigos oficiais COM coordenada (público, sem token)

`Hosted/Abrigos_Defesa_Civil_view_completo` (FeatureServer) — público, sem token.
- 45 abrigos, **todos com lat/lon**, mais `nome_do_ab`, `endereco`, `capacida_2` (capacidade),
  `sigla_do_a` (zona de Defesa Civil, ex. Z2-2), `situacao`, `lotacao`.
- Query (usar `f=json`; `f=geojson` dá 500 neste serviço):
  `/server/rest/services/Hosted/Abrigos_Defesa_Civil_view_completo/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json`

**Por que importa:** Blumenau já mostra o abrigo mais próximo junto da cota de rua (do PDF de 2014).
Itajaí não tinha — com coordenada, dá "abrigo mais próximo de você" por distância real, não por bairro.
Encaixa no Bloco 4 da tela de Itajaí.

**Ressalva (regra do AVISO-LEGAL):** a lista traz `situacao`/`lotacao`, mas é **cadastro, não estado
atual**. NÃO exibir como "aberto agora" — quem ativa abrigo é a Defesa Civil.

### Para entrar no repo (precisa do arquivo bruto)
O JSON dos abrigos foi baixado na sessão de navegador (`itajai-abrigos-defesa-civil.json`), mas **ainda
não está no repositório**. Passos quando o arquivo estiver disponível (subir aqui ou mover na VPS):
1. `data/brutos/itajai-abrigos-defesa-civil.json` (bruto) → `data/abrigos-itajai.json` (normalizado).
2. Tela de Itajaí, seção "Meu ponto": os 3 abrigos mais próximos (distância em linha reta), com endereço
   e capacidade, e o aviso de que a ativação é decisão da Defesa Civil.

---

## Coordenadas das estações ESTADUAIS (DCSC) — encontradas e ADOTADAS (02/09/2026)

Fonte: **GraphQL da Defesa Civil de SC** (`monitoramento.defesacivil.sc.gov.br/graphql`), campo
`position { latitude longitude }` da própria query `Tags_data` do app (o servidor tem allowlist de
queries — é preciso usar a query exata do bundle). **61 estações da bacia, todas com coordenada.**
Bruto em `data/brutos/dcsc-estacoes-coordenadas-bacia-itajai.json`.

**Atenção — o que isto NÃO é:** são as estações **estaduais da cadeia** (Taió, Rio do Sul, …, Brusque),
**não** as 11 réguas DC municipais de Itajaí. A ordenação do Mirim pelas DC de Itajaí **segue bloqueada**
(seção acima). Estas coordenadas servem para a cadeia, não para a foz.

### Adotadas em `data/estacoes.json`
As 13 cidades da cadeia passaram a usar a coordenada da **estação** (posição da régua no rio), no lugar
da sede municipal aproximada. É melhor para o marcador e para projetar no traçado. Movimentos maiores:
Ituporanga ~7,9 km, Blumenau ~6,9 km, Botuverá ~5,0 km, Indaial ~4,1 km (a sede ficava longe da régua).
Exceções mantidas: **Vidal Ramos** (já era a estação Asthon) e **Itajaí** (foz, sem estação estadual).
A convenção no `_meta` do `estacoes.json` foi atualizada para refletir a nova origem.

### 🎯 Confirma por coordenada: nossa Vidal Ramos = estação Asthon = DCSC
**DCSC-00024 = -27.38548, -49.35813** contra a Asthon **-27.38547, -49.35812** → **~4 m**. É a MESMA
estação, confirmado por coordenada (não por nome). **Ressalva:** isto confirma a identidade da NOSSA
régua; se a "Salseiro" 83892990 da EPAGRI é essa mesma estação continua dependendo da coordenada da
EPAGRI (ofício C9) — a pendência EPAGRI/Salseiro do README segue aberta por esse lado.

### O que estas coordenadas destravam (cadeia, não Itajaí)
- Vínculo estação↔cidade por coordenada (regra do projeto).
- Ordenar a cadeia do Açu e do Mirim pela descida real (projetando no traçado) — quando houver o script.
- Distância entre estações como insumo para calibrar tempo de trânsito com base física.

---

## Ordem de descida das réguas DC (T2/T3, 02/09/2026) — `scripts/ordenar_estacoes_itajai.py`

**Como, e por que não pela projeção no traçado:** o traçado (`data/rios/*.geojson`) é um
MultiLineString de **segmentos soltos do OSM** (57 no Mirim), sem ordem nem conectividade — não dá
"distância ao longo do curso" sem montar um grafo, e o Mirim tem dois braços. Pior, o **canal
retificado e os ribeirões não estão no traçado** (mediado: DC-03/SEMASA a 2,3 km, ribeirões a
0,9–4,4 km). Então a ordem é pela **distância à foz** (reta), robusta e verificável; a projeção entra
só como *checagem de qualidade* (afastamento > 500 m = braço/ribeirão fora do desenho).

**Ordem gravada (`ordem_descida` em `estacoes_tempo_real`, montante → foz):**
- **Itajaí-Açu:** DC-11 Santa Regina (12,2 km) → DC-02 Praça (7,6) → DC-01 CEPSUL (1,0).
- **Itajaí-Mirim:** DC-10 Limoeiro (26,0) → DC-05 Sítio (10,9) → DC-03 SEMASA (7,7, *canal, fora do
  traçado*) → **DC-04 Vitalmar ≡ DC-06 Itamirim (4,8, EMPATE)**.
- **Ribeirão da Murta:** DC-07 Portal (9,4) → DC-09 (6,5). **Ribeirão Canhanduba:** DC-08 (10,7).

**T3 — o empate NÃO se resolve:** DC-04 e DC-06 estão à mesma distância da foz (~4,8 km) e projetam no
**mesmo ponto** do traçado (offset 55 m as duas). São co-locadas — não há "qual vem antes". Recebem a
MESMA `ordem_descida` e uma `ordem_nota` de braços paralelos. **Nunca forçar sequência entre elas.**
Para a UI (T5): o canal retificado (DC-03) e os ribeirões não estão no traçado; DC-04/DC-06 são um par
lado a lado — mostrar como tal, não em fila.

## Estrutura em dois braços do Mirim (documento de rota, 02/09/2026)

O Jefferson mandou um documento de rota hidrológica confirmando o que os próprios **títulos das
réguas** já dizem: em Itajaí o Mirim **se divide em dois braços paralelos** depois de DC-10 (Limoeiro),
que se **reencontram** perto da foz:

- **Curso antigo (meandros):** DC-05 (Sítio Hilário) → DC-06 (Clube Itamirim).
- **Canal retificado:** DC-03 (Captação SEMASA) → DC-04 (Vitalmar, na junção dos dois braços).
- DC-06 e DC-04 ficam no **mesmo ponto** de reencontro (~4,8 km da foz) — daí o empate do T3.

A tela do Mirim passou a mostrar essa estrutura (curso antigo e canal como braços paralelos, não uma
fila intercalada). O rótulo do braço vem do título de cada régua (`(curso antigo)` / `(canal
retificado)`), **não** das coordenadas — que continuam em disputa (abaixo).

### ⚠ PENDÊNCIA — coordenadas do documento divergem dos marcadores do Mapa.php

O documento traz coordenadas próprias, **marcadas como "Aprox."** (3 casas), que **divergem** dos
marcadores oficiais do Mapa.php (5 casas, adotados no `estacoes.json`) — de 0,9 km (DC-06) até **8,9 km
(DC-10)** e 5,9 km (DC-05). Além disso o documento é **internamente inconsistente**: o diagrama põe
DC-04 a montante de DC-03, mas as coordenadas dele mesmo põem DC-03 mais longe da foz (o Mapa.php
concorda com esta segunda leitura — DC-03/SEMASA a montante da cunha salina, DC-04/Vitalmar na junção).

**Decisão (Jefferson, 02/09/2026): "não sei qual está certa" → manter os marcadores do Mapa.php** (fonte
verificada, precisa, coerente com a ordem física) e **não sobrescrever** com as do documento. A
divergência fica registrada aqui até dar para conferir em campo (GPS nos 11 pontos) ou em fonte oficial
(ofício C2 / GEOItajaí). Isto **não bloqueia** a estrutura em braços (que vem do título), só o futuro
**marcador de cada régua no mapa**, que depende da coordenada exata.

Coordenadas do documento (para conferência futura, NÃO adotadas):
DC-10 `-27.055, -48.775` · DC-05 `-26.924, -48.689` · DC-06 `-26.917, -48.683` ·
DC-04 `-26.908, -48.688` · DC-03 `-26.899, -48.694`.
