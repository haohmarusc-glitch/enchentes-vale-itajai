# Fontes indicadas pela Defesa Civil de Ascurra

Consulta no Chrome em 11/09/2026 à página encaminhada no C18:
https://sites.google.com/view/prefeituramunicipaldeascurra-s/in%C3%ADcio

A página incorpora a estação DCSC-00003 e publica acumulados de 1, 12, 24 e 168 horas. A consulta GraphQL com `data.chuva.acumulado.h168.value` foi aceita pela API em 11/09/2026; para Ascurra retornou 127,83999633789062 mm na conferência. Esse retrato não é embutido como leitura atual no site.

O coletor passa a gravar `chuva_168h_mm`. A tela aceita o campo quando disponível, sem inferir valores de arquivos antigos. Usa o carimbo da estação; não afirma possuir horário independente da chuva. O deploy na VPS foi confirmado pelo usuário em 11/09/2026: atualização até 28eafface, coleta e publicação concluídas, com chuva de 168 horas presente para Ascurra.

## Cartografia

https://sites.google.com/view/prefeituramunicipaldeascurra-s/%C3%A1reas-de-risco

O projeto Google Earth tem acesso de leitura e identifica mapeamento da CPRM/SGB e da COMPDEC. Pastas de limite municipal, eixos, mapeamento CPRM de 2015 e cartografia municipal. Setor examinado: SC_ASCURRA_SR_3_CPRM, bairro Estação/BR-470, data 25/06/2015, tipologia inundação, risco alto, referência ao evento de 2011. Os atributos examinados não fornecem cota operacional na DCSC-00003. Não tratar a área como mancha correspondente a um nível ou como perímetro da cheia de 2011. As elevações inferidas pelo Google Earth não são cotas da régua.

Na primeira integração, o piloto oferecia somente o link oficial. A integração dos quatro setores CPRM está descrita abaixo; recomendações de intervenção, abrigos e instruções de conduta não são importados.

## Outras fontes apontadas

A aba Monitoramento indica os gráficos Cemaden `idpcd=17625` e `idpcd=17626`, radar estadual e Agroconnect/EPAGRI. Esses vínculos são pistas oficiais, ainda sem nova integração de série ou classificação de estação.


## Integração dos setores CPRM de 2015

Fonte direta: https://rigeo.sgb.gov.br/handle/doc/18496
Arquivo vetorial: https://rigeo.sgb.gov.br/bitstreams/507ca798-4c01-4583-ade3-faba0d5d2359/download

O ZIP contém o KMZ `KML/ASCURRA_SC.kmz`. Foram preservadas as coordenadas dos quatro setores com COBRADE_1 = 1.2.1.0.0 (inundação), incluindo anéis internos, sem simplificação ou interpolação. Levantamento em 25/06/2015; publicação em agosto de 2015. O setor cujo identificador original é SC_ASCURRA_SR__CPRM permanece com esse identificador incompleto; não foi inventado um número.

A camada estática aparece no monitor de Ascurra e pode ser ocultada no controle Camadas de cheia. Não participa da escolha automática por nível, não representa a cheia de 2011 nem alagamento atual. Não foram importadas recomendações de intervenção, estimativas de moradores ou setores de deslizamento, corrida de massa e erosão. Os setores adicionais da cartografia municipal do Google Earth continuam pendentes.

SHA-256 do ZIP original: `3f70d1eea2089ae8462c36bae2e1b0747327f04d3df1f4caa6f5e87e4848edb1`. As quatro geometrias passaram pela validação Shapely; nenhum anel foi corrigido ou redesenhado.


## Carta de suscetibilidade SGB, março de 2026

Fonte: https://rigeo.sgb.gov.br/handle/doc/25961
PDF: https://rigeo.sgb.gov.br/bitstreams/4c552f7f-74e4-4bf9-897d-6b18b0c76e86/download

Conferência visual da página única, Quadro-legenda B e Notas 1 e 2. O quadro usa alturas relativas à lâmina de água regular do curso: alta suscetibilidade abaixo de 1,5 m; média entre 1,5 e 3 m; baixa a partir de 3 m. Isso NÃO documenta correspondência com DCSC-00003. Não converter esses valores em níveis da régua, nem tratá-los como cenários operacionais ou picos de cheias históricas.

A Nota 1 exige atenção à escala e a estudos locais detalhados. A carta tem escala apresentada 1:30.000; as notas indicam base generalizada e compatibilidade do zoneamento em 1:50.000. O site oferece a fonte para consulta; não importa os polígonos nesta etapa. A carta de suscetibilidade de 2026 e os setores de risco de 2015 são produtos distintos, não versões intercambiáveis da mesma mancha.
