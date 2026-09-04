# Cotas de referência ausentes no monitor do Vale do Itajaí

**Fonte do monitor:** [Enchentes do Vale do Itajaí — Monitor](https://haohmarusc-glitch.github.io/enchentes-vale-itajai/#/monitor)  
**Cadastro consultado:** [`data/estacoes.json`](https://github.com/haohmarusc-glitch/enchentes-vale-itajai/blob/main/data/estacoes.json)  
**Consulta às Defesas Civis:** 3 de setembro de 2026  
**Emergência:** 199 (Defesa Civil) ou 193 (Bombeiros). Este levantamento **não** substitui aviso oficial.

No mapa, círculo **cinza** = *sem cota / sem leitura*. Leituras com o sufixo **bruto** são nível bruto da estação estadual, sem faixa oficial de atenção/alerta/inundação cadastrada no site.

---

## Resumo

| Cidade | Rio / ramo | No cadastro do monitor | O que a Defesa Civil municipal publica | Status |
|---|---|---|---|---|
| Taió | Itajaí do Oeste | `cotas_m: {}` | Plano de Contingência jan/2026: 5 / 7 / 8 / 9 m | **Encontrada** |
| Ituporanga | Itajaí do Sul | `cotas_m: {}` | Mapa oficial “Cotas com Manchas” (Prefeitura): manchas a 3,00 / 3,50 / 4,00 / 4,50 / 5,00 m + cotas de rua no Plano de Assistência 2025 | **Encontrada (manchas + ruas)** |
| Ibirama | Hercílio / Itajaí do Norte | `cotas_m: {}` | Plano homologado 2024: 3,00 / 3,50 / 4,00 m | **Encontrada** |
| Ascurra | Tronco do Açu | `cotas_m: {}` | Prefeitura, maio/2026, Ponte do Beber: 8,50 / 9,76 / 10,76 m | **Encontrada** |
| Indaial | Tronco do Açu | `cotas_m: {}` | Página oficial: alagamento já registrado a **6,00 m** em 12 vias | **Encontrada (limiar de rua)** |
| Ilhota | Tronco do Açu (foz) | `cotas_m: {}` | Plano 2025/2028, régua da ponte: 9,20 / 10,00 / 10,50 m | **Encontrada** |
| Vidal Ramos | Itajaí-Mirim | `cotas_m: {}` | COMPDEC/imprensa: transborda acima de ~3 m (3,0–3,8 m observados) | **Observada (não homologada)** |
| Botuverá | Itajaí-Mirim | `cotas_m: {}` | Transbordo ~7,50 m (prefeitura/imprensa 2015); Carta estadual sem PDF | **Observada (não homologada)** |
| Guabiruba | Itajaí-Mirim | `cotas_m: {}` | Carta estadual sem PDF; risco típico é enxurrada | **Não encontrada** |

Cidades **já cadastradas** no monitor (não entram nesta lista de lacuna): Rio do Sul (4,50 / 5,50 / 6,50), Blumenau (6,00 / 6,50 / 7,40), Gaspar (5,00 / 6,00 / 7,00), Brusque (atenção 4,80 / inundação 6,00, ainda incompleta) e as 11 réguas DC de Itajaí.

### Lote 2 — conferência de portais (03/09/2026)

| Cidade | Rio | Ficha | Resultado |
|---|---|---|---|
| Lontras | Açu | `lontras.md` | Cota de segurança **9,20 m** (2022); sem API |
| Apiúna | Açu | `apiuna.md` | Sem faixa; pico 6,50 m em 2022; Carta estadual pendente |
| Rodeio | ribeirões | `rodeio.md` | Sem cota; estação nova anunciada |
| Pomerode | Testo | `pomerode.md` | PLANCOM 2025 sem número; normal ~0,70 / alerta ~4,56 observado |
| Brusque | Mirim | `brusque.md` | Portal + mapas; 4,75–4,80 / 6,00 / 8,96 (2023) |
| Gaspar | Açu | `gaspar.md` | Portal + app; 5,00 / 6,00 / 7,00 + carta CEOPS |

### Lote 3 — conferência de portais (03/09/2026)

| Cidade | Rio | Ficha | Resultado |
|---|---|---|---|
| Blumenau | Açu | `blumenau.md` | AlertaBlu; 6,00 / 6,50 / 7,40 (hist. 8,50) |
| Itajaí | foz | `itajai.md` | PLANCON v17 Tabela 11 — 11 réguas |
| Timbó | Benedito | `timbo.md` | PLANCON ativa em 5,00 m; GEO Timbó |
| Rio dos Cedros | Rio dos Cedros | `rio-dos-cedros.md` | 4,80 / 5,30 / 5,70; praça 6,02 m |
| Presidente Nereu | alto Vale | `presidente-nereu.md` | COMPDEC 2025; sem faixa |

### Lote 4 — conferência de portais (03/09/2026)

| Cidade | Rio | Ficha | Resultado |
|---|---|---|---|
| José Boiteux | Hercílio / barragem Norte | `jose-boiteux.md` | Sem cota urbana; card de barragem |
| Benedito Novo | Benedito | `benedito-novo.md` | Sem faixa; enxurrada |
| Doutor Pedrinho | Benedito / Forcação | `doutor-pedrinho.md` | Carta estadual sem PDF |
| Massaranduba | Itapocu | `massaranduba.md` | Fora do tronco; sem cota |
| Luiz Alves | rio Luiz Alves | `luiz-alves.md` | Sem faixa; 180 mm/24 h nov/2025 |

### Lote 5 — conferência de portais (03/09/2026)

| Cidade | Rio | Ficha | Resultado |
|---|---|---|---|
| Aurora | Itajaí do Sul | `aurora.md` | Sem faixa; 2 km de desassoreamento |
| Agrolândia | Trombudo | `agrolandia.md` | Sem faixa |
| Pouso Redondo | cabeceira / Pombas | `pouso-redondo.md` | Alerta 6 h; sem metros |
| Presidente Getúlio | Krauel / Índios | `presidente-getulio.md` | Sem faixa; 8 cheias em 2023 |
| Vitor Meireles | Dollmann + reservatório | `vitor-meireles.md` | Sem faixa; isolado pela barragem Norte |

### Lote 6 — conferência de portais (03/09/2026)

| Cidade | Rio | Ficha | Resultado |
|---|---|---|---|
| Trombudo Central | Trombudo | `trombudo-central.md` | Pico **8,71 m** (2023); sem faixa |
| Agronômica | Trombudo | `agronomica.md` | Abrigo 15,10 m ≠ régua |
| Laurentino | Itajaí do Oeste | `laurentino.md` | Sem faixa; aponta DC-SC |
| Rio do Oeste | Oeste + Pombas | `rio-do-oeste.md` | Sem faixa; 7,8 km de obra |
| Mirim Doce | Rio Taió / barragem | `mirim-doce.md` | 4ª barragem (R$ 110 mi); sem cota urbana |

### Lote 7 — conferência de portais (03/09/2026)

| Cidade | Rio | Ficha | Resultado |
|---|---|---|---|
| Braço do Trombudo | Trombudo | `braco-do-trombudo.md` | Fundo DC 2025; sem faixa |
| Atalanta | cabeceira | `atalanta.md` | Sem faixa |
| Imbuia | Itajaí do Sul | `imbuia.md` | SE granizo; sem faixa |
| Petrolândia | barragem projeto | `petrolandia.md` | 3,54 hm³ previstos; sem cota urbana |
| Chapadão do Lageado | — | `chapadao-do-lageado.md` | 1 setor CPRM; SE granizo |

---

## Mapas de mancha / carta de enchente (busca 03/09/2026)

Procura no Google My Maps e nos sites das Defesas Civis por camadas do tipo “COTA — X,XX m” (o formato de Ituporanga). **Não há outro mapa municipal nesse mesmo molde** no Vale. O que existe:

| Cidade | Mancha por cota? | Onde | Tipo |
|---|---|---|---|
| **Ituporanga** | Sim | [My Maps da Prefeitura](https://goo.gl/maps/MuMjQF1hENuKi7E2A?g_st=ac) | Camadas 3,00 / 3,50 / 4,00 / 4,50 / 5,00 m |
| **Brusque** | Sim | [Cotas de ruas](https://defesacivil.brusque.sc.gov.br/mapas/cotas-de-ruas) e cartas 7–15 m no Plano | Pontos de rua (2011 laranja + 2023 azul até 8,96 m) + manchas simuladas 7 a 15 m |
| **Gaspar** | Sim | [defesacivil.gaspar.sc.gov.br](https://defesacivil.gaspar.sc.gov.br/) — “Ver mancha de cheias” / Carta Enchente CEOPS | Mancha + busca de cota por endereço (1.619 pontos já no repo) |
| **Blumenau** | Sim | [AlertaBlu](https://alertablu.blumenau.sc.gov.br/) (site/app) | Mancha interativa por nível + cotas de rua (2.042 pontos no repo). Novo mapa FURB em campo (até 16 m) |
| **Rio do Sul** | Parcial | [My Maps de pesquisa](https://www.google.com/maps/d/viewer?mid=1BFoe-q2LJHLd66R0MpianejE30_XYkdo) + tabela oficial no site da DC | O My Maps **não é** da COMPDEC (projeto de pesquisa). Cotas de rua oficiais: 555 pontos no repo |
| **Itajaí** | Mancha histórica, sem cota de rua | [GeoItajaí / SIE](https://geoitajai.github.io/sie/dcitajai.html) | Manchas de eventos 1983–2015. Cota por endereço no ArcGIS **fechada por token** |
| **Ibirama** | Áreas de risco, **sem cota em metro** | [ÁREAS DE RISCO — IBIRAMA](https://goo.gl/maps/dfcXKigjxcDj9WDS7?g_st=ac) (José Eduardo do Rosário / COMPDEC, 49 polígonos) | 10 polígonos de inundação/alagamento/solapamento; o resto é encosta. Ver `ibirama.md` |
| Taió, Ascurra, Indaial, Ilhota | Não | — | Só faixa da régua no plano; sem polígono público por cota |
| Vidal Ramos, Botuverá, Guabiruba | Não | Estado anunciou cartas de Botuverá e Guabiruba (nov/2025), ainda sem publicação | Sem My Maps, sem KML |

Conclusão: o formato “camada COTA — X m no Google My Maps” hoje é **só Ituporanga**. As outras cidades com mancha usam site próprio (Brusque, Gaspar, Blumenau) ou camada histórica (Itajaí).

---

## 1. Taió — Itajaí do Oeste

**Estação no cadastro:** DCSC-00041 · ANA 83050000  
**Site municipal:** [defesacivil.taio.sc.gov.br](https://defesacivil.taio.sc.gov.br/)  
**Documento:** [Plano de Contingência — janeiro de 2026 (PDF)](https://defesacivil.taio.sc.gov.br/wp-content/uploads/2026/01/PLANO-DE-CONTINGENCIA-TAIO-JAN-2026.pdf)

Faixas oficiais da **cota do Rio do Oeste** (régua de cidade, não a da Barragem Oeste):

| Fase | Critério no plano |
|---|---|
| Normal (verde) | ≤ 5,00 m |
| Observação / monitoramento (amarelo) | > 5,00 m e ≤ 7,00 m |
| Atenção (laranja) | > 7,00 m e ≤ 8,00 m |
| Alerta (vermelho) | > 8,00 m e ≤ 9,00 m |
| Emergência (roxo) | > 9,00 m |

**Sugestão para `estacoes.json`:**

```json
"cotas_m": {
  "normal_ate": 5.0,
  "observacao": 5.0,
  "atencao": 7.0,
  "alerta": 8.0,
  "emergencia": 9.0
}
```

**Atenção:** o site municipal tem campos “Cota de Alagamento” e “Cota de Atenção”, mas na consulta estavam **em branco**. A Barragem Oeste (capacidade ~100,6 hm³, 7 comportas, emergência de reservatório 23,30 m no painel de Rio do Sul) **não** é a mesma régua da cidade. O monitor mostra ~5,21 m bruto.

---

## 2. Ituporanga — Itajaí do Sul

**Estação no cadastro:** DCSC-00039  
**Mapa oficial:** [Cotas com Manchas de Inundação — Prefeitura de Ituporanga SC](https://goo.gl/maps/MuMjQF1hENuKi7E2A?g_st=ac) (Google My Maps, publicado 29/07, 4.684 visualizações)

O município **não nomeia** as faixas como atenção/alerta/emergência no mapa. Publica **manchas de inundação por cota da régua**, de 50 em 50 cm:

| Camada no My Maps | O que representa |
|---|---|
| COTA — 3,00 | Primeira mancha (início da ocupação de várzea / ruas mais baixas) |
| COTA — 3,50 | Segunda mancha |
| COTA — 4,00 | Terceira mancha |
| COTA — 4,50 | Quarta mancha |
| COTA — 5,00 | Quinta mancha (há mais camadas abaixo da dobra da lista) |

Cada camada contém polígonos (`MPOLYGON`) da área alagada naquela cota.

**Cotas de rua** no Plano Municipal de Assistência Social 2025 (tabela “Nome das Ruas e suas Esquinas / Bairro / Cota metros”) batem com o mapa — as primeiras vias do Centro e Vila Nova alagam já na casa dos **3,3–3,5 m**:

| Esquina / via | Bairro | Cota (m) |
|---|---|---|
| João Carlos Thiesen / Gov. Jorge Lacerda | Centro | 3,37 |
| João Back / Galpão Chapeação | Vila Nova | 3,38 |
| Balduino Sens / Aderbal Ramos da Silva | Centro | 3,47 |
| Balduino Sens / Presidente Nereu | Centro | 3,50 |
| Major Generoso / Ten. Jacob Philippi | Centro | 4,00 |
| Emílio Altenburg / Presidente Nereu | Centro | 4,50 |
| Guilherme Meurer / Vitório Sens | Gruta | 4,90 |
| 7 de Setembro / Presidente Nereu | Centro | 4,90 |

**Leitura sugerida para o monitor** (inferida das manchas + primeira rua; a Prefeitura **não** escreveu “atenção/alerta” nestes números):

```json
"cotas_m": {
  "primeira_mancha": 3.0,
  "atencao": 3.0,
  "alerta": 3.5,
  "inundacao": 4.0
}
```

Marcar `verificado: false` até a COMPDEC confirmar o nome das faixas. O monitor mostra ~3,81 m bruto — já dentro da terceira mancha (4,00 m) se a régua estadual for a mesma do mapa municipal.

**Não confundir** com a Barragem Sul (emergência de reservatório 31,00 m no painel de Rio do Sul). Boletim estadual de agosto/2026 que falou em “emergência entre 2,5 e 3,0 m” é previsão de evento, não a tabela permanente — e fica **abaixo** da primeira mancha do mapa da Prefeitura.

---

## 3. Ibirama — Rio Hercílio (Itajaí do Norte)

**Estação no cadastro:** DCSC-00020  
**Site:** [defesacivilibirama.com.br](https://www.defesacivilibirama.com.br/)  
**Documento:** Decreto nº 5.431/2024, que homologa o Plano Municipal de Contingência  
([PDF no DOM/SC](https://s3cache.dom.sc.gov.br/atos/2024/08/1724680743_decreto_n_5.431__homologa_o_plano_municipal_de_contingncia.pdf))

Faixas oficiais do **Rio Itajaí do Norte**:

| Fase | Cota |
|---|---|
| Observação | 3,00 m |
| Atenção | 3,50 m |
| Emergência | 4,00 m |

Cotas aproximadas de rua no mesmo plano:

- Rua Blumenau, BR-470 (Padre Anchieta), Rua Marechal Rondon — ~**4,00 m**
- Rua Dr. Getúlio Vargas, Rua 11 de Março — ~**6,00 m**

Informativos da COMPDEC em 2025 já classificam 1,50 m como “normalidade”, coerente com a tabela.

**Sugestão para `estacoes.json`:**

```json
"cotas_m": {
  "observacao": 3.0,
  "atencao": 3.5,
  "emergencia": 4.0
}
```

**Mapa de risco (não é mancha por cota):** [ÁREAS DE RISCO — IBIRAMA](https://goo.gl/maps/dfcXKigjxcDj9WDS7?g_st=ac) — 49 polígonos (19 muito alto / 26 alto / 4 médio). Só ~10 são inundação, alagamento ou solapamento. Detalhe e KML em `ibirama.md`.

Ibirama **não** é elo da fila do Açu: a cheia entra no tronco perto de Rio do Sul.

---

## 4. Ascurra — tronco do Itajaí-Açu

**Estação no cadastro:** DCSC-00003  
**Fonte oficial:** Prefeitura de Ascurra / Defesa Civil Municipal, 22 de maio de 2026  
([Instagram @prefeituraascurra](https://www.instagram.com/p/DYpKHbxgGsq/))

Níveis de criticidade na **Ponte do Beber**:

| Fase | Faixa |
|---|---|
| Monitoramento | até 8,50 m |
| Atenção | 8,50 m a 9,76 m |
| Alerta | 9,76 m a 10,76 m |
| Emergência | acima de 10,76 m |

Ao atingir **9,76 m**, o primeiro ponto de interdição é a **Travessa Zonta**.

**Sugestão para `estacoes.json`:**

```json
"cotas_m": {
  "monitoramento_ate": 8.5,
  "atencao": 8.5,
  "alerta": 9.76,
  "emergencia": 10.76
}
```

**Ressalva:** o monitor mostra ~7,95 m **bruto**. As faixas de Ascurra estão numa escala alta (8,5–10,8 m). Antes de pintar faixa no mapa, conferir se a régua da Ponte do Beber é a **mesma** DCSC-00003. Se não for, cadastrar as cotas só na régua municipal e deixar a estadual sem faixa.

---

## 5. Indaial — tronco do Itajaí-Açu

**Estação no cadastro:** DCSC-00006  
**Página oficial:** [Cotas de enchente](https://indaial.atende.net/subportal/defesa-civil-indaial/pagina/cotas-de-enchente)  
**Ficha:** `indaial.md`

A COMPDEC **não** publica atenção/alerta/emergência. Publica o limiar de rua:

> Com **6 m** do nível do Rio Itajaí-Açu já se tem registro de alagamentos nas ruas: Sete de Setembro, Av. Carlos Schroeder, Melvin Jones, Bagé, Beco 2 de Julho, Beco Itapuã, Pres. Nereu, Mariana, 3 Corações, ID 24, 24 de Outubro, Brusque.

PDF na aba Arquivos: “Indaial - cotas de enchente” (picos máximos das cheias). Picos clássicos fora da página: 7,78 m (1983) e 8,04 m (1984).

```json
"cotas_m": {
  "primeira_inundacao": 6.0
}
```

---

## 6. Ilhota — tronco do Açu, próximo à foz

**Estação no cadastro:** DCSC-00030  
**Documento:** [Plano de Contingência 2025/2028, versão 016 (PDF)](https://ilhota.sc.gov.br/wp-content/uploads/2025/08/Plano_de_Contingencia_Defesa_Civil_Ilhota.pdf)

Régua municipal na **Ponte Cláudio Jeremias Cadorin**:

| Faixa na régua | Situação no plano |
|---|---|
| 0 a 9,20 m | Rio na calha — normal |
| 9,20 a 10,00 m | Represamento dos ribeirões — atenção (monitoramento constante, sem aviso à população) |
| 10,00 a 10,50 m | Água nas várzeas — prontidão |
| acima de 10,50 m | Sinal oficial de emergência; alagamentos nas partes mais baixas |

O PDF traz um trecho “mais de 10,50 centímetros”; no contexto da tabela (metros) trata-se de **10,50 m**.

**Sugestão para `estacoes.json`:**

```json
"cotas_m": {
  "normal_ate": 9.2,
  "atencao": 9.2,
  "prontidao": 10.0,
  "emergencia": 10.5
}
```

Cotas de **rua** no mesmo plano são **altitude em relação ao nível do mar** (a partir de 12,00 m na régua municipal de altitude), **não** o zero da régua do rio. Não misturar as duas escalas.

O monitor mostra ~9,44 m bruto — já na faixa de atenção do plano, se a régua estadual for a mesma da ponte.

---

## 7. Vidal Ramos — cabeceira do Itajaí-Mirim

**Ficha:** `vidal-ramos.md`  
Nível ao vivo: Asthon / DC-SC + [CIRAM Rios on-line](https://ciram.epagri.sc.gov.br/rios-online/). Sem PLANCON com faixas. COMPDEC (via imprensa, 2015): transborda **acima de 3 m** (~3,50 m no levantamento). Eventos recentes: 3,00–3,80 m = atenção / calha. Av. Jorge Lacerda e centro. Jusante: Botuverá (5–6 h), Brusque (~12 h).

```json
"cotas_m": { "atencao_observada": 3.0, "transbordo_observado": 3.8 }
```

`verificado: false` até a COMPDEC homologar. Pendência do repo (ofício C5 / EPAGRI-CIRAM) segue.

---

## 8. Botuverá — Itajaí-Mirim

Sem régua com faixas publicadas. O Governo do Estado anunciou em novembro/2025 a elaboração das **Cartas de Enchentes** de Botuverá (junto com Apiúna, Doutor Pedrinho e Guabiruba), R$ 412 mil. Até a carta sair, não há cota oficial de rua nem de régua.

Há edital da futura Barragem de Botuverá (Rio Itajaí-Mirim); isso não cria faixa da cidade.

---

## 9. Guabiruba — Itajaí-Mirim

Mesma situação de Botuverá: carta de enchentes estadual em elaboração, sem tabela municipal de cotas da régua.

---

## Já cadastradas, mas com ressalva

### Brusque (Itajaí-Mirim)

No cadastro: atenção **4,80 m** e inundação **6,00 m**. A Defesa Civil de Brusque não publica atenção/alerta oficiais da Ponte Estaiada; 4,80 m é a cota em que a Av. Beira-Rio começa a alagar. Ponto da Av. Beira Rio × Maria Scarpa Formonti (Limoeiro) alaga a **3,76 m**. Ofício C1 enviado em 31/08/2026.

Site útil: monitoramento republicado em [defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios](https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios) (aba Brusque).

### Gaspar

Faixas do Plano de Contingência (5 / 6 / 7 m) já estão no JSON. Falta nível ao vivo da régua municipal (DCSC-00005 entrega chuva). Ofício C4 pendente.

### Itajaí (foz)

A cidade no JSON está com `cotas_m: {}` porque as faixas são **por régua**, não por município. As 11 estações DC-01 a DC-11 têm cotas oficiais da Tabela 11 do Plano de Contingência da COMPDEC, v. 17 (22/12/2025):

| Régua | Atenção | Alerta | Emergência |
|---|---|---|---|
| DC-01 ICMBio/CEPSUL | 1,16 | 1,36 | 1,56 |
| DC-02 Praça Celso Pereira | 1,60 | 2,00 | 2,50 |
| DC-03 Captação SEMASA | 1,48 | 1,85 | 2,50 |
| DC-04 Vitalmar | 1,50 | 1,85 | 2,25 |
| DC-05 Propriedade privada | 1,60 | 2,20 | 3,00 |
| DC-06 Itamirim | 1,50 | 1,85 | 2,55 |
| DC-07 Murta Portal | 1,00 | 1,35 | 1,65 |
| DC-08 Canhanduba | 1,80 | 2,30 | 2,89 |
| DC-09 Murta Lidia Puel | 1,12 | 1,32 | 1,52 |
| DC-10 Limoeiro | 8,00 | 9,00 | 10,00 |
| DC-11 Santa Regina | 3,00 | 4,00 | 5,00 |

PDF: [Plano de Contingência de Inundação — alterado em 22/12/2025](https://defesacivil.itajai.sc.gov.br/wp-content/uploads/2025/12/Plano-de-Contingencia-de-Inundacao-ALTERADO-EM-22-12-25.pdf)

DC-10 (8 / 9 / 10 m) continua destoando do nível calmo (~4 m) e das outras réguas do Mirim. Conferência pendente na COMPDEC de Itajaí.

---

## Fontes gerais usadas

- Monitor: https://haohmarusc-glitch.github.io/enchentes-vale-itajai/#/monitor
- Cadastro: https://github.com/haohmarusc-glitch/enchentes-vale-itajai
- Defesa Civil SC (mapa): https://monitoramento.defesacivil.sc.gov.br/mapa
- Defesa Civil Taió: https://defesacivil.taio.sc.gov.br/
- Defesa Civil Ibirama: https://www.defesacivilibirama.com.br/
- Prefeitura de Ilhota — plano 2025/2028
- Prefeitura de Ascurra — níveis da Ponte do Beber (maio/2026)
- Defesa Civil Itajaí — níveis e plano v.17
- Portal Rio do Sul (barragens Taió / Ituporanga): https://defesacivil.riodosul.sc.gov.br/
- Pendências já abertas no repo: `docs/pendencias-navegador-e-oficios.md` (ofícios C1 Brusque, C2 Itajaí ruas, C4 Gaspar, C5 EPAGRI)

---

## Próximos passos sugeridos (para o cadastro)

1. Incorporar as faixas de **Taió**, **Ibirama**, **Ilhota** — documentos municipais nominais, com `verificado: true` e a URL do PDF.
2. Incorporar **Ascurra** só depois de cruzar Ponte do Beber × DCSC-00003.
3. Incorporar **Ituporanga** com as manchas 3,00 / 3,50 / 4,00 m (`verificado: false` até a COMPDEC nomear as faixas). Manter cinza **Indaial, Vidal Ramos, Botuverá, Guabiruba**.
4. Não usar cota de barragem (Taió 23,30 m / Ituporanga 31,00 m) como cota de cidade.
5. Em Ilhota, não misturar cota da régua do rio (9,20–10,50 m) com cota de rua em altitude (12 m+).
