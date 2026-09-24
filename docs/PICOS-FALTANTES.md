# Picos históricos que faltam — levantamento de 24/09/2026

O chat do histórico respondia "O site não tem picos de cheia registrados para Itajaí".
A causa é dado, não código: `data/enchentes.json` tem 276 registros em **7 das 19 cidades** do
cadastro. Este documento lista o que falta e traz, no fim, um **prompt pronto para colar em
outra IA** (ChatGPT, Gemini, Perplexity…) e buscar os números.

> Nada que vier de outra IA entra no JSON sem abrir a URL e conferir o trecho citado. IA inventa
> número de cheia com a maior naturalidade — e aqui um número errado vira decisão errada de
> morador.

## 1. O que já temos

| Cidade | Rio | Registros |
|---|---|---|
| Blumenau | Itajaí-Açu | 117 |
| Rio do Sul | Itajaí-Açu | 65 |
| Gaspar | Itajaí-Açu | 48 |
| Brusque | Itajaí-Mirim | 28 |
| Indaial | Itajaí-Açu | 16 |
| Taió | Itajaí-Açu | **1** (12,40 m em 09/10/2023) |
| Timbó | Itajaí-Açu (Rio Benedito) | **1** (9,86 m em 09/09/2011) |

## 2. O que falta, por cidade

As **datas-alvo** saem do Atlas Digital de Desastres (`data/brutos/atlas-desastres-recorte-*.json`):
são os dias em que a cidade registrou desastre com mais gente fora de casa — onde houve estrago,
houve rio alto, e é ali que vale procurar o nível. Para antes de 1991 (fora do Atlas), os
eventos-alvo são os grandes da bacia: **jul/1983, ago/1984, out/2001, nov/2008**.

| Cidade | Rio | Régua a que o número tem de pertencer | Datas-alvo (Atlas) | Pistas já no cadastro |
|---|---|---|---|---|
| **Itajaí** | Açu e Mirim (foz) | **Onze réguas DC**, cada uma com zero próprio — ver §3 | 09/09/2011, 20/02/2008, 23/11/2008, 31/01/2008, 27/03/2013, 17/10/2013; e 1983, 1984 | Boletim de 10/09/2011 13h30 (leitura, **não** pico); manchas de 1983, 1984, 2001, 2008, 2011, 2013, 2014, 2015 já no repo sem nível |
| **Ilhota** | Açu | Ponte Cláudio Jeremias Cadorin (a do PLANCON) | 24/11/2008, 30/08/2011, 22/01/2011, 01/10/2013, 30/09/2001 | cotas 9,20/10,00/10,50 m |
| **Ascurra** | Açu | Ponte do Beber (DCSC-00003) | 08/09/2011, 27/09/2013, 22/11/2008, 22/10/2015 | cotas 8,50/9,76/10,76 m |
| **Apiúna** | Açu | ANA 83500000 (vínculo com régua municipal pendente) | 26/09/2013, 08/09/2011, 26/10/2015, 09/01/1995, 17/12/2020 | — |
| **Lontras** | Açu | Régua do Açu em Lontras (ponto não nomeado) | 01/10/2001, 09/08/2011, 20/12/2020 | "segurança observada" 9,20 m |
| **Ibirama** | Rio Hercílio (Itajaí do Norte) | Régua do Hercílio em Ibirama | 08/09/2011, 18/12/2020, 21/11/2008, 01/10/2001 | — |
| **Ituporanga** | Itajaí do Sul | ANA 83145140 | sem registro no Atlas | — |
| **Trombudo Central** | Rio Trombudo | Régua do Rio Trombudo | sem registro no Atlas | "inundação histórica" 8,71 m (sem data) |
| **Rio dos Cedros** | Rio dos Cedros | Régua da Praça Matriz | sem registro no Atlas | cotas 4,80/5,30/5,70 m |
| **Vidal Ramos** | Mirim | não identificada | 24/03/2001, 08/09/2011, 16/11/2005 | — |
| **Botuverá** | Mirim | não identificada | 09/09/2011, 18/03/2011, 23/11/2008 | — |
| **Guabiruba** | Mirim (Rio Guabiruba) | não identificada | 22/11/2008, 12/03/2011, 09/09/2011 | — |
| Taió (só 1) | Itajaí do Oeste | régua do CENTRO (não a da Barragem Oeste) | 1983, 1984, 2011, 2013, 2015, nov/2023 | Decisão de 09/09/2026: cristas da ANA **não** viram registro |
| Timbó (só 1) | Benedito | Rua Equador | 1983, 1984, 2008, 2013, 2015, 2023 | — |

