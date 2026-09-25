# Picos históricos que faltam — levantamento de 24/09/2026

O chat do histórico respondia "O site não tem picos de cheia registrados para Itajaí".
A causa é dado, não código: `data/enchentes.json` tem 276 registros em **7 das 19 cidades** do
cadastro. Este documento lista o que falta e traz, no fim, um **prompt pronto para colar em
outra IA** (ChatGPT, Gemini, Perplexity…) e buscar os números.

> Nada que vier de outra IA entra no JSON sem abrir a URL e conferir o trecho citado. IA inventa
> número de cheia com a maior naturalidade — e aqui um número errado vira decisão errada de
> morador.

## 1. O que já temos

Atualizado em 25/09/2026, depois da terceira rodada (§10) e da remoção de Botuverá: **327 registros em 15 cidades**.

| Cidade | Rio | Registros | Régua |
|---|---|---|---|
| Blumenau | Itajaí-Açu | 117 | municipal / IBGE |
| Rio do Sul | Itajaí-Açu | 65 | municipal |
| Gaspar | Itajaí-Açu | 48 | municipal |
| Brusque | Itajaí-Mirim | 28 | municipal (5 da ANA) |
| Indaial | Itajaí-Açu | 16 | municipal |
| Ituporanga · Ibirama · Apiúna · Ilhota | Açu e afluentes | 5 cada | **só ANA** (zero próprio) |
| Rio dos Cedros | Rio dos Cedros | 14 | não declarada (PLANCON) |
| Taió | Itajaí do Oeste | +1 (11 no total) | municipal / DCSC |
| Timbó | Benedito | 4 | não declarada / DCSC |
| Vidal Ramos | Itajaí-Mirim | 2 | estação DCSC |
| Trombudo Central · Lontras | — | 1 cada | não declarada / DCSC |
| **Itajaí · Ascurra · Guabiruba · Botuverá** | — | **0** | — |

A seção 2 abaixo é o levantamento original de 24/09 e continua valendo como referência de régua e
de datas-alvo. **O que ainda falta está no prompt da seção 6.**

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

Versão 3.1, de 25/09/2026, escrita depois da terceira rodada (§10) e da remoção de Botuverá. O que funcionou foi receber **os
arquivos originais** (PDF ou página salva): sem eles nada entra. Os boletins da SDE/SC com a tabela
"Níveis máximos atingidos" foram a fonte mais produtiva até agora.

