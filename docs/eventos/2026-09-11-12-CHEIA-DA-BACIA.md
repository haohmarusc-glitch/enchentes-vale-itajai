# Cheia de 11–12/09/2026 — a maior que este projeto já observou

Congelado em 13/09/2026 22:00Z (19:00 BRT) a partir do que a nossa própria coleta publicou:
`data/brutos/evento-2026-09-11-12-serie-recente-2200Z.json` (janela de 48 h) e
`data/brutos/evento-2026-09-11-12-ultimo-2200Z.json`.

**Por que congelar agora:** a série publicada é uma JANELA MÓVEL DE 48 H. Quando este arquivo foi
escrito ela já começava em **11/09 19:05**, com Blumenau em 6,75 m — ou seja, **a subida já tinha
saído**. Em poucas horas as próprias cristas sairiam também. O registro completo (a subida inclusive)
só existe em `data/tempo-real/2026-09.ndjson`, na VPS, que não é publicado — ver "O que falta" no fim.

## As cristas, e o que cada uma significa na régua da própria cidade

| cidade · régua | crista | quando | faixa que alcançou | agora (13/09 ~19:00) |
|---|---|---|---|---|
| **Blumenau** (DC Itajaí) | **7,87 m** | 12/09 02:15 | **ALERTA** (6,00); parou **13 cm** abaixo da emergência (8,00) | 4,34 m, ainda em atenção |
| Blumenau (AlertaBlu, horária) | 7,86 m | 12/09 05:00 | idem — as duas fontes concordam | 4,34 m |
| **Rio do Sul** (Ponte Dom Tito Buss) | **5,89 m** | 11/09 23:12 | **ALERTA** (5,50); 61 cm abaixo da inundação (6,50) | 5,31 m, **ainda em atenção** |
| **Taió** (Centro) | **6,95 m** | 12/09 03:43 | monitoramento (5,00); parou **5 cm** abaixo da atenção (7,00) | 4,46 m |
| **Brusque** (Ponte Estaiada – DCSC) | **4,62 m** | 12/09 01:35 | **atenção** (3,00); 38 cm abaixo da emergência (5,00) | 1,77 m |
| Itajaí · DC-10 Mirim, Limoeiro | 8,08 m | 12/09 03:30 | sem cotas cadastradas | 4,01 m |
| Itajaí · DC-11 Açu, Santa Regina | 4,37 m | 12/09 04:00 | sem cotas cadastradas | 3,14 m |
| Indaial (régua municipal) | 4,10 m | 12/09 22:00 | acima do **alerta** municipal (4,00) | **uma leitura só, e já com mais de 24 h** |
| Gaspar (estação 21) | 2,98 m | 13/09 08:11 | abaixo da atenção (5,00) | 2,72 m — a coleta só voltou depois do pico |

Nas 48 h da janela, **Rio do Sul não desceu da atenção em nenhuma leitura** (197 de 197 acima de
4,50) e Blumenau passou 138 leituras acima de 4,00.

## O que este evento prova, e o que não prova

**Prova que o par régua ↔ cota funciona sob carga.** Blumenau chegou a alerta com as duas fontes
independentes (Defesa Civil de Itajaí e AlertaBlu) concordando em 1 cm na crista — 7,87 contra 7,86 —,
o que é a melhor confirmação possível de que as duas leem a mesma régua.

**Não prova tempo de trânsito.** A crista de Rio do Sul (11/09 23:12) vem ANTES da de Taió
(12/09 03:43), que fica a montante. Não é a onda de Taió descendo: é chuva na bacia inteira, cada
cidade cheia pela sua própria sub-bacia. O mesmo padrão do evento de 10/09. Calcular trânsito com
estes horários daria um número invertido.

**Não fecha a magnitude.** A crista de Rio do Sul está a 18 leituras do início da janela; a subida
inteira, e qualquer pico anterior a 11/09 19:00, ficaram fora deste congelamento.

## ⚠️ ACHADO NA SÉRIE COMPLETA (13/09/2026): as duas fontes de Blumenau estão 3 h fora de fase