## 3. Itajaí: por que é o caso difícil

Itajaí tem onze réguas da Defesa Civil com zeros diferentes, e as de estuário sobem e descem com
a maré. "O rio chegou a 3 m em Itajaí" não diz nada sem a régua. As do rio:

| Régua | Rio | Cotas atenção/alerta/emergência |
|---|---|---|
| DC-01 CEPSUL | Açu | 1,16 / 1,36 / 1,56 |
| DC-02 Praça Celso Pereira da Silva (Murta) | Açu | 1,60 / 2,00 / 2,50 |
| DC-11 Santa Regina (Volta de Cima) | Açu | 3,00 / 4,00 / 5,00 |
| DC-03 Captação SEMASA (canal retificado) | Mirim | 1,48 / 1,85 / 2,50 |
| DC-04 Vitalmar | Mirim | 1,50 / 1,85 / 2,25 |
| DC-05 Sítio Sr. Hilário (curso antigo) | Mirim | 1,60 / 2,20 / 3,00 |
| DC-06 Itamirim Clube de Campo | Mirim | 1,50 / 1,85 / 2,55 |
| DC-10 Limoeiro | Mirim | 8,00 / 9,00 / 10,00 |

Armadilhas conhecidas:
- **Boletins de Itajaí citam o nível de Blumenau.** O 12,60 m de 2011 é de Blumenau.
- **Nomes antigos:** em 2011 as estações se chamavam "Teporti/Açu", "Teporti/Murta", "Início Rio",
  "AMP Logística/Canhanduba" — só CEPSUL, SEMASA, Vitalmar e Itamirim batem com os nomes de hoje.
- **Leitura ≠ pico.** Em 10/09/2011 às 13h30 o rio já descia; o pico foi antes (a tabela de
  **09/09/2011 17h30**, reproduzida no blog Alcateia GEMAT, é a candidata).
- A escala antiga do porto/"régua da Marinha" também circula em notícias de 1983/1984.

## 4. Onde procurar

- Defesa Civil de Itajaí (boletins, relatórios pós-evento, Plano de Contingência — versões antigas)
- Defesas Civis municipais de Ilhota, Ascurra, Apiúna, Lontras, Ibirama, Timbó, Taió, Botuverá, Guabiruba, Vidal Ramos
- CEOPS/FURB (acervo), AlertaBlu, Epagri/CIRAM (notas hidrológicas e avisos — parte já em `data/brutos/ciram-*`)
- ANA/HidroWeb: 83500000 (Apiúna), 83145140 (Ituporanga), 83050000 (Taió)
- Acadêmico: UNIVALI (Itajaí), FURB, UFSC, anais ABRH/SBRH, relatórios JICA (2011) e do Plano de Bacia
- Imprensa: NSC Total/g1 SC, Diarinho, O Município (Brusque), Jornal de Santa Catarina, Rádio Clube, Jornal Metas (Gaspar/Ilhota), acervos digitalizados de jornais de 1983/1984
- Atlas Digital de Desastres: os formulários (AVADAN/FIDE) às vezes trazem a cota do rio no texto

## 5. Regras para o que voltar

