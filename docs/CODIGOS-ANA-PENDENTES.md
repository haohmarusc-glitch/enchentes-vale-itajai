# Os códigos ANA — o que a execução de 07/09/2026 respondeu

Continua `docs/INVENTARIO-ANA.md`. As oito estações pendentes foram lidas no
inventário público com `scripts/ana_inventario.py`, rodando **na VPS** — este
ambiente de desenvolvimento tem `*.ana.gov.br` bloqueado (403 no CONNECT do
proxy, inclusive no inventário, que não exige autenticação). Bruto em
`data/brutos/ana-inventario-2026-09-07.json`, gerado na VPS.

**Resultado: uma cidade fechou, quatro "nãos" ficaram provados, uma decisão
sobrou e uma ressalva antiga encolheu.** Todas as oito são fluviométricas —
nenhum pluviômetro disfarçado desta vez.

---

## ⛔ Antes de tudo: um defeito meu, achado na própria saída

A primeira versão do script imprimia a distância com `f"{d:,.0f} m"`. A saída
real trouxe **`4,350 m`** para uma estação a **4.350 metros**. Em português a
vírgula é separador **decimal**: aquilo se lê **4,35 m**.

Erro de mil vezes, e na direção perigosa — faz estação distante parecer colada
na régua, que é exatamente o vínculo errado que este script existe para
impedir. Os vereditos impressos estavam certos (a comparação usa o número, não
o texto), mas quem lesse a saída leria o contrário.

Corrigido: acima de 1 km sai em quilômetros, com vírgula decimal, e nunca há
separador de milhar. Travado em `teste_ana_inventario.py::TextoDaDistancia`.

---

## ✅ Ituporanga fechou — e a resposta veio cruzada

`codigo_ana` de Ituporanga é **83145140 DCSC BARRAGEMSUL ITUPORANGA JUSANTE**:
fluviométrica, 1.170 km², **a 45 m deste pino**. Era o candidato a que faltava
só o tipo.

**A armadilha era a outra.** A `83250000` se chama ITUPORANGA, é fluviométrica
no Itajaí do Sul e tem a série mais longa do ramo — **aberta desde 04/1929, 97
anos**. Estava listada como "a série longa que destrava Ituporanga". A
coordenada desmente: **9,59 km** deste pino, drenando 1.650 km² contra os 1.170
da nossa. É outra estação, em outro ponto do rio. Usar a série dela como
histórico de Ituporanga seria vínculo por **nome de município** com aparência de
vínculo por coordenada — o erro que a regra emendada existe para impedir.
Gravado como `codigo_ana_nao_e`, com teste.

**Duas coisas a lembrar sobre o que ganhamos:**

- O nome diz **JUSANTE DA BARRAGEM SUL**, e é literal: a régua lê água já
  **amortecida pela barragem**. Importa para previsão a jusante e para não ler a
  série como regime natural.
- **A série é curta**: começa em **10/2020**. Não tem 2008 nem 2011.

---

## ❌ Quatro "nãos" provados

Um "não" gravado vale tanto quanto um "sim": sem ele, a próxima rodada de
pesquisa propõe o mesmo vínculo, com a mesma aparência de acerto.

| Cidade | Estação | Distância | Por que não |
|---|---|---|---|
| **Indaial** | 83520000 WARNOW | **3,95 km** | Sucessora da 83690000, 9.790 km², **99 anos** de escala aberta desde 10/1927 — a série mais longa da bacia. A antecessora já ficava a 4,1 km: **a estação da ANA em Indaial nunca foi a nossa régua** |
| **Botuverá** | 83892998 BOTUVERA-MONTANTE | **3,47 km** | O nome já avisava: MONTANTE. Mesma família do Salseiro em Vidal Ramos |
| **Ilhota** | 83870001 ILHOTA-JUSANTE | **1,18 km** | Acima do limite de 1 km. A antecessora 83870000 também ficava a 1,2 km — é o sítio da ANA, não o nosso |
| **Taió** | 83030000 BARRAGEM OESTE | **4,35 km** | É a barragem, não a cidade. Fica a 30 m da DCSC-00040, que não é pino de cidade nenhuma |

