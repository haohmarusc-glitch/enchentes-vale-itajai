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

> ⚠️ **Reaberto às 21:30 do mesmo dia, só quanto à DIREÇÃO.** O que segue prova (a) que o desvio é
> de 3 h 00 exatas e (b) que não é o nosso coletor. A conclusão de que o relógio errado é o de Itajaí
> ganhou um contra-indício com as séries da rede estadual (relógio DCSC, Brasília provado): Ascurra
> cristou 00:00, Indaial 01:00 e **Ilhota 05:10** de 12/09. Pelo AlertaBlu, Blumenau crista às 05:00
> — dez minutos antes de Ilhota, 45 km rio abaixo. Pelo repasse, 02:15, em ordem. A crista de Blumenau
> é um platô de 2 h, então o máximo é frágil dos dois lados; decide-se pela forma das curvas
> (item E12 do checklist). **Até lá, o ofício C23 não sai.**

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
