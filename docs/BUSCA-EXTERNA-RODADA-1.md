# Busca externa, rodada 1 — o que voltou em 07/09/2026

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
