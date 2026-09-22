# Análise do evento de novembro de 2008 — trazida do repositório `prevencao-itajai` (22/09/2026)

**De onde veio.** Este documento é o `relatorios/analise_2008_itajai.md` do repositório
`haohmarusc-glitch/prevencao-itajai`, commit `4572e6e` de 30/08/2026, trazido para cá por
decisão do Jefferson em 22/09/2026, antes de aquele repositório ser arquivado. O texto
original está reproduzido **sem alteração** na seção "Texto original", abaixo. Tudo o que
vem antes dela é leitura de 22/09/2026 contra o que este repositório já conferiu.

**O que ele é, e o que não é.** É uma base bruta sobre o desastre de novembro de 2008: o
diagnóstico de que a maioria das mortes foi por deslizamento e não por afogamento, e de que o
alerta previa o rio e não o morro. O próprio texto diz que "valores com confiança `media` ou
`baixa` devem ser conferidos nas fontes oficiais antes de irem ao ar". **Nada daqui entra em
`enchentes.json`, `estacoes.json` ou `transito.json`**: os picos, as cotas e os trânsitos de
2008 que valem são os do cadastro, com fonte e referência. Os números de vítimas entram como
diagnóstico de falha, nunca como vitrine, como o texto original pede.

## Leitura contra o repositório principal (22/09/2026)

Conferido contra `data/enchentes.json`, `data/desastres/eventos.json` (Atlas de Desastres,
S2ID, base v1.1) e `docs/AUDITORIA-JICA-2011.md`.

### Picos que o texto cita

| o texto diz | o cadastro tem | leitura |
|---|---|---|
| Blumenau, pico 11,52 m | `blumenau 2008-11-24`, **11,52 m**, fonte Defesa Civil de Blumenau, referência não declarada | bate |
| Indaial, pico ~6,0 m | `indaial 2008-11-23`, **5,04 m** (régua), PDF da Defesa Civil de Indaial, marcado "VALOR EM DÚVIDA, preservado como a fonte publica" | **diverge em ~1 m**; o "~6,0" do texto não tem fonte nomeada e não substitui o cadastro; entra como mais um indício de que o 5,04 merece conferência |
| Timbó, pico ~8,0 m | Timbó só tem `2011-09-09`, 9,86 m; **não há registro de 2008** | sem fonte nomeada, não entra; fica anotado como pico a procurar na fonte de Timbó |
| "1983 e 1984, cheias maiores (15+ m em Blumenau)" | 15,34 e 15,46 m são **IBGE (régua + 0,20 m)**, série CEOPS; na régua são ~15,14 e ~15,26 | verdadeiro, com a referência dita |
| Brusque, vazão ~1.200 m³/s | `brusque 2008-11`, 8,5 m (UNIVALI); vazão não é dado do cadastro | sem par para conferir |

### Chuva

O texto atribui ao JICA "236 mm na sub-bacia do Itajaí-Açu e 160 mm na do Itajaí-Mirim" em
quatro dias. A auditoria do estudo JICA feita aqui (`docs/AUDITORIA-JICA-2011.md`) leu do
mesmo estudo **média de bacia de 121–144 mm em 4 dias e 575–576 mm em Blumenau**: chuva
localizada em Blumenau, média de bacia pequena. Os dois números não são a mesma grandeza (o
texto pode estar citando outra sub-bacia ou outra janela) e **nenhum foi reconciliado**. Fica
como pendência de leitura do JICA, não como erro de ninguém.

**Medida, em 22/09/2026** (`docs/INMET-CHUVA-2026-09-22.md`): Indaial (INMET A817) 246,6 mm em
21–24/11, 145,2 mm no dia 23, 567,4 mm no mês; Ituporanga 46,4 mm nos quatro dias. Os 236 mm
cabem num ponto do médio vale; os 121–144, numa média de bacia com cabeceira seca.
No Mirim, com os pluviômetros da ANA (`docs/HIDROWEB-MIRIM-2026-09-22.md`): Botuverá-Montante
334 mm e Brusque 287 mm em 21–24/11, Vidal Ramos 54 — os 160 mm do JICA cabem numa média com a
cabeceira seca.

### Vítimas e afetados: o texto (imprensa e JICA) contra o Atlas de Desastres (S2ID)

O Atlas é o registro oficial dos decretos, com o cuidado que ele mesmo pede: é o que o
município declarou no S2ID, na data do decreto, e a base é subnotificada nos anos antigos.

