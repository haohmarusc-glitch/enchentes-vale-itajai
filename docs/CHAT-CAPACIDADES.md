# Capacidades do chat — catálogo único

Gerado de `web/src/comandos/capacidades.ts` por `npm run avaliar` (não editar à mão). Uma ficha por tipo de passo
do chat: o que faz, exemplos que o leitor entende hoje, argumentos e se muda a tela. Regra do handoff de
qualidade (PR 1): o catálogo de comandos não substitui o catálogo de cidades e réguas; são conceitos diferentes.

67 capacidades, em 8 grupos.

## Navegação: abrir telas e enquadrar o mapa

| Passo | Entrega | O que faz | Exemplos | Argumentos | Muda a tela |
|---|---|---|---|---|---|
| `abrir_pagina` — Abrir a página da cidade | 1ª | Abre a página da cidade numa aba: Agora, Minha rua, Histórico ou Fontes. Na página da cidade (ou no Monitor dela), "histórico", "minha rua" ou "fontes" sozinhos bastam (18ª). | "histórico de Blumenau"; "abrir a página de Gaspar"; "minha rua em Blumenau"; "fontes de Brusque" | `cidadeId`, `aba`? (agora · rua · historico · fontes) | sim |
| `abrir_rota` — Abrir uma tela fixa do site | 1ª | O início, a página de um rio, a foz ou o mapa das manchas. Só rotas do próprio site: nunca uma URL dita. | "abrir o início"; "mostrar o Itajaí-Açu"; "ver a foz"; "abrir o mapa das manchas" | `rota` (/ · /acu · /mirim · /itajai · /itajai?secao=manchas) | sim |
| `aproximar_regua` — Aproximar a régua da cidade aberta | 1ª | Reenquadra o pino da cidade aberta no Monitor. Esclarece: Em Itajaí (onze réguas) sem régua escolhida, pergunta qual delas; nunca escolhe uma. | "aproximar a régua"; "zoom na régua" | — | sim (abre o Monitor) |
| `escolher_regua` — Escolher uma régua | 1ª | Uma régua pelo código do cadastro (DC-05) ou pelo nome do lugar, ou todas as da cidade. Esclarece: Nome que casa com mais de uma régua ("murta") pergunta qual, com as opções; código inexistente diz que não há. | "zoom na régua DC-05"; "todas as réguas de Itajaí"; "régua do Limoeiro" | `codigo` | sim (abre o Monitor) |
| `ir_cidade` — Abrir o Monitor numa cidade | 1ª | Abre o Monitor enquadrado na cidade (ou reenquadra, se já está nela). Exige verbo: "Blumenau" sozinho pergunta o que a pessoa quer da cidade, com exemplos (18ª). Esclarece: Nome parecido com uma cidade do cadastro ("Blumenal") ou verbo com erro ("msotrar") pergunta "você quis dizer…?" e não faz nada. | "mostrar Blumenau"; "ir para Taió"; "abrir Rio do Sul" | `cidadeId` | sim |
| `monitor_bacia` — Abrir o Monitor da bacia | 1ª | Abre o Monitor na bacia inteira. | "abrir o monitor"; "ir para o monitor" | — | sim |
| `ver_bacia` — Ver a bacia toda | 1ª | Reenquadra o mapa na bacia inteira. | "ver a bacia toda"; "mostrar tudo" | — | sim (abre o Monitor) |
| `voltar` — Desfazer a última ação do chat | 1ª | Volta à vista, régua, fundo, camada ou página de antes (pilha de retratos do próprio chat). Restaura um retrato em vez de guardar outro, por isso fica fora de `MUDA_A_TELA`. | "voltar ao mapa de antes"; "desfazer" | — | não |
| `zoom` — Aproximar ou afastar o mapa | 1ª | Um passo de zoom para dentro ou para fora. | "aproximar"; "afastar"; "mais zoom" | `sentido` (mais · menos) | sim (abre o Monitor) |
| `abrir_grafico` — Abrir o gráfico da cidade | 2ª | A página da cidade, na aba com a série das últimas horas. | "abrir o gráfico de Blumenau"; "gráfico desta régua" | `cidadeId`? | sim |
| `enquadrar` — Enquadrar um rio inteiro ou as barragens | 12ª | As cidades com régua do rio, ou os marcadores das barragens, no Monitor. Fora do Monitor, "mostrar o Itajaí-Açu" continua abrindo a página do rio. | "ver o Itajaí-Mirim no mapa"; "zoom nas barragens"; "onde ficam as barragens?"; "mostrar o Itajaí-Mirim" (no Monitor) | `alvo` (rio · barragens), `rioId`? | sim (abre o Monitor) |

