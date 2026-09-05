# Tela do rio no estilo Kikikuru — como está montada

Inspiração: o Kikikuru (キキクル) da Agência Meteorológica do Japão — o rio inteiro
colorido por trecho, a cor ligada à ação, uma barra de tempo com histórico, e o
zoom que troca a informação. Copiamos o **método**, não os dados (que são do
Japão). O que segue é o mapa dos componentes e das regras que os prendem, para
achar rápido e não reintroduzir os erros que a honestidade do projeto proíbe.

## A regra que atravessa tudo: cor = faixa, nunca metro

A cor de uma cidade é a **faixa da régua DELA** (abaixo da atenção / atenção /
alerta / inundação), nunca o nível absoluto em metros. Cada cidade tem seu zero;
duas cidades na mesma cor **não** estão no mesmo metro. Por isso a cor é
normalizada e pode ser comparada de montante a jusante — o metro não. Quem
computa a faixa é `web/src/logica/tempoReal.ts::faixaDaCidade`:

- sem cota cadastrada, ou leitura velha, ou sem leitura → `sem-dado` (cinza,
  **nunca** verde — ausência de dado não pode parecer segurança);
- cidade com várias réguas distintas (a foz) → `varias`;
- caso contrário, a faixa da cota mais alta alcançada.

Os **textos** de cada faixa (rótulo + a frase que remete à Defesa Civil) vêm de
`data/faixas.json` — fonte única — e o site nunca recomenda ação: as únicas
chamadas permitidas são "Siga a Defesa Civil" e "ligue 199".

## Os componentes

| O quê | Arquivo | Lê de |
|---|---|---|
| Diagrama linear, colorido por trecho | `web/src/componentes/DiagramaRio.tsx` | `ultimo.json` (via `useTempoReal`) |
| Mapa do rio em `<canvas>`, colorido por trecho + correnteza + onda | `web/src/componentes/MapaRios.tsx` (motor em `web/src/logica/mapaMotor.ts`; geometria pura em `mapaCanvas.ts`) | `data/rios/*.geojson` + `ultimo.json` |
| Monitor da bacia em tela cheia (Açu + Mirim juntos) + reprodução 24 h | `web/src/telas/MonitorBacia.tsx` (mesmo motor `mapaMotor.ts`) | `data/rios/*.geojson` + `ultimo.json` + `serie-recente.json` + `mare-itajai.json` |
| Linha do tempo de 24 h por cidade | `web/src/componentes/LinhaDoTempo.tsx` | `serie-recente.json` (via `useSerieRecente`) |
| Reprodução da onda descendo | `web/src/componentes/AnimacaoOnda.tsx` | `serie-recente.json` |
| Legenda + textos das faixas | `web/src/componentes/LegendaFaixas.tsx` | `data/faixas.json` |
| Chegada a jusante "se o pico fosse agora" | `web/src/componentes/PainelSePicoAgora.tsx` | `ultimo.json` + `transito.json` |

Tudo é montado em `web/src/telas/TelaRio.tsx`, que no **desktop** põe o mapa numa
coluna fixa (sticky) à esquerda e os dados à direita; no **celular** é coluna
única, com o mapa por último, sob o botão "Ver mapa". O mapa do rio é um
`<canvas>` próprio (NÃO puxa o Leaflet: as telas `/acu` e `/mirim` deixaram de
baixá-lo). O corte é `@media (min-width: 1024px)` em `TelaRio.module.css`.

## O traçado do rio (mapa em canvas)

- Vem do OpenStreetMap (`waterway=river`), licença **ODbL** — o crédito está na
  tela. O bruto fica em `data/brutos/tracado-rios-osm.json`; `scripts/converter_tracado_rios.py`
  agrupa por nome e emite `data/rios/itajai-acu.geojson` e `itajai-mirim.geojson`
  (MultiLineString, `[lon,lat]`).
- O mapa do rio é desenhado num `<canvas>` (não é Leaflet): sem mapa-base de
  ruas, projeção equiretangular própria (a geometria pura fica em
  `web/src/logica/mapaCanvas.ts`, testada). A troca veio do estudo do protótipo
  Grok e do pedido "animação moderna bem intuitiva". O Leaflet segue no pacote,
  mas só carrega com o **mapa de manchas** de Itajaí (`MapaManchas`), onde as
  ruas do fundo são essenciais — logo a economia da dependência não se realiza
  enquanto aquele mapa não mudar.
