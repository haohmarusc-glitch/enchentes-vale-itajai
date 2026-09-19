# Fechamento documental — 19/09/2026

Auditoria pelo Chrome, com confronto de dados locais. Este arquivo registra evidências e a proposta de alteração; não modifica cadastro, coletor, produção ou pedidos externos.

## Rio do Sul — conferência concluída

Fonte: [Defesa Civil municipal](https://defesacivil.riodosul.sc.gov.br/), menu **Histórico de Cheias**. A URL não muda ao abrir o menu. A tabela declara como origem a Defesa Civil de Rio do Sul / Exportação de Dados. Não identifica nominalmente a régua histórica nem seu zero.

Confronto com os nove registros em `enchentes-resolucao-2026-09-19/data/enchentes.json`:

| Cadastro atual | Pico (m) | Tabela municipal | Resultado |
|---|---:|---|---|
| 1954-10 | 10,70 | Outubro/1954, 10,70 m | Confere |
| 1957-08 | 10,65 | Agosto/1957, 10,65 m | Confere |
| 1984-08 | 12,80 | Agosto/1984, 12,80 m | Confere |
| 2011-09 | 12,96 | Setembro/2011, 12,96 m | Confere |
| 2015-10 | 10,71 | Outubro/2015, 10,71 m | Confere |
| 2017-06 | 10,89 | Junho/2017, 10,89 m | Confere |
| 1911-05 | 12,20 | Outubro/1911, 12,20 m | Mesmo pico, mês divergente |
| 2023-10-07 | 11,86 | 13/10/2023, 11,86 m | Mesmo pico, dia divergente |
| 2023-11-18 | 13,04 | 17/11/2023, 13,04 m | Mesmo pico, dia divergente |

**Os seis solicitados estão confirmados.** Para adotar o histórico municipal como fonte dos nove, três registros precisam também da conciliação de data. Não atribuir à Prefeitura as datas antigas que ela não publica. Preservar os dados anteriores como divergência/proveniência, inclusive a comparação já existente com a série ANA de novembro/2023.

Quatro inclusões sustentadas diretamente pela tabela, com precisão de mês:

| Data | Pico (m) |
|---|---:|
| 1983-05 | 7,35 |
| 1983-07 | 13,58 |
| 1983-09 | 7,60 |
| 2013-09 | 10,39 |

Rótulo proposto: **Defesa Civil de Rio do Sul — Histórico de Cheias**, acompanhado da URL e consulta em 19/09/2026. Referência de régua não informada. Não rotular como ANA nem Ponte Dom Tito Buss apenas porque essa estação aparece no painel atual. A tabela consultada não resolve a referência altimétrica.

## Brusque — captura do portal novo obtida

[Portal de Itajaí com Brusque selecionada](https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/rios?municipio_id=2), aberto e capturado visualmente no Chrome nesta rodada:

- Identificação: **Estação MKS DCSC-00019**.
- Nível: **1,96 m**.
- Medição: **19/09/2026, 20:00**, conforme exibido na página.
- Fonte declarada: **Brusque**.
- Legenda do gráfico: **Atenção (3,5 m), Alerta (5 m), Emergência (6 m)**.

A captura foi exibida na conversa. O cabeçalho verde permanece com o texto “Situação atual em Itajaí” e data de 18/09/2026 às 17h35; não é o carimbo da medição de Brusque. O carimbo correto está no cartão da estação.

**A seleção e a leitura atual estão comprovadas. Os limites não estão conciliados.** O portal novo relaciona explicitamente o código a 3,5/5/6, diferente dos 3/5 da página municipal DCSC e dos 4/7 da ANA. Não alterar automaticamente a decisão de manter DCSC 3/5. Acrescentar esta terceira configuração à divergência documental e pedir vigência/referência ao operador.

O [boletim de 30/10/2023](https://www.facebook.com/defesacivilbrusque/posts/pfbid0Ao5RGThRxdWkMF92Y91dWtG6rq6qErTexYFKuA1LzskB6VBD72TgXsa99x5TUrxDl) informa 3,18 m em atenção, mas não identifica o código. É evidência histórica favorável ao limite de 3 m, não prova de vigência atual. A nova captura também não estabelece equivalência entre essa régua e as cotas de rua.

## Itajaí — divergências preservadas

| Estação | Plano v17: atenção/alerta/emergência (m) | Portal capturado anteriormente (m) |
|---|---|---|
| DC-01 | 1,16 / 1,36 / 1,56 | 1,21 / 1,61 / 1,75 |
| DC-07 | 1,00 / 1,35 / 1,65 | 1,00 / 1,40 / 1,50 |
| DC-08 | 1,80 / 2,30 / 2,89 | 1,70 / 2,30 / 2,89 |
| DC-09 | 1,12 / 1,32 / 1,52 | 1,22 / 1,42 / 1,62 |

Não foi localizada declaração municipal de substituição do Plano v17. Preservar a decisão de cadastro nele baseada e a divergência documentada.

O original municipal de **09/09/2011 às 17h30** continua não recuperado. Há reprodução secundária anteriormente localizada; ela não foi promovida a original. A série oficial recuperada permanece nos dois boletins de 10/09, 13h30 e 16h40. Não afirmar máximos do evento a partir deles.

## Taió e Timbó — perguntas documentais pendentes

- **Taió:** a estação apresentada como “Nível no Centro Rio Itajaí” corresponde à régua instalada na nova passarela em 13/10/2022? Solicitar código, coordenadas e referência do zero; se forem instrumentos distintos, esclarecer quais limiares pertencem a cada um.
- **Timbó:** a escala publicada em 02/07/2026, referente ao Rio Benedito (até 2 m; 2,01–3; 3,01–4,29; a partir de 4,30), se aplica a qual estação/ponto? Solicitar coordenadas, referência e início de vigência. A data da publicação não prova a data de implantação da escala.

Nenhum contato foi enviado nesta rodada.

## Gaspar — houve nova medição

[Estação 21](https://defesacivil.gaspar.sc.gov.br/estacao/ver/21), conferida no Chrome:

- **1,45 m, medido em 19/09/2026 às 18h01**, fonte DC. Gaspar, situação de normalidade.
- A observação anterior era 1,32 m em 18/09 às 18h03. Diferença entre os carimbos observados: 23h58; isso não prova que não tenham existido leituras intermediárias.
- Cadência oficial não declarada na página consultada.
- Não foi repetido nesta rodada o teste de acesso pela VPS/IP **65.108.154.111**. A página abrir pelo PC não comprova liberação desse IP.

Texto de consulta já preparado em `PENDENCIAS-ENCHENTES-2026-09-19.md`; permanece sem envio. Preservar o horário real da medição, sem renová-lo por causa de uma consulta bem-sucedida.

## INMET e C24 — consulta autenticada concluída

Ao acessar o caminho de acesso à informação no [Fala.BR](https://falabr.cgu.gov.br/web/cidadao/novo-informa-br), o site informou que pedidos e histórico migraram para o [Informa.BR](https://informabr.cgu.gov.br/). Após o usuário fazer login diretamente no Chrome, foram consultados a listagem federal e os detalhes dos dois protocolos. A listagem sem filtros exibiu total de dois pedidos.

- **[INMET — 21210.009435/2026-61](https://informabr.cgu.gov.br/cidadao/pedido/21210009435202661):** situação **Cadastrada**, responsável **MAPA**, prazo confirmado na tela de detalhes **22/09/2026**. Histórico completo: cadastro em 01/09 às 23h53; alterações de classificação em 02/09 às 09h53, incluindo subassunto INMET — Redes de observações meteorológicas e de transmissão de dados. Não há resposta ou prorrogação no histórico exibido nesta consulta.
- **[Cemaden anterior — 01217.006547/2026-93](https://informabr.cgu.gov.br/cidadao/pedido/01217006547202693):** situação **Concluída**, decisão **Acesso Concedido**, resposta em **10/09/2026 às 14h34**, um anexo. A interface disponibiliza recurso até **21/09/2026 às 23h59**; isso não obriga a recorrer nem transforma o C24 em recurso.
- **C24 — Cemaden:** texto pronto em `enchentes-auditoria-2026-09-19/docs/oficios-prontos.md`, seção C24. Pedido novo sobre 421320321H (Pomerode) e 420290901H (Brusque), referenciando o anterior. **Não aparece protocolado na listagem federal consultada.** Nenhum pedido foi enviado nesta rodada.

### O que a resposta anterior do Cemaden já informa

A resposta foi aberta no Chrome. Ela declara que as PCDs hidrológicas têm sensor de chuva e de nível, informa transmissão a cada **10 minutos com chuva** e **1 hora sem chuva**, horários em **UTC**, dados brutos sujeitos a falhas e lacunas, e orienta solicitar acesso programático histórico por **ped@cemaden.gov.br**.

Consequência para o C24: não afirmar que variável e cadência nunca foram respondidas. A pergunta complementar deve pedir a aplicabilidade dessas regras **à estação específica**, a unidade e referência do nível, curso d'água, acesso às leituras hidrológicas, limiares e histórico/inativação. A orientação de webservice foi apresentada no contexto de dados pluviométricos; não presumir que assegure acesso ao nível hidrológico.

Não foi enviado e-mail para ped@cemaden.gov.br, recurso ou pedido novo. O conteúdo acima é uma consulta autenticada, não um protocolo de envio.
