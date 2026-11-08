# Descida medida — quanto tempo a cheia leva de uma régua à outra

Gerado por `scripts/medir_descida.py` em 2026-11-08T00:24:32+00:00. Séries de 2026-07-19T21:10 a 2026-11-07T21:00 (hora de Brasília). **Não é o tempo que o site mostra** (`transito.json`, Tabela 7.5.1 da JICA): é o que as réguas viram nas cheias de 2026. Trocar o do site é decisão do Jefferson.

Atraso em horas a partir da crista de cima; negativo = lá embaixo cresta ANTES (chuva local, maré, afluente). Faixa = p25–p75 dos eventos; IC90 = intervalo de confiança de 90 % da mediana (bootstrap).

| Trecho | Eventos | Pico a pico | Meia-subida | Centro de massa | Correlação | DTW | JICA | Confiança |
|---|---|---|---|---|---|---|---|---|
| Taió (DCSC-00041) → Rio do Sul (DCSC-00013) | 12 | -1.7 (-5.8 a +10.7) | +0.7 (-0.4 a +7.2) | +2.3 (-4.5 a +12.9) | +0.6 (-0.8 a +5.5) | -0.9 (-7.4 a +14.8) | 6 h | insuficiente: os eventos discordam: p25–p75 de 16.5 h |
| Ituporanga (DCSC-00039) → Rio do Sul (DCSC-00013) | 11 | +7.0 (+4.9 a +12.2) | +6.7 (+5.7 a +7.5) | +9.5 (+5.8 a +13.4) | +6.1 (+5.1 a +7.6) | +8.9 (+7.2 a +14.9) | -1 h | insuficiente: os eventos discordam: p25–p75 de 7.3 h |
| Rio do Sul (DCSC-00013) → Ascurra (DCSC-00003) | 13 | +2.1 (-0.3 a +4.7) | +3.5 (+0.8 a +3.8) | +2.5 (-2.0 a +4.0) | +3.0 (+1.0 a +5.2) | +1.5 (-2.3 a +3.7) | — | media |
| Ascurra (DCSC-00003) → Blumenau (PADKND + AlertaBlu) | 10 | +5.4 (+4.3 a +7.5) | +2.5 (+0.3 a +4.1) | +5.5 (+3.1 a +6.5) | +4.7 (+3.7 a +5.3) | +5.6 (+3.8 a +6.1) | — | media |
| Rio do Sul (DCSC-00013) → Blumenau (PADKND + AlertaBlu) | 8 | +6.6 (+4.9 a +10.8) | +3.1 (+1.5 a +6.2) | +5.5 (+4.9 a +9.5) | +4.2 (+3.8 a +8.8) | +6.4 (+4.1 a +7.5) | 7–10 h | media |
| Blumenau (PADKND + AlertaBlu) → Ilhota (DCSC-00030) | 10 | +3.7 (+0.7 a +4.7) | +1.9 (+0.0 a +3.0) | +2.0 (-2.4 a +3.4) | +2.5 (+2.3 a +2.5) | +2.2 (-1.4 a +3.2) | 5–7 h | media |
| Ilhota (DCSC-00030) → Itajaí DC-11 Volta de Cima | 19 | +5.3 (-0.5 a +18.3) | -0.0 (-0.8 a +12.3) | +3.5 (+0.6 a +22.1) | -0.5 (-0.5 a -0.4) | -0.5 (-0.5 a +0.7) | 7–10 h | insuficiente: os eventos discordam: p25–p75 de 18.8 h; os métodos discordam em 5.8 h |
| Blumenau (PADKND + AlertaBlu) → Itajaí DC-11 Volta de Cima | 10 | +1.5 (+0.2 a +4.6) | +1.7 (-3.5 a +3.3) | +1.8 (-0.4 a +3.7) | +3.7 (+3.7 a +3.7) | +3.6 (-1.4 a +4.0) | 12–17 h | media |
| Blumenau (PADKND + AlertaBlu) → Itajaí DC-02 Praça Celso Pereira | 3 | +6.8 (+2.4 a +19.8) | +11.1 (+3.2 a +19.1) | +2.5 (+2.5 a +2.5) | -3.4 (-3.6 a -3.2) | +14.7 (+6.3 a +23.1) | 12–17 h | insuficiente: os eventos discordam: p25–p75 de 17.4 h; só um método achou forma comparável nas duas réguas; sem segundo método, não há como conferir |
| Vidal Ramos (DCSC-00024) → Botuverá (DCSC-00018) | 14 | +5.2 (+4.4 a +6.4) | +7.3 (+6.4 a +27.8) | +6.4 (+4.7 a +7.1) | +5.7 (+5.1 a +7.3) | +6.3 (+4.9 a +7.0) | — | media |
| Botuverá (DCSC-00018) → Brusque (DCSC-00019) | 14 | +7.0 (+6.3 a +8.4) | +2.3 (-6.0 a +6.0) | +6.3 (+4.3 a +7.2) | +6.3 (+5.6 a +7.0) | +6.5 (+4.5 a +7.7) | — | insuficiente: os métodos discordam em 4.7 h |
| Brusque (DCSC-00019) → Itajaí DC-10 Limoeiro | 11 | +1.9 (+1.2 a +2.5) | +0.2 (-0.8 a +2.2) | +1.8 (+1.0 a +7.8) | +1.2 (+0.8 a +1.5) | +1.4 (+0.1 a +1.8) | — | alta |

