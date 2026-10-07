# Auditoria dos domínios usados pelo repositório — 07/10/2026

Levantamento de todos os hosts que o projeto usa:
- nos coletores, scripts e cadastros (`data/*.json`);
- nas configurações e workflows;
- no site.

Para cada host: quem o usa, para quê e se a sessão de código na nuvem o alcança. Os coletores **não** foram
alterados nesta auditoria.

## Como foi feito

- **Inventário:** URLs literais em `scripts/*.py` (fora os testes), `scripts/*.sh`, `deploy/`, `.github/workflows/`,
  `web/` (`src`, `public`, `functions`, `index.html`) e `data/*.json`. `data/brutos/` ficou de fora, porque é
  evidência guardada e nenhum script busca nada lá.
- **Função de cada host:** análise sintática (`ast`) dos scripts. Cada constante de módulo com URL foi ligada às
  funções que a usam. Os casos montados com f-string (`coleta_taio`, `coleta_asthon`, `coleta_mare_ciram`,
  `coleta_chuva_cemaden`, espelhos Overpass) foram conferidos à mão.
- **Acesso:**
  - um pedido `GET` por endereço **real** usado pelo código, sem seguir redirecionamento automático (cada salto
    registrado);
  - User-Agent do projeto, TLS verificado (Blumenau com o intermediário de `scripts/certs/`), sem `verify=False`;
  - "bloqueado" = o proxy da sessão respondeu 403 ao `CONNECT`, registrado em `__agentproxy/status`.
- **Duas rodadas:**
  - **antes:** com a política de rede original;
  - **depois:** com os domínios que o Jefferson liberou no ambiente, no mesmo dia.
- **Domínios autorizados:** a lista de domínios liberados não fica visível de dentro da sessão. "Autorizado" aqui
  quer dizer "o proxy deixou abrir o túnel".

Legenda da coluna de acesso:
- **ok**: respondeu.
- **bloq.**: política de rede da sessão.
- **servidor**: o túnel abriu, mas o servidor derrubou a conexão ou não respondeu em 25 s. Não é a política.

## 1. Fontes de dados (nível, chuva, maré, barragens)

| Domínio | Arquivo → função | Dado | Antes | Depois |
|---|---|---|---|---|
| `monitoramento.defesacivil.itajai.sc.gov.br` | `coleta_itajai_portal.py` → `coletar()`/`parse()`; `coleta_niveis.py` → `baixar_niveis()`/`coletar_fonte_itajai()`; `capturar_fontes.py` (`ALVOS`, municípios 1–4) | nível das 11 réguas DC de Itajaí; PADKND de Blumenau | bloq. | **ok** |
| `monitoramento.defesacivil.sc.gov.br` | `coleta_nivel_sc.py` → `_post()`; `coleta_chuva_sc.py` → `baixar_estacoes()`; `coleta_estadual_com_cota.py` → `coletar()`; `baixar_historico_dcsc.py` → `_transporte_requests()`; `gaspar_estadual.py` → `consultar()` | nível e chuva da rede estadual (GraphQL) | ok | ok |
| `defesacivil.blumenau.sc.gov.br` | `coleta_alertablu.py` → `baixar()`; `capturar_fontes.py` | nível horário do AlertaBlu (`nivel_oficial.json`) | ok | ok |
| `public.asthon.com.br` | `coleta_asthon.py` → `baixar()`/`coletar()`; `coleta_barragens.py` → `coletar()`; `conferir_par_regua.py` → `conferir()` | nível de Rio do Sul e Vidal Ramos; barragens | bloq. | **ok** |
| `api-scr.uniparking.com.br` | `coleta_taio.py` → `coletar()`/`baixar_json()` | nível de Taió e comportas da Barragem Oeste | bloq. | **ok** |
| `defesacivil.gaspar.sc.gov.br` | `coleta_gaspar.py` → `analisar()`/`analisar_estacao()`/`permitido()`; `vigiar_cadencia_gaspar.py` → `baixar()`; `gaspar_actions.py` | nível de Gaspar | ok, instável | ok |
| `resources.cemaden.gov.br` | `coleta_chuva_cemaden.py` → `baixar_estacoes()` | chuva (pluviômetros CEMADEN) | bloq. | **ok** |
| `ciram.epagri.sc.gov.br` | `coleta_mare_ciram.py` → `buscar()`/`coletar()` | maré (marégrafos EPAGRI/CIRAM) | ok | ok |
| `defesacivil.itajai.sc.gov.br` | `coleta_chuva.py` → `coletar()`; `coleta_mares.py` → `main()`; `coleta_itajai.py` → `coletar()` (legado) | chuva e maré de Itajaí | ok, **fonte morta** (§5) | idem |
| `docs.google.com` | `coleta_indaial.py` → `motivo_para_nao_baixar()` | só o `robots.txt`, que proíbe o documento de Indaial | bloq. | bloq. |
| `www.ituporanga.sc.gov.br` | `capturar_fontes.py` (`ALVOS`); não há coletor | nível de Ituporanga | bloq. | **ok** |
| `alertablu.blumenau.sc.gov.br` | `sonda_cotas_ruas.py` → `mostrar_robots_blumenau()`; `sonda_fontes2.py`; links do site | sondas e link de referência | bloq. | bloq. |

