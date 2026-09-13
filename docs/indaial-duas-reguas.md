# Indaial: duas réguas — 12/09/2026

## Atualização em 13/09/2026

Vínculo institucional confirmado no Chrome: https://www.facebook.com/indaialdefesacivil/posts/1441560437999883/ divulga exatamente o documento abaixo. Isso supera a pendência de autoria institucional registrada na alteração anterior (não identifica individualmente o editor do documento).

`scripts/coleta_indaial.py` lê a exportação pública TXT e entra em `coleta_niveis.py`. Usa apenas o primeiro bloco diário, seleciona o maior horário desse bloco, preserva Brasília sem fuso e recusa referência ausente, datas inválidas, futuro e conflitos. Aceita a grafia observada `1209/2026`; não interpreta `mm` como metros. Não converte a DCSC-00006 nem importa o arquivo histórico inteiro, que contém erros e divergências.

Teste real: 4,10 m em 12/09/2026 às 22h. Essa leitura é antiga no momento da consulta; o monitor mantém sua regra de idade e não deve pintá-la como atual. Atualização do documento não renova o horário da medição.

Deploy necessário na VPS para ativar o novo coletor no cron existente. Não foi implantado por esta alteração.

A imagem enviada pelo usuário mostra SDC-SC Indaial, atualização 18:34:52, nível 6,74 m. É a DCSC-00006 já coletada por `coleta_nivel_sc.py` e exibida pelo monitor como nível estadual bruto. Não é uma estação nova e não deve ser duplicada.

O documento enviado, [Nível do Rio Itajaí-Açu em Indaial](https://docs.google.com/document/d/1EN1iEU3lDUfRnOtPx6IjeSpoO7DMGd-iD4i2AdHiFvk/edit), distingue o monitoramento estadual na terceira ponte da régua dos fundos da Celesc. A escala normal/atenção/alerta/emergência de 3/4/5,5 m é associada à segunda. A última linha do dia no documento consultado era 4,29 m às 17h, enquanto a captura estadual mostra 6,74 m às 18h34. São lugares e horários diferentes: não calcular offset entre esses números.

O painel passa a nomear a estação estadual, dar acesso à fonte e explicar por que o número não recebe a classificação municipal. Foi removido o texto contraditório “sem leitura fresca” quando existe uma medição estadual apresentada logo abaixo.

O documento é uma fonte fornecida pelo usuário; sua autoria institucional não foi verificada nesta alteração. Não foram importados picos históricos nem promovida sua série a coleta governamental automática. Nenhuma escala foi atribuída à DCSC-00006 por inferência. A imagem não contém limites oficiais para essa régua.

Mudança de frontend: não exige alteração do coletor nem deploy na VPS.
