# Dados de cheias — pesquisa e downloads

Levantamento em 24/09/2026, orientado pelas 14 cidades do anexo PICOS-FALTANTES.md. **Resultado parcial quanto aos picos municipais:** 5 picos publicados com data completa, 2 registros com data incompleta, 25 leituras auxiliares e uma tabela oficial com 10 linhas históricas de Taió. Esses conjuntos têm sobreposições e não devem ser somados como eventos únicos. As réguas dos picos publicados ainda precisam de confirmação.

Foram baixados **20 pacotes ANA: 17 com conteúdo e 3 vazios**, contendo 61 arquivos de dados, além de **5 PDFs integrais** e páginas de referência. Todos os arquivos de dados ANA têm versões integrais em Markdown. ZIP vazio é registrado como ausência de conteúdo, não como série obtida.

## Arquivos para consulta

- [Inventário ANA e links para todos os dados em Markdown](ANA-inventario.md).
- [Máximas mensais nos anos-alvo, sem equiparação a picos municipais](ANA-maximas-mensais-anos-alvo.md).
- [Dados estruturados e fontes em JSON](dados-cheias-pesquisados.json).
- [Fontes e registro de acesso](FONTES.md).
- `fontes/`: PDFs e HTML originais; `ana/`: ZIPs, TXT originais e Markdown.

## Picos publicados com data completa

Nenhuma das fontes abaixo identifica explicitamente a régua necessária para associação automática à base municipal. Confiança do vínculo: baixa, mesmo quando a publicação é oficial.