A régua de Blumenau (ANA 83800002) chega ao projeto por dois caminhos, e o projeto inteiro os trata
como UMA régua pelo campo `resgate_de`: a **Defesa Civil de Itajaí**, que a repassa a cada ~10 min, e o
**AlertaBlu**, de hora em hora, como resgate. Comparando as duas na série completa da cheia, ponto a
ponto, elas **não descrevem o mesmo rio no mesmo instante** — mas descrevem, com precisão quase
perfeita, se uma for deslocada 3 horas:

| deslocamento aplicado | pares | diferença média | desvio | maior diferença |
|---|---:|---:|---:|---:|
| nenhum | 56 | −0,135 m | 0,522 m | **1,80 m** |
| −1 h | 56 | −0,087 m | 0,347 m | 1,25 m |
| −2 h | 56 | −0,054 m | 0,188 m | 0,66 m |
| **−3 h** | 54 | **−0,004 m** | **0,015 m** | **0,05 m** |
| −4 h | 53 | +0,044 m | 0,153 m | 0,55 m |

Um desvio de 1,5 cm entre 54 pares, nos três dias (10, 11 e 12/09, medido em cada um separadamente),
não é coincidência: é a mesma régua, com os relógios separados por exatamente 3 horas.

**Qual dos dois está certo.** O do AlertaBlu está ancorado três vezes: (1) o `horaLeitura` do bruto é
UTC de verdade — na coleta das 23:45Z de 10/09 o ponto mais novo era 23:00Z, 45 min antes; se o "Z"
fosse rótulo falso sobre hora local, o ponto mais novo estaria 3 h no futuro, o que é impossível;
(2) o `coleta_alertablu.py` converte, e esse ponto (23:00Z = 4,23 m) está na nossa série como
**20:00 = 4,23 m**, como manda o contrato do projeto; (3) a página oficial da Defesa Civil de Blumenau
marcava 4,23 m caindo por volta das 20:40 daquele dia.

**Logo é o repasse da Defesa Civil de Itajaí que carrega `medido_em` ~3 h ATRÁS do instante real:** o
valor que ele rotula 17:05 aconteceu por volta das 20:05.

**E é específico de Blumenau, não do coletor.** Brusque vem da MESMA página, pelo MESMO coletor, e o
relógio dela bate no minuto: a tela aberta às 19:35 de 10/09 mostrava 2,19 m, e a nossa série tem
2,19 m às 19:35. Só a linha de Blumenau está fora de fase.

### O que isso corrige neste documento

**A crista de Blumenau provavelmente foi por volta das 05:15 de 12/09, não às 02:15.** O valor não
muda (7,87 m); o horário, sim. O próprio AlertaBlu põe a crista dele às **05:00** com 7,86 m — que é
exatamente 02:00 + 3 h. A tabela lá em cima traz o horário como veio do repasse; o horário real está
3 h à frente até isto ser resolvido.

### O que isso quebra fora daqui

- **Idade da leitura.** O site decide pintar ou não pela idade do `medido_em`. Com 3 h de atraso no
  rótulo, a leitura primária de Blumenau nasce "velha" e a cidade passa a depender do resgate horário
  do AlertaBlu — que é o que se via em 10/09, quando a primária aparecia parada às 16:35 e o número
  que pintava a tela vinha do AlertaBlu.
- **Qualquer tempo de trânsito que use Blumenau** sai 3 h errado, e Blumenau é o meio do Açu.
- **Cristas já registradas** com o relógio do repasse (esta e a de 10/09) carregam o mesmo desvio.

### ✅ CONFIRMADO em 13/09/2026, 20:22 BRT — o carimbo errado nasce fora do projeto

> ℹ️ A direção (quem está certo) ficou em dúvida entre 21:30 de 13/09 e a madrugada de 14/09, por
> causa da crista de Ilhota (seção "E12" abaixo). Foi fechada a favor do AlertaBlu por prova
> independente da física. O que segue continua válido.

As duas fontes lidas no mesmo minuto, na VPS:

