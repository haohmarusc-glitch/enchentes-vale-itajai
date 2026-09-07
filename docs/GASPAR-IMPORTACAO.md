# Gaspar: 49 registros importados, 21 segurados — e por quê

Data: 07/09/2026.

Gaspar tinha **zero picos** em `enchentes.json` e 1.619 cotas de rua: sabia-se em
que nível cada rua alaga e não se sabia em que nível o rio esteve. A tabela da
Defesa Civil chegou pelo celular do Jefferson (a página é inalcançável deste
ambiente e da VPS) com **70 linhas, de 1852 a 2023**.

**Importados 49. Segurados 21.** Gaspar passa de 0 a 49 picos — a maior entrada
única já feita na base.

---

## ⚠️ O achado: a coluna do ANO está desalinhada em dois trechos da tabela

Vinte e um registros não pareavam com evento nenhum já cadastrado. Testei duas
hipóteses e **as duas foram refutadas no conjunto**:

| Hipótese | Conserta | Quebra |
|---|---|---|
| "o mês publicado é um a menos" | 6 | **38** |
| "o ano está deslocado uma linha" | 12 | **29** |

Nenhuma vale para a tabela inteira. **Mas os acertos da segunda não são acaso.**
Onze deles casam com **dia e mês IDÊNTICOS** a um evento já cadastrado, em outro
ano — coincidência de ~1/365 por caso —, e ficam em **dois trechos contíguos**:

| Linha | Publicado | Com o ano da linha de cima | Bate com |
|---|---|---|---|
| 42 | 1950-10-31 | 1953-10-31 | Blumenau 1953-11-01 (1 d) |
| 43 | 1948-10-17 | 1950-10-17 | **Blumenau 1950-10-17** |
| 44 | 1943-05-17 | 1948-05-17 | **Blumenau 1948-05-17** |
| 45 | 1939-08-03 | 1943-08-03 | **Blumenau 1943-08-03** |
| 46 | 1935-11-27 | 1939-11-27 | **Blumenau 1939-11-27** |
| 48 | 1932-10-04 | 1933-10-04 | **Blumenau 1933-10-04** |
| 53 | 1927-06-18 | 1928-06-18 | **Blumenau 1928-06-18** |
| 54 | 1926-11-09 | 1927-11-09 | **Indaial 1927-11-09** |
| 55 | 1925-01-14 | 1926-01-14 | **Blumenau 1926-01-14** |
| 56 | 1923-05-14 | 1925-05-14 | **Blumenau 1925-05-14** |
| 57 | 1911-06-20 | 1923-06-20 | **Blumenau 1923-06-20** |
| 5 | 2011-11-09 | 2013-11-09 | **Blumenau 2013** |

Em negrito, dia e mês idênticos. **Data imprecisa de registro antigo não produz
onze igualdades exatas de dia e mês.** É a assinatura de uma coluna que
escorregou uma linha num pedaço da tabela — o que acontece quando se monta uma
tabela colando colunas de comprimentos diferentes.

### Por que isso impede a importação desses 21

Se o ano está errado, o pico de **8,43 m publicado em 1939** é na verdade o de
**1943**. Uma correlação montante → jusante que pareasse o Gaspar de 1939 com o
Blumenau de 1939 estaria cruzando **águas de cheias diferentes** — e o número que
sairia disso é o que a tela mostraria para quem mora em Gaspar.

Pior: **não dá para saber daqui se escorregou só o ANO ou a data inteira.** No
segundo caso nem o valor pertence àquela linha. Por isso não se conserta e não
se importa: os 21 ficam registrados, com a evidência linha a linha, para o
ofício à Defesa Civil de Gaspar poder citar.

**As duas linhas que o levantamento já tinha estranhado eram reais**, e não erro
de transcrição: `09/11/2011` e `09/06/1983` estão assim na página.

---

## O que entrou

- **49 registros**, de 29/10/1852 a 12/10/2023, maior pico **12,56 m** (23/09/1880).
- `referencia: "régua"` em todos, travado por teste — as cotas de rua e o tempo
  real de Gaspar são régua, e misturar com o datum IBGE de Blumenau é a
  `REGRA_REFERENCIA_BLUMENAU`.
