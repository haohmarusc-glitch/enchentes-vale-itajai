# Indaial: como o erro entrou, e o que o consertou

Resolvido em 06/09/2026, com o PDF lido na fonte pelo Jefferson (o proxy do
ambiente de desenvolvimento recusa `indaial.atende.net`).

## O erro

O cadastro trazia `atencao: 6,00 m`. A escala que a COMPDEC publica é:

| Metragem | Situação |
|---|---|
| até 3 m | Normal |
| 3 a 4 m | **Atenção** |
| 4 a 5,5 m | Alerta |
| acima de 5,5 m | **Emergência** |

**A "atenção" cadastrada ficava 1,5 m ACIMA da emergência do município.** A tela
chamaria de "abaixo da atenção" um nível que Indaial já trata como emergência —
o lado perigoso, o único que este projeto não pode errar.

## Como entrou, e por que não foi descuido

A `observacao` antiga dizia, com todas as letras, o que estava sendo feito:

> a COMPDEC de Indaial **NÃO publica faixa de atenção, alerta ou emergência**.
> O que ela publica é uma lista de 12 vias com alagamento JÁ REGISTRADO a
> 6,00 m na régua. Os 6,00 m estão gravados aqui como 'atencao' porque é o
> único número que existe (…) **mas o nome é NOSSO, não da COMPDEC**.

Quem gravou o 6,00 m foi honesto: documentou que o rótulo era invenção nossa e
explicou por quê. O erro não foi de descuido — **foi de alcance**. A escala
existe, e está num PDF na aba **ARQUIVOS** da mesma página. Quem leu, leu a
página; o anexo ficou.

**A lição:** "a fonte não publica X" é uma afirmação sobre a nossa busca, não
sobre a fonte. Antes de inventar um rótulo nosso, esgotar os anexos.

## As duas informações convivem

Os 6,00 m continuam valendo — como o que sempre foram: **alagamento de rua**,
que começa meio metro depois de a emergência abrir. Não são degrau da escada de
aviso e não entram em `cotas_m`. A lista das 12 vias é dado útil e continua no
cadastro como observação.

## A referência estava resolvida no próprio PDF

O PDF diz que 5,5 m equivale a aproximadamente a **cota 67 m** acima do nível do
mar. Como **67 − 5,5 = 61,5**, e o RN 1402-X do IBGE (perto da rua Tiradentes)
tem cota **61,49 m**, o zero da régua **é** o RN.

Não há duas referências verticais concorrentes, e a escala publicada é a
operacional. Cai a hipótese de datum diferente levantada em
`PESQUISA-2026-09-06-CRUZAMENTO.md`.

## O que a correção tornou urgente

A rede estadual lê **6,06 m** em Indaial (DCSC-00006, medido 06/09/2026 16:31).
A emergência da COMPDEC é **5,50 m**.

**Se fossem a mesma régua, Indaial estaria em emergência agora.** Não são: o
dado estadual vem com `datum: bruto_estadual` e `offset_datum: null` — o
deslocamento entre os dois zeros é desconhecido —, e por isso carrega
`usar_para_cota: false` e aparece em violeta, sem virar faixa. Isso está certo
e tem de continuar assim.

Repare no que a correção mudou. Com a "atenção" falsa de 6,00 m, o bruto de
6,06 m **parecia bater**, e um pareamento ingênuo passaria despercebido por
parecer calmo. Com a escala real, o mesmo pareamento **gritaria emergência**.
Nos dois casos ele seria igualmente infundado — o que mudou é que agora o erro
seria barulhento em vez de silencioso.

**A pergunta que fecha Indaial** passa a ser: qual é o deslocamento entre a
régua da COMPDEC (zero no RN 1402-X, 61,49 m) e a estação DCSC-00006? Com ele,
Indaial ganha aviso de verdade; sem ele, o número fica em violeta, que é o
honesto.

## Os 16 picos

Entraram os dezesseis, com `confianca: alta` e a fonte creditada (dados do
engenheiro hidrólogo Ademar Cordeiro, projeto Crise / FURB, via o PDF da
COMPDEC), **menos um**:

**23/11/2008, 5,04 m** entrou com `confianca: baixa` e nota. É o MENOR valor dos
dezesseis, e novembro de 2008 foi a maior cheia do Vale no período moderno. Ou é
erro da fonte, ou a linha se refere a outra coisa. **Nenhuma correção foi
inferida** — trocar o número por um "mais plausível" seria inventar medição.

O pedido original era registrar 2008 em `divergencias`. Não cabe: `divergencias`
guarda um valor CONCORRENTE com a sua fonte, e aqui não há segundo valor, há um
valor duvidoso. O arquivo já tem precedente para isso — o registro de 1852 de
Blumenau usa `confianca: baixa` + `nota` para valor contestado. Foi o que se
usou.

**08/09/2014, 6,38 m** ficou literal, com nota. A cheia mais lembrada de 2014 no
Vale é a de junho, e a tentação é "corrigir" setembro para junho. O validador de
meses pareados sinaliza esse par — é sinal para conferir na fonte, não para
trocar a data.

## O que passou a reprovar

- `valida_ordem_das_cotas`: as faixas de uma cidade têm de subir na ordem
  (monitoramento < atenção < alerta < inundação < emergência). Devolver o
  6,00 m dá erro.
- Cinco testes travam a escala de Indaial, a fonte apontando para o PDF (e não
  só para a página) e a referência do RN.
- O conjunto de desalinhamentos de mês conhecidos passou a ser **enumerado com
  o motivo de cada um**, em vez de contado — assim um desalinhamento NOVO
  reprova, e os três que entraram com Indaial não viram ruído.

**Sabotagem conferida:** devolver `atencao: 6,00 m` produz 1 erro no validador e
4 testes reprovados.
