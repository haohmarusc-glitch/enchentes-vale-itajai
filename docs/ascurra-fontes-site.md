# Fontes indicadas pela Defesa Civil de Ascurra

Consulta no Chrome em 11/09/2026 à página encaminhada no C18:
https://sites.google.com/view/prefeituramunicipaldeascurra-s/in%C3%ADcio

A página incorpora a estação DCSC-00003 e publica acumulados de 1, 12, 24 e 168 horas. A consulta GraphQL com `data.chuva.acumulado.h168.value` foi aceita pela API em 11/09/2026; para Ascurra retornou 127,83999633789062 mm na conferência. Esse retrato não é embutido como leitura atual no site.

O coletor passa a gravar `chuva_168h_mm`. A tela aceita o campo quando disponível, sem inferir valores de arquivos antigos. Usa o carimbo da estação; não afirma possuir horário independente da chuva. **O coletor precisa ser atualizado na VPS** para o campo entrar no arquivo publicado. Esta alteração não realiza deploy na VPS.

## Cartografia

https://sites.google.com/view/prefeituramunicipaldeascurra-s/%C3%A1reas-de-risco

O projeto Google Earth tem acesso de leitura e identifica mapeamento da CPRM/SGB e da COMPDEC. Pastas de limite municipal, eixos, mapeamento CPRM de 2015 e cartografia municipal. Setor examinado: SC_ASCURRA_SR_3_CPRM, bairro Estação/BR-470, data 25/06/2015, tipologia inundação, risco alto, referência ao evento de 2011. Os atributos examinados não fornecem cota operacional na DCSC-00003. Não tratar a área como mancha correspondente a um nível ou como perímetro da cheia de 2011. As elevações inferidas pelo Google Earth não são cotas da régua.

O piloto oferece o link oficial para consulta. Não importou geometria, recomendações de intervenção, abrigos ou instruções de conduta.

## Outras fontes apontadas

A aba Monitoramento indica os gráficos Cemaden `idpcd=17625` e `idpcd=17626`, radar estadual e Agroconnect/EPAGRI. Esses vínculos são pistas oficiais, ainda sem nova integração de série ou classificação de estação.
