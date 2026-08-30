# Fontes acadêmicas — o que cada universidade tem e como usar

> Levantamento de 30/08/2026. Complementa `docs/cotas-de-ruas.md`. Tudo o que já foi incorporado
> em `data/` está marcado com ✔; o resto são tarefas ou pedidos pendentes.

## FURB (Blumenau) — CEOPS e LabGeo

| Material | O que contém | Onde | Status |
|---|---|---|---|
| Cordero & Medeiros, *Estudo estatístico das vazões máximas do rio Itajaí-Açu em Blumenau* (XV SBRH/ABRH) | **Tabela 4: todos os picos > 8 m em Blumenau de 1852 a 2001 com data** (72 registros, referência IBGE = régua + 0,20 m); curva-chave de Blumenau; níveis por período de retorno (TR 2 a 1000 anos) | https://files.abrhidro.org.br/Eventos/Trabalhos/154/291.pdf | ✔ incorporado em `data/enchentes.json` (eventos + `_meta.curva_chave_blumenau` + `_meta.periodos_retorno_blumenau_m`) |
| CEOPS/FURB, *Cotas-enchente do município de Blumenau* (SBRH 2013) | Metodologia do levantamento pós-2011: 1.851 pontos topográficos, referenciados à régua da ANA no Centro; linha d'água de 3 enchentes | https://files.abrhidro.org.br/Eventos/Trabalhos/66/SBRH2013__PAP013055.pdf | ler; extrair Tabela 2 (níveis das 3 enchentes) |
| CEOPS/FURB, *Validação de MDT em mapeamento de inundação* (Blumenau e Timbó) | Carta-enchente 2011: Blumenau 13,00 m, Timbó 9,86 m; acurácia das manchas | https://files.abrhidro.org.br/Eventos/Trabalhos/60/PAP022777.pdf | ✔ picos já em `enchentes.json` |
| CEOPS/FURB, *Análise hidrometeorológica do evento de 2008* | Pico em Blumenau 24/11/2008 = 11,52 m (TR ~10 anos); chuva de nov/2008 com TR > 3000 anos | https://files.abrhidro.org.br/Eventos/Trabalhos/153/ (PDF do evento) | ✔ pico incorporado |
| CEOPS/FURB, *Levantamento de cotas-enchente de Brusque* | Cotas rua a rua de Brusque com base nas marcas de 2011, até cota 15 m; estudo estatístico de níveis máximos do Itajaí-Mirim em Brusque; linha d'água | ResearchGate (resumo) — pedir PDF ao LabGeo/FURB | pedido enviado 30/08 |
| CEOPS/FURB, *Cotas de enchente de Gaspar* (2016–2017, coord. Ademar Cordero) | Cotas rua a rua de Gaspar referenciadas à régua da ANA (empresa Círculo); mapa de inundação | Site da Defesa Civil de Gaspar ("Pesquise sua cota") | investigar endpoint |
| LabGeo/FURB — GeoServer | Camadas WMS, inclusive carta-enchente de Blumenau 2011 (12,8 m) | https://labgeo.furb.br/ | pedido enviado 30/08 |
| Acervo CEOPS | Série de picos 1852–2022, boletins, tempos de trânsito | http://ceops.furb.br/ (bloqueia robôs) | pedido enviado 30/08 |

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