## Evento a evento

### Taió (DCSC-00041) → Rio do Sul (DCSC-00013)

| Crista em cima | Pico (zero da régua) | Crista embaixo | pico a pico | meia-subida | centro de massa | correlação | DTW | Obs. |
|---|---|---|---|---|---|---|---|---|
| 2026-07-22 23:15 | 6.02 m | 2026-07-22 15:40 | -7.6 | -1.8 | -5.7 | -0.7 | -7.8 |  |
| 2026-07-30 02:55 | 4.30 m | 2026-07-30 07:30 | +4.6 | -1.8 | +4.1 | -3.0 | +6.7 |  |
| 2026-08-06 23:55 | 4.03 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-09 08:05 | 3.76 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-12 21:00 | 4.46 m | 2026-08-13 06:00 | +9.0 | +24.6 | +12.6 | +4.2 | +14.1 |  |
| 2026-08-15 12:30 | 5.58 m | 2026-08-15 12:30 | +0.0 | +0.8 | +0.5 | -0.5 | -0.2 |  |
| 2026-08-18 02:00 | 5.92 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-01 09:00 | 7.16 m | 2026-09-01 05:35 | -3.4 | +0.7 | -2.3 | +1.7 | -4.2 |  |
| 2026-09-04 14:40 | 5.77 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-10 13:20 | 5.48 m | 2026-09-12 00:25 | +35.1 | +35.9 | +38.5 | +35.0 | +35.7 |  |
| 2026-09-12 05:25 | 6.95 m | 2026-09-12 00:25 | -5.0 | -0.1 | -4.7 | -0.7 | -8.0 |  |
| 2026-09-15 19:35 | 6.08 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-22 17:50 | 6.57 m | 2026-09-22 09:15 | -8.6 | +0.1 | -6.5 | -1.2 | -10.8 |  |
| 2026-09-26 05:45 | 5.71 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-03 01:15 | 5.72 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-07 09:15 | 5.26 m | 2026-10-08 00:55 | +15.7 | +5.5 | +16.4 | +5.3 | +16.8 |  |
| 2026-10-13 14:50 | 3.42 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-16 14:25 | 4.58 m | 2026-10-16 09:10 | -5.2 | -1.4 | +4.2 | -1.0 | -1.7 |  |
| 2026-10-19 15:00 | 3.95 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-25 07:25 | 5.28 m | 2026-10-26 00:10 | +16.8 | +6.6 | +13.6 | +6.0 | +17.0 |  |
| 2026-10-30 23:35 | 3.29 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-11-02 16:35 | 4.69 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-11-05 08:00 | 5.96 m | 2026-11-05 00:05 | -7.9 | +9.1 | -4.4 | +9.2 | -7.2 |  |

Theil–Sen: -0.60 h por metro de amplitude em cima (negativo = cheia maior desce mais rápido, como a JICA prevê).

### Ituporanga (DCSC-00039) → Rio do Sul (DCSC-00013)