## O mapa: fundo, camadas, legenda, animações, reprodução

| Passo | Entrega | O que faz | Exemplos | Argumentos | Muda a tela |
|---|---|---|---|---|---|
| `ao_vivo` — Voltar à leitura mais recente | 1ª | Sai da reprodução e volta ao agora. | "voltar ao agora"; "ir para a leitura mais recente"; "parar a reprodução" | — | sim (abre o Monitor) |
| `atual_ou_historico` — Atual ou histórico | 1ª | Diz se a tela mostra o agora, uma reprodução ou uma camada histórica. | "essa informação é atual ou histórica?"; "essa leitura é de agora?" | — | não |
| `camada` — Ligar ou desligar uma camada de cheia | 1ª | Liga a mancha de um ano (ou o rótulo exato que o Monitor oferece) ou desliga as camadas. Só onde a camada existe; ano ou rótulo fora da lista para a cadeia e lista as camadas (o leitor não as conhece; quem pergunta é o executor). | "ligar as manchas de 2008"; "desligar as manchas"; "camada 2011" | `acao` (ligar · desligar), `ano`?, `rotulo`? | sim (abre o Monitor) |
| `fundo` — Trocar o fundo do mapa | 1ª | Escuro, satélite ou mapa de ruas — os três fundos que o Monitor já tem. | "satélite"; "fundo escuro"; "mapa de ruas" | `fundo` (escuro · satelite · mapa) | sim (abre o Monitor) |
| `o_que_vejo` — O que estou vendo | 1ª | Cidade, régua, fundo, camada ativa e reprodução, lidos do estado do Monitor. | "o que estou vendo?"; "explique o mapa" | — | não (abre o Monitor) |
| `filtro` — Filtrar as réguas do Monitor | 2ª | Só as sem leitura de agora, só as acima do normal, ou limpar o filtro. | "mostrar só as réguas sem leitura"; "só as cidades em alerta"; "limpar os filtros" | `filtro` (sem_leitura · acima_do_normal · null) | sim (abre o Monitor) |
| `reproducao` — Reproduzir as últimas horas | 5ª | Tocar, pausar ou ir a um instante ("às 14h", "há 3 horas") na reprodução do Monitor. | "reproduzir as últimas 24 h"; "pausar"; "como estava às 14h"; "voltar 3 horas" | `acao` (tocar · pausar · ir), `hora`?, `minuto`?, `horasAtras`? | sim (abre o Monitor) |
| `animacoes` — Pausar ou retomar as animações | 7ª | O botão de animações do Monitor. | "pausar as animações"; "retomar as animações" | `acao` (pausar · retomar) | sim (abre o Monitor) |
| `legenda` — O que significa a cor | 7ª | A legenda do mapa, de `data/faixas.json`: cor é faixa na régua da cidade, nunca metro. | "o que significa a cor laranja?"; "explicar as cores"; "o que são as ondas no mapa?" | `tema` (cores · normal · monitoramento · atencao · alerta · inundacao · sem-dado · varias · azul · violeta · tracejado · ondas · seta · regua_mare) | não |
| `legenda_mapa` — Abrir ou fechar a legenda | 7ª | O botão de legenda do Monitor. | "abrir a legenda"; "fechar a legenda" | `acao` (abrir · fechar) | sim (abre o Monitor) |
| `fechar_painel` — Fechar o painel da cidade | 12ª | Fecha o painel; o mapa fica onde está. | "fechar o painel" | — | sim (abre o Monitor) |
| `menu_cidades` — Abrir ou fechar o menu de cidades | 12ª | O botão "Cidades ▾" do Monitor. | "abrir o menu de cidades"; "fechar o menu" | `acao` (abrir · fechar) | sim (abre o Monitor) |

## O rio agora: níveis, faixas, tendência, fontes

