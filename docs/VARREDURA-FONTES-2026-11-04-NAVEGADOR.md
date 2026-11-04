<!-- Texto do Jefferson (conferência pelo Chrome, 04/11/2026), trazido ao repositório sem alteração de conteúdo no PR da varredura. Complementa docs/VARREDURA-FONTES-2026-11-04.md. -->

# Varredura de fontes — conferência pelo navegador (04/11/2026)

Complemento ao documento "Varredura de fontes novas — 04/11/2026". Leitura feita pelo Chrome do Jefferson, só GET, sem login, sem formulário, sem download de arquivo. Nada entrou em data/.

## Resumo

| # | Fonte | Resultado no navegador | Serve para o projeto? |
|---|---|---|---|
| 1 | CEMADEN `mapservices` (MapaInterativoWS) e `resources.cemaden.gov.br` | **conexão recusada** também da rede do Jefferson (ERR_CONNECTION_REFUSED) | segue pendente: tentar na VPS |
| 1b | CEMADEN WMS `gsc.cemaden.gov.br/geoserver/cemaden_dev/wms` GetCapabilities | **abre** (2,8 MB, 1.180 camadas) | pouco: sem camada de PCD hidrológica ativa |
| 2 | FURB `monitora.furb.br` | **abre**; é o GeoNode do FlorestaSC (31 camadas, API `/api/layers/`) | não: nenhuma camada de enchente/cota |
| 3 | Mendeley "Histórico de enchentes em Blumenau" | **abre**; metadados lidos; arquivo não baixado | sim, para cruzamento (falta abrir a tabela) |
| 4 | SGB geoportal (ArcGIS REST) + RIGEO (DSpace) | **abrem**, com consulta por atributo | sim: suscetibilidade a inundação e setorização de risco por cidade |
| 5 | Defesa Civil SC — `wp-json` e `/feed/` | **abrem** (HTTP 200, JSON e RSS) | sim: feed de alertas/avisos para o chat |

## 1. CEMADEN

- `js/script.js` define `ws_path = https://mapservices.cemaden.gov.br/MapaInterativoWS/resources/layer/id/` (as antigas, `sjc.salvar...` e `mapainterativo.../MapaInterativoWS`, estão comentadas). O `<n>` é montado em `createImageLayer(produto, ...)`, que é a camada de **imagem** (radar/produtos), não o cadastro de estações.
- A página carrega `https://resources.cemaden.gov.br/dados/311_24.json` como script. Pelo navegador do Jefferson, `resources.cemaden.gov.br` e `mapservices.cemaden.gov.br` **recusaram a conexão**. Não é só o proxy do ambiente.
- WMS `cemaden_dev` (GetCapabilities abre): 1.180 camadas. Relevantes: `SC` e `SC_MOV` (bbox de SC), `bacia_estadual_sc`, `bacias_montante_pcd_otto`, `estacoes_nivel_serrana`, `areasrisco_inov_*`, `pcds_hidrologicas_inativas_mapa`. **Não há camada de PCD hidrológica ativa** neste workspace, e as `HECRas-*` são do Acre (bbox −67,8 / −10,0). O nível das PCDs continua dependendo do pedido C24.
- Achado à parte: o geoportal do SGB tem um serviço `Cemaden/MapServer` (camada `EstacoesCemaden`), mas é um recorte antigo, com 242 registros, de 2019, de Alagoas, e **0 em SC**. Descartar.

## 2. FURB — monitora.furb.br

É o "FlorestaSC – Plataforma de Mapas" (Inventário Florístico Florestal de SC), GeoNode com 31 camadas: espécies, unidades de conservação, uso da terra (MonitoraSC 2017), municípios, bacias, `hidrografia_epagri` ("Rios principais") etc. **Nenhuma camada da carta-enchente do CEOPS**, nem cota/inundação. Descartar como fonte de cheia. No máximo, `Bacias_Hidrograficas` e `hidrografia_epagri` servem de base cartográfica, conferindo a licença.

## 3. Mendeley Data — Histórico de enchentes em Blumenau

- DOI 10.17632/cj64gycsw8.2, versão 2, de 23/09/2025 (v1 de 18/09/2025). Licença **CC BY 4.0**.
- Autores: Albio Fabian Melchioretto, Bruno Cristiano Loos e Silva, Abel Braga Warwar da Fonseca (Senac Santa Catarina).
- Segundo a descrição, os dados vêm da Defesa Civil de Blumenau, com a classificação de Ribeiro (2023, *Revista de Tecnologia & Gestão Sustentável*, v. 2, n. 6) e cruzamento bibliográfico. Cobre do século XIX até hoje, com data e nível do Itajaí-Açu.
- Arquivos: `Tabela de enchentes.xlsx` (20,9 KB, SHA-256 `56fdbe6baa58fbc14a78552b66aefe92f8ad223fd39de6ec28c6d0ec75aa30c6`) e uma pasta de fotos (o total chega a 9,77 MB).
- O site não mostra prévia da planilha. **Falta baixar o xlsx** para ver se a tabela diz em que régua está cada nível. Confiança, se entrar: média (compilação).