- `MapaRios` encaixa cada cidade no ponto mais próximo do rio, forma uma
  "espinha" montante→jusante e, para cada aresta do traçado, decide entre quais
  cidades ela cai; a aresta ganha a cor da cidade **a montante** — a mesma regra
  do diagrama. Trecho sem cidade que o pinte fica **cinza**.
- Sobre a cor, a **correnteza animada** desce no sentido do rio (setas orientadas
  pela espinha, pois os ways do OSM não vêm todos montante→jusante) e corre
  **mais rápido onde o nível está mais alto** (`VEL_FAIXA`): a animação
  **significa o nível**, não enfeita. Trecho cinza **não corre** —
  `VEL_FAIXA['sem-dado'] = 0` —, porque não se anima uma água que não se mede.
  `prefers-reduced-motion` congela o movimento (um quadro estático).
- **As COTAS DE RUA aparecem no mapa da cidade, com quatro travas** (`logica/cotasNoMapa.ts`).
  (1) **Só onde o par cota↔leitura foi provado** — a cota descreve UMA régua e o nível vem de outra
  fonte; hoje só **Gaspar** (`cotas_verificado: true`). **Brusque tem 348 ruas georreferenciadas e
  fica de fora**, porque a régua da leitura ao vivo não é a das cotas dela: coordenada não é
  passaporte, e `cotas_verificado` ausente é "ninguém conferiu", não "pode". (2) **Só de perto**
  (≤ 8 km na tela): 1.613 pontos no zoom da bacia viram uma nuvem, e nuvem num mapa de enchente
  lê-se como **mancha** — a área alagada que este projeto se recusa a inventar. (3) **Sem leitura,
  sem estado**: o ponto fica vazado e apagado, porque "não sei" não é "não alagou". (4) **Dois
  estados, nunca um degradê por metro** — cheio, o rio já passou da cota; vazado, ainda não —, com
  **cor fora da paleta de faixa e do violeta do bruto**, porque rua alagada não é faixa de rio. O
  **vazio entre os pontos continua vazio**: não se preenche o que não se sabe. Carregadas sob
  demanda, e desenhadas por baixo de réguas, pinos e barragens.
- **`/monitor/:cidadeId` abre o MESMO Monitor, enquadrado numa cidade.** Não é uma segunda tela: duas
  implementações do mapa ao vivo divergem com o tempo, e o dia da divergência é o dia em que a mesma
  cidade aparece verde numa e laranja na outra. Só mudam o enquadramento inicial e qual pino já vem
  aberto — **nada do que o mapa afirma depende do zoom**. O enquadramento mostra **24 km de largura**
  (`KM_NA_TELA`), calculados a partir da largura da bacia e não cravados: é para caber a cidade **e os
  vizinhos de montante e jusante**, porque a cheia vem de cima e enquadrar só o município esconderia o
  trecho de onde a água está chegando. Aplica-se **uma vez**; depois o zoom é de quem mexe, senão o
  mapa seria arrancado da mão da pessoa no meio da cheia. Cidade sem coordenada (ou id errado no
  endereço) abre na **bacia inteira**: não se inventa posição, e tela em branco num aplicativo de
  enchente é pior que tela sem zoom.
- **Tocar no RIO seleciona a cidade daquele trecho** (`cidadeNoTrecho`, raio 18 px). A ordem do
  toque é do alvo mais preciso para o mais largo: régua (14 px) → pino da cidade (26 px) → trecho do
  rio (18 px). A resposta é a cidade que **PINTOU** o trecho — a mesma que decidiu a cor debaixo do
  dedo —, nunca a mais próxima em linha reta, que poderia ter outra faixa e contradizer o que está na
  tela. Trecho cinza (`sem-dado`) não devolve nada: ali não se sabe de quem é.
  **Regra de pintura, medida em 05/09/2026 e anterior a isto:** o trecho entre duas cidades é pintado
  pela de **montante** (`trechoDoPonto` devolve índice de SEGMENTO da espinha), e por isso a **última
  cidade do rio não pinta trecho nenhum** — quem colore a foz é a penúltima. O corte de trecho passou
  a ser por (faixa, âncora) e não só por faixa: duas cidades vizinhas na mesma cor formavam um trecho
  só, e a metade de baixo devolveria o nome da de cima.
