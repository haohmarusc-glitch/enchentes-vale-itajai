# Rio do Sul alto não é alarme — é esvaziamento de barragem — 05/09/2026

O nível sustentado de Rio do Sul depois da cheia de 01/09 não é cota errada nem defeito de coleta. É o
sistema de contenção **esvaziando de propósito**, para recuperar capacidade antes da próxima chuva.

## O que fecha o argumento

Não é a leitura de um dia. São dois registros independentes, feitos com dois dias de distância, sobre a
mesma barragem:

| fonte | quando | montante da Barragem Oeste | comportas |
|---|---|---|---|
| `docs/TAIO-E-BARRAGEM-OESTE.md` (registro nosso, API Uniparking) | 03/09 20:41 | **17,2 m** | 7 de 7 abertas |
| leitura de 05/09 (API Asthon, endpoint `dams`) | 05/09 08:19 | **15,00 m** | 7 de 7 abertas |

**O reservatório caiu 2,2 m em 36 horas com todas as comportas abertas.** Isso é esvaziamento
controlado, e nenhuma outra explicação cabe nos dois pontos.

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

## O que fazer, em ordem

1. **Coletar o `dams` da Asthon.** Não foi escrito aqui porque `public.asthon.com.br` não responde deste
   ambiente (`connect_rejected`), e escrever o leitor de um JSON que não se viu é inventar a estrutura
   dele — o mesmo motivo que segurou o leitor de Brusque. Capturar de dentro da região ou da VPS, e o
   coletor sai contra o corpo real.
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