O caso de **Ilhota** merece nota: 1,18 km fica perto o bastante para ser
tentador e longe o bastante para ser outra. Sem a cota do zero das duas réguas,
parear as séries somaria um degrau desconhecido.

---

## 🟡 Ibirama: sobrou uma decisão, não uma busca

A **83440000 IBIRAMA** (Rio Hercílio, 3.330 km², escala de 12/1928 a **12/2021**)
fica a **476 m** do nosso pino. Não é os 10 m de Gaspar nem os 6,9 km de
Blumenau: **cai na faixa em que o projeto não tem critério escrito.**

O que resolve não é outra busca, é olhar o Hercílio: se as duas estão no mesmo
trecho reto, é a mesma régua; se há confluência entre elas, não é. **O traçado
do Hercílio não está em `data/rios/`**, então a conferência ainda não pode ser
feita aqui. E vem junto uma segunda pendência: a escala **encerrou em 12/2021**,
então o vínculo precisa declarar `codigo_ana_sucessor` — e as candidatas
conhecidas são de usina (CGH Mafrás Montante, PCH Ibirama Barramento), que medem
barramento, não a cidade.

Gravado como `codigo_ana_candidatos` com o `falta` dizendo isso.

---

## 🔽 Rio do Sul: a ressalva encolheu muito

A dúvida era: a **83094000** fica a **35 m** da nossa régua, mas está cadastrada
no Itajaí do **Oeste**, enquanto o código que usamos (**83300200**) está no
**Açu**, a 0,43 km. Seria a 83094000 a estação daqui?

**O dado que faltava mudou a pergunta: a escala da 83094000 encerrou em 08/2005.**
Ela é a estação que ficava na nossa régua, e está **morta há 21 anos**. A 83300200
é a que continua publicando. **Para o presente não há escolha a fazer.**

Para o histórico resta saber se as duas compartilham o zero — que é a mesma
pergunta do datum de Blumenau, e o inventário público não responde.

⚠️ **Dois sinais de que o cadastro da 83094000 é frágil, e vieram juntos:** a
área aparece como **5.160 km², igual à do Açu**, o que não faz sentido para uma
cabeceira; e a data de início da escala vem como **1800-01-01**, que não é data,
é preenchimento. Não usar nem a área nem o rio declarado dessa estação sem
conferir em outra fonte.

---

## Uma trava precisou de conserto para aceitar Ituporanga

A regra nº 2 do validador media a estação contra o **traçado do rio**. A
83145140 fica a 45 m do pino e a **21,4 km** do traçado do Itajaí do Sul — que
só cobre 10,5 km perto de Rio do Sul. **A estação não está em outro rio; o rio é
que não está desenhado.**

A primeira correção passou a medir contra o **pino** nas cidades com exceção — e
reprovou Blumenau, onde o problema é o oposto: lá o pino é uma régua de **chuva**
a 3 km do talvegue, e a 83800002 está a 6,94 km dele e a **49 m** do traçado.

A regra que ficou: **medir contra as duas referências e valer a mais perto.** A
pergunta é uma só — "esta estação é de outro curso d'água?" — e cada referência
falha num caso diferente. Não abre buraco: o pino já é validado contra o traçado
em `valida_pinos_no_tracado`, com as exceções escritas e datadas. Três testes
por sabotagem travam os dois casos e o buraco que a regra do mínimo poderia
abrir (estação longe das duas continua reprovando).

---

## O que sobrou

1. **Ibirama, 476 m** — decisão, com o traçado do Hercílio.
2. **A cota do zero da régua** — não está no inventário público. Continua sendo
   o que destrava a `REGRA_REFERENCIA_BLUMENAU`, e agora também a comparação
   entre 83094000 e 83300200 em Rio do Sul.
3. **`data/brutos/ana-inventario-2026-09-07.json`** foi gerado na VPS e ainda
   não está no repositório. Os valores gravados aqui vieram da **saída
   transcrita**, não do arquivo — commitar o bruto da VPS fecha isso.