| Crista em cima | Pico (zero da régua) | Crista embaixo | pico a pico | meia-subida | centro de massa | correlação | DTW | Obs. |
|---|---|---|---|---|---|---|---|---|
| 2026-07-22 10:15 | 3.13 m | 2026-07-22 15:40 | +5.4 | +7.1 | +9.5 | +5.0 | +8.1 |  |
| 2026-07-24 16:55 | 3.40 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-07-30 00:30 | 2.76 m | 2026-07-30 07:30 | +7.0 | -0.8 | +5.3 | -0.0 | +8.9 |  |
| 2026-08-13 01:40 | 3.42 m | 2026-08-13 06:00 | +4.3 | +6.4 | +6.5 | +5.5 | +6.2 |  |
| 2026-08-17 11:30 | 3.53 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-19 19:15 | 4.05 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-30 08:55 | 3.24 m | 2026-08-29 23:35 | -9.3 | +6.6 | +4.0 | +3.7 | -1.9 |  |
| 2026-09-06 21:10 | 4.26 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-08 00:40 | 4.09 m | 2026-09-08 11:50 | +11.2 | +7.2 | +6.3 | +6.1 | +8.2 |  |
| 2026-09-10 09:30 | 2.45 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-14 18:30 | 3.87 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-20 06:40 | 3.14 m | 2026-09-20 13:25 | +6.8 | +4.8 | +10.2 | +6.2 | +10.6 |  |
| 2026-09-21 20:00 | 1.95 m | 2026-09-22 09:15 | +13.2 | +7.8 | +15.7 | — | +18.2 |  |
| 2026-10-02 20:05 | 4.37 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-07 14:25 | 4.37 m | 2026-10-08 00:55 | +10.5 | +5.0 | +11.0 | +6.3 | +11.5 |  |
| 2026-10-15 10:00 | 2.77 m | 2026-10-16 09:10 | +23.2 | +17.8 | +31.1 | +17.6 | +6.2 |  |
| 2026-10-16 14:25 | 2.13 m | 2026-10-16 09:10 | -5.2 | +6.7 | +2.0 | +17.7 | +23.5 |  |
| 2026-10-30 19:30 | 1.40 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-11-04 08:40 | 2.89 m | 2026-11-05 00:05 | +15.4 | +13.9 | +17.3 | +8.1 | +19.2 |  |
| 2026-11-06 13:10 | 2.63 m | 2026-11-07 20:10 | +31.0 | +24.8 | — | — | — | a crista de baixo está na ponta da série (pode não ter passado) |
| 2026-11-07 13:05 | 2.21 m | 2026-11-07 20:10 | +7.1 | +4.2 | — | — | — | a crista de baixo está na ponta da série (pode não ter passado) |

Theil–Sen: -3.37 h por metro de amplitude em cima (negativo = cheia maior desce mais rápido, como a JICA prevê).

### Rio do Sul (DCSC-00013) → Ascurra (DCSC-00003)

| Crista em cima | Pico (zero da régua) | Crista embaixo | pico a pico | meia-subida | centro de massa | correlação | DTW | Obs. |
|---|---|---|---|---|---|---|---|---|
| 2026-07-22 15:40 | 5.76 m | 2026-07-22 19:55 | +4.2 | +3.5 | +4.0 | +5.7 | +4.3 |  |
| 2026-07-30 07:30 | 4.43 m | 2026-07-30 19:00 | +11.5 | +3.5 | +4.0 | — | +6.3 |  |
| 2026-08-13 06:00 | 4.66 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-15 12:30 | 5.51 m | 2026-08-15 14:35 | +2.1 | +0.8 | +1.8 | +1.7 | +2.7 |  |
| 2026-08-29 23:35 | 3.83 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-01 05:35 | 7.06 m | 2026-09-01 05:40 | +0.1 | -0.4 | -2.4 | +0.3 | -2.7 |  |
| 2026-09-08 11:50 | 4.78 m | 2026-09-08 19:10 | +7.3 | +6.4 | +5.1 | +6.8 | +1.5 |  |
| 2026-09-12 00:25 | 6.05 m | 2026-09-12 00:05 | -0.3 | -2.7 | -2.8 | -0.3 | -2.3 |  |
| 2026-09-20 13:25 | 5.45 m | 2026-09-20 18:05 | +4.7 | +3.6 | +2.5 | +3.7 | +3.7 |  |
| 2026-09-22 09:15 | 6.48 m | 2026-09-22 07:40 | -1.6 | -0.6 | -2.0 | +1.0 | -3.3 |  |
| 2026-09-29 22:15 | 5.33 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-01 08:35 | 6.52 m | 2026-10-01 13:45 | +5.2 | +2.4 | +4.3 | +5.0 | +5.2 |  |
| 2026-10-08 00:55 | 5.73 m | 2026-10-07 20:25 | -4.5 | +3.8 | -2.3 | +2.3 | -0.6 |  |
| 2026-10-16 09:10 | 4.42 m | 2026-10-16 13:20 | +4.2 | +6.1 | +2.7 | +7.0 | -1.5 |  |
| 2026-10-26 00:10 | 3.65 m | 2026-10-25 21:15 | -2.9 | +12.3 | +5.1 | +1.0 | -5.0 |  |
| 2026-11-05 00:05 | 8.25 m | 2026-11-05 01:45 | +1.7 | +1.9 | +2.1 | +3.7 | +2.0 |  |

Theil–Sen: -1.84 h por metro de amplitude em cima (negativo = cheia maior desce mais rápido, como a JICA prevê).

### Ascurra (DCSC-00003) → Blumenau (PADKND + AlertaBlu)