| município | mortes no texto | mortes no Atlas (nov/2008) | desabrigados / desalojados no Atlas |
|---|---|---|---|
| Blumenau | 24 (21 por deslizamento) | **24** | 5 209 / 25 000 (o texto diz "25.000 evacuados") |
| Gaspar | 19 | **16** | 4 305 / 7 153 |
| Ilhota | 23 | **26** | 1 300 / 3 500 |
| Itajaí | 2 | **5** | 18 208 / 1 929 (o texto diz 28.400 imóveis danificados) |
| Timbó | não citado | **2** | 127 / 700 |
| Rodeio | 4 | **0** | 0 / 0 |
| Ascurra | 1 | **1** | 0 / 110 |
| Pomerode | não citado | **3** | 200 / 1 020 |
| Brusque | 1 | **1** | 1 200 / 8 000 (o texto diz 300 / 160) |
| Guabiruba | 30 desabrigados | 0 mortes | 100 / 60 |
| Benedito Novo | 2 | sem registro de nov/2008 no recorte | — |
| Luiz Alves | 11 | fora das vinte cidades do recorte | — |

Total nas vinte cidades do recorte, nov/2008, pelo Atlas: **78 mortes, 31 388 desabrigados,
52 366 desalojados**, em 15 decretos. As diferenças (Gaspar 19 × 16, Ilhota 23 × 26, Itajaí
2 × 5, Rodeio 4 × 0, Brusque 300/160 × 1 200/8 000) são de fonte e de data: a imprensa contou
na hora, o S2ID contou no decreto. Nenhuma foi "corrigida" aqui. Quem for usar um número de
vítimas escolhe a fonte e a cita.

### O que o texto pede e o repositório já faz, ou já sabe que não faz

- "Cadastrar horário do pico em cada cidade para calibrar descida" — o campo `hora` existe
  em `enchentes.json` e continua raro; é a pendência de calibração do trânsito, que segue.
- "Integração maré–rio na foz" — é a tela `/itajai`, prevista desde o CLAUDE.md e sem fonte
  de maré integrada.
- "Alerta de encosta", "mapa de risco por rua", "rotas de fuga", "zoneamento" — **não são
  escopo deste repositório**, que mostra nível de rio e cotas. Ficam aqui como o que o
  desastre de 2008 ensinou e o site não cobre, para que ninguém leia a cor do rio como
  segurança de encosta.

---

## Texto original (`prevencao-itajai`, commit `4572e6e`, 30/08/2026)

# Análise do evento de novembro de 2008 — bacia do Rio Itajaí

> Documento de base para o site de **prevenção**. Os números de vítimas entram apenas como diagnóstico de falha do sistema de alerta, ordenamento e infraestrutura — nunca como catálogo. O que importa aqui é o que falhou e o que impede a repetição.

**Fontes principais:** Defesa Civil SC, JICA (estudo da bacia do Itajaí, 2011), ABRH/CEOPS-FURB, UNIVALI/CTTMAR, imprensa contemporânea (G1, UOL). Valores com confiança `media` ou `baixa` devem ser conferidos nas fontes oficiais antes de irem ao ar.

---

## 1. O que aconteceu (resumo factual)

Entre 21 e 24 de novembro de 2008, chuvas intensas concentraram-se no **Médio e Baixo Vale**, sobre solo já saturado por chuvas acima da média em outubro. A precipitação de quatro dias atingiu cerca de **236 mm** na sub-bacia do Itajaí-Açu e **160 mm** na do Itajaí-Mirim (JICA). Em Blumenau, o mês fechou com mais de 1.000 mm — recorde da série.

O pico do Itajaí-Açu em Blumenau foi de **11,52 m**, com vazão estimada em torno de **4.200 m³/s**. Em Brusque (Itajaí-Mirim), a vazão chegou a cerca de **1.200 m³/s**. O Alto Vale (Rio do Sul) ficou relativamente baixo — a enchente nasceu da chuva local, sem aviso prévio das nascentes.

O evento atingiu cerca de 60 municípios e mais de 1,5 milhão de pessoas. Catorze municípios decretaram calamidade pública; onze deles ficavam no Vale do Itajaí.

---

## 2. Por que matou — diagnóstico de falha

A enchente em si **não explica** o número de mortes. Em 1983 e 1984, cheias maiores (15+ m em Blumenau) mataram menos, porque a maioria das vítimas morria por afogamento em áreas baixas — e a cidade já sabia lidar com isso.

Em 2008, **cerca de 97% dos óbitos** resultaram de soterramento por deslizamento de encosta, não de afogamento. Em Blumenau, dos 24 mortos, 21 foram por deslizamento; a cidade registrou quase 3.000 pontos de desmoronamento. Em Itajaí, cerca de 3.000 pontos de deslizamento e 28.400 imóveis danificados.

