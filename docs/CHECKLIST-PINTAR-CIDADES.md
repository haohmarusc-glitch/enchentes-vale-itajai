# Checklist — o que falta para cada cidade pintar

Lista viva. Atualizada a cada item que fecha; o Claude marca e avisa o Jefferson no chat. Medida de
referência: `python3 scripts/conferir_cobertura.py --arquivo <ultimo.json publicado>`.

**Situação em 10/09/2026 11:31Z** — Açu 184 de 323 km animados (57%), Mirim 50 de 186 km (27%).
Pintam: Taió, Rio do Sul, Blumenau, Brusque. Regra nº 1 continua: cota só pinta amarrada à MESMA
régua da leitura.

## A. Cidades — uma coisa por cidade

| # | cidade | km cinza | o que falta | de quem | estado |
|---|---|---:|---|---|---|
| A1 | Vidal Ramos | 84,2 | faixas da régua Asthon = DCSC-00024 | COMPDEC Vidal Ramos | [ ] **C15 enviado** em 10/09/2026; aguarda resposta |
| A2 | Lontras | 52,4 | faixas amarradas à DCSC-00032, ou o zero dela | COMPDEC Lontras | [ ] **C16 enviado** em 10/09/2026; aguarda resposta |
| A3 | Botuverá | 46,9 | faixas + régua nomeada (pistas de 09/09 não bastam) | COMPDEC Botuverá | [ ] **C17 enviado** em 10/09/2026; aguarda resposta |
| A4 | Ilhota | 36,4 | em que régua estão 9,20 / 10,00 / 10,50 e o zero | COMPDEC Ilhota | [ ] **C11 enviado** em 10/09/2026; aguarda resposta |
| A5 | Ascurra | 18,2 | — | — | [x] ✅ **PINTA**: no site desde 12/09 (`referenciaAscurra.ts`, exceção do front pelo bruto); no back-end desde 14/09 — a leitura da DCSC-00003 entra em `leituras` por `scripts/coleta_estadual_com_cota.py` com `codigo`, e bot, extrator, vigia e `conferir_cobertura` passam a vê-la (allowlist trancada por teste contra o `estacoes.json`; o front deduplica por `codigo`). Ganho medido no `ultimo.json`: Açu 62 % → 68 % (+18,2 km). [Evidência](resposta-ascurra-c18-2026-09-11.md) |
| A6 | Gaspar | 16,9 | regularizar cadência (portal acessível no PC, nível ainda de 19:07 às 22:11); esclarecer legenda e o "ALERTA a 1,74 m" de 10/09 | Jefferson (celular/PC) + C10 | [ ] **C10 enviado** em 10/09/2026; aguarda resposta |
| A7 | Indaial | 16,0 | UM número: deslocamento régua COMPDEC (RN 1402-X) ↔ DCSC-00006 | COMPDEC Indaial | [ ] **C19 enviado** em 10/09/2026; aguarda resposta |
| A8 | Guabiruba | 4,8 | faixas e curso d'água da régua (ribeirão, não o Mirim) | COMPDEC Guabiruba | [ ] **C20 aprovado**, envio pendente de destinatário confirmado |
| A9 | Itajaí | pinos | critério de classificação sob influência da maré para DC-01 a DC-09; DC-10/DC-11 já têm cotas e cor habilitada | Defesa Civil de Itajaí | [ ] **C21 não enviar**, conforme instrução de Jefferson; cotas DC-01–DC-11 já cadastradas |
| A10 | Ituporanga | pino | leitura da 83250000, ou faixas da Ponte Vitório Sens amarradas à DCSC-00039 | Defesa Civil de Ituporanga / EPAGRI | [ ] **C22 enviado** em 10/09/2026; aguarda resposta |
| A11 | Brusque (já pinta) | — | régua do 8,96 m de 2023, zero da DCSC-00019, legenda vigente (4 ou 79) | Defesa Civil de Brusque | [ ] **C13 enviado** em 10/09/2026; aguarda resposta |
| A12 | Ibirama, Timbó, Rio dos Cedros, Trombudo | pinos | cota não verificada + datum da leitura DCSC (mesma pergunta de Indaial) | COMPDEC de cada uma | [ ] depois de A1–A11 |