| Crista em cima | Pico (zero da régua) | Crista embaixo | pico a pico | meia-subida | centro de massa | correlação | DTW | Obs. |
|---|---|---|---|---|---|---|---|---|
| 2026-07-19 21:50 | 6.48 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-07-20 19:50 | 6.37 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-07-22 19:55 | 8.63 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-07-30 19:00 | 7.30 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-01 21:20 | 6.74 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-02 21:30 | 6.62 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-03 19:25 | 6.55 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-04 19:20 | 6.47 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-05 19:35 | 6.46 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-07 18:20 | 7.06 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-15 14:35 | 8.53 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-01 05:40 | 10.13 m | 2026-09-01 10:30 | +4.8 | — | +7.1 | — | — |  |
| 2026-09-08 19:10 | 7.55 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-10 17:15 | 7.97 m | 2026-09-10 18:30 | +1.2 | +1.8 | +2.6 | +4.5 | +3.5 |  |
| 2026-09-12 00:05 | 10.45 m | 2026-09-12 05:20 | +5.2 | +4.0 | — | +4.8 | +5.8 |  |
| 2026-09-20 18:05 | 8.35 m | 2026-09-20 21:45 | +3.7 | +0.4 | +3.1 | +1.5 | +3.8 |  |
| 2026-09-22 07:40 | 9.41 m | 2026-09-22 11:50 | +4.2 | +0.0 | +3.2 | +1.4 | +5.3 |  |
| 2026-09-28 22:25 | 8.24 m | 2026-09-29 06:05 | +7.7 | +3.2 | +5.9 | +4.5 | +7.1 |  |
| 2026-10-01 13:45 | 8.76 m | 2026-10-01 19:15 | +5.5 | +4.4 | +5.5 | +5.2 | +5.8 |  |
| 2026-10-07 20:25 | 8.29 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-16 13:20 | 7.61 m | 2026-10-16 20:10 | +6.8 | +5.0 | +6.5 | +5.5 | +7.7 |  |
| 2026-10-25 21:15 | 7.17 m | 2026-10-26 05:05 | +7.8 | -10.2 | +0.1 | +6.8 | +1.5 |  |
| 2026-10-31 21:25 | 6.60 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-11-01 22:05 | 6.62 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-11-05 01:45 | 9.46 m | 2026-11-05 21:30 | +19.8 | — | +20.2 | — | — |  |

Theil–Sen: +0.77 h por metro de amplitude em cima (negativo = cheia maior desce mais rápido, como a JICA prevê).

### Rio do Sul (DCSC-00013) → Blumenau (PADKND + AlertaBlu)

| Crista em cima | Pico (zero da régua) | Crista embaixo | pico a pico | meia-subida | centro de massa | correlação | DTW | Obs. |
|---|---|---|---|---|---|---|---|---|
| 2026-07-22 15:40 | 5.76 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-07-30 07:30 | 4.43 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-13 06:00 | 4.66 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-15 12:30 | 5.51 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-29 23:35 | 3.83 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-01 05:35 | 7.06 m | 2026-09-01 10:30 | +4.9 | — | +4.7 | — | — |  |
| 2026-09-08 11:50 | 4.78 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-12 00:25 | 6.05 m | 2026-09-12 05:20 | +4.9 | +1.3 | — | +4.2 | +3.5 |  |
| 2026-09-20 13:25 | 5.45 m | 2026-09-20 21:45 | +8.3 | +4.0 | +5.5 | +3.8 | +6.8 |  |
| 2026-09-22 09:15 | 6.48 m | 2026-09-22 11:50 | +2.6 | -0.6 | +1.2 | +1.5 | +2.2 |  |
| 2026-09-29 22:15 | 5.33 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-01 08:35 | 6.52 m | 2026-10-01 19:15 | +10.7 | +6.9 | +9.8 | +8.8 | +11.2 |  |
| 2026-10-08 00:55 | 5.73 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-16 09:10 | 4.42 m | 2026-10-16 20:10 | +11.0 | +11.1 | +9.2 | +12.7 | +6.0 |  |
| 2026-10-26 00:10 | 3.65 m | 2026-10-26 05:05 | +4.9 | +2.1 | +5.2 | — | +7.8 |  |
| 2026-11-05 00:05 | 8.25 m | 2026-11-05 21:30 | +21.4 | — | +22.3 | — | — |  |

Theil–Sen: +5.06 h por metro de amplitude em cima (negativo = cheia maior desce mais rápido, como a JICA prevê).

### Blumenau (PADKND + AlertaBlu) → Ilhota (DCSC-00030)

