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

`1ª` a `4ª` = entregas (✓ = entregue em 06/10/2026) · `dado` = depende de dado ou infraestrutura · `não` = fora de escopo.

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
| "quais leituras estão atrasadas?" | 2ª ✓ | idade de cada leitura pela regra de leitura velha que já existe (`MIN_VELHA`) |
| "mostrar só as réguas sem leitura" | 2ª ✓ | filtro novo no Monitor, visível na tela, com "limpar filtros" |
| "abrir o gráfico desta régua" | 2ª ✓ | não há gráfico no Monitor; abre a página da cidade, na aba que tiver a série |
| "o que mudou na última hora?" | 2ª ✓ | `serie.ts`; diz lacunas e o passo das medições |
| "de onde vem esse traçado?" | 2ª ✓ | fonte e cobertura do GeoJSON; a data da base precisa ir do bruto para o arquivo |
| "o que fica a montante daqui?", "afluentes deste trecho" | 2ª ✓ | resposta pela árvore; conexão não é previsão de impacto |
| "ver a confluência do Benedito" | 2ª ✓ | ponto gravado (−26,89134, −49,23557). O Luís Alves não tem ponto e o chat diz isso |
| "comparar as réguas de Itajaí" | 2ª ✓ | lado a lado com hora e referência; nunca subtrai referências diferentes |
| "copiar resumo desta cidade" | 2ª ✓ | `textoParaCompartilhar` (D4: sem endereço, com hora, sem ordem de ação) |
| "copiar link desta visualização" | 2ª ✓ | `#/monitor/…?regua=…&fundo=…`. **Atenção:** o site só abre para e-mail cadastrado, e isso tem de vir escrito junto |
| "mostrar a rua X, Itajaí" + destaque | 3ª ✓ | traçado real da via (GeoItajaí); escolha entre homônimos |
| "rua X, Gaspar/Brusque" | 3ª ✓ | só ponto: "localização aproximada; traçado da rua indisponível" |
| "rua X, Blumenau/Rio do Sul" | dado | só a cota; sem ponto no mapa (decisão 3) |
| "manchas na rua X" com rua em outra cor | 3ª ✓ | ver abaixo |
| "relatar problema nesta régua" | 4ª ✓ | não há canal: o chat prepara o texto para a pessoa copiar |
| "usar minha localização" | 4ª ✓ | só com permissão pedida na hora; nada é guardado nem enviado |
| "tela cheia" | 4ª ✓ | o navegador exige toque no botão; o chat aponta o botão |
| evacuar ou ficar, "é seguro?", previsão de hora exata | não | barreira do presente: dado, hora e 199 |

## Rua destacada sobre as manchas (3ª entrega — saiu em 06/10/2026, ver o fim do documento)

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

### O que ficou para depois (dependências)

- **Segunda entrega:** saiu em 06/10/2026 (seção abaixo).
- **Rua no mapa e rua sobre as manchas:** saíram na 3ª entrega (fim do documento). Blumenau e Rio do Sul
  continuam sem ponto no mapa, porque a fonte não publica a coordenada.
- **Relatar problema, localização e tela cheia:** saíram na 4ª entrega (fim do documento).

## Segunda entrega (06/10/2026): o que saiu

Os dez pedidos da matriz marcados com ✓. Mesmo desenho da 1ª entrega: o texto só propõe um passo tipado
(`comandos/tipos.ts`), tudo é resolvido contra o cadastro, e o chat diz o resultado real.

### Os pedidos

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "quais leituras estão atrasadas?" | Lista as réguas municipais em dia, atrasadas (90 min a 3 h; Blumenau, 2 h), velhas e sem horário, com a hora e a idade de cada uma. Inclui a rede da Defesa Civil de SC e as estações que não publicaram nível. | Mostrar o número da leitura atrasada. Contar primária e resgate como duas réguas. |
| "mostrar só as réguas sem leitura", "limpar filtros" | Filtro no Monitor: some o pino e a régua com leitura de agora (municipal, estadual ou uma régua da cidade), e o mapa enquadra a bacia inteira. A tela escreve "Filtro: …" com "Limpar filtro". | Mudar cor, faixa ou número. Ligar o filtro quando todos têm leitura (diz isso). |
| "gráfico de Blumenau", "abrir o gráfico desta régua" | Abre a página da cidade em `?secao=grafico`, que rola até "Últimas horas". | Em Itajaí, inventar um gráfico só: abre a foz e oferece "comparar as réguas". |
| "o que mudou na última hora?" | Variação de UMA régua: de quanto a quanto, em quantas medições, o passo e as lacunas. Blumenau usa a publicação mais fresca, sem fundir; com série horária, compara com a medição anterior se ela tem até 90 min. | Responder com série velha (diz a hora da última). Juntar réguas de Itajaí (pergunta qual). Chamar de previsão. |
| "de onde vem esse traçado?" | Fonte, número de trechos, cobertura e **a data da base do OSM**, com o bruto de origem. | Confundir traçado com mancha. |
| "o que fica a montante daqui?", "afluentes deste trecho" | Tronco acima, cabeceiras, Trombudo (sem posição na árvore) e afluentes, pela `_topologia`. O Benedito sai com o ponto que o cadastro escreve; em Indaial ele aparece como "logo depois da régua". | Dizer antes/depois de uma régua quando o cadastro só diz "perto de". Sugerir que a água "vai chegar". |
| "ver a confluência do Benedito", "onde nasce o Itajaí-Açu?" | Centra e marca o ponto gravado (anel branco, "Marca: …" com "Tirar marca") e diz a coordenada e como ela foi medida. | Marcar ponto estimado: Luís Alves, Hercílio, Rio dos Cedros e Guabiruba respondem que não há ponto gravado. |
| "comparar as réguas de Itajaí" | As onze lado a lado, em ordem de código, cada uma com hora, idade e faixa. | Subtrair, ordenar por metro ou dar faixa a leitura velha. |
| "copiar resumo desta cidade" | O texto de compartilhar (D4) com o botão "Copiar". | Sair sem leitura de agora. Levar o endereço do site. Enviar sozinho. |
| "copiar link desta visualização" | O endereço com `?regua=` e `?fundo=`, mais o aviso de que o site só abre para e-mail cadastrado. | Enviar sozinho. |

### Dados e código

- **A data da base do traçado** morava só no bruto. `scripts/converter_tracado_rios.py` agora grava em cada
  arquivo de `data/rios/` a propriedade `origem: [{bruto, base_osm}]`. A geometria não mudou: o conversor foi
  rodado de novo e comparado arquivo por arquivo. Teste em `scripts/teste_converter_tracado_rios.py`
  (`OrigemDoTracado`). Os rios de Ibirama mostram base de 06/05/2026, do espelho atrasado; o chat diz a data
  como está.
- **Confluências** (`comandos/catalogo.ts`): só as gravadas no cadastro — `confluencia_cabeceiras`,
  `rio_chega_a` do Trombudo e a coordenada que o `ponto_exato` do Benedito escreve (lida do texto, travada
  por teste). Os outros rios entram em `semPonto`, com o motivo.
- **Respostas** em `comandos/respostas.ts` (funções puras) e `comandos/rios.ts`. O resumo para copiar sai de
  `compartilharDaCidade` (`chat-local/situacaoAgora.ts`), o mesmo texto de "como está X?".
- **Leituras ao vivo:** o chat espera a primeira busca terminar (até 12 s); sem dado, diz que não conseguiu.
- **No celular**, a conversa só recolhe depois de pedido que mexe no mapa. Resposta de leitura ou de cópia fica
  aberta.

### No Monitor (com o rótulo `monitor-autorizado`)

- `filtro` e `marca` no estado, com aviso escrito e botão para tirar; os dois entram no retrato de "voltar".
- A ponte ganhou `filtrar` e `marcarPonto`. `pronto`, o enquadramento e o `?regua=` olham os pinos sem filtro.
- A regra do filtro está em `logica/filtroSemLeitura.ts`, com teste.
- Desligados, o Monitor é o de antes: `trava-monitor` passa com a referência atual.

### Testes

- `src/comandos/segunda.test.ts` (24): cadastro e confluências; frases que viram pedido e perguntas que
  continuam perguntas; cada resposta, inclusive o que ela não pode dizer; o executor com Monitor e dados falsos.
- `testes-navegador/chat-comandos.mjs`, seção 3, em 390 e 1280 px: link, filtro, confluência, Luís Alves,
  traçado, montante, leituras atrasadas e gráfico.
- Sonda manual com os dados reais do branch `tempo-real` (06/10/2026, 14h): 17 de 17 réguas municipais em dia;
  Rio do Sul +5 cm na última hora; as onze de Itajaí lado a lado; filtro com Lontras, Apiúna e Indaial (as três
  sem leitura estadual utilizável); resumo de Rio do Sul pronto para copiar.

## Terceira entrega (06/10/2026): a rua no mapa

O plano da seção "Rua destacada sobre as manchas", com as regras dela. Nada é geocodificado na hora: só entra no
mapa o que a fonte publicou com geometria.

### Os pedidos