Hosts adicionais que o portal novo de Itajaí chama, lidos no código da própria página
(`defesacivil.itajai.sc.gov.br/assets/index-*.js`), sem nenhum endereço presumido:
- `https://monitoramento.defesacivil.itajai.sc.gov.br/api/v1`, com os caminhos:
  - `/municipios`, `/mapa`, `/mapa/{id}`;
  - `/rios`, `/rios/{id}`, `/rios/{id}/series-12h`;
  - `/chuvas`, `/chuvas/{id}`, `/chuvas/{id}/series-12h`;
  - `/barragens`, `/barragens/{id}`, `/barragens/{id}/series-12h`;
  - `/meteorologia`, `/meteorologia/{id}`;
  - `/situacao-atual`, `/alertas/ativo`, `/alerta-sms`.
- `https://monitoramento.defesacivil.itajai.sc.gov.br/data/current/app.json` (instantâneo).
- `https://api-portal.itajai.sc.gov.br/public/portaladm-pmitajai`: notícias do portal da Prefeitura. Não é dado de
  rio. Depois da liberação responde com três redirecionamentos dentro do próprio host.
- A página de **marés** passou para `https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/mares`. O
  código da página **não** traz endpoint de API para a maré, e nenhum foi inventado.

Redirecionamentos encontrados nos endereços dos coletores:
- `defesacivil.gaspar.sc.gov.br/robots.txt` → 302 para `/404`, no mesmo host. Não há `robots.txt`; nenhum host novo.
- Os demais endereços de coleta responderam sem redirecionamento.
- `coleta_indaial.py` nunca baixa o documento (o `robots.txt` proíbe), então não precisa do host de download do
  Google.

## 2. Documentos e cadastros baixados por script

| Domínio | Arquivo → função | O que baixa | Antes | Depois |
|---|---|---|---|---|
| `arcgis.itajai.sc.gov.br` | `baixar_itajai_arcgis.py` → `main()`/`permitido()`/`url_da_pagina()`; `coleta_abrigos_itajai.py` → `baixar()`; `sonda_cotas_ruas*.py` | camadas oficiais de Itajaí (manchas, abrigos, ruas) | bloq. | **ok** (`robots.txt` = 404) |
| `defesacivil.riodosul.sc.gov.br` | `importar_cotas_rio_do_sul.py` → `baixar_pacote()` | cotas de rua de Rio do Sul | ok | ok |
| `defesacivil.gaspar.sc.gov.br` | `importar_gaspar_enchentes.py` → `main()`/`monta()` | tabela de enchentes de Gaspar | ok | ok |
| `defesacivil.blumenau.sc.gov.br` | `importar_manchas_blumenau.py` (lê arquivo local; a URL é metadado) | manchas de inundação | ok | ok |
| `raw.githubusercontent.com` (geoitajai/sie) | `baixar_manchas_itajai.py` → `main()` | manchas do GeoItajaí | ok | ok |
| `atlasdigital.mdr.gov.br` | `atlas_desastres.py` → `descobrir_url()`/`baixar()` | CSV consolidado do S2ID | bloq. | servidor (reset) |
| `www.ana.gov.br` | `ana_hidroweb.py` → `base_url()` | séries históricas (API HidroWeb) | bloq. | servidor (301, depois sem resposta) |
| `telemetriaws1.ana.gov.br` | `ana_inventario.py` → `busca()`/`main()` | inventário de estações. **O código usa `http://`**, que o proxy desta sessão não transporta | bloq. | servidor (sem resposta em HTTPS) |
| `overpass-api.de`, `overpass.kumi.systems`, `overpass.private.coffee` | `baixar_vao_canhanduba.py` → `buscar()`; reaproveitado por `baixar_tracado_hercilio.py`, `baixar_tracados_afluentes.py`, `baixar_rios_municipio.py` (rodam no Actions) | traçados dos rios (OSM) | bloq. | servidor (reset/sem resposta) |

