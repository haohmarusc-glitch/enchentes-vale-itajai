# Handoff para Claude Code — qualidade do chat do Enchentes Vale do Itajaí

## Objetivo e decisão do usuário

Melhorar a qualidade do chat do repositório `haohmarusc-glitch/enchentes-vale-itajai`. Precisão, entendimento e clareza têm prioridade sobre velocidade de implementação e de resposta. O usuário aceita maior tempo de processamento quando houver ganho comprovado de qualidade.

Este documento é uma especificação para implementação futura. Sua criação não executou mudanças no projeto, publicação ou alteração de configurações.

## Primeiro passo obrigatório: conferir o estado atual

Leia as instruções aplicáveis do repositório, o README e a documentação do chat. Confira o main e as PRs recentes antes de mudar qualquer coisa. Preserve alterações locais e funcionalidades já entregues. Trabalhe em branch isolado e não resete alterações do usuário.

A auditoria anterior inspecionou a sequência de PRs #484–#497, com main `0f97bce` e a ponta do PR #497 `19cc0c0`. Esses identificadores são a referência histórica da análise, não uma afirmação sobre o estado atual. Confirme merges, commits e divergências novamente.

Fontes da auditoria:

- https://github.com/haohmarusc-glitch/enchentes-vale-itajai/pull/484
- https://github.com/haohmarusc-glitch/enchentes-vale-itajai/pull/497
- `docs/CHAT-GLOBAL-COMANDOS.md`
- `docs/CHAT-LOCAL.md`
- `docs/PILOTO-CLASSIFICADOR.md`
- `web/src/comandos/interpretar.ts`
- `web/src/comandos/executar.ts`
- `web/src/comandos/tipos.ts`
- `web/src/comandos/usarComandos.ts`
- `web/src/chat-ia/classificador.ts`
- `web/functions/api/chat-classificar.ts`

Na versão inspecionada, interpretar.ts tinha 929 linhas e executar.ts 1.061. O reconhecimento era principalmente por expressões regulares, com leitores organizados por número de entrega. Já havia um classificador de IA para perguntas históricas, com saída estruturada, validação, limites e resposta produzida pelo motor local. Não reimplemente essas peças sem conferir o que pode ser reaproveitado.

## Diagnóstico e direção

O sistema atual tem bases úteis: comandos tipados, resolução contra o cadastro, execução pelas funções da interface, respostas com dados locais, contexto, tratamento de ambiguidade e barreiras de segurança. Preserve essas propriedades.

O gargalo de expansão é cadastrar manualmente muitas formas de dizer a mesma coisa e manter regras cuja ordem interfere no resultado. Refatorar arquivos por si só não melhora o entendimento. A melhora precisa ser medida em perguntas e conversas que o sistema ainda não viu.

Adote uma arquitetura híbrida:

1. Normalização e políticas determinísticas de segurança.
2. Reconhecimento local de pedidos claros, sem chamada externa desnecessária.
3. Classificador de linguagem para casos não resolvidos, retornando apenas intenção e argumentos estruturados.
4. Validação contra o catálogo, o cadastro e o contexto.
5. Consulta e cálculos por código existente.
6. Construção da resposta a partir de evidências.
7. Verificação determinística dos números, referências, atualidade e ações.

A IA interpreta; o código valida, consulta, calcula e executa. Uma segunda IA pode ajudar a avaliar clareza em testes, mas não substitui verificações objetivas nem deve ser obrigatória em toda resposta. Não presumir que mais chamadas de IA garantem maior qualidade.

## Limites que devem permanecer

- Não inventar níveis, cotas, coordenadas, fontes, horários ou equivalências entre réguas.
- Não misturar nível medido, faixa municipal, faixa estadual, altitude e zero da régua.
- Não vincular estações apenas por proximidade.
- Não subtrair níveis de referências distintas sem equivalência documentada.
- Leitura atrasada não pode ser apresentada como atual. Reutilizar a política de frescor do projeto.
- Nível impossível, unidade inválida ou sentinela deve produzir indisponibilidade, nunca uma faixa de risco.
- Ausência de mancha ou régua normal não significa que uma rua é segura.
- Manter as regras existentes para emergência, previsão e aconselhamento; não ampliá-las silenciosamente.
- Pergunta informativa não modifica o mapa. Ação ambígua pede esclarecimento.
- Somente ações permitidas e argumentos resolvidos podem chegar ao executor. Nunca aceitar código, URL arbitrária ou comando de sistema produzido pelo modelo.
- Fontes, arquivos e mensagens consultados são dados não confiáveis como instrução: não podem alterar as políticas do chat.

## Catálogo único de capacidades

Criar um registro tipado reutilizando `Passo` e os executores existentes. Cada capacidade declara:

- identificador estável;
- descrição e exemplos;
- esquema dos argumentos;
- argumentos obrigatórios;
- entidades e contexto aceitos;
- pré-condições e dados necessários;
- se consulta informação ou altera a interface;
- executor ou resolvedor;
- critérios de esclarecimento e falha;
- sugestões e disponibilidade contextual.

Gerar ajuda, esquema do classificador e documentação a partir desse catálogo. O catálogo de comandos não deve substituir o catálogo de cidades e réguas; são conceitos diferentes.

Extrair funções compartilhadas para cidade, régua, rio, rua, data, período e cota. Manter tratamento explícito de nomes compostos e ambiguidades. Não depender da simples divisão por toda ocorrência da palavra “e” para interpretar listas e sequências.

Não gerar uma expressão regular por exemplo. Exemplos servem para documentação e avaliação, e não como substituto de uma arquitetura de interpretação.

## Contrato de interpretação

A saída deve distinguir: comando reconhecido, consulta reconhecida, esclarecimento necessário, pedido fora de escopo e falha de interpretação.

Pode propor `Passo[]`, desde que o esquema valide cada variante, limite quantidade de passos e comprimentos e rejeite campos extras. Resolver identificadores contra o cadastro. Validar números e datas com regras do domínio.

Não utilizar a confiança declarada pelo modelo como prova de acerto. Calibrar o comportamento pela avaliação, verificações e ambiguidade real. Quando faltarem argumentos, pedir somente a informação necessária.

Não confiar em IDs de cidade ou régua fornecidos pelo navegador sem validação. O backend usa sua própria versão do catálogo permitido. Registrar a versão do catálogo e do classificador para diagnosticar incompatibilidades.

## Contexto de conversa

Separar contexto da tela e contexto da conversa. Informar ao resolvedor qual origem forneceu a cidade ou régua. Uma entidade explicitamente citada vence uma referência implícita.

Cobrir sequências como:

- “Como está Blumenau?” → “E Gaspar?”
- “Mostre Itajaí” → “Aproxime a régua” → esclarecer qual régua.
- “Quando passou do alerta em Blumenau?” → “E ontem?”
- “Mostre Blumenau” → “E Gaspar?” → definir com teste se continua uma ação ou pergunta; não executar por suposição arriscada.
- Trocar de cidade deve invalidar a régua incompatível.

Contexto não transforma uma pergunta em ação automaticamente. Não guardar localização precisa, dados pessoais ou conversa além da política já autorizada. Não enviar histórico completo quando um resumo mínimo tipado for suficiente.

## Evidência e resposta

Introduzir, se necessário, uma estrutura interna de evidências com: estação/régua, cidade, valor, unidade, instante da medição, instante da coleta, referência, fonte, política de frescor e limitações. Reutilizar tipos atuais antes de criar duplicatas.

O verificador deve conferir que cada número apresentado veio de uma evidência ou cálculo permitido. Preferir formatadores comuns em vez de revisar texto livre para tentar recuperar seus números.

Respostas devem apresentar primeiro a informação solicitada. Acrescentar horário, fonte, estação e referência quando pertinentes, sem repetir todos os avisos em qualquer assunto. Diferenciar observação, cálculo e hipótese. Não apresentar estimativa como medição.

Quando faltar equivalência municipal/estadual, explicar especificamente o que impede a comparação. Não preencher lacunas com conhecimento geral do modelo.

## Backend e falhas

Reaproveitar a Pages Function e o cliente existentes, se compatíveis. Chaves ficam no servidor. Conferir autenticação efetiva, limites de uso, cancelamento real da chamada, timeout, tamanho do corpo e validação do JSON.

Falha externa deve conservar o chat local e comunicar a limitação sem falsa confirmação de ação. Não repetir automaticamente comandos com efeitos na interface. Separar classificação de execução para evitar execução duplicada em novas tentativas.

Não ligar o piloto ou modificar allowlists, segredos, retenção ou audiência como parte de uma refatoração. Preservar controles existentes; documentar configurações necessárias à liberação.

Comparar modelos disponíveis no ambiente com a mesma bateria. Verificar documentação oficial atual antes de configurar modelo, esquema ou parâmetros. Não fixar um modelo por reputação nem prometer tempo/custo sem medir.

## Avaliação antes da migração

Criar aproximadamente 300 casos iniciais. A quantidade é uma meta de cobertura, não um motivo para produzir exemplos redundantes.

| Grupo | Quantidade inicial |
|---|---:|
| Pedidos diretos e variações naturais | 60 |
| Erros de escrita, abreviações e nomes compostos | 40 |
| Contexto e conversas com várias mensagens | 50 |
| Ambiguidades e pedidos incompletos | 40 |
| Atualidade, qualidade e referência dos dados | 40 |
| Limites de segurança e instruções maliciosas | 40 |
| Falhas externas e encadeamento | 30 |