| Pedido | Itajaí | Gaspar e Brusque | Blumenau, Rio do Sul e outras |
|---|---|---|---|
| "mostrar a rua X", "zoom na avenida Y", "onde fica a rua Z em Gaspar" | Abre o mapa das manchas com o **traçado real** da via (base de vias da Prefeitura) destacado, e diz a interseção com cada cenário. | Abre o Monitor da cidade e marca **os pontos de cota** da rua (um anel por ponto, nenhuma linha entre eles), com a cota de cada um na régua da cidade e o aviso "localização aproximada; traçado da rua indisponível". | Diz que a rua tem cota, mas a fonte não publica a coordenada. O mapa não muda; sugere a pergunta da cota. |
| "manchas na rua X", "mancha de 2008 na rua X" | Destaca a rua e, com o ano, troca o cenário. Sem ano, com várias cheias cruzando a rua, **pergunta qual cenário mostrar** em vez de trocar. | — | — |
| "remover destaque", "tirar a marca" | Tira a rua do endereço e do mapa. | Tira os anéis do Monitor. | — |

- **Homônimos:** a base de Itajaí tem "R." e "Av." com o mesmo nome (Carlos Drumond de Andrade, Jorge Mattos…).
  O tipo escrito pela pessoa ("rua", "avenida") decide; sem ele, o chat pergunta qual, e nada é marcado antes.
- **Sem cidade no pedido:** vale a cidade da tela, se a rua estiver lá. Senão, o chat procura em Itajaí,
  Gaspar e Brusque e pergunta se achar em mais de uma.
- **Interseção, nunca alagamento:** "Interseção com o cenário de novembro de 2008: 32% do trecho (727 m)
  dentro da mancha". Rua fora da mancha "não quer dizer rua segura". O texto sai de
  `manchas/itajai/ruas-por-mancha.json`, o mesmo cruzamento do chat de perguntas (corte de 10 m).

### O destaque no mapa das manchas (`componentes/MapaManchas.tsx`)

- **Aparência:** linha magenta (`#ff3db8`) com contorno escuro, num pane próprio acima das manchas (z 450). A
  escala azul de profundidade não muda.
  - O nome da rua vai escrito sobre a linha.
  - A legenda diz "rua selecionada, destaque de localização", e que o destaque não indica risco.
  - O contorno escuro foi conferido nos três fundos.
- **O endereço manda:** `?rua=<nome na base>&cenario=<evento>`.
  - A busca da própria página (`BuscaViaItajai`) grava o mesmo `?rua=`, então o destaque é um só, com o chat
    ou sem ele.
  - O link leva o destaque junto, e "voltar ao mapa de antes" o restaura.
- **Comportamento:**
  - trocar de cenário mantém a rua e o enquadramento dela;
  - "Remover destaque" tira só a rua;
  - sair de Itajaí limpa, porque o endereço é outro.
- **Base de vias:** `dados/viasItajai.ts` baixa a base uma vez por página e a reparte entre a busca e o chat.

### No Monitor (rótulo `monitor-autorizado`)

- A marca do chat (`marcarPonto`) aceita vários pontos (`extras`) e a largura da vista (`km`): os pontos de cota
  de uma rua de Gaspar ou Brusque entram juntos, centrados no meio deles.

### Testes

- `src/comandos/terceira.test.ts` (11), com as bases de verdade: casar nomes e homônimos; frases que viram
  pedido e as que continuam pergunta ("Rua XV de Novembro, Blumenau", "a rua X alagou em 2011?"); os textos
  de interseção e de ponto; o executor com Itajaí, Gaspar, Blumenau, "remover destaque" e "voltar".
- `testes-navegador/chat-comandos.mjs`, seção 4: o endereço, o traço magenta, a legenda, o nome escrito, a
  troca de cenário com a rua mantida, a interseção, "remover destaque", a marca de Gaspar e Blumenau sem
  mexer no mapa.

## Quarta entrega (06/10/2026): o aparelho da pessoa

O plano não tinha uma 4ª entrega. Ela juntou o que tinha sobrado da matriz (relatar problema, localização,
tela cheia) com comandos para as preferências que o site já guarda no aparelho (minha cidade, cidades
seguidas, letra).

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "usar minha localização", "qual a régua mais perto de mim?" | O navegador pede permissão. O chat diz a régua mais perto **em linha reta** e as duas seguintes, abre o Monitor da cidade mais perto e marca a posição ("Você está aqui, aproximado; não fica guardado"). Itajaí entra pelas onze réguas dela. Avisa quando a posição veio imprecisa (> 2 km), quando a régua mais perto é de coordenada não confirmada (Timbó) e quando a pessoa está fora da área (> 25 km). | Gravar a posição, pô-la no endereço ou enviá-la a qualquer lugar. Dizer que a água chega (ou não) até a pessoa: distância em linha reta não é previsão. |
| permissão recusada, aparelho sem posição, demora | Diz o porquê e como permitir. A espera tem limite de 25 s, contando a pergunta do navegador: sem resposta, o chat não fica preso em "Executando…". | Mexer na tela. |
| "relatar problema nesta régua", "essa leitura está errada" | Prepara o texto: quando (hora de Brasília), a tela (Monitor, régua, caminho), o que o site mostra agora e o espaço "O problema: …", com o botão "Copiar". Diz que não há canal e para quem mandar. | Enviar. Pôr o endereço do site. Tratar relato como alerta: se a água está subindo, 199. |
| "minha cidade é Gaspar", "definir Rio do Sul como minha cidade" | A mesma preferência do Início ("Minha cidade"). Diz se não deu para guardar (navegação anônima). | Aceitar cidade fora do cadastro. |
| "seguir Blumenau", "deixar de seguir", "quais cidades eu sigo?" | A lista do Início, no máximo quatro; com a lista cheia, pede para tirar uma. | Trocar uma cidade seguida por conta própria. |
| "letra maior", "letra normal" | A mesma preferência do botão de letra. No Monitor avisa que o mapa não muda. | — |
| "tela cheia" | Aponta o botão "Tela cheia" (no Monitor) ou o link para o Monitor. | Abrir sozinho: o navegador exige o toque da pessoa. |

- **Código:**
  - `comandos/aparelho.ts`: distância, régua mais perto e os textos;
  - `logica/preferencias.ts`: ganhou `seguir`;
  - a posição vem de `navigator.geolocation`, uma vez por pedido (`usarComandos.ts`);
  - as preferências avisam as telas abertas (`avisarPreferencias`).
- **Testes:**
  - `src/comandos/quarta.test.ts` (9): textos, frases e executor;
  - `testes-navegador/chat-comandos.mjs`, seção 5: localização simulada no Chromium, com e sem permissão; a
    posição fora do endereço e do aparelho; minha cidade guardada; relato com "Copiar"; letra.


## Quinta entrega (06/10/2026): o tempo e a bacia

A 5ª entrega dá ao chat o tempo (a reprodução das últimas horas, que o Monitor já tinha em botão e barra) e o
resto da bacia que as telas já mostram: chuva, barragens, maré e a origem de cada leitura. Nenhum número novo:
tudo vem das mesmas fontes e regras das telas.

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "reproduzir as últimas 24 h", "pausar" | Os mesmos estados do botão "Reproduzir 24 h" do Monitor. Diz de quando a quando vai a série e que é o medido, não previsão. | Tocar no Monitor de Ascurra, que não tem reprodução. Inventar série onde não há. |
| "como estava às 14h", "voltar 3 horas" | Põe o mapa no último instante da série até aquela hora (hora de Brasília; hora que ainda não chegou hoje é a de ontem), com cada cidade na última leitura até ali. Diz "passado, não agora". | Ir para antes do começo da série: diz desde quando ela cobre. Mostrar leitura posterior ao instante. |
| "ir para a leitura mais recente", "parar a reprodução" | Volta ao vivo. | — |
| "onde está chovendo mais?" | Os pluviômetros com leitura que não é velha, do maior acumulado de 1 h para baixo (sem chuva na última hora, pelo de 24 h), até seis cidades, com quantos pluviômetros e a hora. Diz quantas cidades ficaram de fora por leitura velha e que a fonte não publica 6 h. | Contar leitura velha. Dizer que chuva forte quer dizer cheia ali. |
| "como estão as barragens?" | O estado das comportas e o percentual de uso do reservatório **como a fonte publica**, com hora e idade. Acima de 60 min, "pode ter mudado desde então". | O nível da barragem em metros (zero próprio, 339–370 m de altitude). Veredito sobre a cheia: comporta aberta não quer dizer que a cheia passou. |
| "como está a maré?", "quando é a próxima preamar?" | Pela tábua da Marinha (porto de Itajaí): subindo ou baixando agora, a próxima preamar e a próxima baixamar com a altura da tábua, e a sizígia. Atalho para `/itajai`. | Chamar previsão astronômica de medição. Dizer que maré alta é cheia: ela dificulta o escoamento na foz. |
| "de onde vem essa leitura?", "de onde vem a leitura de Blumenau?" | As estações municipais da coleta, com a hora da medição e a de resgate quando for o caso; a estação estadual, com "zero próprio"; as fontes de tempo real do cadastro. Atalho para a aba Fontes da cidade. | Trocar a hora da medição pela da coleta. |

