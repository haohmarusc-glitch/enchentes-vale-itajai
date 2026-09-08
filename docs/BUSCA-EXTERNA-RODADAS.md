# Busca externa, rodadas 1 e 2 — o que voltou em 07/09/2026

Resultado da primeira rodada feita a partir de `docs/BUSCA-EXTERNA.md`, por uma IA
com acesso à web. **Nada foi cadastrado como cota ou pico.** O que entrou no dado
foram registros de investigação, com a fonte e a data.

A disciplina da rodada foi boa e vale dizer onde: ela **recusou** cadastrar
previsão como pico observado, **recusou** dar 1,70 m de emergência à DC-01 por vir
de imprensa, **recusou** Timbó por vir de jornal, e **não sobrescreveu** a decisão
antiga sobre a 83250000 — pediu reconciliação. É exatamente o comportamento que o
roteiro pede.

---

## 🟢 Guabiruba — a causa da anomalia, com data e fonte

**Já estávamos barrando; agora sabemos por quê.**

O coletor estadual tinha Guabiruba (DCSC-00029) em `SUSPEITAS` com a nota "~24,8 m:
estação Hidro real, mas o valor bruto é implausível para o ribeirão — datum/escala
própria não calibrada". Era descrição do sintoma.

A causa: a **Prefeitura de Brusque informou em abril de 2026** que o sistema de
medição de Guabiruba mudou para **"cota automática", referenciada ao nível do mar**.
Na ocasião a leitura aparecia como **28,4 m** com o rio a cerca de **4 m**.

Não é sensor quebrado nem escala desconhecida: **é outra grandeza** — altitude em
vez de régua.

Duas consequências, as duas gravadas em `coleta_nivel_sc.py`:

1. **Há uma quebra de série datada em 04/2026.** A série anterior de Guabiruba e a
   atual não podem ser juntadas sem reconciliar o datum.
2. **⚠️ O `LIMITE_M` de 30 m não teria pego isto.** 28,4 m passa por baixo dele —
   conferido. Quem pegou foi a lista `SUSPEITAS`, escrita à mão. Ou seja: a régua de
   plausibilidade por valor absoluto é **rede de segurança, não primeira linha**.

---

## 🟠 Ituporanga — escala oficial existe, mas é de outra estação

A SPDC/SC publica (documento de **18/10/2024**), para Ituporanga:

```
normal    < 1,40 m
atenção   > 1,40 m
alerta    > 1,90 m
emergência> 2,60 m
```

Com a ressalva de que os níveis vieram de estudos hidráulico-hidrológicos validados
junto ao município — procedência boa.

**Mas o documento amarra esses valores à estação `83250000`** — que este cadastro
**rejeitou** como régua de Ituporanga por coordenada: fica a **9,59 km** do nosso
pino e drena **1.650 km²** contra os **1.170 km²** da nossa `83145140`.

Cadastrar 1,40/1,90/2,60 contra a nossa régua seria aplicar a escala de uma estação
a outra — o erro do Salseiro outra vez.

### Por que este caso é diferente dos anteriores

Nos casos já resolvidos (Salseiro, Warnow, Botuvera-Montante) o que havia era um
**rótulo** carregando o nome do município. Aqui há uma **designação operacional**: o
estado diz que a situação de inundação de Ituporanga *se estabelece* por aquela
estação.

**As duas coisas podem ser verdadeiras ao mesmo tempo** — a estação fica a 9,59 km
*e* é a referência oficial do município. Rio não exige que a régua esteja dentro da
cidade.

### A pergunta vira outra

Se o estado opera Ituporanga pela `83250000`, **talvez a régua questionável seja a
nossa**. Escolhemos a `83145140` por proximidade do pino; o estado escolheu a outra
por decisão operacional.

**Enquanto isso não for resolvido, não se cadastra cota nenhuma ali** — nem contra
uma régua nem contra a outra. O que resolve: perguntar à Defesa Civil de SC, ou à
EPAGRI que opera a 83250000, **qual estação alimenta o aviso de Ituporanga hoje** e
qual é a cota do zero de cada uma.

---

## 🔵 Itajaí-Mirim — dois eventos que apontam a ordem de grandeza

