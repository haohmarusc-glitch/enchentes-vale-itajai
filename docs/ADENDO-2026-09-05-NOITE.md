# Adendo 05/09 noite — réguas da foz, par MKS/Tito, home vs árvore

Adendo de Jefferson à auditoria, recebido em 06/09/2026. Cada item abaixo traz **o que eu conferi**
contra o repositório — porque adendo repetido sem medir vira folclore, e três dos nove já estavam
resolvidos.

**O resultado da auditoria não muda:** publicação viva, travas úteis, dados não integralmente coerentes.

---

## A1 · Itajaí: zero picos, dez manchas, onze réguas ✅ confirmado, e é o bloqueio

`enchentes.json` não tem `cidade: itajai`. As dez manchas estão com `pico_registrado: null`.
**Conferido também o que não estava dito:** minerei os brutos de Itajaí (`itajai-arcgis-inundacoes`,
`itajai-pontos-cotados-altimetricos`, `itajai-terreno-sujeito-inundacao`) e os dez geojson de mancha —
**as feições das manchas não têm propriedade nenhuma**, nem de nível. Não há pico de Itajaí em lugar
algum do repositório.

**A regra que fica:** índice só depois de **pico E `codigo_regua` na mesma linha**. E não se copia
15,34 / 12,80 / 11,52 de Blumenau — são de outra régua, de outra cidade.