| Crista em cima | Pico (zero da régua) | Crista embaixo | pico a pico | meia-subida | centro de massa | correlação | DTW | Obs. |
|---|---|---|---|---|---|---|---|---|
| 2026-09-01 10:30 | 7.57 m | 2026-09-01 11:10 | +0.7 | — | -2.1 | — | — |  |
| 2026-09-10 18:30 | 4.26 m | 2026-09-10 22:20 | +3.8 | +2.5 | +1.3 | — | +2.2 |  |
| 2026-09-12 05:20 | 7.86 m | 2026-09-12 08:55 | +3.6 | +1.9 | — | -0.2 | +3.2 |  |
| 2026-09-20 21:45 | 4.29 m | 2026-09-21 02:35 | +4.8 | +3.0 | +2.7 | +5.2 | +3.2 |  |
| 2026-09-22 11:50 | 6.62 m | 2026-09-22 19:05 | +7.2 | +1.0 | +4.9 | +2.3 | +6.7 |  |
| 2026-09-29 06:05 | 3.87 m | 2026-09-28 22:30 | -7.6 | -59.4 | -3.6 | — | -4.1 |  |
| 2026-10-01 19:15 | 4.53 m | 2026-10-01 23:25 | +4.2 | -0.1 | +2.9 | +2.5 | +3.2 |  |
| 2026-10-07 07:55 | 5.04 m | 2026-10-07 08:35 | +0.7 | +4.4 | — | +2.5 | -5.3 |  |
| 2026-10-16 20:10 | 3.18 m | 2026-10-17 23:50 | +27.7 | +0.0 | +21.3 | — | +1.0 |  |
| 2026-10-26 05:05 | 2.92 m | 2026-10-26 05:05 | +0.0 | +24.3 | -5.3 | — | -1.4 |  |
| 2026-11-05 21:30 | 4.91 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |

Theil–Sen: -0.18 h por metro de amplitude em cima (negativo = cheia maior desce mais rápido, como a JICA prevê).

### Ilhota (DCSC-00030) → Itajaí DC-11 Volta de Cima

| Crista em cima | Pico (zero da régua) | Crista embaixo | pico a pico | meia-subida | centro de massa | correlação | DTW | Obs. |
|---|---|---|---|---|---|---|---|---|
| 2026-07-20 20:10 | 9.28 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-07-21 21:10 | 9.14 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-07-23 07:00 | 9.91 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-07-30 07:55 | 9.30 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-05 19:40 | 9.13 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-07 09:35 | 9.17 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-08 10:30 | 9.51 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-11 15:25 | 9.55 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-12 16:00 | 9.53 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-13 16:15 | 9.60 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-15 20:30 | 10.25 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-19 08:05 | 9.47 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-25 11:45 | 9.37 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-27 15:50 | 8.97 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-28 15:55 | 9.01 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-29 16:55 | 9.39 m | 2026-08-30 16:10 | +23.2 | — | +24.6 | — | — |  |
| 2026-09-01 11:10 | 11.61 m | 2026-09-01 10:40 | -0.5 | -0.6 | +0.4 | -0.4 | +0.3 |  |
| 2026-09-06 19:05 | 9.76 m | 2026-09-06 17:20 | -1.8 | -0.5 | +1.4 | -0.5 | -0.5 |  |
| 2026-09-10 22:20 | 9.98 m | 2026-09-12 08:20 | +34.0 | +31.4 | — | -0.5 | +17.2 |  |
| 2026-09-12 08:55 | 11.83 m | 2026-09-12 08:20 | -0.6 | +0.2 | — | -0.5 | +1.8 |  |
| 2026-09-21 02:35 | 9.80 m | 2026-09-21 02:50 | +0.2 | -6.5 | +0.5 | -0.5 | -0.5 |  |
| 2026-09-22 19:05 | 11.06 m | 2026-09-22 17:30 | -1.6 | +0.2 | +1.2 | -0.5 | -0.5 |  |
| 2026-09-28 03:30 | 9.66 m | 2026-09-28 03:00 | -0.5 | -4.6 | -0.2 | -0.4 | -0.7 |  |
| 2026-09-28 22:30 | 9.67 m | 2026-09-29 03:50 | +5.3 | +53.2 | +3.9 | -0.4 | -0.4 |  |
| 2026-10-01 23:25 | 10.16 m | 2026-10-01 22:00 | -1.4 | -3.5 | +0.6 | -0.5 | -0.2 |  |
| 2026-10-07 08:35 | 10.40 m | 2026-10-07 08:15 | -0.3 | +0.8 | — | -0.5 | -0.5 |  |
| 2026-10-17 23:50 | 9.63 m | 2026-10-18 09:50 | +10.0 | -0.2 | +3.1 | -0.4 | -2.8 |  |
| 2026-10-22 00:15 | 10.60 m | 2026-10-23 11:10 | +34.9 | — | +34.1 | — | -9.5 |  |
| 2026-10-22 23:45 | 9.31 m | 2026-10-23 11:10 | +11.4 | +8.5 | +9.9 | — | -1.3 |  |
| 2026-10-24 01:20 | 9.47 m | 2026-10-25 13:20 | +36.0 | +38.3 | +46.4 | -0.5 | +24.5 |  |
| 2026-10-25 02:50 | 9.80 m | 2026-10-25 13:20 | +10.5 | -0.4 | +21.3 | -0.5 | +0.0 |  |
| 2026-10-26 05:05 | 11.04 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-28 04:30 | 9.59 m | 2026-10-29 05:05 | +24.6 | +23.8 | +24.8 | — | +13.6 |  |
| 2026-10-29 05:10 | 9.44 m | 2026-10-29 05:05 | -0.1 | -1.4 | +0.0 | -0.4 | — |  |
| 2026-10-30 05:50 | 9.53 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-31 13:05 | 9.47 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-11-01 13:55 | 9.28 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-11-03 10:30 | 9.50 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-11-05 08:20 | 11.02 m | 2026-11-05 21:40 | +13.3 | — | +13.7 | — | — |  |

