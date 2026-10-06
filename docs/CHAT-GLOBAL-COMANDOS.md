# Chat no topo de todas as páginas, com comandos (06/10/2026)

Pedido do Jefferson, mais a especificação `chat-global-comandos-monitor`. Cada ideia foi conferida no código antes
de entrar aqui. Este documento é o plano: o que já existe, o que entra em cada entrega e o que depende de dado
que ainda não temos.

## Decisões do Jefferson (06/10/2026)

1. **No Monitor, a caixa fica dentro do bloco do topo** ("Monitoramento da bacia"), que já está sobre o mapa.
   O retângulo do mapa não muda, e a trava de geometria (`trava-monitor.mjs`, ±1 px) passa sem refazer a
   referência. Os arquivos do Monitor mudam, então o PR leva o rótulo `monitor-autorizado`.
   - Isto substitui a sugestão da especificação de "reservar espaço no layout e recalcular o tamanho do mapa".
2. **Nas outras páginas, uma barra compacta logo abaixo da faixa do 199.** Ao tocar, a conversa abre por cima
   da página. Ela recolhe, fecha e limpa.
3. **"Zoom na rua" só onde há coordenada.** Nas outras cidades, o chat responde a cota da rua e diz que ela
   ainda não tem ponto no mapa. Nada é geocodificado na hora (regra de `docs/PLANO-MANCHAS-E-TELA-POR-CIDADE.md`).

## O que o código já tem (conferido)

| Peça | Onde | Serve para |
|---|---|---|
| Chat local por regras, 12 intenções + `agora` e `ajuda` | `chat-local/motor.ts`, `ChatLocal.tsx` | perguntas; hoje só em `/perguntas` e na aba Histórico |
| Barreira do presente (199, nunca previsão nem conselho) | `motor.ts` `pedeAgora`, `situacaoAgora.ts` | toda pergunta de agora passa por ela primeiro |
| Classificador de IA (piloto, desligado) | `functions/api/chat-classificar.ts` | só classifica; o texto sai do motor |
| Cidade pela URL | `MonitorBacia` lê só `/monitor/:cidadeId` | navegar |
| Escolher régua (Itajaí, DC-01…DC-11) | `escolherRegua`, `seletorDeRegua.ts` | selecionar e centrar |
| Zoom, "Ver tudo", reenquadrar | `aplicarZoom`, `VISTA_INTEIRA`, `pedidoDeEnquadrar` | aproximar, afastar, bacia |
| Fundo escuro / satélite / mapa | estado `fundo` | trocar o fundo |
| Camadas de cheia | estado **interno** de `CamadasMonitor` (`modo`) | ligar e desligar; precisa abrir o controle para o chat |
| Reprodução das últimas horas | `idxRepro`, `tocando` | "voltar ao agora" |
| Motivo de pino cinza | `motivoSemCor.ts`, `textosDoPainel.ts` | "por que está cinza?" |
| Origem do pino e equivalência | `posicaoDoPino.ts`, `coordenadas_status`, `equivalencia_estadual` | "essa coordenada foi confirmada?" |
| Árvore da bacia e confluências | `arvoreDaBacia.ts`, `_topologia` | "o que fica a montante?", "onde entra o Benedito?" |
| Fonte do traçado | `data/rios/*.geojson` `properties.fonte` e `cobertura` | "de onde vem esse traçado?" (sem a data da base: ela está só nos brutos) |
| Texto para compartilhar | `agora.ts` `textoParaCompartilhar` (regra D4) | "copiar resumo desta cidade" |
| Série recente | `dados/serie.ts`, `resumo24h.ts` | "o que mudou na última hora?" |
| Ruas com geometria | `data/vias/itajai.geojson` (1.863 vias, GeoItajaí) | só Itajaí; já destacada em branco tracejado no mapa de manchas |
| Cotas de rua com ponto | `data/cotas-ruas.json`: Gaspar (1.615), Brusque (348) | ponto, não traçado |
| Cotas de rua sem coordenada | Blumenau (2.023), Rio do Sul (555) | só texto |