- As **barragens** (Oeste em Taió, Sul em Ituporanga, Norte em José Boiteux)
  entram como **marcadores próprios**: uma parede de aço com as comportas em
  fila, na coordenada que a API da Asthon publica (`coleta_barragens.py`). É a
  **terceira animação** do mapa, e ela **significa operação, não nível**:
  comporta **aberta** mostra a água atravessando (animada); **fechada** é um
  bloco parado. **Leitura velha não anima nenhuma** — o mesmo "cinza não corre"
  da correnteza, aplicado à comporta: não se anima um estado que não se sabe
  mais (`FRESCA_MIN`, 60 min, o mesmo limite do coletor). A **cor é própria**
  (aço + azul-água), **nunca a de faixa**: segurar e soltar são operação normal,
  e cor de faixa ali diria perigo. O **nível da barragem em metros NÃO aparece**
  no mapa — a régua dela tem zero próprio (339 m de altitude na Oeste), e um
  número ao lado do rio convidaria a comparação que a regra do topo proíbe; o
  que atravessa sem datum é o estado das comportas e o percentual do
  reservatório. A parede é horizontal na tela, **simbólica**; a Sul flutua a
  20 km do rio desenhado mais perto porque a cabeceira do Itajaí do Sul ainda
  não tem traçado, e o rótulo carrega a informação sozinho. Só nos mapas do
  **Açu** e da **bacia**: no Mirim não há barragem. Regras em
  `web/src/logica/barragensNoMapa.ts`, com teste.
- Na **foz** (a leste, onde fica Itajaí) o mapa desenha o **MAR**, colorido pela
  **maré** numa escala **azul PRÓPRIA** — jamais a de cheia. Isto é deliberado:
  maré alta **não** é cheia (as réguas do estuário são `alerta_automatico:false`);
  o que ela faz é **travar o escoamento** do rio. `estadoMareAgora` (em
  `logica/mare.ts`) lê a tábua (`data/mare-itajai.json`, via `mareItajai`) e diz
  se a maré **sobe** ou **desce** agora e a que altura do ciclo — o azul segue
  essa altura, e um chip mostra "Mar · Maré subindo/baixando". **Sem tábua**
  (hoje ela está vazia) o mar fica **cinza**, "maré: sem dado" — nada é estimado;
  acende quando `scripts/coleta_mares.py` preencher a tábua.
- Os nomes das cidades têm **anticolisão**: onde os pinos se amontoam (a foz do
  Açu), o rótulo da faixa **mais grave** ganha o espaço e o nome que cairia por
  cima é omitido — o ponto continua e o toque abre o detalhe. A altura do mapa
  se ajusta à proporção da bacia. Acesso por teclado/leitor: botões fora da
  vista repetem o toque em cada cidade (o canvas não é focável por cidade).

## A linha do tempo e a onda (`serie-recente.json`)

- O navegador só tem o `ultimo.json` (um instante). A série acumulada em
  `data/tempo-real/AAAA-MM.ndjson` é matéria-prima **gitignorada** (só na VPS).
- `scripts/coleta_niveis.py::escrever_serie_recente` recorta as últimas ~48 h de
  **nível** por rio e cidade em `data/tempo-real/serie-recente.json`, e
  `publicar_tempo_real.sh` publica esse arquivo junto do `ultimo.json` no branch
  `tempo-real`. Só nível (chuva é outra grandeza e dobraria o arquivo).
- `LinhaDoTempo` desenha UMA cidade por vez (régua própria, nunca metros de
  cidades diferentes no mesmo eixo) com as cotas como faixas de cor e um `Brush`
  de 24 h. `AnimacaoOnda` reproduz o passado: a cada instante pinta cada cidade
  pela faixa dela naquele momento (usa `serie.ts::leituraEm`, a última medição
  ATÉ o instante — nunca a futura). É reprodução do MEDIDO, não previsão.

## Fuso — a regra que já custou uma sessão

`medido_em` sem fuso = **hora de Brasília** (America/Sao_Paulo). Toda fonte grava
assim. O site lê com `deBrasilia()`. Fontes que publicam UTC (a Asthon manda
`last_reading_at` com `Z`) **convertem na entrada do coletor**, não no site. Ver
a regra completa no `CLAUDE.md`.

## O que ainda falta (do brief do Kikikuru e além)

- **Projeção na mesma barra do tempo**: hoje a chegada a jusante vive num painel
  à parte (`PainelSePicoAgora`); juntá-la ao slider é o que resta do item 3.
- **Cota de referência de Vidal Ramos** (e das demais cabeceiras): sem ela o
  nível aparece mas a faixa fica cinza. Ver Pendências no `README.md`.
- **Sinal antecipado das barragens** (Oeste/Sul subindo rápido) como aviso de
  cheia a jusante — anotado, ainda não na tela.