A Defesa Civil de Brusque publicou, em **23/06/2025**: Vidal Ramos com pico
**observado** de 3,12 m às 06:10; Botuverá em 1,05 m subindo, pico **previsto**
12:15; Brusque em 2,03 m subindo, pico **previsto** 18:30.

E em **01/09/2026**: Vidal Ramos chegando a 3,87 m, Botuverá com pico de 5,85 m por
volta das 02:00, usados para projetar Brusque a 5,50 m por volta das 10:00.

Os dois sugerem **6 a 8 horas** entre pontos sucessivos.

**Não entra em `transito.json`, e a rodada acertou em não propor que entrasse:** em
23/06 só Vidal Ramos tem pico *observado* — Botuverá e Brusque são *previsão*.
Cadastrar a diferença seria transformar a estimativa da própria Defesa Civil em
medição nossa, e depois usá-la para prever o que ela já previu.

**O que fecha isso** é o `extrair_picos.py --serie-estadual`: a partir da próxima
cheia do Mirim os picos de Vidal Ramos e Botuverá saem **observados**, com horário,
da série que já vem sendo acumulada. Aí a faixa nasce de medição.

---

## ⛔ Candidatos que NÃO foram cadastrados, e por quê

| Achado | Valor | Por que não entrou |
|---|---|---|
| Timbó, atenção | 4,30 m (Rio Benedito a 4,63 m em 31/08/2026) | fonte jornalística; falta o documento municipal que diga a estação e os outros limiares |
| Itajaí DC-01, emergência | 1,70 m (atingiu 1,96 m na maré alta de julho/2026) | veio de imprensa, não da Tabela 13 do PLANCON |

Os dois são **candidatos**: valem a busca do documento oficial, não o cadastro.

---

## O que a rodada procurou e não achou

- escala oficial completa ligada inequivocamente à **DCSC-00024 de Vidal Ramos** —
  continua sendo o item mais barato da lista, e continua aberto;
- escalas completas confiáveis para **Lontras, Ascurra, Trombudo Central, Botuverá
  e Guabiruba**;
- o **endpoint JSON novo de Gaspar**, depois da reformulação do portal;
- sequência de picos **observados** (não previstos) suficiente para fechar os
  trechos do Mirim.

E manteve a recusa do Salseiro para Vidal Ramos, como o roteiro determina.

---

## O que muda no `BUSCA-EXTERNA.md`

- **Ituporanga** sai de "procurar a escala" e vira "resolver a reconciliação da
  régua" — a escala existe, o vínculo é que está em aberto.
- **Guabiruba** ganha uma armadilha nova e datada: mudou de referência vertical em
  04/2026, e o valor novo é altitude.
- Nada mais muda: Vidal Ramos, Gaspar, os picos e os demais elos seguem como estão.


---
---

# Rodada 2 — a Tabela 13 achou um conflito, não uma lacuna

## 🔴 Itajaí: as cotas já existiam, e não batem

A rodada achou a **Tabela 13** do PLANCON de Itajaí — *"Determinação das subfases
de alerta do município com base no Nível do Rio (m)"* — com 27 limiares para DC-01
a DC-09. Achado bom e fonte primária.

**Mas o repositório já tinha as onze réguas cadastradas**, citando a **Tabela 11 da
versão 17 (22/12/2025)**, com URL do PDF. Os números divergem em nove das nove:

| Régua | nosso (Tab. 11, v17) | busca (Tab. 13) | atenção mais cedo |
|---|---|---|---|
| DC-01 | 1,16 / 1,36 / 1,56 | 1,15 / 1,44 / 1,75 | busca |
| DC-02 | 1,60 / 2,00 / 2,50 | 1,60 / 2,00 / **3,30** | iguais |
| DC-03 | 1,48 / 1,85 / 2,50 | 2,28 / 2,85 / 3,30 | **nosso** |
| DC-04 | 1,50 / 1,85 / 2,25 | 1,28 / 1,60 / 2,00 | busca |
| DC-05 | 1,60 / 2,20 / 3,00 | 1,44 / 1,80 / 2,50 | busca |
| DC-06 | 1,50 / 1,85 / 2,55 | 1,28 / 1,60 / 2,00 | busca |
| DC-07 | 1,00 / 1,35 / 1,65 | 0,98 / 1,23 / 1,60 | busca |
| DC-08 | 1,80 / 2,30 / 2,89 | 2,24 / 2,80 / 3,20 | **nosso** |
| DC-09 | 1,12 / 1,32 / 1,52 | 0,98 / 1,23 / 1,60 | busca |

