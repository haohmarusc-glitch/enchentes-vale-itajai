# Maré medida do CIRAM — coleta, publicação e tela (07/10/2026)

**Decisão do Jefferson (07/10/2026):** implementar a coleta agendada, a publicação e a tela da maré medida da
EPAGRI/CIRAM, com quatro condições:

1. antes de ir ao ar, conferir que a fonte publica medições recentes, com horário, estação, unidade e referência
   vertical identificados — a existência do endereço não prova que o marégrafo funciona;
2. a diferença entre maré medida e prevista só aparece quando as duas são compatíveis em local, horário e referência
   vertical, com o nome **"diferença entre nível observado e maré astronômica prevista"**. Ela não se atribui só a
   vento e pressão: pode incluir influência do rio e outros efeitos;
3. com a operação ou a referência incerta, a integração fica pronta e a tela diz **"medição indisponível"** ou
   **"referência pendente"**. Leitura antiga nunca aparece como atual;
4. a previsão astronômica que já existe (tábua da Marinha) continua, e a fonte e o horário da medição aparecem à parte.

## O que a conferência de 07/10/2026 achou

| Item | Situação | Prova |
|---|---|---|
| Medições recentes | **Sim** | Balneário Camboriú (`getDataMare5_2927.php`): última medição 18:30 de 07/10, consultada às 19:09; cadência de 15 min. Florianópolis e Imbituba, idem. |
| Estação | **Identificada** | O endpoint é da lista da página dos marégrafos. Itajaí (`12/2921`) responde, mas sem nenhuma maré observada. |
| Horário | **Identificado por conferência** (a fonte não declara) | As preamares astronômicas do CIRAM para Itajaí caem 10 a 25 min antes das da tábua da Marinha em 06–09/10, nos quatro dias. Em UTC, a diferença seria de 3 h. Conclusão: horário de Brasília. |
| Unidade | **Identificada por conferência** (a fonte não declara) | A preamar astronômica do CIRAM em Itajaí (108 em 07/10 12:15) bate com a tábua da Marinha (1,02 m às 12:34): centímetros. |
| Referência vertical | **Não identificada** | Nem o JSON nem a página dizem a que zero a maré observada se refere. O "NMM" de cada estação é outro número (66,4 em Balneário Camboriú, 55,2 em Florianópolis, 47,4 em Imbituba). |

Resultado: a integração vai ao ar **pronta**, e a tela diz **"referência pendente"**, com a hora da última medição
e sem número. Nenhum nível sai no arquivo publicado enquanto a referência não for confirmada.

## Como funciona

- **Coleta agendada:** `publicar_tempo_real.sh` roda `coleta_mare_ciram.py --publicar` a cada publicação (15 min,
  no cron que já existe; não há linha nova no crontab). É **uma** consulta, só à estação principal, com o
  `User-Agent` do projeto. O `robots.txt` do CIRAM só fecha `/wp-admin/`.
- **Arquivo:** `data/tempo-real/ultimo_mare_medida.json` (versão 1), pequeno, publicado no branch `tempo-real` se for
  JSON, da versão 1, com estação e gerado há no máximo 30 min. Falha na coleta apaga o arquivo anterior e nunca
  segura o nível.
  - `ultima_medicao` leva **só a hora** enquanto a referência estiver pendente ou a medição não for recente.
  - Com a referência confirmada e a medição recente, leva `observada_m`, `astronomica_m` e
    `diferenca_observado_astronomica_m`. A diferença é da **mesma linha** da fonte: mesma estação, mesmo horário,
    mesma série. A tábua da Marinha é outro ponto e outro zero e nunca entra nessa conta.
- **Tela:** `/itajai`, no cartão "Por que a maré pesa tanto aqui", painel **"Maré medida perto da foz"**
  (`componentes/PainelMareMedida.tsx`, lógica em `dados/mareMedida.ts`).
  - O site refaz a idade no relógio de agora: medição com mais de 60 min ou do futuro vira "Medição indisponível",
    com a hora dela e "Não é atual".
  - Arquivo de publicação parada (mais de 30 min) ou fora do combinado: "Medição indisponível".
  - Horário sempre em Brasília, escrito na tela.
  - A tábua da Marinha continua sendo a previsão da tela, com a fonte dela à parte.
- **O chat não mudou:** "como está a maré?" responde pela tábua, como antes.

## Para mostrar o número

`REFERENCIA_VERTICAL` em `scripts/coleta_mare_ciram.py` está **vazio**, e há teste que trava isso. Entrada nova
(`{"descricao": …, "fonte": …}`) só com a referência escrita pela EPAGRI/CIRAM ou outra fonte oficial, por decisão
do Jefferson. A resposta da EPAGRI ao C5 não falou dos marégrafos (`docs/RESPOSTA-EPAGRI-C5-2026-09-09.md`).

Perguntas a fazer à EPAGRI/CIRAM (rascunho C33 em `docs/oficios-prontos.md`, não enviado):
1. A que referência vertical (zero) a maré observada de Balneário Camboriú se refere? É a mesma da maré astronômica
   que a página publica para a estação?
2. Em que unidade e em que fuso a série é publicada?
3. A estação de Itajaí (`12/2921`) voltará a publicar maré observada?

## Testes

- `scripts/teste_coleta_mare_ciram.py`, classe `OArquivoQueOSiteLe`: sem referência não sai número; referência sem
  fonte não conta; medição antiga não leva número; a diferença vem da mesma linha; nenhum texto chama a diferença de
  "maré meteorológica"; falha apaga o arquivo anterior.
- `scripts/teste_publicar_tempo_real.py`: o arquivo sobe quando é desta coleta, e o velho, quebrado ou de outra
  versão não sobe nem derruba a publicação.
- `web/src/dados/mareMedida.test.ts`: os quatro estados da tela, o horário em Brasília, a leitura antiga e a do
  futuro, e o arquivo fora do combinado.
