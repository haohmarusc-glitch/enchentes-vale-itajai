# Rio do Sul alto não é alarme — é esvaziamento de barragem — 05/09/2026

O nível sustentado de Rio do Sul depois da cheia de 01/09 não é cota errada nem defeito de coleta. É o
sistema de contenção **esvaziando de propósito**, para recuperar capacidade antes da próxima chuva.

## O que fecha o argumento

Não é a leitura de um dia. São dois registros independentes, feitos com dois dias de distância, sobre a
mesma barragem:

| fonte | quando | montante da Barragem Oeste | comportas |
|---|---|---|---|
| `docs/TAIO-E-BARRAGEM-OESTE.md` (registro nosso, API Uniparking) | 03/09 20:41 | **17,2 m** | 7 de 7 abertas |
| leitura de 05/09 (API Asthon, `dams`) | 05/09 08:19 | **15,00 m** | 7 de 7 abertas |
| **coleta própria** (`coleta_barragens.py`, corpo capturado) | **05/09 14:05** | **14,66 m** | **7 de 7 abertas** |

**O reservatório caiu 2,54 m em 41 horas com todas as comportas abertas** — e a terceira leitura, já
pela nossa própria coleta, mostra que continuava caindo. Isso é esvaziamento controlado, e nenhuma
outra explicação cabe nos três pontos.

Na Barragem Sul, no mesmo instante: **22,58 m, 5 de 5 abertas, 35,5% da capacidade**. As doze
comportas do sistema abertas, os dois reservatórios abaixo de 36%.

No sistema inteiro, em 05/09: **12 de 12 comportas abertas** — 7 de 7 na Oeste (Taió, 34% da
capacidade) e 5 de 5 na Sul (Ituporanga, 38%).

## ⭐ A lacuna que isto fecha

`docs/AUDITORIA-JICA-2011.md` registrava, item 3: *"'7 comportas = 7 condutos' bate. **Não implica que o
site da Asthon exponha estado de cada comporta — isso continua lacuna.**"*

Ela está fechada. O endpoint

```
GET https://public.asthon.com.br/public/dams?city_id=4214805
```

traz `comportas[].aberta` (por comporta), `montante_m`, `jusante_m`, `percent_use` e `vertido`, para as
**duas** barragens — sem autenticação. A API de Taió (Uniparking) já dava `comportasAbertas` como texto
`"N de 7"` só para a Oeste; o `dams` dá granularidade por comporta e cobre o sistema todo.

O JICA aponta que a previsão de Rio do Sul "não é apropriada para uso prático" porque a DEINFRA não
informa a **vazão** de saída. Ela continua não informando — mas o **número de comportas abertas** é o
proxy operacional mais próximo, e está publicado.

## O que o site deveria mostrar, e não mostra

Este é o erro real, e não é a cota:

| estado | leitura |
|---|---|
| comportas **fechadas** + rio subindo | a barragem está **segurando** — o pior ainda pode vir |
| comportas **abertas** + rio estável ou caindo | **esvaziamento controlado** — o pico já passou |

O mesmo 5,4 m significa coisas opostas nos dois casos. Hoje o site mostra só o número.

## ⚠️ A cota de alerta de Rio do Sul parece ser MÓVEL — e isto precisa de confirmação oficial

Duas notícias, com 16 dias de diferença, dizem que a Defesa Civil de Rio do Sul **ajusta a faixa de
alerta por evento**, conforme a análise hidrológica e pluviométrica:

| data | faixa de alerta publicada |
|---|---|
| 15/08 | *"reduziu a cota de alerta… a nova faixa fica entre **5,50 e 6,50 m**"* |
| 31/08 | *"a cota de alerta estipulada pela Defesa Civil fica entre **6,5 e 7,5 m**"* |

**Confiança: `media` — é imprensa, não documento oficial.** Não foi gravado em `estacoes.json`, e não
deve ser até confirmar com a COMPDEC. Mas a consequência, se confirmada, é grande: o
`band_thresholds` da API (4,50 / 5,50 / 6,50) seria **cadastro**, não a faixa operacional do dia, e o
site não deveria dizer "ALERTA" com base nele para Rio do Sul.

Escala reconstruída, com a origem de cada número à vista:

| nível | o que é | fonte |
|---|---|---|
| 4,50 m | atenção | cadastro fixo da API Asthon |
| 5,5–6,5 **ou** 6,5–7,5 | faixa de alerta **móvel**, por evento | imprensa (`media`) — **a confirmar** |
| 7,00 m | *"marca considerada oficialmente como situação de enchente no município"* | imprensa (`media`) |
| 8,00 m | nível a partir do qual avisam quem mora em cota abaixo | imprensa (`media`) |

## ✅ O coletor existe — `scripts/coleta_barragens.py` (05/09/2026)

O corpo foi capturado na VPS e o leitor foi escrito **contra ele**, não contra suposição. E o corpo
real trouxe uma armadilha que nenhuma descrição tinha adiantado.

### ⚠️ `montante_m` é ALTITUDE, não régua

```
Barragem Oeste:  montante_m 353,66  ·  gauge_zero_m 339  ·  nivel_m 14,66
Barragem Sul:    montante_m 392,58  ·  gauge_zero_m 370  ·  nivel_m 22,58
```

A relação é **exata nas duas**: `nivel_m = montante_m − gauge_zero_m`. Ou seja, `montante_m` é metros
**acima do nível do mar**, e a leitura da régua da barragem é `nivel_m`.

E o cuidado maior é com a **palavra**: `docs/TAIO-E-BARRAGEM-OESTE.md` chama de *"montante"* o que esta
API chama de `nivel_m` — registrou **17,2 m** em 03/09, que nesta API seria `montante_m` ≈ 356,2.
A mesma palavra, duas grandezas, em duas fontes nossas. Comparar `montante_m` com régua de rio erra por
centenas de metros, e por isso o coletor grava os dois com nomes que não se confundem:
`altitude_montante_m` e `nivel_na_regua_da_barragem_m`.

### As outras três armadilhas, todas com teste

| armadilha | o que acontece se passar |
|---|---|
| `measured_at` vem em **UTC com `Z`** | gravado como local, envelhece a leitura em 3 h na tela |
| `percent_use` **não** é sempre `capacidade_atual/capacidade_maxima` — bate na Oeste, diverge 0,057 pp na Sul | recalcular inventa um número que a fonte não afirma; o coletor usa o publicado e registra a divergência |
| `vertido` vem **0 nas duas** com 12 comportas abertas | não é a vazão de saída; gravado cru, com o significado marcado como desconhecido |

O `comportas_abertas` da fonte é um campo derivado: o coletor **conta pela lista** e avisa se os dois
discordarem. Comporta sem o campo `aberta` conta como **fechada** — "não sei" não pode virar
"esvaziando", que é a direção que engana.

## O que falta fazer, em ordem

1. ~~Coletar o `dams`.~~ **Feito.** Falta pôr no cron e publicar junto do resto do tempo real.
2. **Mostrar o estado do sistema junto do nível** de Rio do Sul e Taió: quantas comportas abertas, e o
   percentual de uso dos reservatórios.
3. **Confirmar com a COMPDEC de Rio do Sul** se a faixa de alerta é mesmo definida por evento. Isso muda
   o que o site pode afirmar.
4. **Suprimir cor de alerta durante esvaziamento declarado** — comportas abertas e nível estável ou
   caindo. ⚠️ **Não implementado, e não deve ser sem decisão de quem mantém o projeto:** suprimir alarme
   é a direção perigosa. A regra precisa da condição "estável ou caindo" e de um teste que prove que
   comportas abertas **com o rio subindo** continuam alarmando.

## O que este documento corrige

`docs/MEDICAO-MARE-2026-09-05.md` afirmava que a cota de 4,50 m está "abaixo do leito normal" e que a
pergunta ia para a Defesa Civil. Errado nas duas pontas, e a refutação estava no próprio parágrafo: o
relatório diz **"1 travessia"**, e uma travessia é o rio cruzando de baixo para cima — com a cota abaixo
do leito seriam **zero**. A janela de 6 dias caiu inteira dentro do evento de 01/09 (pico 6,78 m) e do
esvaziamento que veio depois.

**Onde fica o nível normal de Rio do Sul continua sem resposta.** As duas medições feitas até aqui —
6 dias e, antes, 48 h — caem na mesma janela de evento. Isso se responde sozinho rodando o
`medir_mare.py` depois de um período seco, porque o ndjson mestre acumula.
