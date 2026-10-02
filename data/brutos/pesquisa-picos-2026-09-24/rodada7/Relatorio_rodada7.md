# Rodada 3 — cheias da bacia do rio Itajaí (SC)

Gerado em 2026-10-01 (PT, UTC-3). Nada foi escrito no GitHub nem em enchentes.json.
Todos os números abaixo têm arquivo original no zip `fontes-rodada3.zip` (77 arquivos, 19,7 MB, abaixo de 24 MB; nada foi cortado).

Como ler:
- A coluna "tipo" usa a palavra da fonte: PICO (a fonte diz pico/máximo com hora), LEITURA (valor de um horário) ou COTA (limite de alerta).
- "Fuso não declarado" = a fonte não diz o fuso.
- "p. PDF" é a página do arquivo PDF; HTML não tem página ("—").
- Nenhum número foi estimado, interpolado ou convertido entre réguas ou zeros.
- Os trechos literais foram conferidos nos arquivos salvos. Em HTML com acento perdido (Clicrbs 2008) o trecho está como lido.

---

## 0. Itens de documento (14, 15, 11, 10, 16)

### Item 15 — JICA 2011, Vol. III-A, Tabela 7.5.1 (ENCONTRADO)

| o que se pediu | título | órgão | URL | página | trecho literal | arquivos |
|---|---|---|---|---|---|---|
| Página A-80 inteira, com colunas por período de retorno | JICA, Preparatory Survey for the Project on Disaster Prevention and Mitigation Measures for the Itajai River Basin, Final Report, Supporting Report Annex A (Hydrology), Vol. III-A | JICA (openjicareport) | https://openjicareport.jica.go.jp/pdf/12043584_01.pdf | PDF p. 91 (impressa "A - 80") | "Table 7.5.1 Largest Discharge Peak Time from each City, by Return Period". Colunas: Catchment Area (km²); 5, 10, 25 e 50 anos, cada uma com Discharge (m³/s) e Peak (formato MM/DD HH:mm). "Source: JICA Survey Team". | `JICA_VolIII-A_pdf-p91_A-80_Tabela-7.5.1.pdf` (página extraída com pdfseparate); `JICA_VolIII-A_pdf-p91_A-80_render-91.png` (130 dpi, pdftoppm); PDF completo `JICA_2011_VolIII-A_Hydrology_12043584_01.pdf` |

São tempos de pico **modelados** (cheia de projeto), não observados. Os horários não têm fuso declarado. Texto de p. 90 (A-79): "The difference of peak time between Rio do Sul and Blumenau city is from 7 to 10 hours; between Blumenau and Itajaí is from 14 to 17 hours."

Valores como na tabela (vazão m³/s, pico MM/DD HH:mm). O original escreve "IIHOTA" para Ilhota.

| Cidade | Área km² | 5 anos | 10 anos | 25 anos | 50 anos |
|---|---|---|---|---|---|
| Ituporanga | 1.645 | 310, 08/06 23:00 | 370, 08/06 23:00 | 430, 08/06 23:00 | 490, 08/06 23:00 |
| Taió | 1.570 | 430, 08/06 16:00 | 520, 08/06 16:00 | 620, 08/06 16:00 | 710, 08/06 16:00 |
| Rio do Sul | 5.041 | 1.300, 08/06 22:00 | 1.600, 08/06 22:00 | 1.900, 08/06 22:00 | 2.200, 08/06 22:00 |
| Apiúna | 9.288 | 2.100, 08/07 07:00 | 2.600, 08/07 07:00 | 3.100, 08/07 06:00 | 3.600, 08/07 06:00 |
| Ibirama | 3.341 | 840, 08/06 17:00 | 970, 08/06 17:00 | 1.200, 08/06 17:00 | 1.300, 08/06 17:00 |
| Indaial | 11.275 | 2.900, 08/07 08:00 | 3.500, 08/07 07:00 | 4.300, 08/07 06:00 | 5.100, 08/07 06:00 |
| Timbó | 1.430 | 760, 08/06 22:00 | 920, 08/06 22:00 | 1.200, 08/06 22:00 | 1.300, 08/06 22:00 |
| Blumenau | 11.921 | 3.000, 08/07 08:00 | 3.700, 08/07 07:00 | 4.600, 08/07 05:00 | 5.500, 08/07 05:00 |
| Gaspar | 12.421 | 3.000, 08/07 10:00 | 3.700, 08/07 09:00 | 4.600, 08/07 07:00 | 5.400, 08/07 06:00 |
| Ilhota | 12.673 | 2.900, 08/07 15:00 | 3.500, 08/07 13:00 | 4.400, 08/07 12:00 | 5.200, 08/07 10:00 |
| Itajaí | 15.092 | 3.300, 08/08 01:00 | 4.000, 08/07 22:00 | 5.000, 08/07 19:00 | 6.000, 08/07 17:00 |
| Brusque | 1.207 | 350, 08/07 04:00 | 430, 08/07 04:00 | 540, 08/07 04:00 | 630, 08/07 03:00 |

(Conferir os valores contra o PNG/PDF anexo antes de usar. A data "08/06" etc. é a do hidrograma de projeto da JICA.)

### Item 14 — Tábua de marés 2027, porto de Itajaí (NÃO PUBLICADA nas capturas consultadas)

| o que se pediu | título | órgão | URL | página | trecho literal | arquivo |
|---|---|---|---|---|---|---|
| Publicação 2027 | "TÁBUAS DAS MARÉS PARA 2026 - 63ª edição" (a página só lista 2026; nada de 2027) | Marinha do Brasil, DHN/CHM | https://web.archive.org/web/2026/https://www.marinha.mil.br/chm/dados-do-segnav-publicacoes/tabuas-das-mares (captura 20260928002148, i.e. 2026-09-28) | — | "TÁBUAS DAS MARÉS PARA 2026 - 63ª edição"; "Atualizado em 12/02/2026" | `CHM_wayback_tabuas-das-mares.html` |
| Publicação 2027 | "Tábuas de Maré 2025 \| CHM" (lista de PDFs por porto: só 2025 e 2026; a lista salva não tem linha de Itajaí) | Marinha/CHM | https://web.archive.org/web/20260921032732/https://www.marinha.mil.br/chm/tabuas-de-mare | — | só aparecem edições 2025 e 2026 | `CHM_wayback_tabuas-de-mare_20260921.html` |

Conclusão: nas capturas de 21 e 28/09/2026 não há tábua 2027. Os sites ao vivo (marinha.mil.br/chm/tabuas-de-mare e dados-do-segnav-publicacoes/tabuas-das-mares) dão 403 (Cloudflare "Just a moment") no curl, então não pude ver a página ao vivo de 01/10/2026.

### Item 11 — Blumenau: referência de cada lista e cotas ANA 83800002

**(a) Documentos sobre a referência (régua/IBGE)**

