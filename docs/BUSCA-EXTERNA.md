# O que falta — roteiro para busca externa

**Para quem recebe este arquivo:** você vai procurar dados que faltam a um site de
enchentes do Vale do Itajaí (Santa Catarina, Brasil). Você **não tem acesso ao
repositório** — tudo o que precisa saber está aqui. Gerado em 07/09/2026.

---

## 0. Leia isto antes de procurar qualquer coisa

O site mostra o nível dos rios **Itajaí-Açu** e **Itajaí-Mirim** para moradores,
durante enchentes. A regra que manda em tudo:

> **É melhor dizer "não sei" do que dar um número errado.
> Nunca fazer alguém se sentir mais seguro do que está.**

Disso saem quatro regras práticas que **valem para toda resposta que você trouxer**:

1. **Toda régua tem seu próprio zero.** 7 m em Gaspar não é 7 m em Blumenau, e o
   nível da rede estadual não é o nível da régua municipal *na mesma cidade*.
   Medimos: em Rio do Sul, no mesmo minuto, a rede estadual deu **3,92 m** e a
   régua municipal **5,24 m** — 1,32 m de diferença. **Nunca compare metros de
   fontes diferentes sem provar que são a mesma régua.**
2. **Diga sempre de onde veio.** Um número sem fonte, data e nome da régua é
   inútil aqui — não será cadastrado. Prefira o documento oficial (Plano de
   Contingência, PDF da Defesa Civil) à notícia de jornal.
3. **Não preencha lacuna com estimativa.** Se não achou, escreva "não achei". Um
   `null` documentado vale mais que um número plausível.
4. **Data e ano importam.** Registre a data de publicação da fonte. Cota de 2014
   pode estar obsoleta por obra de drenagem.

---

## 1. ⚠️ Sete armadilhas que já custaram caro — não caia nelas de novo

Estas são erros **reais** que este projeto cometeu e corrigiu. Elas vão aparecer
de novo na sua busca, com outra roupa.

### 1.1 "Cota de rua alagando" não é "cota de atenção"

Duas vezes o projeto gravou, no campo *atenção*, o nível em que **uma rua começa
a alagar** — porque era o único número que existia. Nos dois casos a escala real
do município existia, só estava em outro lugar da mesma página:

| Cidade | Estava gravado | Escala real do município | Erro |
|---|---|---|---|
| Indaial | atenção 6,00 m | 3 / 4 / 5,5 m | avisava **1,5 m depois** da emergência |
| Brusque | atenção 4,80 m | atenção 3,00 / emergência 5,00 m | avisava **1,80 m tarde** |

**O que fazer:** quando achar um número de "cota", pergunte se ele é um *limiar de
aviso* ou a *consequência* (rua alagando, ponte fechando). Procure a legenda da
estação e a aba "Arquivos"/anexos da página — em Indaial a escala estava num PDF
sem rótulo, num ícone de download.

### 1.2 Mesmo município ≠ mesma estação

A estação **"Salseiro – Vidal Ramos"** parecia ser a régua de Vidal Ramos. Não é:
Salseiro é uma **localidade rural** do município, e a estação fica a **6,8 km** da
régua da sede. Outro ponto do rio = outro zero = a cota **não** se transplanta.

O mesmo com **"BOTUVERA-MONTANTE"** (a 3,47 km de Botuverá) e **"WARNOW"**
(sucessora de "INDAIAL" na ANA, a 3,95 km do nosso ponto).

**O que fazer:** o nome do município no rótulo da estação **não prova** que é a
régua da cidade. Traga sempre **coordenada** e **área de drenagem**.

### 1.3 Zero servido como medição

Duas estações publicam número onde não têm dado:

- **Ribeirão Belchior (Gaspar)**: publica `0,00` em todos os pontos das últimas
  12 h. Zero não é "rio seco", é "sem leitura".
- **Salseiro (estação 31 de Brusque)**: mostra nível de **18/04/2026** como se
  fosse de agora, com o rótulo verde "situação de NORMALIDADE". No mesmo cartão,
  as chuvas acumuladas aparecem como `---` e a "chuva atual" como `0,00 mm` — ou
  seja, a própria página prova que `---` é o "não tenho dado" dela, e o `0,00` ao
  lado é fabricado.

