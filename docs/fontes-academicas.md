# Fontes acadêmicas — o que cada universidade tem e como usar

> Levantamento de 30/08/2026. Complementa `docs/cotas-de-ruas.md`. Tudo o que já foi incorporado
> em `data/` está marcado com ✔; o resto são tarefas ou pedidos pendentes.

## FURB (Blumenau) — CEOPS e LabGeo

| Material | O que contém | Onde | Status |
|---|---|---|---|
| Cordero & Medeiros, *Estudo estatístico das vazões máximas do rio Itajaí-Açu em Blumenau* (XV SBRH/ABRH) | **Tabela 4: todos os picos > 8 m em Blumenau de 1852 a 2001 com data** (72 registros, referência IBGE = régua + 0,20 m); curva-chave de Blumenau; níveis por período de retorno (TR 2 a 1000 anos) | https://files.abrhidro.org.br/Eventos/Trabalhos/154/291.pdf | ✔ incorporado em `data/enchentes.json` (eventos + `_meta.curva_chave_blumenau` + `_meta.periodos_retorno_blumenau_m`) |
| CEOPS/FURB, *Cotas-enchente do município de Blumenau* (SBRH 2013) | Metodologia do levantamento pós-2011: 1.851 pontos topográficos, referenciados à régua da ANA no Centro; linha d'água de 3 enchentes | https://files.abrhidro.org.br/Eventos/Trabalhos/66/SBRH2013__PAP013055.pdf | ler; extrair Tabela 2 (níveis das 3 enchentes) |
| CEOPS/FURB (Nicoletti, Luconi, Moser, Refosco & Severo), *Validação de MDT em mapeamento de inundação* (Blumenau e Timbó) | Carta-enchente 2011: Blumenau 13,00 m, Timbó 9,86 m; **acurácia medida das manchas** (Blumenau OA 89,05 % CEOPS / 85,12 % MDT-SDS; Timbó 74,1 % / 71,76 %); tolerâncias aceitas (20 cm carta-enchente, 50 cm cota-enchente); a receita de 6 passos, incluindo a conversão geométrica→ortométrica por modelo geoidal; e a frase *"os eventos de enchentes não tendem a linearização"* | https://files.abrhidro.org.br/Eventos/Trabalhos/60/PAP022777.pdf | ✔ picos em `enchentes.json`; acurácia e método extraídos em `docs/MDT-SC-E-CARTA-ENCHENTE.md` |
| CEOPS/FURB, *Análise hidrometeorológica do evento de 2008* | Pico em Blumenau 24/11/2008 = 11,52 m (TR ~10 anos); chuva de nov/2008 com TR > 3000 anos | https://files.abrhidro.org.br/Eventos/Trabalhos/153/ (PDF do evento) | ✔ pico incorporado |
| CEOPS/FURB, *Levantamento de cotas-enchente de Brusque* | Cotas rua a rua de Brusque com base nas marcas de 2011, até cota 15 m; estudo estatístico de níveis máximos do Itajaí-Mirim em Brusque; linha d'água | ResearchGate (resumo) — pedir PDF ao LabGeo/FURB | pedido enviado 30/08 |
| CEOPS/FURB, *Cotas de enchente de Gaspar* (2016–2017, coord. Ademar Cordero) | Cotas rua a rua de Gaspar referenciadas à régua da ANA (empresa Círculo); mapa de inundação | Site da Defesa Civil de Gaspar ("Pesquise sua cota") | investigar endpoint |
| LabGeo/FURB — GeoServer | Camadas WMS, inclusive carta-enchente de Blumenau 2011 (12,8 m) | https://labgeo.furb.br/ | pedido enviado 30/08 |
| Acervo CEOPS | Série de picos 1852–2022, boletins, tempos de trânsito | http://ceops.furb.br/ (bloqueia robôs) | pedido enviado 30/08 |
| **SDS/SC — Levantamento Aerofotogramétrico do Estado** (Engemap, 2010–2012) | **MDT e MDS de 1,0 m** em GEOTIFF, ortofotos de 0,39 m e hidrografia restituída 1:10.000 ottocodificada, cobrindo os 97.037 km² do estado; o Vale do Itajaí foi prioridade no plano de voo. É aerofotogrametria, **não LiDAR**, e é de 2012. | https://sigsc.sc.gov.br/download/ | não baixado — ver `docs/MDT-SC-E-CARTA-ENCHENTE.md`; conferir os termos de uso antes |

