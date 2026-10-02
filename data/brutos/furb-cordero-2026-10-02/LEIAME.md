# Planilha de picos de Blumenau do Prof. Ademar Cordero (FURB), 02/10/2026

**Origem:** anexo do e-mail de Ademar Cordero (cordero@furb.br) a Jefferson, 02/10/2026 18:10 (hora de
Brasília), na conversa do ofício C25 ("Referência (régua ANA ou zero IBGE) da série histórica de enchentes
de Blumenau"). Arquivo salvo como veio, sem edição.

| Arquivo | sha256 | Observação |
|---|---|---|
| `Picos-Blumenau-1888-2024-IBGE-GPS.xls` | `15e81f37d2df828ddde5485b70dbe1ff66a23309cd01e780ec628e653c502752` | Excel 97–2003. Metadados: autor "FURB", criado em 20/10/1997, impresso em 13/02/2012, salvo em 02/10/2026 21:00. Só a `Plan1` tem dados; `Plan2`–`Plan16` estão vazias. |
| `transcricao.tsv` | `07b978f1baadb931dabe39f2dd898641476a853995aa27dbb818f274e49272d0` | 83 linhas lidas com `xlrd`, sem correção. |

## Texto do e-mail (literal)

> Olá! Encaminho os picos com as enchentes com as duas referências (Régua antiga +0,2 = IBGE) a outra
> (IBGE+0,2=GPS)
> Após enchente de 2011 foi instalada nova régua (em relação a régua antiga tem 40 cm). A partir desta data
> não precisa somar nem o 20 cm nem o 40 cm.

## Como ler a planilha

* Título: "Picos de Enchentes Registrados na Bacia do Rio Itajaí (em metros)". Colunas: número, ano, data,
  **"(IBGE) Blumenau"** e **"(IBGE-GPS) (Regua Nova)"**. Na linha de 2013 a coluna F diz
  **"Mudança da regua nova"**.
* Até 2011 a coluna GPS é sempre IBGE + 0,20 m. **De 2013 em diante as duas colunas são iguais**: é o que o
  e-mail diz ("não precisa somar").
* **A célula de data guarda só dia e mês.** O ano gravado dentro dela é o do dia em que a célula foi digitada
  (1997, 2004, 2011, 2017, 2023…), não o da cheia. A transcrição usa o **ano da coluna B** e o dia/mês da
  célula; a célula bruta vai na última coluna para conferência.

## O que a planilha NÃO autoriza sozinha

Ela diverge da Tabela 4 publicada (Cordero & Medeiros, XV SBRH) e da lista "Enchentes Registradas" da
Defesa Civil de Blumenau entre 1911 e 1983. A análise, linha a linha, está em
`docs/fontes-academicas.md`, seção "A planilha do Prof. Cordero". **Nada foi gravado em `enchentes.json`.**
