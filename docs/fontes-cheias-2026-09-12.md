# Conferência das fontes enviadas em 12/09/2026

## Blumenau

Fonte: https://defesacivil.blumenau.sc.gov.br/m/inundacao e seu `static/mapas/inundacao/camadas_get_nivel.js`.

Extraídas 16 cartas FURB 2025, cotas 8, 8,5, 9, 9,5, 10, 10,5, 11, 11,5, 12, 12,5, 13, 14, 15, 16, 17 e 18 m. GeoJSON CRS84 preservado, incluindo propriedades e coordenadas. O índice guarda origem e SHA-256. O importador lê somente o objeto JSON; não executa scripts baixados.

No Monitor, a escolha manual mostra qualquer carta. A automática usa a maior cota disponível que não supera a leitura recente de Blumenau/AlertaBlu, sem interpolar. Abaixo de 8 m, sem leitura compatível ou durante reprodução, não desenha automaticamente. As cartas são simulações por cota, não eventos históricos: não recebem ano de cheia, pico histórico nem chuva semanal inventados.

As faixas 3/4/6/8 m já estavam no cadastro e foram reconfirmadas no JSON oficial `static/data/nivel_oficial.json`. Não mudam por causa das manchas. O carimbo UTC continua convertido para Brasília pelo coletor. Para a cor e seleção automática, Blumenau passa a recusar leitura com idade superior a 120 minutos, na resolução em minutos do projeto. Demais cidades mantêm a regra existente.

## Itajaí / SIE

As dez camadas históricas do SIE já estavam em `data/manchas/itajai` e no monitor. Não foram duplicadas nem vinculadas a um pico de régua não documentado. A fonte `https://geoitajai.github.io/sie/data/viewviasdecretorecuos.geojson` retornou 1.863 vias e foi baixada para os artefatos de consulta. Recuo viário é informação urbanística: valor nulo não foi transformado em dois metros nem usado como altura de inundação.

## Ilhota

PLANCON 2025/2028, pp. 15–19: https://ilhota.sc.gov.br/wp-content/uploads/2025/08/Plano_de_Contingencia_Defesa_Civil_Ilhota.pdf

O plano confirma leitura junto à ponte e patamares de 9,20/10/10,50 m. A seção de ruas declara alturas relativas ao mar. Isso não fornece conversão para a DCSC-00030, cuja leitura estadual já é coletada separadamente. Gaspar não substitui essa estação.

A tabela histórica das pp. 18–19 contém valores iguais aos de Blumenau, como 15,34 m em 1983, 15,46 m em 1984 e 10,76 m em outubro/2023. Não demonstra identidade com a régua da Cadorin. Por isso não foram importados como picos de Ilhota. A coincidência é um indício de reprodução de outra série, não prova de equivalência entre zeros.

## Histórico e limites

O resumo recebido mistura referências e datas divergentes; não foi importado em bloco. Critério de inclusão de uma cheia em uma tabela, limite de aviso e datum são conceitos diferentes. O corte de 8 m não prova outro zero. Não se somam alturas de cidades, não se calcula offset de medições em horários diferentes e não se converte cota de lâmina em nível de régua.

Verificação: testes do importador; testes de limites e identidade da fonte; auditoria em navegador carregando as 16 cartas e recusando seleção automática a 6,10 m; build e validador de dados. Mudança de frontend e arquivos estáticos, sem alteração de serviço da VPS.