```text
Preciso de níveis máximos (picos) históricos de cheias de rios em cidades da bacia do rio
Itajaí, Santa Catarina, Brasil. Responda em português.

MUITO IMPORTANTE: junto com a resposta, me entregue os ARQUIVOS ORIGINAIS de cada fonte, num zip:
o PDF baixado, ou a página salva como HTML. Não resuma nem transcreva no lugar do original. Número
sem o arquivo original não entra no meu cadastro. Se não conseguir baixar, diga isso na linha.

PRIORIDADE 1 — cidades sem NENHUM pico no meu cadastro:

1. Itajaí (foz do Itajaí-Açu e do Itajaí-Mirim). Cheias: jul/1983, ago/1984, out/2001, nov/2008,
   set/2011, set/2013, out/2015, out/2023 e nov/2023. Itajaí tem várias réguas com zeros diferentes:
   CEPSUL, Praça da Murta (Celso Pereira da Silva), Santa Regina/Volta de Cima, Captação SEMASA/São
   Roque, Vitalmar, Itamirim Clube de Campo, Limoeiro, e nomes antigos como Teporti, Início Rio e AMP
   Logística. Quero o MÁXIMO de cada evento POR RÉGUA: relatório pós-evento da Defesa Civil de Itajaí,
   AVADAN/FIDE, plano de contingência antigo ou trabalho acadêmico (UNIVALI, UDESC) com tabela por
   estação. Não quero leitura de um horário qualquer (a de 09/09/2011 17h30 já tenho), nem limite do
   tipo "mais de 3 m acima do normal".
2. Ascurra: régua do Itajaí-Açu na Ponte do Beber. Cheias: nov/2008, set/2011, set/2013, out/2015,
   out/2023, nov/2023, mai/2024. O Ribeirão Braço São Paulo é outro rio e não serve.
3. Guabiruba: rio Guabiruba. Cheias: nov/2008, mar/2011, set/2011, out e nov/2023. A estação de
   Guabiruba nos boletins de Brusque está em cota ortométrica (~25 m) e não serve.
4. Botuverá (Itajaí-Mirim). Os 8,61 m de 17/11/2023 que o prefeito citou
   foram descartados, porque são o máximo da estação de BRUSQUE no boletim estadual. Quero o pico
   de Botuverá pela Defesa Civil do município, em nov/2008, set/2011, out/2023 e nov/2023.

PRIORIDADE 2 — boletins estaduais com a tabela "Níveis máximos atingidos nos eventos de inundação":

5. A SDE/SC publica o "Boletim Hidrometeorológico" em aguas.sc.gov.br. Já tenho as edições 010/2023
   (outubro), 011/2023 (novembro) e 006/2024 (maio). Quero TODAS as outras edições de 2020 a 2026
   que tenham essa tabela para o Vale do Itajaí, especialmente as de eventos de mai/2022, jan/2021,
   jun/2017, out/2015 e set/2026. Mande o PDF de cada uma.

PRIORIDADE 3 — cidades com poucos picos:

6. Lontras (Itajaí-Açu; só tenho mai/2024), Vidal Ramos (Itajaí-Mirim; só tenho nov/2023 e mai/2024)
   e Trombudo Central (rio Trombudo; só tenho 17/11/2023). Cheias: 1983, 1984, 2001, 2008, 2011, 2013,
   2015, 2017, mai/2022 e out/2023. Para Trombudo, 1983 aparece como 6,22 m na ND+, mas preciso do original.
7. Ituporanga (rio Itajaí do Sul), Ibirama (rio Hercílio), Apiúna e Ilhota (Itajaí-Açu): tenho só a
   série da ANA. Quero a régua da DEFESA CIVIL de cada cidade, com o nome da ponte ou do local. Em
   Ituporanga, a estação da Defesa Civil de SC não é a da ANA (fica a jusante da Barragem Sul?):
   diga onde fica cada uma. Em Ilhota, a Defesa Civil às vezes usa a medição de Gaspar, e o PLANCON
   de Ilhota traz os números de BLUMENAU (15,34 / 15,46 / 12,60): não mande esses.

PRIORIDADE 4 — lacunas pontuais:

8. Timbó (rio Benedito, régua da Rua Equador): o original do Jornal do Médio Vale de 13/09/2011
   (cita 10,42 m em 1992 e 10,01 m em 2011; tenho 9,86 m para 2011 pela Defesa Civil) e o dia e mês
   do pico de 9,58 m de 2014.
9. Taió (rio Itajaí do Oeste): o MÊS da cheia de 1983 de 11,85 m (a tabela da prefeitura diz
   setembro, a ANA indica julho) e da de 9,38 m de 2013 (a tabela diz junho, a ANA indica setembro).
10. Rio dos Cedros: cheias depois de jan/2021 (tenho a tabela do PLANCON de 1992 a 2021 e 12/10/2023)
    e o dia da crista de 8,96 m de 2014 (08 ou 09/06).

JÁ TENHO, NÃO PRECISA MANDAR: os boletins SDE 010/2023, 011/2023 e 006/2024; o PLANCON de Rio dos
Cedros v1.07; o Estudo Socioambiental de Taió; as séries da ANA do HidroWeb; e as notícias de
Trombudo Central (8,71 m) e O Auditório (Timbó e Rio dos Cedros, out/2023).

FORMATO — uma linha de tabela por número:
cidade | data (AAAA-MM-DD) | hora | nível (m) | régua/estação/ponte (ou "não declarada") |
PICO ou leitura de um horário? | título da fonte | órgão/veículo | URL exata | página do PDF |
trecho literal | nome do arquivo no zip

REGRAS:
- Não estime, não interpole, não converta entre réguas, não use memória sem fonte.
- Não confunda cidades: boletins de Itajaí, Ilhota e Gaspar citam o nível de BLUMENAU (15,34 m em
  1983, 15,46 m em 1984, 11,52 m em 2008, 12,60 m em 2011, 9,49 m em 2023), e o "10,03 m em 2011"
  de Botuverá é de BRUSQUE.
- Se não achar nada para uma cidade, escreva "nada encontrado".
- Se fontes diferentes dão valores diferentes para o mesmo evento, liste todas.
- Prefira Defesa Civil (municipal ou de SC), SDE/SC, prefeituras, CEOPS/FURB, Epagri/CIRAM e artigos
  acadêmicos; depois imprensa regional (NSC Total, g1 SC, ND+, Diarinho, O Município, Jornal do
  Médio Vale, Misturebas).
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

## 10. Terceira rodada (25/09/2026), conferida nos originais

A pesquisa externa trouxe os PDFs, e os quatro estão em `data/brutos/pesquisa-picos-2026-09-24/rodada3/`
com SHA-256. Cada número foi lido de novo no PDF. A tabela de outubro/2023 é imagem e foi lida
renderizando a página.

**Entraram 18 registros, todos `confianca: baixa`:**

| Cidade | Data | Pico | Fonte |
|---|---|---|---|
| Rio dos Cedros | 13 cheias, 28/05/1992 a 21/01/2021 | 9,25 (1992) · 8,96 (2014) · 7,94 (2008) · 7,73 (2011)… | PLANCON municipal v1.07, p. 9 + Anexo I |
| Taió | 19/05/2024 13h | 8,47 m | Boletim SDE 006/2024 |
| Timbó | 03/11/2023 21h | 7,61 m | Boletim SDE 011/2023 |
| Vidal Ramos | 17/11/2023 08h · 18/05/2024 22h | 4,86 · 3,43 m | Boletins SDE 011/2023 e 006/2024 |
| Lontras | 19/05/2024 09h | 7,09 m | Boletim SDE 006/2024 |

**Ajustes em registros que já existiam:**
- **Taió 10,37 m:** a linha que estava sem dia é de 17/11/2023, às 21h, pelo boletim de novembro. A ANA leu 10,30 m às 17h do mesmo dia. A pendência foi fechada.
- **Taió 09/10/2023:** o boletim dá 12,39 m às 13h e entrou em `divergencias`. O valor adotado continua 12,40 m.
- **Timbó 12/10/2023 e Trombudo Central 17/11/2023:** os dois foram confirmados pelos boletins. Em Trombudo, o boletim dá 18h e a prefeitura 17h.
- **Botuverá 8,61 m:** o boletim de novembro dá exatamente 8,61 m como máximo da estação de **Brusque** em 17/11/2023, e Botuverá não aparece na tabela. O registro ganhou uma `pendencia`, e decidir se ele sai é do Jefferson.

**Rio dos Cedros, 2020 ou 2021:** a tabela diz 20/01/2020, e o anexo diz 20–21/01/2021, com a
crista às 15h de 21/01. A ANA de Timbó tem um grande evento em 21/01/2021. Ficou 2021, e o ano da
tabela está em `data_na_fonte`. Em 2014, a tabela diz 08/06, mas a crista do anexo cai depois da
meia-noite. A data da tabela foi mantida, com pendência.

**Ficou fora:**
- **Ituporanga, pelo boletim:** 6,92 m em out/2023, 5,25 m em nov/2023 e 3,54 m em mai/2024. A estação
  do boletim não é a série da ANA do cadastro: em out/2023 a ANA marca 5,10 m, e em nov/2023, 6,88 m, a
  ordem inversa. Misturar os dois zeros faria a série saltar sem cheia.
- **Sem original aberto:** Trombudo Central 1983 (6,22 m), Timbó 1992 (10,42 m) e 2011 (10,01 m),
  Ituporanga 2017, e Botuverá e Vidal Ramos em set/2026.
- **Leituras que não são pico:** Itajaí, Ascurra e Apiúna.

## 9. Estado

- [x] Chat: cidade sem pico passa a dizer o motivo e mostrar o impacto do Atlas, sem metro (PR #409).
- [x] Pesquisa web, primeira rodada: pistas na §7, nenhuma conferida (rede bloqueada).
- [x] Segunda rodada conferida nos originais: 14 registros (§8).
- [ ] Itajaí: pico por régua — boletim final da Defesa Civil de 2011, ou relatório com máximo por estação.
- [x] Séries da ANA baixadas: picos extraídos por `scripts/picos_ana_vale.py`, e os 5 maiores de Ituporanga, Ibirama, Apiúna e Ilhota entraram marcados como régua da ANA (confiança baixa) — ver `docs/HIDROWEB-VALE-2026-09-24.md`.
- [x] Terceira rodada conferida nos originais: 18 registros (§10).
- [ ] Itajaí, Ascurra e Guabiruba: ainda sem pico.
- [x] Botuverá 8,61 m: **removido em 25/09/2026 por decisão do Jefferson**. Era exatamente o máximo da estação DCSC de Brusque em 17/11/2023 (Boletim SDE 011/2023, p. 18), e Botuverá não aparece na tabela. A cidade volta a zero pico.