Theil–Sen: -1.31 h por metro de amplitude em cima (negativo = cheia maior desce mais rápido, como a JICA prevê).

### Blumenau (PADKND + AlertaBlu) → Itajaí DC-11 Volta de Cima

| Crista em cima | Pico (zero da régua) | Crista embaixo | pico a pico | meia-subida | centro de massa | correlação | DTW | Obs. |
|---|---|---|---|---|---|---|---|---|
| 2026-09-01 10:30 | 7.57 m | 2026-09-01 10:40 | +0.2 | — | -1.7 | — | — |  |
| 2026-09-10 18:30 | 4.26 m | 2026-09-10 17:45 | -0.8 | +2.6 | +0.1 | — | -0.2 |  |
| 2026-09-12 05:20 | 7.86 m | 2026-09-12 08:20 | +3.0 | +2.2 | — | — | +3.8 |  |
| 2026-09-20 21:45 | 4.29 m | 2026-09-21 02:50 | +5.1 | -3.5 | +3.2 | — | +3.8 |  |
| 2026-09-22 11:50 | 6.62 m | 2026-09-22 17:30 | +5.7 | +1.2 | +6.1 | — | +7.2 |  |
| 2026-09-29 06:05 | 3.87 m | 2026-09-29 03:50 | -2.2 | -6.2 | +0.3 | — | -5.1 |  |
| 2026-10-01 19:15 | 4.53 m | 2026-10-01 22:00 | +2.8 | -3.5 | +3.6 | — | +4.4 |  |
| 2026-10-07 07:55 | 5.04 m | 2026-10-07 08:15 | +0.3 | +5.2 | — | +3.7 | -6.8 |  |
| 2026-10-16 20:10 | 3.18 m | 2026-10-17 06:55 | +10.8 | +7.7 | +3.9 | — | +3.3 |  |
| 2026-10-26 05:05 | 2.92 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-11-05 21:30 | 4.91 m | 2026-11-05 21:40 | +0.2 | — | -1.6 | — | — |  |

Theil–Sen: +0.27 h por metro de amplitude em cima (negativo = cheia maior desce mais rápido, como a JICA prevê).

### Blumenau (PADKND + AlertaBlu) → Itajaí DC-02 Praça Celso Pereira

| Crista em cima | Pico (zero da régua) | Crista embaixo | pico a pico | meia-subida | centro de massa | correlação | DTW | Obs. |
|---|---|---|---|---|---|---|---|---|
| 2026-09-01 10:30 | 7.57 m | 2026-09-01 17:20 | +6.8 | — | +2.5 | — | — |  |
| 2026-09-10 18:30 | 4.26 m | 2026-09-12 03:20 | +32.8 | +27.0 | — | -3.1 | +31.6 |  |
| 2026-09-12 05:20 | 7.86 m | 2026-09-12 03:20 | -2.0 | -4.8 | — | -3.7 | -2.2 |  |
| 2026-09-20 21:45 | 4.29 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-22 11:50 | 6.62 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-29 06:05 | 3.87 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-01 19:15 | 4.53 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-07 07:55 | 5.04 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-16 20:10 | 3.18 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-26 05:05 | 2.92 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-11-05 21:30 | 4.91 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |

### Vidal Ramos (DCSC-00024) → Botuverá (DCSC-00018)