```
2026-09-13 23:22 UTC                       (= 20:22 em Brasília)
AlertaBlu bruto: {'nivel': 4.29, 'horaLeitura': '2026-09-13T23:00:00Z'}
  4.29 m  2026-09-13T17:15:00  Blumenau
  4.01 m  2026-09-13T20:10:00  DC-10 Rio Itajaí-Mirim – Bairro Limoeiro
```

Três fatos em quatro linhas:

1. **Mesmo valor, dois carimbos.** 4,29 m nas duas fontes. O AlertaBlu diz `23:00Z`, que é 20:00 de
   Brasília — 22 minutos antes da coleta. O repasse diz **17:15**, três horas atrás.
2. **Não é o nosso coletor.** A linha do DC-10 saiu da MESMA página, no MESMO `parse()`, com 12 minutos
   de idade. Se o `coleta_itajai.py` subtraísse 3 h de alguma coisa, o DC-10 teria saído às 17:10.
   Só a linha de Blumenau está fora de fase — como Brusque já havia mostrado em 10/09.
3. **O valor está certo; o rótulo é que mente.** 4,29 m é o rio agora, não uma leitura velha de 3 h.

**Medida fina do deslocamento.** Interpolando a série do AlertaBlu no instante de cada um dos 230
pontos do repasse na cheia (10 a 12/09), e somando um deslocamento ao rótulo do repasse:

| deslocamento somado ao repasse | pares | diferença média | desvio | maior |
|---|---:|---:|---:|---:|
| nenhum | 230 | +0,160 m | 0,550 m | 1,75 m |
| +2 h 00 | 222 | +0,053 m | 0,179 m | 0,62 m |
| +2 h 45 | 220 | +0,012 m | 0,045 m | 0,17 m |
| **+3 h 00** | 218 | **−0,001 m** | **0,010 m** | **0,06 m** |
| +3 h 15 | 218 | −0,014 m | 0,045 m | 0,17 m |
| +4 h 00 | 214 | −0,052 m | 0,168 m | 0,62 m |

O mínimo é agudo e cai **exatamente em 3 h 00**: 1 cm de desvio em 218 pares, contra 55 cm sem
deslocamento. Não é "mais ou menos três horas" — são três horas redondas, o que tem a cara de uma
conversão de fuso aplicada duas vezes (a hora UTC do AlertaBlu lida como se já fosse local e
convertida outra vez) na integração que leva o dado de Blumenau para a página de Itajaí.

**Consequência imediata para este documento:** a crista de Blumenau nesta cheia foi por volta das
**05:00 de 12/09** (7,86 m, pelo relógio do AlertaBlu), não às 02:15. A tabela no alto traz o horário
como veio do repasse.

**Conserto.** Não é código nosso: o pedido de correção vai à Defesa Civil de Itajaí (ofício **C23**,
em `docs/oficios-prontos.md`). Enquanto não for corrigido, vale a regra: **nenhum horário de crista de
Blumenau sai da linha repassada** — sai do AlertaBlu. O valor do repasse continua bom; o relógio, não.

### E12 — a direção do desvio, fechada em 14/09/2026

**O que pôs em dúvida.** Com as séries de 10 min da rede estadual (relógio DCSC = Brasília, provado),
as cristas de 12/09 saíram Ascurra 00:00 → Indaial 01:00 → Ilhota 05:10. Pelo AlertaBlu, Blumenau
crista às 05:00–06:00, dez minutos antes de Ilhota, 45 km rio abaixo; pelo repasse, 02:15, em ordem.

**Por que a física não decidiu.** Correlação da curva inteira (11/09 06:00 → 12/09 22:00):

| trecho | lag pelo repasse | lag pelo AlertaBlu | r |
|---|---:|---:|---:|
| Ascurra → Indaial (~15 km, controle) | +1,17 h | — | 0,999 |
| Indaial → Blumenau (~25–30 km) | **0,00 h** | **+3,00 h** | 0,989 |
| Blumenau → Ilhota (~40 km) | +5,83 h | +2,00 h | 0,966 |
| Blumenau → Ilhota-Arraial | +0,67 h | −2,17 h | 0,992 |