| o que se pediu | título | órgão | URL | página | trecho literal | arquivo |
|---|---|---|---|---|---|---|
| Referência da régua e relação com o IBGE | "COTAS-ENCHENTE DO MUNICIPIO DE BLUMENAU" (Cordero, Salvador, Refosco), XX Simpósio Brasileiro de Recursos Hídricos | FURB / ABRH | https://files.abrhidro.org.br/Sumarios/155/97a206c1b1ad37424e0fbf557d9cfd26_c081107e6d21fbbcc1b378241a2c984f.pdf | p. 1–2 | "referenciado ao nível do Rio Itajaí-Açu medido na régua da estação fluviométrica que fica localizada na ponte Adolfo Konder no centro de Blumenau"; "a régua da ANA tinha uma referência diferente da referência do IBGE ... pedimos que fosse alterada a referencia da régua da ANA. O pedido foi aceito e agora ficou a Referência IBGE levantada através do GPS que deu 40 cm. Assim a referência da régua da ANA ficou 40 cm a menos do que as enchentes anteriores." Resumo (p. 1): "Itajaí-Açu, na estação fluviométrica de Blumenau, atingiu o valor de 13,0 metros" (set/2011). | `ABRH_Cotas-enchente-Blumenau.pdf` |
| idem | mesmo paper, Tabela 2 | idem | idem | p. 2 | A tabela "Alturas atingidas ... 1983, 1992 e 2011" é altitude por GPS, não leitura de régua. Linha "Ponte Adolfo Konder - Régua": 15,54 (1983), 13,00 (1992), 13,00 (2011). | idem |
| Régua CEOPS (Ponte Adolfo Konder) vs. prefeitura (Ponte de Ferro) | "Sistema de cotas de enchente apresenta falhas em Blumenau" (ND, 26/09/2013) | Notícias do Dia | https://ndmais.com.br/noticias/sistema-de-cotas-de-enchente-apresenta-falhas-em-blumenau/ | — | "A diferença entre a régua do Ceops, que fica na Ponte Adolfo Konder e da Prefeitura, na Ponte de Ferro chegou a 20 centímetros" | `ND_sistema-cotas-falhas.html` |
| Régua oficial mudou de lugar | "Obra em ponte de Blumenau exige a instalação de novas réguas no rio" (NSC, coluna, 21/09/2020) | NSC Total | https://www.nsctotal.com.br/colunista/evandro-de-assis/obra-em-ponte-de-blumenau-exige-a-instalacao-de-novas-reguas-no-rio/ | — | "A régua que serve de parâmetro oficial do nível do Rio Itajaí-Açu, em Blumenau, precisa mudar de lugar."; "arrasta-se desde 2011, quando a enchente levou a seção de réguas metálicas dispostas no talude. A que está na ponte deveria ser uma solução provisória." | `NSC_novas-reguas-ponte-blumenau.html` |
| Níveis revisados | "Prefeitura de Blumenau admite que irá rever cotas de enchente na cidade" (blog reproduzindo JSC, 2011) | blog Novo Plantão Blumenau (JSC) | http://moniquebecker.blogspot.com/2011/09/prefeitura-de-blumenau-admite-que-ira.html | — | "Os níveis usados atualmente foram calculados em 1984 e revisados em 1992, quando se percebeu diferença de 10 centímetros entre o previsto e o real." | `Blumenau_moniquebecker_2011-09.html` |
| Lista oficial da Defesa Civil de Blumenau (102 enchentes) | "Enchentes registradas" (AlertaBlu) | Defesa Civil de Blumenau | https://alertablu.blumenau.sc.gov.br/p/enchentes (redireciona para https://defesacivil.blumenau.sc.gov.br/p/enchentes) | — | A lista **não declara a régua nem o zero**. Linhas: 1983-07-09 = 15,34; 1984-08-07 = 15,46; 2001-10-01 = 11,02; 2008-11-24 = 11,52; 2011-09-09 = 12,6; 2013-09-23 = 10,51; 2015-10-23 = 10,03; 2023-10-09 = 10,19; 2023-10-12 = 10,76; 2023-11-17 = 9,14; 2024-05-19 = 8,67 | `AlertaBlu_enchentes-registradas.html` |
| Legenda do AlertaBlu | "Critérios de Nível do Rio" | Defesa Civil de Blumenau | https://defesacivil.blumenau.sc.gov.br/c/meteorologia/legenda_nivel_rio | — | "Normalidade 0 - 3m; Observação 3 - 4m; Atenção 4 - 6m; Alerta 6 - 8m; Alerta Máximo Acima de 8m. Fonte: Adaptado de AlertaRio" | `DefesaCivilBlumenau_c_meteorologia_legenda_nivel_rio.html` |
| Contrato de atualização das cotas | FURB e Defesa Civil de Blumenau assinam contrato para atualização das cotas de enchente | FURB | https://www.furb.br/pt/noticias/furb-e-defesa-civil-de-blumenau-assinam-contrato-para-atualizacao-das-cotas-de-enchente | — | (página salva; não traz zero/referência) | `FURB_contrato-cotas.html` |

**Divergência de zero**: o paper da FURB diz "40 cm" para a diferença ANA×IBGE; você citou 0,20 m. O ND (2013) fala em 20 cm entre régua CEOPS e régua da Prefeitura. São afirmações diferentes; não converti nada. Não achei documento que diga qual referência (régua ANA, AlertaBlu ou IBGE) a lista de 102 enchentes usa; a Tabela 4 de Cordero & Medeiros não foi achada nesta rodada.

**(b) Cotas ANA 83800002 em 1983 e 1984 — serviço ANA, valores como publicados**

Fonte: serviço SOAP/HTTP da ANA `HidroSerieHistorica` (CodEstacao=83800002, TipoDados=1; NivelConsistencia=2 consistido e 1 bruto), 01/01/1983 a 31/12/1984. O XML **não declara a unidade** (HidroWeb costuma publicar cota em cm, mas isso não está escrito no arquivo). O significado do código de status não foi confirmado. A API REST do HidroWeb dá 401 (precisa de token).

| data | tag XML | valor publicado | consistência | comparação com a lista AlertaBlu (sem converter) | arquivo |
|---|---|---|---|---|---|
| 1983-07 (dia 9) | `Cota09`; `Maxima`=1519, `DiaMaxima`=9, `MaximaStatus`=2 | **1519** (também `Cota07`=1076, `Cota08`=1430, `Cota10`=1410) | nível 2 (o nível 1 não traz 1983-07) | AlertaBlu: 15,34 | `ANA_ws_HidroSerieHistorica_83800002_1983-1984_nc2-consistido.xml` |
| 1984-08 (dia 7) | `Cota07`; `Maxima`=1485, `DiaMaxima`=7, `MaximaStatus`=1 | **1485** (também `Cota05`=369, `Cota06`=1145, `Cota08`=1388, `Cota09`=1118) | níveis 1 e 2 | AlertaBlu: 15,46 | `..._nc2-consistido.xml` e `..._nc1-bruto.xml` |

URL: http://telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroSerieHistorica?CodEstacao=83800002&DataInicio=01/01/1983&DataFim=31/12/1984&TipoDados=1&NivelConsistencia=2 (e =1).

### Item 10 — Rio do Sul: régua dos picos do "Histórico de Cheias"

| o que se pediu | título | órgão | URL | página | trecho literal | arquivo |
|---|---|---|---|---|---|---|
| A aba "Histórico de Cheias" **não declara a régua** | Portal Defesa Civil de Rio do Sul (SPA React; os dados estão no bundle JS) | Defesa Civil de Rio do Sul | https://defesacivil.riodosul.sc.gov.br/ ; bundle https://defesacivil.riodosul.sc.gov.br/assets/index-DyPsDK0O.js | — | Aba "Histórico de Cheias": 77 linhas, 1911–2024; "Fonte: Defesa Civil de Rio do Sul - Exportação de Dados". Valores: 1911 Outubro 12,20 (primeira linha); 1983 Julho 13,58; 1984 Agosto 12,80; 2011 Setembro 12,96; 2013 Setembro 10,39; 2015 Outubro 10,71; 2017 Junho 10,89; 2023 "13 de outubro" 11,86; 2023 "17 de novembro" 13,04; 2024 "18 de maio" 8,97. | `DCRioDoSul_portal_bundle_index-DyPsDK0O.js`, `DCRioDoSul_home.html` |
| Outra aba do mesmo portal cita a ponte | idem | idem | idem | — | Na aba "Cotas de Cheia por Rua": "Cotas em metros na régua da Ponte Dom Tito Buss". O nível atual vem como "m na Ponte Dom Tito Buss". Isso vale para as cotas por rua e o nível atual, não para o Histórico. | idem |
| Artigo técnico (CEOPS/FURB) | "Previsão de cheia em tempo atual, com um modelo ARMAX, para a cidade de Rio do Sul - SC" (Cordero, Momo, Severo), XIX SBRH | FURB/ABRH | https://files.abrhidro.org.br/Eventos/Trabalhos/153/ccad18bf02d5a87b17c23b64e5139d5b_d987acd551ef387e4e219508a27e69c5.pdf | p. 1 | "a primeira grande enchente que se tem registro ocorreu em 1911, atingindo um pico de 12,20m, referenciada na régua da atual estação fluviométrica localizada naquela cidade"; "atualmente as primeiras edificações começam a ser inundadas quando o rio ... atinge a cota 6,60m"; "julho de 1983 ... 13,58m ... agosto de 1984 ... 12,80m". Não nomeia Dom Tito Buss. | `ABRH_ARMA_RioDoSul_2011.pdf` |
| Tabelas CEOPS de picos | "Esboços" (UFSC), vulnerabilidades em Rio do Sul, Tabelas 2 e 3 "Picos de Enchentes Registrados na Bacia do Rio Itajaí-Açu" | UFSC / CEOPS-FURB | https://periodicos.ufsc.br/index.php/esbocos/article/download/2175-7976.2013v20n30p9/27829/118436 | PDF p. 11 (Tabela 2) e p. 12 (Tabela 3); páginas impressas 19–21 | Régua **não declarada**. Rio do Sul: 1911 (29/05) = 12,2 m; texto: "Rio do Sul atingiu a cota de 12,8m" em 1911 e "15,58m em julho de 1983" (provável erro de digitação). Linha 2011-09-09: "Rio do Sul 12,98m" | `Esbocos_Rio-do-Sul_vulnerabilidades.pdf` |