**O que fazer:** sempre anote a **data/hora da última medição**. Uma página que diz
"minuto a minuto" pode estar servindo um número de meses atrás.

### 1.4 A faixa verde do topo é do município, não da estação

Nos portais da plataforma DEXTAK (Gaspar, Brusque) há uma faixa "situação de
NORMALIDADE" no alto de **todas** as páginas. Ela é o estado declarado do
município — não o estado da estação que você está lendo.

### 1.5 O link óbvio pode servir o ano errado

A busca por "tábua de maré" leva primeiro a uma página intitulada **"Tábuas de Maré
2025"** que serve um PDF cujo nome interno é `CAPA-TABUAS-DAS-MARES-2024`.
**Confira o ano DENTRO do documento**, nunca o título da página.

### 1.6 "Ativo" no cadastro não quer dizer transmitindo

A estação **83800002 (Blumenau)** da ANA consta como `Desc. Status: Ativo` e sua
última transmissão foi em **07/02/2024**. Dois anos e meio parada.

### 1.7 A régua pode trocar de grandeza no meio do caminho

Em **abril de 2026** o sistema de medição de **Guabiruba** passou a usar "cota
automática", referenciada ao **nível do mar**: a leitura virou **28,4 m** com o rio a
cerca de 4 m. Não é sensor quebrado nem escala desconhecida — é **outra grandeza**,
altitude em vez de régua, e há uma **quebra de série datada** ali.

Detalhe que vale para qualquer verificação automática: o nosso corte de plausibilidade
era 30 m, e **28,4 m passa por baixo dele**. Valor absurdo é rede de segurança, não
primeira linha — o que pegou foi uma lista escrita à mão.

### 1.8 Ausência de dado não é dado

Se uma tabela não lista uma cidade, isso **não** significa que a cidade não tem o
dado — significa que aquela tabela não o traz. Diga qual fonte você consultou e o
que ela não tinha.

---

## 2. O que JÁ ESTÁ RESOLVIDO — não perca tempo

| Item | Situação |
|---|---|
| Cotas de Indaial | ✅ 3 / 4 / 5,5 m, RN 1402-X do IBGE (cota 61,49 m) |
| Cotas de Brusque | ✅ atenção 3,00 / emergência 5,00 m (portal municipal) |
| Picos de Indaial | ✅ 16 registros (Ademar Cordeiro, projeto Crise/FURB) |
| Picos de Gaspar | ✅ 48 registros (portal da Defesa Civil de Gaspar) |
| Cotas de rua de Gaspar | ✅ 1.617 pontos |
| Cotas de rua de Blumenau | ✅ 2.023 pontos |
| Cotas de rua de Rio do Sul | ✅ 555 pontos |
| Cotas de rua de Brusque | ✅ 377 pontos |
| Código ANA de Rio do Sul, Blumenau, Gaspar, Taió, Ituporanga, Brusque | ✅ confirmados por coordenada |
| Cotas das réguas DC-01…DC-11 de Itajaí | ⚠️ **JÁ EXISTEM** (Tabela 11 da v17) — e há **conflito aberto** com uma leitura da Tabela 13; ver `BUSCA-EXTERNA-RODADAS.md`. **Não trazer mais valores dessa tabela sem a VERSÃO do documento** |
| Estação oficial do aviso de Ituporanga | ✅ **83250000** (ANA/EPAGRI), com atenção 1,40 / alerta 1,90 / emergência 2,60 — resolvido |
| Tábua de maré do CHM | ✅ o PDF de 2026 cobre até **31/12**; falta importar. 2027 não existe |
| `Indaial → Blumenau` no trânsito | ⛔ **não procurar** — ver §6 |

---

## 3. 🔴 PRIORIDADE 1 — Cotas oficiais (a cor da tela não existe sem elas)

Sem cota, a cidade fica **cinza no mapa mesmo tendo leitura de nível**. É o item
mais barato de resolver e o de maior efeito visível.

### 3.1 Vidal Ramos — o caso mais urgente da lista

