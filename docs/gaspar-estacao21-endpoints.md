# Gaspar: estação 21 — conferência de 12/09/2026

- Página e nível atual: GET https://defesacivil.gaspar.sc.gov.br/estacao/ver/21
- Tabela: GET https://defesacivil.gaspar.sc.gov.br/monitoramento/tabela
- Histórico: POST https://defesacivil.gaspar.sc.gov.br/estacao/baixar-historico, formulário `codest=21&inicio=2026-09-12&fim=2026-09-12`.
- Validação do período usada pelo site: POST no mesmo endpoint com `?validar`. O JavaScript informa limite de um ano por pedido.

Não foi encontrada API JSON de nível no código da página: nível, carimbo e série do gráfico vêm incorporados ao HTML. O endpoint de histórico respondeu HTTP 200, com nome `.xls` e MIME de Excel, mas seu conteúdo é uma tabela HTML. A resposta do dia foi preservada em `data/brutos/gaspar-estacao21-historico-2026-09-12.html`.

As dez leituras retornadas para o dia têm `manual=1`, entre 01:01 e 17:02. A última é 4,26 m. Isso é evidência de registros marcados como manuais; não permite prometer atualização a cada 15 minutos. Não se troca o carimbo da medição pelo horário da consulta.

## Legenda da própria estação

- Normalidade: nível menor que 5,00 m.
- Atenção: nível maior que 5,00 m **ou** chuva atual maior que 6,00 mm.
- Emergência: nível maior que 7,00 m.

Não há faixa de alerta a 6 m nesta legenda. O monitor usa a parcela de nível da legenda; não afirma reproduzir o estado oficial que também depende da chuva. Em 5 m exatos, inclusão não definida: sem classificação. Em 7 m exatos, atenção. As faixas anteriores do Plano (5/6/7) e a legenda observada em 03/09 ficam em `cotas_divergencias`. O conferidor do Plano continua apontando a diferença de 6 m, intencionalmente.

A chuva aparece como `---` na página detalhada, embora o histórico traga zeros. Não incorporamos esses zeros como chuva observada. A cor indica faixa da régua, não mancha de alagamento ou confirmação de água nas ruas. As cotas de ruas existentes não foram convertidas nem alteradas.

## Integração e publicação

O coletor tenta a tabela e, caso ela falhe ou não tenha a régua, lê a página 21 com identificação exata, campo de nível e data. A coleta continua preservando as demais cidades em caso de falha. O deploy na VPS é necessário para ativar essa alternativa; acesso bem-sucedido deste PC não garante acesso da VPS. A leitura recente é requisito para pintar; fonte antiga permanece sem cor.