| Crista em cima | Pico (zero da régua) | Crista embaixo | pico a pico | meia-subida | centro de massa | correlação | DTW | Obs. |
|---|---|---|---|---|---|---|---|---|
| 2026-07-22 07:35 | 3.68 m | 2026-07-22 12:55 | +5.3 | +6.8 | +6.7 | +7.3 | +6.3 |  |
| 2026-07-29 11:55 | 3.10 m | 2026-07-29 19:05 | +7.2 | +7.7 | +8.8 | +7.3 | +8.8 |  |
| 2026-08-07 05:00 | 3.00 m | 2026-08-07 12:50 | +7.8 | +9.7 | +8.7 | +18.9 | +8.6 |  |
| 2026-08-13 23:50 | 3.42 m | 2026-08-14 04:50 | +5.0 | +34.8 | +5.5 | +5.5 | +5.2 |  |
| 2026-08-29 11:35 | 3.53 m | 2026-08-29 17:35 | +6.0 | +7.2 | +6.9 | +7.0 | +6.3 |  |
| 2026-08-31 22:35 | 3.88 m | 2026-09-01 02:45 | +4.2 | +53.5 | +4.5 | +4.7 | +2.8 |  |
| 2026-09-10 05:10 | 3.00 m | 2026-09-10 11:40 | +6.5 | +6.7 | +6.8 | +6.4 | +6.5 |  |
| 2026-09-11 15:05 | 3.38 m | 2026-09-11 19:20 | +4.2 | +33.9 | +4.0 | +5.0 | +4.1 |  |
| 2026-09-20 07:50 | 3.33 m | 2026-09-20 13:40 | +5.8 | +5.4 | +6.1 | +5.5 | +5.9 |  |
| 2026-09-21 20:45 | 3.81 m | 2026-09-22 01:55 | +5.2 | +6.3 | +5.9 | +5.3 | +6.3 |  |
| 2026-09-29 14:30 | 3.40 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-30 23:50 | 4.18 m | 2026-10-01 04:45 | +4.9 | +37.4 | +7.2 | +5.8 | — |  |
| 2026-10-16 00:20 | 2.99 m | 2026-10-16 08:05 | +7.8 | +7.4 | +7.6 | +7.7 | +9.0 |  |
| 2026-11-04 15:00 | 4.49 m | 2026-11-04 18:50 | +3.8 | +2.4 | +3.8 | +4.0 | +3.2 |  |
| 2026-11-07 13:20 | 4.56 m | 2026-11-07 17:30 | +4.2 | +4.5 | +2.8 | +4.3 | — |  |

Theil–Sen: -2.78 h por metro de amplitude em cima (negativo = cheia maior desce mais rápido, como a JICA prevê).

### Botuverá (DCSC-00018) → Brusque (DCSC-00019)

| Crista em cima | Pico (zero da régua) | Crista embaixo | pico a pico | meia-subida | centro de massa | correlação | DTW | Obs. |
|---|---|---|---|---|---|---|---|---|
| 2026-07-22 12:55 | 4.82 m | 2026-07-22 20:20 | +7.4 | +6.4 | +7.2 | +6.3 | +7.7 |  |
| 2026-07-29 19:05 | 3.66 m | 2026-07-30 03:50 | +8.8 | -23.1 | +8.2 | +7.7 | +9.0 |  |
| 2026-08-06 03:15 | 3.18 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-07 12:50 | 3.36 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-09 04:20 | 3.41 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-14 04:50 | 4.96 m | 2026-08-14 12:00 | +7.2 | +6.1 | +7.1 | +6.7 | +7.5 |  |
| 2026-08-15 08:30 | 4.27 m | 2026-08-15 15:05 | +6.6 | +5.8 | +6.2 | +6.5 | +6.5 |  |
| 2026-08-29 17:35 | 4.08 m | 2026-08-30 02:30 | +8.9 | +7.9 | +8.2 | +7.3 | +8.3 |  |
| 2026-09-01 02:45 | 5.76 m | 2026-09-01 09:40 | +6.9 | -3.5 | +4.6 | +7.0 | +3.1 |  |
| 2026-09-10 11:40 | 3.81 m | 2026-09-10 06:40 | -5.0 | -5.8 | -5.5 | -5.4 | +4.5 |  |
| 2026-09-11 19:20 | 5.44 m | 2026-09-12 01:55 | +6.6 | +1.6 | +4.1 | +1.6 | +6.3 |  |
| 2026-09-20 13:40 | 4.16 m | 2026-09-20 07:55 | -5.8 | -6.0 | -0.3 | -5.7 | -2.2 |  |
| 2026-09-22 01:55 | 5.18 m | 2026-09-22 10:35 | +8.7 | -6.1 | +6.4 | +6.0 | +7.3 |  |
| 2026-10-01 04:45 | 5.38 m | 2026-10-01 12:00 | +7.2 | -23.9 | +7.0 | +5.7 | — |  |
| 2026-10-04 14:20 | 3.84 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-07 03:10 | 3.85 m | 2026-10-06 22:25 | -4.8 | +3.5 | +1.5 | — | +1.2 |  |
| 2026-10-08 11:50 | 3.39 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-10-16 08:05 | 4.02 m | 2026-10-16 20:25 | +12.3 | +8.1 | +10.8 | +11.0 | +12.0 |  |
| 2026-11-04 18:50 | 7.67 m | 2026-11-05 01:00 | +6.2 | +3.0 | +6.0 | +5.6 | +5.7 |  |
| 2026-11-07 17:30 | 6.59 m | 2026-11-07 20:45 | +3.2 | -3.0 | — | -2.7 | — | a crista de baixo está na ponta da série (pode não ter passado) |