Nota: a Tabela 4 usa referência IBGE (régua + 0,20 m). O site deve exibir na régua local; converter subtraindo 0,20 m ou mostrar a referência. Os valores mais citados na imprensa (15,34 m em 1983, 15,46 m em 1984) batem com a tabela IBGE, então a imprensa provavelmente já usa IBGE — **confirmar com a FURB antes de converter**.

## UFSC (Florianópolis)

| Material | O que contém | Onde | Status |
|---|---|---|---|
| Luiz Felipe da Silva, TCC 2025, *Mapeamento de suscetibilidade a inundações da Bacia do Rio Itajaí* | Inventário com polígonos/pontos de inundação fornecidos pelas Defesas Civis de Blumenau, Brusque, Gaspar, Itajaí e Rio do Sul, unificados no QGIS; áreas alagadas por NDWI (satélite); mancha TR 50 anos do Banco Mundial; modelo em Python/scikit-learn | https://repositorio.ufsc.br/bitstream/handle/123456789/266382/TCC_LuizFelipeDaSilva.pdf | ler Tabela 1 (lista dos registros usados); pedir shapefiles ao autor |
| Dissertação PPGEA, *Mapeamento de risco de inundação na bacia do Itajaí-Açu com descritores de terreno* (HAND/f2HAND) | Metodologia que reproduz 92% da mancha de 2011; útil se quisermos gerar manchas para cidades sem carta-enchente | https://repositorio.ufsc.br/handle/123456789/192967 | referência |
| TCC (Laís), *Enchentes em Rio do Sul — medidas estruturais* | Histórico de Rio do Sul, AVADANs | https://repositorio.ufsc.br/xmlui/bitstream/handle/123456789/127455/TCC-Lais-FINAL.pdf | referência |
| SMC-Brasil (UFSC/MMA) — *Níveis e cota de inundação* | Metodologia de inundação costeira/maré para a costa brasileira | https://smcbrasil.paginas.ufsc.br/ | referência para o módulo de maré em Itajaí |

## Univali (Itajaí)

| Material | O que contém | Onde | Status |
|---|---|---|---|
| Marégrafo Cabeçudas (Univali/Porto de Itajaí) | Nível do mar por radar, a cada 10 min, integrado à telemetria da Defesa Civil | https://defesacivil.itajai.sc.gov.br/monitoramento/mares | em instalação; sem dado ainda |
| Projeto MAPI/LibGeo | Estação meteorológica no molhe sul (desde 2018, 5 min), nível d'água do estuário, batimetria | https://libgeo.acad.univali.br/mapi/ (bloqueia robôs) | pedido enviado 30/08 |
| TCC Oceanografia (André do Nascimento Ferreira), levantamento hidrográfico do estuário | Histórico de dragagens 1958–2009, regime de maré, cotas topográficas | https://biblioteca.univali.br/pergamumweb/vinculos/pdf/Andre%20do%20Nascimento%20Ferreira.pdf | referência |
| Sala de Monitoramento e Alerta COMPDEC/Univali | Avisos meteorológicos da Defesa Civil de Itajaí são emitidos em parceria com a Univali | https://defesacivil.itajai.sc.gov.br/ | contexto |

## Outras fontes técnicas (não universitárias, mas usadas pelas universidades)

| Material | O que contém | Onde |
|---|---|---|
| JICA, *Estudo preparatório para o projeto de prevenção e mitigação de desastres na Bacia do Rio Itajaí* | Tempos de trânsito da onda de cheia, diagnóstico das cidades prioritárias (Blumenau, Itajaí, Brusque, Rio do Sul), crítica à retificação do Itajaí-Mirim ("enchentes chegam mais rápido em Itajaí") | https://www.aguas.sc.gov.br/base-documental-rio-itajai/ |
| Plano de Recursos Hídricos da Bacia do Itajaí (Águas SC / Comitê do Itajaí) | Séries, estações, diagnóstico | https://www.aguas.sc.gov.br/ |
| GeoItajaí (Prefeitura, GitHub, MIT) | Manchas de inundação 1983–2015 em GeoJSON | https://github.com/geoitajai/sie — ver `docs/cotas-de-ruas.md` |