## B. Jefferson — pendências abertas

- [x] B1 · Ofícios de A1, A2, A3, A5, A7, A8, A9, A10 redigidos: [C15–C22](oficios-b1-c15-c22.md). C15, C16, C17, C18, C19 e C22 enviados; C20 aprovado, sem destinatário confirmado; C21 excluído do envio por Jefferson.
- [x] B2 · C10 (Gaspar), C11 (Ilhota) e C13 (Brusque) enviados em 10/09/2026 às 21:05 BRT. Gmail IDs: `1a08dc8e84af8f57`, `1a08dc8ec15a69ae`, `1a08dc8f32758c36`. C14 (AlertaBlu) enviado em 10/09/2026 20:58 BRT, conforme registro anterior. Envio não encerra as dúvidas técnicas.
- [x] B3 · Consultado pelo PC em 10/09/2026, aproximadamente 22:11 BRT: NORMALIDADE, 2,58 m de 19:07; chuva atual ausente (`---`). Legenda e diagnóstico em [verificação das réguas](verificacao-reguas-2026-09-10.md). Leitura antiga continua impedindo a cor; cadência e divergência de legendas seguem abertas.
- [x] B4 · Consultado pelo PC em 10/09/2026 ~22:12 BRT: estação 4 (ANA) publica atenção >4 m/emergência >7 m; estação 79 (DCSC), atenção >3 m/emergência >5 m. São legendas diferentes; não transferir cotas entre elas. Ver [evidências](verificacao-reguas-2026-09-10.md). C13 continua aberto para confirmar a referência correta.
- [ ] B5 · VPS: `scp` da pasta `historico-dcsc` para `data/series/dcsc-zips/`, consolidador, checagem "IGUAL ao resumo do repo".
- [x] B6 · ✅ Script de download do histórico DCSC entregue em 13/09/2026, junto com o levantamento da
  API (`coletar_dcsc.py`, catálogo das 66 estações do Vale e `docs/API-DEFESA-CIVIL-SC.md`). Destrava o
  C4 e, com ele, o Indaial — a `historic` da DCSC-00006 responde normalmente.
- [~] B7 · **REESCOPADO em 10/09/2026** (`docs/eventos/2026-09-10-B7-FONTES-E-EVENTO-TAIO.md`): a Asthon retém ~6 semanas e a API de Taió só 24 h — não há fonte para 2022. Vira três: B7a confirmar o código ANA da DCSC-00041 e puxar do Hidroweb; B7b listar quais das 16 estações da cadeia existem no portal de Brusque e baixar por `baixar-historico` (chunks anuais, 2018+); B7c ✅ acumular o `dados/historico` de Taió (feito: `coleta_taio.acumula_historico`, `data/tempo-real/taio-historico.ndjson`; **provado na VPS às 20:30 BRT: 24 linhas no primeiro ciclo**). O script de download da DCSC (B6) continua valendo para as janelas que a GraphQL `historic` responde.
- [ ] B8 · "Sim" para os registros de Blumenau 2021/2022 (6,82 m em 21/01/2021 21:45; 9,41 m em 05/05/2022 02:45, régua).
- [x] B9 · C12 enviado à EPAGRI em 10/09/2026 às 21:05 BRT, na thread do C5 (`1a06001cb0e0b6ce`). Gmail ID: `1a08dc8f1ad59701`. Aguarda resposta.
- [ ] B10 · Diagnóstico da VPS: `curl -v` da estação 79 de Brusque e as cinco URLs (é bloqueio dos portais ou da VPS?).
- [ ] B11 · VPS: `apt upgrade` + `reboot` numa hora sem chuva (26 atualizações, "restart required"). **Não em 10/09 à noite**: onda descendo a bacia, Blumenau em atenção.

## C. Claude — o que faz sozinho assim que puder