1. Um registro por (cidade, rio, data). Para Itajaí: um no Açu e um no Mirim, cada um dizendo a régua.
2. `fonte` e `confianca` obrigatórios: `alta` = oficial/acadêmica, `media` = imprensa, `baixa` = compilação informal.
3. Só **pico** entra em `pico_m`. Leitura de um horário não entra.
4. Estação não declarada pela fonte → `confianca: baixa` e nota dizendo.
5. Valores diferentes para o mesmo pico → `divergencias`, nunca dois registros.
6. Nada de conversão entre réguas ou referências gravada no JSON.

## 6. Prompt para colar em outra IA

```text
Preciso de níveis máximos (picos) históricos de cheias de rios em cidades da bacia do
rio Itajaí, Santa Catarina, Brasil. Responda em português.

Cidades e eventos-alvo:
- Itajaí (foz dos rios Itajaí-Açu e Itajaí-Mirim): cheias de jul/1983, ago/1984, out/2001,
  jan–fev/2008, nov/2008, set/2011, set–out/2013, jun/2014, out/2015, out e nov/2023.
  ATENÇÃO: Itajaí tem várias réguas (CEPSUL, Praça da Murta, Santa Regina/Volta de Cima,
  SEMASA, Vitalmar, Itamirim, Limoeiro, e nomes antigos como Teporti). Para cada número,
  diga QUAL régua. Boletins de Itajaí às vezes citam o nível de Blumenau — não confunda.
- Ilhota, Ascurra, Apiúna, Lontras, Ibirama, Ituporanga, Trombudo Central, Rio dos Cedros,
  Timbó e Taió (Itajaí-Açu e afluentes): cheias de 1983, 1984, 2001, 2008, 2011, 2013,
  2015, 2020 e 2023.
- Vidal Ramos, Botuverá e Guabiruba (Itajaí-Mirim): cheias de 2001, 2008, 2011 e 2023.

Para CADA número, devolva uma linha de tabela com:
cidade | data (AAAA-MM-DD) | hora (se houver) | nível em metros | régua/estação/ponte citada
(ou "não declarada") | é o PICO ou leitura de um horário? | título da fonte | veículo/órgão |
URL exata | trecho literal da fonte que traz o número.

Regras:
- Só números que estão escritos numa página que você consegue citar com URL. Não estime,
  não interpole, não converta entre réguas, não use memória sem fonte.
- Se não achar nada para uma cidade, escreva "nada encontrado" — isso também é resposta útil.
- Se fontes diferentes dão valores diferentes para o mesmo evento, liste todas.
- Prefira: Defesa Civil (municipal ou SC), CEOPS/FURB, ANA/HidroWeb, Epagri/CIRAM, artigos
  acadêmicos; depois imprensa regional (NSC, g1 SC, Diarinho, O Município, Jornal de SC).
```

## 7. Pistas da pesquisa de 24/09/2026 — NÃO CONFERIDAS

A busca achou os números abaixo, mas **nenhuma página pôde ser aberta**: a rede do ambiente
recusou todos os domínios de fonte (`connect_rejected`). Cada valor veio só do resumo do
buscador — por isso **nada entrou em `enchentes.json`**. Para cadastrar: abrir a URL, copiar o
trecho literal, confirmar data e régua.

