# Redesenho do Monitor no celular — decisão e etapas (07/10/2026)

## A decisão do Jefferson

Em 07/10/2026 o Jefferson revisou três telas de **maquete** do Monitor no celular (`docs/maquetes/monitor-mobile-2026-10-07-*.jpg`)
e autorizou implementar **a maquete inteira, com as correções abaixo, em etapas e PRs separados**, com estas condições:

- preservar **dados, coordenadas, traçados reais, cotas, fontes e cálculos** — o redesenho é de casca e de controles;
- começar pelo **mapa limpo e controles compactos**; depois os **painéis**; depois a **barra Mapa · Réguas · Perguntar**;
- mostrar **prints reais** da pré-visualização e rodar os testes, **inclusive a trava do Monitor**;
- **sem merge e sem deploy de produção** até ele dizer;
- os arquivos do Monitor podem mudar (rótulo `monitor-autorizado` nos PRs) e o baseline da `trava-monitor` pode ser refeito
  **para esta tarefa**.

Isto revoga, para esta tarefa, a regra "O Monitor não muda" das decisões D1–D7 de 03/10/2026 (`CLAUDE.md`). A trava continua
existindo: ela passa a travar a geometria **nova**, com baseline regravado em cada etapa e a data no commit.

## As correções do Jefferson sobre a maquete

1. **Faixa × painel sem contradição.** O pino só mostra "atenção" (ou outra faixa) quando há faixa válida para aquela leitura;
   sem faixa, só o nível. (No app real a regra já é essa — `faixaDaCidade` só pinta com cota do cadastro e leitura fresca; a
   maquete é que escreveu "sem faixa oficial vinculada" num painel de cidade em atenção. Fica travado em teste.)
2. **Painel inferior em dois tamanhos.** Ao tocar no pino, abre a versão **compacta** (nível, horário, tendência); o tamanho da
   maquete é o **expandido**.
3. **Cabeçalho.** No Monitor do celular, as abas do topo (Início · Monitor · Itajaí-Açu · Itajaí-Mirim) saem; essas páginas
   ficam no menu. Libera mapa.
4. **Rios.** Reduzir um pouco o brilho azul; **traçados e coordenadas reais** continuam. Nas camadas, **Rio Benedito e Rio dos
   Cedros separados** (a maquete os juntou).
5. **Tempo dos dados.** Horário **completo** nos detalhes. Durante a reprodução, "Agora" vira o **horário histórico**, e fica
   claro que a leitura não é atual.
6. **Nenhum texto de maquete** ("não visível no print", "outro estado (exemplo)"): só mensagens que correspondem a dados reais.
   O menu de camadas da maquete ficou bem organizado e é a referência.

## O que a maquete muda em relação ao Monitor de hoje (print real de 07/10/2026, 390×844)