`importar_manchas_ituporanga.py` (`www.google.com/maps/d`) e `extrair_blumenau_2014.py` (`farolblumenau.com`) só
guardam a URL como origem: leem arquivo local e não fazem pedido.

## 3. Documentos oficiais citados nos cadastros

Nenhum script os baixa. Estão nos campos `fonte`, `fonte_cotas`, `fonte_plano`, `fonte_portal`, `cotas_pendencia` e
`url` de `estacoes.json`, `enchentes.json`, `cotas-ruas.json`, `historico-chegada-itajai.json`, `hidraulica.json`,
`abrigos-itajai.json` e `eventos-pendentes-regua.json`. Servem para **reabrir a fonte** antes de mexer num número.

| Situação | Domínios |
|---|---|
| ok (antes e depois) | `riodoscedros.sc.gov.br`, `defesacivil.taio.sc.gov.br`, `ilhota.sc.gov.br`, `defesa-civil-rdc.webnode.page` |
| ok depois da liberação | `labgeo.furb.br`, `www.univali.br` (`biblioteca.univali.br` abre, mas o PDF citado dá 404) |
| bloqueados | `www.aguas.sc.gov.br`, `indaial.atende.net`, `files.abrhidro.org.br`, `s3cache.dom.sc.gov.br`, `www.taio.sc.gov.br`, `www.trombudocentral.sc.gov.br`, `www.gaspar.sc.gov.br`, `amve.org.br`, `www.ensinosuperior.sed.sc.gov.br`, `www.snirh.gov.br`, `openjicareport.jica.go.jp`, `drive.google.com`, `www.google.com` |
| o servidor derruba ou falha | `www.defesacivil.sc.gov.br` e `defesacivil.brusque.sc.gov.br` (reset); `ceops.furb.br` (citado em `http://`; 403 antes, 503 depois); `libgeo.univali.br` (erro de TLS do próprio servidor) |

Os sites de imprensa citados em `enchentes.json` (NSC, ND+, O Município, Diarinho etc.) não entram: não são fonte de
coleta nem documento oficial.

## 4. Recursos visuais e infraestrutura

| Domínio | Onde | Tipo | Antes | Depois |
|---|---|---|---|---|
| `tile.openstreetmap.org` | `web/src/logica/tiles.ts`, `MapaManchas.tsx`, `MapaCotasItuporanga.tsx`, `web/index.html` (preconnect) | **visual**: fundo do mapa no navegador | bloq. | **ok** |
| `server.arcgisonline.com` | `web/src/logica/tiles.ts`, `MapaManchas.tsx` | **visual**: fundo escuro e satélite | bloq. | **ok** |
| `raw.githubusercontent.com` (branch `tempo-real`) | `web/src/dados/tempoReal.ts`, `serie.ts`, `nivelSc.ts`, `barragens.ts`, `publicacao.ts`, `web/public/sw-regras.js`; `conferir_publicado.py` → `medir()`; `gaspar_actions.py` → `ler_publicado()` | infraestrutura: o site lê o tempo real | ok | ok |
| `api.github.com` | `web/src/dados/publicacao.ts`, `sw-regras.js`; `conferir_publicado.py` | infraestrutura | ok | ok |
| `api.telegram.org` | `bot.py` → `rodada()`/`registrar_menu()`/`descartar_pendentes()`; `notificador.py` → `_postar()` | infraestrutura (VPS) | bloq. | bloq. |
| `api.cloudflare.com` | `autorizar_email.py` → `chamada_http()` | infraestrutura (Access) | bloq. | bloq. |
| `enchentes.premercadosc.com` | `alerta_cotas.py` → `texto_aviso()` | endereço do site no aviso | bloq. | bloq. |
| `haohmarusc-glitch.github.io` | `bot.py` → `ajuda()`/`resposta_previsao()` | endereço do site no bot | bloq. | bloq. |
| `api.anthropic.com` | `web/functions/api/chat-ia.ts`, `chat-classificar.ts` (SDK, endereço padrão) | infraestrutura (Cloudflare Functions) | — | — |