## Tarefas para o Claude Code

1. `scripts/validar_enchentes.py`: checar duplicatas, datas válidas e ordenar `data/enchentes.json`. ✔ dados já inseridos
2. Na tela do Itajaí-Açu, usar `_meta.periodos_retorno_blumenau_m` para rotular o gráfico de picos de Blumenau
   ("TR 10 anos ≈ 11,9 m", "TR 100 anos ≈ 15,8 m").
3. Adicionar seletor de referência (régua / IBGE) nos gráficos de Blumenau, aplicando ±0,20 m.
4. Baixar o PDF do TCC da UFSC (`repositorio.ufsc.br`) e transcrever a Tabela 1 para
   `data/manchas/inventario-ufsc.json` (cidade, evento, tipo de registro, origem).
5. Ler o PDF SBRH 2013 (cotas-enchente de Blumenau) e registrar a Tabela 2 em `enchentes.json`.
6. Quando a FURB responder: substituir os picos `confianca: media/baixa` de 2002–2026 pela série oficial.


## O que a tabela do AlertaBlu acrescenta — e o que ela complica (01/09/2026)

Um documento de mapeamento de fontes relatou que o AlertaBlu publica, em `/p/enchentes`, a
**tabela histórica oficial de Blumenau: 102 enchentes entre 1852 e 2024**, e concluiu que ela
"confirma que a série popular está em referência IBGE". Os quatro valores citados foram conferidos
contra `data/enchentes.json`. **Três batem; o quarto não, e é justamente o que importa.**

| evento | AlertaBlu (relatado) | nosso registro | referência do nosso |
|---|---|---|---|
| 1880 | 17,10 | **17,10** | IBGE (régua + 0,20 m) |
| jul/1983 | 15,34 | **15,34** | IBGE (régua + 0,20 m) |
| ago/1984 | 15,46 | **15,46** | IBGE (régua + 0,20 m) |
| set/2011 | 12,60 | **12,80** adotado · divergências **13,00** e **12,60** | `null` |

Para os três eventos antigos, a coincidência ao centavo com a série rotulada IBGE é real e vale
como corroboração de que a tabela do AlertaBlu e a série popular são a mesma série.

**Mas 2011 desmonta a conclusão, e desmonta pelo lado que interessa.** O valor de 12,60 já estava no
nosso arquivo — como divergência, atribuída a "Imprensa". Se ele vem do AlertaBlu, ele não é
imprensa: é a **própria Defesa Civil de Blumenau**. E aí a conta muda de forma:

* CEOPS/FURB, Ponte Adolfo Konder: **13,00 m**
* Defesa Civil (AlertaBlu): **12,60 m**
* diferença: **0,40 m**, e não 0,20 m

A regra bloqueante do `CLAUDE.md` se apoia em "set/2011 = 13,00 m (CEOPS) vs 12,80 m (Defesa Civil),
diferença exata de 0,20 m". O 12,80 é o valor que **nós adotamos** para a série municipal, com fonte
"ABRH / CEOPS-FURB" — não uma leitura publicada pela Defesa Civil. Se a Defesa Civil publica 12,60,
a evidência fundadora da regra precisa ser reexaminada: ou há três leituras do mesmo pico em três
referências, ou uma das atribuições está trocada.

**Nada foi alterado por causa disto**, e é deliberado. O arquivo
`blumenau-enchentes-registradas-alertablu.json` que sustentaria a afirmação **não chegou ao
repositório** — o relato dele chegou, o dado não. Mudar a referência de 113 registros de Blumenau a
partir de um resumo de segunda mão seria exatamente o erro que a regra existe para impedir.

**O que resolve, em ordem de força:**

1. O arquivo em si. Com `data/brutos/blumenau-enchentes-registradas-alertablu.json` no repositório,
   dá para cruzar os 102 eventos contra os nossos 113 de uma vez, e o padrão das diferenças —
   constante em 0,20 m, constante em 0,40 m, ou irregular — responde sozinho.
   **A análise já está escrita e testada**, em `scripts/conferir_blumenau_alertablu.py`: ela roda no
   instante em que o arquivo aparecer. Uma coisa que ela faz e que uma comparação ingênua não faria:
   separa os pares cujo registro nosso está **rotulado IBGE** dos **sem rótulo**, e compara os dois
   grupos. Uma mediana única sobre grupos que se comportam diferente devolve um número que não
   descreve nenhum dos dois — e é exatamente esse o caso que 1880/1983/1984 batendo e set/2011
   fugindo 0,40 m sugere. Quando os grupos discordam, o veredito é **"não converter"**, e não um
   deslocamento médio.