- **Código:**
  - `comandos/bacia.ts`: os textos de chuva, barragens, maré e fonte, e `instantePedido` (a hora pedida em
    Brasília);
  - `comandos/ponte.ts`: `reproducao` (tocar, pausar, ir a um instante);
  - `comandos/executar.ts`: os passos `reproducao`, `chuva_agora`, `barragens`, `mare` e `fonte_leitura`; a
    reprodução muda a tela e precisa do mapa;
  - `comandos/usarComandos.ts`: busca as barragens só quando o pedido chega; a tábua de maré já vem com o site
    (`mareItajai`).
- **No Monitor (rótulo `monitor-autorizado`):** `MonitorBacia.tsx` registra `reproducao` na ponte, sobre os
  mesmos `grade`, `idxRepro` e `tocando` do botão e da barra. Sem pedido, nada muda: a `trava-monitor` passa
  com a referência atual.
- **Defeito achado no caminho:** "parar a reprodução" não era reconhecido pela 1ª entrega; agora volta ao vivo.
- **Testes:**
  - `src/comandos/quinta.test.ts` (9): frases, `instantePedido`, chuva, barragens, maré com a tábua real
    (06/10, 15h00: baixando; próxima preamar 22h59, 0,85 m; baixamar 18h49, 0,42 m), fonte e executor;
  - `testes-navegador/chat-comandos.mjs`, seção 6: reproduzir, pausar, "voltar 3 horas" e voltar ao vivo no
    Monitor de Blumenau; maré, chuva, barragens (sem metros) e fonte da leitura.

## Sexta entrega (06/10/2026): o rio agora, de cima a baixo

O plano original acabou na 5ª entrega; só falta a rua de Blumenau e de Rio do Sul no mapa, que depende de dado.
A 6ª dá ao chat as contas que o cartão "Agora", o painel e o tempo de descida já fazem na tela, e liga no
Monitor um segundo filtro. Nenhum número novo: nada aqui é calculado fora das funções que as telas usam.

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "quanto falta para a cota de alerta em Blumenau?", "quanto falta para a próxima cota?" | A frase do cartão "Agora" (`situacaoNasCotas`): quanto está acima da última cota alcançada e quanto falta para a próxima, com o nome da Defesa Civil da cidade (D6: "Observação", "Alerta Máximo") e a hora da medição. | A conta sobre leitura que não é de agora. A conta em Gaspar ("maior que"), Ascurra (C18) e Itajaí (várias réguas): diz por quê. Usar a régua estadual (zero próprio) contra as cotas da cidade. |
| "o rio está subindo ou descendo?", "Blumenau está subindo?", "qual a tendência em Brusque?" | A seta do cartão (D7, `tendenciaDaLeitura`): cm/h na última hora medida, só quando o último ponto da série é a leitura e é de agora. Leitura antiga com a série subindo: "agora pode estar mais alto", como no cartão. | Dizer tendência com série que não casa com a leitura, nem juntar réguas de Itajaí. "Vai subir?" continua na barreira do presente. |
| "máximo das últimas 24 h em Blumenau", "pico de hoje" | Máximo e mínimo da série publicada de UMA régua, com a hora de cada um, e a variação do primeiro ao último ponto. Diz quando o último ponto é velho. | Misturar réguas (Itajaí pede para escolher uma). Ponto com mais de 24 h. |
| "quais cidades estão em alerta?", "como está a bacia?" | A faixa de cada cidade na régua dela, da mais alta para a mais baixa, com o número e a hora com a idade. Mostra também: as réguas de Itajaí com cor; à parte, a faixa da Defesa Civil de SC, onde não há leitura municipal de agora; e as cidades sem cor. | Dizer que está tudo calmo. Sem nada acima do normal, diz que faixa baixa no rio não quer dizer que não há alagamento. Pôr Itajaí como cidade de um número só. |
| "o que vem de cima para Blumenau?", "como estão as cidades de cima?" | As cidades acima pela árvore do cadastro, da mais perto para a mais longe, e as cabeceiras e os afluentes com régua. Cada uma traz a leitura de agora (ou a estadual, com "zero próprio") e o tempo de descida em intervalo, pelo mesmo `caminho()` da tela. Itajaí recebe as duas seções, Açu e Mirim. | Tempo de descida para afluente ou trecho sem dado ("sem tempo no cadastro", "em estudo"). Chamar ligação de previsão. Comparar metros entre cidades. |
| "mostrar só as cidades em alerta", "só as cidades acima do normal" | Filtro no Monitor: só pinos e réguas com a faixa do mapa de monitoramento para cima, escrito na tela, com "Limpar filtro". O mapa abre na bacia inteira. | Contar cinza, "várias réguas" ou régua de estuário sem cor. Ligar o filtro vazio: diz que nada está acima e que isso não é sinal de segurança. |

- **Código:**
  - `comandos/rioAgora.ts`: os textos de quanto falta, tendência, máximo de 24 h, panorama e "de cima";
  - `logica/filtroSemLeitura.ts`: `faixaAcimaDoNormal`;
  - `comandos/executar.ts`: os passos `quanto_falta`, `tendencia`, `maximo_24h`, `panorama`, `de_cima` e o filtro
    `acima_do_normal`; o tempo de descida chega por `DadosDoChat.transito` (`transito.json`, com os trechos em
    estudo).
- **No Monitor (rótulo `monitor-autorizado`):** `MonitorBacia.tsx` aceita o filtro `acima_do_normal` na ponte,
  esconde os outros pinos e réguas e escreve o filtro na tela. Sem pedido, nada muda: a `trava-monitor` passa com
  a referência atual.
- **Testes:**
  - `src/comandos/sexta.test.ts` (10): frases, cada texto com o cadastro real (cotas de Blumenau, árvore, `transito.json`),
    as recusas (Gaspar, Ascurra, Itajaí, leitura velha), a faixa estadual só à parte e o executor;
  - `testes-navegador/chat-comandos.mjs`, seção 7: panorama, filtro ligado e limpo (ou a recusa sem nada acima),
    "de cima", quanto falta, tendência, máximo de 24 h e Gaspar sem frase de cota.

## Sétima entrega (06/10/2026): a foz e o que o mapa quer dizer

A 7ª traz para o chat o painel "Chegada do pico × maré em Itajaí" e a legenda do Monitor, mais dois botões do
Monitor que o chat ainda não alcançava. Dois painéis ficaram de fora de propósito, porque não aparecem em
nenhuma tela: `PainelSePicoAgora` (chegadas a jusante "se o pico fosse agora") e `prever()` (estimativa a jusante
por regressão). Pôr esses números no chat seria mostrar algo que o site não mostra.

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "o pico de Blumenau já passou?", "quando a cheia chega em Itajaí?", "a cheia vai pegar maré alta?" | O "Hoje" do painel de Itajaí, pela MESMA decisão da tela (`logica/hojeEmItajai.ts`, extraída do componente). Diz se o pico passou (com o platô), se não está confirmado, se o rio ainda sobe (aí a janela é a de "se o pico fosse agora") ou se Blumenau está abaixo da primeira cota. Junto vêm a janela de chegada pela referência de estudo da JICA e as marés da tábua dentro dela. | Chamar a janela de previsão. Mostrar como futura uma janela que já terminou. Dizer que a coincidência com a maré alaga ou não alaga. |
| "se o pico de Blumenau for às 22h", "se o pico em Blumenau for amanhã às 3h30" | A simulação do formulário (`simularChegada`) com o horário informado, em hora de Brasília (hoje, se o dia não vem). | Tratar a última leitura como pico. |
| "o que significa a cor laranja?", "o que é alerta máximo?", "por que o trecho está tracejado?", "por que a água se mexe?", "explicar as cores" | Os textos de `data/faixas.json` (fonte única) e das notas da legenda do Monitor: cor, tracejado (faixa estadual), violeta (nível bruto estadual), azul (mar, chuva, várias réguas), ondas (sentido ilustrativo, velocidade constante), seta e régua sem faixa. Fecha com "cor é faixa, não metro". | Escrever texto de faixa à mão, fora de `faixas.json`. Dizer que cinza é seguro. |
| "pausar as animações", "retomar animações" | O botão "Pausar/Retomar animações" da legenda do Monitor. Avisa quando o aparelho pede movimento reduzido. | Confundir com a reprodução: "pausar" e "pausar a animação" continuam pausando a reprodução (5ª entrega). |
| "abrir a legenda", "recolher a legenda" | O "abrir/recolher" da legenda do Monitor. | — |

- **Código:**
  - `logica/hojeEmItajai.ts`: a decisão do "Hoje", usada pelo `SimulacaoChegada` e pelo chat;
  - `comandos/foz.ts`: os textos da chegada, da simulação e da legenda;
  - `comandos/executar.ts`: os passos `chegada_itajai`, `simular_chegada`, `legenda`, `animacoes` e
    `legenda_mapa`; a referência de estudo chega por `DadosDoChat.referenciaChegada`.
- **No Monitor (rótulo `monitor-autorizado`):** `MonitorBacia.tsx` registra `animacoes` e `legendaDoMapa` na
  ponte, sobre os mesmos `animacoesPausadas` e `legendaAberta` dos botões. Sem pedido, nada muda: a
  `trava-monitor` passa com a referência atual.