Também estão no código, mas não são consultados por máquina: `wa.me` (compartilhar no WhatsApp),
`geoitajai.github.io`, `sites.google.com`, `rigeo.sgb.gov.br` e os links de fonte nas telas.

Nos workflows, a rede vem de `actions/*`, `pip` e `npm`. Na CI, o `npx playwright install` também baixa o Chromium
de um host definido pelo próprio Playwright, não pelo repositório.

## 5. Achado: chuva e maré de Itajaí apontam para uma fonte morta

`defesacivil.itajai.sc.gov.br` responde **HTTP 200** com o mesmo HTML de 641 bytes (`<div id="root">`, uma casca
de aplicação) para os três endereços que os coletores leem:
- `/monitoramento/chuvas`, lido por `coleta_chuva.py`;
- `/monitoramento/ajax/mares.php`, lido por `coleta_mares.py`;
- `/monitoramento/nivel-rios`, lido por `coleta_itajai.py`, o legado.

O status 200 esconde a falha. Os dados foram para a API do portal novo (§1), que a sessão alcança desde a
liberação. A investigação e o conserto de chuva e maré seguem em trabalho separado.

## 6. Domínios ainda bloqueados nesta sessão (depois da liberação)

- **Usados por coletor:**
  - `docs.google.com`: só o `robots.txt` de Indaial; o documento continua proibido pelo próprio `robots.txt`.
  - `alertablu.blumenau.sc.gov.br`: sondas.
- **Infraestrutura:** `api.telegram.org`, `api.cloudflare.com`, `enchentes.premercadosc.com`,
  `haohmarusc-glitch.github.io`.
- **Documentos oficiais:** a linha "bloqueados" do §3.
- **Liberados, mas o servidor não respondeu daqui:** `atlasdigital.mdr.gov.br`, `www.ana.gov.br`,
  `telemetriaws1.ana.gov.br`, os três espelhos Overpass, `www.defesacivil.sc.gov.br` e
  `defesacivil.brusque.sc.gov.br`. Precisam de nova tentativa, não de liberação.

## 7. Trabalho pausado: Blumenau de 5 minutos (PADKND)

A fonte de 5 min de Blumenau foi pausada para esta auditoria. Fica **separada** deste PR.

- **Branch:** `claude/projeto-critico-seguranca-ubkk9l-blumenau5`, criado de `origin/main` em f34fc03, sem
  commits próprios.
- **Stash:** `stash@{0}`, mensagem "wip blumenau 5min (pausado para auditoria de domínios)", commit `0dac622`.
  Existe só no contêiner desta sessão. Cópia do diff na área de rascunho da sessão (`blumenau5-wip.patch`).
- **O que contém:**
  - `parse_blumenau()` e `conferir_com_alertablu()` em `scripts/coleta_itajai_portal.py`;
  - `baixar_nivel_blumenau_5min()` em `scripts/coleta_niveis.py`;
  - 17 testes em `scripts/teste_coleta_itajai_portal.py` (`TestBlumenauDe5Minutos`);
  - o título `Blumenau (PADKND)` em `web/src/logica/camadaBlumenau.ts` e no teste dele.
- **Teste pendente:** `TestBlumenauDe5Minutos.test_prova_velha_nao_vale` falha.
  - **Causa:** erro no próprio teste, não no código. Cortar o AlertaBlu às 17:00Z deixa só dois pares (16:00 e
    17:00) com a série da PADKND, que começa às 15:05Z. O motivo devolvido é "mínimo", não "prova velha".
  - **Conserto:** cortar às 18:00Z, que dá três pares a ~9 h da leitura.
  - Os outros 59 testes do arquivo passam.
- **Para retomar:** `git checkout claude/projeto-critico-seguranca-ubkk9l-blumenau5 && git stash pop`. Depois:
  - corrigir o teste;
  - testar `coleta_niveis`;
  - atualizar docs e README;
  - rodar as suítes;
  - abrir o PR rascunho.