2. O teste no HidroWeb (estação 83800002, cotas de 09/07/1983 e 07/08/1984) ou a resposta da FURB,
   que continuam sendo as duas saídas que a própria regra prevê para ser removida.

### A tabela chegou (02/10/2026) — e diz "muda com a época"

A sétima rodada de pesquisa salvou o HTML de `/p/enchentes`
(`data/brutos/pesquisa-picos-2026-09-24/rodada7/originais/AlertaBlu_enchentes-registradas.html`, sha256 no
manifesto), e o script passou a lê-lo direto. 102 enchentes, 1852–2024; **a lista não declara régua nem
zero**. O que o cruzamento mostra, e o que não mostra:

* **Até 2001, a lista reproduz a Tabela 4 de Cordero & Medeiros ao centavo** — 58 pares com o rótulo IBGE,
  mediana +0,00 m, 98% exatos (a exceção é 18/08/1977: 9,25 nosso × 9,15 dela).
* **De 2008 em diante, nada a julga.** Os nossos registros desse trecho vieram da própria lista ou da
  imprensa, na mesma régua dela; compará-los com ela dá +0,00 m e não prova nada. O que existe de fora é o
  CEOPS na Tabela 3 do Esboços (UFSC, 2013): **+0,20 m** sobre a lista em 31/08/2011 (8,7 × 8,5) e
  09/09/2011 (12,8 × 12,6), e igual a ela em 2001 (11,02).
* O primeiro veredito do script foi "AlertaBlu em IBGE — subtrair 0,20 m" na série inteira. **Estava
  errado**: casava enchentes diferentes do mesmo mês e estendia ao trecho recente uma medida feita só até
  2001. As duas coisas foram corrigidas com teste; o veredito agora é `so_ate_o_ultimo_rotulado` e a saída
  é 2 — **não converter**.

**Três números para a mesma pergunta, e nenhum é o teste da regra:**

1. **0,20 m** — a regra (CEOPS 13,00 × Defesa Civil 12,80 em set/2011) e o padrão do Esboços em 2011.
2. **≤ 0,15 m em 1983, se** a unidade do XML da ANA é cm e o zero é o da régua daquele ano. O serviço
   `HidroSerieHistorica` (83800002, consistido) dá 1519 como valor **diário** de 09/07/1983 (régua lida pelo
   observador, `TipoMedicaoCotas` 1). Um valor diário não passa da crista; se a régua ficasse 0,20 m abaixo
   dos 15,34 m, a crista nela seria 15,14 m. Agosto de 1984 (1485 no dia 7) cabe em qualquer hipótese. O XML
   não declara unidade e o significado do status não foi confirmado: é **pista**, não teste — o teste pede a
   crista.
3. **0,40 m depois de 2011** — Cordero, Salvador e Refosco ("Cotas-enchente do município de Blumenau", XX
   SBRH, p. 2): a ANA aceitou mudar a referência da régua para a do IBGE levantada por GPS, "que deu 40 cm.
   Assim a referência da régua da ANA ficou 40 cm a menos do que as enchentes anteriores". O mesmo artigo dá
   13,0 m para set/2011.