- [x] C1 · Consolidador do histórico DCSC + resumo (PR #269).
- [x] C2 · Ofício C13 rascunhado (PR #270).
- [x] C3 · Oito ofícios redigidos em [C15–C22](oficios-b1-c15-c22.md), com perguntas específicas sobre régua, faixas e referência de nível. Seis enviados; C20 aguarda destinatário confirmado; C21 não deve ser enviado.
- [~] C4 · Script de download do DCSC no repo — **B6 chegou em 13/09**. A API está documentada em
  `docs/API-DEFESA-CIVIL-SC.md` e o catálogo em `data/brutos/dcsc-estacoes-2026-09-13.csv`. Falta portar
  o coletor para as convenções do repo (`comum`, `data/series/dcsc/` do consolidador, fuso de Brasília)
  com testes. **Este ambiente não alcança o host** (bloqueio de egresso) — validação só na VPS.
- [ ] C7 · ✅ **APROVADO em 14/09/2026, com condições** (Jefferson): exigir `ativo = true`, carimbo recente e
  indicadores coerentes entre si; estação desativada ou contraditória **permanece cinza**; a tela identifica
  como **classificação estadual** (não como faixa do projeto); **não libera Telegram** automaticamente.
  ✅ **Camada 1 feita em 14/09 (PR próprio):** `coleta_nivel_sc.classificar_alarmes` lê `rio_alarmes.inundacao`,
  aplica as condições (ativo=true; ≤ 1 flag; contraditório/desativado → `null` com motivo), publica
  `classificacao_estadual` no `ultimo_nivel_sc.json` e `faixa_estadual` na série; o site mostra a faixa no painel
  do bruto, rotulada "Classificação da Defesa Civil de SC", só com leitura recente. Nada entra em `leituras` → bot
  intocado por construção (teste). ✅ **Semântica validada na VPS em 14/09 (25 estações)**: `ativo` = "tem faixas
  configuradas" (Ascurra veio `ativo=false`, exatamente como a COMPDEC disse); `ativo=true` sem flag = **normal**
  (Brusque 1,73 m); `status` é rótulo (0/2/1), nunca decide. "Normal" passou a ser afirmado. Tabela em
  `docs/API-DEFESA-CIVIL-SC.md`.
  ✅ **Camada 2 feita em 14/09** (mock aprovado pelo Jefferson: tracejado + contorno tracejado no pino + rótulo;
  "normal" também pinta; correnteza parada): `mapaMotor.ts` ganha `OrigemFaixa`/`faixaEstadualDe`; trecho e pino
  tracejados, sem bloom; `textoDoPino` diz "faixa estadual"; legenda ganha a entrada. 6 testes pela cena real
  (`faixaEstadualNoMapa.test.ts`). Ganham cor: Ituporanga (alerta), Lontras, Ibirama, Botuverá (atenção), Vidal
  Ramos, Timbó, Rio dos Cedros (normal). Indaial e Ilhota seguem cinzas (o estado não tem faixas para elas).
  Regra registrada em `docs/kikikuru.md`. — **`rio_alarmes`: a faixa oficial sem precisar da cota.** A API publica, por estação, as flags
  `atencao`/`alerta`/`emergencia` já classificadas pela própria Defesa Civil de SC — no datum dela. É a
  saída para pintar cidades onde não temos cota casada com a régua, sem comparar metro com metro e sem
  inventar cota: mostra-se a faixa da fonte, dizendo de quem é. O `coleta_nivel_sc.py` ainda não lê esse
  campo, e tem o mecanismo de "tenta a query enriquecida, cai para a validada" pronto para recebê-lo.
- [ ] C8 · ⚠️ **Guarda de unidade da DCSC**: `rio_nivel` mistura régua (Indaial 6,39) com cota absoluta
  em metros acima do mar (Rio do Campo 576,22; Atalanta 453,42). O `coleta_nivel_sc.py` já descarta acima
  de 30 m. Antes de usar qualquer valor novo da rede estadual, conferir estação por estação — Ilhota
  9,96 m e Guabiruba 24,83 m passam pelo filtro e não se sabe em que zero estão.
- [ ] C5 · Cruzar `data/series/dcsc/` com `data/tempo-real/*.ndjson` da VPS (mesma rede, mesmo fuso) — depende de B5.
- [~] C6 · Com cada resposta de COMPDEC: gravar `cotas_m` + `regua_das_cotas_fonte`, teste do par, e medir o ganho em km com `conferir_cobertura.py`.
  ✅ **Ascurra (14/09/2026)**: cotas já estavam gravadas e o SITE já pintava pelo bruto (`referenciaAscurra.ts`, 12/09); faltava
  o elo no back-end — o bruto estadual sai com `usar_para_cota=False` para todas e nunca entrava no `ultimo.json`, então bot,
  extrator, vigia e `conferir_cobertura` não viam Ascurra. Achado no caminho: sem `codigo` na leitura o site veria DUAS réguas
  e apagaria a cor — o `tempoReal.ts` passou a ler `codigo` e a exceção do front virou fallback (3 testes web). Novo `coleta_estadual_com_cota.py`: allowlist por estação, só com prova ESCRITA da COMPDEC de que as
  faixas estão na escala da própria estação; `TesteOParEstaTrancadoNoEstacoesJson` cobra `codigo_dcsc`, `cotas_m.atencao`
  e `regua_das_cotas_fonte`. Ganho: +18,2 km (Açu 62 % → 68 %). Consequência a saber: Ascurra passa a valer para o
  bot de cotas como qualquer cidade com cota própria (atenção 8,50 m) — é cota municipal na régua municipal, não
  classificação estadual (C7). **Decidido em 14/09/2026 (Jefferson): Ascurra fica no Telegram**, como qualquer cidade com cota própria.

## D. Evento de 10/09/2026 — onda descendo a bacia

- [x] D1 · Evidências congeladas: os dois relatórios em `docs/eventos/`, o card + histórico de Taió com comportas (`data/brutos/taio-cards-e-historico-2026-09-10-1945.json`), a série de 48 h publicada às 19:46 (`data/brutos/evento-2026-09-10-serie-recente-1946.json`) e o CSV horário do navegador, 09/09 20h → 10/09 19h, com chuva e comportas (`data/brutos/taio-evento-2026-09-10-historico-horario.csv`).
- [x] D7 · O `coleta_taio_historico.py` do navegador NÃO entrou: faria o mesmo que `coleta_taio.acumula_historico` (no cron a cada 15 min, contra 12 h), gravando num CSV rastreado em `data/brutos/` que cresceria a cada rodada. O que ele tinha a mais entrou no parser: `chuva_mm`, `jusante_m` e `comportas_fechadas` na mesma linha horária.
- [x] D2 · Taió: mínima 2,40 m 00:13 → crista **5,48 m às 13:29** → 4,45 m 19:43. Cruzou 5,00 m ~09:45. 86,3 mm/24 h. Comportas da Oeste 7→0 às 13h. Gravado em `estacoes.json` como evidência de campo da decisão de avisar em 5,00 m.
- [x] D3 · Rio do Sul (Tito Buss): 2,96 m 00:14 → **crista 4,29 m às 16:57** → 4,20 m 19:44 → **4,15 m às 20:35, NORMAL no portal da Defesa Civil de Rio do Sul** (tela do Jefferson, 20:38 BRT; Ricardo Kanitz/Itajaí do Sul 3,04 m, BR 470/Itajaí do Oeste 4,40 m). Não chegou à atenção (4,50). A subida foi em paralelo com Taió (chuva na bacia inteira) e a barragem fechou no pico: **não serve para calibrar trânsito**. PISTA vista na barra do portal: marcas em 4,50 / 5,50 / 6,50 / **8,00** — o cadastro tem 4,5 / 5,5 / 6,5; conferir na legenda do portal o nome do degrau de 8,00 antes de gravar.
- [x] D4 · Blumenau: 2,64 m 00:05 → **crista 4,26 m (15:35–19:00)** → **4,23 m e caindo às ~20:40, ainda ATENÇÃO no site oficial da Defesa Civil de Blumenau** (tela do Jefferson: "Nível do Rio Itajaí-Açu 4,23 m ↓", situação publicada em 10/09/2026). Confirmado às 20:10 BRT que o site pinta Blumenau AMARELA — primeira cheia real em que o par régua ↔ cota do site coincide com o aviso oficial. **Origem do "2,66 m às 18:00" EXPLICADA às 20:55 BRT**: o navegador do Jefferson recebeu uma cópia do `nivel_oficial.json` cujo último ponto de `niveis` era 2026-09-09T21:00Z (18:00 BRT de 09/09) = 2,66 m. A VPS, lendo o MESMO arquivo pelo `coleta_alertablu.py`, recebeu 25 pontos horários depois desse, até 10/09 19:00 BRT = 4,26 m (série publicada às 19:46). Logo o arquivo não está congelado no servidor — a cópia do navegador estava 25 h velha, por cache do navegador ou de uma borda de CDN. **CAUSA MEDIDA na VPS às 23:45Z: o servidor entrega o arquivo com `Cache-Control: max-age=2592000` (30 dias) e `Expires` um mês à frente, com `Last-Modified` horário** — cache legítimo de um arquivo que muda a cada hora. Aviso ao AlertaBlu rascunhado (C14 em `docs/oficios-prontos.md`), aguarda "sim". O `nivel.json` de 07/11/2013 respondendo 200 é achado válido de qualquer jeito.
- [ ] D5 · Gaspar: 1,74 m às 05:53 é a única leitura que a VPS conseguiu; o navegador viu 2,58 m às 19:07 (NORMALIDADE). Sem série.
- [ ] D6 · Registrar as cristas do evento em `enchentes.json` só se o Jefferson decidir; por ora ficam nos brutos.

## E. Cheia de 11–12/09/2026 — a maior observada até aqui

Registrada em 13/09/2026 19:00 BRT, três dias depois, porque ninguém a tinha registrado.
Evidência congelada em `data/brutos/evento-2026-09-11-12-*-2200Z.json`; análise em
`docs/eventos/2026-09-11-12-CHEIA-DA-BACIA.md`.

- [x] E1 · Cristas: **Blumenau 7,87 m** (12/09 02:15, ALERTA, 13 cm abaixo da emergência; AlertaBlu
  7,86 m às 05:00 — 1 cm de diferença entre as duas fontes), **Rio do Sul 5,89 m** (11/09 23:12,
  ALERTA), **Taió 6,95 m** (12/09 03:43, 5 cm abaixo da atenção), **Brusque 4,62 m** (12/09 01:35,
  atenção), Itajaí DC-10 8,08 m e DC-11 4,37 m (sem cotas).
- [x] E2 · Estado em 13/09 19:00: **Rio do Sul 5,31 m ainda em atenção** (197 de 197 leituras da
  janela acima de 4,50); **Blumenau 4,34 m ainda em atenção**; Taió 4,46 m, Brusque 1,77 m e Gaspar
  2,72 m abaixo das faixas.
- [x] E3 · Evento inteiro extraído da VPS: **4.028 leituras de 19 réguas, 10/09 00:00 → 12/09 23:59**, em
  `data/brutos/cheia-2026-09-11-12.ndjson`. Analisado com o `extrair_picos.py`, que precisou de um
  conserto para enxergar Blumenau (E8) e revelou o desvio de 3 h (E9).
- [x] E4 · ✅ **Decidido em 14/09/2026: entram como MÁXIMOS OBSERVADOS, não como pico definitivo.** Gravados em
  `enchentes.json` os dois de Blumenau — **7,58 m às 09:00 de 01/09** e **7,87 m às 05:15 de 12/09** — com fonte
  (AlertaBlu + repasse, mesma régua ANA 83800002), horário pelo relógio do AlertaBlu, `referencia: "régua"` e
  `nota` dizendo que só viram pico depois de confirmada a cobertura do evento contra o registro oficial
  ("Enchentes Registradas" da Defesa Civil de Blumenau). Ressalva gravada no de 01/09: a série do AlertaBlu
  começa exatamente às 09:00 daquele dia. Os demais máximos que o extrator propôs (Brusque 4,88 e 4,62;
  réguas de Itajaí) ficam para a mesma regra, quando o Jefferson quiser.
- [ ] E5 · Conferir o `estado_alertas.json` da VPS: Blumenau em alerta é o caso que o bot existe para
  cobrir.
- [ ] E6 · Indaial: uma única leitura municipal no período (4,10 m em 12/09 22:00, acima do alerta
  municipal de 4,00) e nada depois. Conferir se a coleta parou ou se a fonte publica esparso.
- [x] E7 · NÃO serve para calibrar trânsito: a crista de Rio do Sul (11/09 23:12) vem ANTES da de Taió
  (12/09 03:43), que é montante — chuva na bacia inteira, como em 10/09.

- [x] E8 · **`extrair_picos.py` contava réguas por título e recusava Blumenau.** A régua chega duas vezes
  (Defesa Civil de Itajaí + AlertaBlu como resgate, ligados por `resgate_de`), virava "duas réguas na
  cidade", e a cota de `estacoes.json` — que é por cidade — era recusada: a maior cheia já medida pelo
  projeto não gerava proposta nenhuma. Agora agrupa por `comum.regua_de`, a mesma resposta que o vigia,
  o bot e o site já usam. 3 testes novos.
- [x] E9 · ✅ **FECHADO em 13/09/2026, 20:22 BRT quanto ao TAMANHO (3 h 00) e à INOCÊNCIA DO COLETOR.
  A direção reabriu às 21:30 — ver E12.** As duas fontes lidas no mesmo minuto: 4,29 m carimbado **17:15**
  no repasse e os mesmos 4,29 m carimbado **20:00** (23:00Z) no AlertaBlu. Na mesma página, no mesmo
  `parse()`, o DC-10 saiu com 12 minutos de idade — se o coletor subtraísse 3 h, o DC-10 também sairia
  errado. Medida fina na cheia inteira: somando deslocamento ao carimbo do repasse, o desvio cai a
  **1 cm em 218 pares exatamente em +3 h 00** (contra 55 cm sem deslocar) — três horas redondas, cara de
  conversão de fuso aplicada duas vezes. O valor está certo; o relógio é que mente. Nada foi "corrigido"
  no dado de ninguém. Detalhe e tabela em `docs/eventos/2026-09-11-12-CHEIA-DA-BACIA.md`.
- [x] E10 · ⛔ **C23 não sai** — decisão do Jefferson em 14/09/2026: mantida a orientação de não enviar ofício ao
  município de Itajaí (mesma do C21). O contato é por telefone (47 3228-7700). O achado do desvio de 3 h fica
  registrado (E12) e pode ser dito na ligação.
- [x] E12 · ✅ **FECHADO em 14/09/2026: o relógio certo é o do AlertaBlu; o repasse da Defesa Civil de
  Itajaí está 3 h atrás.** A física sozinha era ambígua (Indaial→Blumenau dá 0,00 h pelo repasse ou
  3,00 h pelo AlertaBlu; Blumenau→Ilhota 5,8 h ou 2,0 h; Ascurra→Indaial mede 1,17 h em ~15 km, o que
  torna 0,00 h em 25–30 km impossível, mas não decide sozinho). Decidiu a **hora de parede** de quem
  escreveu na noite de 11/09: boletim da Defesa Civil de Blumenau "das 20h" com o rio em 5,78 m (o
  repasse rotula 7,07 m às 20:05); O Blumenauense "6,32 m às 21h" (repasse: 7,31); ND Mais às 22h28
  com "6,73 m às 22h, +41 cm em 1 h" (repasse: 7,50, +10 cm/h); o secretário Menestrina à 0h30 com
  "taxa de subida caindo para ~20 cm/h, ~15 na hora seguinte" (AlertaBlu 23→00: 24 cm/h, 00→01: 18;
  repasse: 4–10). Cada leitura horária citada bate ao centímetro com o rótulo do AlertaBlu na mesma
  hora de parede. Para o repasse estar certo, a Defesa Civil de Blumenau teria de publicar 5,78 m com
  o rio a 7,07 m na régua da ponte em frente ao prédio dela. **A crista de Ilhota às 05:10 não era a
  onda de Blumenau** (Ilhota sobe cedo por chuva local e Luiz Alves; r=0,96 contra 0,99 de Indaial).
  Trava no código: E11.
- [x] E13 · ✅ **Órfãs do resgate corrigidas na VPS (14/09/2026).** Mesmo depois do E8, o extrator na VPS
  ainda via "Blumenau tem 2 réguas": 75 leituras horárias do AlertaBlu, de **01/09 09:00 a 04/09 12:00**,
  estavam sem `resgate_de` — o resgate nasceu em 01/09 (`4b96096`), mas o `coleta_niveis.py` só passou a
  gravar a marca no ndjson em 04/09 (`a5c96c3`). Correção de DADO, não de código: as 75 linhas receberam
  `resgate_de: "Blumenau"` (a relação que o `coleta_alertablu.py` sempre escreveu), com backup
  `data/tempo-real/2026-09.ndjson.bak-<carimbo>` e escrita atômica. Resultado: Blumenau é UMA régua
  (1.411 leituras), cota de atenção 4,00 m, dois eventos — **7,58 m às 09:00 de 01/09** e **7,87 m às
  05:00 de 12/09**, ambos com horário pelo relógio do AlertaBlu (E11 funcionando). Nenhum em
  `enchentes.json`: E4.
  Efeito colateral honesto: onde as duas fontes se sobrepõem, a série mesclada ziguezagueia (o repasse
  está 3 h atrás) e o extrator marca dezenas de "salto grande" em 01/09. É o desvio visto de dentro,
  marcado e não descartado; some quando a Defesa Civil de Itajaí corrigir o carimbo (C23).
- [x] E11 · ✅ `extrair_picos.RELOGIO_DEFASADO`: o horário da crista de uma régua com publicador de
  relógio defasado vem do OUTRO publicador (valor continua o máximo de todos); sem outro, a proposta
  sai sem `hora`, com `nota`, e `--escrever` recusa. 4 testes.

## Histórico

- 10/09/2026 · lista criada; medição 57% / 27%; C1 e C2 fechados.
- 10/09/2026 19:50 BRT · evento real na bacia (bloco D); B7 reescopado em B7a/B7b/B7c, B7c feito; B11 adiado; PR #272.
- 10/09/2026 20:05 BRT · CSV horário do evento e chuva/jusante/comportas fechadas no parser (D1, D7); PR #273.
- 10/09/2026 20:10 BRT · Blumenau amarela no site e em atenção no site oficial (D4).
- 10/09/2026 20:58 BRT · C14 enviado à Defesa Civil de Blumenau (B2).
- 10/09/2026 21:00 BRT · causa do 2,66 m medida: cache de 30 dias no nivel_oficial.json; C14 rascunhado (D4, B2).
- 10/09/2026 20:55 BRT · origem do 2,66 m explicada: cópia de 25 h do nivel_oficial.json no navegador; na VPS o mesmo arquivo está vivo (D4).
- 10/09/2026 20:45 BRT · picos passados em Rio do Sul (4,29 m, 16:57) e Blumenau (4,26 m, 15:35–19:00), ambos caindo nos portais oficiais (D3, D4); acumulador de Taió provado na VPS (B7c).
- 10/09/2026 · B1/C3 concluídos: oito rascunhos C15–C22. B2/B9 corrigidos com evidências de envio do Gmail; A4/A6/A11 aguardam resposta. Nenhuma cota alterada.

- 10/09/2026 ~22:11 BRT · B3 conferido diretamente no PC; seis envios registrados; C21 excluído conforme orientação do usuário; A9 corrigido conforme cadastro e lógica de maré. Ver verificação das réguas.
- 13/09/2026 19:00 BRT · cheia de 11–12/09 registrada três dias depois (bloco E): Blumenau 7,87 m em alerta, Rio do Sul 5,89 m em alerta, ainda em atenção nos dois. Evidência congelada antes de a janela de 48 h rolar.
- 13/09/2026 22:40 BRT · série completa da cheia trazida da VPS (E3); extrair_picos consertado para ver primária+resgate como uma régua (E8); achado 🔴 das 3 h de desvio em Blumenau (E9).
- 13/09/2026 ~21:00 BRT · **E9 fechado**: teste das duas fontes no mesmo minuto na VPS confirma que o carimbo 3 h atrasado de Blumenau nasce na página da Defesa Civil de Itajaí (DC-10 da mesma página com 12 min de idade); medida fina dá +3 h 00 exatos, 1 cm em 218 pares. Ofício C23 rascunhado (E10); trava no código pendente (E11). **B6 chegou**: levantamento da API GraphQL da Defesa Civil de SC (`docs/API-DEFESA-CIVIL-SC.md`), catálogo das 66 estações do Vale e `scripts/baixar_historico_dcsc.py` (14 testes, formato casado com o consolidador). Novos: C7 (`rio_alarmes`, a faixa oficial sem cota) e C8 (guarda de unidade). PR #328 mesclado.
- 14/09/2026 ~00:40 BRT · **E12 fechado a favor do AlertaBlu** pela hora de parede dos boletins e da imprensa de 11/09 (a física era ambígua). **E11 travado** no extrator. **C23 liberado** (falta o e-mail). Séries DCSC de 10 min da cheia (10 estações) trazidas para `data/brutos/dcsc-cheia-2026-09-11-12/` — primeira execução real do `baixar_historico_dcsc.py` na VPS, sem falha. Luiz Alves (DCSC-00062) vem 100 % em cota absoluta (686 implausíveis): confirma o C8.
- 14/09/2026 ~01:20 BRT · **E13**: 75 leituras órfãs do AlertaBlu (01–04/09, sem `resgate_de`) corrigidas na VPS com backup; extrator passa a ver Blumenau como uma régua e propõe 7,58 m (01/09 09:00) e 7,87 m (12/09 05:00), ambos pelo relógio do AlertaBlu. VPS em `0605166`.
- 14/09/2026 ~02:00 BRT · Caixa de e-mail conferida: nada novo desde 11/09 (Ascurra respondeu em 11/09, já incorporada; Itajaí pediu ligação em 02/09; LAI Cemaden respondida em 10/09, já documentada; sem resposta de outros 12 destinatários). **Decisões do Jefferson**: E4 sim, como máximos observados (gravados); C7 sim, com condições; **C23 não sai** (nenhum ofício ao município de Itajaí; contato por telefone); O Blumenauense e SGB/SACE são consultas que o Claude pode fazer.
- 14/09/2026 ~02:40 BRT · **Ascurra no back-end** (C6): `coleta_estadual_com_cota.py` + 7 testes; `coleta_niveis` soma a leitura da DCSC-00003 com `usar_para_cota=True` e `codigo`; site lê `codigo` e a exceção `referenciaAscurra.ts` vira fallback (550/550). Cobertura medida no `ultimo` congelado de 13/09: Açu 200 → 219 km vivos.
- 14/09/2026 ~03:30 BRT · **C7 camada 1**: classificação estadual coletada e validada (9 testes Python), exibida no painel do bruto (parser + 1 teste web); "normal" e o mapa esperam a validação de `ativo`/`status` na VPS.
- 14/09/2026 ~04:00 BRT · #333 mesclado (E4, Ascurra no back-end, correção das duas réguas, C7 camada 1). **Jefferson: Ascurra fica no Telegram.** Falta a validação do C7 na VPS (`ativo`/`status`).
- 14/09/2026 ~04:30 BRT · VPS confirma **Ascurra na coleta** (8,26 m, normal). Achado: a query enriquecida de 03/09 dava **HTTP 400** desde sempre (fallback silencioso), então `type`/`tem_nivel_do_rio`/`rio_alarmes` nunca chegaram; alinhada à forma que funcionou no script de 13/09 (`{ value }` nos objetos, sem `filter`). Validação do C7 espera a próxima execução sem o aviso.
- 14/09/2026 ~04:50 BRT · **C7 validado na VPS**: query enriquecida aceita; 25 estações classificadas; semântica de `ativo`/`status` fechada; "normal" afirmado. Camada 2 (mapa) espera o mock.
- 14/09/2026 ~05:40 BRT · **C7 camada 2** no mapa: faixa estadual tracejada, rotulada e parada, só onde não há faixa municipal. 557/557 no site.