### Por que nenhum número foi trocado

**Não há lado seguro.** Em seis réguas a Tabela 13 avisaria antes; em duas a nossa
avisa antes. Não dá para "ficar com a mais conservadora de cada": isso montaria uma
escala que **nenhum dos dois documentos publica**, e escala remendada de duas fontes
é pior que qualquer uma das duas inteira.

### A pista que aponta o caminho — ❌ ERRADA, ver a resolução no fim

> **Esta leitura foi refutada em 08/09/2026.** Fica escrita porque o erro é o
> ensinamento: indício fraco lido como forte. O parágrafo original era:

Em **DC-02 a atenção e o alerta batem ao centavo** (1,60 e 2,00) e só a emergência
muda (2,50 contra 3,30). Coincidência exata em dois de três valores não acontece
entre tabelas de assuntos diferentes: **é a mesma tabela, revisada.**

A coincidência era real; a conclusão, não. São **edições diferentes**, e nelas a
DC-09 nem sequer é o mesmo rio. Dois de três não prova continuidade.

Então a pergunta central é a **versão**, e ela tem resposta objetiva:

1. Abrir o PDF da v17 (22/12/2025) e ver se a tabela de níveis é a **11 ou a 13**
   nela. Se for a 13, as duas leituras são da mesma tabela e **uma das transcrições
   está errada**.
2. Se a v17 numera como 11, achar a edição em que ela é a 13 e comparar as datas.
3. Confirmar com a COMPDEC de Itajaí qual edição está em vigor.

Um indício de que a v17 é a mais nova: **a Tabela 13 não contém DC-10 nem DC-11**, e
o nosso cadastro tem as duas citando a Tabela 11 da v17 — coerente com terem sido
acrescentadas depois.

Vale notar, sem concluir: os valores de DC-10 (8/9/10) e DC-11 (3/4/5) são
**redondos**, num documento que usa centímetros em todas as outras réguas.

O conflito ficou gravado **em cada uma das nove réguas** (`cotas_divergencia`) mais
um bloco `_conflito_plancon_itajai`, e há teste travando que ninguém troque metade
delas nem misture as duas escalas.

**Correção que a rodada trouxe e vale registrar:** o 1,70 m de emergência da DC-01,
que veio de imprensa na rodada 1, está descartado — nenhuma das duas leituras
oficiais traz esse valor.

---

## 🟢 Ituporanga: pergunta respondida, e o enquadramento da rodada está certo

A SPDC/SC determina que o monitoramento oficial de Ituporanga seja feito pela
**83250000** (ANA, operada pela EPAGRI), com dados via **SIG²A-SPEHC ou Gestor
PCD/ANA**, e publica atenção > 1,40 / alerta > 1,90 / emergência > 2,60 m.

A rodada propôs mudar o estado de *descartada* para **OFICIAL_PARA_ALERTA**, sem
afirmar coincidência física com nenhuma DCSC. **É exatamente a distinção certa**, e
foi assim que entrou no dado: as duas coisas são verdadeiras ao mesmo tempo — a
83250000 **não é a régua deste pino** (9,59 km, 1.650 km² contra 1.170 km²) **e é a
régua pela qual o estado declara a inundação de Ituporanga**. Rio não exige que a
régua do aviso esteja dentro da cidade.

**`cotas_m` continua vazio**, e agora por um motivo preciso: as cotas são da
83250000, e a nossa leitura vem da DCSC-00039. Gravá-las ali criaria o par
régua↔cota errado no dia em que alguém ligar uma leitura a esta cidade — o erro de
Brusque e o do Salseiro somados.

**O que destrava virou uma pergunta só:** coletar a 83250000 pelo caminho que a
própria SPDC indica. Com a leitura *dela*, a cota *dela* vale, e Ituporanga acende
com par provado — sem reconciliar coordenada nenhuma.

---

## 🌊 Maré: a parede é 31/12/2026, não 30/09