- **Testes:**
  - `src/comandos/setima.test.ts` (8): frases, cada ramo do "Hoje" com séries montadas, os textos com a tábua real,
    a simulação, a legenda e o executor;
  - `testes-navegador/chat-comandos.mjs`, seção 8: chegada, simulação, legenda, e os botões de animação e legenda
    mudando de estado no Monitor;
  - `simulacao-chegada.mjs` continua passando com o painel usando a função extraída. Com os dados reais de
    06/10, o chat e o painel de `/itajai` deram a mesma janela (06:00 a 11:00 de 07/10, Blumenau subindo).

## Oitava entrega (06/10/2026): o site e os seus dados

A 8ª entrega cobre o que a pessoa pergunta sobre o próprio site durante a cheia: se o número é o mais novo, se o
site é oficial, como tê-lo no celular, o que ele guarda e para quem ligar. Não toca em arquivo do Monitor.

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "atualizar as leituras", "tem leitura nova?" | Antecipa a próxima busca dos três arquivos de tempo real (leituras, rede estadual, série) em todas as telas abertas (`dados/atualizar.ts`, um evento que os ganchos já existentes escutam). Espera a resposta, por no máximo 10 s, e diz se a coleta é nova ou a mesma, e a hora da medição mais nova. Um pedido a cada 30 s. | Forçar a coleta das fontes (ela roda no servidor) nem prometer leitura nova. Tratar leitura velha como nova. |
| "isso é oficial?", "ler o aviso" | O texto do aviso de toda tela (`AvisoLegal`). | — |
| "telefone de emergência", "para quem devo ligar?" | 199 e 193, os números da faixa de toda tela. | Dar telefone que o site não tem cadastrado. |
| "como instalar o aplicativo?" | O caminho do aparelho: iPhone (Compartilhar → Tela de Início), o botão "Instalar" do Início quando o navegador oferece, ou o menu do navegador. Lembra que, sem internet, o número guardado sai com a hora da medição. | Instalar sozinho: o navegador exige o toque da pessoa. |
| "o que o site guarda de mim?" | As preferências deste aparelho, lidas na hora (cidades, letra, aviso lido, contagem do chat), e o que não é guardado (localização, conversa). | — |
| "apagar minhas preferências" → "sim, apagar minhas preferências" | Pede confirmação; confirmado, apaga as quatro chaves do aparelho (`esquecerPreferencias`) e a letra volta ao normal. | Apagar sem a confirmação. |
| "não contar minhas perguntas", "pode contar minhas perguntas" | A mesma escolha da caixa "Contar as perguntas que o chat não entender", que passa a acompanhar a mudança. | — |
| "limpar a conversa" | O mesmo "Limpar" do painel. | — |

- **Código:**
  - `comandos/site.ts`: os textos;
  - `dados/atualizar.ts`: o pedido de busca, com o limite de 30 s; `useTempoReal`, `useNivelSc` e
    `useSerieRecente` escutam;
  - `logica/preferencias.ts`: `esquecerPreferencias` e `temMemoria`;
  - `dados/modoAplicativo.ts`: `podeInstalar`;
  - `ChatLocal.tsx`: a caixa da contagem acompanha a escolha feita pelo chat.
- **Testes:**
  - `src/comandos/oitava.test.ts` (8): frases, o limite de 30 s, os textos, apagar com armazenamento bloqueado, e o
    executor (nada é apagado sem confirmar);
  - `testes-navegador/chat-comandos.mjs`, seção 9: aviso, atualizar, privacidade, apagar (a cidade sai do
    `localStorage` só depois de confirmar), contagem gravada como `nao`, emergência e conversa limpa;
  - sonda com os dados do branch `tempo-real`: "atualizar" disparou a busca dos três arquivos em cada tela aberta,
    e um segundo pedido em menos de 30 s não disparou nenhuma.

## Nona entrega (06/10/2026): nome de cidade com erro de digitação

Quem digita no celular, na chuva, escreve "Blumenal" ou "Rio do Sol". O chat só casava o nome exato: o comando
não era reconhecido e a pergunta caía na resposta genérica. A 9ª entrega troca isso por uma pergunta de volta.
Não toca em arquivo do Monitor.

| Caso | O que faz | O que nunca faz |
|---|---|---|
| comando: "mostrar Blumenal", "quanto falta para a cota em Rio do Sol?", "mostrar Blumenal e satélite" | Se a frase com o nome corrigido vira comando, responde "Não achei a cidade "Blumenal". Você quis dizer Blumenau? Nada foi feito" e oferece a frase corrigida como sugestão. Tocar nela executa o pedido certo. | Executar o palpite sozinho. |
| pergunta: "como está blumenal?", "cheias de brusqe" | O motor responde o que foi escrito, como antes. Antes da resposta, o chat diz "Você quis dizer Blumenau?" e põe a pergunta corrigida como primeira sugestão. Vale também em `/perguntas` e na aba Histórico. | Responder pela cidade do palpite sem a pessoa tocar. |

- **As regras que seguram o palpite** (`comandos/corrigir.ts`):
  - se a frase já tem um nome conhecido exato, não há correção;
  - nome de até 4 letras (Taió) não é corrigido; 5 a 7 letras aceitam 1 diferença; 8 ou mais, 2;
  - o trecho precisa estar onde cabe um nome de cidade: no começo, depois de "em", "de", "está", "mostrar" e afins,
    ou com maiúscula. Assim "levei um tombo" não vira Timbó e "gastar" não vira Gaspar, e essas palavras também
    estão numa lista curta que nunca é corrigida;
  - perto de dois nomes, nenhum palpite;
  - na pergunta, a lista de nomes inclui os municípios do Atlas que o motor conhece: "Pomerode" nunca vira erro
    de digitação de outra cidade.
- **Prova de falso positivo:** o corretor rodou sobre as 2.744 frases dos testes do chat e da prova. Só houve
  palpite em erros de digitação de verdade, já escritos nos testes ("blumenal", "Rio do Sol").
- **O motor não muda:** a prova do chat (`chat-ia/prova`) responde igual. O "Você quis dizer" é acrescentado pela
  tela do chat (`ChatLocal.tsx`) e pelo interpretador de comandos.
- **Testes:**
  - `src/comandos/nona.test.ts` (5): distância, acertos, recusas (nome exato, curto, palavra comum, fora da posição,
    longe, dois nomes, município do Atlas), comando e pergunta;
  - `testes-navegador/chat-comandos.mjs`, seção 10: "mostrar Blumenal" não muda a tela, e a sugestão abre o Monitor
    de Blumenau; "como está blumenal?" traz o palpite e a pergunta corrigida como sugestão.

## Décima entrega (06/10/2026): a conversa que continua

"Como está Blumenau?" e depois "e Gaspar?". O chat lia cada mensagem sozinha, e "e Gaspar?" virava "Gaspar" solto.
Agora três continuações curtas refazem o último pedido da conversa com uma troca só. Não toca em arquivo do
Monitor.

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "e Gaspar?", "e em Rio do Sul?", "e lá em Ilhota?" | Refaz o último pedido com a cidade trocada, na frase como foi escrita ("quanto falta para a cota em Rio do Sul?"). Mostra antes "Entendi como: …". Vale para pergunta e para comando ("mostrar Blumenau" → "e Gaspar" abre o Monitor de Gaspar). | Adivinhar: sem pedido anterior, pergunta o que saber da cidade; se o pedido anterior cita duas cidades ("de Rio do Sul até Blumenau"), pergunta qual trocar; se não cita cidade, pede o pedido inteiro. Tratar "Itajaí-Açu" ou "Itajaí-Mirim" como a cidade de Itajaí. |
| "e em 2011?" | O último pedido com o ano trocado ("cheias de 2008 em Blumenau" → "cheias de 2011 em Blumenau"). | Trocar quando o pedido anterior não tem ano ou tem mais de um. |
| "de novo", "repetir" | O mesmo pedido de novo (por exemplo, para ver a leitura mais nova). | — |

- **Encadeado:** "e Gaspar?" depois de "e Rio do Sul?" parte do pedido já refeito, guardado na mensagem
  (`Msg.entendidoComo`), e não do "e Rio do Sul?" solto.
- **O mesmo caminho do que é digitado:** o pedido refeito passa pelo interpretador de comandos e pelo motor como
  qualquer outro, com a barreira do presente e o "Você quis dizer" da 9ª entrega. A mensagem da pessoa aparece
  uma vez só, como foi escrita.
- **O que não é continuação:** "e agora?", "e se chover?", cidade fora da lista ("e Pomerode?" segue para o
  motor), e a pergunta inteira ("como está Gaspar?").
- **Código:** `comandos/continuar.ts` (pura), `ChatLocal.tsx` (a ligação e o "Entendi como"), `conversa.ts`
  (`entendidoComo`) e `usarComandos.ts` (`tentar` sem repetir a mensagem).
- **Testes:**
  - `src/comandos/decima.test.ts` (5): troca de cidade e de ano, repetir, as perguntas em vez de palpite, o que não é
    continuação e o pedido refeito virando comando;
  - `testes-navegador/chat-comandos.mjs`, seção 11: sem pedido anterior, "Entendi como" depois de "quanto falta…",
    "de novo" e "e Gaspar" abrindo o Monitor de Gaspar.

## Décima primeira entrega (06/10/2026): as palavras do rio e a resposta em voz alta