**Causa raiz:** a ocupação desordenada dos morros. Após as enchentes dos anos 1980, a população migrou das áreas baixas (alagadiças) para as encostas, consideradas "seguras" contra a água — mas vulneráveis a escorregamento quando o solo satura. O sistema de alerta (CEOPS) previa o rio, **não o risco de encosta**. Não havia mapa de risco de deslizamento operacional, nem evacuação preventiva de áreas de encosta.

Isso é o que o site de prevenção precisa resolver: **alerta de encosta**, não só de régua.

---

## 3. O que falhou no sistema (lições → pendências acionáveis)

| Falha | O que aconteceu | Pendência para o site / bacia |
|---|---|---|
| Alerta só de rio | CEOPS previa cota; não cobria risco de encosta | Integrar alerta de precipitação + saturação de solo por sub-bacia |
| Ordenamento do solo | Ocupação em área de risco pós-1984 | Mapas de risco (UNIVALI) visíveis por rua; zoneamento atualizado |
| Evacuação tardia | Desabrigados só depois do deslizamento | Rotas de fuga e pontos de apoio por bairro, acessíveis offline |
| Comunicação | "Sem aviso prévio" na região de Blumenau | Canais redundantes (rádio, SMS, sirene) testados em chuva |
| Infraestrutura | Porto de Itajaí inoperante; 150 mil sem energia | Plano de continuidade para água, energia e acesso |
| Dados de trânsito | Poucos horários de pico registrados | Cadastrar horário do pico em cada cidade para calibrar descida |

---

## 4. Dados por município (extraídos para filtragem)

Valores de pico e vazão conforme JICA / Defesa Civil. Conferir antes de publicar.

**Itajaí-Açu (concentração da chuva):**
- Blumenau: pico 11,52 m · vazão ~4.200 m³/s · 24 mortes (21 por deslizamento) · ~3.000 deslizamentos · 25.000 evacuados
- Timbó: pico ~8,0 m · vazão ~710 m³/s
- Indaial: pico ~6,0 m · vazão ~3.100 m³/s
- Gaspar: 19 mortes · 100% da população afetada
- Ilhota: 23 mortes · 100% afetada · maior razão de óbitos da região
- Itajaí: 2 mortes · 80% do território alagado · 28.400 imóveis danificados · porto inoperante
- Benedito Novo: 2 mortes
- Luiz Alves: 11 mortes
- Rodeio: 4 mortes
- Ascurra: 1 morte

**Itajaí-Mirim:**
- Brusque: vazão ~1.200 m³/s · 1 morte · 100 residências interditadas por deslizamento · 300 desabrigados · 160 desalojados · 200–400 mm em 72 h
- Guabiruba: 30 desabrigados · 1 residência desmoronou
- Botuverá, Vidal Ramos: afetados, sem mortes registradas nas fontes consultadas

**Fora da bacia mas no estado:** Jaraguá do Sul (13), Rancho Queimado (2), São Pedro de Alcântara (1), Florianópolis (1).

---

## 5. O que a bacia ainda não tem resolvido (para o site destacar)

1. **Alerta de encosta operacional** em todas as sub-bacias — hoje o foco continua no rio.
2. **Mapa de risco por rua**, com atualização pós-obra, visível no celular sem rede.
3. **Rotas de fuga** testadas e sinalizadas, separadas das rotas de trânsito normal.
4. **Horários de pico** em cada cidade para calibrar o tempo de trânsito real (hoje só 2 dos 20 registros têm hora).
5. **Integração maré–rio** na foz (Itajaí): a maré de sizígia segura a vazante e eleva o nível além do que a chuva explica.
6. **Zoneamento** que impeça nova ocupação em área de risco — a lição de 1984→2008 não pode se repetir.

---

## 6. Bibliografia (para citação no site)

- JICA / Nippon Koei — *The Study on Integrated Water Management of the Itajaí River Basin* (2011). Relatórios abertos em openjicareport.jica.go.jp.
- ABRH — trabalhos do Simpósio Brasileiro de Recursos Hídricos sobre a enchente de 2008 (série 1944–2008, ANA + CEOPS/FURB).
- Frank, B.; Sevegnani, L. (org.) — *Desastre de 2008 no vale do Itajaí: água, gente e política*. Agência de Água do Vale do Itajaí, 2009.
- Defesa Civil SC — boletins e Relatórios de Avaliação de Danos (Avadans) 2008/2009.
- UNIVALI/CTTMAR — caracterização da bacia do Itajaí-Mirim (~1.700 km², 9 municípios).
- G1 / UOL — cobertura contemporânea (cotas, desabrigados, depoimentos).

---

*Este documento é a base bruta. O site de prevenção seleciona apenas o que orienta ação — rotas, contatos, cotas, lições — e omite o que for sensível (endereços exatos de famílias atingidas, dados de vítimas individualizados).*