**É a única cidade que TEM leitura de nível chegando e mesmo assim fica cinza.**
Falta só a escala.

- **Régua:** a estação **DCSC-00024**, chamada "Vidal Ramos (Asthon)" na rede
  estadual. Coordenada **−27,38547 / −49,35812**. Publica agora (~2,4 m).
- **Procurar:** as cotas de atenção / alerta / emergência **dessa régua**.
- **Onde:** Defesa Civil de Vidal Ramos (SC); Plano de Contingência (PLANCON) do
  município; Defesa Civil de SC.
- **⛔ NÃO ACEITAR:** as cotas da estação "Salseiro – Vidal Ramos"
  (`defesacivil.brusque.sc.gov.br/estacao/ver/31`, normalidade < 3,00 / atenção
  3,00 ou chuva > 35 mm / emergência 4,50). **Já foram rejeitadas** — ver §1.2.

### 3.2 As outras 11 cidades sem cota

Procurar **atenção, alerta e emergência**, com a régua identificada:

**Rio Itajaí-Açu:** Lontras · Ascurra · Timbó · Trombudo Central · Itajaí

> **Ituporanga saiu desta lista em 07/09/2026 — a escala existe, o vínculo é que não.**
> A SPDC/SC publica normal < 1,40 / atenção > 1,40 / alerta > 1,90 / emergência > 2,60 m
> (documento de 18/10/2024), **amarrados à estação 83250000** — que fica a 9,59 km do
> nosso pino e drena 1.650 km² contra os 1.170 km² da nossa 83145140. Não é mais "procurar
> a escala": é **descobrir qual estação alimenta o aviso de Ituporanga hoje**, perguntando
> à Defesa Civil de SC ou à EPAGRI. Ver `docs/BUSCA-EXTERNA-RODADAS.md`.
**Rio Itajaí-Mirim:** Botuverá · Guabiruba · Itajaí

> Atenção em **Lontras, Timbó e Trombudo Central**: há número guardado para elas,
> mas é "marca de comportamento" (quando tal rua alaga), não escala de aviso.
> Precisamos da **escala**.

**Onde procurar, em ordem de qualidade:**

1. **PLANCON** (Plano de Contingência) do município — costuma ter a tabela de
   cotas por faixa. É a melhor fonte.
2. Página de monitoramento da Defesa Civil municipal — a **legenda da estação**
   (é onde estavam as de Gaspar e Brusque).
3. Defesa Civil de SC (`monitoramento.defesacivil.sc.gov.br`).
4. EPAGRI/Ciram — publica limiares por faixa para algumas estações.

**O que trazer:** cidade · nome da régua · os três valores · fonte com URL · data
de publicação · se a fonte diz a que referência vertical o zero se liga.

---

## 4. 🟠 PRIORIDADE 2 — Fonte de nível ao vivo (12 cidades cinza)

Sem leitura, o pino fica cinza e **nenhuma pesquisa em acervo histórico o acende**.

**Cidades:** Ituporanga · Ibirama · Lontras · Ascurra · Indaial · Gaspar · Ilhota ·
Timbó · Rio dos Cedros · Trombudo Central · Botuverá · Guabiruba

**Dois casos merecem destaque:**

- **Gaspar** — tinha régua no portal municipal
  (`defesacivil.gaspar.sc.gov.br`, estação 21) e ela **sumiu** entre 31/08 e
  07/09/2026, quando o portal foi reformulado. Marcava 3,85 m em 31/08.
  Procurar: para onde foi, ou o endpoint que a página consome.
- **Ilhota** e **Guabiruba** — não têm **nenhuma** fonte cadastrada. Começar do zero.

**O que trazer:** a **URL do endpoint JSON/API** que a página de monitoramento
consome (melhor que a página), ou o endereço da página. Diga se exige login.

> 10 dessas 12 já aparecem na rede estadual
> (`monitoramento.defesacivil.sc.gov.br`), mas com **zero diferente** do
> municipal — por isso não servem para pintar a cor. Ver §7.

---

## 5. 🟡 PRIORIDADE 3 — Picos históricos (a previsão a jusante)