| Cidade / rio | Data | Hora | Pico (m) | Fonte |
|---|---|---|---:|---|
| Trombudo Central / Rio Trombudo | 2023-11-17 | 17:00 | 8.71 | [Prefeitura de Trombudo Central](https://www.trombudocentral.sc.gov.br/trombudo-central-registra-a-maior-enchente-da-sua-historia/) |
| Timbó / Rio Benedito | 2023-10-12 | 21:00 | 7.46 | [O Auditório](https://oauditorio.com/noticias/geral-noticias/10/2023/rio-benedito-comeca-a-baixar-na-regiao-de-timbo/) |
| Rio dos Cedros / Rio dos Cedros | 2023-10-12 | 15:00 | 5.77 | [O Auditório](https://oauditorio.com/noticias/geral-noticias/10/2023/rio-benedito-comeca-a-baixar-na-regiao-de-timbo/) |
| Taió / Rio Itajaí do Oeste | 2023-11-04 | não informada | 10.36 | [Misturebas News](https://misturebas.com.br/2023/11/06/taio-equarta-enchente-em-um-mes/) |
| Botuverá / Rio Itajaí-Mirim | 2023-11-17 | não informada | 8.61 | [O Município](https://omunicipio.com.br/clima/a-agua-baixou-e-os-problemas-dobraram-prefeito-de-botuvera-comenta-situacao-apos-enchente/) |

Botuverá: horário descrito como tarde. Timbó não foi associado automaticamente à Rua Equador; Rio dos Cedros não foi associado à Praça Matriz.

## Registros com data incompleta

- Timbó, 2014: **9.58 m**. Régua/estação não declarada pela fonte. Dia e mês ausentes. Rio Benedito é hipótese a confirmar; não preencher data artificialmente. [Fonte](https://timbonet.com.br/noticia/sessao-ordinaria-ocorre-com-participacao-em-tribuna-da-defesa-civil-municipal-e-rede-feminina).
- Taió, 1983: **11.85 m**. Régua/estação não declarada pela fonte. Relato retrospectivo baseado em medições de Aldo Bogo; fonte não fornece dia, mês ou referência da régua. Valor de cheia histórica, sem série para reconstituir máximo. [Fonte](https://misturebas.com.br/2023/10/13/maior-enchente-de-taio/).

## Taió — tabela oficial histórica

Fonte: [Estudo Socioambiental de Taió](https://www.taio.sc.gov.br/uploads/sites/346/2024/07/Estudo-Socioambiental-do-Municipio-de-Taio.pdf), página 343 do PDF, tabela conferida visualmente. Não fornece dia, hora ou identificação da régua. Mantida a ordem do original.

| Ano | Mês publicado | Nível (m) |
|---|---|---:|
| 1983 | Setembro | 11.85 |
| 2011 | Setembro | 11.65 |
| 2013 | Junho | 9.38 |
| 2014 | Junho | 8.91 |
| 2015 | Outubro | 10.75 |
| 2017 | Junho | 8.18 |
| 2022 | Maio | 9.70 |
| 2023 | Outubro | 12.40 |
| 2023 | Novembro | 10.36 |
| 2023 | Novembro | 10.37 |

A tabela escreve **Setembro para 1983**; essa informação foi preservada, embora não coincida com o mês do evento indicado no anexo. As duas linhas de novembro/2023 não trazem dias: não foram mescladas nem tratadas como uma divergência comprovada do mesmo evento. A p. 304 informa **12,40 m às 13h de 09/10/2023**, complementando o registro já existente. O dado de 10,36 m em 04/11/2023 da imprensa é compatível numericamente com uma linha da tabela, mas a correspondência de régua e data não foi demonstrada.

## Todas as leituras auxiliares

São leituras publicadas, não picos confirmados. O boletim de Itajaí prevê agravamento na maré seguinte. A unidade de Canhanduba foi inferida do contexto; o texto não a repete nessa linha. Apiúna não explicita unidade no corpo do boletim; não houve conversão para metros.

| Cidade | Data | Hora | Rio / régua | Valor publicado | Unidade | Fonte |
|---|---|---|---|---:|---|---|
| Itajaí | 2011-09-09 | 17:30 | Itajaí-Açu / Telemetria CEPSUL | 0.93 | m | [Fonte](https://alcateiagemat.blogspot.com/2011/09/nivel-dos-rios-em-itajai.html) |
| Itajaí | 2011-09-09 | 17:30 | Itajaí-Açu / Telemetria Teporti | 3.03 | m | [Fonte](https://alcateiagemat.blogspot.com/2011/09/nivel-dos-rios-em-itajai.html) |
| Itajaí | 2011-09-09 | 17:30 | Itajaí-Mirim — canal retificado / Telemetria SEMASA São Roque | 3.65 | m | [Fonte](https://alcateiagemat.blogspot.com/2011/09/nivel-dos-rios-em-itajai.html) |
| Itajaí | 2011-09-09 | 17:30 | Itajaí-Mirim — canal retificado / Telemetria VITALMAR | 2.68 | m | [Fonte](https://alcateiagemat.blogspot.com/2011/09/nivel-dos-rios-em-itajai.html) |
| Itajaí | 2011-09-09 | 17:30 | Itajaí-Mirim — curso antigo / Telemetria Início Rio | 2.62 | m | [Fonte](https://alcateiagemat.blogspot.com/2011/09/nivel-dos-rios-em-itajai.html) |
| Itajaí | 2011-09-09 | 17:30 | Itajaí-Mirim — curso antigo / Telemetria Itamirim | 3.21 | m | [Fonte](https://alcateiagemat.blogspot.com/2011/09/nivel-dos-rios-em-itajai.html) |
| Itajaí | 2011-09-09 | 17:30 | Ribeirão da Murta / Telemetria TEPORTI | 2.16 | m | [Fonte](https://alcateiagemat.blogspot.com/2011/09/nivel-dos-rios-em-itajai.html) |
| Itajaí | 2011-09-09 | 17:30 | Ribeirão Canhanduba / Telemetria AMP Logística | 2.78 | m (inferido) | [Fonte](https://alcateiagemat.blogspot.com/2011/09/nivel-dos-rios-em-itajai.html) |
| Apiúna | 2022-05-04 | 06:00 | Itajaí-Açu / não declarada | 5.23 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 08:00 | Itajaí-Açu / não declarada | 5.33 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 09:00 | Itajaí-Açu / não declarada | 5.38 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 10:00 | Itajaí-Açu / não declarada | 5.44 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 11:00 | Itajaí-Açu / não declarada | 5.50 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 13:00 | Itajaí-Açu / não declarada | 5.85 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 14:00 | Itajaí-Açu / não declarada | 6.03 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 15:00 | Itajaí-Açu / não declarada | 6.16 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 16:00 | Itajaí-Açu / não declarada | 6.36 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 17:00 | Itajaí-Açu / não declarada | 6.43 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 18:00 | Itajaí-Açu / não declarada | 6.50 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 19:00 | Itajaí-Açu / não declarada | 6.50 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 20:00 | Itajaí-Açu / não declarada | 6.50 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 21:00 | Itajaí-Açu / não declarada | 6.50 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 22:00 | Itajaí-Açu / não declarada | 6.50 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-04 | 23:00 | Itajaí-Açu / não declarada | 6.45 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |
| Apiúna | 2022-05-05 | 06:00 | Itajaí-Açu / não declarada | 6.10 | não declarada | [Fonte](https://apiuna.sc.gov.br/noticia-733008/) |

## Divergências e cuidados de interpretação

- Taió em 09/10/2023: estudo municipal e anexo trazem 12,40 m; [artigo ABRHidro](https://files.abrhidro.org.br/Eventos/Trabalhos/241/IV-END0065-1-0-20240819-122719.pdf) traz 12,39 m e identifica ANA 83050000 (pp. 2–3). Não foi demonstrada equivalência entre referências. Não gerar duplicata nem aplicar deslocamento entre réguas.
- A figura acadêmica também rotula 10,36 e 10,35; a tabela municipal apresenta 10,36 e 10,37 em novembro. Datas exatas e equivalência não esclarecidas; não presumir que sejam o mesmo máximo.
- [Folha, 11/09/2011](https://www1.folha.uol.com.br/fsp/poder/po1109201116.htm) situa o máximo do Açu no dia anterior, mas fornece apenas elevação aproximada sobre o normal. Não é cota exata de régua. As leituras de 09/09 não comprovam o pico.
- Ilhota: tabela da p. 18 do PLANCON contém valores coincidentes com Blumenau, sem identificar a régua. A associação a Blumenau é inferência pela coincidência, não identificação explícita da tabela. Limiares operacionais não são picos.
- Máximas mensais ANA, médias diárias, cotas instantâneas, vazões, perfis e níveis de barragem permanecem separados. Ausência de dado não significa nível zero.

## Cobertura das 14 cidades

| Cidade | Situação | Evidência / limitação |
|---|---|---|
| Itajaí | Sem pico numérico admissível por régua | 8 leituras recuperadas em 09/09/2011. Folha de 11/09/2011 situa máximo no dia anterior, mas apenas descreve elevação superior a três metros sobre o normal. Não é cota exata de uma régua. Contradiz tratar 09/09 às 17h30 como pico confirmado. Consulte ANA-inventario.md para os arquivos adicionais por estação; vínculo com régua municipal não presumido. |
| Ilhota | Sem pico local confirmado | PLANCON baixado. Cotas 9,20/10,00/10,50 são limiares, não picos. Tabela da página 18 tem valores coincidentes com o histórico de Blumenau (1983:15,34;1984:15,46;2011:12,60), sem explicitar régua na própria tabela. Não atribuída a Ilhota. Consulte ANA-inventario.md para os arquivos adicionais por estação; vínculo com régua municipal não presumido. |
| Ascurra | Pista de outro curso de água, acesso direto falhou | Busca indexada informa pico de 6,65 m às 01h de 09/10/2023 no Ribeirão Braço São Paulo. Não é a régua do Açu na Ponte do Beber. Página falhou por timeout no Chrome e na abertura web; não incluído nos resultados conferidos. |
| Apiúna | Sem pico confirmado nas datas-alvo | Boletim municipal de maio/2022 recuperado como leituras auxiliares. JICA apresenta vazões e curvas; não convertidas para metros. Vínculo da régua municipal com ANA 83500000 não confirmado. Série convencional ANA 83500000 APIÚNA - RÉGUA NOVA baixada integralmente. |
| Lontras | Sem pico local confirmado | PMSB recuperado pelo Chrome após falha HTTP direta; sem pico local identificado. ANA 83301000 retornou ZIP vazio e 83302000 apenas perfil transversal, sem série de cotas. |
| Ibirama | Sem pico em metros confirmado | Relatos históricos e JICA localizados; simulações de rompimento e vazões em m³/s não são cotas históricas do Hercílio. Consulte ANA-inventario.md para os arquivos adicionais por estação; vínculo com régua municipal não presumido. |
| Ituporanga | Identidade do código do anexo corrigida; séries alternativas baixadas | HidroWeb identifica 83145140 como DCSC BARRAGEMSUL ITUPORANGA JUSANTE; ZIP convencional vazio. Séries 83250000 e 83250001 baixadas. Equivalência com régua do centro não confirmada. |
| Trombudo Central | Data e altura histórica confirmadas; régua pendente | 8,71 m em 17/11/2023 às 17h, fonte municipal. Consulte ANA-inventario.md para os arquivos adicionais por estação; vínculo com régua municipal não presumido. |
| Rio dos Cedros | Pico publicado; régua pendente | 5,77 m em 12/10/2023 às 15h. |
| Vidal Ramos | Evento confirmado, sem cota | Reportagem sobre 24/03/2001 aberta e baixada; não informa nível medido em metros. |
| Botuverá | Pico publicado; régua pendente | 8,61 m em 17/11/2023, à tarde. |
| Guabiruba | Sem pico local confirmado | Buscas por histórico, 2008/2011 e nível do rio não retornaram cota verificável local. Valores de Brusque e Blumenau descartados. |
| Taió | Tabela histórica oficial e série ANA baixadas; referências de régua pendentes | Estudo municipal: dez linhas históricas na p. 343 e 12,40 m às 13h de 09/10/2023 na p. 304. ANA 83050000 preservada separadamente. |
| Timbó | Pico de 12/10/2023 e pico de 2014 publicados; régua pendente | 7,46 m; 9,58 m sem dia/mês. Tabela histórica do projeto da ponte aparece no índice, mas as duas URLs municipais retornam 404. Nenhum número dessa tabela foi promovido a dado conferido. Consulte ANA-inventario.md para os arquivos adicionais por estação; vínculo com régua municipal não presumido. |

## O que permanece faltando

A pesquisa não recuperou todos os picos de todas as cidades e anos. Faltam principalmente a identificação das réguas municipais, boletins finais por estação, documentos AVADAN/FIDE e séries telemétricas completas. O projeto da ponte de Timbó retornou 404 nas duas URLs encontradas. Fontes indisponíveis e resultados somente indexados ficaram como pistas, sem promoção a números verificados.

Foram usados Chrome, busca web, downloads HTTP, extração de PDF e leitura dos arquivos ANA. Os ZIPs convencionais foram baixados pela interface oficial sem recorte temporal e validados como arquivos ZIP. Nenhum contato com terceiros ou alteração da base de produção foi feito.
