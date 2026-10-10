# O que depende do Jefferson — lista única de 08/10/2026

Em 08/10/2026 os itens abertos do README foram conferidos um a um, e os que só pediam código ou dado já foram
fechados (#517). O que sobra depende de uma decisão, de um acesso que só o Jefferson tem ou da resposta de um órgão.
Esta página junta tudo, em ordem de prioridade, com a recomendação e o lugar onde está o detalhe. Ela substitui a
seção "O que depende do Jefferson" de `docs/DECISOES-2026-10-04.md` como lista atual.

## 1. Segurança dos avisos (afeta quem recebe o Telegram agora)

| # | decisão | recomendação | detalhe |
|---|---|---|---|
| 1.1 | **DC-05 e DC-08 estão acima da cota de atenção, travadas** (sem aviso e sem cor). Em 07/10, a DC-08 marcou 2,28 m (atenção 1,80) e a DC-05 1,71 m (atenção 1,60). O motivo da trava era a própria cheia de 01/09. | destravar a DC-05 com histerese; a DC-08 depois de escolher a cota (PLANCON 1,80 ou portal 1,70) | `docs/PROPOSTA-TRAVA-ESTUARIO-2026-10-08.md` |
| 1.2 | **DC-11 manda mensagem a cada maré alta** quando o rio está perto de 3,00 m (112 em 36 dias) | histerese de 0,30 m na descida, só para ela (52 em 36 dias, sem atrasar a subida); sem travar e sem descontar a maré | `docs/PROPOSTA-DC11-AVISOS-2026-10-08.md` |
| 1.3 | DC-03 e DC-06 travadas sem precisar | destravar com histerese (12 e 0 mensagens em 36 dias, todas em cheia) | proposta do estuário |
| 1.4 | Ribeirões que ganharem cor: o curso **corre** no mapa? | decidir junto com 1.1 (o teste `afluenteNaoCorre.test.ts` obriga) | proposta do estuário, item 5 |

## 2. Publicação (PRs prontos, esperando o "pode")

**Feito em 08/10/2026:** os três foram mesclados, nesta ordem, e o `deploy.sh` rodou na VPS. A DC-00 entrou na
chuva publicada na coleta das 06h16 UTC (03h16 em Brasília).

| # | PR | o que entra | situação do CI |
|---|---|---|---|
| 2.1 | [#517](https://github.com/haohmarusc-glitch/enchentes-vale-itajai/pull/517) | DC-00 na chuva, C33–C35, as propostas e a limpeza do README | verde; depois do merge, `deploy.sh` na VPS para a DC-00 |
| 2.2 | [#518](https://github.com/haohmarusc-glitch/enchentes-vale-itajai/pull/518) | Monitor: vínculo traçado × cidade × régua (Ituporanga e afluentes) | verde |
| 2.3 | [#519](https://github.com/haohmarusc-glitch/enchentes-vale-itajai/pull/519) | Monitor: painel das barragens | verde; só a prévia do Cloudflare falhou ("Retry deployment" no painel) |

#518 e #519 mexem nos mesmos arquivos do Monitor: o que entrar por segundo precisa trazer o `main`.

## 3. Envios (rascunhos no Gmail, nenhum enviado)

| # | ofício | para | pergunta |
|---|---|---|---|
| 3.1 | C32 | Defesa Civil de Rio dos Cedros | confirmação das cotas na DCSC-00011 |
| 3.2 | C33 | EPAGRI/CIRAM | referência vertical da maré observada (sem ela, a tela segue "referência pendente") |
| 3.3 | C34 | ANA (hidro@ana.gov.br) | 13 leituras com erro de digitação no HidroWeb; série da 83900000 depois de 03/2022 |
| 3.4 | C35 | Defesa Civil de Gaspar (conversa do C10) | cadência da estação 21 |

Textos em `docs/oficios-prontos.md`. Aguardando resposta:
- C11 (Ilhota)
- C13 (Brusque)
- C24 (Cemaden, no Informa.BR)
- C27 (Timbó)
- C28 (Trombudo Central)
- C30 (Apiúna)
- C31 (INMET)

Ibirama (C26) e Rio dos Cedros (C29) já responderam.

## 4. Configuração que só o Jefferson faz (Cloudflare e servidor)

| # | o quê | onde |
|---|---|---|
| 4.1 | variável `ADMIN_EMAILS` no Cloudflare Pages (registro de acessos) | `docs/PUBLICACAO-E-ACESSO.md`, "Registro de acessos" |
| 4.2 | KV `CHAT_NAO_ENTENDI` (contagem das perguntas que o chat não entende) | `docs/PUBLICACAO-E-ACESSO.md` |
| 4.3 | chave `ANTHROPIC_API_KEY` e limite mensal: liga o chat com IA, o piloto do classificador e a prova de 34 perguntas | `docs/CHAT-IA.md` e `docs/PUBLICACAO-E-ACESSO.md`, "Chat com IA" |
| 4.4 | ~~data da volta da DCSC-00029 (Guabiruba) ao zero local~~ **resolvido em 10/10/2026 sem a VPS:** não houve volta; a DCSC reprocessou o histórico (ver 5.9) | `docs/GUABIRUBA-DCSC-00029-2026-10-10.md` |
| 4.5 | coletor de Gaspar no Actions: merge, permissão do token, disparo à mão, `pull` na VPS | `docs/DECISOES-2026-10-04.md` |

## 5. Dados que só entram por decisão

| # | decisão | o que existe hoje | detalhe |
|---|---|---|---|
| 5.1 | cotas de DC-07 e DC-08: PLANCON v17 ou portal | divergem (DC-07 no alerta e na emergência; DC-08 na atenção) | `estacoes.json`, `cotas_conferencia_2026_09_13` |
| 5.2 | código ANA de Brusque (83900000) conferido? | a estação fica a 51 m da DCSC-00019, que desde 03/10 é a régua de Brusque; nas cheias com dia no cadastro, a leitura da ANA bate ao centímetro com a municipal. A regra de 04/10 é "nenhum `verificado: true` novo" | `docs/HIDROWEB-MIRIM-2026-09-22.md`, `docs/INVENTARIO-ANA.md` |
| 5.3 | código ANA de Rio do Sul: 83300200 (Açu) ou 83094000 (Oeste, a 35 m da DCSC-00013)? | conflito registrado em `codigo_ana_ressalva` | `docs/INVENTARIO-ANA.md` |
| 5.4 | Itajaí no histórico de cheias | 2 registros, sem régua; nenhum pico numa régua DC | README, "O bloco de cheias não tem o que mostrar justamente em Itajaí" |
| 5.5 | "quanto do nível é maré" no painel das réguas de Itajaí com correlação ≥ 0,8 | os fatores por régua estão medidos (36 dias) | `docs/ANALISE-CHEGADA-ITAJAI-2026.md`; proposta do estuário |
| 5.6 | Brusque, "Quanto falta": tirar os picos anteriores a 2019 | a opção B só rotula | `docs/DECISOES-2026-10-04.md` |
| 5.7 | Ilhota e Taió sem `regua_das_cotas` | o validador acusa as duas | README |

## O que não depende de decisão e está parado por fonte

- **Gaspar:** a estação 21 publica de forma irregular (mediana de 6 h entre leituras; vazio de até 74 h). Depende do C35.
- **Vidal Ramos:** sem leitura municipal desde 11/09 (saiu da Asthon); segue só a estadual DCSC-00024.
- **Indaial:** o documento municipal parou em 12/09; não há fonte autorizada.
- **DC-02:** a série fica parada; não serve como régua até alguém explicar o porquê.

## Atualização de 10/10/2026 (tarde)

Mesclados e em produção: #539 (DC-03 e DC-06 destravadas, DC-07 com as cotas do portal provisórias, liberação após
6 h na DC-03 e na DC-11, Murta pintando pela DC-07), #540 (Itajaí do Sul e do Oeste em Rio do Sul) e #541
(auditoria com a chuva de 06–07/10). Saem da lista os itens 1.2a, 1.3, 1.5 e 5.1. O item 4.4 também sai: resolveu-se
pelo acervo do Actions, sem comando na VPS.

| # | decisão | recomendação | detalhe |
|---|---|---|---|
| 5.9 | **Guabiruba (DCSC-00029):** a API serve hoje o histórico no zero local desde pelo menos 11/07. O download de 10/09 tinha altitude nas mesmas datas. Manter o trecho reprocessado (19/07 →) na série consolidada? | sim, como série própria, sem emendar no "antes" de 01/04 enquanto o zero não for provado | `docs/GUABIRUBA-DCSC-00029-2026-10-10.md` |
| 5.10 | Perguntar à DCSC qual conta converteu o histórico de 01/04 em diante | só com a resposta "antes" e "depois" viram uma série única; nada rascunhado | idem |

## Atualização de 10/10/2026

**Correção:** os itens 1.1 e 1.2 já estavam resolvidos. O PR #520, mesclado em 08/10, destravou DC-05 (histerese
0,10 m) e DC-08 (atenção provisória 1,70 m) e pôs histerese de 0,30 m na DC-11. A auditoria pedida em 10/10
(`docs/AUDITORIA-TRAVAS-ITAJAI-2026-10-10.md`) mede o que está ligado e o que falta:

| # | decisão | o que a série mostra (30/08–05/10) |
|---|---|---|
| 1.2a | DC-11: soltar a faixa depois de T h abaixo da cota? | a histerese preserva toda subida de faixa e todo início de episódio (8 de 8 na mesma leitura); some a volta à mesma faixa após descida rasa, até 8,3 h abaixo da cota. Soltar após 6 h: 61 mensagens em vez de 52 |
| 1.3 | destravar DC-03 e DC-06 | o motivo da trava não se sustenta: a maré as leva a 0,5 e 0,4 m da atenção, nunca à cota; DC-03 só passou em cheia (20 → 11 mensagens com histerese), DC-06 nunca |
| 1.5 / 5.1 | DC-07: alerta e emergência do Plano (1,35 / 1,65) ou do portal (1,40 / 1,50) | régua e zero confirmados; atenção 1,00 igual nas duas fontes; mesmas 10 mensagens com qualquer das duas |
| 5.1 | DC-08: 1,70 (portal) ou 1,80 (Plano) | mesma régua; só o 1,70 se prova no zero das leituras; mesmas 23 mensagens; recomendação: manter o 1,70 provisório |

## Atualização de 08/10/2026 (tarde)

Mesclados e em produção no mesmo dia (todos pelo Jefferson, exceto o #525 a pedido dele): #523 (linha estadual
contínua), #524 e #525 (divergência de Ituporanga explicada e provada), #526 (Canhanduba pinta pela DC-08),
#527 (CI: `concurrency` por evento), #528 (rótulo "Classificação estadual nesta estação"), #529 (Ituporanga: régua a
jusante da Barragem Sul e régua do Centro), #530 (proposta do Atlas), #531 (traçado da Murta contínuo) e #532
(Centro de Ituporanga pelo Actions, porque a Prefeitura recusa a VPS). O `deploy.sh` rodou depois do #525 e do #532;
a publicação das 17:32 UTC já trouxe `ultimo_ituporanga_centro.json` via Actions.

O item 4.5 (coletor de Gaspar no Actions) está em operação: o branch `coleta-gaspar` recebe leituras (última
publicação 16:50 UTC de hoje).

O que **entrou** na lista de decisões:

| # | decisão | recomendação | detalhe |
|---|---|---|---|
| 1.5 | **DC-07 (Murta):** cota do PLANCON v17 ou do portal (é o 5.1), e destravar? O traçado já é contínuo da DC-07 à foz e o trecho do vínculo está delimitado: DC-07 → DC-09, 4,86 km. | decidir a cota primeiro; com `alerta_automatico: true`, o vínculo rascunhado entra num PR pequeno, **parado** como o Canhanduba (1.4 continua valendo) | `docs/VAO-MURTA.md` |
| 5.8 | **Atlas de Desastres pelo Actions:** autorizar a 1ª rodada (sonda + `--dry-run`, sem trocar o `User-Agent`); se o runner passar, cadência mensal ou só manual; onde apontar as lacunas novas | sonda primeiro; mensal (dia 10) se passar; lacunas num doc por rodada | `docs/PROPOSTA-ATLAS-ACTIONS-2026-10-08.md` |
| 3.5 | **Cotas da régua do Centro de Ituporanga** na mesma régua: a pergunta à Defesa Civil já foi enviada e reforçada; sem resposta, a régua fica sem cor | aguardar; nada a enviar | `docs/ITUPORANGA-CENTRO.md` |

O que **saiu**: 2.1–2.3 (publicados) e 4.5 (em operação). Fora desta lista, não há pendência que a sessão feche
sozinha: os avisos do validador (47, ver README) pedem conferência na fonte, e as demais dependem de resposta
externa (C11, C13, C24, C27, C28, C30, C31) ou de envio (C32–C35, rascunhos no Gmail, nenhum enviado).