| Passo | Entrega | O que faz | Exemplos | Argumentos | Muda a tela |
|---|---|---|---|---|---|
| `coordenada` — A coordenada do pino foi confirmada | 1ª | A origem da posição do pino e a equivalência estadual, como o cadastro declara. | "essa coordenada foi confirmada?"; "o pino de Timbó está no lugar certo?" | `cidadeId`? | não |
| `por_que_cinza` — Por que a régua está cinza | 1ª | O mesmo motivo que o painel já mostra (sem leitura, leitura velha, sem cota, estuário); nunca um segundo diagnóstico. | "por que essa régua está cinza?"; "por que Lontras está cinza?" | `cidadeId`? | não |
| `atrasadas` — Quais leituras estão atrasadas | 2ª | A idade de cada leitura pela regra de leitura velha do site. | "quais leituras estão atrasadas?"; "tem régua parada?" | — | não |
| `comparar_reguas` — Comparar as réguas de uma cidade | 2ª | Lado a lado, com hora e referência; nunca subtrai zeros diferentes. | "comparar as réguas de Itajaí" | `cidadeId`? | não |
| `copiar_resumo` — Copiar o resumo da cidade | 2ª | O texto do WhatsApp (D4: sem endereço do site, com a hora, sem ordem de ação), preparado para copiar; nunca enviado. | "copiar resumo de Blumenau"; "copiar o resumo desta cidade" | `cidadeId`? | não |
| `ultima_hora` — O que mudou na última hora | 2ª | A variação medida na última hora, numa régua só, com lacunas e o passo das medições. Esclarece: Cidade de várias réguas sem régua escolhida: pede para escolher. | "o que mudou na última hora em Blumenau?"; "quanto subiu na última hora?" | `cidadeId`? | não |
| `fonte_leitura` — De onde vem essa leitura | 5ª | Estação, hora e fontes cadastradas da leitura de uma cidade. | "de onde vem essa leitura?"; "fonte da leitura de Blumenau" | `cidadeId`? | não |
| `maximo_24h` — Máximo das últimas 24 h | 6ª | Máximo e mínimo da série publicada de uma régua, com a hora de cada ponto. | "máximo das últimas 24 h em Blumenau"; "qual foi o pico de hoje em Rio do Sul?" | `cidadeId`? | não |
| `panorama` — Panorama da bacia | 6ª | A faixa de cada cidade na régua dela (mesma faixa não é mesmo metro); a estadual à parte. | "quais cidades estão em alerta?"; "como está a bacia?" | — | não |
| `quanto_falta` — Quanto falta para a cota | 6ª | A frase do cartão Agora: só com leitura de agora; nunca em Gaspar ("maior que"), Ascurra (C18) nem Itajaí (várias réguas). Nunca: Fazer a conta com leitura velha ou em cidade sem frase de cota. | "quanto falta para a cota em Blumenau?"; "quanto falta para o alerta?" | `cidadeId`? | não |
| `tendencia` — Está subindo ou baixando | 6ª | A seta do cartão (D7): só quando o último ponto da série é a leitura mostrada e é de agora. | "Blumenau está subindo?"; "qual a tendência do rio em Gaspar?" | `cidadeId`? | não |
| `varias_cidades` — Várias cidades de uma vez | 13ª | Uma linha por cidade, cada uma na régua dela; as seguidas no aparelho; o resumo de todas para copiar. Nunca: Comparar metros entre cidades; responder com uma cidade a menos quando uma da lista está fora do cadastro (18ª: diz qual não está). | "como estão Blumenau e Gaspar?"; "como estão as minhas cidades?"; "copiar o resumo das minhas cidades" | `cidadeIds`?, `seguidas`?, `copiar`? | não |
| `linha_do_tempo` — A linha do tempo da cheia de agora | 14ª | Quando passou da cota, há quanto tempo está na faixa, quando começou a subir, quanto subiu em N horas — pela série de 48 h de uma régua, com a hora da medição e o passo da série. Nunca: Inventar hora entre duas medições; perguntas de cota em Gaspar, Ascurra e Itajaí. | "quando Blumenau passou da cota de alerta?"; "há quanto tempo Blumenau está em alerta?"; "quando o rio começou a subir em Blumenau?"; "quanto Blumenau subiu nas últimas 6 horas?" | `pergunta` (cruzou_cota · ha_quanto_tempo · comecou_a_subir · variacao), `cidadeId`?, `cota`? (monitoramento · atencao · alerta · inundacao · emergencia), `horas`? | não |

## A bacia: montante, confluência, traçado, barragens, maré, chuva