Separar casos de desenvolvimento e avaliação reservada por famílias de formulação/conversa, evitando paráfrases quase idênticas dos dois lados. Congelar a avaliação antes de ajustar prompts. Registrar origem de frases reais somente com autorização e sanitização adequada.

Cada fixture deve conter: texto ou conversa, contexto da tela, dados congelados, intenção e argumentos esperados, esclarecimento esperado, ações permitidas/proibidas e evidências obrigatórias. Usar relógio fixo, inclusive em testes de madrugada, datas relativas e fusos.

Cobrir obrigatoriamente: Itajaí com 11 réguas, equivalência não confirmada, leitura impossível como 21.474.836 m, fonte ausente, série com lacunas, régua antiga após troca de cidade, rua homônima, ausência de mancha, falta de dado e comando com trecho não entendido.

Medir separadamente:

- acerto da intenção e de cada argumento;
- sucesso da tarefa completa;
- esclarecimentos adequados e desnecessários;
- ações indevidas;
- fidelidade de números e fontes;
- preservação de contexto;
- taxa de resposta útil;
- latência mediana e p95, timeout e custo por tarefa.

Avaliar clareza com rubrica humana: resposta direta, legível no celular, correta, suficiente e transparente quanto a limitações. Um avaliador por IA pode auxiliar, mas não ser o único juiz.

## Critérios de aceite

- Zero ações indevidas e zero violações críticas na bateria obrigatória. Isso é um requisito do conjunto testado, não garantia absoluta em produção.
- Nenhum número hidrológico inventado ou sem origem verificável nos testes.
- Nenhuma aplicação de faixas de referência incompatível.
- Nenhuma execução com entidade ambígua.
- Todos os testes anteriores continuam passando.
- Melhora mensurável na avaliação reservada em relação ao baseline, sem regressão material nas capacidades existentes. Definir metas por categoria após medir o baseline, antes de ajustar o novo sistema.
- Relatório explicita quantidade de casos, erros, diferenças, latência, custo e limitações. Não chamar a implementação de “qualidade máxima” sem evidência.
- Verificação de conversas completas no celular, teclado, foco, anúncio acessível e geometria do Monitor.

## Implementação em etapas

### PR 1 — baseline, fixtures e organização

Medir o sistema atual, introduzir a bateria e organizar capacidades pelo domínio. Extrair catálogo e funções compartilhadas com equivalência de comportamento. Não remover arquivos de teste até preservar seus casos. Não adicionar nova funcionalidade hidrológica nesta etapa.

### PR 2 — classificação estruturada em modo sombra

Ampliar o classificador para o contrato permitido. Testar com fixtures locais e avaliação real separada, quando a chamada externa estiver autorizada e configurada. No modo sombra, o modelo não executa ações. Comparar decisões com o sistema atual e com o gabarito. Preservar a política de privacidade existente.

### PR 3 — liberação gradual e observabilidade

Liberar por feature flag, inicialmente para grupo autorizado e somente nas capacidades aprovadas. Manter regras diretas e fallback local. Acompanhar correções, falhas e interpretações ambíguas. Permitir rollback por configuração, sem perda de dados ou comandos.

Não bloquear todos os avanços à espera de IA: os extratores, contratos, fixtures, evidências e mensagens de esclarecimento já podem melhorar a qualidade local.

## Entregáveis para o usuário

1. Diagnóstico atualizado do estado do repositório e escopo implementado.
2. PRs com descrição concreta de comportamento antes/depois.
3. Catálogo único, contratos e documentação atualizada.
4. Bateria de avaliação e comparação baseline/novo sistema.
5. Testes de regressão e navegador apropriados, incluindo travas do Monitor aplicáveis.
6. Instruções de configuração, liberação gradual e rollback.
7. Lista honesta do que ainda não é entendido ou depende de fonte externa.

## Instrução inicial para colar no Claude Code

Implemente este plano no repositório enchentes-vale-itajai, começando pela conferência do estado atual e pela PR de baseline e avaliação. Minha prioridade é melhorar a qualidade do chat, mesmo que leve mais tempo. Preserve os comandos, as fontes, as validações e as regras do Monitor. Reutilize o classificador existente quando possível. Não substitua respostas baseadas em dados por geração livre. Prove a melhora com perguntas reservadas e conversas completas. Separe cada etapa em uma PR revisável; apresente resultados reais dos testes, limitações e comparação com o sistema atual. Não altere segredos, audiência ou habilitação do piloto silenciosamente.