Nenhum documento achado diz que a régua mudou de lugar em Rio do Sul. A estação DCSC-00013 "MKS" não foi tratada. O TCC do CBMSC (Laurentino, "Medidas de controle de enchentes e inundações na cidade de Rio do Sul/SC") deu timeout e 404 no Wayback; não entra.

### Item 16 — Barragens Oeste (Taió) e Sul (Ituporanga): o que cada número mede

| o que se pediu | título | órgão | URL | página | trecho literal | arquivo |
|---|---|---|---|---|---|---|
| 83 e 93,5 hm³ = "gross storage capacity" | JICA, Annex B, Vol. III-B (Flood Mitigation), Tabela 2.2.1 "Main Features of Flood Control Dams" | JICA | https://openjicareport.jica.go.jp/pdf/12043584_02.pdf | PDF p. 18 (B-8) | "Gross storage capacity 83,000,000 m3 / 93,500,000 m3 / 357,000,000 m3" (Oeste/Sul/Norte); "Equivalent rainfall = reservoir storage capacity / drainage area"; nível mínimo EL.340.0 / EL.372.9 / EL.257.0 m; nível máximo EL.363.0 / EL.408.0 / EL.304.25 m; crista do vertedouro de emergência 360.0 m e 399.0 m. As células sombreadas vêm do site do DEINFRA. | `JICA_2011_VolIII-B_FloodMitigation_12043584_02.pdf` |
| idem | JICA Vol. III-B, Tabela 7.1.1 | JICA | idem | PDF p. 80 (B-70) | "Total reservoir capacity 83,000,000 m3 / 93,500,000 m3"; nível máximo EL.362.5 m / EL.408.0 m; "These dams should be operated in empty condition in reservoir" | idem |
| Volume armazenado vs. capacidade | JICA Vol. III-B | JICA | idem | PDF p. 48 (B-38) e p. 43 (B-33) | Oeste: "stored volume is 72.2 x 106 m3, which is within its storage capacity 83.0 x 106 m3" (cheia de 10 anos). Sul: "stored volume is 58.4 x106m3 ... storage capacity 93.5 x106m3". | idem |
| Alteamento de 2 m | JICA Vol. III-B | JICA | idem | PDF p. 57 (B-47) e p. 62 (B-52) | Oeste: "The capacity will be increased by approximately 16,200,000m3". Sul: "the storage capacity of the Sul dam would be increased to be 110 million m3" | idem |
| **Definição do 83 hm³ (Oeste)** | "Análise do rompimento hipotético da Barragem Oeste do Vale do Rio Itajaí" (TCC, aparentemente de Giorgia Cleto Moecke; orientador Pedro L. B. Chaffe) | UFSC (repositório) | https://repositorio.ufsc.br/bitstream/handle/123456789/127343/TCC-FINAL.A5.pdf?sequence=1&isAllowed=y | PDF p. 42; p. 49; p. 51 | p. 42: "Inicialmente a Barragem Oeste possuía a capacidade de armazenamento equivalente a 83,0 milhões de metros cúbicos. Após a implementação das melhorias no corpo da barragem, propostas pela JICA em 2011, sua capacidade foi aumentada em 18,85 milhões de metros cúbicos." p. 49 (seção 4.1.3): equação JICA V = 0,18192 x (H − 338,64)², V = "o volume acumulado no reservatório até a elevação 362,30 m". Tabela 4.4 (Cota x Volume, "adaptado de JICA 2011"): 338,64 = 0,00; 350,00 = 23,48; **360,00 = 83,00**; 361,00 = 90,95; 362,00 = 99,27; 362,30 = 101,84 (10⁶ m³). p. 51: "Volume total do reservatório 102 milhões de m³". | `UFSC_TCC_rompimento-hipotetico-barragem-oeste.pdf` (a camada de texto é codificada; renders em `UFSC_TCC_render_pdf-p42.png` e `..._p49.png`), `UFSC_repo_rompimento-barragem-oeste_handle.html` |
| Dados do operador antigo (DEINFRA, 2013) | "Sobre as barragens" (DEINFRA/SC, cópia Wayback de 2013-04-08) | DEINFRA/SC | https://web.archive.org/web/20130408061057/http://www.deinfra.sc.gov.br/barragens/sobre-as-barragens/ | — | Oeste (Taió): "Volume do Reservatório: 83 milhões m³ ... Cota do Vertedouro: 360 m ... Cota do Coroamento: 309 m [sic]". Sul (Ituporanga): "Volume do Reservatório: 93,5 milhões m³ ... Cota do Vertedouro: 65 m [sic] ... Cota do Coroamento: 309 m [sic]". Não define volume útil/total. O texto traz inconsistências de cota. | `DEINFRA_wayback_barragens.html` |
| Imprensa pós-alteamento | NSC, "Barragens de Taió e Ituporanga chegam à capacidade máxima e começam a verter" (08/10/2023) | NSC Total | https://www.nsctotal.com.br/cotidiano/barragens-de-taio-e-ituporanga-chegam-a-capacidade-maxima-e-comecam-a-verter | — | "reter 100 milhões de metros cúbicos de água" (Taió); "capacidade de armazenamento é de 110 milhões de metros cúbicos" (Ituporanga); subtítulo "Juntas, as estruturas têm capacidade para 210 milhões" | `NSC_barragens-taio-ituporanga-verter.html` |
| idem | RWTV, "Barragem Sul de Ituporanga está com 59% da capacidade nesta quinta-feira" (01/10/2026) | RWTV | https://rwtv.com.br/altovale/barragem-sul-de-ituporanga-esta-com-59-da-capacidade-nesta-quinta-feira/ | — | "O reservatório tem capacidade total de 104,03 hm³." | `RWTV_barragem-sul-59pct.html` |
| idem | Portal Educadora (02/02/2019) | Portal Educadora | https://www.portaleducadora.com/noticia/barragem-de-taio-e-considerada-mais-segura-do-alto-vale/ | — | "A altura do barramento lateral e do vertedouro foram aumentadas em dois metros, o que elevou a capacidade em quase 20% a mais do que o limite anterior." | `Educadora_barragem-taio-segura.html` |

Resumo do item 16: os valores divergem (83 e 93,5 JICA bruta; 100 e 110 NSC pós-alteamento; 104,03 RWTV para a Sul; 99,96 e 104,03 do painel Asthon). O **99,96 do painel Asthon não aparece em nenhum arquivo baixado**. Nenhum documento achado usa "volume útil" nem "de amortecimento"; JICA diz "gross/total storage capacity". O TCC UFSC (citando a JICA) mostra que o 83,00 é o volume acumulado até a cota 360,00 m (crista do vertedouro na JICA).
Pista para você conferir na sua cópia do Manual de Operação de Barragens (2024), **não verificada por mim, veio só de um resumo de busca**: Sul 104,03 hm³ total; cota de atenção 400 m-IBGE = 94,10 hm³; 385 m = 6,93 hm³; Oeste 350,40 m = 13,29 hm³ e atenção 361,30 m = 90,89 hm³.