| Cidade | Data | Metros | Régua | Pico? | URL |
|---|---|---|---|---|---|
| Rio dos Cedros | 1992-05 | 9,25 | não declarada (recorde) | pico | https://riodoscedros.sc.gov.br/uploads/sites/444/2021/12/2056430_plano_de_contingencia_versao_107.pdf |
| Rio dos Cedros | 2008-11 | 7,94 | não declarada | pico | https://www.nsctotal.com.br/noticias/nivel-do-rio-dos-cedros-supera-a-terceira-maior-marca-historica |
| Rio dos Cedros | 2011-09 | 7,73 | não declarada | pico | idem |
| Rio dos Cedros | 2014-06-08 | 8,96 | não declarada | pico (2.º maior) | https://ndmais.com.br/noticias/rio-dos-cedros-enfrenta-a-segunda-maior-enchente-ja-registrada-desde-1992/ |
| Trombudo Central | 1983 | 6,22 | não declarada | pico | https://ndmais.com.br/tempo/atingiu-metade-da-cidade-diz-prefeita-de-trombudo-central-sobre-maior-enchente-da-historia/ |
| Trombudo Central | 2023-11-17 | 8,71 | não declarada | provável pico, ~17h | idem (é o 8,71 de `inundacao_historica` em `estacoes.json`) |
| Timbó | 1992 | 10,42 | Rua Equador | pico | https://www.jornaldomediovale.com.br/on-line/cotidiano/cheia_de_2011_foi_a_maior_de_todas_no_rio_benedito.112538 |
| Timbó | 2011 | 10,01 | Rua Equador | pico — **diverge** dos 9,86 do cadastro | idem |
| Timbó | 2014-06 (seg., ~3h) | 9,40 | não declarada | máximo citado | https://www.nsctotal.com.br/noticias/rio-benedito-atinge-94-metros-e-12-pessoas-sao-removidas-para-abrigos-em-timbo |
| Timbó | 2023-10-12 21h | 7,46 | não declarada | pico | https://oauditorio.com/noticias/geral-noticias/10/2023/rio-benedito-comeca-a-baixar-na-regiao-de-timbo/ |
| Taió | 2011 | 11,65 | não declarada | pico | https://www.nsctotal.com.br/noticias/taio-preve-enchente-pior-do-que-em-2011-e-agua-ja-atinge-2o-piso-das-casas-fotos |
| Taió | 2023-10-09 | 12,33 | não declarada | **diverge** dos 12,40 do cadastro | https://www.nsctotal.com.br/noticias/rio-itajai-do-oeste-ultrapassa-recorde-de-elevacao-dos-ultimos-12-anos-apos-chuvas-fortes-em-sc |
| Ascurra | 2026-09-01 (?) ~6h | 10,13 | Ponte do Beber | máximo citado; confirmar data | https://ndmais.com.br/tempo/rio-avanca-ultrapassa-10-metros-bloqueia-rua-em-ascurra/ |
| Botuverá / Vidal Ramos | data ? | 5,85 / 3,87 | não declarada | pico | https://ndmais.com.br/tempo/avenida-e-interditada-apos-rio-atingir-51-metros-acima-do-nivel-e-sair-da-calha-em-cidade-de-sc/ |

