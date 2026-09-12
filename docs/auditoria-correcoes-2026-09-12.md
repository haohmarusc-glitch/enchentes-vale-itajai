# Correções da auditoria de navegador — 12/09/2026

## Problemas corrigidos

- Removidos os abrigos e painéis de previsão/chegada das telas públicas. Permanecem medições, fontes e comparações históricas.
- Ascurra usa a mesma classificação C18 no monitor regional, no piloto e nas páginas de cidade/rio. A associação exige DCSC-00003; outra régua não é promovida por proximidade. Leitura velha ou futura fica sem cor. O extremo 9,76 m continua sem classificação porque sua inclusão não está definida na fonte.
- O seletor de camadas municipal respeita a largura do celular. Conferência no Chrome: conteúdo e janela útil com 375 px, sem o overflow anterior de 564 px.
- O atalho de acessibilidade foca o conteúdo sem perder a rota. Filtros de ruas são reiniciados ao trocar de rio/cidade.
- Tela cheia tem alternativa CSS quando o navegador recusa a API nativa; Escape e o botão permitem sair.
- O painel selecionado acompanha as novas leituras. Chuva ausente distingue carregamento, falha e ausência de leitura válida.
- Textos da animação descrevem velocidade ilustrativa constante. Não associam movimento a velocidade real ou chegada da água.
- Corrigida a animação pendente do Leaflet ao sair rapidamente do mapa municipal, que causava erro `_leaflet_pos`.
- Lista de cidades sem duplicação de Itajaí; o piloto não lista botões de cidades externas.

## Validação

- 528 testes de lógica/dados aprovados; build TypeScript/Vite aprovado.
- Teste de fumaça aprovado com rede externa indisponível.
- Nova auditoria Playwright em 390 × 844 verifica rota do atalho, seletor, C18, tela cheia alternativa, isolamento municipal e limpeza de filtros, sem erros de página. Usa leituras simuladas apenas no teste.
- 79 arquivos de testes Python executados sem falha no Windows. Os testes de dois scripts POSIX são pulados somente no Windows e continuam obrigatórios na CI Linux.
- Ruff aprovado; validador: zero erros e 14 avisos preservados.
- CI passa a executar a auditoria de regressão após o build e o teste de fumaça.

## Pendências de dados, sem alteração de valores

Os 14 avisos dependem de conferência documental: seis códigos ANA, duas relações de trânsito, quatro divergências de datas históricas, cotas baixas de duas ruas e identificação da régua de referência das cotas em seis municípios. Não foram inventadas equivalências nem corrigidas datas por aproximação. A ausência de chuva em uma consulta não significa zero.

Esta alteração não modifica coletores, cron ou serviços da VPS. A publicação do frontend depende do merge e do deploy habitual do site.
