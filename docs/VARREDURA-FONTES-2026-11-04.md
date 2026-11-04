# Varredura de fontes novas — 04/11/2026

Pedido do Jefferson: "faça uma nova varredura na web e procure novas fontes para o projeto". Feita deste ambiente,
com busca na web e leitura (`GET`, `User-Agent` do projeto, `robots.txt` respeitado) das páginas que o proxy deixou
abrir. **Nada entrou em `data/`**: este documento só separa o que é novo do que o projeto já conhece, diz o que cada
fonte publica e o que falta conferir. Fonte nova entra por decisão do Jefferson, com a prova aberta.

**Limite desta rodada:** a política de saída deste ambiente recusa vários hospedeiros (403 no CONNECT ou DNS sem
resposta): `www.cemaden.gov.br`, `mapservices.cemaden.gov.br`, `gsc.cemaden.gov.br`, `resources.cemaden.gov.br`,
`geoportal.sgb.gov.br`, `monitora.furb.br`, `data.mendeley.com`, `mapping.emergency.copernicus.eu`,
`alertablu.blumenau.sc.gov.br`; `www.defesacivil.sc.gov.br` caiu no meio da conexão três vezes (e devolveu 503 ao
agente de leitura). O que está marcado **"não conferido daqui"** precisa da VPS ou do navegador do Jefferson.

## Resumo

| # | Fonte | O que é | Situação | Vale para |
|---|---|---|---|---|
| 1 | CEMADEN — serviço de camadas do Mapa Interativo | endereços do serviço (`MapaInterativoWS`), do WMS e dos gráficos por PCD, lidos no JavaScript do mapa | página e scripts lidos daqui; **serviço não conferido daqui** | PCDs hidrológicas (nível) e pluviômetros, por código |
| 2 | FURB — GeoNode `monitora.furb.br` | portal de camadas geoespaciais da FURB (apareceu `geonode:hidrografia_epagri`) | **não conferido daqui** (DNS) | hidrografia, possíveis manchas/cotas de Blumenau |
| 3 | Mendeley Data — "Histórico de enchentes em Blumenau" | tabela pública de eventos com data e nível, compilada da Defesa Civil municipal | **não conferido daqui** | cruzamento de `enchentes.json` (Blumenau) |
| 4 | SGB/CPRM — produtos vetoriais por cidade | Brusque (suscetibilidade 1:50.000, 2015, SIG), Gaspar (setorização de risco, 2017), Blumenau (carta de suscetibilidade); relatórios IDF 2013 (Taió, Gaspar, Blumenau, Ilhota) | só Ascurra está no projeto; **não conferido daqui** | contexto de risco na "minha rua"; chuva de projeto |
| 5 | Defesa Civil de SC — WordPress (`wp-json`, `feed`) | possível feed estruturado de avisos e notícias | **não conferido** (503 / conexão caiu) | avisos oficiais no chat e na tela de fontes |
| 6 | Copernicus GFM (Sentinel-1) | manchas de inundação automáticas, por satélite, de eventos passados | **não conferido daqui** | extensão das cheias de out/nov 2023 para comparar com as manchas de Itajaí |
| 7 | Defesa Civil de Itajaí — canais oficiais | canal no WhatsApp, X e Instagram, lidos no pacote JavaScript do site oficial | links lidos daqui | tela "Fontes" (onde o morador acompanha o aviso oficial) |

O que a busca **confirmou que não existe** ou que **o projeto já tem** está nas seções 3 e 4.

## 1. CEMADEN — o serviço por trás do Mapa Interativo

O projeto já usa o cadastro do Mapa Interativo para a chuva (`docs/rede-observacional-cemaden.md`: 137 pluviômetros
ativos, 18 hidrológicas das quais 6 operacionais, Pomerode `421320321H` operacional) e tem o pedido C24 no Informa.BR
pedindo o acesso programático ao **nível** das PCDs hidrológicas. O que é novo nesta rodada são os **endereços que o
próprio mapa usa**, lidos em `https://mapainterativo.cemaden.gov.br/js/script.js` e `js/interativo.js` (página e
scripts abertos daqui, HTTP 200):

