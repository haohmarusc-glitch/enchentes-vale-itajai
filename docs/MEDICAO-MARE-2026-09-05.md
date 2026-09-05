# A trava de maré das nove réguas de Itajaí, medida — 05/09/2026

Rodado na VPS, sobre o ndjson mestre: **17 estações, 6 dias**. É a primeira vez que a trava das nove
réguas de estuário é conferida contra série, e não contra julgamento.

O cadastro trava DC-01 a DC-09 com **o mesmo texto**:

> *"Régua no estuário, com oscilação de maré maior que a distância até a cota."*

A medição diz que essa frase é literalmente verdadeira em **duas** delas.

---

## O que decide, e por que são duas perguntas

A trava só se justifica quando **as duas** coisas valem ao mesmo tempo:

1. a régua **cruza a cota sozinha** — a oscilação diária é maior que a folga até a cota; e
2. essa oscilação **é maré** — pelo menos 45% dela está no período de 12,4 h (a componente M2).

Uma sem a outra não sustenta a trava. Maré que não alcança a cota não dispara nada; oscilação que
alcança mas é do RIO é exatamente o que o aviso existe para pegar.

| régua | oscila/dia | folga | cruza sozinha? | maré (M2) | trava se justifica? |
|---|---|---|---|---|---|
| **DC-01** ICMBio/CEPSUL | 0,99 m | **0,16 m** | **sim** | **45% — MARÉ** | ✅ **sim** |
| **DC-04** Vitalmar | 0,82 m | 0,51 m | **sim** | **51% — MARÉ** | ✅ **sim** |
| DC-02 Praça Celso Pereira | 0,07 m | 0,49 m | não | 23% | ✖ não |
| DC-03 SEMASA | 0,89 m | 0,93 m | não | 45% — maré | ✖ a maré não alcança |
| DC-05 curso antigo | 0,30 m | 0,22 m | sim | 8% | ✖ **não é maré** |
| DC-06 Itamirim | 0,66 m | 0,81 m | não | 51% — maré | ✖ a maré não alcança |
| DC-07 Rib. Murta / Portal | 0,09 m | 0,64 m | não | 11% | ✖ não |
| DC-08 Rib. Canhanduba | 0,11 m | 0,67 m | não | 5% | ✖ não |
| DC-09 Rib. Murta / Ponte | 0,54 m | **0,09 m** | sim | 42% | ✖ **por 3 pontos** |

**DC-01 e DC-04 ficam travadas com razão.** As duas cruzam a cota sozinhas e a oscilação é de maré.
A DC-01 cruzou **26 vezes em 5 dias** sem enchente, com 16 cm de folga.

---

## ⚠️ "A medição não confirma a trava" NÃO quer dizer "destravar"

Esta é a leitura que o número sozinho não dá, e é o ponto principal deste documento. As sete réguas em
que a medição discorda do cadastro **não são um grupo**. São três situações, e destravá-las juntas
repetiria o erro de travá-las juntas.

### 1. Destravar é seguro — a oscilação é pequena e as travessias são curtas
**DC-02** e **DC-07**. Oscilam muito abaixo da folga (0,07 contra 0,49; 0,09 contra 0,64), não são maré,
e quando cruzam ficam pouco tempo acima (1,1 h e 6,2 h). É aviso que acende e apaga — que é o que um
aviso deve fazer.

### 2. A maré é real, mas não alcança a cota
**DC-03** e **DC-06**. A assinatura é de maré (45% e 51%), mas a oscilação é **menor que a folga** —
0,89 contra 0,93 e 0,66 contra 0,81 — e a DC-06 não cruzou nenhuma vez em 6 dias. O motivo cadastrado
("oscilação de maré maior que a distância até a cota") é falso para as duas: a maré existe e não chega lá.

### 3. ⛔ A cota está baixa demais — destravar acende um aviso que nunca apaga
**DC-05**, **DC-08** e **DC-09**. Aqui a discordância com o cadastro é verdadeira (não é maré, ou é
por pouco), mas destravar seria pior, e por outro motivo:

