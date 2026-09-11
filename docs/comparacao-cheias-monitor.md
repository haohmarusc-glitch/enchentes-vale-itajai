# Camadas no Monitor

O controle «Camadas de cheia» desenha uma camada sobre o mapa do Monitor, inclusive em tela cheia. A cidade vem da seleção do Monitor. Itajaí possui dez camadas históricas; Ituporanga possui oito cotas de consulta manual. O rótulo permanece visível quando o controle é recolhido. A área representa a fonte histórica, não confirmação de ruas alagadas no presente.

A comparação automática procura a menor diferença absoluta entre nível atual e pico histórico, exigindo cidade, identificador da régua e fonte do pico, além de leitura com frescor aceito pelo projeto. Exibe evento e diferença em metros. Durante a reprodução, a seleção automática fica pausada. Não há previsão ou detecção de subida implementada por este controle.

## Dados ainda necessários

- Os picos de todas as manchas de Itajaí estão nulos. Para comparar, documentar `pico_registrado.pico_m`, `regua` (identificador da estação compatível com a leitura) e `fonte`, confirmando também que o zero da régua não mudou desde o evento.
- As cotas de Ituporanga não têm vínculo confirmado com a régua atual nem com um ano específico. Permanecem manuais.
- A chuva histórica pode ser descrita por `chuva_7dias: {mm, inicio, fim, estacao, fonte}`. Só cadastrar acumulados documentados de sete dias, com período explícito. Hoje nenhum evento possui esse dado.
- A comparação da chuva atual ainda precisa de série acumulada validada para sete dias, com cobertura e estação comparáveis. Janelas móveis de 24/48 horas não devem ser somadas.

Portanto a integração visual está disponível, mas os avisos automáticos de proximidade durante uma subida e a comparação semanal completa continuam pendentes. Não preencher lacunas com estimativas sem fonte.

Verificação: testes de escolha por distância, recusa de régua diferente e leitura antiga; TypeScript e build; consulta manual no Chrome. Os polígonos são carregados sob demanda e os caminhos do canvas ficam em cache até mudar camada ou enquadramento.
