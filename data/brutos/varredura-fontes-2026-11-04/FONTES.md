# Brutos da varredura de fontes de 04/11/2026

Regra da pasta: todo arquivo entra com sha256 (`SHA256SUMS`) e data de acesso. Nada daqui entra em
`enchentes.json` ou `estacoes.json` sem decisão do Jefferson, com a fonte aberta de novo.

## `Tabela de enchentes.xlsx` — "Histórico de enchentes em Blumenau" (Mendeley Data)

| campo | valor |
|---|---|
| Título | Histórico de enchentes em Blumenau |
| Repositório | Mendeley Data, DOI 10.17632/cj64gycsw8.2 — versão 2, de 23/09/2025 (v1 de 18/09/2025) |
| Autores | Albio Fabian Melchioretto, Bruno Cristiano Loos e Silva, Abel Braga Warwar da Fonseca (Senac Santa Catarina) |
| Licença | CC BY 4.0 |
| Origem declarada | Defesa Civil de Blumenau, com a classificação de Ribeiro (2023), *Revista de Tecnologia & Gestão Sustentável*, v. 2, n. 6, e cruzamento bibliográfico |
| Acesso | 04/11/2026, pelo navegador do Jefferson (download para Downloads; o arquivo chegou a este repositório por upload em 04/11/2026) |
| Tamanho | 21.354 bytes (o site diz 20,9 KB) |
| sha256 | `56fdbe6baa58fbc14a78552b66aefe92f8ad223fd39de6ec28c6d0ec75aa30c6` — **conferido** contra o handoff |
| Conteúdo | planilha única (`Sheet1`), 102 linhas de 1852 a 19/05/2024: Ano, Mês, Dia, COMPLETA, Cota, Categoria; ao lado, tabelas auxiliares (classificação "maior que 12" = Típica e "maior que 16" = Atípica; totais por século, por mês e enchentes por ano) |
| **Régua / referência altimétrica** | **não informada** pela tabela. O cruzamento (`docs/VARREDURA-FONTES-2026-11-04-CRUZAMENTO-BLUMENAU.md`) mostra que ela mistura as três referências de Blumenau: valores iguais aos de Cordero & Medeiros (IBGE) até 2001, régua antiga em 2008–2011 e régua de hoje de 2013 em diante |
| Confiança, se algum número entrar | `media` (compilação); uso: **só cruzamento** — desde 04/11/2026 (decisão do Jefferson) os 101 registros de Blumenau que a tabela também tem trazem o número dela em `cruzamentos`, sem mudar `pico_m` nem `referencia` (`scripts/cruzar_mendeley_blumenau.py --anotar`) |

Problemas conhecidos (do handoff e confirmados na transcrição):

- a coluna COMPLETA mistura texto `d/m/aaaa` (11 linhas, de 1852 a 1898) e data do Excel (91 linhas);
- linha 3: Ano/Mês/Dia dizem 20/11/1855, mas COMPLETA diz 21/11/1855;
- linha 6: COMPLETA de 1868 está gravada como ano 2868 (data do Excel fora do intervalo);
- a cota mínima é 8,06 m: não é a lista de todas as cheias, só das acima de ~8 m;
- a tabela não está em ordem cronológica dentro do ano (vai do mês maior para o menor);
- termina em 19/05/2024.

## `mendeley-blumenau-enchentes.csv`

Transcrição **gerada a partir do xlsx** por `python3 scripts/cruzar_mendeley_blumenau.py --transcrever` (colunas
`ano, mes, dia, cota_m, categoria`; `ano/mes/dia` como estão nas três primeiras colunas da planilha, não na
COMPLETA). 102 linhas. O teste `scripts/teste_cruzar_mendeley_blumenau.py` confere que o CSV commitado é o que o
xlsx dá. O CSV de 102 linhas citado no handoff ("CSV anexo") **não chegou** a este ambiente: a comparação pedida
entre os dois não pôde ser feita; o que está aqui é só a transcrição reproduzível.
