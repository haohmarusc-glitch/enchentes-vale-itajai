# Pesquisa de picos históricos — 14 municípios

Consulta: 24/09/2026. Referência de escopo: PICOS-FALTANTES.md fornecido pelo usuário.

**Resultado:** levantamento com fontes e pendências para todas as 14 cidades. Não foi possível fechar todos os eventos históricos. Itajaí permanece sem máximo numérico exato identificado por régua nas fontes consultadas.

Os dados geográficos extraídos anteriormente do ArcGIS são outro conjunto: cotas em ruas e lotes não equivalem a picos de rio. Não usar o máximo dessas cotas como pico municipal.

Foram organizadas 38 evidências: 20 pico_declarado, 1 divergencia, 7 maximo_da_sequencia, 4 nivel_historico, 1 data_conflitante, 1 pico_sem_valor_exato, 4 leitura_nao_pico. Incluem corroborações de registros existentes e eventos adicionais de 2024/2026; não são todos registros novos.

Nenhuma alteração foi feita na base do projeto. Os dados estão em JSON com fontes, classe, régua, confiança e observações. A confiança é baixa quando a régua exata falta, mesmo que o documento seja oficial. Máximos de sequências são candidatos sujeitos à completude da série. Datas anuais não receberam dia ou mês inventados. Horários foram preservados como publicados.

## Cobertura por município

| Município | Resultado e pendência |
|---|---|
| Itajaí | Sem pico numérico exato por régua confirmado. Há limite qualitativo em 2011 e leituras em 2023. Prioridade para séries locais CEPSUL, Murta, SEMASA, Vitalmar, Itamirim e demais réguas. |
| Ascurra | Leitura localizada na Ponte do Beber em 2026; históricos do documento continuam pendentes. |
| Lontras | Máximo DCSC de maio/2024 encontrado; históricos anteriores continuam pendentes. |
| Vidal Ramos | Máximos de novembro/2023, maio/2024 e notícia de setembro/2026; régua exata pendente. |
| Guabiruba | Nenhum pico municipal utilizável confirmado nesta pesquisa. Não aproveitar cotas altimétricas nem níveis de Brusque. |
| Ituporanga | Máximos DCSC de outubro/2023, novembro/2023 e maio/2024; pico central em 2017. Não associar automaticamente à ANA 83145140, Barragem Sul jusante. |
| Ibirama | Nenhum pico municipal utilizável confirmado nesta pesquisa; leituras e simulações de barragens não fecham a lacuna. |
| Apiúna | Série municipal de maio/2022 encontrada; falta unidade explícita e confirmação do pico e da régua. |
| Ilhota | Fonte municipal histórica usa medição de Gaspar, sem régua local naquele relato. Não importar como pico de Ilhota nem concluir ausência de régua atualmente. |
| Rio dos Cedros | Tabela histórica e sequências oficiais encontradas; régua não nomeada e datas de 2014 e 2020/2021 exigem revisão. |
| Trombudo Central | Recorde de 1983 encontrado e 2023 corroborado; divergência 17h/18h preservada. |
| Botuverá | Pico explícito em setembro/2026; históricos antigos continuam pendentes. Registro 2023 existente no documento não foi revalidado por nova fonte aqui. |
| Timbó | Fontes para 1992, 2011, 2014 e outubro/novembro de 2023; divergência de 2011 não resolvida. |
| Taió | Máximos DCSC de outubro/novembro de 2023 e maio/2024; históricos antigos do documento continuam pendentes. |

## Evidências numéricas

Em tabelas estaduais, DCSC identifica a rede, mas não resolve o ponto exato ou o zero de cada régua. O campo rio permanece nulo quando não está identificado no trecho. Valores com classe diferente de pico declarado precisam de verificação adicional.