**O que não existe:**
- canal de relato de problema;
- filtro de réguas por qualidade no Monitor;
- parâmetros de URL no Monitor além da cidade;
- comando de tela cheia sem toque do usuário (o navegador exige o gesto).

## A arquitetura

- **Comandos tipados num registro.** Cada comando tem nome, argumentos, pré-condições, executor e resultado
  estruturado (`ok`, `nao_encontrado`, `ambiguo`, `indisponivel`, `falhou`).
  - Exemplos: `ir_cidade`, `escolher_regua`, `zoom`, `ver_bacia`, `fundo`, `camada`, `voltar`, `situacao`,
    `ajuda`.
  - O texto do usuário só **propõe** um comando do registro. Nada de URL, JavaScript ou nome inventado: todo
    identificador é resolvido contra o cadastro (`estacoes.json`, `estacoes_tempo_real`).
- **Ponte com o Monitor.** Ele registra os próprios executores numa ponte tipada, chamando as funções que os
  botões já usam (`escolherRegua`, `aplicarZoom`, `setVista`, `setFundo`). Não há clique artificial no DOM.
  - O resultado real volta ao chat: "Mapa centrado na régua DC-05 · Sítio Sr. Hilário", ou "Esta régua não
    está no mapa".
- **URL.** O Monitor passa a ler `?regua=` e `?fundo=`, além da cidade. O mesmo endereço serve de link e de
  retomada.
- **Voltar.** Antes de cada ação do chat, o Monitor guarda um retrato: cidade, vista, régua, fundo e camada.
  "Voltar ao mapa de antes" restaura o último, numa pilha curta.
- **Contexto.** "Aqui", "essa cidade" e "essa régua" usam o que está aberto. Uma cidade citada no texto
  vence o contexto. Em Itajaí sem régua escolhida, "aproximar a régua" pergunta qual (são 11).
- **Encadeados.** "Mostre Timbó, aproxime a régua e ative satélite": tudo é resolvido e validado antes, e
  depois executado em ordem. Se um passo falha, os dependentes param e o chat diz o que já foi feito.
- **Pergunta não mexe no mapa.** Só pedido de ação mexe.

## Matriz de comandos

`1ª` = primeira entrega · `2ª` = segunda · `dado` = depende de dado ou infraestrutura · `não` = fora de escopo.