O público do site não é técnico, e as respostas usam palavras como cota, jusante, preamar e zero da régua. A 11ª
entrega explica essas palavras e lê a resposta em voz alta para quem tem dificuldade de ler na tela. Não toca em
arquivo do Monitor.

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "o que é cota?", "o que significa jusante?", "o que é o zero da régua?", "o que quer dizer sizígia?" | Explica a palavra como ela vale neste site (`comandos/glossario.ts`), com sugestões de pedidos ligados a ela ("quanto falta para a cota em Blumenau?"). | Dar conselho, ou explicar sem as regras do site: cada régua com o seu zero, faixa não é metro, tempo de descida em intervalo, leitura velha não é de agora. |
| "qual a diferença entre enchente e alagamento?" | Os dois verbetes, ou um só quando os dois termos são o mesmo verbete. | — |
| "que palavras você explica?" | A lista dos 18 verbetes. | — |
| "ler em voz alta", "parar de ler" | A voz do próprio navegador (`speechSynthesis`) lê a última resposta, com as unidades por extenso ("4,80 metros", "12 centímetros por hora", "7 a 10 horas"). | Mandar o texto a servidor do site. Travar a tela quando o navegador não tem voz: o chat diz que não há e lembra do leitor de tela do aparelho. |

- **Verbetes (18):** régua; zero da régua; nível; cota (com cota de rua); faixa; montante e jusante; afluente;
  foz; preamar e baixamar; sizígia; estuário; pluviômetro e milímetro de chuva; pico e platô; tempo de
  descida; nível bruto da rede estadual; barragem de contenção; cheia, enchente, inundação e alagamento;
  Defesa Civil e AlertaBlu. Cada um fecha com o 199.
- **A legenda continua sendo a da 7ª entrega:** "o que é alerta?" e "o que significa a cor laranja?" respondem
  pelos textos de `faixas.json`. O glossário atende só as palavras que não são nome de faixa. Palavra que o
  glossário não tem segue para o motor de perguntas.
- **Código:** `comandos/glossario.ts`, `comandos/fala.ts` (o texto para a voz) e a voz em `usarComandos.ts`
  (`lerEmVoz`).
- **Testes:**
  - `src/comandos/decimaprimeira.test.ts` (4): frases, a legenda que continua na 7ª, verbetes com as regras do
    site, o texto para a voz e o executor com e sem voz no navegador;
  - `testes-navegador/chat-comandos.mjs`, seção 12: cota, enchente × alagamento, "ler em voz alta" e
    "parar de ler".

## Décima segunda entrega (06/10/2026): o Monitor, peça por peça

A 12ª entrega dá ao chat as últimas peças do Monitor que só se alcançavam com o dedo: enquadrar um rio inteiro
ou as barragens, fechar o painel da cidade e abrir ou fechar o menu de cidades.

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "ver o Itajaí-Mirim no mapa", "zoom no Itajaí-Açu", no Monitor "mostrar o Itajaí-Mirim" | Enquadra as cidades com régua do rio (com os afluentes) pelo mesmo `vistaQueCabeAsReguas` do pino da cidade. Diz quantas são e que cada cor é a faixa da cidade na régua dela. | Mudar a página fora do Monitor: lá, "mostrar o Itajaí-Açu" continua abrindo a página do rio (1ª entrega). |
| "zoom nas barragens", "mostrar as barragens no mapa", "onde ficam as barragens?" | Enquadra os marcadores das barragens. Sem posição (fonte fora do ar), diz isso e aponta "como estão as barragens?". | Responder o estado das comportas aqui: isso é da 5ª entrega. |
| "fechar o painel" | Fecha o painel da cidade; o mapa fica onde está. | — |
| "abrir o menu de cidades", "fechar o menu" | O botão "Cidades ▾" do topo. | Existir no Monitor de Ascurra, que não tem menu. |

- **"No mapa":** o chat tirava "no mapa" do fim da frase como cortesia. Agora o pedido do rio e das barragens é lido
  no texto inteiro antes disso, e "ver o Itajaí-Mirim no mapa" de qualquer página abre o Monitor no rio.
- **No Monitor (rótulo `monitor-autorizado`):** `MonitorBacia.tsx` registra `enquadrar`, `fecharPainel` e
  `menuDeCidades` na ponte, sobre os mesmos `setVista`, `sel` e `menuAberto` dos botões. Sem pedido, nada muda:
  a `trava-monitor` passa com a referência atual.
- **Testes:**
  - `src/comandos/decimasegunda.test.ts` (3): frases (com "no mapa" e com o contexto do Monitor), o executor
    abrindo o Monitor e usando a ponte, a ajuda;
  - `testes-navegador/chat-comandos.mjs`, seção 13: o painel fecha de verdade, o menu abre e fecha, o Itajaí-Mirim
    enquadrado, as barragens.

## Décima terceira entrega (07/10/2026): várias cidades de uma vez

Quem tem família em Blumenau, Gaspar e Itajaí perguntava cidade por cidade. A 13ª entrega responde todas numa
mensagem só, com as mesmas regras de cada cidade sozinha.

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "como estão Blumenau, Gaspar e Itajaí?", "como estão Blumenau e Gaspar agora?" | Uma linha por cidade (até 6), a mesma de "o que vem de cima" (`leituraCurta`): número na régua dela, faixa com o nome da Defesa Civil, seta só quando a série casa com a leitura (D7), hora e idade. Abre com "cada cidade na régua dela (não compare os metros…)" e fecha com o 199. | Comparar metros de cidades diferentes; mostrar leitura velha como de agora; dar um número só para Itajaí; mudar de tela. |
| "como estão as minhas cidades?", "as cidades que eu sigo" | As cidades guardadas neste aparelho (a sua primeiro, depois as seguidas). Sem nenhuma, ensina "minha cidade é Blumenau" e "seguir Gaspar". | Adivinhar a cidade da pessoa. |
| "copiar o resumo das minhas cidades", "copiar o resumo de Blumenau e Gaspar" | Junta o resumo de cada cidade (o mesmo do WhatsApp, D4) com um rodapé só e mostra o botão "Copiar". Cidade sem leitura de agora fica "sem leitura de agora"; Itajaí, "várias réguas". | Pôr o endereço do site (D4); sair sem nenhuma leitura de agora. |

- **Lista dita:** a vírgula some na normalização, então a lista é lida palavra a palavra, pelo nome mais longo do
  cadastro (até quatro palavras, "e" entre elas). Só vira comando com duas ou mais cidades conhecidas: "como está
  Blumenau?" continua no motor, e uma cidade fora do cadastro ("Pomerode") devolve a frase ao motor em vez de
  responder com uma cidade a menos.
- **Testes:**
  - `src/comandos/decimaterceira.test.ts` (5): frases, texto para copiar (um rodapé, Itajaí sem número, sem
    endereço), executor com lista dita, com as cidades seguidas e sem nenhuma, a ajuda;
  - `testes-navegador/chat-comandos.mjs`, seção 14: as duas cidades com "não compare os metros" e o 199, a tela que
    não muda, "minhas cidades" antes e depois de "minha cidade é Gaspar", o botão "Copiar".

## Ajuste (07/10/2026): as duas perguntas do morador sobre a foz

O Jefferson perguntou no chat: "quanto tempo chega a água de Blumenau até Itajaí?" e "a água chega na hora da maré
alta?". A primeira já respondia (12 a 17 h, estudo da JICA). A segunda caía em "Não entendi", e as duas juntas
respondiam só o tempo.

- **Rota:** frase com a cheia descendo (água, cheia, pico, enchente ou Blumenau), com chegar (ou pegar,
  coincidir, bater, junto) e com maré alta, maré cheia ou preamar vai para o quadro de chegada × maré (7ª entrega).
  Esse quadro já diz a janela em horas e se há preamar dentro dela. "Como está a maré?" e "quando é a maré alta?" não
  falam da cheia e continuam na maré.
- **Sem pico descendo:** o quadro dizia "não há pico de cheia descendo" sem dizer quanto tempo a água leva. Agora diz
  também "quando há pico, ele leva de 12 a 17 h de Blumenau até Itajaí, pela referência de estudo; não é previsão",
  e sem leitura de Blumenau termina com o 199.
- **Sugestão:** a resposta do tempo de descida até Itajaí oferece "a água chega na hora da maré alta?".
- **Testes:**
  - `setima.test.ts`: as frases do morador e o tempo dito sem pico;
  - `motor.test.ts`: a sugestão;
  - `chat-comandos.mjs`, seção 8: as duas perguntas juntas, com "12 a 17 h" e o 199.

## Décima quarta entrega (07/10/2026): a linha do tempo da cheia de agora