| ID | Município | Data | Hora | Valor publicado | Classe | Fonte |
|---|---|---|---|---:|---|---|
| P001 | Taió | 2023-10-09 | 13:00 | 12,39 m | pico_declarado | [out23](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_010_2023.pdf) |
| P002 | Ituporanga | 2023-10-12 | 18:00 | 6,92 m | pico_declarado | [out23](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_010_2023.pdf) |
| P003 | Timbó | 2023-10-12 | 21:00 | 7,46 m | pico_declarado | [out23](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_010_2023.pdf) |
| P004 | Vidal Ramos | 2023-11-17 | 08:00 | 4,86 m | pico_declarado | [nov23](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_011_2023.pdf) |
| P005 | Ituporanga | 2023-11-18 | 10:00 | 5,25 m | pico_declarado | [nov23](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_011_2023.pdf) |
| P006 | Trombudo Central | 2023-11-17 | 18:00 | 8,71 m | pico_declarado | [nov23](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_011_2023.pdf) |
| P007 | Taió | 2023-11-17 | 21:00 | 10,37 m | pico_declarado | [nov23](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_011_2023.pdf) |
| P008 | Timbó | 2023-11-03 | 21:00 | 7,61 m | pico_declarado | [nov23](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_011_2023.pdf) |
| P009 | Vidal Ramos | 2024-05-18 | 22:00 | 3,43 m | pico_declarado | [mai24](https://www.aguas.sc.gov.br/jsmallfib_top/Diretoria%20de%20Recursos%20Hidricos/Relatorios/Boletim_Hidrometeorologico_62.pdf) |
| P010 | Ituporanga | 2024-05-24 | 05:00 | 3,54 m | pico_declarado | [mai24](https://www.aguas.sc.gov.br/jsmallfib_top/Diretoria%20de%20Recursos%20Hidricos/Relatorios/Boletim_Hidrometeorologico_62.pdf) |
| P011 | Taió | 2024-05-19 | 13:00 | 8,47 m | pico_declarado | [mai24](https://www.aguas.sc.gov.br/jsmallfib_top/Diretoria%20de%20Recursos%20Hidricos/Relatorios/Boletim_Hidrometeorologico_62.pdf) |
| P012 | Lontras | 2024-05-19 | 09:00 | 7,09 m | pico_declarado | [mai24](https://www.aguas.sc.gov.br/jsmallfib_top/Diretoria%20de%20Recursos%20Hidricos/Relatorios/Boletim_Hidrometeorologico_62.pdf) |
| P013 | Vidal Ramos | 2026-09-01 | — | 3,87 m | pico_declarado | [nd26](https://ndmais.com.br/tempo/avenida-e-interditada-apos-rio-atingir-51-metros-acima-do-nivel-e-sair-da-calha-em-cidade-de-sc/) |
| P014 | Botuverá | 2026-09-01 | 02:00 | 5,85 m | pico_declarado | [nd26](https://ndmais.com.br/tempo/avenida-e-interditada-apos-rio-atingir-51-metros-acima-do-nivel-e-sair-da-calha-em-cidade-de-sc/) |
| P015 | Trombudo Central | 1983 | — | 6,22 m | pico_declarado | [ndtrom](https://ndmais.com.br/tempo/atingiu-metade-da-cidade-diz-prefeita-de-trombudo-central-sobre-maior-enchente-da-historia/) |
| P016 | Timbó | 1992 | — | 10,42 m | pico_declarado | [jmv](https://jornaldomediovale.com.br/geral/cheia_de_2011_foi_a_maior_de_todas_no_rio_benedito-112538/) |
| P017 | Timbó | 2011 | — | 9,86 m | pico_declarado | [timbo](https://timbonet.com.br/noticia/sessao-ordinaria-ocorre-com-participacao-em-tribuna-da-defesa-civil-municipal-e-rede-feminina) |
| P018 | Timbó | 2014 | — | 9,58 m | pico_declarado | [timbo](https://timbonet.com.br/noticia/sessao-ordinaria-ocorre-com-participacao-em-tribuna-da-defesa-civil-municipal-e-rede-feminina) |
| P019 | Timbó | 2011 | — | 10,01 m | divergencia | [jmv](https://jornaldomediovale.com.br/geral/cheia_de_2011_foi_a_maior_de_todas_no_rio_benedito-112538/) |
| P020 | Ituporanga | 2017-06-05 | 05:00 | 2,95 m | pico_declarado | [itup17](https://www.jornaldepomerode.com.br/diversas-regioes-de-sc-ja-sofrem-com-as-consequencias-da-chuva/) |
| P021 | Rio dos Cedros | 2009-09-28 | — | 6,42 m | pico_declarado | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P022 | Rio dos Cedros | 2010-04-26 | — | 6,98 m | maximo_da_sequencia | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P023 | Rio dos Cedros | 2010-05-08 | — | 6,19 m | maximo_da_sequencia | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P024 | Rio dos Cedros | 2011-03-11 | — | 7,27 m | maximo_da_sequencia | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P025 | Rio dos Cedros | 2011-08-30 | — | 6,50 m | maximo_da_sequencia | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P026 | Rio dos Cedros | 2011-09-08 | — | 7,73 m | maximo_da_sequencia | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P027 | Rio dos Cedros | 2014-06-08 | — | 8,96 m | maximo_da_sequencia | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P028 | Rio dos Cedros | 2015-10-22 | — | 7,69 m | maximo_da_sequencia | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P029 | Rio dos Cedros | 1992-05-28 | — | 9,25 m | nivel_historico | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P030 | Rio dos Cedros | 2008-11-12 | — | 6,43 m | nivel_historico | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P031 | Rio dos Cedros | 2008-11-22 | — | 7,94 m | nivel_historico | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P032 | Rio dos Cedros | 2011-02-14 | — | 6,18 m | nivel_historico | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P033 | Rio dos Cedros | não resolvida | — | 6,49 m | data_conflitante | [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf) |
| P034 | Itajaí | 2011-09-10 | — | sem valor exato | pico_sem_valor_exato | [folha](https://www1.folha.uol.com.br/fsp/poder/po1109201116.htm) |
| P035 | Itajaí | 2023-11-18 | — | 2,50 m | leitura_nao_pico | [diarinho](https://diarinho.net/materia/648703/Pico-da-mare-as-18h-pode-provocar-mais-inundacoes-em-Itajai-) |
| P036 | Itajaí | 2023-11-18 | — | 3,45 m | leitura_nao_pico | [diarinho](https://diarinho.net/materia/648703/Pico-da-mare-as-18h-pode-provocar-mais-inundacoes-em-Itajai-) |
| P037 | Ascurra | 2026-09-01 | 06:00 | 10,13 m | leitura_nao_pico | [ascurra](https://ndmais.com.br/tempo/rio-avanca-ultrapassa-10-metros-bloqueia-rua-em-ascurra/) |
| P038 | Apiúna | 2022-05-04 | 18:00–22:00 | 6,50 (unidade ausente) | leitura_nao_pico | [apiuna](https://www.apiuna.sc.gov.br/noticia-733008/) |

## Limitações e divergências

- **Trombudo Central — 2023-11-17:** 8,71 m: Prefeitura informa 17h; boletim DCSC informa 18h. Mesmo valor, horários divergentes; não criar dois eventos. [trom](https://www.trombudocentral.sc.gov.br/trombudo-central-registra-a-maior-enchente-da-sua-historia/) [nov23](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_011_2023.pdf) [ndtrom](https://ndmais.com.br/tempo/atingiu-metade-da-cidade-diz-prefeita-de-trombudo-central-sobre-maior-enchente-da-historia/)
- **Taió — 2023-10:** Boletim DCSC: 12,39 m em 09/10 às 13h. Documento fornecido menciona 12,40 m. Não arredondar nem substituir silenciosamente. [out23](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_010_2023.pdf)
- **Taió — 2023-11:** Boletim permite datar 10,37 m em 17/11 às 21h na rede DCSC; equivalência à régua do registro mensal existente ainda precisa ser demonstrada. [nov23](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_011_2023.pdf)
- **Timbó — 2011:** 9,86 m na fala da Defesa Civil de 2023 versus 10,01 m no jornal de 2011, que previa revisão. Réguas/datum não conciliados. [timbo](https://timbonet.com.br/noticia/sessao-ordinaria-ocorre-com-participacao-em-tribuna-da-defesa-civil-municipal-e-rede-feminina) [jmv](https://jornaldomediovale.com.br/geral/cheia_de_2011_foi_a_maior_de_todas_no_rio_benedito-112538/)
- **Rio dos Cedros — 2020/2021:** 6,49 m com três datas internas incompatíveis; manter data e pico_m nulos. [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf)
- **Rio dos Cedros — 2014-06:** Tabela registra 08/06; sequência do anexo cruza meia-noite. Horário e dia do máximo de 8,96 m precisam de conciliação. [cedros](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf)

## Itajaí: o que a evidência permite dizer

Em 10/09/2011, o Itajaí-Açu teria atingido um máximo superior a três metros acima do normal. A reportagem não fornece o valor exato, o zero ou a régua. O JSON guarda apenas o limite inferior, mantendo pico_m nulo. [Folha](https://www1.folha.uol.com.br/fsp/poder/po1109201116.htm)

Em 18/11/2023, foram publicados 2,50 m no Itajaí-Açu e 3,45 m no Itajaí-Mirim durante a evolução da cheia. O texto ainda previa efeito da maré às 18h; esses números não certificam máximos finais. [Diarinho](https://diarinho.net/materia/648703/Pico-da-mare-as-18h-pode-provocar-mais-inundacoes-em-Itajai-)

Foram consultados também o histórico da Defesa Civil e pesquisados os textos do relatório JICA e da dissertação UDESC abaixo. Nenhum máximo local por régua foi localizado nesses materiais nesta consulta. Isso não demonstra que a série não exista. Para fechar a lacuna, é necessária a série ou boletim do evento por estação, com zero de referência e identificação histórica das réguas.

## Observações de cada registro

- **P001** — Régua: não identificada. Máximo declarado da rede DCSC; localização e zero da régua não identificados na tabela.
- **P002** — Régua: não identificada. Máximo declarado da rede DCSC; localização e zero da régua não identificados na tabela.
- **P003** — Régua: não identificada. Máximo declarado da rede DCSC; localização e zero da régua não identificados na tabela.
- **P004** — Régua: não identificada. Máximo declarado da rede DCSC; localização e zero da régua não identificados na tabela.
- **P005** — Régua: não identificada. Máximo declarado da rede DCSC; localização e zero da régua não identificados na tabela.
- **P006** — Régua: não identificada. Máximo declarado da rede DCSC; localização e zero da régua não identificados na tabela.
- **P007** — Régua: não identificada. Máximo declarado da rede DCSC; localização e zero da régua não identificados na tabela.
- **P008** — Régua: não identificada. Máximo declarado da rede DCSC; localização e zero da régua não identificados na tabela.
- **P009** — Régua: não identificada. Máximo declarado da rede DCSC no boletim de maio; evento adicional ao recorte histórico inicial.
- **P010** — Régua: não identificada. Máximo declarado da rede DCSC no boletim de maio; evento adicional ao recorte histórico inicial.
- **P011** — Régua: não identificada. Máximo declarado da rede DCSC no boletim de maio; evento adicional ao recorte histórico inicial.
- **P012** — Régua: não identificada. Máximo declarado da rede DCSC no boletim de maio; evento adicional ao recorte histórico inicial.
- **P013** — Régua: não identificada. Notícia descreve novos picos na madrugada; régua ausente.
- **P014** — Régua: não identificada. Horário aproximado; notícia emprega explicitamente pico.
- **P015** — Régua: não identificada. Recorde histórico anterior; sem dia, mês ou régua.
- **P016** — Régua: Fundos da rua Equador. Série da régua nomeada; não comparar diretamente com série municipal sem verificar o datum.
- **P017** — Régua: não identificada. Valor informado pelo coordenador da Defesa Civil; divergente de 10,01 m publicado em 2011. Data mantida com precisão anual.
- **P018** — Régua: não identificada. Pico explicitamente informado; sem dia, mês ou régua.
- **P019** — Régua: Fundos da rua Equador (contexto da comparação). Notícia de 13/09/2011 diz que a medição seria revisada. Não substituir 9,86 m.
- **P020** — Régua: não identificada. Pico no centro, abaixo do limiar de transbordamento de 3,20 m citado na reportagem. Ponto exato não nomeado.
- **P021** — Régua: não identificada. Tabela histórica p. 9 e sequência no anexo a partir da p. 40. Máximo explícito no texto.
- **P022** — Régua: não identificada. Tabela histórica p. 9 e sequência no anexo a partir da p. 41. Máximo observado na sequência com posterior queda; não pressupõe série contínua completa.
- **P023** — Régua: não identificada. Tabela histórica p. 9 e sequência no anexo a partir da p. 42. Máximo observado na sequência com posterior queda; não pressupõe série contínua completa.
- **P024** — Régua: não identificada. Tabela histórica p. 9 e sequência no anexo a partir da p. 43. Máximo observado na sequência com posterior queda; não pressupõe série contínua completa.
- **P025** — Régua: não identificada. Tabela histórica p. 9 e sequência no anexo a partir da p. 44. Máximo observado na sequência com posterior queda; não pressupõe série contínua completa.
- **P026** — Régua: não identificada. Tabela histórica p. 9 e sequência no anexo a partir da p. 45. Máximo observado na sequência com posterior queda; não pressupõe série contínua completa.
- **P027** — Régua: não identificada. Tabela histórica p. 9 e sequência no anexo a partir da p. 49. Máximo observado na sequência com posterior queda; não pressupõe série contínua completa. Data de 08/06 preservada da tabela; sequência cruza meia-noite e requer conferir o dia do ápice.
- **P028** — Régua: não identificada. Tabela histórica p. 9 e sequência no anexo a partir da p. 51. Máximo observado na sequência com posterior queda; não pressupõe série contínua completa.
- **P029** — Régua: não identificada. Tabela de enchentes p. 9. Pico não explicitado no trecho; conservar como candidato.
- **P030** — Régua: não identificada. Tabela de enchentes p. 9. Pico não explicitado no trecho; conservar como candidato.
- **P031** — Régua: não identificada. Tabela de enchentes p. 9. Pico não explicitado no trecho; conservar como candidato.
- **P032** — Régua: não identificada. Tabela de enchentes p. 9. Pico não explicitado no trecho; conservar como candidato.
- **P033** — Régua: não identificada. Tabela p. 9: 20/01/2020. Cabeçalho p. 52: 20/01/2021. Linhas: 21/01/2021. Data não resolvida.
- **P034** — Régua: não identificada. Pico descrito como mais de três metros acima do normal; limite >3 m, sem valor exato nem régua. Data derivada de ontem na edição de 11/09/2011.
- **P035** — Régua: não identificada. Leitura em notícia durante evento em curso; previsão de maré às 18h. Não é máximo final.
- **P036** — Régua: não identificada. Leitura em notícia durante evento em curso; previsão de maré às 18h. Não é máximo final.
- **P037** — Régua: Ponte do Beber. Horário aproximado; leituras posteriores menores, mas reportagem não certifica pico final do evento.
- **P038** — Régua: não identificada. Maior número da série publicada; unidade e régua ausentes. Não converter automaticamente em pico_m.

## Fontes consultadas

- **out23:** [Boletim Hidrometeorológico 010/2023, p. 17; publicado em 09/11/2023](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_010_2023.pdf)
- **nov23:** [Boletim Hidrometeorológico 011/2023, p. 18; publicado em 06/12/2023](https://www.aguas.sc.gov.br/jsmallfib_top/DRHI/cadastro_de_usuarios_de_recursos_hidricos/Abastecimento%20Urbano/Boletim_Hidrometeorologico_011_2023.pdf)
- **mai24:** [Boletim Hidrometeorológico, edição 62, p. 16; publicado em 07/06/2024](https://www.aguas.sc.gov.br/jsmallfib_top/Diretoria%20de%20Recursos%20Hidricos/Relatorios/Boletim_Hidrometeorologico_62.pdf)
- **cedros:** [PLANCON Rio dos Cedros, versão 1.07, p. 9 e anexos p. 40–52](https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf)
- **nd26:** [ND Mais, Avenida é interditada após rio atingir 5,1 metros…, 01/09/2026](https://ndmais.com.br/tempo/avenida-e-interditada-apos-rio-atingir-51-metros-acima-do-nivel-e-sair-da-calha-em-cidade-de-sc/)
- **trom:** [Prefeitura de Trombudo Central, maior enchente da história, 27/11/2023](https://www.trombudocentral.sc.gov.br/trombudo-central-registra-a-maior-enchente-da-sua-historia/)
- **ndtrom:** [ND Mais, Atingiu metade da cidade, 21/11/2023](https://ndmais.com.br/tempo/atingiu-metade-da-cidade-diz-prefeita-de-trombudo-central-sobre-maior-enchente-da-historia/)
- **timbo:** [Comunicação da Câmara de Timbó, republicada pelo Timbó Net em 01/11/2023](https://timbonet.com.br/noticia/sessao-ordinaria-ocorre-com-participacao-em-tribuna-da-defesa-civil-municipal-e-rede-feminina)
- **jmv:** [Jornal do Médio Vale, Cheia de 2011 foi a maior de todas no Rio Benedito, 13/09/2011](https://jornaldomediovale.com.br/geral/cheia_de_2011_foi_a_maior_de_todas_no_rio_benedito-112538/)
- **itup17:** [Jornal de Pomerode, Diversas regiões de SC já sofrem com as consequências da chuva, 05/06/2017](https://www.jornaldepomerode.com.br/diversas-regioes-de-sc-ja-sofrem-com-as-consequencias-da-chuva/)
- **folha:** [Folha de S.Paulo, Moradores de Itajaí temem onda de saques, 11/09/2011](https://www1.folha.uol.com.br/fsp/poder/po1109201116.htm)
- **diarinho:** [Diarinho, Pico da maré às 18h pode provocar mais inundações em Itajaí, 18/11/2023](https://diarinho.net/materia/648703/Pico-da-mare-as-18h-pode-provocar-mais-inundacoes-em-Itajai-)
- **ascurra:** [ND Mais, Rio avança, ultrapassa 10 metros…, 01/09/2026](https://ndmais.com.br/tempo/rio-avanca-ultrapassa-10-metros-bloqueia-rua-em-ascurra/)
- **apiuna:** [Prefeitura de Apiúna, Atualizações do nível do Rio Itajaí-Açu, 04/05/2022](https://www.apiuna.sc.gov.br/noticia-733008/)
- **ilhota:** [Prefeitura de Ilhota, Notícias do Último Segundo](https://ilhota.sc.gov.br/noticia-100533/)
- **itajai:** [Defesa Civil de Itajaí, Histórico institucional](https://defesacivil.itajai.sc.gov.br/historico/)
- **jica:** [JICA, Relatório principal, parte 1, novembro de 2011](https://openjicareport.jica.go.jp/pdf/12043683_02.pdf)
- **udesc:** [UDESC, A enchente em Itajaí: relatos, percepções e memórias, 2010](https://www.faed.udesc.br/arquivos/id_submenu/866/caio_floriano_dos_santos.pdf)