A previsão montante→jusante precisa de **pelo menos 5 eventos** com registro nas
duas cidades. Abaixo de 5, o site diz "dados insuficientes" — e é isso que ele
mostra hoje na maioria das cidades.

| Cidade | Picos hoje |
|---|---:|
| Ituporanga, Ibirama, Lontras, Ascurra, Ilhota, Rio dos Cedros, Trombudo Central, Vidal Ramos, Botuverá, Guabiruba, Itajaí | **0** |
| Taió, Timbó | **1** |
| Rio do Sul, Brusque | **9** |

**Onde procurar:** acervos das Defesas Civis municipais · CEOPS/FURB (⚠️ o site
`ceops.furb.br` está **fora do ar** desde 07/09/2026 — procurar em arquivos,
Wayback Machine, ou contato direto com a FURB) · jornais locais (Diplomata FM,
Olhar do Vale, O Município, Jornal de Santa Catarina) · ANA/HidroWeb.

**O que trazer:** cidade · data (dia/mês/ano quando houver) · nível em metros ·
**nome da régua** · fonte · se a fonte declara a referência vertical.

**Grande evento a priorizar:** 1983, 1984, 2008, 2011, 2023 — as maiores cheias
modernas do Vale.

---

## 6. 🟡 PRIORIDADE 4 — Tempo de trânsito entre cidades

Quanto tempo a cheia leva para descer de uma cidade à seguinte. Hoje há 9 trechos
cadastrados; faltam 7 que valem procurar (dois saíram da lista — ver abaixo). **A Defesa Civil de Brusque opera exatamente assim** —
olhando Vidal Ramos → Botuverá → Brusque em sequência.

**Faltam (procurar):**

| De → Para | Rio |
|---|---|
| Rio do Sul → Lontras | Açu |
| Lontras → Ascurra | Açu |
| Ascurra → Indaial | Açu |
| Rio dos Cedros → Timbó | Açu |
| **Vidal Ramos → Botuverá** | Mirim |
| **Botuverá → Guabiruba** | Mirim |
| **Guabiruba → Brusque** | Mirim |

Os três do Mirim são os mais valiosos: destravam a lógica que a Defesa Civil já usa.

### ⛔ Saíram desta lista em 07/09/2026: `Ibirama → Rio do Sul` e `Timbó → Indaial`

Estavam aqui como "procurar", e **não são coisa a procurar**. Ibirama corre no Rio
Hercílio e Timbó no Rio Benedito — os dois são **afluentes laterais**, e a outra ponta
está no **tronco** do Açu.

Aí não há viagem da cheia: o pico do tronco vem da cheia que desce o tronco, e o do
afluente vem da chuva na sub-bacia dele. O vão entre os dois é a **coincidência de dois
hidrogramas independentes** — muda de valor, e até de sinal, de cheia para cheia. Um
número ali teria cara de tempo de trânsito sem ser um.

Mesma família do `Indaial → Blumenau` abaixo. **Nem outra fonte nem uma cheia medida
resolvem: a grandeza não existe.**

### ⛔ NÃO procurar: `Indaial → Blumenau`

Não é um tempo de trânsito. O relatório JICA tem as duas pontas e a diferença
**não é positiva** (+0 h, +0 h, −1 h, −1 h para os tempos de retorno de 5, 10, 25
e 50 anos): o **Rio Benedito** entra entre as duas cidades e **adianta** o pico de
baixo. Inventar um número positivo daria horas que não existem.

**O que trazer:** faixa em horas ("14–17 h"), nunca número exato · fonte · em que
condição foi medido (cheia grande? qual?).

**Onde procurar:** relatório **JICA 2011** (`openjicareport.jica.go.jp`, a Tabela
7.5.1 é a que já usamos e ela não lista essas cidades) · estudos da bacia ·
horários de pico registrados pela Defesa Civil em cheias reais (dá para calcular:
hora do pico na cidade de cima menos hora do pico na de baixo).

---

## 7. 🔵 PRIORIDADE 5 — Offset da rede estadual (destrava 10 cidades de uma vez)

**Este é o item de maior alavancagem da lista inteira.**