- `confianca: "alta"` — fonte oficial do município. As ressalvas vão na nota.
- Todos com `data_e_do_inicio_do_evento: true`: a data publicada é a de **início**
  do evento, não a do pico. Não atrapalha o pareamento (a tolerância do site é de
  sete dias) e **não serve para calibrar tempo de trânsito**.

## ⚠️ O que a importação NÃO destravou, e é uma surpresa

Eu esperava que a previsão **Blumenau → Gaspar** passasse a sair. Não sai:

| Par | Pares no mesmo evento | Mesma referência? |
|---|---|---|
| Gaspar × Blumenau | 48 | **0** — Gaspar é régua, Blumenau é IBGE ou nulo |
| Gaspar × Indaial | 9 | **9** ✅ ambos régua |
| Gaspar × Rio do Sul | 8 | 0 — Rio do Sul sem referência |
| Gaspar × Brusque | 5 | 0 — Brusque sem referência |

A previsão pareia **igual com igual** na referência, e faz isso certo: 20 cm de
datum entre duas cidades é erro que ninguém vê e todo mundo carrega.

**Consequência que vale registrar: resolver o datum de Blumenau acabou de ficar
muito mais valioso.** Antes, os 41 registros de Blumenau com `referencia: null` e
os 72 em IBGE bloqueavam uma correlação com uma cidade sem dado nenhum. Agora
bloqueiam uma correlação com uma cidade que tem 49 picos e 1.619 cotas de rua —
e que é a próxima a jusante de Blumenau no tronco, a 2 h de distância.

---

## A trava que disparou, e o que ela ensinou

`valida_meses_pareados` acusou **38 desalinhamentos novos**, e o teste
`test_os_desalinhados_dos_dados_reais_sao_EXATAMENTE_os_conhecidos` reprovou —
que é exatamente o que ele existe para fazer.

Fui medir antes de aceitar, e a premissa da trava é que **as duas cidades
registram os mesmos eventos**. Com Gaspar isso é falso:

| Meses de Blumenau | n | Mediana do pico de Blumenau |
|---|---|---|
| em que Gaspar TEM registro | 48 | **11,13 m** (mínimo 8,50) |
| em que Gaspar NÃO tem | 64 | **9,60 m** (mínimo 5,65) |

**Nenhum evento de Blumenau abaixo de 8,50 m tem par em Gaspar.** O menor pico da
lista de Gaspar é 6,19 m e a primeira rua dele alaga a 6,20 m: é uma lista de
cheias **que alagaram**, não de todas as subidas.

Então os 38 avisos são propriedade das FONTES, não erro de dado. Entrou
`LISTAS_SO_COM_CHEIA_GRANDE` no validador, com o motivo medido escrito junto, e
três testes: a exceção precisa de motivo, precisa continuar curta (no máximo
três cidades — porta sem tranca vira corredor), e **a esparsidade tem de
continuar verdadeira no dado**. Se alguém importar as cheias pequenas de Gaspar
um dia, a premissa cai e o teste avisa.

Ruído de 38 avisos não é inofensivo: é assim que uma trava morre, deixando de
ser lida.

---

## Diferenças e pendências

- O levantamento falava em **71 registros**; chegaram **70**. Não sei qual
  faltou — pode ser corte na cópia. Vale conferir o total na página.
- **A data de término é `-` em 69 das 70 linhas.** A única preenchida é a do
  registro de 20/11/1855, e é `24/11/9855` — impossível. Preservada como veio e
  marcada `data_anomala`; há teste exigindo que o valor gravado **não contenha**
  "1855". Consertar em silêncio apagaria a prova de que a fonte errou.
- Os **21 segurados** esperam resposta da Defesa Civil de Gaspar sobre o
  desalinhamento. Para importá-los assim mesmo (não recomendado):
  `--incluir-sem-par`.
- A **Carta de Enchente** de Gaspar, com dados atribuídos ao CEOPS, continua sem
  levantamento.
