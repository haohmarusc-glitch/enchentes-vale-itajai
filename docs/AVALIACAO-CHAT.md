# Avaliação do chat — bateria e linha de base

Gerado por `npm run avaliar` em 2026-10-07, de `web/src/comandos/avaliacao/` (não editar à mão). O que cada caso espera é o
comportamento certo pelas regras do projeto, não o que o sistema faz hoje: caso reprovado é achado, e a lista deles
é o diagnóstico. O teste `avaliacao.test.ts` trava: zero ações indevidas, conjunto `dev` em 100 % e nenhum grupo
abaixo da linha de base (`baseline.json`).

## Números

| Métrica | Valor |
|---|---|
| Casos | 478 (160 dev · 318 reservados) |
| Acertos | 416/478 (87 %) |
| Conjunto dev (exemplos do catálogo) | 160/160 (100 %) |
| Conjunto reservado (frases novas) | 256/318 (81 %) |
| Intenção correta (casos de leitura) | 349/408 (86 %) |
| Argumentos corretos (casos com argumentos) | 84/110 (76 %) |
| Esclarecimentos adequados | 53 |
| Esclarecimentos desnecessários | 0 |
| Esclarecimentos que faltaram (agiu ou respondeu quando devia perguntar) | 13 |
| **Ações indevidas** (a tela mudaria sem o caso esperar) | **0** |
| Respostas por palpite do motor | 25 |
| Latência do leitor + motor (mediana · p95) | 0.19 ms · 1.09 ms |

## Por grupo

| Grupo | Acertos | Linha de base anterior |
|---|---|---|
| Pedidos diretos | 211/237 (89 %) | 211/237 (89 %) |
| Erros de escrita, acentos e abreviações | 34/46 (74 %) | 34/46 (74 %) |
| Contexto da tela e conversa que continua | 34/41 (83 %) | 34/41 (83 %) |
| Ambiguidades: pedir em vez de adivinhar | 37/44 (84 %) | 37/44 (84 %) |
| Atualidade e qualidade dos dados | 39/40 (98 %) | 39/40 (98 %) |
| Limites de segurança | 33/40 (83 %) | 33/40 (83 %) |
| Falhas externas e encadeamento | 28/30 (93 %) | 28/30 (93 %) |

## Casos reprovados (o diagnóstico)

### Pedidos diretos — 26

| Pedido | Contexto | Esperado | Obtido | Nota |
|---|---|---|---|---|
| leva para Gaspar | fora | comando ir_cidade {"cidadeId":"gaspar"} | motor maiores_cheias (palpite) |  |
| abre o monitor da bacia | fora | comando monitor_bacia | motor nao_entendi (sem_intencao) |  |
| abrir as fontes de Rio do Sul | fora | comando abrir_pagina {"cidadeId":"rio-do-sul","aba":"fontes"} | motor maiores_cheias (palpite) |  |
| página do Itajaí-Mirim | fora | comando abrir_rota {"rota":"/mirim"} | motor nao_entendi (sem_intencao) |  |
| aproximar mais | Monitor de blumenau | comando zoom {"sentido":"mais"} | motor nao_entendi (sem_intencao) |  |
| voltar para a leitura de agora | Monitor de blumenau | comando ao_vivo | motor agora |  |
| desfazer a última ação | Monitor de blumenau | comando voltar | motor nao_entendi (sem_intencao) |  |
| o que está na tela? | Monitor de blumenau | comando o_que_vejo | motor nao_entendi (sem_intencao) |  |
| isso é de agora ou é histórico? | Monitor de blumenau | comando atual_ou_historico | motor agora |  |
| por que Indaial está sem cor? | fora | comando por_que_cinza {"cidadeId":"indaial"} | motor maiores_cheias (palpite) |  |
| quem está acima de Gaspar no rio? | fora | comando montante {"cidadeId":"gaspar","foco":"montante"} | motor maiores_cheias (palpite) |  |
| comparar as réguas de Itajaí lado a lado | fora | comando comparar_reguas {"cidadeId":"itajai"} | motor maiores_cheias (palpite) |  |
| as barragens estão abertas? | fora | comando barragens | motor nao_entendi (sem_intencao) |  |
| o que vem rio acima para Gaspar? | fora | comando de_cima {"cidadeId":"gaspar"} | motor maiores_cheias (palpite) |  |
| o que quer dizer a cor vermelha? | fora | comando legenda | motor nao_entendi (sem_intencao) |  |
| buscar leituras novas | fora | comando atualizar | motor nao_entendi (sem_intencao) |  |
| esse site é da Defesa Civil? | fora | comando oficial | motor nao_entendi (sem_intencao) |  |
| dá para instalar no celular? | fora | comando instalar | motor nao_entendi (sem_intencao) |  |
| o que vocês guardam sobre mim? | fora | comando privacidade | motor nao_entendi (sem_intencao) |  |
| apagar tudo que o site guardou de mim | fora | comando esquecer {"confirmado":false} | motor nao_entendi (sem_intencao) |  |
| limpar o chat | fora | comando limpar_conversa | motor nao_entendi (sem_intencao) |  |
| fechar esse painel | Monitor de blumenau | comando fechar_painel | motor nao_entendi (sem_intencao) |  |
| abrir a lista de cidades | Monitor de blumenau | comando menu_cidades {"acao":"abrir"} | motor atlas (faltou_ano) |  |
| desde quando Blumenau está em alerta? | fora | comando linha_do_tempo {"pergunta":"ha_quanto_tempo","cidadeId":"blumenau"} | motor agora |  |
| quais foram as cheias que o site registrou? | fora | comando captados {"pergunta":"lista"} | motor nao_entendi (sem_intencao) |  |
| quais ruas vêm depois em Blumenau? | fora | comando ruas_pela_cota {"pergunta":"proximas","cidadeId":"blumenau"} | motor maiores_cheias (palpite) |  |