Dez das doze cidades sem leitura **já têm nível chegando** pela rede estadual:

```
Ascurra 7,49   Ilhota 9,55   Indaial 5,98   Lontras 3,94   Ituporanga 0,98
Botuverá 2,72  Ibirama 2,19  Timbó 1,36    Rio dos Cedros 1,10  Vidal Ramos 2,40
```

Não podem pintar a cor porque **o zero estadual não é o zero municipal**. Prova:
Rio do Sul deu 3,92 m (estadual) e 5,24 m (municipal) no mesmo minuto.

E o perigo é concreto: Indaial marcou **5,98 m na rede estadual num dia sem
chuva**, enquanto a emergência municipal é **5,50 m**. Pintar vermelho ali seria
alarme falso com o rio parado.

**O que procurar:** para cada estação da rede estadual, **a cota do zero da régua**
(altitude do zero, ou a referência vertical a que se liga). Com isso o offset por
estação sai por conta.

**Onde:** Defesa Civil de SC (é quem opera) · EPAGRI/Ciram · ANA/HidroWeb, que
publica a cota do zero de estações fluviométricas.

**Também útil:** acesso à operação `historic` do GraphQL em
`monitoramento.defesacivil.sc.gov.br/graphql`. A introspecção está aberta e a
consulta existe, mas é bloqueada por lista de operações permitidas — **não tente
forjar a requisição**, é pedido a fazer à Defesa Civil de SC.

---

## 8. 🟢 PRIORIDADE 6 — Itens pontuais

### 8.1 Tábua de maré do porto de Itajaí — ⏰ prazo curto

A tábua atual **acaba em 30/09/2026**. Depois disso a tela da foz fica sem maré.

- Fonte localizada: CHM/Marinha, `marinha.mil.br/chm/tabuas-de-mare-6`, arquivo
  "52 - PORTO DE ITAJAÍ - 166 - 168.pdf". Metadados: Nível Médio 0,6 m, Carta
  1841, fuso UTC−03:00.
- **Não existe edição 2027** (conferido em 07/09/2026). Importar a de 2026 só leva
  até 31/12/2026.
- ⚠️ Ver armadilha §1.5 (o link óbvio serve 2024).
- **Procurar:** se surge edição 2027; ou outra fonte de previsão harmônica para
  Itajaí que publique **altura com o datum declarado**.

### 8.2 CEOPS/FURB fora do ar

`ceops.furb.br` não responde (nem http nem https, conferido 07/09/2026 — e não é
queda geral da FURB: `labgeo.furb.br` responde). O CEOPS é a origem de várias
fontes do projeto. **Procurar:** novo endereço do acervo, ou confirmação de que
saiu do ar; cópias no Wayback Machine.

### 8.3 Códigos ANA que faltam

Sem código ANA confirmado: Ibirama · Lontras · Ascurra · Indaial · Ilhota · Timbó ·
Rio dos Cedros · Trombudo Central · Vidal Ramos · Botuverá · Guabiruba · Itajaí.

⚠️ Já **descartados** por coordenada (não sugerir de novo): `83520000 WARNOW` para
Indaial · `83892990 SALSEIRO` para Vidal Ramos · `83892998 BOTUVERA-MONTANTE` para
Botuverá · `83250000` para Ituporanga.

**O que trazer:** código · nome oficial · **coordenada** · área de drenagem · tipo
(fluviométrica/pluviométrica) · período da série.

### 8.4 Cotas de rua

Faltam em 15 cidades. A única com manchas de inundação e nenhuma cota de rua é
**Itajaí** — o dado está num ArcGIS fechado por token da prefeitura.

---

## 9. Como me devolver o resultado

Um arquivo por assunto, em Markdown, com **uma linha por achado**:

```
CIDADE | O QUE É | VALOR | RÉGUA/ESTAÇÃO | FONTE (URL) | DATA DA FONTE | RESSALVAS
```

E, no fim, uma seção **"o que procurei e não achei"** — ela vale tanto quanto os
achados, porque impede que a mesma busca seja refeita daqui a um mês.

**Se a fonte for ambígua, diga que é ambígua.** Não escolha por nós.