| recurso | endereço | observação |
|---|---|---|
| camadas de estações | `https://mapservices.cemaden.gov.br/MapaInterativoWS/resources/layer/id/<n>` | os `<n>` ficam no JS; o host **não abre daqui** |
| camadas antigas | `http://sjc.salvar.cemaden.gov.br/WebServiceSalvar-war/resources/layer/id/<n>` | mesmo serviço, host antigo |
| WMS | `https://gsc.cemaden.gov.br/geoserver/cemaden_dev/wms` | GeoServer; `GetCapabilities` listaria as camadas; **não abre daqui** |
| gráfico por PCD | `.../graficos/interativo/grafico_CEMADEN.php?idpcd=` e `grafico_Acqua_CEMADEN.php?idpcd=` | série recente por estação, em HTML |
| download | `https://mapainterativo.cemaden.gov.br/download/download_form.php?type=3|5|10` | por UF, município, mês e ano, **com captcha** (pluviômetro e "E. Hidrológicas") |

**O que conferir na VPS (só leitura):** `curl` no `layer/id/<n>` com os `<n>` do JS e no `GetCapabilities` do WMS; filtrar
UF = SC e os municípios da bacia; ver se as PCDs hidrológicas trazem nível e em que zero. Regra que vale desde já: nível
de PCD do CEMADEN é **régua própria**, como a rede estadual — nunca se compara com cota municipal sem vínculo escrito.

## 2. FURB — GeoNode `monitora.furb.br`

Apareceu na busca como `https://monitora.furb.br/layers/geonode:hidrografia_epagri/metadata_detail`: um GeoNode da FURB
com camada de hidrografia da Epagri. GeoNode costuma expor WMS/WFS e licença por camada. Pode guardar as camadas da
carta-enchente do CEOPS (os 1.851 pontos de 2011 de `docs/fontes-academicas.md` e `docs/MDT-SC-E-CARTA-ENCHENTE.md`),
que o projeto só conhece por artigo. **Não conferido daqui** (DNS recusado). Próximo passo: abrir no navegador, listar
as camadas com "enchente", "inundação", "cota", "Blumenau" e ler a licença antes de qualquer uso.

## 3. Mendeley Data — "Histórico de enchentes em Blumenau"

`https://data.mendeley.com/datasets/cj64gycsw8` — descrito pela busca como tabela pública com os principais eventos de
Blumenau (data e nível do Itajaí-Açu), compilada de dados da Defesa Civil municipal. **Não conferido daqui.** Serve
para cruzar os registros de Blumenau em `enchentes.json`, com a regra da referência altimétrica (régua antiga, IBGE,
régua de hoje) em mente: a tabela precisa dizer em que régua está cada número, senão vira divergência, não registro.
Confiança, se entrar: `media` (compilação) ou a da fonte primária que ela citar.

## 4. SGB/CPRM — produtos por cidade que o projeto ainda não leu

O projeto tem a carta de suscetibilidade de Ascurra (`docs/ascurra-fontes-site.md`). A busca mostrou, no RIGEO e no
geoportal do SGB (hosts **não conferidos daqui**):

- **Brusque:** carta de suscetibilidade 1:50.000 (2015) com vetores (`sig_brusque_sc_suscet.zip`) e base cartográfica;
- **Gaspar:** "Setorização de áreas em alto e muito alto risco a movimentos de massa, enchentes e inundações" (2017), com
  vetores; e o relatório IDF de 2013;
- **Blumenau:** carta de suscetibilidade a movimentos de massa e inundação; relatório IDF 2013 (que diz que a estação
  pluviométrica 02649007 é operada pela Epagri);
