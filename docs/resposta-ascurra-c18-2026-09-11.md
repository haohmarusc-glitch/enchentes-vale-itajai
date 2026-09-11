# Resposta da Defesa Civil de Ascurra — C18

Recebida em 11/09/2026 às 08:48 BRT, em resposta ao assunto «Cotas de acionamento do Itajaí-Açu e referência da estação DCSC-00003». Remetente institucional autenticado no Gmail (SPF, DKIM e DMARC aprovados). Sem anexos. Este documento resume apenas os dados técnicos, sem reproduzir a conversa ou os contatos pessoais.

## Informações recebidas

- A DCSC-00003 fica na Ponte do Beber, sobre o Itajaí-Açu: 26°57'40.7"S, 49°22'22.8"W.
- Faixas municipais estabelecidas com base nas elevações anteriores: até 8,50 m monitoramento; 8,50–9,76 m atenção; 9,76–10,76 m alerta; acima de 10,76 m emergência.
- Não existe referência de faixas estabelecida pelo estado sobre as cotas municipais, segundo a resposta. Não foi fornecido deslocamento numérico.
- A régua física do Ribeirão São Paulo não foi nivelada, não é oficial e deixou de ser utilizada para divulgação após a instalação da estação estadual. Servia ao acompanhamento da evolução pela população.

## Incorporação

`data/estacoes.json` passa a registrar régua, coordenadas e faixas, com crédito à COMPDEC. A página da cidade mostra a descrição literal dos intervalos. Nenhuma cota de rua, pico histórico ou camada de inundação foi inferida desta resposta.

O coletor estadual ainda publica esta leitura como bruta (`usar_para_cota=false`) em arquivo separado. Esta alteração de cadastro não promove a leitura automaticamente. A integração ao fluxo de níveis operacionais e os limites inclusivos/exclusivos das faixas devem ser testados antes de liberar cores: a resposta diz expressamente emergência **acima de** 10,76 m, enquanto a lógica genérica usa maior ou igual. O C18 está respondido; a ativação operacional permanece pendente.

## Conferência da caixa de e-mail

Em 11/09/2026, buscas incluindo recebidas, arquivadas, spam e lixeira localizaram esta nova resposta desde os envios de 10/09. As respostas anteriores da EPAGRI (09/09), ANA (08/09), Itajaí (02/09) e UNIVALI (31/08 BRT) já constavam do acompanhamento. Ascurra não enviou arquivos de geometria nem chuva semanal. Nenhuma mensagem foi enviada nesta verificação.