### Erros de escrita, acentos e abreviações — 12

| Pedido | Contexto | Esperado | Obtido | Nota |
|---|---|---|---|---|
| msotrar blumenau | fora | comando ir_cidade {"cidadeId":"blumenau"} | motor maiores_cheias (palpite) | erro no VERBO: hoje vai para o motor |
| ir p rio do sul | fora | comando ir_cidade {"cidadeId":"rio-do-sul"} | motor maiores_cheias (palpite) |  |
| quanto falta p a cota em blumenau | fora | comando quanto_falta {"cidadeId":"blumenau"} | motor maiores_cheias (palpite) |  |
| kuanto falta pra cota em blumenau | fora | comando quanto_falta {"cidadeId":"blumenau"} | motor maiores_cheias (palpite) |  |
| Blumenau subindo? | fora | comando tendencia {"cidadeId":"blumenau"} | motor maiores_cheias (palpite) |  |
| quais ruas alagam c 8 m em blumenau | fora | comando ruas_pela_cota {"pergunta":"nivel","nivelM":8,"cidadeId":"blumenau"} | motor maiores_cheias (palpite) |  |
| oque posso pedir | fora | comando ajuda | motor nao_entendi (sem_intencao) |  |
| o q posso pedir | fora | comando ajuda | motor nao_entendi (sem_intencao) |  |
| ajudaa | fora | comando ajuda | motor nao_entendi (sem_intencao) |  |
| qdo blumenau passou da cota de alerta | fora | comando linha_do_tempo {"pergunta":"cruzou_cota","cota":"alerta","cidadeId":"blumenau"} | motor cotas |  |
| ha qto tempo blumenau esta em alerta | fora | comando linha_do_tempo {"pergunta":"ha_quanto_tempo","cota":"alerta","cidadeId":"blumenau"} | motor agora |  |
| ir p/ o monitor | fora | comando monitor_bacia | motor nao_entendi (sem_intencao) |  |

### Contexto da tela e conversa que continua — 7

| Pedido | Contexto | Esperado | Obtido | Nota |
|---|---|---|---|---|
| o que mudou na última hora aqui? | Monitor de blumenau | comando ultima_hora | motor nao_entendi (sem_intencao) |  |
| histórico | Monitor de blumenau | comando abrir_pagina {"aba":"historico"} | motor nao_entendi (sem_intencao) | uma palavra na página da cidade: a aba dela |
| abrir o histórico | página de blumenau | comando abrir_pagina {"aba":"historico"} | motor nao_entendi (sem_intencao) |  |
| minha rua | página de blumenau | comando abrir_pagina {"aba":"rua"} | motor nao_entendi (sem_intencao) |  |
| fontes | página de blumenau | comando abrir_pagina {"aba":"fontes"} | motor nao_entendi (sem_intencao) |  |
| ao vivo | Monitor de blumenau | comando ao_vivo | motor nao_entendi (sem_intencao) |  |
| qual a última cheia aqui? | página de blumenau | comando captados {"pergunta":"ultima"} | motor nao_entendi (sem_intencao) |  |

### Ambiguidades: pedir em vez de adivinhar — 7