---

## 1. Item 12 — HORA da crista nas grandes cheias

Formato: cidade | data | hora | nível (m) | régua | tipo | título | veículo | URL | pág. | trecho literal | arquivo

### Blumenau
| cidade | data | hora | nível (m) | régua | tipo | título | veículo | URL | pág. | trecho literal | arquivo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Blumenau | 2008-11-24 | 0h (fuso não declarado) | 11,52 | não declarada | PICO | Blumenau decreta estado de calamidade pública | Clicrbs/RBS (Defesa Civil), 24/11/2008 02h41 | http://www.clicrbs.com.br/especial/sc/sos-sc/19,0,2305644,Blumenau-decreta-estado-de-calamidade-publica.html | — | "O nível do rio Itajaí-Açu chegou a 11,52 metros à 0h desta segunda e baixou 5 centímetros até as 2h." | `Blumenau_clicrbs_calamidade_2008-11-24.html` |
| Blumenau | 2008-11-23 | 11h (fuso não declarado) | 10,06 | não declarada | LEITURA | CUHVA no estado: situação por município e das rodovias (atualização 14h30) | Acaert | https://www.acaert.com.br/noticia/967/cuhva-no-estado-situacao-por-municipio-e-das-rodovias-atualizacao-14h30 | — | "Às 11h deste domingo, o nível do Rio Itajaí-Açu ... estava em 10 metros e 6 centímetros" | `Acaert_2008-11-23.html` |
| Blumenau | 2008-11-24 | sem hora | 11,52 | não declarada | PICO | paper ABRH sobre barragem Norte, cheia 2008 | ABRH | ver arquivo | — | confirma 11,52 sem hora | `ABRH_barragem-norte_cheia2008.pdf` |
| Blumenau | 2008-11-24 | sem hora | **11,72** | não declarada (CEOPS) | PICO (tabela) | Esboços, Tabela 3 | UFSC/CEOPS | https://periodicos.ufsc.br/index.php/esbocos/article/download/2175-7976.2013v20n30p9/27829/118436 | PDF p. 12 | linha "2008 24/11 11,72m" (a coluna Timbó da mesma linha, 8,22m, tem alinhamento incerto) | `Esbocos_Rio-do-Sul_vulnerabilidades.pdf` |
| Blumenau | 2011-09-09 | 11h (fuso não declarado) | 12,60 | não declarada | PICO | Prefeitura de Blumenau admite que irá rever cotas de enchente (JSC via blog) | Novo Plantão Blumenau | http://moniquebecker.blogspot.com/2011/09/prefeitura-de-blumenau-admite-que-ira.html | — | "atingiram o pico de 12,60 metros às 11h de sexta-feira" | `Blumenau_moniquebecker_2011-09.html` |
| Blumenau | 2011-09-09 | 11h | 12,60 | CEOPS (citado no blog) | PICO, com série horária | Enchente em Blumenau setembro/2011 | blog Adalberto Day | https://adalbertoday.blogspot.com/2011/09/enchente-em-blumenau-setembro-2011.html | — | "10:00 = 12,56m 11:00 = 12,60m pico Segundo (Ceops), 12,80 ? 12:00 = 12,55m 13:00 = 12,52m" (fuso não declarado) | `Blumenau_adalbertoday_2011-09.html` |
| Blumenau | 2011-09-09 | sem hora | **12,8** | não declarada (CEOPS) | PICO (tabela) | Esboços, Tabela 3 | UFSC/CEOPS | idem Esboços | PDF p. 12 | linha "2011 9/09 12,8m" | `Esbocos_Rio-do-Sul_vulnerabilidades.pdf` |
| Blumenau | 2011-09 | sem hora | **13,0** | "estação fluviométrica de Blumenau" | máxima | Cotas-enchente do município de Blumenau | FURB/ABRH | link do item 11 | p. 1 | "atingiu o valor de 13,0 metros" | `ABRH_Cotas-enchente-Blumenau.pdf` |
| Blumenau | 2013-09-23 | 2h (fuso não declarado) | 10,51 | não declarada | PICO | Blumenau tem madrugada estável, e rio Itajaí-Açu começa a descer | G1 SC, 23/09/2013 06h33 | https://g1.globo.com/sc/santa-catarina/noticia/2013/09/blumenau-tem-madrugada-estavel-e-rio-itajai-acu-comeca-descer.html | — | "O pico do rio Itajaí-Açu ocorreu às 2h, com 10,51m" | `G1_blumenau_2013-09-23.html` |
| Blumenau | 2013-09-23 | 02h | 10,51 (00h 10,47; 01h 10,50; 03h 10,42) | "Fonte: CEOPS (Régua da Ponte Adolfo Konder)" | série horária | 2013 - Blumenau, rio Itajaí-Açu | blog Dalva Day, 21/09/2013 (atualizado) | http://dalvaday.blogspot.com/2013/09/2013-blumenau-rio-itajai-acu.html | — | "SEGUNDA - 23/SET 00h - 10,47 01h - 10,50 ..." | `Blumenau_dalvaday_2013-09.html` |
| Blumenau | 2015-10-23 | 1h (fuso não declarado) | 10,03 | não declarada | PICO | Deslizamento de terra em Blumenau atinge quatro casas | G1 SC, 23/10/2015 | https://g1.globo.com/sc/santa-catarina/noticia/2015/10/deslizamento-de-terra-em-blumenau-atinge-quatro-casas-ninguem-se-feriu.html | — | "depois de atingir um pico de 10,03m, à 1h, o Rio Itajaí-Açú baixou para 8,92 metros às 14h desta sexta-feira" | `G1_blumenau_2015-10-23.html` |
| Blumenau | 2015-10-22 | 22h | 9,87 | não declarada | LEITURA | Nível do rio Itajaí-Açu segue em emergência mesmo sem chuva | G1 SC | https://g1.globo.com/sc/santa-catarina/noticia/2015/10/nivel-do-rio-itajai-acu-segue-em-emergencia-mesmo-sem-chuva.html | — | "Às 22h, o Rio Itajaí-Açu atingiu 10,49 metros em Rio do Sul e 9,87 metros em Blumenau." | `G1_2015-10_nivel-segue-emergencia.html` |
| Blumenau | 2023-10-08 | ~02h15 (fuso não declarado) | 9,49 | AlertaBlu | PICO do 1º ciclo | Pico do nível do rio Itajaí-Açu em Blumenau atinge 9,49 metros e começa a baixar | ND Mais | https://ndmais.com.br/tempo/pico-do-nivel-do-rio-itajai-acu-em-blumenau-atinge-949-metros-e-comeca-a-baixar/ | — | "O pico do nível do rio ... atingiu 9,49 metros por volta das 2h15, de acordo com a medição do AlertaBlu" | `ND_blumenau_pico-949_2023-10-08.html` |
| Blumenau | 2023-10-09 | 06h (fuso não declarado) | 10,19 | não declarada | máxima do evento | Vídeos: Blumenau amanhece com rio acima dos 10 metros e em estabilização | ND Mais, 09/10/2023 | https://ndmais.com.br/tempo/videos-blumenau-amanhece-com-rio-acima-dos-10-metros-e-em-estabilizacao/ | — | "a marca mais alta alcançada nas últimas horas foi às 06h da manhã, de 10,19 metros, com uma leve queda na leitura das 07h" | `ND_blumenau_amanhece-acima-10m_2023-10-09.html` |
| Blumenau | 2023-10-10 | 18h | 7,98 | não declarada | LEITURA | Blumenau sai da situação de enchente e serviços voltam à normalidade | NSC Total, 10/10/2023 | https://www.nsctotal.com.br/cotidiano/blumenau-sai-da-situacao-de-enchente-e-servicos-voltam-a-normalidade | — | "saíram deste estado às 18h de ontem, com o Rio Itajaí-Açu em 7,98 metros" (esse texto diz "pico foi na madrugada de domingo (8) ... 10,19", **inconsistente quanto ao dia** com o ND, que dá 09/10) | `NSC_blumenau_sai-enchente_2023-10-10.html` |
| Blumenau | 2023-10-13 (virada 12/13) | meia-noite (fuso não declarado) | 10,75 (lista oficial: 12/10 = 10,76) | não declarada | PICO | Rio Itajaí-Açu começa a recuar em Blumenau | Mesorregional, 13/10/2023 | https://www.mesorregional.com.br/rio-itajai-acu-comeca-a-recuar-em-blumenau/ | — | "pico de 10,75 metros à meia-noite" | `Mesorregional_blumenau_2023-10-13.html` |
| Blumenau | 2023-11-17 | 9h45 (fuso não declarado) | 9,14 | não declarada | PICO ("pico momentâneo") | Atualização do quadro de enchente na manhã desta sexta (17/11) em Blumenau | O Blumenauense | https://oblumenauense.com.br/atualizacao-do-quadro-de-enchente-na-manha-desta-sexta-17-11-em-blumenau/ | — | "A Defesa Civil confirmou que o pico momentâneo do rio Itajaí-Açu em Blumenau foi de ... 9,14 metros às 9h45" | `OBlumenauense_2023-11-17.html` |
| Blumenau | 2024-05-19 | 12h (fuso não declarado) | 8,67 | não declarada | PICO | Blumenau amanhece com mais uma enchente neste domingo | O Auditório | https://oauditorio.com/noticias/geral-noticias/05/2024/blumenau-amanhece-com-mais-uma-enchente-neste-domingo/ | — | "atingiu de 8,67m às 12h"; às 13h estava em 8,65 | `Oauditorio_blumenau_2024-05-19.html` |

