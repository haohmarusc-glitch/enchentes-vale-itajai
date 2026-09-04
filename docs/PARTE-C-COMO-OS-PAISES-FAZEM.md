# Como os países que mais alagam resolvem a "parte C" — a mancha em tempo real

Pesquisa de 04/09/2026. Pergunta: alguém gera mancha de inundação em tempo real a partir de cotas de
rua? **Resposta: ninguém.** Três modelos distintos, e nenhum interpola pontos em runtime.

> Este documento é **pesquisa sobre sistemas de terceiros** — não descreve dado nosso, e por isso não
> há contagem daqui para conferir. As três afirmações sobre o projeto que ele faz de passagem foram
> conferidas em 04/09/2026: Itajaí tem **10** manchas observadas (`data/manchas/itajai/`, 1983–2015) ✅,
> os **5.237** pontos cotados existem (`brutos/itajai-pontos-cotados-altimetricos.geojson.json`) ✅ e
> o `_meta` deles avisa que são **altura de terreno, não cota de régua** ✅ — o que reforça, e não
> enfraquece, a ressalva de datum. Leia junto com `docs/MDT-SC-E-CARTA-ENCHENTE.md`, que é o
> precedente **local** do mesmo problema, com número de acurácia.

---

## 1. Japão — Kikikuru (JMA): NÃO desenha mancha. Desenha RISCO em grade.

O Kikikuru é uma **grade colorida de 1 km²** (era 5 km² até 2019) que mostra, em cinco níveis, *"o quão
perto o perigo atual e previsto está de um critério de aviso pré-definido em cada ponto"*.
Fonte: JMA, "Real-time Risk Map".

**O que ele NÃO faz:** não desenha até onde a água vai chegar. Não tem polígono de inundação. Não diz
"esta rua está alagada". Ele diz "neste quilômetro quadrado o risco está roxo".

**A divisão de papéis é deliberada, e é a parte mais instrutiva:**
> *"Para rios grandes como o Arakawa ou o Tone, o governo nacional/prefeitural e a JMA emitem juntos
> 'Previsões de Cheia de Rios Designados' — porque esses rios têm estações de nível, permitindo avaliação
> por nível REAL. Ou seja, há uma divisão: previsão de cheia para rios grandes, e Kikikuru de cheia para
> rios pequenos e médios."*

Para o rio grande, **mostra-se o nível medido contra a cota**. Para o córrego sem régua, mostra-se
**risco calculado**, em grade grossa, sem fingir precisão de rua. **O Kikikuru existe justamente para o
"córrego sem nome atrás da sua casa"** — onde não há régua para medir.

**Tradução para o Vale do Itajaí:** o Açu, o Mirim e o Hercílio são "rios designados" — têm régua, mostra-se
nível × cota. Os ribeirões da Murta e Canhanduba, os "córregos sem nome" de Gaspar e Ilhota que represam
— esses seriam o caso do Kikikuru: risco por área, não mancha por rua.

**Como o morador usa:** a cor do lugar onde ele está. Roxo = evacue. Preto = já está acontecendo, suba um
andar. Atualiza a cada 10 min. E a instrução explícita: *"se rio acima está perigoso, rio abaixo pode
ficar perigoso depois — cheque também rio acima"*. É a topologia em árvore ensinada ao cidadão.

---

## 2. EUA — FIMAN (Carolina do Norte): DESENHA mancha. Mas é BIBLIOTECA PRÉ-CALCULADA.

O FIMAN mostra polígono de inundação em tempo real — é o caso mais próximo do que foi pedido. **Mas o
polígono não é gerado no momento.** Os documentos oficiais são explícitos:
> *"Gauges · Telemetry · **Pre-made inundation libraries** · Web tool"*
> *"For each incremental rise in flood waters, buildings, roads, and infrastructure that would be impacted
> are identified."*

**Como funciona de verdade:**
1. Para cada régua, **antes** de qualquer evento, roda-se modelo hidráulico sobre LiDAR e gera-se **um
   mapa de inundação para cada incremento de nível** (a cada ~15 cm, por exemplo).
2. Isso vira uma **biblioteca**: régua X, nível 3,00 m → mapa A; nível 3,15 m → mapa B; e assim por diante.
3. Em tempo real, o sistema **só consulta a biblioteca**: lê o nível da régua e mostra o mapa
   pré-calculado correspondente. Zero interpolação em runtime.
4. Cada mapa pré-calculado já traz a lista de prédios, ruas e pontes atingidas naquele nível — porque
   também foi cruzado antes.