O mecanismo `manchasPorNivel` está pronto e **apagado** (PR #184), com teste que trava o próprio
bloqueio: ele afirma que hoje nenhuma mancha tem pico. No dia em que os picos entrarem, o teste cai.

### A busca externa foi feita (06/09/2026) — e o resultado é NEGATIVO

Jefferson procurou. **Tudo que circula com metro nessas datas é régua de BLUMENAU** (ou vazão do JICA,
sem cota da foz):

| evento da mancha | número que circula | régua real | entra? |
|---|---|---|---|
| 1983-07 | 15,34 m | Blumenau | não — o JICA lista Itajaí com 40 mil atingidos e **célula de nível vazia** |
| 1984-08 | 15,46 m | Blumenau | não |
| 2001 | 11,02 m | Blumenau | não |
| 2008-11 | 11,52 / 11,72 m | Blumenau (JICA: 11,5 m na régua) | não — "o rio subiu 11,52 m" cita Blumenau. Porto destruído é fato, **sem metro da barra** |
| 2011-09 | 12,60 / 12,80 / 13,00 m | Adolfo Konder / CEOPS | não — a tese Fachi (UFRJ) usa a mancha da DC de Itajaí e hidrograma do HidroWeb de **Indaial/Blumenau** |
| 2013-07 / 09 | 10,51 m (set) | Blumenau | não — julho/2013 na foz nem tem data fechada |
| 2014-06 | 10,18 m | Blumenau | não |
| 2015-10 | 10,03 m | Blumenau | não |

**Três fatos que fecham a questão:**

1. **A "Itajaipedia" copia a série de Blumenau.** Não é fonte da foz, apesar do nome.
2. **A estação ANA 02648008, em Itajaí, é PLUVIOMÉTRICA** — mede chuva, não nível de rio.
3. **Não há código fluviométrico da barra de Itajaí no cadastro.** Os que o projeto mapeou são
   83300200 (Rio do Sul), 83800002 (Blumenau), 83900000 (Brusque), 83250000 (Ituporanga),
   83880000 (Luiz Alves) — nenhum na foz.

**Conclusão, e é diferente de "ainda não procuramos":** o pico de Itajaí por evento **pode não existir
publicado**. Quem tem o número, se alguém tem, é a **Defesa Civil de Itajaí** — que opera as onze
réguas e publicou as manchas. É pergunta de ofício, não de busca.

**A armadilha que esta busca revelou, e que virou trava:** os números de Blumenau estão a um
copiar-e-colar de distância, com o nome do evento certo ao lado. Gravar 15,34 m como pico de Itajaí
seria aplicar a régua de uma cidade a 70 km rio acima. `valida_pico_copiado_de_outra_cidade` agora
**recusa** um registro de Itajaí cujo nível seja igual ao de outra cidade no mesmo evento.

### O que é FATO, sem metro

- As dez manchas existem e são da **prefeitura (GeoItajaí)**.
- **2008 e 2011 alagaram Itajaí** — porto destruído; **1.647 pessoas em abrigo** em 2011.
- No hidrograma do JICA, **o pico na foz cai no dia seguinte ao de Rio do Sul**. Serve para amarrar
  **data**, não altura.

### ⛔ A segunda armadilha: DC-01…11 não são a série 1983–2015

As onze réguas de hoje **não são** as que mediram aqueles eventos. **Indexar uma mancha de 2011 na DC-11
atual, sem prova de mesmo zero, é outro erro** — e mais sutil que o primeiro, porque o número teria
vindo de Itajaí mesmo.

Por isso `manchasPorNivel` exige `reguaDoPico === reguaDaLeitura` e **recusa pico sem régua declarada**:
o pico tem de trazer o nome da régua **da época**, e a comparação só acontece se for a mesma régua que
o site lê hoje. Um pico de 2011 na "régua do porto" não se compara com a leitura da DC-11.

### O ArcGIS de Itajaí também NÃO tem cota — conferido em 06/09/2026

O visualizador `arcgis.itajai.sc.gov.br/portal/apps/webappviewer` consome o
`server/rest/services/historico_inundacoes/FeatureServer`, cujo bruto **já está no repositório**
(`data/brutos/itajai-arcgis-inundacoes.geojson.json`, 10 camadas, 357 feições). Atributos de todas as
camadas, lidos um a um:

| camada | atributos |
|---|---|
| 1983 | `objectid`, `...area`, `hectares`, `Shape__Area`, `Shape__Length` |
| outras de área total | `objectid`, `sum_area`, `sum_hectar`, `Shape__*` |
| as de lâmina | `objectid`, `Shape__*`, **`situa`** (`"0,20"`, `"0,21 a 0,40"`, `"0,51 a 1"`) |

**Área, hectares e classe de lâmina. Nenhum campo de cota de régua.** É o mesmo conteúdo das manchas do
GeoItajaí, com outro empacotamento — o que também confirma a decisão de **não trocar uma pela outra**.

**O que ainda vale conferir nessa fonte, e é uma pergunta pequena:** se ALGUMA camada do serviço tem
campo de nível que o bruto não capturou. Responde-se abrindo, num navegador com acesso:

```
https://arcgis.itajai.sc.gov.br/server/rest/services/historico_inundacoes/FeatureServer?f=json
https://arcgis.itajai.sc.gov.br/server/rest/services/?f=json
```

O primeiro lista as camadas e **os campos de cada uma**; o segundo lista os outros serviços publicados
pela prefeitura — é onde apareceria uma série de cota, se existir. Procurar por `cota`, `nivel`,
`regua`, `metro`.

### Onde ainda dá para achar o metro (nesta ordem)

1. **HidroWeb, pelo mapa** — filtrar município Itajaí, procurar ícone de **onda** (fluviométrica, não
   pluviométrica) e baixar a cota nas datas: `1983-07-09`, `1984-08-07`, `2001-10-01`, `2008-11-24`,
   `2011-09-09`, `2013-07-*`, `2013-09-23`, `2014-06-09`, `2015-10-23`.
2. **E-mail `hidro@ana.gov.br`** — "série de cota, estação fluviométrica Itajaí-Açu / porto de Itajaí,
   sub-bacia 83".
3. **Ofício à COMPDEC de Itajaí** — as dez datas × **o nome da régua da época** (antes das DC-xx).
   Este é o único caminho que resolve as duas armadilhas de uma vez.
4. **Arquivo do porto** (superintendência / dragagem) — 2008 e 2011 às vezes têm nível no cais, **em
   outra referência**; se vier, entra com a referência declarada, nunca convertida.
5. **Livro *Desastre de 2008 no Vale do Itajaí*** (Agência da Água) — conferir se a **quinta estação**
   que o JICA não copiou é a foz.

### O que NÃO foi feito nesta sessão, de propósito

- **Nenhuma linha inserida em `enchentes.json`.**
- **`pico_registrado` do `index.json` continua `null`** nas dez.
- **12,80 m não foi usado** como "pico da mancha de set/2011 em Itajaí".

**O levantamento, por enquanto, é este:** as datas das manchas estão amarradas à cheia da bacia; **a
altura na régua de Itajaí continua `null`**. O passo que destrava é **HidroWeb + ofício**, não mais
busca na web.

## A2 · Colisão de nome DC-02 ✅ já resolvido
`logica/reguas.ts` linha 251: `const nome = e.titulo`. O nome do Plano vai em `nomeNoPlano`, como nota
de rodapé. A Murta de verdade (DC-07 / DC-09) segue no `ribeirao-murta`.

## A3 · DC-11 "sem cota" ✅ já resolvido
`proximaCotaEntre` monta a faixa a partir de `cotas_m` independentemente de `alerta_automatico`.
`alerta_automatico: null` é "Telegram não decidido", não "sem cota".

## A4 · Rio do Sul: duas réguas ⛔ **confirmado, e o achado é maior**

Confirmado: a única estação ao vivo é **"Rio do Sul Estação MKS"**, e as cotas 4,50/5,50/6,50 são da
**Ponte Dom Tito Buss** (`scripts/conferir_par_regua.py`). São réguas de nome diferente, e **isso pinta
a cor do mapa**.

**Medido agora, e é sistêmico:** **nove cidades pintam cor no mapa** (taio, rio-do-sul, ibirama,
indaial, blumenau, gaspar, ilhota, rio-dos-cedros, brusque) e, até este commit, **nenhuma declarava de
qual régua eram as cotas**. As **dezesseis** estações ao vivo têm `regua: null`. A regra nº 1 do projeto
existia em palavras e **não havia campo onde ela pudesse ser conferida**.

**Feito:** campo `regua_das_cotas` (+ `regua_das_cotas_fonte`) preenchido onde a fonte NOMEIA a régua —
Rio do Sul (Ponte Dom Tito Buss) e Brusque (Ponte Estaiada) —, e `valida_regua_das_cotas` passa a
**avisar** a cada rodada as que faltam (sete hoje).

**Por que aviso e não erro:** virar erro reprovaria as nove de uma vez, e o conserto seria apagar cota.
Tirar cor do mapa de uma cidade durante cheia é **decisão de quem mantém o projeto**, não efeito
colateral de validador. O aviso mantém a lacuna visível, que é o que faltava.

## A5 · Gaspar estação 21 — identidade OK, atraso é da fonte
A auditoria notou a ausência de nível fresco; falta dizer que **a identidade da estação 21 está provada**
(mesma régua em `/estacao/ver/21` e na tabela) e que o atraso vem da fonte. Sem nível fresco o site não
inventa — `NivelAoVivo` e `CotasDeRua` já recusam leitura velha.
**Divergência a registrar:** a legenda do site municipal diz **5/7 + chuva 6 mm**; o PLANCON diz
**5/6/7**. São escalas diferentes para a mesma cidade.

## A6 · Home linearizava o Açu ✅ resolvido em 05/09
A home lia o cadastro errado e afirmava `Taió e Rio do Sul → Ibirama → Indaial → …`. Agora sai do
`estacoes.json`: tronco, cabeceiras e afluentes em linhas separadas e rotuladas. Ibirama aparece como
lateral (Rio Hercílio), Taió e Ituporanga como cabeceiras paralelas.

## A7 · Barragens: montante ≠ cidade ✅ travado
`montante_m` é **altitude do reservatório** (353,66 m na Oeste), e `nivel_na_regua_da_barragem_m` é a
régua da barragem (14,66). Há teste e `_meta.ALTITUDE_NAO_E_REGUA`. Taió cidade usa `nivelCentro`. O
nível da barragem em metros **não vai ao mapa**.

## A8 · Maré de Itajaí — não há marégrafo na foz
A coleta CIRAM devolveu **384 linhas sem nível** para Itajaí. **Balneário Camboriú é proxy/residual, não
régua da barra.** A tábua da UNIVALI é de setembro/2026.

## A9 · Clima360 / AMFRI — não entra
Promessa de 38 estações (Meteoblue, ago/2026). `clima360.pro` **não é fonte aberta** e não entra no
`ultimo.json`.

---

## Adendo B — o que fica explícito no plano de tela

| item | estado |
|---|---|
| tela rica por cidade | ✅ existia; ganhou `/monitor/:cidadeId` em 05/09 |
| clique no traço do rio | ✅ feito em 05/09 |
| Gaspar sem mancha | ✅ 1.613 cotas de rua no mapa |
| Brusque | ✅ no mapa **sem estado**, até cravar a régua |
| mecanismo mancha×nível | ✅ apagado até A1 |

**Não interpolar eventos, não preencher rua sem cota, não usar mancha como previsão.** Travado por teste.

## O que NÃO fazer (registrado para não voltar)

- Não subir os itens 4–10 para "Alta".
- **Não "corrigir" o histórico de Blumenau com −20 cm global** — a regra de referência do `CLAUDE.md`
  proíbe conversão gravada.
- Não trocar as manchas do GeoItajaí pelas do ArcGIS.
- Não tratar 76 grupos de cotas como 76 erros: parte é "sem número" colado.