Theil–Sen: +0.00 h por metro de amplitude em cima (negativo = cheia maior desce mais rápido, como a JICA prevê).

### Brusque (DCSC-00019) → Itajaí DC-10 Limoeiro

| Crista em cima | Pico (zero da régua) | Crista embaixo | pico a pico | meia-subida | centro de massa | correlação | DTW | Obs. |
|---|---|---|---|---|---|---|---|---|
| 2026-07-22 20:20 | 3.20 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-07-30 03:50 | 1.87 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-14 12:00 | 3.40 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-15 15:05 | 2.96 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-08-30 02:30 | 2.12 m | — | — | — | — | — | — | sem cheia correspondente lá embaixo na janela de −12 a +36 h |
| 2026-09-01 09:40 | 4.88 m | 2026-09-01 11:10 | +1.5 | -1.0 | — | +1.3 | -2.0 |  |
| 2026-09-10 06:40 | 2.19 m | 2026-09-10 07:40 | +1.0 | -0.0 | +1.1 | +0.8 | +1.0 |  |
| 2026-09-12 01:55 | 4.62 m | 2026-09-12 03:05 | +1.2 | +0.5 | — | +0.8 | +1.8 |  |
| 2026-09-20 07:55 | 2.97 m | 2026-09-20 09:05 | +1.2 | -0.8 | -2.0 | +1.2 | +1.2 |  |
| 2026-09-22 10:35 | 4.10 m | 2026-09-22 12:30 | +1.9 | -1.4 | +0.8 | +1.5 | +1.8 |  |
| 2026-09-30 04:15 | 2.72 m | 2026-10-01 13:55 | +33.7 | +31.5 | +35.2 | +1.5 | +1.6 |  |
| 2026-10-01 12:00 | 3.76 m | 2026-10-01 13:55 | +1.9 | +29.6 | +2.2 | +1.5 | +3.0 |  |
| 2026-10-06 22:25 | 2.45 m | 2026-10-07 00:55 | +2.5 | -0.8 | — | +0.2 | -0.2 |  |
| 2026-10-16 20:25 | 2.87 m | 2026-10-16 22:55 | +2.5 | +2.1 | +2.3 | +1.5 | +2.3 |  |
| 2026-10-26 02:25 | 1.98 m | 2026-10-25 20:15 | -6.2 | +2.3 | +1.5 | +0.5 | -0.9 |  |
| 2026-11-05 01:00 | 6.88 m | 2026-11-05 21:40 | +20.7 | — | +24.3 | — | — |  |

Theil–Sen: +0.50 h por metro de amplitude em cima (negativo = cheia maior desce mais rápido, como a JICA prevê).

## Como ler

- Cada régua tem o seu zero; só o HORÁRIO entra na conta, nunca o metro.
- Nas réguas de Itajaí a maré sai pelo filtro de Godin (24-24-25 h); ele não desloca o horário, mas achata a crista.
- Cristas quase simultâneas (|atraso| ≤ 1 h) dizem que o baixo vale subiu com a mesma chuva, não que a água chegou em uma hora.
- **Blumenau → Ilhota e → Itajaí:** a crista lá embaixo vem cedo (1 a 4 h) porque o baixo vale cresta com a chuva local, o Luiz Alves e o represamento da maré (`docs/ANALISE-CHEGADA-ITAJAI-2026.md`). Esse número é a hora da crista local, **não** a chegada da água de Blumenau; a JICA (12–17 h até Itajaí) continua sendo a referência para a onda que desce. Nenhuma das cheias de 2026 foi grande.
- Confiança `alta`: ≥ 5 cheias, p25–p75 ≤ 3 h e métodos a ≤ 2 h; `media`: ≥ 3, ≤ 6 h e ≤ 4 h.
