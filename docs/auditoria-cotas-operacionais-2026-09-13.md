# Auditoria de cotas operacionais — 13/09/2026

O fallback de primeiraCota aceitava seguranca_observada de Lontras e outras chaves documentais. Removido também dos comparadores de cota alcançada/próxima cota. cotasOperacionais.ts centraliza as cinco fases, inclui monitoramento e recusa valores não finitos. O monitor lista somente estas fases; os registros documentais permanecem no JSON.

Ibirama: cotas municipais preservadas em cotas_pendentes_de_vinculo, fora de cotas_m. A fonte municipal e as observações originais permanecem. O cadastro não comprova equivalência com DCSC-00020. O caminho de bruto estadual já impedia a classificação; a mudança também protege caminhos futuros que recebam leitura municipal. O aviso público explica a pendência. Não foram inventadas conversões.

Apiúna: cadastro sem cota, codigo_ana/codigo_dcsc nulos e fontes_tempo_real vazias. Coordenadas do registro fluviométrico 83500000 no inventário ANA arquivado em data/brutos/ana-inventario-api-2026-09-08.json, não confirmação de transmissão. A estação permanece candidata. docs/cotas-municipais/apiuna.md documenta os boletins municipais sem equivalência. A exclusão antiga passa a identificar DCSC-00178, não o município inteiro. Tronco: Lontras → Apiúna → Ascurra. Não foram criados tempos de trânsito.

O aviso do validador sobre regua_das_cotas não prova sozinho que existe pintura ao vivo: o caminho de leitura também importa. As outras quatro cidades com esse aviso continuam pendentes de auditoria documental específica; nenhum vínculo foi preenchido por suposição.