| Hoje | Maquete |
|---|---|
| Faixa do 199 + cabeçalho + abas (≈197 px antes do mapa) | Faixa do 199 compacta + cabeçalho com menu; sem abas no celular |
| Bloco "Monitoramento da bacia" com a caixa do chat, "Cidades ▾", "Tela cheia" por cima do mapa | Busca "Cidade ou régua" em pílula; botões redondos de camadas e tela cheia à direita |
| Rótulo de cada cidade com nível, idade, "24 h: N mm" e setas | Pino com o nome; chuva só como bolha nas estações com pluviômetro; "sem leitura" em texto pequeno |
| "Faixa estadual" em roxo nos rótulos | Pino tracejado "faixa estadual" (na legenda) |
| Botão "Camadas de cheia" + painel aberto | Menu "Camadas do mapa": Camadas de cheia · Maré · Chuva 24 h · Legenda (recolhível) · Traçados dos rios (caixas) |
| "▶ Reproduzir 24 h" + slider + "ao vivo" | Barra com ▶, "24 h", slider com −24h/−18h/−12h/−6h/**Agora** (vira o horário na reprodução) |
| Chip "Mar · Maré baixando ▾" no canto | Chip "≈ Maré: baixando ▾" acima da barra |
| Painel da cidade: folha com tudo (cotas, estadual, fonte) | Folha compacta (nível · horário · tendência) → expandida (chuva 24 h, cota, botões Ver histórico / Detalhes da fonte) |
| — | Barra inferior **Mapa · Réguas · Perguntar** |

## Etapas (um PR por etapa, todos com `monitor-autorizado`, nenhum mergeado sem o Jefferson)

| Etapa | Entrega | Trava |
|---|---|---|
| 1 | Mapa limpo e controles compactos: cabeçalho sem abas no celular, busca em pílula, botões redondos, menu de camadas organizado (Benedito e Cedros separados), brilho dos rios reduzido, rótulos enxutos, barra de reprodução com "Agora" → horário histórico, horário completo | baseline novo (390×844 e 360×740); regras 2–3 continuam |
| 2 | Painel da cidade compacto → expandido; só textos de dados reais | baseline igual ao da etapa 1 |
| 3 | Barra inferior Mapa · Réguas · Perguntar | a regra 4 da trava (barra fixa no Monitor) é revista: a barra passa a ser parte do Monitor e o baseline a desconta |

Desktop (1280×800, 1366×768): a etapa 1 muda só o que é comum (menu de camadas, brilho, rótulos, horário); a casca de desktop
fica como está até decisão.

## O que não muda

Dados em `data/`, coordenadas dos pinos (`coordenadas` do cadastro), traçados (`data/rios/*.geojson`), cotas, fontes, as regras
do mapa (`docs/kikikuru.md`: cor = faixa, nunca metro; animação = nível; cinza não corre; fuso), os comandos do chat e a ponte
(`comandos/ponte.ts`).

## Etapa 1 — o que entrou (07/10/2026, PR em rascunho, sem merge)

Prints reais da pré-visualização (390×844, 360×740 e 1280×800) estão no PR. O que mudou, por arquivo:

- **Casca no celular** (`App.tsx`, `App.module.css`, `FaixaEmergencia`): a faixa do 199 vira uma linha
  ("Defesa Civil: 199 · Bombeiros: 193 · Não é alerta oficial"); o cabeçalho vira uma linha com o menu ☰
  (as cinco páginas descem dele), a marca e o nome da página atual. Nada é `position: fixed`. No computador a
  casca é a mesma de antes. O mapa mede `calc(100dvh − 5.875rem)` (94 px medidos em 360 e 390) e termina no fim
  da tela.
- **Topo do mapa** (`MonitorBacia.tsx`/`.module.css`): o mesmo DOM do cartão de sempre vira, no celular, uma
  linha transparente — a caixa do chat em pílula ("Cidade, régua ou pergunta", com o botão de enviar em seta) e
  o botão "Cidades". Título, aviso e "Tela cheia" em texto somem (o aviso volta em tela cheia). À direita, uma
  coluna de botões redondos: Camadas do mapa, Tela cheia, +, −, e Ver tudo quando há zoom.
- **Destaque da bacia** (`logica/destaqueDaBacia.ts`, com teste): sob a pílula, a cidade com a faixa
  **municipal** mais grave acima da atenção, com o nível e a hora **dela**; toque abre a cidade. Só existe com
  faixa válida (cota do cadastro + leitura fresca — `faixaDaCidade`, travado em teste); nunca estadual, "várias
  réguas", cinza, nem durante a reprodução. Sem cidade nessas condições, não aparece nada — não há "tudo normal".
- **Menu "Camadas do mapa"** (celular e computador), nesta ordem: Camadas de cheia (interruptor que espelha o modo
  do `CamadasMonitor`, que continua montado para o chat; sub-linha com a camada desenhada ou "nenhuma camada
  desenhada agora"), Maré (visibilidade; sub-linha com o estado real), Chuva 24 h (visibilidade), Animações
  (o botão "Pausar/Retomar animações" saiu da legenda para cá — um só, o mesmo da ponte do chat), Legenda
  (recolhível, a mesma lista da legenda do canto), Traçados dos rios (uma caixa por curso **carregado**,
  `logica/tracadosDoMapa.ts` com teste — Benedito e Rio dos Cedros separados, braços do Rio Rafael juntos,
  tronco marcado e fixo; só o que existe em `data/rios/`, sem "em breve") e Fundo do mapa (saiu da legenda; a
  atribuição do OSM ficou fora, sempre à vista).
- **Rótulos compactos** (`mapaMotor.ts`, `OpcoesPinos.compacto`, só em ≤ 700 px): nome; "sem leitura"/"sem régua"
  quando não há número; a chuva como bolha com o valor, e só onde há pluviômetro com acumulado de 24 h de agora
  (`linhasChuvaCompactas`). A cidade selecionada continua com a linha inteira. Nível e hora ficam no painel.
- **Brilho**: halo do rio de 12→8 e alfa 0,9→0,8; brilho do pino 10→7. Traçados, cores por faixa e largura por
  faixa não mudam.
- **Maré**: o chip saiu do canvas (`etiquetaMare: false`) e virou HTML acima da barra de reprodução, com a próxima
  preamar/baixa-mar ao toque, a fonte (tábua da Marinha) e "maré não é cheia". No `MapaRios` nada muda.
- **Reprodução**: botão com ▶ e "24 h"; marcas −24 h · −18 h · −12 h · −6 h · **Agora**; no passado, "Agora" vira o
  horário (Brasília) em âmbar e a linha de estado diz "{dia, hora} · reprodução · não é a leitura atual".
  Ao vivo, a linha diz "ao vivo" (o chat e os testes leem isso).
- **Horário completo**: o painel da cidade e o da régua mostram sempre "medida em dd/mm, hh:mm"; leitura velha
  ganha "(leitura antiga, não é a de agora)".
- **Trava**: baseline regravado (celular: y = 94; computador: igual ao de antes). `auditoria.mjs` abre o menu pelo
  botão "Camadas do mapa"; `pwa.mjs` aceita a faixa do 199 nas duas redações; `colisao-dos-controles` passou a
  cobrir a coluna de botões da direita (com o menu de cidades aberto ela some, como o rodapé).
- **Prints reais** (pré-visualização local com os dados do branch `tempo-real` de 07/10/2026 ~07h UTC):
  `docs/prints/monitor-etapa1-2026-10-07/`.

Fora da etapa 1 (ficam para a 2 e a 3): painel compacto → expandido; barra inferior Mapa · Réguas · Perguntar.