O PDF do CHM para o Porto de Itajaí **contém outubro, novembro e dezembro de 2026**.
Confirma os metadados que já tínhamos: lat 26°54,3' S, long 48°39,2' W, UTC−03:00,
78 componentes, Nível Médio 0,6 m, Carta 1841.

A observação do roteiro de que a tábua "acaba em 30/09/2026" era sobre **a tabela
importada**, não sobre a fonte. Os 92 dias que faltavam existem e estão disponíveis
— falta importar.

**2027 continua não existindo** no portal.

---

## 🟡 CEOPS: sem endereço novo, mas com uma lista valiosa

Nenhum substituto para `ceops.furb.br`. Mas a FURB documenta **17 estações de
telemetria** no Vale, e outra publicação lista as cidades: Indaial, Timbó, Taió,
Blumenau, Rio do Sul, Ibirama, Brusque, Rio do Oeste, Ituporanga, Alfredo Wagner,
**Vidal Ramos**, Pouso Redondo, Gaspar, Benedito Novo, **Rio dos Cedros** e
**Botuverá** — com atualização a cada 10 minutos.

São exatamente várias das cidades hoje vazias no nosso banco. Reforça procurar
**snapshots e arquivos** do CEOPS (Wayback Machine, acervo da FURB), não só um
endereço novo.

---

## 🔍 Vidal Ramos: a rodada abriu uma pista melhor

Sem documento ligando atenção/alerta/emergência à DCSC-00024 — continua aberto, e
continua sendo o item mais barato da lista.

Mas o acervo mostra que **CEOPS e ANA já tiveram telemetria em Vidal Ramos**, com
registro de implantação de estação da ANA em 2012. A pista que a rodada propõe é
melhor que continuar buscando "DCSC-00024": **identificar qual estação histórica
ficava na sede de Vidal Ramos e comparar a coordenada dela com −27,38547 /
−49,35812.** Se coincidir, abre-se a documentação histórica daquela estação — sem
transplantar nada do Salseiro.

---
---

# Resolução — 08/09/2026: o PDF da v17 foi lido na fonte

Jefferson trouxe o **PDF do PLANCON v17 (22/12/2025)**. Ele responde a pergunta
central da rodada 2 — *qual é a versão* — de forma direta:

- o documento tem **68 páginas** e **doze tabelas**;
- o índice vai da **Tabela 1 à Tabela 12**: **não existe Tabela 13 nele**;
- a tabela de níveis é a **Tabela 11, na página 23** — *"Determinação das subfases
  de alerta do município com base no Nível do Rio (m)"*;
- a página 22 manda, nas três subfases, *"Ver Tabela 11 com os valores de nível de
  água (m) dos Rios/Ribeirões"*.

E a conferência valor a valor: **11 de 11 batem EXATAMENTE com o que já estava
cadastrado**, sem uma divergência de centavo. As únicas diferenças são de hífen
contra travessão nos nomes.

## O que era, então, a "Tabela 13"

**Outra edição do documento.** E a diferença entre as edições não é só de número de
tabela nem de valores:

| Código | na leitura externa | na v17 (22/12/2025) |
|---|---|---|
| DC-09 | Ribeirão **Ariribá** — Clube Ariribá | Ribeirão da **Murta** – Bairro Murta |

**Rio diferente para o mesmo código de estação.** Isso é mais grave que valor
revisado: quer dizer que as estações foram **remanejadas** entre edições, e que uma
cota tirada de uma edição antiga pode estar amarrada a **outro curso d'água**. Um
número certo no lugar errado avisa a cidade errada.

## A regra que fica

> **Valor do PLANCON de Itajaí só entra com a VERSÃO do documento junto.**
> Sem versão não se sabe a que estação o número pertencia.

## O que isto custou e o que rendeu

Nenhum limiar foi alterado — nem em 07/09, quando o conflito foi registrado, nem
agora, ao fechá-lo. O conflito passou dois dias aberto **sem que nada no site
mudasse**, e é isso que estava certo: a régua que o morador lê continuou sendo a
mesma o tempo todo, e a decisão veio da fonte primária, não de escolher entre duas
transcrições.

A leitura da outra edição **fica guardada** nas nove réguas. Não é lixo: é a prova
do remanejamento da DC-09. Há teste travando que ninguém a apague.
