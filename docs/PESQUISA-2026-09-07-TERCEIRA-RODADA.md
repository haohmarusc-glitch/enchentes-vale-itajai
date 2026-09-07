# Terceira rodada de pesquisa — 07/09/2026

Levantamento do Jefferson, ampliando termos e cruzando documento oficial, estudo
acadêmico e imprensa local. Trouxe **uma correção de rumo em Brusque** e fechou a
questão de fonte em Gaspar.

**Nada aqui foi importado.** Este documento registra o que a busca achou, o que
isso muda de decisão, e o que continua faltando. Os valores citados vêm do
levantamento — **não foram lidos na fonte por este ambiente**, que não alcança
`*.ana.gov.br`, `marinha.mil.br` nem `defesacivil.*.sc.gov.br`.

---

## 🔴→🟡 Brusque: a pergunta estava errada, não a resposta

Eu vinha procurando "a cota de alerta de Brusque". A evidência de agosto/setembro
de 2026 diz que essa pergunta não tem resposta, porque **não é assim que a Defesa
Civil opera**.

Na cheia de 31/08–01/09/2026, com estado de **atenção** declarado:

| Momento | Vidal Ramos | Botuverá | Brusque | Estado declarado |
|---|---|---|---|---|
| 31/08–01/09 | 3,31 m | 4,86 m | **3,49 m** | atenção |
| dia seguinte, na recessão | 3,00 m | 4,45 m | **5,04 m** | atenção |
| pico da mesma cheia | — | — | **5,74 m**, depois 5,10 m | alagamentos nas áreas previstas |

Fonte: Olhar do Vale e Diplomata FM, cobertura do evento.

**O que isso mede, e é o ponto:** a mesma palavra — "atenção" — cobriu Brusque a
**3,49 m** e a **5,04 m**, com um pico de 5,74 m no meio. A nossa `atencao` de
Brusque é **4,80 m**, e ela cai **entre** os dois. Ou seja, o rótulo da Defesa
Civil não é função da régua de Brusque: **em um momento o site pintaria mais
calmo que a Defesa Civil (3,49 m, abaixo da nossa cota) e em outro mais grave
(5,04 m, acima)** — nos dois casos por motivo estrutural, não por erro de número.

A Defesa Civil está olhando **Vidal Ramos → Botuverá → Brusque** e a tendência,
que é exatamente a lógica montante → jusante que este projeto quer construir.

### O que muda de decisão

1. **Não inventar `alerta` para Brusque.** A auditoria de lacunas marca Brusque
   como "cota incompleta"; a leitura correta dessa marca não é "falta preencher",
   é "a cidade não opera por cota isolada". Fica gravado em `cotas_ressalva`.
2. **A régua de Brusque sozinha não decide a cor.** Enquanto a previsão a jusante
   não existir, a tela continua mostrando o número e a cota com a ressalva — que
   é o honesto — mas o projeto agora sabe **por que** as duas coisas divergem.
3. **É argumento a favor do trecho que falta.** `botuvera → brusque` e
   `vidal-ramos → botuvera` estão entre os dez elos ausentes de `transito.json`.
   Este evento é a evidência de que a Defesa Civil já usa esse encadeamento.

⚠️ **O que NÃO se conclui:** que a nossa cota de 4,80 m está errada, nem que ela
deva descer para 3,49 m. 3,49 m foi o valor da régua quando um estado de bacia
foi declarado — não um limiar de Brusque. Trocar um pelo outro seria o mesmo erro
de natureza que o projeto recusa em outros lugares.

---

## 🟢 Gaspar: a fonte fechou

A página oficial da Defesa Civil de Gaspar (`/enchentes`) traz **71 registros de
1852 a 2023**, cada um com data de início, data de término e metragem máxima.

Controles para a importação futura conferir:

| Evento | Pico |
|---|---|
| 12/10/2023 | 7,45 m |
| 09/11/2011 | 9,42 m |
| 24/11/2008 | 9,80 m |
| 07/08/1984 | 11,40 m |
| 09/06/1983 | 11,50 m |
| 29/05/1911 | 12,42 m |
| 23/09/1880 | 12,56 m |
| 29/10/1852 | 12,00 m |

### ⚠️ A armadilha do 9855 — vira teste, não conserto silencioso