### Rio do Sul
| cidade | data | hora | nível (m) | régua | tipo | título | veículo | URL | pág. | trecho literal | arquivo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Rio do Sul | 2011-09-09 | 22h (fuso não declarado) | 12,91 | não declarada | PICO | Situação continua caótica em Rio do Sul e região | ND, 11/09/2011 | https://ndmais.com.br/noticias/situacao-continua-caotica-em-rio-do-sul/ | — | "pico máximo de 12,91 m, na sexta-feira às 22h" (divergem: 12,96 lista Defesa Civil de Rio do Sul; 12,98 Esboços/CEOPS) | `ND_riodosul_2011_caotica.html` (e `ND_riodosul_2011_estabilizado.html`) |
| Rio do Sul | 2015-10-23 | 6h e 9h | 10,71 (6h); 10,6 (9h) | não declarada | LEITURA | Deslizamento de terra em Blumenau atinge quatro casas | G1 SC, 23/10/2015 | https://g1.globo.com/sc/santa-catarina/noticia/2015/10/deslizamento-de-terra-em-blumenau-atinge-quatro-casas-ninguem-se-feriu.html | — | "Na medição feita às 9h, o Rio Itajaí-Açu chegou a 10,6m. Às 6h, o nível do rio era de 10,71m." (hora do pico não declarada; a lista do portal de Rio do Sul dá 10,71) | `G1_blumenau_2015-10-23.html` |
| Rio do Sul | 2015-10-22 | 22h | 10,49 | não declarada | LEITURA | Nível do rio Itajaí-Açu segue em emergência mesmo sem chuva | G1 SC | https://g1.globo.com/sc/santa-catarina/noticia/2015/10/nivel-do-rio-itajai-acu-segue-em-emergencia-mesmo-sem-chuva.html | — | "Às 22h, o Rio Itajaí-Açu atingiu 10,49 metros em Rio do Sul e 9,87 metros em Blumenau." | `G1_2015-10_nivel-segue-emergencia.html` |
| Rio do Sul | 2023-10-13 | 3h10 (fuso não declarado) | 11,86 | não declarada | PICO | Enchente de Rio do Sul atingiu pico de 11,86 metros | Rádio Mirador, 13/10/2023 | https://radiomirador.com.br/enchente-de-rio-do-sul-atingiu-pico-de-1186-metros/ | — | "pico de nível máximo às 3h10 da madrugada desta sexta-feira (13), com 11,86 metros" | `Mirador_riodosul_pico-1186.html` |
| Rio do Sul | 2023-11-18 | 0h40 (fuso não declarado) | 13,04 | não declarada | PICO | Rio do Sul enfrenta a segunda maior enchente histórica | GCD, 17/11/2023 23h29 | https://www.gcd.com.br/rio-do-sul/rio-do-sul-enfrenta-a-segunda-maior-enchente-historica/ | — | "O pico das águas foi de 13,04 metros às 0h40 deste sábado, 18. O volume supera o registro de setembro de 2011 quando o nível das águas foi de 12,96." Mesma matéria: "a cota de 13,53m marcou o mês de julho de 1983". | `GCD_riodosul_segunda-maior.html` |
| Rio do Sul | 2023-11-18 | 0h40 | 13,04 | não declarada | PICO | Cidade de SC registra segunda maior enchente da história | Jornal Universo, 20/11/2023 (segundo a Defesa Civil) | https://jornaluniversoonline.com.br/cidade-de-santa-catarina-registra-segunda-maior-enchente-da-historia/ | — | "atingiu 13,04 metros à 0h40 deste sábado (18/11) ... superada pela registrada em 1983, quando o rio chegou a 13,58 metros" | `Universo_riodosul_segunda-maior.html` |
| Rio do Sul | 2023-11-18 | **1h** | 13 m e 2 cm (13,02) | não declarada | PICO (segundo o JN) | Rio do Sul registra segunda maior enchente da história | G1/Jornal Nacional, 18/11/2023 | https://g1.globo.com/jornal-nacional/noticia/2023/11/18/rio-do-sul-em-sc-registra-segunda-maior-enchente-da-historia-da-cidade.ghtml | — | "O rio Itajaí-açu atingiu o nível máximo a 1h da madrugada: 13 metros e 2 centímetros." (**diverge** das demais: 13,04 às 0h40) | `G1_riodosul_2023-11-18.html` |

Divergência 1983 em Rio do Sul: 13,58 (Universo, lista do portal, ABRH) × 13,53 (GCD). Esboços escreve 15,58 no texto.

### Taió
| cidade | data | hora | nível (m) | régua | tipo | título | veículo | URL | pág. | trecho literal | arquivo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Taió | 2023-10-09 | 5h (fuso não declarado) | 12,11 | "no centro da cidade" | LEITURA (a hora da crista não foi encontrada) | Enchente histórica em Santa Catarina: cidade de Taió está debaixo d'água | MetSul | https://metsul.com/enchente-historica-em-santa-catarina-cidade-de-taio-esta-debaixo-dagua/ | — | "Medição das 5h desta segunda-feira indicou o rio com 12,11 metros no centro da cidade." | `MetSul_taio_2023.html` |
| Taió | 2023-10-09 | sem hora | 12 (arredondado) | não declarada | — | Rio atinge 12 metros e cidade ... amanhece com ruas inundadas | G1 SC, 09/10/2023 | https://g1.globo.com/sc/santa-catarina/noticia/2023/10/09/rio-atinge-12-metros-e-cidade-de-sc-amanhece-com-ruas-inundas-e-moradores-ilhados-video.ghtml | — | título "Rio atinge 12 metros" | `G1_taio_2023-10-09.html` |
| Taió | 2023-10 | sem hora | 12,11 | não declarada | "marca histórica" | Alto Vale segue em estado de emergência após registros históricos | Diarinho | https://diarinho.net/materia/647524/Alto-Vale-segue-em-estado-de-emergencia-apos-registros-historicos-de-enchentes- | — | "marca histórica de 12,11m" | `Diarinho_altovale_2023.html` |
| Taió | 2013-09-22 | 15h (fuso não declarado) | 8,78 | não declarada | LEITURA, "cota de emergência" | Chuvas volumosas e temporais já afetam 56 cidades em SC | blog SOS Rios do Brasil (cópia Wayback de 2018 de boletim da Defesa Civil) | https://web.archive.org/web/20181109172046/http://sosriosdobrasil.blogspot.com/2013/09/chuvas-volumosas-e-temporais-ja-afetam.html | — | "Conforme a última medição (15h) da rede de monitoramento da Bacia, estão com cota de emergência as seguintes estações: Blumenau (9,59m), Indaial (6,26m), Rio do Sul (10,08m), Taió (8,78m), Brusque (6,51m) e Benedito Novo (5,03m). Estão com cota de Alerta: Apiúna..." (mesma lista: Apiúna 7,94 alerta; Ituporanga 3,58 alerta; Rio do Oeste 8,79; Gaspar 7,21) | `SOSRios_wayback_2013-09.html` |

