# Importar os 71 registros de Gaspar — o que está pronto e o que falta

Data: 07/09/2026.

Gaspar tem **zero picos** em `enchentes.json` e **1.619 cotas de rua**: sabe-se em
que nível cada rua alaga e não se sabe em que nível o rio esteve. A página
`/enchentes` da Defesa Civil do município traz **71 registros de 1852 a 2023**,
com data de início, data de término e metragem máxima. Seria a **maior entrada
única já feita na base**.

`scripts/importar_gaspar_enchentes.py` está pronto e testado. **Nada foi
importado**: este ambiente tem `defesacivil.gaspar.sc.gov.br` bloqueado (403 no
CONNECT do proxy, medido hoje).

```
# na VPS, ou com a página salva
python3 scripts/importar_gaspar_enchentes.py            # só relata
python3 scripts/importar_gaspar_enchentes.py --gravar   # escreve
```

---

## O que eu consegui conferir daqui, e é o mais importante

Cruzei os **oito valores de controle** contra a base, usando a mesma semântica de
pareamento do site (`web/src/logica/datas.ts`, tolerância de sete dias). **Seis
batem com um evento já cadastrado a zero ou um dia de vão** — o que confirma que
a fonte é real, que o formato é `dd/mm/aaaa` e que a escala de Gaspar conversa
com a das outras cidades:

| Gaspar | Pico | Pareia com | Vão |
|---|---|---|---|
| 29/10/1852 | 12,00 m | Blumenau 1852-10-29 (16,30) | 0 d |
| 23/09/1880 | 12,56 m | Blumenau 1880-09-23 (17,10) | 0 d |
| 29/05/1911 | 12,42 m | **Rio do Sul 1911-05** (12,20) | 0 d |
| 07/08/1984 | 11,40 m | Blumenau 1984-08-07 (15,46) | 0 d |
| 24/11/2008 | 9,80 m | Blumenau 2008-11-24 (11,52) | 0 d |
| 12/10/2023 | 7,45 m | Blumenau 2023-10-13 (10,61) | 1 d |

⚠️ **O de 1911 quase virou um falso alarme meu.** Na primeira passada comparei só
contra Blumenau, cujo evento de 1911 é de **outubro**, e o 29/05 apareceu como
"não pareia, 126 dias". 1911 teve **dois** eventos: o de maio está em **Rio do
Sul**. Comparar contra uma cidade só produz um "não" que não existe.

## ⚠️ Dois dos oito NÃO pareiam, e o padrão é estranho

| Gaspar | Pico | Mais perto | Vão |
|---|---|---|---|
| **09/11/2011** | 9,42 m | Rio do Sul 2011-09 (12,96) | **40 d** |
| **09/06/1983** | 11,50 m | Blumenau 1983-05-20 (12,52) | **20 d** |

Nos dois casos o **dia bate com um pico conhecido de Blumenau** e o **mês não**:
Blumenau tem **09/09/2011** (12,80 m) e **09/07/1983** (15,34 m). Mesmo dia, mês
diferente, nas duas linhas.

Pode ser erro de mês na fonte, pode ser evento local de verdade — Gaspar é a
confluência do Itajaí-Açu com o Rio Luís Alves e alaga por conta própria.
**Não dá para decidir daqui, e não se decide por parecer.** O importador marca
esses registros com `pareamento: "sem par"` e a nota dizendo qual era o
candidato mais próximo; nem conserta nem descarta.

⚠️ **Ressalva sobre esta análise:** os oito valores vieram da transcrição do
levantamento, não da leitura da página. Um deslize de transcrição é tão provável
quanto um erro da fonte. **A primeira coisa a fazer com a página aberta é olhar
essas duas linhas.**

## O ensaio com o validador

Rodei a importação da amostra de nove linhas contra uma cópia de
`enchentes.json`: **0 erros**. E o validador achou os mesmos dois registros
sozinho, por outro caminho — a guarda que já existia ("*X não tem evento de
gaspar no mesmo mês*") acusou 1983-06-09 e 2011-11-09. Duas verificações
independentes apontando as mesmas duas linhas.

Aviso de escala: nove registros levaram os avisos de 16 para 33, porque a guarda
é por par. **Os 71 vão gerar muito aviso** — é ruído esperado, não defeito.

---

## As três armadilhas que o importador trata

**1. A data é do INÍCIO do evento, não do pico.** Vai para `data` assim mesmo,
mas marcada: `data_e_do_inicio_do_evento: true`, com `data_fim` ao lado. Isso
**não atrapalha o pareamento** da previsão, que tolera sete dias — atrapalharia
qualquer cálculo de **horário**, e por isso o registro diz o que é. Continua
valendo: **não calibra tempo de trânsito**.

**2. A fonte publica uma data impossível.** O registro de 20/11/1855 traz
término **24/11/9855**. O importador **preserva o original** e marca
`data_anomala`. Virar 9855 em 1855 em silêncio apagaria a prova de que a fonte
errou — mesma classe de erro que este projeto persegue em toda parte. Há teste
exigindo que o valor gravado **não contenha** "1855".

**3. Data que não pareia é suspeita, não é fato.** Vira `pareamento: "sem par"`
com o candidato nomeado na nota.

## Decisões tomadas, para não se perder

- `confianca: "alta"` — a fonte é a Defesa Civil do próprio município, e a
  escala do projeto diz *alta = oficial/acadêmica*. As ressalvas de data vão na
  `nota`, não rebaixam o valor.
- `referencia: "régua"` — as cotas de rua e o tempo real de Gaspar são régua.
  Misturar com o datum IBGE de Blumenau é a `REGRA_REFERENCIA_BLUMENAU`. Travado
  por teste.
- **Idempotente**: não sobrescreve `(cidade, data)` que já exista, e acrescenta
  ao fim sem reordenar a série histórica.
- **Não grava sem `--gravar`.**

## O que falta

1. Rodar de fora, ou salvar a página e passar `--arquivo`.
2. **Olhar as duas linhas sem par** (09/11/2011 e 09/06/1983) na página aberta.
3. A estrutura da tabela **não foi conferida** contra a página real. O parser
   acha as colunas pelos cabeçalhos, aceita várias grafias e, quando não
   encontra, **imprime os cabeçalhos que a página trouxe** — o conserto vira uma
   linha. Mesma disciplina de `ana_inventario.py`.
4. A **Carta de Enchente** de Gaspar, com dados atribuídos ao CEOPS, continua
   sem levantamento.