0,00 h em 25–30 km é fisicamente impossível para a mesma onda; mas −2,17 h para Ilhota-Arraial
também. A saída é que **Ilhota e Arraial sobem cedo por chuva local** (25 % da subida às 14:15 e
14:38, uma hora depois da pancada das 13–14 h; Arraial é um ribeirão de 0,6→4 m) e não são âncora
de roteamento. Restava Indaial→Blumenau: 3,00 h cabe na celeridade medida em Ascurra→Indaial
(1,17 h em ~15 km → ~2–2,3 h em 25–30 km); 0,00 h não cabe. Forte, mas com ±1 h de folga contra
uma pergunta de 3 h.

**O que decidiu: a hora de parede.** A Defesa Civil de Blumenau emite boletim em hora de emissão,
e a imprensa escreve em tempo real. Da noite de 11/09:

| hora de parede | quem | o que disse | AlertaBlu (rótulo) | repasse (rótulo) |
|---|---|---|---:|---:|
| 20h | boletim da Defesa Civil de Blumenau | rio em **5,78 m**; pico de 9 m às 2h | 20:00 = **5,78** | 20:05 = 7,07 |
| ~21h | O Blumenauense | "chegou a **6,32 m** às 21h"; 18→19h +62 cm, 19→20h +59, 20→21h +54 | 21:00 = **6,32**; +62/+59/+54 | 21:05 = 7,31 |
| 22h28 | ND Mais | "**6,73 m** às 22h, +41 cm em 1 h"; nova projeção: 8 m às 4h | 22:00 = **6,73**, +41 | 22:05 = 7,50, ~+10/h |
| 0h30 | secretário Menestrina | "taxa de subida caiu para **~20 cm/h**, ~15 na hora seguinte" | 23→00: **24**; 00→01: 18 | 22:45→00:35: 10; 00:05→00:35: 4 |
| manhã | Jornal Razão | pico 7,86 às 5h e 6h; 7,82 às 7h; 7,73 às 8h | 05:00 = 7,86 … 08:00 = 7,73 | crista 02:15, 05:00 já em 7,69 |

Cada número citado bate **ao centímetro** com o rótulo do AlertaBlu na mesma hora de parede — e
os incrementos horários também. Para o repasse ser o relógio certo, a Defesa Civil de Blumenau, que
lê a própria régua na Ponte Adolfo Konder em frente ao prédio, teria publicado 5,78 m com o rio a
7,07 m, e o secretário teria falado em 20 cm/h com o rio praticamente parado. Não é crível.