Quem olha o rio subir pergunta "quando passou da cota?", "há quanto tempo está assim?", "quando começou?" e
"quanto subiu desde de manhã?". A 14ª entrega responde as quatro pela série publicada de UMA régua (a janela de
~48 h de `dados/serie.ts`), sem conta nova sobre o futuro.

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "quando Blumenau passou da cota de alerta?", "a que hora o rio passou da cota em Blumenau?", "quando Blumenau entrou em alerta máximo?" | O primeiro ponto da série na cota ou acima, depois de estar abaixo, com o passo da série ("medição a cada ~15 min: o cruzamento pode ter sido até 15 min antes"). Se já voltou para baixo, diz quando. Sem cota dita, usa a da faixa de agora. Cota que a cidade não tem: lista as que tem. | Inventar hora entre duas medições; chamar de agora o que a série velha mostra. |
| "há quanto tempo Blumenau está em alerta?", "há quanto tempo está acima da cota de atenção em Blumenau?" | Desde o último cruzamento, para cima, da cota da faixa pedida (ou a de agora). Abaixo de todas: diz desde quando. Já estava acima no começo da série: "mais de N h". | — |
| "quando o rio começou a subir em Blumenau?", "há quanto tempo o rio está subindo?" | O começo da subida que ainda dura: o último ponto no mínimo do trecho que só sobe, com 2 cm de tolerância (o limiar de `tendencia`). Diz quanto subiu e a média em cm/h. Rio descendo: o pico das 48 h e quanto desceu. | Chamar patamar de subida. |
| "quanto Blumenau subiu nas últimas 6 horas?", "quanto o rio baixou nas últimas 12 h em Blumenau?" | O ponto de agora contra o ponto de N horas antes (1 a 72), na mesma régua; se no meio passou mais alto, diz. Série curta: diz de onde a onde ela vai. | Comparar pontos de réguas diferentes. |

- **Regras que continuam:** as duas perguntas de cota são recusadas em Gaspar ("maior que"), Ascurra (C18) e Itajaí
  (várias réguas), pelos mesmos motivos de "quanto falta" — e apontam as outras duas, que funcionam em qualquer
  régua. Itajaí: a linha do tempo é de uma régua; com uma escolhida no Monitor, vale para ela. Série velha leva a
  frase "a série para às HH:MM: depois disso ela não diz nada". Toda resposta termina com "tudo na régua de X: não
  compare com outras cidades" e o 199.
- **Frases:** a cidade pode vir antes do verbo ("quando Blumenau passou…") ou no fim ("…em Blumenau"); "o rio",
  "o nível" e "a água" antes do verbo não são cidade. Sem cidade, vale a da página. "Blumenau está subindo?",
  "quanto falta…", "o que mudou na última hora" e "máximo das últimas 24 h" continuam onde estavam; o tempo de
  descida e o histórico continuam no motor.
- **Testes:**
  - `src/comandos/decimaquarta.test.ts` (5): frases, as contas (cruzamentos, começo da subida, ponto de N horas
    antes), os textos (hora de medição, série velha, Gaspar), o executor (Itajaí pede régua; nada navega), a ajuda;
  - `testes-navegador/chat-comandos.mjs`, seção 15: as quatro perguntas em Blumenau, com a hora de medição ou o
    motivo, sem mudar de tela.

## Décima quinta entrega (07/10/2026): as cheias que o site já captou

Pedido do Jefferson: perguntas sobre os eventos dos últimos meses que o site já captou. A fonte é a série de 15 em
15 min que o coletor grava (agosto a outubro de 2026, cópia no branch `arquivo-series`), destilada por
`scripts/eventos_captados.py` em `data/eventos-captados.json`: por régua, os episódios acima da cota de referência,
com a maior leitura captada, a hora dela, a maior lacuna e se já há registro em `enchentes.json`. Regra em
`CLAUDE.md` ("Cheias captadas pelo site").

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "quais cheias o site captou?", "o que aconteceu nos últimos meses?", "cheias recentes em Blumenau" | As ondas na bacia (cristas a menos de 48 h uma da outra), da mais recente para a mais antiga, com a maior leitura de cada cidade e "✓ registrado" no que já foi conferido. Com cidade: os episódios dela. | Chamar a maior leitura de pico; juntar réguas de Itajaí num número só. |
| "qual foi a última cheia em Blumenau?", "quando foi a última vez que Blumenau passou da cota de alerta?" | O último episódio (ou o último na faixa pedida ou acima), com a hora da medição, a duração acima da cota, a lacuna quando passa de 3 h e o registro conferido. Se a série termina dentro dele, diz que pode não ter acabado. | Descrever o nível de agora (isso é "como está X?"). |
| "qual foi o maior nível que o site já captou em Blumenau?", "maior leitura captada em Rio do Sul" | A maior leitura desde o começo da série, por publicação quando a cidade trocou de fonte (Rio do Sul: Estação MKS → Ponte Dom Tito Buss), cada uma com o seu zero. Aponta "maior cheia de X" para o histórico registrado. | Comparar publicações entre si. |
| "quantas vezes Blumenau passou da cota de alerta desde que o site acompanha / este ano?", "quantas cheias o site captou em X?" | A contagem de episódios desde o começo da série, com as datas. Diz que 18 h abaixo da cota separam dois episódios e que a série tem lacunas. | — |
| "como foi a cheia de setembro em Blumenau?", "o que aconteceu em 12 de setembro?", "cheias de setembro de 2026" | Os episódios do mês ou do dia (todas as cidades ou uma). Mês anterior à série: diz desde quando o site acompanha e aponta o histórico. | Responder sobre ano antigo: "cheias de setembro de 2011" continua no motor (`enchentes.json`). |

- **Captura, não registro:** toda resposta termina com "é o que a coleta do site captou, com lacunas; não é
  registro oficial nem pico conferido" e o 199. Em Blumenau, quando só o repasse (3 h atrasado) tinha a leitura, a
  hora vem com "hora do repasse". Réguas de estuário de Itajaí não geram episódio; Ascurra e Gaspar ficam sem faixa.
- **Testes:**
  - `scripts/teste_eventos_captados.py` (7): relógio de Blumenau, estuário, troca de fonte, Ascurra/Gaspar,
    casamento com `enchentes.json`, lacuna, arquivo;
  - `src/comandos/decimaquinta.test.ts` (4): frases (e o que continua no motor), os textos sobre um arquivo pequeno
    (nunca "pico", sempre o 199), o executor (link para a aba Histórico; nada navega), a ajuda;
  - `testes-navegador/chat-comandos.mjs`, seção 16: lista, última, setembro com o registrado, quantas, o link.
- **Validador:** `valida_eventos_captados` cobra cidade do cadastro, hora em Brasília sem fuso, faixa do
  vocabulário e que "registrado" aponte registro existente.

## Décima sexta entrega (07/10/2026): as ruas pela cota, cidade inteira

A aba "Minha rua" responde uma rua por vez e tem o controle "e se o rio estivesse em…". A 16ª entrega leva as
mesmas contas (`logica/cotasRuas.ts`: `atingidas`, `proximas`, `nivelUtilizavel`, `podeAfirmarAlcance`) para o chat,
pela cidade inteira. Textos em `comandos/ruasPelaCota.ts`.

| Pedido | O que faz | O que nunca faz |
|---|---|---|
| "quais ruas alagam com 8 m em Blumenau?", "se o rio chegar a 8,50 m, quais ruas alagam?" | Os pontos com cota até o nível: quantos de quantos, por bairro, e os 8 mais perto do nível (os últimos alcançados), com abrigo quando a fonte dá. Nível impossível (≥ 25 m) não vira comando. | Afirmar que "já alagou": nível dito é hipótese. |
| "quais ruas o rio já alcançou em Blumenau?", "que ruas estão alagadas agora?" | O mesmo, no nível de agora — só com leitura fresca (`nivelUtilizavel`, a regra de idade da cidade), em régua, numa cidade de uma régua só. Leitura velha ou cidade de várias réguas: recusa e aponta "com 8 m". | Chamar de observação o que é tabela. |
| "quais são as próximas ruas em Blumenau?", "quais ruas alagam se subir mais 50 cm?" | As de cota logo acima do nível de agora, com quanto falta; com "mais N", os pontos entre o nível e nível + N. | Dizer que o rio vai subir. |
| "quais ruas alagam primeiro em Gaspar?", "quais são as ruas mais baixas de Blumenau?" | As cotas mais baixas da cidade, sem precisar de leitura. | — |

- **Regras da aba que valem aqui:** cota de rua é PONTO, não rua inteira; a lista é a que a Defesa Civil publicou e
  não é completa; ponto `usar_para_aviso: false` (Rio do Sul) fica fora da conta e é dito à parte; cota nula não é
  zero (contada à parte); números na régua da própria cidade. Cidade sem cotas (Itajaí) aponta as manchas.
- **O que continua onde estava:** "qual a cota da Rua X" e "quantas cheias passaram da cota da Rua X" (motor);
  "manchas na rua X" e "mostrar a rua X" (3ª entrega).
- **Testes:**
  - `src/comandos/decimasexta.test.ts` (4): frases (número com vírgula, "mais 50 cm", o que fica no motor), os
    textos sobre uma tabela pequena (bloqueado fora da conta, sem número, Itajaí, leitura velha), o executor
    (fresca × velha; link para a aba Minha rua; nada navega), a ajuda;
  - `testes-navegador/chat-comandos.mjs`, seção 17: com 8 m (contagem, bairros, aviso), agora ou a recusa, as
    próximas, Gaspar primeiro, o link.

## Décima sétima entrega (07/10/2026): linha de base, bateria de avaliação e catálogo de capacidades

É o **PR 1** do handoff de qualidade do chat (`docs/HANDOFF-QUALIDADE-CHAT-2026-10-07.md`): medir o que existe antes
de mudar como o chat entende. **Nenhuma função hidrológica nova**; nenhum comando mudou de comportamento (os 1.001
testes das dezesseis entregas passam iguais). O que entrou:

| Peça | Onde | O que é |
|---|---|---|
| Extratores compartilhados | `comandos/entidades.ts` | `cidadePorNome`, `cidadeOpcional`, `cidadesDaLista`, `cotaDita`, `metrosDitos`, `mesDito`, `soSujeito`, `ARTIGOS`, `AQUI`, `COTA_DITA`, `SUJEITO`. Antes cada leitor de `interpretar.ts` tinha a sua cópia; agora é uma, com a resolução contra o cadastro num lugar só. |
| Catálogo único de capacidades | `comandos/capacidades.ts` → `docs/CHAT-CAPACIDADES.md` | `Record<Passo['tipo'], Capacidade>`: 67 fichas (título, descrição, exemplos, argumentos tipados, `mudaTela`, `precisaDoMapa`, dados que lê, quando esclarece, o que nunca faz), em 8 grupos. Passo novo sem ficha não compila. `esquemaDoClassificador()` deriva daí os identificadores para o PR 2. É o catálogo de **comandos**; o de cidades e réguas continua em `catalogo.ts`. |
| Bateria de avaliação | `comandos/avaliacao/casos.ts`, `cenarios.ts`, `avaliar.ts` | **478 casos** nos sete grupos do handoff (diretos 237 · escrita 46 · contexto 41 · ambiguidades 44 · atualidade 40 · segurança 40 · falhas 30). `dev` = os 160 exemplos do catálogo; `reservado` = 318 frases novas. Os casos de atualidade e falhas rodam o **executor de verdade** em cenários congelados (leitura fresca, velha, cidade sem leitura, Itajaí com três réguas, série curta, leituras indisponíveis, nível impossível de 30 m lido pelo próprio `buscarTempoReal`, Monitor que não abre, sem tabelas). Relógio fixo: 06/10/2026 15h00. |
| Trava | `avaliacao/avaliacao.test.ts` + `baseline.json` | zero ações indevidas; `dev` em 100 %; nenhum grupo abaixo da linha de base; tamanho da bateria igual ao registrado (caso novo exige regravar a linha). |
| Ferramenta | `npm run avaliar` (`ferramentas/avaliar-chat.ts`) | grava `docs/AVALIACAO-CHAT.md` e `docs/CHAT-CAPACIDADES.md`; com `--baseline`, regrava `baseline.json`; com `--falhas`, lista os reprovados. |

### A linha de base (07/10/2026)

**416/478 (87 %)**: dev 160/160; reservado 256/318 (81 %); intenção correta 349/408; argumentos corretos 84/110;
**0 ações indevidas**; 0 esclarecimentos desnecessários; 13 esclarecimentos que faltaram; 25 respostas por palpite do
motor; latência do leitor + motor 0,2 ms (p95 1,1 ms). Por grupo: diretos 89 %, escrita 74 %, contexto 83 %,
ambiguidades 84 %, atualidade 98 %, segurança 83 %, falhas 93 %. A lista completa dos 62 reprovados está em
`docs/AVALIACAO-CHAT.md`; cada caso espera o comportamento **certo pelas regras**, não o de hoje, então reprovado é
achado e não se ajusta o esperado para o número subir.

### O diagnóstico, atualizado com os números

1. **Paráfrase fora do padrão cai no motor** (26 diretos, 12 de escrita): "leva para Gaspar", "abre o monitor da
   bacia", "as barragens estão abertas?", "buscar leituras novas", "ir p/ o monitor", "qdo blumenau passou da cota".
   É o limite do leitor por expressões regulares que o handoff descreve, agora com medida.
2. **O motor responde por palpite** (25 casos): achou a cidade e nada mais e devolve "maiores cheias" — para
   "blumenau" solto, para "quais ruas alagam com 30 m", para "mude o nível de Blumenau para 10 m" e, o mais sério,
   para **"é seguro ficar em casa em Blumenau?"**, que devia cair na barreira do presente e não cai (a palavra
   "seguro" sem "está" escapa de `pedeAgora`). Nenhum palpite muda a tela.
3. **Contexto da página pouco usado** (7): "histórico", "minha rua", "fontes", "ao vivo" na página da cidade ou no
   Monitor não viram comando; "aqui" só é entendido em algumas frases.
