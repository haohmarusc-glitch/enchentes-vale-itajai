# Checklist — o que falta para cada cidade pintar

Lista viva. Atualizada a cada item que fecha; o Claude marca e avisa o Jefferson no chat. Medida de
referência: `python3 scripts/conferir_cobertura.py --arquivo <ultimo.json publicado>`.

**Situação em 10/09/2026 11:31Z** — Açu 184 de 323 km animados (57%), Mirim 50 de 186 km (27%).
Pintam: Taió, Rio do Sul, Blumenau, Brusque. Regra nº 1 continua: cota só pinta amarrada à MESMA
régua da leitura.

## A. Cidades — uma coisa por cidade

| # | cidade | km cinza | o que falta | de quem | estado |
|---|---|---:|---|---|---|
| A1 | Vidal Ramos | 84,2 | faixas da régua Asthon = DCSC-00024 | COMPDEC Vidal Ramos | [ ] ofício a redigir |
| A2 | Lontras | 52,4 | faixas amarradas à DCSC-00032, ou o zero dela | COMPDEC Lontras | [ ] ofício a redigir |
| A3 | Botuverá | 46,9 | faixas + régua nomeada (pistas de 09/09 não bastam) | COMPDEC Botuverá | [ ] ofício a redigir |
| A4 | Ilhota | 36,4 | em que régua estão 9,20 / 10,00 / 10,50 e o zero | COMPDEC Ilhota | [ ] **C11 pronto**, aguarda envio |
| A5 | Ascurra | 18,2 | faixas + régua nomeada (DCSC-00003 lê) | COMPDEC Ascurra | [ ] ofício a redigir |
| A6 | Gaspar | 16,9 | leitura de IP brasileiro + cadência; e o "ALERTA a 1,74 m" de 10/09 | Jefferson (celular/PC) + C10 | [ ] **C10 pronto**, aguarda envio |
| A7 | Indaial | 16,0 | UM número: deslocamento régua COMPDEC (RN 1402-X) ↔ DCSC-00006 | COMPDEC Indaial | [ ] ofício a redigir |
| A8 | Guabiruba | 4,8 | faixas e curso d'água da régua (ribeirão, não o Mirim) | COMPDEC Guabiruba | [ ] ofício a redigir |
| A9 | Itajaí | pinos | faixas das réguas DC-01 a DC-11 | Defesa Civil de Itajaí | [ ] ofício a redigir |
| A10 | Ituporanga | pino | leitura da 83250000, ou faixas da Ponte Vitório Sens amarradas à DCSC-00039 | Defesa Civil de Ituporanga / EPAGRI | [ ] ofício a redigir |
| A11 | Brusque (já pinta) | — | régua do 8,96 m de 2023, zero da DCSC-00019, legenda vigente (4 ou 79) | Defesa Civil de Brusque | [ ] **C13 pronto**, aguarda envio |
| A12 | Ibirama, Timbó, Rio dos Cedros, Trombudo | pinos | cota não verificada + datum da leitura DCSC (mesma pergunta de Indaial) | COMPDEC de cada uma | [ ] depois de A1–A11 |

## B. Jefferson — pendências abertas

- [ ] B1 · "Sim" para redigir os ofícios de A1, A2, A3, A5, A7, A8, A9, A10.
- [ ] B2 · Envio de C10 (Gaspar), C11 (Ilhota), C13 (Brusque) — um "sim" por ofício, ou "manda todos".
- [ ] B3 · Gaspar pelo celular: situação, nível, chuva atual e legenda em `defesacivil.gaspar.sc.gov.br/estacao/ver/21`.
- [ ] B4 · Brusque pelo celular: legenda das estações 4 e 79 (`defesacivil.brusque.sc.gov.br/estacao/ver/4` e `/ver/79`).
- [ ] B5 · VPS: `scp` da pasta `historico-dcsc` para `data/series/dcsc-zips/`, consolidador, checagem "IGUAL ao resumo do repo".
- [ ] B6 · Anexar o script de download do histórico DCSC (PC).
- [ ] B7 · Baixar de novo a partir de 2022-06-01: Taió `DCSC-00041` e as 16 da cadeia (00032, 00023, 00011, 00040, 00038, 00025, 00033, 00031, 00001, 00043, 00021, 00004, 00028, 00007, 00027, 00163).
- [ ] B8 · "Sim" para os registros de Blumenau 2021/2022 (6,82 m em 21/01/2021 21:45; 9,41 m em 05/05/2022 02:45, régua).
- [ ] B9 · Envio do C12 à EPAGRI (thread do C5).
- [ ] B10 · Diagnóstico da VPS: `curl -v` da estação 79 de Brusque e as cinco URLs (é bloqueio dos portais ou da VPS?).
- [ ] B11 · VPS: `apt upgrade` + `reboot` numa hora sem chuva (26 atualizações, "restart required").

## C. Claude — o que faz sozinho assim que puder

- [x] C1 · Consolidador do histórico DCSC + resumo (PR #269).
- [x] C2 · Ofício C13 rascunhado (PR #270).
- [ ] C3 · Ofícios de A1, A2, A3, A5, A7, A8, A9, A10 — depende de B1.
- [ ] C4 · Script de download do DCSC no repo, com query e allowlist documentadas — depende de B6.
- [ ] C5 · Cruzar `data/series/dcsc/` com `data/tempo-real/*.ndjson` da VPS (mesma rede, mesmo fuso) — depende de B5.
- [ ] C6 · Com cada resposta de COMPDEC: gravar `cotas_m` + `regua_das_cotas_fonte`, teste do par, e medir o ganho em km com `conferir_cobertura.py`.

## Histórico

- 10/09/2026 · lista criada; medição 57% / 27%; C1 e C2 fechados.