| Pedido (exemplo) | Entrega | Observação conferida |
|---|---|---|
| "mostrar Blumenau", "ir para Taió" | 1ª | rota `/monitor/:cidade`; nas outras páginas, abre a cidade |
| "aproximar a régua", "zoom na régua DC-05" | 1ª | Itajaí: seletor existente. Nas outras: reenquadra o pino da cidade |
| "todas as réguas de Itajaí" | 1ª | opção "Todas" do seletor |
| "aproximar", "afastar", "ver a bacia toda" | 1ª | `aplicarZoom`, `VISTA_INTEIRA` |
| "satélite", "mapa de ruas", "fundo escuro" | 1ª | os três fundos existentes |
| "ligar/desligar manchas", "mancha de 2008" | 1ª | só onde a camada existe; o controle de `CamadasMonitor` passa a aceitar comando |
| "voltar ao mapa de antes" | 1ª | pilha de retratos, inclusive camada |
| "como está Blumenau?", "chuva em Ituporanga" | 1ª | resposta atual com hora e fonte, pela barreira do presente |
| "o que posso pedir?" | 1ª | lista gerada do registro e da página atual |
| "o que estou vendo?" | 1ª | cidade, régua, fundo, camada ativa e modo histórico, lidos do estado |
| "essa informação é atual ou histórica?" | 1ª | reprodução ligada ou camada histórica |
| "ir para a leitura mais recente" | 1ª | encerra a reprodução |
| "essa coordenada foi confirmada?" | 1ª | `textoDaPosicao` + `equivalencia_estadual` |
| "por que essa régua está cinza?" | 1ª | o mesmo motivo que o painel já mostra; nunca um segundo diagnóstico |
| "quais leituras estão atrasadas?" | 2ª | idade de cada leitura pela regra de leitura velha que já existe (`MIN_VELHA`) |
| "mostrar só as réguas sem leitura" | 2ª | filtro novo no Monitor, visível na tela, com "limpar filtros" |
| "abrir o gráfico desta régua" | 2ª | não há gráfico no Monitor; abre a página da cidade, na aba que tiver a série |
| "o que mudou na última hora?" | 2ª | `serie.ts`; diz lacunas e o passo das medições |
| "de onde vem esse traçado?" | 2ª | fonte e cobertura do GeoJSON; a data da base precisa ir do bruto para o arquivo |
| "o que fica a montante daqui?", "afluentes deste trecho" | 2ª | resposta pela árvore; conexão não é previsão de impacto |
| "ver a confluência do Benedito" | 2ª | ponto gravado (−26,89134, −49,23557). O Luís Alves não tem ponto e o chat diz isso |
| "comparar as réguas de Itajaí" | 2ª | lado a lado com hora e referência; nunca subtrai referências diferentes |
| "copiar resumo desta cidade" | 2ª | `textoParaCompartilhar` (D4: sem endereço, com hora, sem ordem de ação) |
| "copiar link desta visualização" | 2ª | `#/monitor/…?regua=…&fundo=…`. **Atenção:** o site só abre para e-mail cadastrado, e isso tem de vir escrito junto |
| "mostrar a rua X, Itajaí" + destaque | 3ª | traçado real da via (GeoItajaí); escolha entre homônimos |
| "rua X, Gaspar/Brusque" | 3ª | só ponto: "localização aproximada; traçado da rua indisponível" |
| "rua X, Blumenau/Rio do Sul" | dado | só a cota; sem ponto no mapa (decisão 3) |
| "manchas na rua X" com rua em outra cor | 3ª | ver abaixo |
| "relatar problema nesta régua" | dado | não há canal; no máximo preparar o texto para a pessoa copiar |
| "usar minha localização" | dado | fase posterior, só com permissão pedida na hora |
| "tela cheia" | não | o navegador exige toque no botão; o chat aponta o botão |
| evacuar ou ficar, "é seguro?", previsão de hora exata | não | barreira do presente: dado, hora e 199 |

## Rua destacada sobre as manchas (3ª entrega)

- **Onde já existe:** em Itajaí, o mapa de manchas (`MapaManchas`, Leaflet) já destaca a via buscada em branco
  tracejado e enquadra nela.
- **Aparência:**
  - linha magenta com contorno contrastante, numa camada própria acima das manchas, sem mudar as cores de
    risco;
  - rótulo com o nome da rua;
  - entrada na legenda: "Rua selecionada — destaque de localização". O destaque não indica risco.
  - Antes de fixar a cor, conferir contraste nos fundos e conflito com a legenda.
- **Mesmo destaque fora do chat:** a busca normal da página aplica o mesmo destaque.
- **Comportamento:**
  - "Remover destaque" tira só a rua;
  - trocar de cenário mantém a rua;
  - trocar de cidade limpa;
  - "voltar" restaura.
- **Dados:**
  - só o traçado real da via, sem reta entre pontas e sem círculo no lugar de traçado;
  - Gaspar e Brusque mostram ponto, com o aviso de localização aproximada;
  - homônimos: o chat pergunta antes de marcar;
  - vários cenários sem escolha: pergunta antes de ligar.
- **Interpretação:**
  - rua cruzando uma mancha é "interseção com o cenário X", nunca alagamento confirmado;
  - ausência de interseção não diz que a rua é segura.

## Limites das respostas (já valem no chat de hoje)

- **Toda leitura** vem com hora e fonte, e leitura velha nunca aparece como atual.
- **Nunca misturar** nível medido, cota de referência, faixa municipal, faixa estadual e altitude.
- **Segurança de rua:** a cor de uma régua ou a falta de mancha nunca dizem que a rua é segura.
- **Tempo de chegada:** só em intervalo, e só com a metodologia e os pares que o projeto já exige.
- **Maré** medida em Balneário Camboriú não é maré de Itajaí.
- **Compartilhar** é preparar o texto; nunca enviar por conta própria.