A própria fonte traz **`20/11/1855 → término 24/11/9855`**. O importador **não
pode** transformar 9855 em 1855 em silêncio: tem de **preservar o original** e
marcar a data como anômala. É exatamente a classe de erro que este projeto
persegue — o conserto invisível que apaga a evidência de que a fonte estava
errada. Fica como caso de teste obrigatório de `scripts/importar_*` de Gaspar.

**A ressalva anterior continua de pé:** a data publicada é de **início do evento**,
não necessariamente do pico. Não serve para calibrar trânsito da cheia. Gaspar
tem hoje **zero picos** em `enchentes.json`, então esses 71 registros seriam a
maior entrada única já feita na base — razão a mais para a importação ser
conferida, e não automática.

Há também a **Carta de Enchente** oficial de Gaspar, com dados atribuídos ao CEOPS.

---

## 🟡 83690000 INDAIAL: é reconciliação de versões, não um offset

Documento da **ANEEL** registra que a ANA informou, sobre a 83690000:

- os dados fluviométricos precisavam de **revisão**;
- isso incluía a **curva-chave**;
- havia dados usados **depois de 2008 que não estavam consistidos** pela ANA;
- a **área de drenagem cadastrada estava divergente**, e a ANA **alterou essa área
  no HidroWeb em março de 2016**.

Estudo da **UNIVALI** dá a área da 83690000 como **9.850 km², ~66% da bacia do
Itajaí** — e lembra um princípio que vale para nós: estação usada para converter
nível em vazão por curva-chave **deve ficar fora da influência da maré**.

### O que isso muda

O plano anterior era "reconciliar a 83690000" como se fosse somar um número. Não
é: **é reconciliar versões da série e da curva-chave**, com um corte conhecido em
março/2016 e um trecho pós-2008 não consistido. Baixar a série e comparar picos
sem saber de qual versão cada valor veio produz um resultado que parece limpo e
não é.

⚠️ **A área não se funde com a que já temos.** O inventário dá **9.790 km²** para
a **83520000 WARNOW**, que é a sucessora; a UNIVALI dá **9.850 km²** para a
**83690000**. São estações diferentes, e ainda por cima a área da 83690000 mudou
de cadastro em 2016. Guardar lado a lado, como já se faz com as áreas das
barragens em `hidraulica.json` — **não escolher em silêncio**.

---

## 🔴 Indaial COMPDEC ↔ DCSC-00006: a busca voltou vazia, e isso se registra

Nova rodada com DCSC-00006, SDC-SC Indaial, COMPDEC, datas de outubro de 2023,
estação, nível, API e combinações: **não recuperou o valor histórico simultâneo da
DCSC-00006**.

Continua assim:

```
COMPDEC     05/10/2023 08:00 = 5,27 m
DCSC-00006  05/10/2023 08:00 = desconhecido
Δ = 5,27 − ?
```

**O offset não vai ser fabricado.** Um resultado negativo de busca é resultado: o
caminho deixa de ser busca textual e passa a ser API/backend do monitoramento
estadual, arquivo histórico, ou ofício à Defesa Civil.

---

## 🟢 Maré: a fonte está definida, com uma correção

Confirmado que o Porto de Itajaí é a **tábua nº 52, páginas 166–168**, do CHM para
2026. **Correção importante:** a Marinha comercializa a **edição completa** da
Tábua das Marés; o que é aberto é o **produto de dados por estação**. Não se deve
presumir que exista um PDF gratuito da edição inteira esperando download.

**Decisão:** usar o produto oficial de dados de maré do CHM para o Porto de
Itajaí, e não depender de agregador comercial. A tábua atual acaba em
**30/09/2026** — 23 dias.

---

## Resumo

| Item | O que destrava | Situação |
|---|---|---|
| CHM / Itajaí | os dias de maré depois de 30/09 | 🟢 fonte definida |
| Gaspar `/enchentes` | 71 picos, a maior entrada única na base | 🟢 fonte resolvida, importação a conferir |
| Brusque / Mirim | aviso antecipado montante → jusante | 🟡 descoberta conceitual: não há cota isolada |
| 83690000 | histórico coerente de quatro cidades | 🟡 reconciliar versões, não somar offset |
| COMPDEC ↔ DCSC-00006 | alarme confiável de Indaial | 🔴 falta o dado simultâneo |