Somam-se a eles o ND de 26/09/2013 ("A diferença entre a régua do Ceops, que fica na Ponte Adolfo Konder e
da Prefeitura, na Ponte de Ferro chegou a 20 centímetros") e o JSC de 2011, sobre as cotas de enchente ("Os
níveis usados atualmente foram calculados em 1984 e revisados em 1992, quando se percebeu diferença de 10
centímetros entre o previsto e o real"). **Nada foi convertido; a regra fica.**
A pergunta à FURB (C25, enviado em 02/10/2026 12:30 BRT a cordero@furb.br) ganha três itens: a unidade e o zero da série da ANA em 1983; o que "40 cm a menos"
significa em leitura de régua; e desde quando a lista do AlertaBlu deixa de ser a Tabela 4.

Até lá a regra fica de pé, e o campo `referencia` do registro de 2011 continua `null` — que é o
rótulo honesto para "não se sabe", e não um problema a ser preenchido no chute.

### A resposta do Prof. Cordero (02/10/2026) — parcial, e a regra fica

Três e-mails curtos, minutos depois do C25 (texto literal em `docs/oficios-prontos.md`, C25):

* **Set/2011 em três referências, pela própria fonte:** "12,60m na régua 12,80 (IBGE) 13,00(GPS)". Os três
  números que circulavam (Defesa Civil 12,60; Esboços/CEOPS 12,80; artigo do XX SBRH 13,0) são a **mesma cheia**,
  não três leituras em conflito: IBGE = régua + 0,20; GPS = régua + 0,40.
* **"Antes era somar 20 cm para a referência do IBGE"** — confirma, para a régua de antes da troca, o
  deslocamento que a regra bloqueante usa.
* **"A régua nova tem que somar 40 cm aos níveis da régua antiga"** — confirma que houve troca de régua depois
  de 2011, mas a frase admite os dois sentidos (a mesma água lida 0,40 m mais baixa ou mais alta). Isso mexe
  com comparar a leitura de hoje com cheias antigas, então **não se interpreta no chute**: o seguimento enviado
  em 02/10/2026 pergunta com um exemplo (10,00 m na antiga = 9,60 ou 10,40 na nova?) e a data.
* **Ele tem a série** e ofereceu enviá-la; o seguimento aceitou. Ele respondeu que envia "quando chegar em
  casa" — a tabela ainda não chegou.
* **A Tabela 4 está em IBGE.** Ao seguimento ("Os valores da Tabela 4 (1852–2001), como 15,34 m em 1983, estão na
  referência IBGE, ou seja, régua antiga + 0,20 m?"), a resposta foi uma palavra: "IBGE". É a **premissa da regra
  bloqueante confirmada pela fonte**: o rótulo `IBGE (régua + 0,20 m)` dos 72 registros da série longa está certo.

Ficaram sem resposta: o sentido e a data da troca de régua de 40 cm (perguntado de novo no seguimento, com o
exemplo 10,00 m = 9,60 ou 10,40), a unidade do 1519 da ANA e desde quando a lista do AlertaBlu muda de
referência.

**Consequência:** é resposta da FURB, mas não fecha a regra — e mostra que ela não se resolve com um número só,
porque há duas réguas (antes e depois de 2011). Nada foi convertido. O site continua seguro do jeito que está:
em Blumenau, a comparação com o nível atual só usa os registros rotulados `régua`, que são leituras recentes.

### A planilha do Prof. Cordero (02/10/2026, 18:10) — fecha o sentido da troca, abre 1931–1983

Anexo `Picos-Blumenau-1888-2024-IBGE-GPS.xls` (83 cheias, 1852–2024), guardado como veio em
`data/brutos/furb-cordero-2026-10-02/` com transcrição e sha256. Colunas: **IBGE** e **"IBGE-GPS (Régua
Nova)"**. A célula de data guarda só dia e mês (o ano gravado nela é o da digitação); o ano vem da coluna B.
E-mail que a acompanha: "Régua antiga +0,2 = IBGE … IBGE+0,2=GPS. Após enchente de 2011 foi instalada nova
régua (em relação a régua antiga tem 40 cm). A partir desta data não precisa somar nem o 20 cm nem o 40 cm."

**O que fica respondido:**

* **O sentido da troca.** A régua nova lê **0,40 m mais alto** que a antiga, e já está em GPS = IBGE + 0,20 m:
  set/2011 = 12,60 (régua antiga) = 12,80 (IBGE) = 13,00 (GPS = régua nova). Até 2011 a coluna GPS é sempre
  IBGE + 0,20; **de 2013 em diante as duas colunas são iguais**, e a linha de 2013 traz a anotação
  "Mudança da regua nova". A data exata da instalação continua sem dia: entre set/2011 e set/2013.
* **A lista do AlertaBlu muda de régua no meio.** Comparada com o HTML guardado na sétima rodada:
  - 1852–1900, 09/07/1983, 1984, 1990, 1992, 1997 e 2001: **iguais ao centavo** (planilha IBGE = lista = Tabela 4);
  - 2008, 31/08/2011 e 09/09/2011: a lista dá **0,20 m a menos** que a coluna IBGE. Nesse trecho a lista está na
    **régua antiga**, como o Esboços já sugeria;
  - 2014, 2015, 2017 e as seis de out–nov/2023 e 2024: **iguais**. A lista está na **régua nova**, que é a
    mesma das leituras de hoje.
* **Consequência para o que o site compara.** A leitura ao vivo e as cotas de atenção, alerta e inundação
  estão na régua nova, ou seja, **0,20 m acima do IBGE** e **0,40 m acima da régua antiga**. Os 15,34 m de
  1983 da Tabela 4 equivalem a **15,54 m** na régua de hoje. O site não converte nada e, em Blumenau, compara
  o nível atual só com registros rotulados `régua`, todos de 2021 em diante (régua nova). Isso continua
  seguro. Mas o texto de `GraficoPicos.tsx` ("está em referência IBGE, 20 cm acima da régua") vale só para a
  régua antiga: para a régua de hoje, o IBGE fica 20 cm **abaixo**.

**O que a planilha NÃO autoriza, e por quê:**

* **1911–1928, datas trocadas de linha.** Os valores são os da Tabela 4, mas o dia/mês de cada linha é o da
  cheia anterior (ex.: 1911 = 16,90 m com data 29/05, que na Tabela 4 e na lista é 02/10; a data 02/10 está
  na linha de 1900). Erro de digitação da planilha, não dado novo.
* **1931–1983, valores diferentes da Tabela 4 publicada e da lista.** Das 22 linhas com a mesma data, em 16 a
  lista do AlertaBlu (= Tabela 4) fica acima da planilha por **+0,20 a +0,31 m**, metade delas exatamente
  +0,25 m (ex.: 1980, 13,27 × 13,02; 1961, 10,35 × 10,10). As outras seis fogem do padrão (1931 +0,73;
  1973-08 +0,11; 1978 +0,05; 1983-05 +0,06; 1977 −0,10; 1979-05 −0,30), e de 1931 a 1955 a maioria das datas
  nem casa. A planilha foi criada em 1997, antes do artigo do XV SBRH (2003), e a
  coluna "IBGE" pode ter ficado com valores de uma versão anterior nesse trecho. **Fica valendo a Tabela 4
  publicada**, que é revisada e é a que os 72 registros já citam. A diferença iria ao Prof. Cordero. (Cancelado em 03/10/2026, decisão do Jefferson: **sem mais perguntas ao Prof. Cordero**.) O desempate passa a ser pedido a fontes publicadas (prompt v3.8, item 11).
* **Linhas que o cadastro não tem:** 18/07, 27/07, 29/07 e 02/08/1983 (10,95 / 10,38 / 11,08 / 11,20 m IBGE),
  08/10/2023 (9,49 m, régua nova) e 26/05/2010 (8,64 m; a lista dá 26/04 e 8,46, possível troca de dígitos).
  São **candidatos**, não registros: entram só por decisão do Jefferson.
* **Nada foi convertido e a regra bloqueante fica**, até decisão do Jefferson sobre como aplicar a resposta,
  em um único commit.

### A régua de hoje está em GPS: confirmado pela fonte (02/10/2026, 19:33)

Resposta do Prof. Cordero à pergunta direta ("As leituras de hoje … já estão nessa régua nova, ou seja, na referência
GPS?"): **"A régua atual já está na referência gps !"** (texto literal em `docs/oficios-prontos.md`, C25). Ele acrescenta
por que houve troca: na cheia de set/2011 o talude do rio deslizou e levou as réguas. A nova foi instalada no pilar da
ponte, já em GPS, e depois as réguas a montante da ponte, na mesma referência. **Ele não lembra a data**; a planilha
marca 2013. Janela da troca: set/2011 a set/2013, sem nenhum registro de Blumenau dentro dela.

**O que fica estabelecido, com fonte:**

| Referência | Relação | Exemplo set/2011 | Exemplo jul/1983 |
|---|---|---|---|
| Régua antiga (até 2011) | — | 12,60 m | 15,14 m |
| IBGE (Tabela 4, 1852–2001) | régua antiga + 0,20 m | 12,80 m | 15,34 m |
| GPS = régua de hoje | IBGE + 0,20 m = régua antiga + 0,40 m | 13,00 m | 15,54 m |

É a "resposta da FURB" que a REGRA BLOQUEANTE prevê para ser removida. **A remoção e a conversão continuam sendo
decisão do Jefferson**, em um único commit registrado aqui. Até lá nada é convertido. Ficam abertos: a data exata da troca
e a divergência da planilha com a Tabela 4 publicada em 1931–1983 (vale a Tabela 4).

### Decisão: conversão parcial de Blumenau para a régua de hoje (03/10/2026)

**Decisão do Jefferson, 03/10/2026:** sem mais perguntas ao Prof. Cordero; converter **só os 57 registros de
certeza alta**. Feito em um único commit por `scripts/converter_blumenau.py --aplicar`, com o relatório em
`docs/CONVERSAO-BLUMENAU.md`.

* **O que somou:** IBGE + 0,20 m (37 registros); régua antiga + 0,40 m (4: 2008, 2010, 31/08/2011 e 2009-09-29
  conferidos na lista); régua de hoje + 0 (16, só o rótulo). Exemplos: 1880 17,10 → 17,30 m; 1983 15,34 → 15,54 m;
  1984 15,46 → 15,66 m; 2008 11,52 → 11,92 m; set/2011 12,80 → 13,00 m.
* **O que ficou guardado:** `pico_publicado_m`, `referencia_publicada` e `conversao` em cada registro. As
  divergências ficam como publicadas, cada uma com a sua referência. Duas que, convertido o adotado, ficaram
  iguais a ele (1852, 16,50 m; set/2011, 13,00 m do CEOPS) viraram confirmação no texto da conversão.
* **O que NÃO foi convertido (67):** 60 de 1929–1983 em que a Tabela 4 publicada e a planilha do Cordero
  discordam; 4 inferidos sem par na lista do AlertaBlu (1862-11, 1888-01, 2009-10-06, 2011-09-08); 3 pendentes
  (2013 e 23/09/2013, na janela da troca; 12/07/2026, sem régua declarada). Continuam com o rótulo que tinham
  e **fora da comparação com o nível de agora**.
* **O que mudou no site e no bot:** o painel "quanto falta" e o bot passam a comparar Blumenau com os 57 picos
  na régua de hoje e dizem quantos ficaram de fora. O validador refaz a conta de cada registro convertido.
* **O que não mudou:** `_meta.periodos_retorno_blumenau_m` e `_meta.curva_chave_blumenau` (Tabela 5 e curva de
  Cordero & Medeiros, "na régua" da época) não são lidos pelo site e ficam como estão.
* **A regra bloqueante continua**, para os 67 restantes. `data/desastres/correspondencias.json` é uma foto de
  21/09/2026 e não foi regerado.

### As seis cheias da planilha que faltavam no cadastro (03/10/2026, decisão do Jefferson)

* **Quatro de jul–ago/1983** (18/07 10,95 m; 27/07 10,38 m; 29/07 11,08 m; 02/08 11,20 m, valores da coluna IBGE da
  planilha): picos secundários da cheia longa de 1983, que não estão na Tabela 4 publicada nem na lista do AlertaBlu.
  Entraram com `referencia: null` e `referencia_hipotese` "IBGE", porque em 1929–1983 a coluna IBGE da planilha discorda
  da Tabela 4. Ficam fora da comparação com o nível de agora. Confiança `media`: planilha pessoal, não publicada, com
  erros de transcrição conhecidos em outros trechos.
* **08/10/2023, 9,49 m**, na régua de hoje: de 2013 em diante as colunas da planilha são iguais e batem com a lista
  oficial nas outras seis cheias de out–nov/2023. Fica um dia antes da crista de 09/10/2023 (10,19 m); a planilha a conta
  como cheia separada. Confiança `media`.
* **26/05/2010** (8,64 m IBGE = 8,84 m na régua de hoje) **não virou registro novo**: é quase certamente a cheia de
  26/04/2010 já cadastrada (8,46 m na régua antiga = 8,86 m na de hoje) — mesmo dia, 2 cm de diferença, mês e dígitos
  trocados. Ficou como divergência desse registro, para não contar a mesma cheia duas vezes.
* Cadastro de Blumenau: 124 → 129 registros (58 na régua de hoje, 71 fora da comparação).