## 4. SGB/CPRM

### Geoportal (ArcGIS Server 11.3, `geoportal.sgb.gov.br/server/rest/services`): abre e aceita consulta

- `hidrologia/` (77 serviços): as manchas de inundação (`mancha_*`, `manchas_inundacao`) são de Colatina, Gov. Valadares, Manaus, Montenegro, Porto Velho, Teresina, Uruguaiana etc. **Nenhuma da bacia do Itajaí** (confirma a suspeita).
- `gestaoterritorial/inundacao/MapServer/0` ("Inundação Área"): suscetibilidade a inundação (classes Alta/Média/Baixa), com campos `uf, municipio, processo, classe, fonte, ano, executor`. Na bacia há: **Apiúna 2016, Benedito Novo 2017, Blumenau 2013, Brusque 2013, Gaspar 2013, Ilhota 2013, Itajaí 2019, José Boiteux 2019, Luiz Alves 2013, Navegantes 2013, Rodeio 2013, Taió 2013, Timbó 2013**. A fonte diz que o produto é de modelagem validada em campo pela CPRM. É suscetibilidade, **não cota**: serve de contexto na "minha rua".
- `gestaoterritorial/risco/MapServer/0` ("Setorização de Risco"): campos `munic, num_setor, data_setor, local, tipolo_g1..5, grau_risco, num_edif, num_domi, num_pess, sug_interv, descricao`. Setores na bacia: Ascurra, Brusque (2018–19), Gaspar (2018), Ilhota (2018), Indaial, Itajaí (2012, com "Enchente"), Navegantes (2018, com "Inundação"), Pomerode, **Rio do Sul (set e nov/2025)**, Timbó (2013–14).

### RIGEO (DSpace 7, API `/server/api/`): arquivos listados, nada baixado

| handle | produto | ano | arquivos (tamanho) |
|---|---|---|---|
| doc/15117 | Carta de suscetibilidade — Brusque | 2015 | CS-Brusque.pdf (15 MB), sig_brusque_sc_suscet.zip (182 MB), bc_brusque_sc.zip (63 MB), ortofotos (395 MB), MDE (362 MB) |
| doc/15115 | Carta de suscetibilidade — Blumenau | 2015 | CS-Blumenau.pdf (23 MB), sig_blumenau_sc_suscet.zip (124 MB), bc_blumenau_sc.zip (96 MB), ortofotos (691 MB), MDE (643 MB) |
| doc/18546 | Setorização de risco alto/muito alto — Gaspar (revisita) | 2019-03 | sig_gaspar_sc_risco_revisita_2019.zip (22 KB), produtos_... (81 MB) |
| doc/15144 | Carta de suscetibilidade — Nova Trento | 2015 | CS-NovaTrento.pdf, sig_... |

Os relatórios IDF aparecem como "Atlas pluviométrico do Brasil: equações IDF" (doc/17510, doc/23512, doc/23510). Ainda falta abrir e ver qual é de qual cidade.
Observação: para consultar, o serviço `inundacao` do geoportal é bem mais leve que os ZIPs de 100–180 MB.

## 5. Defesa Civil de SC — WordPress

- `https://www.defesacivil.sc.gov.br/wp-json/wp/v2/posts?per_page=3&_fields=id,date,link,title,categories` → **200, JSON**. Último post: id 39521, 04/11/2026 09:41, "ATENÇÃO – 04/11 09:34 – TEMPORAIS ... nas próximas 4 horas".
- `/feed/` → 200, `application/rss+xml`.
- Categorias (id: nome, nº de posts): **7 Alerta (5.098)**, **6 Aviso (1.040)**, 17 Boletins e Notas (362), 16 Boletins para os Próximos 5 Dias (824), 25 El Niño (46), **23 Monitoramento (802)**, 1 Notícia (20), 5 Previsão do Tempo (123).
- O conteúdo do post diz as **regiões** em texto livre ("Extremo Oeste, Oeste e Meio-Oeste"), sem município nem polígono. Para o chat, basta filtrar `categories=7,6` e procurar "Vale do Itajaí", "Foz do Itajaí", "Litoral Norte" no texto.
- Monitoramento: posts "Monitoramento Meteorológico DC/SC dd/mm hh:mm", cerca de 2 por dia.
- Consulta sugerida: `.../wp-json/wp/v2/posts?categories=6,7&per_page=20&_fields=id,date,link,title,content`.

## Não feito nesta rodada

- Copernicus GFM / EMS (aplicativo web pesado; fica para depois).
- Download do xlsx do Mendeley e dos ZIPs do RIGEO (aguardando ok).
- `mapservices`/`resources` do CEMADEN: recusados também na rede doméstica; tentar da VPS.