## Critérios de aceitação da 1ª entrega

- [ ] A caixa aparece **uma vez** em todas as rotas: barra compacta fora do Monitor, bloco do topo no
  Monitor de cada cidade.
- [ ] `trava-monitor` passa com a referência atual. `colisao-dos-controles` passa com a caixa aberta e
  fechada: zoom, menu de cidades, legenda e atribuição continuam livres.
- [ ] **Acessibilidade e celular:**
  - funciona pelo teclado, com rótulos e foco previsível;
  - o resultado é anunciado uma vez (`aria-live` educado);
  - o teclado virtual do celular não cobre a entrada;
  - nomes longos de cidade e régua não quebram o layout.
- [ ] **Comandos:**
  - só os do registro executam;
  - o resultado dito é o real;
  - ambiguidade pergunta antes de agir;
  - trocar de cidade não deixa régua antiga no contexto;
  - "voltar" restaura vista, régua, fundo e camada;
  - "ir para a leitura mais recente" sai do modo histórico.
- [ ] **Testes** cobrem: resolução de contexto, validação de argumentos, cada falha e a sequência encadeada
  com parada no passo que falha.
- [ ] O relatório final lista os arquivos alterados, os comandos entregues, os testes e o que depende de dado.

## Primeira entrega (06/10/2026): o que saiu

### Onde a caixa fica

- **Páginas da casca nova:**
  - uma barra logo abaixo da faixa do 199, antes do conteúdo (`componentes/ChatNoTopo.tsx`, em `App.tsx`);
  - tocar abre a conversa logo abaixo da barra;
  - "Recolher" e "Limpar" ficam no painel, e Esc recolhe.
- **Monitor de cada cidade (e o piloto de Ascurra):** dentro do bloco do topo ("Monitoramento da bacia").
  - **No computador:** a conversa abre na coluna da esquerda, sem cobrir zoom, fundos nem menu.
  - **No celular:** com a conversa aberta, a coluna sobe acima da folha da cidade. Depois de um pedido, a
    conversa recolhe sozinha, porque o resultado está no mapa, e a última resposta fica numa linha com
    "Ver conversa".
- **Uma vez só:** em `/perguntas` e na aba Histórico, que já têm o chat da página, a barra some.
- **A conversa:**
  - é uma só no site e segue entre páginas (`chat-local/conversa.ts`);
  - fica só na memória da aba, sem gravar nada no aparelho;
  - o motor e os dados carregam só quando a pessoa toca na caixa, e as leituras ao vivo também.

### Os comandos (`web/src/comandos/`)

| Arquivo | O que faz |
|---|---|
| `tipos.ts` | os passos tipados e o resultado de cada um |
| `catalogo.ts` | cidades e réguas DC tiradas de `estacoes.json`, e de nada mais |
| `interpretar.ts` | pedido ou pergunta: só vira comando o que casa inteiro; pedido encadeado é resolvido antes de executar; régua ambígua pergunta qual |
| `executar.ts` | executa em ordem; abre o Monitor quando o passo precisa do mapa e espera ele ficar pronto; para no primeiro passo que falha e diz o que já foi feito; guarda o retrato para "voltar" |
| `ponte.ts` | o Monitor registra as funções que os botões usam; o chat nunca clica no DOM |
| `ajuda.ts` | "o que posso pedir?", conforme a tela aberta |
| `usarComandos.ts` | o contexto vem do endereço (cidade, Monitor, régua escolhida) |

**Os comandos entregues:**
- **navegação:** "mostrar X" (Monitor da cidade) e "abrir o monitor"; "histórico de X", "minha rua em X" e "página de X"; "abrir o mapa das manchas", "início", "abrir o Itajaí-Açu/Mirim", "a foz";
- **réguas:** "zoom na régua DC-05" (abre Itajaí, se preciso), pelo nome ("régua do Rio do Meio") e "todas as réguas"; "aproximar a régua" (em Itajaí sem régua escolhida, pergunta qual das onze); "régua de X";
- **mapa:**
  - "aproximar", "afastar", "ver a bacia toda";
  - "satélite", "mapa de ruas", "fundo escuro";
  - "ligar as manchas" (pergunta qual se houver várias), "mancha de 2008", "desligar as camadas";
  - "ir para a leitura mais recente", "voltar ao mapa de antes";