**Custo real disso:** programa estadual criado em 1999 depois do furacão Floyd, ~550 réguas, LiDAR do
estado inteiro, modelagem hidráulica profissional por trecho, empresas de engenharia contratadas
(ESP, Timmons). Anos de trabalho. E tem os quatro modos separados e rotulados: *Current* (nível medido
agora), *Scenario* (e-se), *Forecast* (previsão do NWS) e *Historic* (evento passado). **Nunca mistura.**

**O que o FIMAN prova:** mancha em tempo real é possível — **quando é seleção de mapa pronto, feito com
modelo e terreno, não desenho feito na hora a partir de pontos de rua.** A diferença entre os dois é
exatamente a diferença entre "medição + modelo validado" e "chute geométrico".

---

## 3. Reino Unido — Environment Agency: POLÍGONOS FIXOS que mudam de COR.

A EA não gera mancha nem em runtime nem por biblioteca. Ela tem **3.379 polígonos fixos** — as *Flood
Warning Areas* e *Flood Alert Areas* — desenhados **uma vez**, por especialista, cobrindo a planície de
inundação de cada trecho. Cada polígono tem uma régua gatilho com limiar.

Em tempo real, o que muda é **só a cor do polígono**: verde → Alert (nível 3) → Warning (nível 2) →
Severe Warning (nível 1). O contorno nunca muda. O morador não vê "a água chegou até aqui" — vê "sua área
está em Warning".

**Detalhe de rigor que interessa ao projeto:** a API da EA declara o **datum** de cada leitura —
`mAOD` (metros acima do datum nacional), `mASD` (metros acima do zero local da régua), ou `m` (datum não
especificado). É a regra do datum do projeto, formalizada em campo obrigatório.

---

## Síntese: os três modelos e o que cada um exige

| | Kikikuru (JP) | FIMAN (EUA) | Environment Agency (UK) |
|---|---|---|---|
| **O que mostra** | risco em grade 1 km | mancha por nível | polígono fixo colorido |
| **Gerado em runtime?** | sim, mas é RISCO, não extensão | **não** — busca em biblioteca | não — só muda cor |
| **Base** | chuva + modelo hidrológico | LiDAR + hidráulica, pré-calculado | planície desenhada por perito |
| **Precisão que afirma** | 1 km² | prédio a prédio | área |
| **Exige** | modelo nacional de escoamento | LiDAR + anos de modelagem | levantamento de planície |
| **Mistura medido/estimado?** | não — separa rio grande (medido) de córrego (risco) | não — 4 modos rotulados | não |

**Nenhum dos três interpola cotas de rua em tempo real.** O que foi pedido não tem precedente nos sistemas
de referência — e não é por limitação técnica, é por escolha: os três preferem afirmar menos com certeza a
afirmar mais com chute.

---

## O que isto diz para o projeto

**Existe um caminho para a parte C, e é o do FIMAN — mas em versão que cabe no projeto:**

**Biblioteca de manchas OBSERVADAS, indexada por nível.** Itajaí tem 10 manchas reais (1983–2015), cada
uma de um evento com pico conhecido. Isso já é uma biblioteca: nível → mapa. Falta só o índice.
- Rio em 2,8 m → *"a mancha observada mais próxima é a de 2015, quando o pico foi 3,1 m; ela alcançou
  até AQUI"* — e desenha a de 2015, rotulada "observada em 2015 · pico 3,1 m".
- É FIMAN sem LiDAR: em vez de mapa modelado por incremento, mapa observado por evento. Menos resolução,
  mas **cada polígono é levantamento de campo**, não chute. E o rótulo diz de onde veio.
- Para Gaspar (69 picos) e Blumenau (102), o mesmo modelo funciona **se** existirem manchas por evento —
  hoje não existem no projeto; vale perguntar à Defesa Civil de cada uma.

**Para os ribeirões e o represamento (Gaspar, Ilhota, Itajaí): o modelo do Kikikuru.** Não há régua
suficiente, o comportamento é de estuário, os planos municipais dizem que a COMPDEC "não avisa a população"
nessa fase. Não desenhar mancha. Marcar a **área** do ribeirão com risco em faixa, explicitando que é
cálculo, não medição.

**O que fica proibido, com precedente:** polígono interpolado de pontos de rua, apresentado como extensão
atual. Nenhum dos três sistemas faz isso, e o FIMAN — o único que mostra mancha — gastou 25 anos e LiDAR
estadual para não ter que fazer.

**A regra do projeto sai reforçada pela comparação:** cada coisa no mapa é uma medição (nível), um
levantamento (cota de rua, mancha histórica) ou uma conta entre os dois. O Kikikuru acrescenta um quarto
tipo legítimo — **risco calculado, em grade grossa, rotulado como risco** — para onde não há medição.
Nunca o quinto: extensão inventada.