### Gaspar (os números são "metros acima da normalidade", termo da fonte; não é leitura de régua com zero declarado)
| cidade | data | hora | nível | régua | tipo | título | veículo | URL | pág. | trecho literal | arquivo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gaspar | 2023-10-09 | 7h50 | 7,09 m acima da normalidade | não declarada | PICO | Boletim Defesa Civil – 10/10 – 17h | Prefeitura de Gaspar | https://www.gaspar.sc.gov.br/boletim-defesa-civil-10-10-17h/ | — | "O nível do rio atingiu seu pico às 7h50 de segunda-feira (9) com 7,09 metros acima da normalidade" (Jornal Metas confirma: `JornalMetas_2023-10.html`) | `Gaspar_boletim_10-10-17h.html` |
| Gaspar | 2023-10-12 | 18h | 7,10 | idem | LEITURA | Boletim 12/10 – 18h | Prefeitura de Gaspar | https://www.gaspar.sc.gov.br/boletim-defesa-civil-12-10-18h/ | — | boletim | `Gaspar_boletim_12-10-18h.html` |
| Gaspar | 2023-10-12 | 21h | 7,34 | idem | LEITURA | Boletim 12/10 – 21h | idem | https://www.gaspar.sc.gov.br/boletim-defesa-civil-12-10-21h/ | — | boletim | `Gaspar_boletim_12-10-21h.html` |
| Gaspar | 2023-10-13 | 0h (boletim publicado 13/10 às 00h06 BRT, atualizado 1h) | 7,44 | idem | LEITURA | Boletim 12/10 – 0h | idem | https://www.gaspar.sc.gov.br/boletim-defesa-civil-12-10-0h/ | — | "atingiu 7, 44 metros acima da normalidade às 0h" | `Gaspar_boletim_12-10-0h.html` |
| Gaspar | 2023-10-13 | 3h | 7,48 | idem | LEITURA (o boletim não usa "pico") | Boletim 13/10 – 3h | idem | https://www.gaspar.sc.gov.br/boletim-defesa-civil-13-10-3h/ | — | "atingiu 7, 48 metros acima da normalidade às 3h"; "não atingiu os 7,60 metros, estimado para às 2h" | `Gaspar_boletim_13-10-3h.html` |
| Gaspar | 2023-10-13 | 6h | 7,41 | idem | LEITURA | Boletim 13/10 – 6h | idem | https://www.gaspar.sc.gov.br/boletim-defesa-civil-13-10-6h/ | — | "atingiu 7,41 metros acima da normalidade às 6h"; desde as 4h o rio desceu 6 cm | `Gaspar_boletim_13-10-6h.html` |
| Gaspar | 2023-10-13 | 9h | 7,22 | idem | LEITURA | Boletim 13/10 – 9h | idem | https://www.gaspar.sc.gov.br/boletim-defesa-civil-13-10-9h/ | — | boletim | `Gaspar_boletim_13-10-9h.html` |

### Outros (Indaial, Brusque, Botuverá, Vidal Ramos, Ascurra, barragens)
| cidade | data | hora | nível (m) | régua | tipo | título | veículo | URL | pág. | trecho literal | arquivo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Indaial | 2023-10-04 | 20h | 5,75 (07h de 05/10: 5,35) | não declarada | "máxima registrada" | Indaial em estado de alerta: 13 bairros atingidos | Vale do Itajaí Notícias, 05/10/2023 | https://valedoitajainoticias.com.br/indaial-em-estado-de-alerta-sao-13-bairros-atingidos-e-es/ | — | "A máxima registrada às 20h de ontem (04), foi de 5,75 metros ... Às 07h da manhã desta quinta-feira (05), o nível do Rio alcançou 5,35 metros" | `Indaial_valedoitajai_2023-10.html` |
| Brusque | 2023-11-17 | ~21h (fuso não declarado) | 8,96 | não declarada | PICO | Enchente desta sexta-feira é terceira maior registrada em Brusque | O Município, 18/11/2023 | https://omunicipio.com.br/clima/enchente-desta-sexta-feira-e-terceira-maior-registrada-em-brusque/ | — | "O pico do rio Itajaí-Mirim foi de 8,96 metros por volta das 21h. Os dados são da Defesa Civil" ; "1984 e 2011 ... 10,30 m ... 10,03 m" | `OMunicipio_brusque-terceira-maior.html` (e `SCC10_brusque-12-cheias.html` confirma 8,96) |
| Brusque | 2011-09 | sem hora | 10,03 (O Município 2023) × 10,3 (O Município 09/09/2026) × 10,21 (Esboços/CEOPS) | não declarada | PICO (todos sem hora) | Enchente completa 15 anos | O Município, 09/09/2026 | https://omunicipio.com.br/clima/enchente-completa-15-anos-veja-como-brusque-ficou-em-setembro-de-2011/ | — | "Cheia fez o nível do rio Itajaí-Mirim chegar a 10,3 metros" | `OMunicipio_brusque_2011-15anos.html` |
| Brusque | 2008-11 | sem hora | 8,88 | não declarada | PICO | O Município, "Mais água, menos danos" (20/11/2023) | O Município | https://omunicipio.com.br/clima/mais-agua-menos-danos-o-que-levou-enchente-de-sexta-causar-estragos-menores-que-tragedia-de-2008-em-brusque/ | — | consta 8,88 (conferir trecho no arquivo); também diz que a medição mudou a partir de 1978 | `OMunicipio_brusque-mais-agua-menos-danos.html` |
| Botuverá | 2026-07-22 | 13h | 4,80 | não declarada (rio Itajaí-Mirim) | PICO | Pontes interditadas pelas chuvas são liberadas em Botuverá | O Município, 22/07/2026 | https://omunicipio.com.br/clima/pontes-interditadas-pelas-chuvas-sao-liberadas-em-botuvera/ | — | "O rio Itajaí-Mirim atingiu o pico de 4,80 metros às 13h, em Botuverá, e desde então apresenta redução no nível." | `OM_botuvera_pontes.html` |
| Botuverá | 2026-09-01 | ~2h | 5,85 | não declarada | pico (Defesa Civil de Brusque) | Defesa Civil projeta pico de 5,50 metros no rio Itajaí-Mirim por volta das 10h | Diplomata FM, 01/09/2026 | https://www.diplomatafm.com.br/2026/09/01/defesa-civil-projeta-pico-de-550-metros-no-rio-itajai-mirim-por-volta-das-10h/ | — | "em Botuverá, por volta das 2h da madrugada, o pico foi de 5,85 metros" | `Diplomata_pico550.html` |
| Vidal Ramos | 2026-09-01 | "ao longo da noite" | 3,87 | não declarada | "novos picos" | idem | Diplomata FM | idem | — | "em Vidal Ramos, o nível chegou a 3,87 metros" | `Diplomata_pico550.html` |
| Ascurra | 2026-09-01 | ~6h (8h: 10,05; 11h: 9,82) | 10,13 | "Ponte do Beber" | LEITURA (não declarado pico) | Rio avança, ultrapassa 10 metros e bloqueia rua em Ascurra | ND Mais, 01/09/2026 | https://ndmais.com.br/tempo/rio-avanca-ultrapassa-10-metros-bloqueia-rua-em-ascurra/ | — | "O rio atingiu 10,13 metros por volta das 6h, na medição da Ponte do Beber"; "10,05 metros às 8h e recuou para 9,82 metros às 11h" | `ND_ascurra_rio-avanca-ultrapassa-10m.html` |
| Barragem Sul (Ituporanga) | 2015-10-22/23 | 12h | ocupação 122,8% (22h) | — | contexto | Nível do rio segue em emergência | G1 SC | link G1 2015-10 acima | — | "Na barragem de Ituporanga, às 22h, a ocupação era de 122,8% ... Ela transbordou às 12h." | `G1_2015-10_nivel-segue-emergencia.html` |
| Barragem Oeste (Taió) | 2015-10-22 | perto das 18h | ocupação 110,8% | — | contexto | idem | G1 SC | idem | — | "A barragem transbordou perto das 18h. Uma hora depois, três das sete comportas foram abertas." | idem |
| Barragens Oeste e Sul | 2023-10-08 | Taió 1h15; Ituporanga 7h30 | — | — | contexto (início do vertimento) | Barragens de Taió e Ituporanga ... começam a verter | NSC | URL do item 16 | — | "começou a verter por volta da 1h15min da madrugada"; "a barragem começou a verter às 7h30min deste domingo (8)" | `NSC_barragens-taio-ituporanga-verter.html` |