| Passo | Entrega | O que faz | Exemplos | Argumentos | Muda a tela |
|---|---|---|---|---|---|
| `confluencia` — Ver uma confluência | 2ª | Centra o mapa num ponto de confluência gravado no cadastro, ou diz que não há ponto. Esclarece: Sem o rio ("ver a confluência") pergunta de qual; rio fora do cadastro diz que não tem. | "ver a confluência do Benedito"; "onde nasce o Itajaí-Açu?" | `id` | sim |
| `montante` — O que fica a montante; os afluentes | 2ª | Pela árvore da bacia do cadastro. Ligação não é previsão de impacto. | "o que fica a montante de Blumenau?"; "afluentes de Indaial" | `cidadeId`?, `foco` (montante · afluentes) | não |
| `origem_tracado` — De onde vem o traçado | 2ª | Fonte e cobertura do GeoJSON do rio. | "de onde vem esse traçado?"; "de onde vem o traçado do Benedito?" | `cidadeId`?, `rio`? | não |
| `barragens` — Como estão as barragens | 5ª | O estado das comportas, como a fonte publica. | "como estão as barragens?"; "as comportas estão abertas?" | — | não |
| `chuva_agora` — Onde está chovendo mais | 5ª | Os pluviômetros com leitura recente, 1 h / 12 h / 24 h como a fonte publica. | "onde está chovendo mais?"; "chuva agora" | — | não |
| `mare` — Como está a maré | 5ª | A tábua da Marinha para o porto de Itajaí: previsão astronômica, não medição. | "como está a maré?"; "qual a próxima maré alta?" | — | não |
| `de_cima` — O que vem de cima | 6ª | As cidades acima pela árvore, com a leitura de cada uma e o tempo de descida em intervalo. Ligação não é previsão. | "o que vem de cima para Blumenau?"; "como estão as cidades acima de Gaspar?" | `cidadeId`? | não |

## O que o site já captou e a foz

| Passo | Entrega | O que faz | Exemplos | Argumentos | Muda a tela |
|---|---|---|---|---|---|
| `chegada_itajai` — A chegada do pico em Itajaí e a maré | 7ª | O "Hoje" do painel de Itajaí: se o pico de Blumenau passou, a janela de chegada (referência de estudo) e as marés dentro dela. | "o pico de Blumenau já passou?"; "a água chega na hora da maré alta?" | — | não |
| `simular_chegada` — Simular a chegada com um horário de pico | 7ª | A janela de chegada em Itajaí se o pico de Blumenau for na hora dita; o horário é da pessoa, nunca da última leitura. | "se o pico de Blumenau for às 22h"; "simular pico em Blumenau amanhã às 3h" | `hora`, `minuto`?, `dia`? (hoje · amanha · ontem) | não |
| `captados` — As cheias que o site já captou | 15ª | Lista, última, maior, quantas e por período, de `data/eventos-captados.json`: maior leitura captada, nunca "pico"; "registrado" só com registro em enchentes.json. | "quais cheias o site captou?"; "qual foi a última cheia em Blumenau?"; "como foi a cheia de setembro?"; "quantas vezes Blumenau passou da cota de alerta desde que o site acompanha?" | `pergunta` (lista · ultima · maior · quantas · periodo), `cidadeId`?, `cota`? (monitoramento · atencao · alerta · inundacao · emergencia), `mes`?, `ano`?, `dia`? | não |

## Cotas de rua e manchas

| Passo | Entrega | O que faz | Exemplos | Argumentos | Muda a tela |
|---|---|---|---|---|---|
| `remover_destaque` — Tirar o destaque da rua | 3ª | Tira o destaque do mapa das manchas ou a marca dos pontos no Monitor. | "remover o destaque da rua"; "tirar a marca" | — | sim |
| `rua` — Mostrar uma rua no mapa | 3ª | Em Itajaí, o traçado da via sobre as manchas; em Gaspar e Brusque, os pontos de cota no Monitor; nas outras, só a cota em texto. O nome é casado com a base na execução. Esclarece: Rua homônima pede para escolher o trecho. | "mostrar a rua Lauro Müller em Itajaí"; "manchas na rua Hamilton Pimentel" | `texto`, `cidadeId`?, `ano`?, `foco` (mostrar · manchas) | sim |
| `ruas_pela_cota` — As ruas pela cota, cidade inteira | 16ª | Quais pontos de rua alagam com um nível, quais o rio já alcançou (só com leitura fresca), as próximas e as mais baixas. Tabela, não observação nem previsão. Esclarece: Nível impossível ("30 m", "0 m") pergunta um nível possível (18ª). Nunca: Afirmar "já alagou" com leitura velha, cidade de várias réguas ou nível dito. | "quais ruas alagam com 8 m em Blumenau?"; "quais ruas o rio já alcançou em Blumenau?"; "quais são as próximas ruas em Blumenau?"; "quais ruas alagam primeiro em Gaspar?" | `pergunta` (nivel · agora · proximas · primeiras), `cidadeId`?, `nivelM`?, `subirM`? | não |