| régua | tempo ACIMA da cota por travessia | máximo |
|---|---|---|
| DC-05 | **46,8 h** | 46,8 h |
| DC-08 | **25,5 h** | 25,5 h |
| DC-09 | 3,1 h | **47,5 h** |

Uma régua que fica **dois dias seguidos** acima da cota de atenção não está avisando de nada — está
ligada. É o mesmo defeito já documentado em Rio do Sul, e **amarelo que nunca apaga é amarelo que
ninguém mais vê**. O que essas três pedem não é destravar: é **conferir a cota com a COMPDEC**.

A DC-09 é o caso mais delicado dos nove: **9 cm de folga**, 42% de maré (três pontos abaixo do limiar) e
uma travessia que durou 47,5 h. Ela falha nos dois critérios por muito pouco, nas duas direções.

---

## ⛔ Rio do Sul: o aviso já está ligado e não desliga

Fora das nove, e mais urgente que todas:

```
Rio do Sul Estação MKS
  típico 5,52 m · cota 4,50 · folga −1,02 m
  1 travessia em 6 dias · fica acima da cota 106,3 h por travessia
  hoje: DISPARA
```

A folga é **negativa**: o rio nunca desce até a cota. A única "travessia" da série durou **106 horas** —
os 6 dias inteiros. A cabeceira do Açu está permanentemente em alerta no mapa, hoje. Isso não é ajuste
de trava: a cota de 4,50 m está abaixo do leito normal, e a pergunta vai para a **Defesa Civil de Rio do
Sul**, não para o cadastro.

---

## O que a medição diz sobre as duas que HOJE disparam

| régua | estado hoje | medição |
|---|---|---|
| **DC-11** Santa Regina | dispara (`alerta_automatico: null`) | **não é maré** (40%) — mas oscila 0,85 m contra 0,25 m de folga, com 7 travessias em 3 dos 6 dias, uma delas de 45,5 h |
| **DC-10** Limoeiro | dispara | não é maré (23%), folga 3,45 m, 1 travessia — comportamento saudável |

A DC-11 corrige uma medição anterior: a correlação com as réguas de maré sugeria que ela fosse de maré,
e o teste de frequência diz que **não é**. O método de frequência é o melhor dos dois — foi construído
justamente para eliminar o falso positivo que a correlação dava (ela apontou "MARÉ" em Taió, a 200 km do
mar). Mas ela ainda cruza a cota com frequência, e uma travessia durou quase dois dias: é candidata ao
mesmo problema de cota das outras três, não a uma trava de maré.

---

## Recomendação

**Nada foi alterado.** Mudar quem dispara aviso é decisão de quem mantém o projeto. O que a medição
sustenta, em ordem de segurança:

| ação | réguas | por quê |
|---|---|---|
| **manter travada** | DC-01, DC-04 | cruzam sozinhas **e** a oscilação é maré |
| **destravar com segurança** | DC-02, DC-07 | oscilação bem abaixo da folga, não é maré, travessias curtas |
| **destravar, corrigindo o motivo** | DC-03, DC-06 | são maré, mas a maré não alcança a cota |
| **NÃO destravar — conferir a cota** | DC-05, DC-08, DC-09 | ficam 25 a 47 h acima da cota por travessia |
| **conferir a cota, urgente** | Rio do Sul | folga −1,02 m; 106 h acima; disparando agora |

E, independente da trava: o `motivo_sem_alerta` das nove precisa deixar de ser **o mesmo texto**. Ele
afirma uma coisa específica — "oscilação de maré maior que a distância até a cota" — que a série
confirma em duas réguas e desmente em sete.

## Como refazer

```bash
cd /opt/enchentes-vale-itajai && git pull
python3 scripts/medir_mare.py            # todas, com veredito
python3 scripts/medir_mare.py --json     # para colar
```

O script **sugere e não decide**, e diz isso na última linha da própria saída.