**Itajaí: nenhum pico por régua achado** para os eventos históricos. Só leituras de 2023, que
não entram em `pico_m`: 08/10/2023 Açu/Murta 2,52 m e Itamirim ~2,28 m (boletim 05 da DC de
Itajaí, https://defesacivil.itajai.sc.gov.br/noticia/5705/boletim-05-08-10-23); 19/11/2023
Vitalmar 2,05 m e Itamirim 2,72 m (NDmais). Números que circulam como "de Itajaí" e **não são**:
9,49 m (08/10/2023, Diplomata FM — régua de Blumenau), 15,34/15,46 m (Itajaipédia — Blumenau
1983/1984), 11,52 m (Wikipédia, 2008 — Blumenau).

**Achados que mudam o cadastro:**
- **Ilhota não tem régua própria**: a Defesa Civil de Ilhota usa a medição de Gaspar
  (https://ilhota.sc.gov.br/noticia-100533/). Confirmar e, se for, Ilhota não terá pico próprio.
- **Guabiruba** aparece em boletins de Brusque em **cota ortométrica** (~25 m), não em régua de zero local.
- O "10,03 m em 2011" que surge nas buscas de Botuverá é de **Brusque**.
- Ibirama, Apiúna, Lontras e Ituporanga: nada utilizável.

**Melhores alvos para Itajaí** (não abriram daqui): https://defesacivil.itajai.sc.gov.br/historico/ ·
Avisos Hidrológicos de out/2015 · JICA com tabelas por estação
(https://openjicareport.jica.go.jp/pdf/12043683_02.pdf) · dissertação UDESC de Caio Floriano dos
Santos (https://www.faed.udesc.br/arquivos/id_submenu/866/caio_floriano_dos_santos.pdf).

## 8. Cadastrado em 24/09/2026 (segunda rodada, páginas abertas no Chrome)

Pesquisa externa com as páginas abertas e salvas; cada trecho foi conferido de novo no arquivo
original, em `data/brutos/pesquisa-picos-2026-09-24/` (fontes, 17 séries da ANA e os relatórios).
**14 registros novos, todos `confianca: baixa`**, porque nenhuma fonte declara a régua:

| Cidade | Data | Pico | Fonte |
|---|---|---|---|
| Trombudo Central | 17/11/2023 17h | 8,71 m | Prefeitura |
| Botuverá | 17/11/2023 (tarde) | 8,61 m | O Município, citando o prefeito |
| Timbó | 12/10/2023 21h | 7,46 m | O Auditório |
| Timbó | 2014 | 9,58 m | Câmara de Timbó (fala da Defesa Civil) |
| Rio dos Cedros | 12/10/2023 15h | 5,77 m | O Auditório |
| Taió | 1983, set/2011, jun/2013, jun/2014, out/2015, jun/2017, mai/2022, 04/11/2023, nov/2023 | 11,85 · 11,65 · 9,38 · 8,91 · 10,75 · 8,18 · 9,70 · 10,36 · 10,37 m | Estudo Socioambiental de Taió, p. 343 (+ Misturebas para 04/11) |

Decisões tomadas no cadastro:
- **Taió 1983:** a tabela diz setembro, a ANA tem a máxima do ano em 12/07/1983. O registro fica
  só com o ano, e o mês da fonte vai em `data_na_fonte`.
- **Taió nov/2023:** duas linhas sem dia (10,36 e 10,37). A de 10,36 é a de 04/11 (imprensa); a
  outra fica como `2023-11` com `pendencia`. Não usei a crista da ANA de 17/11 para datar, porque é outra régua.
- **Taió out/2023:** a tabela confirma os 12,40 m já cadastrados. Não criei um registro duplicado.
- **Timbó 2011:** a Câmara cita 9,86 m, o mesmo valor do cadastro. Isso confirma o registro.

**Itajaí continua com zero picos.** A segunda rodada achou a tabela de 09/09/2011 17h30 (a
candidata da pendência do README): CEPSUL 0,93 · Teporti 3,03 · SEMASA 3,65 · Vitalmar 2,68 ·
Início Rio 2,62 · Itamirim 3,21 · Teporti/Murta 2,16 · AMP Logística 2,78 (unidade inferida).
É **leitura**, e o próprio boletim prevê piora na maré das 00h30. A Folha de 11/09/2011 põe o
máximo no dia 10, sem cota. Nada disso é pico, e nada entrou.

Outros achados: 83145140 é **Barragem Sul / Ituporanga Jusante**, não a régua do centro. O
PLANCON de Ilhota traz uma tabela com os números de Blumenau (15,34/15,46/12,60). As leituras
de Apiúna em 04–05/05/2022 não dizem a unidade. Nenhum desses achados virou registro.

## 9. Estado

- [x] Chat: cidade sem pico passa a dizer o motivo e mostrar o impacto do Atlas, sem metro (PR #409).
- [x] Pesquisa web, primeira rodada: pistas na §7, nenhuma conferida (rede bloqueada).
- [x] Segunda rodada conferida nos originais: 14 registros (§8).
- [ ] Itajaí: pico por régua — boletim final da Defesa Civil de 2011, ou relatório com máximo por estação.
- [ ] Ilhota, Ascurra, Apiúna, Lontras, Ibirama, Ituporanga, Vidal Ramos, Guabiruba: sem pico ainda.
- [ ] Séries da ANA baixadas (Apiúna 83500000, Ibirama 83440000, Ituporanga 83250000, Timbó 83677000/83680000, Ilhota 83860000/83870000): extrair picos por script, como foi feito no Itajaí-Mirim — são réguas da ANA, com zero próprio.