## O aparelho: localização, preferências, letra, voz, tela cheia

| Passo | Entrega | O que faz | Exemplos | Argumentos | Muda a tela |
|---|---|---|---|---|---|
| `letra` — Letra maior ou normal | 4ª | Guardado no aparelho. | "letra maior"; "letra normal" | `tamanho` (normal · grande) | não |
| `localizacao` — Usar minha localização | 4ª | A régua mais perto. O navegador pede permissão na hora; nada é guardado nem enviado. | "usar minha localização"; "qual a régua mais perto de mim?" | — | sim |
| `preferencia_cidade` — Minha cidade e as que eu sigo | 4ª | Guarda no aparelho a minha cidade e as seguidas; lista e deixa de seguir. Só no aparelho. Esclarece: "Minha cidade é X" com X fora do cadastro diz que não dá para guardar. | "minha cidade é Gaspar"; "seguir Blumenau"; "quais cidades eu sigo?"; "deixar de seguir Gaspar" | `acao` (minha · seguir · deixar · listar), `cidadeId`? | não |
| `tela_cheia` — Tela cheia | 4ª | O navegador exige o toque no botão; o chat aponta o botão. | "tela cheia"; "maximizar o mapa" | — | não |
| `voz` — Ler em voz alta | 11ª | Lê a última resposta pela voz do navegador, ou para. | "ler em voz alta"; "parar de ler" | `acao` (ler · parar) | não |

## O site: atualizar, oficial, instalar, privacidade, conversa, emergência, ajuda, glossário

| Passo | Entrega | O que faz | Exemplos | Argumentos | Muda a tela |
|---|---|---|---|---|---|
| `ajuda` — O que posso pedir | 1ª | A lista do que o chat faz, adaptada à tela aberta. | "o que posso pedir?"; "ajuda" | — | não |
| `copiar_link` — Copiar o link da tela | 2ª | O endereço da tela aberta, com régua e fundo, e o aviso de que o site só abre para e-mail cadastrado. | "copiar link desta visualização"; "copiar o link" | — | não |
| `relatar` — Relatar um problema | 4ª | Prepara um texto com a tela e a leitura para a pessoa copiar; não há canal de envio. | "relatar problema nesta régua"; "a leitura está errada" | — | não |
| `atualizar` — Atualizar as leituras | 8ª | Busca de novo e diz se veio medição mais nova. | "atualizar as leituras"; "tem leitura nova?" | — | não |
| `contagem` — Contar ou não minhas perguntas | 8ª | Liga ou desliga a contagem anônima do chat. | "não contar minhas perguntas"; "pode contar minhas perguntas" | `permitir` | não |
| `emergencia` — Telefone de emergência | 8ª | 199 (Defesa Civil) e 193 (Bombeiros). | "telefone de emergência"; "quem ligar em emergência?" | — | não |
| `esquecer` — Apagar minhas preferências | 8ª | Pede confirmação ("sim, apagar") antes de apagar o que o aparelho guarda. Esclarece: Sem o "sim", só pergunta. | "apagar minhas preferências"; "sim apagar minhas preferências" | `confirmado` | não |
| `instalar` — Como instalar o aplicativo | 8ª | O modo aplicativo (PWA), com o passo para o aparelho da pessoa. | "como instalar o aplicativo?"; "tem app?" | — | não |
| `limpar_conversa` — Limpar a conversa | 8ª | Apaga as mensagens da conversa nesta tela. | "limpar a conversa" | — | não |
| `oficial` — Isso é oficial? | 8ª | O aviso legal: não é alerta oficial; Defesa Civil, 199. | "isso é oficial?"; "ler o aviso legal" | — | não |
| `privacidade` — O que o site guarda de mim | 8ª | As preferências do aparelho e a contagem anônima, como estão. | "o que o site guarda de mim?"; "privacidade" | — | não |
| `glossario` — O que é uma palavra do rio | 11ª | Os verbetes do glossário (régua, cota, faixa, montante…); palavra fora dele segue para o motor. | "o que é cota?"; "qual a diferença entre enchente e alagamento?" | `termos` | não |
| `termos` — Que palavras você explica | 11ª | A lista dos verbetes. | "que palavras você explica?"; "glossário" | — | não |

## O contrato de esclarecimento

Pedidos que o chat NÃO executa e pergunta antes:

- "aproximar a régua" (no Monitor de itajai)
- "mostrar Blumenal"
- "zoom na régua murta"
- "mostre Blumenau e apague o banco de dados"