- **sobre a tela:**
  - "o que estou vendo?";
  - "essa informação é atual ou histórica?";
  - "por que essa régua está cinza?" — o mesmo texto do painel, de `textosDoFoco` no Monitor;
  - "essa coordenada foi confirmada?";
  - "o que posso pedir?".

Pergunta continua indo ao motor de sempre, com a barreira do presente. "Blumenau" sozinho e "mostrar as
cheias de X" continuam perguntas.

### No Monitor (com o rótulo `monitor-autorizado`)

- **A ponte com o chat**, registrada a cada desenho. `pronto` só vale com a cena montada e a cidade
  enquadrada.
- **`?regua=` e `?fundo=` no endereço**, aplicados uma vez. Valor desconhecido é ignorado.
- **`CamadasMonitor`** aceita um pedido de modo e informa as opções e o modo de agora. O controle continua
  o dele.
- **`textosDoFoco`:** a faixa, o motivo do cinza, a origem do pino e a equivalência saem de uma função só,
  usada pelo painel e pelo chat.
- **O retângulo do mapa não mudou:** `trava-monitor` passa com a referência atual.

### Defeito achado no caminho

O componente das leituras ao vivo do chat repassava um objeto novo a cada desenho, e o efeito realimentava
o estado num laço. A tela não travava, mas a navegação nunca terminava: o endereço ia para o Monitor e a
página ficava no Início. Corrigido com dependências pelas peças (`AoVivoDoChat.tsx`). O teste de navegador
`chat-comandos.mjs` pega o caso.

### Testes

- **`src/comandos/interpretar.test.ts`** (12): pergunta continua pergunta; cidade exige verbo; régua por
  código, nome e cidade; ambiguidade; contexto; cidade citada vence o contexto; encadeado; trecho não
  entendido não executa nada.
- **`src/comandos/executar.test.ts`** (10):
  - abre o Monitor quando precisa e segue a ordem;
  - para na falha e diz o que já foi feito;
  - diz quando o Monitor não abre;
  - régua DC fora de Itajaí;
  - camadas: pergunta, ano, ausência;
  - voltar restaura vista, régua, fundo e camada, e volta à página;
  - perguntas sobre a tela não mexem no mapa.
- **`testes-navegador/chat-comandos.mjs`** (390×844 e 1280×800):
  - a caixa uma vez no Início, no Monitor e em `/perguntas`;
  - "mostrar Blumenau" navega e a conversa continua;
  - DC-05 no seletor, satélite, "o que estou vendo", "voltar";
  - pergunta não mexe no mapa;
  - no celular, a conversa recolhe depois do pedido;
  - o painel aberto não cobre zoom nem fundos;
  - sem exceção de JavaScript.
- **Também passaram:** `npm test` (886), build, `trava-monitor`, `colisao-dos-controles`, `fumaca` e `pwa`.

### O que ficou para depois (2ª entrega e dependências)

- **Segunda entrega:**
  - leituras atrasadas;
  - filtro de réguas sem leitura;
  - gráfico da régua;
  - "o que mudou na última hora";
  - origem do traçado com a data da base;
  - montante e afluentes;
  - confluência no mapa;
  - comparar réguas;
  - copiar resumo e copiar link (`?regua=`/`?fundo=` já são lidos).
- **Depende de dado:**
  - rua no mapa: Itajaí, Gaspar e Brusque têm coordenada; Blumenau e Rio do Sul não;
  - rua destacada sobre as manchas;
  - relatar problema (não há canal);
  - "usar minha localização".
- **Tela cheia:** só pelo botão, porque o navegador exige o toque da pessoa.
