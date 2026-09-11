# Verificação das réguas — 10/09/2026, aproximadamente 22:11–22:12 BRT

Consulta direta pelo PC; não é diagnóstico de conectividade da VPS. Nenhuma cota ou regra de cor foi alterada.

## Gaspar — B3 concluído

Fonte: https://defesacivil.gaspar.sc.gov.br/estacao/ver/21 (HTTP 200).

- Situação publicada: NORMALIDADE; nível 2,58 m; medição 10/09/2026 19:07.
- Chuva atual e acumuladas: `---`, não zero.
- Legenda literal em valores: normalidade <5,00 m; atenção >5,00 m OU chuva atual >6,00 mm; emergência >7,00 m. Não exibiu degrau de alerta nessa consulta.
- `python scripts/coleta_gaspar.py --seco` funcionou e extraiu a mesma leitura da tabela. Outros sensores tinham horários de 22:09/22:10; o nível de Gaspar continuava em 19:07.
- A leitura ultrapassava o limite de 180 minutos do frontend. Acesso local e parser funcionam; falta atualização do nível na fonte. Não estender o limite para fazer a cidade ganhar cor.
- A ausência de alerta na legenda não autoriza remover a cota do Plano de Contingência. C10 continua aberto; o episódio de ALERTA a 1,74 m não foi explicado por esta consulta.

## Brusque — B4 concluído

| Página | Fonte publicada | Última medição | Nível | Legenda |
|---|---|---|---|---|
| https://defesacivil.brusque.sc.gov.br/estacao/ver/4 | ANA, Ponte Estaçada | 08/09/2026 06:28 | 1,10 m | normalidade <4 m; atenção >4 m OU chuva atual >30 mm; emergência >7 m |
| https://defesacivil.brusque.sc.gov.br/estacao/ver/79 | DCSC, Ponte Estaiada | 10/09/2026 22:10 | 2,02 m | normalidade <3 m; atenção >3 m OU chuva atual >6 mm; emergência >5 m |

Ambas responderam HTTP 200 e publicaram NORMALIDADE. Estação 4 está antiga; estação 79 tinha chuva atual 0,00 mm e 33,80 mm/24h. As legendas diferem: não misturar leitura de uma com cotas da outra. C13 permanece necessário para confirmar zero/referência e aplicação das faixas ao coletor utilizado no projeto.

## Envios confirmados

C15 Vidal Ramos: `1a08dfcbf6b86e29`; C16 Lontras: `1a08dfcc2a0fa03d`; C17 Botuverá: `1a08dfcc58beb30b`; C18 Ascurra: `1a08dfcc898b64ca`; C19 Indaial: `1a08dfccc7693da7`; C22 Ituporanga: `1a08dfccf0e61bca`. Todos confirmados como SENT pelo Gmail em 10/09/2026.

C20 Guabiruba aprovado, sem destinatário confirmado. C21 Itajaí não deve ser enviado, por instrução expressa de Jefferson.

## Itajaí

O cadastro já contém cotas DC-01–DC-11. DC-01–DC-09 têm `alerta_automatico: false`, respeitado por `reguasNoMapa.ts` devido à maré. DC-10/DC-11 têm classificação habilitada quando há leitura recente. A antiga pendência genérica de obter todas as cotas estava desatualizada.
