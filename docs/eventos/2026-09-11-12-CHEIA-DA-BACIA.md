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

## O que falta

1. **Extrair o evento completo do ndjson da VPS**, antes que alguém limpe a pasta:
   ```
   cd /opt/enchentes-vale-itajai
   grep -h '"2026-09-1[012]' data/tempo-real/2026-09.ndjson > /tmp/cheia-2026-09-11-12.ndjson
   wc -l /tmp/cheia-2026-09-11-12.ndjson
   ```
   e trazer o arquivo para `data/brutos/`. Com ele sai a subida, a taxa de variação em cm/h e o
   horário real de cada crista.
2. **Decidir se as cristas entram em `enchentes.json`.** São picos de 2026 medidos pela nossa coleta,
   com régua nomeada nos dois lados — o material mais limpo que o projeto tem. Decisão do Jefferson.
3. **Conferir se o aviso saiu.** Blumenau em alerta é exatamente o caso que o bot existe para cobrir;
   `data/tempo-real/estado_alertas.json` na VPS diz o que ele fez.
4. **Indaial**: a leitura municipal de 12/09 22:00 (4,10 m, acima do alerta municipal) é a única que
   chegou. Conferir se a coleta parou ou se a fonte publica esparso.