Fontes: [ND Mais — pode chegar a 9 m](https://ndmais.com.br/tempo/rio-itajai-acu-pode-chegar-a-9-metros-e-provocar-enchente-em-blumenau/),
[ND Mais — nova projeção após subir 1,5 m em 3 h](https://ndmais.com.br/tempo/nova-projecao-mantem-blumenau-em-alerta-maximo-para-risco-de-enchente-apos-rio-subir-15-metro-em-apenas-tres-horas/),
[ND Mais — sobe 2,7 m e estabiliza](https://ndmais.com.br/tempo/rio-itajai-acu-sobe-quase-27-metros-durante-a-madrugada-mas-estabiliza-antes-da-cota-de-enchente-em-blumenau/),
[O Blumenauense — 6,32 m às 21h](https://oblumenauense.com.br/rio-itajai-acu-chegou-a-632-metros-as-21h-desta-sexta-feira-11-09-em-blumenau),
[O Blumenauense — nova projeção perto de 8 m](https://oblumenauense.com.br/nova-projecao-indica-rio-itajai-acu-proximo-de-8-metros-e-cenario-sem-enchente-em-blumenau),
[Jornal Razão — estabiliza e descarta enchente](https://jornalrazao.com/meio-ambiente/apos-noite-de-alerta-nivel-do-rio-itajai-acu-estabiliza-volta-a-baixar-e-defesa-civil-descarta-enchente-em-blumenau),
[Mesorregional](https://www.mesorregional.com.br/defesa-civil-descarta-enchente-em-blumenau-apos-reducao-na-elevacao-do-rio/).
Lidas por trechos de busca em 14/09/2026 (os sites não abrem deste ambiente); vale conferir a hora
de publicação na própria página.

**Conclusão.** O relógio do AlertaBlu é o real. O repasse da Defesa Civil de Itajaí publica Blumenau
com carimbo 3 h atrás; o valor é bom. A crista de Blumenau foi **05:00–06:00 de 12/09, 7,86–7,87 m**.
Trava no código: `extrair_picos.RELOGIO_DEFASADO` (E11). Ofício C23 liberado.

## Velocidade de subida, em cm/h (calculada em 23/09/2026)

Pedido do Jefferson em 23/09. `scripts/subida_cheia.py` lê o ndjson desta cheia e calcula, por
régua: a **base** (menor leitura antes do meio-dia de 10/09), a **crista**, a **subida total** e a
**maior subida em 1 h e em 3 h** — para cada leitura, o nível exatamente N horas depois vem por
interpolação linear entre as leituras vizinhas (nunca por cima de buraco maior que 3 h). É a taxa
que alguém lendo a régua de hora em hora teria visto. Saltos de ≥ 60 cm em ≤ 20 min ficam
**listados**, não apagados. 13 testes (`teste_subida_cheia.py`) travam estes números.

**Réguas de rio** (cada uma na própria régua; cm/h é diferença na mesma régua, comparável entre
cidades só como descrição do evento):

| régua | base | crista | subida | **maior 1 h** | quando começou | maior 3 h |
|---|---|---|---|---|---|---|
| Taió, Centro | 2,40 | 6,95 (12/09 03:43) | 455 cm | **50 cm/h** | 11/09 14:59 | 47 cm/h |
| Rio do Sul, Ponte Dom Tito Buss | 2,96 | 5,89 (11/09 23:12) | 293 cm | **35 cm/h** | 11/09 14:27 | 28 cm/h |
| Blumenau (AlertaBlu, horária) | 2,38 | 7,86 (12/09 05:00) | 548 cm | **62 cm/h** | 11/09 18:00 | 58 cm/h |
| Blumenau (repasse DC Itajaí, carimbo 3 h atrasado) | 2,64 | 7,87 (12/09 02:15) | 523 cm | 63 cm/h | 11/09 15:45 (= ~18:45 real) | 57 cm/h |
| Vidal Ramos (Asthon) | 2,43 | 3,39 (11/09 14:37) | 96 cm | **56 cm/h** | 11/09 12:56 | 24 cm/h |
| Brusque, Ponte Estaiada | 1,26 | 4,62 (12/09 01:35) | 336 cm | **62 cm/h** | 11/09 13:15 | 42 cm/h |
| Itajaí · DC-10 Mirim, Limoeiro | 2,98 | 8,08 (12/09 03:30) | 510 cm | **95 cm/h** | 11/09 14:00 | 69 cm/h |
| Itajaí · DC-11 Açu, Santa Regina | 2,24 | 4,37 (12/09 04:00) | 213 cm | 46 cm/h | 11/09 13:30 | 28 cm/h |

O que a tabela diz:

- **A hora mais rápida foi a mesma em quase toda a bacia: o começo da tarde de 11/09**, entre
  13h e 15h (Vidal Ramos, Brusque, Taió, Rio do Sul, DC-10, DC-11). Chuva na bacia inteira ao
  mesmo tempo, não uma onda descendo.
- **Blumenau subiu mais rápido às 18h**, três a quatro horas depois das cabeceiras — o que se
  espera de quem recebe a água de Rio do Sul (7–10 h de trânsito) somada à chuva local. As duas
  fontes de Blumenau dão a mesma taxa (62–63 cm/h); a diferença de horário é o carimbo atrasado
  do repasse, já diagnosticado acima (E12).
- **Rio do Sul foi a régua mais lenta** (35 cm/h) e a primeira a cristar (23h12 de 11/09), com
  um ramo de subida longo: 293 cm em ~9 h. Taió, a montante, subiu mais rápido e cristou 4 h e
  meia depois — a régua de Taió mede o Itajaí do Oeste, que não passa por Rio do Sul antes.
- **DC-10 (Limoeiro) é a maior taxa da bacia, 95 cm/h**, e a maior subida absoluta (5,10 m). É a
  régua do Mirim em Itajaí, sem cotas cadastradas: o número descreve o evento, não diz o que
  ele significa para a rua.
- Vidal Ramos cristou às 14h37 de 11/09, **11 h antes de Brusque** (01h35 de 12/09) — coerente
  com a antecedência "até ~14 h" medida na ANA (`docs/HIDROWEB-MIRIM-2026-09-22.md`). A régua é
  a Asthon da cidade, não a Salseiro.

**Réguas de estuário e ribeirões de Itajaí** (DC-01 a DC-09): a maré cruza a cota sem enchente
nenhuma, e aqui a "subida" **mistura maré e cheia**. Os números ficam pelo registro, com essa
etiqueta, e **não** são velocidade de cheia:

| régua | crista | maior 1 h | observação |
|---|---|---|---|
| DC-01 Açu, ICMBio | 2,00 (12/09 03:01) | 58 cm/h (11/09 23:01) | |
| DC-02 Açu, Praça Celso Pereira | 1,90 (12/09 02:31) | 86 cm/h (11/09 14:31) | **salto de 0,95 → 1,57 m em ≤ 20 min às 15:01 de 11/09**: leitura suspeita, e o 86 cm/h é dela |
| DC-03 Mirim, canal, Captação SEMASA | 1,97 (12/09 03:30) | 49 cm/h | |
| DC-04 Mirim, Vitalmar | 2,18 (12/09 03:11) | 43 cm/h | |
| DC-05 Mirim, curso antigo | 2,42 (12/09 04:41) | 16 cm/h | |
| DC-06 Mirim, Itamirim | 1,48 (12/09 02:40) | 36 cm/h | |
| DC-07 Ribeirão da Murta, Portal | 1,08 (**10/09 05:40**) | 45 cm/h | a "crista" é maré da véspera, não a cheia |
| DC-08 Canhanduba | 2,41 (11/09 23:00) | 43 cm/h | |
| DC-09 Murta, Ponte Lidia Puel | 1,93 (12/09 03:30) | 41 cm/h | |

Indaial e Gaspar têm uma leitura só na janela e ficam de fora. Nada disto entra em
`enchentes.json` nem em `transito.json`: é descrição de um evento, e as cristas continuam sendo a
decisão pendente do item 2 abaixo.

**Sobre a branch `vps/cheia-2026-09-11-12`** (23/09): o ndjson que ela adiciona é **byte a byte o
mesmo** que já está no `main` desde 13/09 (`c8e4bfc`), e a branch nasceu de um `main` antigo —
mesclá-la apagaria 74 arquivos de dados (126 mil linhas). Não há PR a abrir; a branch pode ser
apagada.

## O que falta

1. ~~**Extrair o evento completo do ndjson da VPS**~~ — feito em 13/09/2026: 4.028 leituras de 19
   réguas estão em `data/brutos/cheia-2026-09-11-12.ndjson`.
2. **Decidir se as cristas entram em `enchentes.json`.** São picos de 2026 medidos pela nossa coleta,
   com régua nomeada nos dois lados — o material mais limpo que o projeto tem. Decisão do Jefferson.
3. **Conferir se o aviso saiu.** Blumenau em alerta é exatamente o caso que o bot existe para cobrir;
   `data/tempo-real/estado_alertas.json` na VPS diz o que ele fez.
4. ~~**Resolver o desvio de 3 h de Blumenau**~~ — *diagnosticado e confirmado* em 13/09 (seção acima):
   o carimbo errado vem da página da Defesa Civil de Itajaí, não do projeto. Falta **enviar o ofício
   C15** e, no código, impedir que o extrator de picos tire horário de crista da linha repassada.
5. **Indaial**: a leitura municipal de 12/09 22:00 (4,10 m, acima do alerta municipal) é a única que
   chegou. Conferir se a coleta parou ou se a fonte publica esparso.
