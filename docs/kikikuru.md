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
| Mapa do rio em `<canvas>`, colorido por trecho + correnteza animada | `web/src/componentes/MapaRios.tsx` (geometria pura em `web/src/logica/mapaCanvas.ts`) | `data/rios/*.geojson` + `ultimo.json` |
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
