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
- [~] B7 · **REESCOPADO em 10/09/2026** (`docs/eventos/2026-09-10-B7-FONTES-E-EVENTO-TAIO.md`): a Asthon retém ~6 semanas e a API de Taió só 24 h — não há fonte para 2022. Vira três: B7a confirmar o código ANA da DCSC-00041 e puxar do Hidroweb; B7b listar quais das 16 estações da cadeia existem no portal de Brusque e baixar por `baixar-historico` (chunks anuais, 2018+); B7c ✅ acumular o `dados/historico` de Taió (feito: `coleta_taio.acumula_historico`, `data/tempo-real/taio-historico.ndjson`; **provado na VPS às 20:30 BRT: 24 linhas no primeiro ciclo**). O script de download da DCSC (B6) continua valendo para as janelas que a GraphQL `historic` responde.
- [ ] B8 · "Sim" para os registros de Blumenau 2021/2022 (6,82 m em 21/01/2021 21:45; 9,41 m em 05/05/2022 02:45, régua).
- [ ] B9 · Envio do C12 à EPAGRI (thread do C5).
- [ ] B10 · Diagnóstico da VPS: `curl -v` da estação 79 de Brusque e as cinco URLs (é bloqueio dos portais ou da VPS?).
- [ ] B11 · VPS: `apt upgrade` + `reboot` numa hora sem chuva (26 atualizações, "restart required"). **Não em 10/09 à noite**: onda descendo a bacia, Blumenau em atenção.

## C. Claude — o que faz sozinho assim que puder

- [x] C1 · Consolidador do histórico DCSC + resumo (PR #269).
- [x] C2 · Ofício C13 rascunhado (PR #270).
- [ ] C3 · Ofícios de A1, A2, A3, A5, A7, A8, A9, A10 — depende de B1.
- [ ] C4 · Script de download do DCSC no repo, com query e allowlist documentadas — depende de B6.
- [ ] C5 · Cruzar `data/series/dcsc/` com `data/tempo-real/*.ndjson` da VPS (mesma rede, mesmo fuso) — depende de B5.
- [ ] C6 · Com cada resposta de COMPDEC: gravar `cotas_m` + `regua_das_cotas_fonte`, teste do par, e medir o ganho em km com `conferir_cobertura.py`.

## D. Evento de 10/09/2026 — onda descendo a bacia

- [x] D1 · Evidências congeladas: os dois relatórios em `docs/eventos/`, o card + histórico de Taió com comportas (`data/brutos/taio-cards-e-historico-2026-09-10-1945.json`), a série de 48 h publicada às 19:46 (`data/brutos/evento-2026-09-10-serie-recente-1946.json`) e o CSV horário do navegador, 09/09 20h → 10/09 19h, com chuva e comportas (`data/brutos/taio-evento-2026-09-10-historico-horario.csv`).
- [x] D7 · O `coleta_taio_historico.py` do navegador NÃO entrou: faria o mesmo que `coleta_taio.acumula_historico` (no cron a cada 15 min, contra 12 h), gravando num CSV rastreado em `data/brutos/` que cresceria a cada rodada. O que ele tinha a mais entrou no parser: `chuva_mm`, `jusante_m` e `comportas_fechadas` na mesma linha horária.
- [x] D2 · Taió: mínima 2,40 m 00:13 → crista **5,48 m às 13:29** → 4,45 m 19:43. Cruzou 5,00 m ~09:45. 86,3 mm/24 h. Comportas da Oeste 7→0 às 13h. Gravado em `estacoes.json` como evidência de campo da decisão de avisar em 5,00 m.
- [x] D3 · Rio do Sul (Tito Buss): 2,96 m 00:14 → **crista 4,29 m às 16:57** → 4,20 m 19:44 → **4,15 m às 20:35, NORMAL no portal da Defesa Civil de Rio do Sul** (tela do Jefferson, 20:38 BRT; Ricardo Kanitz/Itajaí do Sul 3,04 m, BR 470/Itajaí do Oeste 4,40 m). Não chegou à atenção (4,50). A subida foi em paralelo com Taió (chuva na bacia inteira) e a barragem fechou no pico: **não serve para calibrar trânsito**. PISTA vista na barra do portal: marcas em 4,50 / 5,50 / 6,50 / **8,00** — o cadastro tem 4,5 / 5,5 / 6,5; conferir na legenda do portal o nome do degrau de 8,00 antes de gravar.
- [x] D4 · Blumenau: 2,64 m 00:05 → **crista 4,26 m (15:35–19:00)** → **4,23 m e caindo às ~20:40, ainda ATENÇÃO no site oficial da Defesa Civil de Blumenau** (tela do Jefferson: "Nível do Rio Itajaí-Açu 4,23 m ↓", situação publicada em 10/09/2026). Confirmado às 20:10 BRT que o site pinta Blumenau AMARELA — primeira cheia real em que o par régua ↔ cota do site coincide com o aviso oficial. **Origem do "2,66 m às 18:00" EXPLICADA às 20:55 BRT**: o navegador do Jefferson recebeu uma cópia do `nivel_oficial.json` cujo último ponto de `niveis` era 2026-09-09T21:00Z (18:00 BRT de 09/09) = 2,66 m. A VPS, lendo o MESMO arquivo pelo `coleta_alertablu.py`, recebeu 25 pontos horários depois desse, até 10/09 19:00 BRT = 4,26 m (série publicada às 19:46). Logo o arquivo não está congelado no servidor — a cópia do navegador estava 25 h velha, por cache do navegador ou de uma borda de CDN. **Aviso ao AlertaBlu fica em espera** até distinguir os dois (fetch com `?nc=1` no navegador + cabeçalhos na VPS). O `nivel.json` de 07/11/2013 respondendo 200 é achado válido de qualquer jeito.
- [ ] D5 · Gaspar: 1,74 m às 05:53 é a única leitura que a VPS conseguiu; o navegador viu 2,58 m às 19:07 (NORMALIDADE). Sem série.
- [ ] D6 · Registrar as cristas do evento em `enchentes.json` só se o Jefferson decidir; por ora ficam nos brutos.

## Histórico

- 10/09/2026 · lista criada; medição 57% / 27%; C1 e C2 fechados.
- 10/09/2026 19:50 BRT · evento real na bacia (bloco D); B7 reescopado em B7a/B7b/B7c, B7c feito; B11 adiado; PR #272.
- 10/09/2026 20:05 BRT · CSV horário do evento e chuva/jusante/comportas fechadas no parser (D1, D7); PR #273.
- 10/09/2026 20:10 BRT · Blumenau amarela no site e em atenção no site oficial (D4).
- 10/09/2026 20:55 BRT · origem do 2,66 m explicada: cópia de 25 h do nivel_oficial.json no navegador; na VPS o mesmo arquivo está vivo (D4).
- 10/09/2026 20:45 BRT · picos passados em Rio do Sul (4,29 m, 16:57) e Blumenau (4,26 m, 15:35–19:00), ambos caindo nos portais oficiais (D3, D4); acumulador de Taió provado na VPS (B7c).