4. **Dois defeitos do executor em encadeamento** (falhas): pedido com duas leituras ("quanto falta … e quais ruas o
   rio já alcançou") responde só a primeira; passo de camada com ano inexistente no meio da cadeia não diz o que já
   foi feito nem que os seguintes não foram.
5. **Publicação sem leitura válida** (atualidade, 1): o panorama diz "nenhuma cidade em alerta" em vez de dizer que a
   coleta não trouxe leitura. O nível impossível **nunca** aparece como número (travado), mas a ausência é mal
   explicada.
6. **O que já está firme** (e a bateria trava): leitura velha nunca vira "agora" em nenhum comando; Gaspar, Ascurra
   e Itajaí recusam a conta de cota; Itajaí pede a régua; falha externa é dita (SEM_DADOS, maré, barragens, traçado,
   Monitor que não abre); nenhum pedido malicioso, URL, rota dita ou "apagar" muda a tela ou executa algo.

### Limitações desta medição

- As frases reservadas foram escritas por quem conhece o leitor; não são frases reais de moradores (a telemetria
  anônima não guarda texto, por decisão de 04/10/2026). A rubrica humana de clareza do handoff não foi aplicada.
- Os cenários do executor são de mentira: dados fixos, Monitor falso que aceita tudo. O que eles provam é a regra,
  não a tela — a tela continua coberta por `testes-navegador/chat-comandos.mjs`.
- A latência medida é do leitor + motor em Node; não inclui rede nem o classificador (desligado).
- "Intenção correta" e "argumentos corretos" só valem para os casos de leitura; os de execução conferem o texto.
- Metas por grupo para o PR 2 ficam para depois desta medida, como o handoff pede ("definir metas por categoria após
  medir o baseline").

### O que NÃO mudou (de propósito)

O piloto do classificador continua desligado; nenhuma lista de permissões, segredo, retenção ou público foi tocado;
nenhum comando ganhou ou perdeu frase; os arquivos do Monitor ficaram intactos.

## Décima oitava entrega (07/10/2026): os achados da linha de base

A 17ª mediu; a 18ª corrige o que a bateria reprovou **sem IA** — regras do leitor, do motor e do executor — e mede de
novo. Nenhuma função hidrológica nova; o piloto do classificador continua desligado.

### O que mudou

| Achado da linha de base | Correção | Onde |
|---|---|---|
| "é seguro ficar em casa em Blumenau?" escapava da barreira do presente (sem "está") e virava palpite de "maiores cheias" | `(é\|seria) segur[oa]`, `segur[oa] (ficar\|sair\|atravessar…)`, `vai (chegar\|passar\|atingir…)`, `posso dormir\|ficar` entraram na barreira | `chat-local/motor.ts` `AGORA` |
| O motor palpitava "maiores cheias" com qualquer cidade ("blumenau", "leva para Gaspar", "mude o nível de Blumenau") | Palpite só quando a pergunta fala do rio (`FALA_DO_RIO`); sem isso, "não entendi o que você quer saber de Blumenau" com exemplos da cidade | `motor.ts` `responder` |
| Pedido com duas leituras ("quanto falta … e quais ruas o rio já alcançou") respondia só a primeira | O executor roda cada passo em `executarPasso`; resposta de leitura é guardada e a cadeia segue; no fim, todas juntas (link da última que tem link). Falha ainda para a cadeia e diz o que foi feito (`Saida.falhou`) | `executar.ts` |
| Camada de ano inexistente no meio da cadeia não dizia o que já fora feito | Vira `falha(…, sugestões)`: "Feito: … <motivo>. Os passos seguintes não foram feitos." | `executar.ts` `camada` |
| Panorama com publicação sem leitura válida dizia "nenhuma cidade em alerta" | "A coleta de agora não trouxe leitura válida de nenhuma régua … isso não quer dizer que o rio está normal" | `executar.ts` `panorama` |
| Só o nome da cidade ("blumenau") | Pergunta "O que você quer saber de Blumenau?" com 4 exemplos; nada executado | `interpretar.ts` |
| Pedido de ALTERAR dado ("mude o nível…", "registrar pico…", "apagar o histórico de Blumenau", "cadastrar a cota…") | Recusa dita: "O chat não altera dados do site…", lida depois de todos os leitores (apagar manchas, limpar conversa, mudar minha cidade continuam comandos) | `interpretar.ts` `pedeAlteracaoDeDado` |
| Endereço ou rota digitada ("abrir /monitor/blumenau", "http://…") | Esclarecer: "Não abro endereços nem rotas digitadas" — nem comando, nem motor | `interpretar.ts` |
| "mostrar Blumenau" × 30 | Palavra repetida 6+ vezes em pedido longo: pergunta | `interpretar.ts` `palavraRepetida` |
| Abreviações do celular ("ir p/ o monitor", "qdo", "qto", "oque", "q", "c 8 m", "hj", "vc") | `expandirAbreviacoes` depois de `normalizar`, no leitor e nos trechos | `interpretar.ts` |
| Erro de digitação no verbo ou na peça ("msotrar blumenau", "kuanto falta", "abrir monitr") | Como no nome da cidade (9ª): "Você quis dizer …?" com a frase corrigida; nada executado. Palavra por palavra, candidato único à menor distância | `interpretar.ts` `corrigirVerbo` |
| "… aqui", "… desta cidade" no fim do pedido | Sai do texto; o executor usa a cidade da tela | `interpretar.ts` `AQUI_NO_FIM` |
| "histórico", "minha rua", "fontes" sozinhos na página da cidade | Abrem a aba da cidade da tela | `interpretar.ts` |
| "quanto Blumenau subiu?" sem janela | Pergunta a janela ("em quantas horas?") | `interpretar.ts` (14ª) |
| "quais ruas alagam com 30 m" | Pergunta um nível possível (0–25 m) em vez de ir ao motor | `interpretar.ts` (16ª) |
| "como estão Blumenau e Pomerode?" | Diz qual nome não está entre as cidades do site | `interpretar.ts` (13ª) |
| Paráfrases: "leva para", "abre o monitor da bacia", "página do Itajaí-Mirim", "aproximar mais", "voltar para a leitura de agora", "desfazer a última ação", "o que está na tela", "sem cor", "quem está acima … no rio", "lado a lado", "as barragens estão abertas", "rio acima", "cor vermelha", "buscar leituras novas", "site é da Defesa Civil", "dá para instalar", "o que vocês guardam", "apagar tudo que o site guardou", "limpar o chat", "fechar esse painel", "abrir a lista de cidades", "desde quando … em alerta", "cheias que o site registrou", "ruas vêm depois", "Blumenau subindo?", formas "liga/desliga/troca/coloca" | Regras dos leitores de cada entrega | `interpretar.ts` |
| Relógio da simulação de chegada | `simular_chegada` usa o mesmo `agora` das leituras (`AoVivo.agora`); o teste da 7ª dependia da data real e ficaria vermelho em 07/10 | `executar.ts` |

### A medida

Linha de base da 17ª (478 casos): **416/478 (87 %)**, reservado 81 %, 25 palpites. Com as correções, nos MESMOS 478:
**473/478**, e os cinco restantes eram quatro esperados que precisavam de revisão (abaixo) e um bug de cortesia.

**Generalização:** antes de fechar, entraram **47 frases novas** (`RESERVADOS_18`), escritas depois das correções e
antes de rodar o leitor com elas. Primeira rodada: **39/47 (83 %)**. As oito que falharam ("a página da foz", "troca o
fundo para o mapa de ruas", "desliga as camadas", "coloca em tela cheia", "vc guarda meus dados?", "hj teve leitura
nova?", "abrir monitr", "posso dormir tranquilo em Blumenau?") foram corrigidas — uma delas era **defeito da regra
nova**: "coloca em tela cheia" caía na recusa de alterar dado porque "cheia" estava na lista de dados e "coloca" na
de verbos; os dois saíram da lista.

Linha de base nova (`baseline.json`): **525/525**, 0 ações indevidas, **0 palpites**, latência 0,2 ms (p95 1 ms).
Honestidade do número: 100 % é sobre frases escritas por quem conhece o leitor; a próxima família de frases novas vai
reprovar de novo, e é para isso que ela existe.

### Quatro esperados revistos (documentados, não "ajustados para subir")

1. "msotrar blumenau" e "kuanto falta pra cota em blumenau": esperavam executar; passam a esperar **esclarecer**,
   pela regra da 9ª (erro de digitação pergunta, não executa).
2. "ligar camada 1999": esperava "perguntar" no leitor; o leitor não conhece as camadas do Monitor — vira **comando** e
   quem pergunta é o executor (agora com "Feito: …" e a lista).
3. "vai chegar a 10 m?": esperava "perguntar"; é previsão, e o certo é a **barreira do presente** (que passou a pegá-la).

### Testes que mudaram de contrato (18ª)

`interpretar.test.ts` ("Blumenau" solto → esclarecer), `oitava.test.ts` ("apagar o histórico de Blumenau" → recusa),
`decimasexta.test.ts` (30 m → esclarecer), `decimaterceira.test.ts` (Pomerode → esclarecer), `casosClassificador.ts`
(`p-dormir-rio-do-sul` agora cai na barreira: `barreira: true`). `testes-navegador/chat-comandos.mjs` ganhou a seção
18 (barreira, duas leituras, nome solto, alteração de dado, "histórico" na página da cidade).

## Décima nona entrega (07/10/2026): o contexto da conversa

A seção "Contexto de conversa" do handoff (`docs/HANDOFF-QUALIDADE-CHAT-2026-10-07.md`), sem IA. Até aqui o chat lia
cada mensagem com o contexto da TELA; a conversa só entrava em "e Gaspar?" (10ª). Agora os dois contextos são
separados e tipados, e a conversa entra em três lugares, sempre dizendo de onde veio a entidade.

| Regra do handoff | Como ficou | Onde |
|---|---|---|
| Separar contexto da tela e da conversa; informar a origem | `Contexto.cidadeDaConversa` (a última cidade citada nesta conversa) ao lado de `cidadeAtual` (tela). O executor usa a da conversa só quando a tela não tem cidade, e a resposta começa com **"Pela conversa, entendi que é de Gaspar."** | `comandos/conversa.ts` (`memoriaDaConversa`, `contextoComConversa`), `executar.ts` |
| Entidade dita vence a implícita | Dita no pedido > tela > conversa (`passo.cidadeId` primeiro; a tela antes da conversa porque é o que a pessoa está olhando) | `executar.ts`, testado em conversas |
| "Como está Blumenau?" → "E Gaspar?" | Continua como na 10ª (refaz e responde) | `continuar.ts` |
| "Mostre Itajaí" → "Aproxime a régua" → esclarecer | A tela depois de navegar é o Monitor de Itajaí: pergunta qual das 11 réguas | já valia; agora coberto por conversa na bateria |
| "Quando passou do alerta em Blumenau?" → "E ontem?" | Continuação de **dia**: refaz como "… ontem?"; o passo `linha_do_tempo` ganhou `dia` (hoje/ontem/anteontem, em Brasília) e a resposta diz só o que aconteceu naquele dia, ou que a série não o cobre | `continuar.ts`, `interpretar.ts`, `linhaDoTempo.ts` |
| "Mostre Blumenau" → "E Gaspar?": não executar por suposição | A continuação que **mudaria a tela** não executa: *"Entendi como "mostrar Gaspar", que muda a tela. É isso? Toque na sugestão para confirmar; nada foi feito."* — a sugestão é a frase pronta. Continuação que só responde ("copiar resumo", "como está") refaz direto, com "Entendi como:" | `conversa.ts` `decidirContinuacao` |
| Trocar de cidade invalida a régua | "zoom na régua DC-05" → "mostrar Blumenau" → "aproximar a régua" aproxima a régua de Blumenau (a DC-05 é de Itajaí e sai com a navegação) | já valia; coberto por conversa |
| Contexto não transforma pergunta em ação | "e a tendência?", "e quanto falta?" continuam o ASSUNTO (o "e" de continuação, com o resto lido como pedido inteiro); perguntas e recusas continuam perguntas e recusas no meio da conversa | `interpretar.ts` `lerTrecho` |
| Não guardar além da política | A memória é a lista de mensagens desta aba (como já era); nada vai ao aparelho nem ao servidor | `ChatLocal.tsx` |

Continuações novas em `continuar.ts`, sempre UMA troca no pedido anterior como foi escrito: **dia** ("e ontem?", "e
hoje?" — só em pergunta de "quando"), **número** ("e com 9 m?", "e nas últimas 12 horas?", "e 12?" — a unidade tem
de bater; dois números ou nenhum → pergunta) e **cota** ("e de atenção?", "e a de alerta máximo?").

### A medida

- Bateria: **+36 casos** (`RESERVADOS_19`), 29 deles **conversas completas** (2–3 turnos, com a tela e a memória
  seguindo os pedidos no avaliador: "mostrar X" abre o Monitor de X, página da cidade, régua escolhida). Métrica nova no
  relatório: "Conversas completas (todos os turnos certos)". Escritas antes de rodar: **36/36 na primeira rodada** —
  número a ler com desconfiança, porque quem escreveu as conversas acabara de escrever as regras (a mesma pessoa, no
  mesmo dia). O que vale é a trava: elas ficam na bateria e qualquer mudança no leitor que quebre uma conversa reprova.
  Linha de base: **556/556**, 0 ações indevidas, 0 palpites.
- Testes: `decimanona.test.ts` (continuações, memória, decisão refazer/confirmar/perguntar, leitor, executor com a
  nota, linha do tempo por dia); `chat-comandos.mjs` seção 19 (cidade da conversa fora de cidade, "e a tendência?",
  confirmação depois de navegar e a navegação ao tocar na sugestão).

### Decisões

1. **Tela vence conversa.** Na página de Blumenau, depois de "como está Gaspar?", "quanto falta?" é de Blumenau — a
   resposta nomeia a cidade, e quem quer Gaspar diz Gaspar.
2. **Confirmar só o que muda a tela.** Uma resposta a mais não custa nada; uma navegação errada no meio da cheia custa.
3. **"ontem" é dia de Brasília** (`chaveDoDia`), não "24 h atrás"; a série publicada tem 48 h, então "anteontem" quase
   sempre responde "não cobre".
