# Comparação da revisão v3.6 → v3.7

Data da revisão: 2026-10-02.

## Base de comparação

A versão anterior exata do prompt não estava disponível como arquivo. A comparação foi feita entre o arquivo recebido `01-prompt-picos-v3.6.txt` e a última rodada documental descrita na conversa, entregue como `cheias_itajai_fontes_2026-10-01.zip`.

## Correções aplicadas

1. **Escopo das tabelas:** “prioridades 1 a 6” era ambíguo, pois há prioridades 1B e itens numerados de 1 a 16. A v3.7 determina tabela numérica para os itens 1–9 e 13–14 e tabela documental para 10–12 e 15–16.
2. **Rio dos Cedros, 2014:** a busca não deve ficar limitada a 08 ou 09/06. A v3.7 explicita o conflito entre o resumo do PLANCON (08/06) e a sequência intradiária que pode apontar para 10/06, sem elevar essa inferência a fato.
3. **Publicações futuras:** boletim de setembro de 2026 e tábua de marés de 2027 agora exigem verificação na data da execução; se ausentes, devem ser registrados horário, URL oficial e status de acesso.
4. **Regra do original:** a v3.7 deixa explícito que um número sem PDF/HTML original não é dado validado para cadastro.
5. **Rastreabilidade:** foram incluídos data/hora de coleta, status HTTP, SHA-256 e correspondência inequívoca entre linha e arquivo.
6. **ZIPs:** cada arquivo deve ter menos de 30 MB e ser extraível sozinho; não usar um ZIP fracionado que dependa das demais partes.
7. **Espelhos:** espelho, cache, captura e resumo de busca devem ser identificados e não confundidos com original do órgão.
8. **Privacidade:** correspondência particular pode orientar a pesquisa, mas não deve ser publicada no pacote sem autorização.

## Comparação com a última rodada

| Tema | Última rodada | Situação após revisão |
|---|---|---|
| JICA III-A, Tabela 7.5.1 | Obtida, inclusive página A-80 | Já consta em “JÁ TENHO”; não repetir |
| Boletim SDE 008/2023 | PDF recuperado por URL direta | Já consta no histórico; não é lacuna atual |
| Rio dos Cedros 2014 | Resumo dizia 08/06; série poderia sugerir 10/06 | Conflito incorporado ao prompt; exige prova explícita |
| Blumenau, referência das cotas | Fonte FURB indicava alteração de 40 cm | Mantido como conflito; não converter referências |
| Rio do Sul, régua histórica | Não resolvido | Continua pendente |
| Barragem Oeste, 99,96 hm³ | Definição/cota não resolvida | Continua pendente; novos indícios não fecham a questão |
| Tábua de marés 2027 | Não disponível na consulta anterior | Exige nova verificação datada, sem promessa futura |
| Ascurra, Guabiruba e Itajaí | Sem documentos conclusivos | Continuam pendentes |

## Decisões de cadastro sugeridas

- **Blumenau, 12/10/2023:** preferir 10,76 m quando acompanhado do original da lista oficial; conservar 10,61 m como valor divergente não adotado se o original do g1 não estiver disponível.
- **Brusque, 1984:** adotar 10,30 m se o documento original da Defesa Civil identificar a régua; manter 10,5 m apenas como divergência histórica, sem substituir silenciosamente.
- **Ascurra, 01/09/2026:** 10,13 m às 05:10 pode ser cadastrado se o arquivo original da DCSC-00003 estiver preservado e a fonte confirmar que é a crista, não apenas uma leitura.
- **Gaspar e Indaial:** não misturar séries sem referência. Cadastre somente em séries separadas, com campo de referência/estação obrigatório; se a régua não estiver declarada, use “referência não declarada” e desabilite comparações automáticas.