Sem hora de crista nova achada para: Ituporanga, Lontras, Ibirama, Apiúna, Ilhota (sem régua, rodada 2), Itajaí, Timbó, Taió (o 11,86 às 02h21 é da rodada 1), e Blumenau 2023-10-12/13 (só "meia-noite"). Brusque 2011 e 2008, Indaial 2008/2011/2013/2015: nada com hora.
Taió, notícia municipal 75218 (20/09/2013), régua do Centro: "Às 17h desta sexta-feira o nível do rio Itajaí do Oeste estava em 5,46 metros ... A primeira cota de enchente da cidade de Taió acontece quando o rio atinge 7,5 m[etros], na região da antiga Apae" — LEITURA e COTA de enchente (https://www.taio.sc.gov.br/noticia-75218/, `Taio_noticia-75218.html`).

---

## 2. Item 13 — Cotas oficiais com nome de régua

| cidade | data | hora | nível (m) | régua | tipo | título | órgão | URL | pág. | trecho literal | arquivo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Ibirama (rio Hercílio) | — | — | — | — | — | nada encontrado | — | — | — | Esboços/CEOPS dá picos de Ibirama (1983 7,15; 2010 4; 2011-09-09 4,97; 2011-08-31 3,81) sem nome de régua nem cota de alerta | `Esbocos_Rio-do-Sul_vulnerabilidades.pdf` (contexto) |
| Apiúna | 2013-09-22 | 15h | 7,94 | não declarada | LEITURA, "cota de Alerta" (a estação está na categoria Alerta) | boletim SOS Rios (Defesa Civil) | Defesa Civil via blog | link SOSRios acima | — | "Estão com cota de Alerta: Apiúna ..." | `SOSRios_wayback_2013-09.html` |
| Botuverá | — | — | — | — | — | nada encontrado (nenhuma estação de Brusque nomeada: 18, 2 ou 32) | — | — | — | — | — |
| Guabiruba (DCSC-00029) | — | — | — | — | — | nada encontrado | — | — | — | — | — |
| Vidal Ramos | — | — | — | — | — | nada encontrado (cota oficial). Uma frase de busca sobre "3,54 m, nível de atenção" não está em nenhum arquivo salvo e **não entra** | — | — | — | — | — |
| Lontras | — | — | — | — | — | nada encontrado (continua só a "segurança observada" 9,20 m que você já tinha) | — | — | — | — | — |
| Ascurra (extra) | 2026-09-01 | — | monitoramento até 8,50; atenção 8,50–9,76; alerta 9,76–10,76; emergência acima de 10,76 | "Ponte do Beber" (régua citada na mesma matéria) | COTA (classificação da Defesa Civil Municipal) | Rio avança, ultrapassa 10 metros ... em Ascurra | ND Mais | https://ndmais.com.br/tempo/rio-avanca-ultrapassa-10-metros-bloqueia-rua-em-ascurra/ | — | "o rio fica em nível de monitoramento até 8,50 metros. Entre 8,50 e 9,76 metros, a situação é considerada de atenção. De 9,76 a 10,76 metros, entra na faixa de alerta, enquanto níveis acima de 10,76 metros são classificado[s]..." | `ND_ascurra_rio-avanca-ultrapassa-10m.html` |
| Blumenau (extra) | — | — | Normalidade 0–3; Observação 3–4; Atenção 4–6; Alerta 6–8; Alerta Máximo >8 | AlertaBlu | COTA | Critérios de Nível do Rio | Defesa Civil de Blumenau | https://defesacivil.blumenau.sc.gov.br/c/meteorologia/legenda_nivel_rio | — | "Fonte: Adaptado de AlertaRio" | `DefesaCivilBlumenau_c_meteorologia_legenda_nivel_rio.html` |
| Taió (extra) | 2013-09-20 | 17h | primeira cota de enchente: 7,5 | régua do Centro (região da antiga Apae) | COTA | notícia 75218 | Prefeitura de Taió | https://www.taio.sc.gov.br/noticia-75218/ | — | "A primeira cota de enchente da cidade de Taió acontece quando o rio atinge 7,5 metros, na região da antiga Apae" | `Taio_noticia-75218.html` |
| Rio do Sul (extra) | — | — | 6,60 | "cota" na régua da estação | COTA de início de inundação de edificações | ARMAX Rio do Sul | CEOPS/ABRH | link item 10 | p. 1 | "as primeiras edificações começam a ser inundadas quando o rio ... atinge a cota 6,60m" | `ABRH_ARMA_RioDoSul_2011.pdf` |

---

## 3. Itens 1 a 6 (fontes novas)

### Item 1 — Ascurra (Ponte do Beber, DCSC-00003)
Nada encontrado para nov/2008, set/2011, set/2013, out/2015, out/2023, nov/2023 e mai/2024. Só o evento novo de 2026-09-01 (linhas acima, em item 12 e item 13). ND Mais (12/12/2023, `ND_ascurra_siga-e-pare-2.html`, https://ndmais.com.br/transito/br-470-tera-esquema-siga-e-pare-nesta-terca-feira-em-ponte-de-ascurra/): "instalação de uma nova Estação Hidrológica da Defesa Civil para monitorar a situação do Rio Itajaí-Açu, sob a ponte conhecida como Irineu Bornhausen" (km 88 da BR-470, instalação prevista para a tarde de 12/12/2023). A matéria não diz "Ponte do Beber" nem o código DCSC-00003; a ligação Ponte do Beber = Irineu Bornhausen **não está em nenhum arquivo**.

### Item 2 — Guabiruba (DCSC-00029)
Nada com nível em régua local. Guabiruba 46906: 403 e Wayback 404. Um resultado de busca citava "25,14 metros" para Guabiruba (cota ortométrica, não serve; sem arquivo salvo, não entra).

### Item 3 — Itajaí (1B)
Nada encontrado. Monografia de Anderson Ficagna Passos (UNIVALI) e série telemétrica de set/2011 (tese de Valdeir): **não pesquisadas especificamente nesta rodada**. Itajaí consta apenas na tabela JICA 7.5.1 (modelada).

### Item 4 — Boletins SDE/SC
| cidade | data | hora | nível | régua | tipo | título | órgão | URL | pág. | trecho literal | arquivo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bacia | 2026-06 | — | — | — | — | Boletim Hidrometeorológico nº 87, 007/2026 (publicado 07/07/2026) | SDE/SC (Águas) | https://www.aguas.sc.gov.br/instrumentos/ferramentas-de-gestao/monitoramento-instrumentos/boletim-hidrometeorologico | PDF p. 1 (ver arquivo) | "Durante o mês, não foi registrado nenhuma estação em cotas para eventos de enchentes/inundações" | `SDE_Boletim_Hidrometeorologico_87_007-2026.pdf`; listas `SDE_pagina_boletim-hidrometeorologico.html`, `SDE_tag-boletim_lista.html` |

Baixei os 87 PDFs listados no site (001–017/2020 a 2024, nº 41 e 62–87); só a ed. 87 ficou no zip. A tabela "Níveis máximos atingidos nos eventos de inundação" só existe em 62 (006/2024), 011/2023 e 001/2024, que você já tem. Edições 88–90 (set/2026) não existem no site (devolve HTML; índice termina em 07/2026). Ago/2023 (008/2023) você já tem. Antes de 2020 não há boletim na lista (out/2015, jun/2017: nada).

### Item 5 — Lontras, Vidal Ramos, Trombudo Central, Botuverá, Ituporanga, Ibirama, Apiúna, Ilhota
Nada encontrado além das linhas de Botuverá, Vidal Ramos e Apiúna acima. Brusque: ver tabela "Outros". Ituporanga (Ponte Vitório Sens): nada novo; a leitura 3,58 m de 22/09/2013 15h (SOSRios, "cota de Alerta") é a única nova, sem nome de régua. Trombudo Central, Lontras (cheias 1983–2024), Ilhota, Ibirama: nada.

### Item 6 — Timbó, Taió, Rio dos Cedros
- **Timbó**: 9,58 m de 2014 não encontrado. Esboços/CEOPS (régua não declarada) traz 9,86 em 2011-09-09, 8,7 em 1983-07-09 (alinhamento incerto), 8,22 em 2008-11-24 (alinhamento incerto), 7,95 em 2001-10-01 (alinhamento incerto) e 8,76/6,21 para 2011-08-31 (alinhamento incerto). PDF p. 11–12.
- **Taió**: o mês da cheia de 1983 (11,85 m) não tem fonte nova. Set/2013, régua do Centro: leituras (5,46 às 17h de 20/09/2013 e 8,78 às 15h de 22/09/2013), não o pico. A notícia 75219 não traz número.
- **Rio dos Cedros depois de nov/2022**: nada baixado. Misturebas (4,80 m, 04/10/2023) e Testo (5,32 m, 03/11/2023) vieram de resumo de busca, e os arquivos não foram obtidos (Cloudflare/404 no Wayback).

---

## 4. Divergências (todas as fontes listadas)
- Blumenau 2008-11-24: 11,52 (Clicrbs, ABRH, lista AlertaBlu) × 11,72 (Esboços/CEOPS).
- Blumenau 2011-09-09: 12,60 (JSC, Adalberto Day citando CEOPS, lista AlertaBlu) × 12,8 (Esboços/CEOPS; o blog também escreve "12,80 ?") × 13,0 (paper ABRH/FURB).
- Blumenau 1983-07-09 e 1984-08-07: lista AlertaBlu 15,34 e 15,46 × ANA 83800002 "1519" e "1485" (unidade não declarada no XML). Esboços: 15,34 em 1983.
- Zero/referência: paper FURB diz 40 cm; ND 2013 diz 20 cm entre régua CEOPS e régua da Prefeitura; JSC 2011 diz 10 cm de diferença revisada em 1992.
- Blumenau out/2023: 9,49 (08/10 ~02h15), 10,19 (09/10 06h), 10,75 ou 10,76 (12–13/10). O NSC situa o 10,19 na madrugada de 08/10; ND e a lista oficial dizem 09/10.
- Rio do Sul 2011: 12,91 (ND) × 12,96 (lista do portal, GCD) × 12,98 (Esboços). 1983: 13,58 × 13,53. 1911: 12,20 × 12,8 (texto de Esboços). 2023-11: 13,04 às 0h40 (GCD, Universo) × "13 m e 2 cm" a 1h (JN/G1).
- Taió 2023-10-09: 12,11 (5h, MetSul; "marca histórica" Diarinho) × 12 (G1) × 11,86 às 02h21 (rodada 1).
- Brusque 2011: 10,03 × 10,3 × 10,21.
- Barragens: 83 / 93,5 (JICA, bruta) × 100 / 110 (NSC, pós-alteamento) × 104,03 (RWTV, Sul) × 99,96 (painel Asthon, não achado).

---

## 5. Falhas (403/404/timeout/login)
- marinha.mil.br/chm (tabuas-de-mare e página de dados): 403 Cloudflare no curl. Contornado com Wayback (capturas de 21 e 28/09/2026). Paginação `?page=1..3` no Wayback: 404.
- alertablu.blumenau.sc.gov.br: erro de certificado SSL e redirecionamento para defesacivil.blumenau.sc.gov.br; baixado com `curl -skL`. A rota /d/barragens falhou.
- ANA HidroWeb REST (snirh): 401 (token). Usado o serviço ServiceANA.asmx; o método HidroSerieCotas não existe.
- defesacivil.sc.gov.br: inacessível (timeout). Manual de Operação de Barragens: tentativa de rebaixar falhou (000); você já tem a cópia.
- aguas.sc.gov.br: boletins 88–90 inexistentes (devolve HTML).
- Guabiruba noticia-46906: 403 e Wayback 404.
- Taió 75218/75219 e Gaspar (boletins): 403 no curl simples, recuperados com cookie de desafio (get.sh). A 75219 é duplicata da rodada 1 e ficou fora do zip.
- Misturebas (Taió/Rio dos Cedros) e Olhar do Vale (Indaial): só página de desafio; descartados.
- docplayer e TCC do CBMSC (Laurentino): timeout; Wayback 404.
- Blog Dalva Day 2011: 302 vazio. sosriosdobrasil.blogspot: 302; usado o Wayback.
- UDESC repositório (HEC-HMS barragem Oeste): 751 bytes, inútil, descartado.
- monitoramento.defesacivil.sc.gov.br (API interna) e Facebook/Instagram: não consultados.
- Números só vistos em resultado de busca, sem arquivo (ex.: 13,04 em portalinsights, cotas 4,50/5,50/6,50 de Rio do Sul, "Ponte do Beber = Irineu Bornhausen"): ficaram de fora.
- Arquivos descartados do zip por serem inúteis ou duplicados: `Misturebas_taio_2023-10-13.html`, `Taio_noticia-75219.html`, `Guabiruba_wayback_noticia-46906.html`, `UDESC_repo_HEC-HMS-barragem-oeste.html`, `ND_ituporanga-40cm-verter.html`, `OCP_barragem-sul-verter.html`, `Araguaia_440.html`. Como o trecho do OCP (03/11/2023, "cota de 31 metros (IBGE 401,00m)") **não está mais no zip**, não use esse número.

## 6. Nada encontrado, por item
- 14: tábua 2027 não publicada nas capturas consultadas.
- 12: hora da crista não encontrada para Taió 2023 (só 5h = 12,11), Ituporanga, Lontras, Ibirama, Apiúna, Ilhota, Itajaí, Timbó, Blumenau 2023-10-12/13 além de "meia-noite", Brusque 2008/2011, Indaial 2008/2011/2013/2015, Gaspar 2008/2011/2013/2015, Rio do Sul 2011 além de 22h, Rio do Sul 2015 (só leituras), Rio do Sul 2023-10-13 em diante (ok), Ascurra, Vidal Ramos, Botuverá 2008–2023.
- 13: Ibirama, Botuverá, Guabiruba, Vidal Ramos e Lontras: cota oficial com nome de régua não encontrada.
- 10: nenhum documento diz a régua do "Histórico de Cheias" nem que a régua mudou de lugar; DCSC-00013 "MKS" não tratada.
- 11: Tabela 4 de Cordero & Medeiros não achada; lista de 102 enchentes sem referência declarada.
- 16: nenhuma fonte define "volume útil" ou "de amortecimento"; 99,96 do painel Asthon não achado.
- 1, 2, 3, 5 e 6: ver notas por item acima.