- **Ilhota e Taió:** relatórios IDF 2013;
- **geoportal.sgb.gov.br:** pasta `hidrologia` com um "Visualizador das Manchas de Inundação" (há serviços de manchas
  para outras cidades, como Colatina; **não achei um da bacia do Itajaí**, e não deu para listar a pasta daqui).

Suscetibilidade **não é cota de inundação**: entra, se entrar, como contexto na "minha rua", nunca como faixa. Os IDF são
chuva de projeto (intensidade-duração-frequência), úteis para dizer o quanto uma chuva observada é rara.

## 5. Defesa Civil de SC — WordPress

`https://www.defesacivil.sc.gov.br/wp-json/wp/v2/posts` e `https://www.defesacivil.sc.gov.br/feed/` seriam um feed
estruturado dos avisos e notícias (é WordPress). **Não conferido:** daqui a conexão caiu três vezes e o agente de
leitura recebeu 503. O `wp-json` do CIRAM (`docs/fontes-tempo-real.md`) e o de Taió (`docs/TAIO-API-E-COTAS.md`) só
expõem o CMS, sem hidrologia — o da DCSC deve ser igual, mas um feed de **avisos** já teria uso no chat ("há aviso da
Defesa Civil de SC para a região?"). Testar na VPS com `curl -sS 'https://www.defesacivil.sc.gov.br/wp-json/wp/v2/posts?per_page=3'`.

## 6. Copernicus — EMS e Global Flood Monitoring

- **EMS Rapid Mapping:** a busca não achou ativação para Santa Catarina. As do Brasil que apareceram são do Rio Grande
  do Sul (EMSR720, maio de 2024) e Porto Alegre (EMSN194, 2023). A lista oficial **não abre daqui**.
- **GFM (Global Flood Monitoring):** produto automático do Copernicus com manchas de inundação do Sentinel-1 em até 8 h
  da passagem do satélite. Para o projeto, serviria como **extensão observada** das cheias de out/nov 2023 (e de
  2024–2026), para comparar com as manchas históricas do ArcGIS de Itajaí e com as áreas de risco. Resolução de ~20 m e
  dificuldade em área urbana: contexto, nunca cota. **Não conferido daqui.**

## 7. Defesa Civil de Itajaí — canais oficiais (lidos no pacote do site)

O pacote JavaScript de `https://defesacivil.itajai.sc.gov.br/` (`/assets/index-CozbPDlV.js`, lido em 31/10/2026)
aponta os canais oficiais: canal no WhatsApp (`https://www.whatsapp.com/channel/0029VaiuiLFIyPtXp9TvU10Y`),
`https://x.com/DEFESAITAJAI` e `https://www.instagram.com/defesacivil_itajai/`. Não são dados, mas são **onde o aviso
oficial chega**: candidatos à tela "Fontes" de Itajaí. O mesmo pacote confirma que o site oficial lê
`monitoramento.defesacivil.itajai.sc.gov.br/data/current/app.json` e `/api/v1` — o `app.json` já está documentado em
`docs/INVESTIGACAO-CHUVA-MARE-ITAJAI-2026-10-07.md` e foi o que mostrou o portal parado em 30/10. O endereço
`api-portal.itajai.sc.gov.br` é a intranet da Prefeitura (tela de login): **descartado**.

## 8. O que a busca confirmou que NÃO existe (ou não serve)

| procurado | resultado |
|---|---|
| Sistema de Alerta Hidrológico do SGB/CPRM (SACE) para o Itajaí | os 17 SAHs do SGB não incluem a bacia do Itajaí (Doce, Caí, Uruguai, Itapecuru, Branco, São Francisco, Velhas, Madeira…) |
| Portal de nível da Defesa Civil de **Navegantes** | nada encontrado; a cidade segue sem régua própria publicada |
| Portais de **Pomerode, Benedito Novo, Apiúna, Lontras, Laurentino** | nada encontrado; essas cidades continuam só pela rede estadual |
| Marégrafo público do **Porto de Itajaí / Praticagem / Portonave** | nenhum feed; o marégrafo de Cabeçudas (UNIVALI/Porto) já entra pelo portal de Itajaí (`/monitoramento/mares`) e pela tábua da UNIVALI; o RMPG do IBGE mais perto é Imbituba, longe demais |
| Dado ao vivo da **Barragem Norte** | nenhum; ver fatos de passagem abaixo |
| GloFAS para o Itajaí-Açu | nada específico; sem uso |
| Documentação do modelo de previsão do **AlertaBlu** | só notícias; nada técnico novo |
| API do INMET sem token | confirmado de novo que é só com ACT (C31 enviado em 04/10/2026) |
| Rios On-Line da Epagri/CIRAM | continua exigindo credencial (`docs/fontes-tempo-real.md`; C5 respondido sem acesso) |
| Mapa de inundação da **Prefeitura de Blumenau** (GeoBlumenau) como camada aberta | nada encontrado |
| NASA Disasters "Flooding_Brasil_May2024" | só Rio Grande do Sul |

## 9. Fatos achados de passagem (não conferidos na fonte)

- **Barragem Norte (José Boiteux):** documento da Defesa Civil de SC numa consulta legislativa de 2026 (portal e-Legis da
  ALESC) diz que a barragem tem **uma comporta não operacional, na posição fechada**; e o contrato **28/2026/SDC**, de
  cerca de R$ 9,9 milhões (pregão 767/2025), é para a recuperação dela. Ajuda a explicar o "dados indisponíveis nesta
  fonte" do Monitor (`docs/BARRAGENS-NO-MONITOR.md`). Lido só no resumo da busca.
- **Boletim de Monitoramento Hidrológico da Epagri/CIRAM:** a série continua (nº 75/2026 em 14/05; o projeto já tem o
  150/2026 em `data/brutos/`). Contato da equipe: sshidrosc@epagri.sc.gov.br, (48) 3665-5124 — já no projeto pelo C5/C12.
- **Grupo `notamet` da Epagri:** público no Google Groups; o projeto já recebe as notas por e-mail (C12).

## 10. Próximos passos propostos (decisão do Jefferson)

1. **Na VPS, só leitura:** `layer/id/<n>` e `GetCapabilities` do CEMADEN (seção 1); `wp-json` da DCSC (seção 5);
   `monitora.furb.br` (seção 2); `data.mendeley.com/datasets/cj64gycsw8` (seção 3). Guardar os brutos em
   `data/brutos/varredura-fontes-2026-11-04/` com sha256, como nas rodadas anteriores.
2. **No navegador:** geoportal do SGB (pasta `hidrologia`) e os downloads do RIGEO de Brusque, Gaspar e Blumenau.
3. **Nada entra em `estacoes.json`, `enchentes.json` ou no site** antes disso. Os canais oficiais de Itajaí (seção 7)
   podem entrar na tela "Fontes" por decisão, sem dado.

## Como foi feito

Buscas (04/11/2026): CEMADEN estações/API; ANA HidroWebService telemetria; SGB/CPRM SACE; Epagri/CIRAM rios e API;
Defesas Civis de Navegantes, Ilhota, Indaial, Timbó, Pomerode, Benedito Novo, Apiúna, Lontras, Laurentino; Comitê do
Itajaí/AGIR; Barragem Norte; Porto de Itajaí/maré; Copernicus EMS/GFM; avisos da DCSC; AlertaBlu/FURB previsão; GeoBlumenau;
mapas de inundação de Brusque, Rio do Sul e Gaspar; dados abertos de SC; GloFAS; INMET `apitempo`. Leituras diretas
(HTTP 200): `mapainterativo.cemaden.gov.br` (página, `js/script.js`, `js/interativo.js`, formulários de download),
`defesacivil.itajai.sc.gov.br` e seu pacote JavaScript. Recusas registradas pelo proxy: ver o início deste documento.
Nenhuma escrita, nenhum formulário enviado, nenhum e-mail.

## 11. Conferência pelo navegador e handoff (04/11/2026, à tarde)

O Jefferson abriu no Chrome o que este ambiente não alcança (`docs/VARREDURA-FONTES-2026-11-04-NAVEGADOR.md`) e
baixou a tabela do Mendeley. Status final das candidatas:

| # | Fonte | Status | O que ficou |
|---|---|---|---|
| 1 | CEMADEN `mapservices`/`resources` | conexão recusada também na rede doméstica | testar da VPS |
| 1b | CEMADEN WMS `cemaden_dev` | abre (1.180 camadas), sem PCD hidrológica ativa | o nível das PCDs segue no C24 |
| 2 | FURB `monitora.furb.br` | GeoNode do FlorestaSC, 31 camadas, nenhuma de enchente | **descartada** como fonte de cheia |
| 3 | Mendeley "Histórico de enchentes em Blumenau" | baixada (sha256 conferido), transcrita e cruzada | `data/brutos/varredura-fontes-2026-11-04/` e `docs/VARREDURA-FONTES-2026-11-04-CRUZAMENTO-BLUMENAU.md`; nada cadastrado |
| 4 | SGB geoportal `inundacao` e `risco` | funcionam, com consulta por município | contexto de suscetibilidade e risco; manchas de inundação do SGB **não cobrem** a bacia |
| 5 | DCSC `wp-json` / `feed` | funcionam (200) | candidato a avisos no chat; texto só por região |
| 6 | Copernicus GFM / EMS | não conferido | pendente |
| 7 | Canais oficiais da DC de Itajaí | links lidos | candidatos à tela "Fontes" |

Índices atualizados: `docs/fontes-tempo-real.md` (DCSC, SGB, CEMADEN, FURB) e `docs/fontes-academicas.md` (Mendeley).

## 12. Sondagem pelo GitHub Actions (04/11/2026, noite)

Terceiro ponto de vista, depois deste ambiente e da rede do Jefferson: `.github/workflows/sondar-fontes.yml` roda
`scripts/sondar_fontes.py` (um GET por alvo, só depois do `robots.txt` do host) e `scripts/baixar_sgb_suscetibilidade.py`,
e publica o resultado no branch `sondagem-fontes` (`sondagem.txt/json`, `sgb.txt`, `sgb-resumo.json`, `sgb/*.geojson`).
Primeira rodada, 13h52 UTC:

| Alvo | Do runner | Leitura |
|---|---|---|
| CEMADEN WMS `cemaden_dev` | 200, 2 MB de capabilities | igual ao navegador |
| CEMADEN `mapservices` / `resources` | `robots.txt` sem resposta → nada pedido | o relatório não dizia o motivo; **corrigido**: agora grava a exceção (rota, TLS ou recusa) |
| CEMADEN gráfico PCD | 404 (página WordPress) | endereço de exemplo não existe mais |
| DCSC `wp-json` / `feed` | `robots.txt` sem resposta → nada pedido | idem; da VPS o coletor de avisos (#564) é quem decide |
| SGB `inundacao` / `risco` (distintos) | 200 (4 KB e 62 KB) | **funcionam do runner** |
| SGB download por cidade | nada pedido | o geoportal responde **404 ao `robots.txt`**, e o script tratava 404 como "sem resposta". **Corrigido**: 404 = não há robots = nada proibido (como em `sondar_fontes`); outro erro continua fechando tudo |
| FURB GeoNode, Mendeley | 200 | como antes |

A rodada seguinte (disparada pelo push desta correção) deve trazer o motivo da falha nos hosts do CEMADEN e da
DCSC e os GeoJSON do SGB por cidade. Regra que não muda: só GET, `User-Agent` do projeto, robots antes de tudo.