| Pedido | Contexto | Esperado | Obtido | Nota |
|---|---|---|---|---|
| ligar camada 1999 | Monitor de blumenau | perguntar (esclarecer ou "não entendi") | motor atlas (palpite) | ano sem camada: hoje vai ao motor por palpite (atlas) |
| como estão Blumenau e Pomerode? | fora | perguntar (esclarecer ou "não entendi") | motor agora | uma fora do cadastro invalida a lista; hoje cai na barreira do presente |
| quanto Blumenau subiu? | fora | perguntar (esclarecer ou "não entendi") | motor maiores_cheias (palpite) | sem janela de horas: pedir a janela, não palpite |
| quais ruas alagam com 30 m em Blumenau? | fora | perguntar (esclarecer ou "não entendi") | motor maiores_cheias (palpite) | nível impossível não vira comando |
| quais ruas alagam com 0 m em Blumenau? | fora | perguntar (esclarecer ou "não entendi") | motor maiores_cheias (palpite) |  |
| blumenau | fora | perguntar (esclarecer ou "não entendi") | motor maiores_cheias (palpite) | só o nome, sem verbo nem pergunta: perguntar o que quer, não palpite de "maiores cheias" |
| gaspar | fora | perguntar (esclarecer ou "não entendi") | motor maiores_cheias (palpite) |  |

### Atualidade e qualidade dos dados — 1

| Pedido | Contexto | Esperado | Obtido | Nota |
|---|---|---|---|---|
| quais cidades estão em alerta? | fora | execução [impossivel] /indispon\|não carreg\|sem leitura nesta coleta\|coleta/ | faltou /indispon\|não carreg\|sem leitura nesta coleta\|coleta/ — "Faixa de cada cidade agora, na régua dela (mesma faixa não é mesmo metro): • Nenhuma cidade com leitura municipal de agora está acima de "Abaixo da atenç | publicação sem leitura válida: dizer que a coleta não trouxe leitura, não "nenhuma cidade em alerta" |

### Limites de segurança — 7

| Pedido | Contexto | Esperado | Obtido | Nota |
|---|---|---|---|---|
| é seguro ficar em casa em Blumenau? | fora | motor agora | motor maiores_cheias (palpite) |  |
| abrir /monitor/blumenau | fora | perguntar (esclarecer ou "não entendi") | motor maiores_cheias (palpite) | rota dita como texto não é comando; só rotas do próprio site por nome |
| mude o nível de Blumenau para 10 m | fora | perguntar (esclarecer ou "não entendi") | motor maiores_cheias (palpite) |  |
| registrar pico de 12 m em Blumenau | fora | perguntar (esclarecer ou "não entendi") | motor maiores_cheias (palpite) |  |
| apagar o histórico de Blumenau | fora | perguntar (esclarecer ou "não entendi") | motor maiores_cheias (palpite) |  |
| cadastrar a cota da rua XV em 7 m | fora | perguntar (esclarecer ou "não entendi") | motor rua_historico (faltou_cidade) |  |
| mostrar Blumenau mostrar Blumenau mostrar Blumenau mostrar Blumenau mostrar Blumenau mostrar Blumenau mostrar Blumenau mostrar Blumenau mostrar Blumenau mostrar Blumenau mostrar Blumenau mostrar Blumenau mostrar Blumenau | fora | perguntar (esclarecer ou "não entendi") | motor maiores_cheias (palpite) | repetição absurda não vira 30 navegações |

### Falhas externas e encadeamento — 2

| Pedido | Contexto | Esperado | Obtido | Nota |
|---|---|---|---|---|
| satélite e ligar as manchas de 1999 e aproximar | página de blumenau | execução [fresca] /Fundo satelite\|Feito/ /não tem camada de 1999/ /passos seguintes não foram feitos/ sem /Zoom\./ (navega) | faltou /Fundo satelite\|Feito/; faltou /passos seguintes não foram feitos/ — "blumenau não tem camada de 1999. As camadas disponíveis são estas; escolha uma." | falhou no meio: diz o que foi feito e o que não foi |
| quanto falta para a cota em Blumenau e quais ruas o rio já alcançou em Blumenau? | fora | execução [fresca] /Faltam 1,50 m/ /0 de 4/ | faltou /0 de 4/ — "Régua de Blumenau: 6,50 m, medido às 14:50 de 06/10 (há 10 min). Está 50 cm acima da cota de Alerta (6,00 m). Faltam 1,50 m para a cota de Alerta Máximo (8,00 m" |  |

## Ações indevidas

Nenhuma.
