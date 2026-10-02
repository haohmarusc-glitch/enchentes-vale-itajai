# Picos históricos que faltam — levantamento de 24/09/2026

O chat do histórico respondia "O site não tem picos de cheia registrados para Itajaí".
A causa é dado, não código: `data/enchentes.json` tem 276 registros em **7 das 19 cidades** do
cadastro. Este documento lista o que falta e traz, no fim, um **prompt pronto para colar em
outra IA** (ChatGPT, Gemini, Perplexity…) e buscar os números.

> Nada que vier de outra IA entra no JSON sem abrir a URL e conferir o trecho citado. IA inventa
> número de cheia com a maior naturalidade — e aqui um número errado vira decisão errada de
> morador.

## 1. O que já temos

Atualizado em 25/09/2026, depois da quinta rodada (§12): **368 registros em 17 cidades**.

| Cidade | Rio | Registros | Régua |
|---|---|---|---|
| Blumenau | Itajaí-Açu | 117 | municipal / IBGE |
| Rio do Sul | Itajaí-Açu | 65 | municipal |
| Gaspar | Itajaí-Açu | 48 | municipal |
| Brusque | Itajaí-Mirim | 28 | municipal (5 da ANA) |
| Indaial | Itajaí-Açu | 16 | municipal |
| Ituporanga · Ibirama · Apiúna · Ilhota | Açu e afluentes | 5 cada | **só ANA** (zero próprio) |
| Rio dos Cedros | Rio dos Cedros | 15 | não declarada (PLANCON) |
| Taió | Itajaí do Oeste | 19 | municipal / DCSC (7 deles da ANA) |
| Timbó | Benedito | 30 | Rua Equador (1992) / não declarada / DCSC (24 deles da ANA, 1935–2022) |
| Vidal Ramos | Itajaí-Mirim | 3 | estação DCSC / não declarada |
| Trombudo Central · Botuverá | — | 2 cada | não declarada / DCSC |
| **Itajaí** | Açu e Mirim | 2 | estações nº 1 e nº 3 da tese UEM (set/2011), **não ligadas a nenhuma DC de hoje** |
| Lontras | Itajaí-Açu | 1 | DCSC |
| **Ascurra · Guabiruba** | — | **0** | — |

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

Versão 3.6, de 02/10/2026. Atualizada com a sétima rodada (§14), as decisões do Jefferson de 02/10/2026 e a
resposta da FURB ao ofício C25 e, no mesmo dia, com a oitava rodada (§15): sai a Tabela 7.5.1 do JICA (lida), sai a referência da Tabela 4 de Blumenau
(a FURB respondeu "IBGE"), Ascurra e Guabiruba passam a pedir só o que a série da Defesa Civil de SC não cobre,
e entram Gaspar/Indaial (eventos pendentes de régua) e a troca de régua de 2011 em Blumenau. O que funcionou
foi receber **os arquivos originais** (PDF ou página salva): sem eles nada entra. Número visto só em resumo
de busca, sem arquivo, não entra.

```text
Preciso de dados históricos de cheias de rios em cidades da bacia do rio Itajaí, Santa Catarina,
Brasil: níveis máximos (picos), a hora das cristas, as cotas de alerta e alguns documentos técnicos.
Responda em português.

MUITO IMPORTANTE: junto com a resposta, me entregue os ARQUIVOS ORIGINAIS de cada fonte, num zip:
o PDF baixado, ou a página salva como HTML. Não resuma nem transcreva no lugar do original. Número
sem o arquivo original não entra no meu cadastro — inclusive número que você só viu no resumo de um
buscador. Se não conseguir baixar, diga isso na linha.

PRIORIDADE 1 — cidades sem pico ANTIGO (a série da Defesa Civil de SC eu já tenho):

1. Ascurra: régua do Itajaí-Açu na Ponte do Beber (estação DCSC-00003). Já tenho a série dessa estação
   de abr/2023 em diante (inclusive 01/09/2026, 10,13 m). Quero as cheias de ANTES: nov/2008, set/2011,
   set/2013, out/2015, numa régua municipal com nome ou local. Quero também um documento que ligue a
   DCSC-00003 a um local: uma matéria do ND (12/12/2023) fala de "uma nova Estação Hidrológica da Defesa
   Civil ... sob a ponte conhecida como Irineu Bornhausen" (BR-470, km 88), e a série da DCSC-00003
   começa em abr/2023 — são a mesma estação? A Ponte do Beber é a Irineu Bornhausen? O Ribeirão Braço
   São Paulo (Travessa Zonta) é outro rio e não serve.
2. Guabiruba: rio Guabiruba, estação DCSC-00029. Já tenho a série dela de nov/2022 a mar/2026. Quero as
   cheias de ANTES: nov/2008, mar/2011, set/2011, set/2013, out/2015, numa régua com zero declarado.
   Desde abr/2026 a estação mede em altitude (~24–25 m): esse número não serve, nem lâmina d'água na
   rua. A notícia guabiruba.sc.gov.br/noticia-46906/ já tenho e não traz nível. O boletim SDE 006/2024
   não lista Ascurra nem Guabiruba.

PRIORIDADE 1B — Itajaí (foz do Itajaí-Açu e do Itajaí-Mirim), a cidade mais difícil:

3. Só tenho set/2011, das estações telemétricas nº 1 (Açu, 3,20 m) e nº 3 (Mirim, curso antigo,
   4,29 m) da tese de Valdeir Demetrio da Silva (UEM, 2017). Quero:
   (a) um documento que diga QUAL régua de hoje (DC-01 a DC-11) é cada estação telemétrica de 2011
       — sem isso os números não se comparam com nada;
   (b) a série telemétrica de set/2011 que a tese usou ("Fonte: Defesa Civil, 2015"), ou o máximo
       da estação nº 2 (Mirim, canal retificado): a tese dá 3,21 m na tabela e o gráfico chega a
       ~4,5 m;
   (c) o máximo POR RÉGUA das outras cheias: jul/1983, ago/1984, out/2001, nov/2008, set/2013,
       out/2015, out/2023 e nov/2023.
   Itajaí tem várias réguas com zeros diferentes: CEPSUL, Praça da Murta (Celso Pereira da Silva),
   Santa Regina/Volta de Cima, Captação SEMASA/São Roque, Vitalmar, Itamirim Clube de Campo,
   Limoeiro, e nomes antigos como Teporti, Início Rio e AMP Logística. Fontes boas: relatório
   pós-evento da Defesa Civil de Itajaí, AVADAN/FIDE, plano de contingência antigo, trabalho
   acadêmico (UNIVALI, UDESC) com tabela por estação. A monografia de Anderson Ficagna Passos
   (biblioteca.univali.br/pergamumweb/vinculos/pdf/Anderson%20Ficagna%20Passos.pdf) deu 404 e ainda
   não foi procurada em outro lugar: ache outra cópia. Não quero leitura de um horário qualquer (as de
   09/09/2011 17h30 e 10/09/2011 13h30 já tenho), nem limite do tipo "mais de 3 m acima do normal".

PRIORIDADE 2 — boletins estaduais com a tabela "Níveis máximos atingidos nos eventos de inundação":

4. A SDE/SC publica o "Boletim Hidrometeorológico" em aguas.sc.gov.br. Já tenho as edições 010/2023,
   011/2023, 001/2024, 006/2024 e 087 (007/2026, sem cheia), e a auditoria do índice até 07/2026. Quero:
   a edição de set/2026 quando for publicada (até 01/10/2026 não existia); e relatório equivalente de
   ANTES de 2020 (out/2015, jun/2017) de outro órgão (Defesa Civil de SC, Epagri/CIRAM), porque o
   índice da SDE não cobre esse período.

PRIORIDADE 3 — cidades com poucos picos:

5. Lontras (Itajaí-Açu; só tenho 29/11/2023 e mai/2024), Vidal Ramos (Itajaí-Mirim; só tenho
   set/2013, nov/2023, mai/2024 e set/2026), Trombudo Central (rio Trombudo; só tenho 1983, set/2011,
   set/2013, out/2022 e 17/11/2023) e Botuverá (Itajaí-Mirim; só tenho dez/2023, 22/07/2026 e
   set/2026 — os 8,61 m de 17/11/2023 que o prefeito citou foram descartados, porque são o máximo da
   estação de BRUSQUE no boletim estadual). Cheias: 1983, 1984, 2001, 2008, 2011, 2013, 2015, 2017,
   mai/2022, out/2023 e nov/2023. Em Vidal Ramos, a estação "Salseiro" (ANA 83892990, estação 31 da
   Defesa Civil de Brusque) é OUTRA régua, a 6,8 km: não mande números dela como se fossem de Vidal
   Ramos.
6. Ituporanga (rio Itajaí do Sul), Ibirama (rio Hercílio), Apiúna e Ilhota (Itajaí-Açu): tenho só a
   série da ANA. Quero a régua da DEFESA CIVIL de cada cidade, com o nome da ponte ou do local. Em
   Ituporanga, a régua municipal fica na Ponte Vitório Sens (centro), e a estação da Defesa Civil
   de SC não é a da ANA: quero a SÉRIE ou os máximos históricos da régua da Ponte Vitório Sens (o
   2,95 m de 05/06/2017 do Jornal de Pomerode e o 3,58 m de 22/09/2013 15h já tenho). Em Ilhota, a
   Defesa Civil às vezes usa a medição de Gaspar, e o PLANCON de Ilhota traz os números de BLUMENAU
   (15,34 / 15,46 / 12,60): não mande esses.

PRIORIDADE 4 — lacunas pontuais:

7. Timbó (rio Benedito, régua da Rua Equador): o dia e o mês do pico de 9,58 m de 2014, e uma fonte
   que confirme esse valor (a AMVE dá 9,12 m às 22h; nenhuma fonte que tenho confirma os 9,58 m).
8. Taió (rio Itajaí do Oeste): o MÊS da cheia de 1983 de 11,85 m (a tabela da prefeitura diz
   setembro, a ANA indica julho). E o PICO de Taió em SETEMBRO de 2013 na régua do Centro — já tenho as
   leituras de 20/09 17h (5,46 m) e 22/09 15h (8,78 m), que não são o pico; a notícia
   taio.sc.gov.br/noticia-75219/ não traz número.
9. Rio dos Cedros: cheias depois de nov/2022 (tenho a tabela do PLANCON 10.7 até 27/11/2022 e
   12/10/2023) e uma fonte que ESCREVA o dia da crista de 8,96 m de 2014 (o registro de 15 em 15 min do
   PLANCON começa em 08/06 18:30 e chega aos 8,96 m depois de duas meias-noites, isto é, na madrugada de
   10/06, mas a página não repete a data). Dois valores apareceram só em resumo
   de busca e PRECISAM da página salva: Misturebas, 4,80 m em 04/10/2023, e Testo, 5,32 m em 03/11/2023
   (as duas páginas deram desafio do Cloudflare ou 404 no Wayback).

PRIORIDADE 5 — de que régua é cada série (sem isso, os números não se comparam entre cidades):

10. Rio do Sul: a página "Histórico de Cheias" da Defesa Civil de Rio do Sul (defesacivil.riodosul.sc.gov.br)
    lista picos desde 1911 sem dizer a régua. O artigo de Cordero, Momo e Severo (XIX SBRH, ARMAX) diz que
    os 12,20 m de 1911 estão "referenciada na régua da atual estação fluviométrica localizada naquela
    cidade", e a aba "Cotas de Cheia por Rua" do mesmo portal usa a "régua da Ponte Dom Tito Buss". Quero
    um documento que diga QUAL estação é essa "atual estação fluviométrica" (código ANA ou nome da ponte)
    e se o Histórico de Cheias usa a mesma régua, ou se a régua mudou de lugar (quando). A estação "MKS"
    da Defesa Civil de SC (DCSC-00013) tem zero ~0,17 m acima da Ponte Dom Tito Buss, então "Rio do Sul"
    sozinho não basta. Atenção: a estação de hoje na Ponte Dom Tito Buss é NOVA (sistema inaugurado em
    jul/2026, oito estações fluviométricas), e a prefeitura diz que o histórico de níveis "faz parte do
    sistema antigo de monitoramento". Quero saber a régua e o zero do sistema ANTIGO, e se a estação nova
    manteve o mesmo zero.
11. Blumenau, a troca de régua de 2011: a FURB (Prof. Ademar Cordero) me confirmou que a Tabela 4 de
    Cordero & Medeiros está na referência IBGE (régua antiga + 0,20 m), que set/2011 foi 12,60 m na
    régua, 12,80 m no IBGE e 13,00 m no GPS, e que depois de 2011 "a régua nova tem que somar 40 cm aos
    níveis da régua antiga". Falta o SENTIDO e a DATA dessa troca. Quero um documento da ANA (ficha ou
    histórico da estação 83800002, alteração de referência de nível/RN), do CEOPS ou da Defesa Civil de
    Blumenau que diga: (a) em que data a régua da Ponte Adolfo Konder mudou de referência; (b) se a
    mesma água passou a ser lida 0,40 m mais BAIXA ou mais ALTA. E a referência da lista "Enchentes
    Registradas" do AlertaBlu a partir de 2008 (régua antiga, régua nova ou IBGE). Não converta nada:
    mande o número como a fonte publica.
12. Gaspar e Indaial — eventos que tenho, mas sem régua (estão FORA da minha série até isso se
    resolver):
    (a) Gaspar: de que régua e de que zero é o "metros acima da normalidade" dos boletins da Defesa
        Civil de Gaspar de out/2023 (pico de 7,09 m às 7h50 de 09/10/2023); é a mesma régua da tabela
        oficial "histórico de enchentes" da Defesa Civil de Gaspar?
    (b) Gaspar: qual estação/régua o CEOPS usava em Gaspar (9,42 m em 09/09/2011, Tabela 3 da revista
        Esboços), e o zero dela em relação à régua municipal.
    (c) Indaial: em que régua a Defesa Civil de Indaial leu os 5,75 m de 20h de 04/10/2023 — na régua
        da COMPDEC ou na estação DCSC-00006 —, e o deslocamento entre as duas, se houver documento.
13. A HORA da crista nas grandes cheias, para calcular quanto tempo a cheia leva de uma cidade à outra.
    JÁ TENHO hora de: Blumenau 24/11/2008 (0h), 09/09/2011 (12,60 m às 11h), 23/09/2013 (2h),
    23/10/2015 (1h), 09/10/2023 (6h), 17/11/2023 (9h45); Rio do Sul 09/09/2011 (22h), 13/10/2023 (3h10)
    e 18/11/2023 (0h40); Brusque 17/11/2023 (~21h); Ascurra 01/09/2026 (05:10); Taió 09/10/2023 (11,86 m às 02h21, Rádio Mirador — a hora do pico
    de 12,40 m não tenho).
    FALTAM, com data E hora da crista na régua de cada cidade: Ituporanga, Lontras, Ibirama, Apiúna,
    Indaial, Ilhota, Itajaí e Timbó (todas as cheias: nov/2008, set/2011, set/2013, out/2015, out/2023,
    nov/2023, mai/2024); Blumenau mai/2024 (8,67 m às 12h eu tenho, mas a fonte não diz que é o pico) e
    12–13/10/2023 (só "meia-noite"); Rio do Sul out/2015 e mai/2024; Brusque nov/2008 e set/2011; Vidal
    Ramos e Botuverá antes de 2026. Serve boletim de hora em hora ou relatório que diga "o pico ocorreu
    às 14h de 23/11"; hora de uma leitura qualquer não serve.

PRIORIDADE 6 — cotas de atenção, alerta e emergência que faltam:

14. As cotas oficiais (atenção / alerta / emergência ou inundação), com o NOME da régua a que
    pertencem, para: Ibirama (régua do rio Hercílio), Apiúna (Itajaí-Açu, régua da Defesa Civil; as faixas
    da estação ANA 83500000 "Apiúna - Régua Nova" no manual da Sala de Situação ANA/Epagri eu já tenho), Botuverá (Itajaí-Mirim; a Defesa Civil de Brusque publica
    TRÊS estações em Botuverá — 18 "Botuverá", 2 "CEOPS – Botuverá" e 32 "Botuverá – Prefeitura" —,
    então diga de qual é a cota), Guabiruba (DCSC-00029), Vidal Ramos (não a do Salseiro; uma frase
    "3,54 m, nível de atenção" apareceu só em resumo de busca — quero a página) e Lontras (tenho só uma
    "segurança observada" de 9,20 m, que não é cota de alerta). Fontes boas: PLANCON municipal, plano de
    contingência da Defesa Civil, decreto, boletim com a tabela de cotas. Cota sem o nome da régua não
    serve, e cota de uma régua não pode ir para outra, mesmo que as duas tenham o nome da cidade.

PRIORIDADE 7 — documentos técnicos:

15. Tábua de marés de 2027 do porto de Itajaí (SC), da Marinha do Brasil (Centro de Hidrografia da
    Marinha, DHN): o PDF da publicação anual, com as páginas do porto de Itajaí, quando sair (nas
    capturas de 21 e 28/09/2026 só havia a de 2026). Já tenho a de 2026.
16. Barragem Oeste (Taió): o painel público da Asthon dá 99,96 hm³ de capacidade, e esse número não
    aparece em nenhum documento que tenho. Já sei que 83 hm³ (JICA) é o volume até a cota 360 m e que o
    alteamento de 2 m aumentou a capacidade; o Plano de Recursos Hídricos da bacia (cap. A2, Tabela A2.4,
    dados do DEOH) dá "Volume do reservatório" de 83,00 (Oeste) e 93,50 (Sul) — e o mesmo texto diz 97 para
    a Sul. Quero o documento do operador (Defesa Civil de SC, SDE/SC)
    com a curva cota × volume DEPOIS do alteamento, que diga a que cota correspondem os 99,96 hm³. Para
    a Barragem Sul já tenho 104,03 hm³ de capacidade total. Não calcule percentuais.

JÁ TENHO, NÃO PRECISA MANDAR: os boletins SDE 010/2023, 011/2023, 001/2024, 006/2024 e 087/2026 (e a
auditoria do índice); os PLANCON de Rio dos Cedros v1.07 e 10.7, o de Ilhota e o de Itajaí v17
(22/12/2025); a tese de Valdeir D. da Silva (UEM, 2017); o manual "Operação de Barragens" (2024); o
relatório de vulnerabilidade costeira da UFSC (2017); o plano de saúde de Rio dos Cedros; o Estudo
Socioambiental de Taió; o trabalho de Orli sobre Taió (SED/SC, 2017); a nota da Autoridade Portuária de
Itajaí sobre set/2013; a tabela de cheias da Defesa Civil de Rio dos Cedros (1911–1984); as séries da ANA
do HidroWeb e o serviço HidroSerieHistorica da estação 83800002 (1983–1984); os Volumes II, III-A
(inclusive a Tabela 7.5.1, p. A-80) e III-B do JICA 2011; a revista Esboços (UFSC, 2013, Tabelas 2 e 3);
os artigos "Cotas-enchente do município de Blumenau" (XX SBRH) e ARMAX de Rio do Sul (XIX SBRH); o TCC da
UFSC sobre o rompimento hipotético da Barragem Oeste; a página do DEINFRA sobre as barragens (Wayback
2013); a lista "Enchentes Registradas" do AlertaBlu (102 enchentes); os boletins da Defesa Civil de
Gaspar de 10 a 13/10/2023; a tábua de marés de 2026; a notícia 75218 de Taió; e as notícias já usadas: G1,
ND+, NSC, Rádio Mirador, GCD, Jornal Universo, MetSul, Diarinho, O Município, SCC10, O Blumenauense, O
Auditório, Mesorregional, Clicrbs (2008), Acaert (2008), Diplomata FM, RWTV, Portal Educadora, Vale do
Itajaí Notícias (Indaial 2023); o Plano de Recursos Hídricos da bacia do Itajaí (cap. A2, Tabelas A2.3 e
A2.4); o Manual de Operação da Sala de Situação ANA/Epagri/Ciram (faixas por estação ANA, em cm); o relatório
do CEOPS/FURB de 2016 sobre Rio dos Cedros; o PLANCON de Rio dos Cedros v10.4 (2017); a notícia do novo
sistema de monitoramento de Rio do Sul (jul/2026); a notícia 46906 de Guabiruba; o boletim SDE 008/2023;
os blogs Adalberto Day, Dalva Day e Monique Becker (Blumenau) e o
SOS Rios do Brasil (Wayback, set/2013); e as da rodada anterior (Trombudo Central, Timbó, Rio dos
Cedros, Lontras, Botuverá, Vidal Ramos, Ituporanga).

FORMATO — para as prioridades 1 a 6, uma linha de tabela por número:
cidade | data (AAAA-MM-DD) | hora | nível (m) | régua/estação/ponte (ou "não declarada") |
PICO, leitura de um horário ou COTA de alerta? | título da fonte | órgão/veículo | URL exata |
página do PDF | trecho literal | nome do arquivo no zip
Para a prioridade 5 (qual régua) e a prioridade 7 (documentos), uma linha por documento:
o que se pediu | título | órgão | URL exata | página | trecho literal que responde | nome do arquivo.

REGRAS:
- Não estime, não interpole, não converta entre réguas nem entre régua, zero do IBGE e GPS, não use
  memória sem fonte.
- Não confunda cidades: boletins de Itajaí, Ilhota e Gaspar citam o nível de BLUMENAU (15,34 m em
  1983, 15,46 m em 1984, 11,52 m em 2008, 12,60 m em 2011, 9,49 m em 2023), e o "10,03 m em 2011"
  de Botuverá é de BRUSQUE.
- Em Blumenau, o mesmo pico aparece em referências diferentes: em set/2011, 12,60 (régua), 12,80
  (IBGE) e 13,00 (GPS); em 2008, 11,52 (Defesa Civil) e 11,72 (CEOPS). Diga sempre de qual fonte veio
  cada número; não troque um pelo outro.
- Hora sempre com o fuso que a fonte usar; se ela não disser, escreva "fuso não declarado".
- Se não achar nada para um item, escreva "nada encontrado".
- Se fontes diferentes dão valores diferentes para o mesmo evento, liste todas.
- Prefira Defesa Civil (municipal ou de SC), SDE/SC, ANA, Marinha, prefeituras, CEOPS/FURB,
  Epagri/CIRAM e artigos acadêmicos; depois imprensa regional (NSC Total, g1 SC, ND+, Diarinho,
  O Município, Jornal do Médio Vale, Misturebas).
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

## 11. Quarta rodada (25/09/2026), conferida nos originais

Os originais chegaram em duas levas de anexos soltos e estão em `data/brutos/pesquisa-picos-2026-09-24/rodada4/`,
junto com o relatório, o JSON de evidências, a auditoria dos 87 boletins da SDE/SC e o manifesto SHA-256.
Todos os arquivos usados batem com o manifesto, e cada número foi lido de novo no original.

**Cadastrado:**

| Cidade | Data | Pico | Fonte |
|---|---|---|---|
| Timbó | 1992 | 10,42 m | Jornal do Médio Vale, régua dos **fundos da Rua Equador** (a de `estacoes.json`). Confiança média |
| Timbó | 21/01/2021 20h | 7,62 m | OCP News, com balanço da Defesa Civil |
| Taió | 02/12/2023 05h | 6,54 m | Boletim SDE 001/2024 (nível "Atenção") |
| Botuverá | 03/12/2023 23h | 3,58 m | Boletim SDE 001/2024: primeiro pico de Botuverá desde a remoção dos 8,61 m |
| Trombudo Central | 1983 | 6,22 m | ND+ (recorde anterior a 2023) |
| Botuverá | 01/09/2026 ~02h | 5,85 m | ND+, dados da Defesa Civil de Brusque |
| Vidal Ramos | 01/09/2026 madrugada | 3,87 m | ND+ |

**Trocas pela regra de que o municipal prevalece:** em Timbó, os registros da ANA de 29/05/1992 (9,10 m) e
de 21/01/2021 (7,59 m às 17h) saíram do cadastro e viraram `divergencias` dos municipais. A dupla de 2021,
com 7,59 m às 17h na ANA e 7,62 m às 20h na régua municipal, é coerente com a mesma régua e a crista
depois da leitura. Em Timbó 2011 também entrou uma divergência: os 10,01 m do Jornal do Médio Vale, com
a observação de que a notícia avisava que a medida seria revista.

**Conferido, mas fora do cadastro:**
- **Ituporanga:** 3,72 m em dez/2023. É a mesma estação estadual que não bate com a série da ANA. A régua
  municipal fica na **Ponte Vitório Sens** (primeira cota de alagamento: 3,25 m, na antiga Lanchonete São
  Jorge, segundo a Rádio Sintonia de 17/06/2026). Isso é cadastro de régua para `estacoes.json` e fica pendente.
- **Boletim de dez/2023:** as linhas com hora "01/12/2023 00:00" são o início da janela do mês, ou seja,
  a cauda da cheia de novembro, e não máximos de dezembro.
- **Duas notícias de Timbó 2014:** não trazem nível.

**Ainda esperando o original:** Rio dos Cedros 27/11/2022 e a tese UEM de Itajaí chegaram na quinta
rodada (§12).

## 12. Quinta rodada (25/09/2026), conferida nos originais

Dois zips (`Picos_20260925_094511_parte_01_de_02` e `_02_de_02`), com os 25 arquivos batendo com o
manifesto SHA-256. O relatório, as evidências e a auditoria são os mesmos da quarta rodada, byte a byte;
o que é novo são nove originais. Os usados estão em `data/brutos/pesquisa-picos-2026-09-24/rodada5/`, com o
manifesto.

**Cadastrado:**

| Cidade | Rio | Data | Pico | Fonte |
|---|---|---|---|---|
| Rio dos Cedros | Rio dos Cedros | 27/11/2022 22h15 | 7,29 m | PLANCON 10.7, tabela da p. 9 e anexo da p. 55 |
| Itajaí | Itajaí-Açu | 09/09/2011 | 3,20 m | Tese UEM (2017), estação telemétrica nº 1, Quadro 11 e Figura 46 |
| Itajaí | Itajaí-Mirim | 09/09/2011 | 4,29 m | Tese UEM (2017), estação nº 3 (curso antigo), Quadro 13 e Figura 48 |

- **Rio dos Cedros:** o anexo da p. 55 é a captura de tela da leitura: 7,29 m parado de 22:15 a 23:00 e
  depois a descida (6,92 m às 03:00 de 28/11). As leituras antes de 22:15 não aparecem, então a hora é o
  início visível do patamar. Mesma régua não declarada e confiança baixa dos outros 14 do PLANCON. A
  tabela da versão 10.7 repete a da 1.07 para os anos anteriores, inclusive o "20/01/2020" que o anexo
  mostra ser 2021.
- **Itajaí, decisão do Jefferson:** entram as estações nº 1 e nº 3, com `referencia: null` e confiança
  baixa. A tese não diz qual DC de hoje é cada estação, e ligar por distância seria vínculo por lugar. Por
  isso a mancha de Itajaí continua sem acender, e o painel "quanto falta" recusa a comparação (há teste
  para os dois). A estação nº 2 (canal retificado) fica fora porque a tese se contradiz: o Quadro 12 diz
  3,21 m e a Figura 47 chega perto de 4,5 m.
- **Chat do site:** para Itajaí, deixa de eleger "a maior cheia". Lista cada pico com o rio e avisa que
  estações diferentes não se comparam. O bot do Telegram passa do motivo "não temos cheia registrada" para
  o das réguas com zeros diferentes, que é o motivo certo quando há registro.
- **Validador:** 4 desalinhamentos novos e nomeados, porque Itajaí só tem 09/09/2011 e as cheias de
  jul/ago de 2011 a montante são outros eventos.

**Conferido, mas fora do cadastro:**
- **Ituporanga 05/06/2017, 2,95 m às 5h** (Jornal de Pomerode): é a régua do centro, a municipal (a
  mesma notícia diz que o rio "sai da calha com 3,20 m"). A ANA 83250000, régua dos 5 registros de
  Ituporanga, marcou 4,66 m às 07h do mesmo dia. São réguas diferentes, e cadastrar misturaria as duas
  na mesma cidade. Entra quando Ituporanga tiver a série da régua da Ponte Vitório Sens.
- **Rio dos Cedros 2014 (ND+, 08/06):** é da subida e traz previsão, não o máximo. Não resolve 08 × 09/06.
- **PLANCON de Ilhota, plano de saúde de Rio dos Cedros, "Operação de Barragens" e relatório da UFSC
  (2017):** nenhum pico novo. O plano de saúde repete os 9,25 m de 1992, e o da UFSC fala de maré e de
  nível do mar.

## 13. Sexta rodada (27/09/2026), conferida nos originais

Pacote `fontes-originais-leve.zip` + `resultado.md` ("pesquisa v3.4, somente leitura", 26/09/2026): 33
originais e um relatório com 30 linhas de leitura, cada uma com o trecho literal. Os originais estão em
`data/brutos/pesquisa-picos-2026-09-24/rodada6/` com manifesto SHA-256 (34 guardados; o boletim SDE
008/2023, 3,8 MB e sem tabela de máximos, ficou só com o hash; a pasta dos boletins de Itajaí de 2013
veio vazia na versão "leve"). **Dezoito dos dezoito trechos que dependem de arquivo presente batem
letra a letra** com o original; o PDF do Orli (Taió) foi lido com pypdf, Tabela 1 e texto das pp. 12–13.

Antes de cadastrar, cada número foi cruzado com o que o repositório já tem: HidroWeb do Mirim
(Salseiro, Botuverá-Montante, Brusque), a série de 15 min da Salseiro pela DC de Brusque, e as séries
da ANA do Vale (Ituporanga, Apiúna, Taió, Timbó Novo).

**Cadastrado (8 registros, todos `confianca: baixa` por régua não declarada):**

| Cidade | Rio | Data | Pico | Fonte |
|---|---|---|---|---|
| Trombudo Central | Açu | 09/09/2011 06h | 5,58 m | Prefeitura ("5,58 cm" no original; lido como metros, ver nota) |
| Trombudo Central | Açu | 22/09/2013 | 3,10 m | Prefeitura |
| Trombudo Central | Açu | 11/10/2022 (tarde) | 3,00 m | Prefeitura |
| Lontras | Açu | 29/11/2023 01h | 6,41 m | ND+, atribuído à Defesa Civil |
| Vidal Ramos | Mirim | 22/09/2013 | 4,32 m | Revista Portuária (nota da Autoridade Portuária de Itajaí) |
| Rio dos Cedros | Rio dos Cedros | 02/01/1911* · 09/07/1983 · 07/08/1984 | 9,00 · 7,90 · 7,65 m | Defesa Civil de Rio dos Cedros, tabela em imagem (o PLANCON só cita os anos) |

**Divergências e complementos em registros existentes (nada adotado mudou de valor):**

- **Rio do Sul 2013-09** (10,39 municipal): + 10,47 m em 23/09 (Autoridade Portuária).
- **Indaial 22/09/2013** (6,46 COMPDEC): + 6,52 m (Autoridade Portuária).
- **Apiúna 22/09/2013** (7,14 ANA 17h): + 7,23 m — provável máximo entre leituras da mesma estação.
- **Brusque 2013** → **22/09/2013**: mesmo 7,61 m, agora com dia e fonte (Autoridade Portuária) no lugar de
  "Compilação informal" (guardado em `fonte_rotulo_anterior`).
- **Blumenau 23/09/2013** e **Taió 1983**: "confirmado por" (Autoridade Portuária 10,51 m; Rádio Mirador 11,85 m).
- **Taió 2013/2014/2015/2017** (tabela do Estudo Socioambiental): + os valores do Orli (2017; SED/SC, citando a
  Defesa Civil): 9,53 · 9,38 · 10,39 · 8,15 m, e uma **pendência** no registro de 2013.
- **Taió 09/10/2023** (12,40 g1): nota com o 11,86 m às 02h21 da Rádio Mirador e os 12,25/12,32 m da ANA.
- **Timbó 2014** (9,58 Câmara): + 9,12 m às 22h (AMVE); nota com a ND (8,61 e 8,95 m, régua da Rua
  Equador) e a ANA (9,00 m às 07h e 17h de 09/06). Nenhuma fonte confirma 9,58; decisão do Jefferson se o
  adotado muda.

**O que os cruzamentos mostraram:**

- **Os dois "picos de Vidal Ramos" de 2023 são a Salseiro, não a régua da cidade.** O 3,47 m às 05h15 de
  29/10/2023 é, ao centímetro e ao minuto, o máximo da série de 15 min da estação 31 da DC de Brusque
  (SALSEIRO); o 4,0 m às 14h45 de 07/10 a própria matéria atribui à "estação ANA/Epagri". A Salseiro fica
  6,8 km da sede, em `codigo_ana_nao_e`. **Não cadastrados.** Já o 4,32 m de 22/09/2013 **não** é a Salseiro
  (ANA: 3,10/3,38 m no dia; crista dela em 20/09, 4,10 m) — entrou como régua não declarada.
- **A nota da Autoridade Portuária de 2013 lista as réguas das cidades, não as da ANA:** Brusque 7,61 m contra
  5,68/5,72 m na ANA 83900000 no mesmo dia. Isso diz que **em 2013 a régua municipal de Brusque e a
  83900000 não coincidiam** como coincidem em 2019–2021 (`docs/HIDROWEB-MIRIM-2026-09-22.md`) — zero ou
  régua diferentes, o motivo fica em aberto. Consequência: os cinco picos de Brusque da ANA que entraram
  em 22/09/2026 (1961–2015) são piso **na régua da ANA**, e a coincidência com o municipal só vale onde foi
  medida.
- **Ituporanga 22/09/2013, 5,82 m: não é a ANA 83250000** (2,68/3,54 m no dia). É outra régua, provavelmente
  a municipal manual da Ponte Vitório Sens. Como os cinco registros de Ituporanga são da ANA, cadastrar
  misturaria as duas — mesma razão do 2,95 m de 2017 (§12). **Fora**, até haver a série municipal.
- **Taió: a tabela do Estudo Socioambiental deslocou um ano.** O Orli dá 9,38 m para **2014**, e a ANA
  83050000 marcou 9,37 m às 17h de 09/06/2014; a tabela do Estudo põe 9,38 m em "jun/2013", quando a ANA
  marcou 6,80 m, e a ANA de set/2013 chega a 9,70 m (17h), perto dos 9,53 m que o Orli dá para 2013. Fica
  como pendência no registro; corrigir só com a Defesa Civil de Taió.
- **Timbó 2014: a régua da Rua Equador e a ANA 83677000 andam juntas** (8,95 m às 14h × 9,00 m às 07h/17h
  de 09/06). Pista para o vínculo, não prova.
- **Gaspar 23/09/2013, 8,03 m (Autoridade Portuária): fora do cadastro por decisão técnica.** A tabela oficial de
  Gaspar (48 registros, `referencia: régua`) não tem 2013. Um registro novo sem `referencia` faria o site tratar
  Gaspar como duas escalas e parar de comparar o nível atual com o histórico (`cenarioAnterior`), e afirmar
  `referencia: régua` seria vínculo por nome. **Entra só por decisão do Jefferson**, com a referência que ele
  decidir declarar.

**Conferido, fora do cadastro (regra 3 da §5: leitura não é pico):** Itajaí, boletins de set/2013 (1,67 m,
estação não declarada; a pasta veio vazia), 08/09/2011 (1,23/1,94/1,19 m às 08h) e out/nov de 2023 (2,89 m
às 02h20 na DC-02, 2,22 m na DC-04, 2,46 m na DC-06, a lista das 13h10 de 09/10 — as primeiras leituras
de Itajaí **com régua nomeada** depois de 2011, guardadas na §3 como pista); Botuverá 22/10/2015 (5,15 m às
14h30) e 29/10/2023 (4,52 m "subindo"); Taió 22/10/2015 (8,73 m às 14h, subida). Contexto guardado:
Plano de Contingência de Itajaí v17 (22/12/2025) em PDF, telemetria de Itajaí no Wayback de 2017 (nomes
antigos das réguas: DC02 = TEPORTI), estação da DCSC em Ascurra instalada em 12/12/2023 (se for a
DCSC-00003, não há leitura dela para 2008–2023).

## 14. Sétima rodada (02/10/2026), conferida nos originais

Pacote `fontes-rodada3.zip` + `resultado.md`/`.pdf` ("Rodada 3", pesquisa v3.5, 01/10/2026): 77 originais
e um relatório com o trecho literal de cada número. Tudo em `data/brutos/pesquisa-picos-2026-09-24/rodada7/`
com manifesto SHA-256. Quatro PDFs grandes (TCC da UFSC 7 MB, JICA Vol. III-B 3,7 MB, Boletim SDE 87
3,5 MB, JICA Vol. III-A inteiro 2,3 MB) ficaram só com o hash; as páginas citadas de cada um estão em
`originais/` como extrato (`derivado_de` no manifesto). **Todos os trechos usados batem letra a letra com
o original.** Três correções ao relatório: o ARMAX de Rio do Sul está na p. 2 do PDF (não na 1); a frase
do Boletim SDE 87 está na p. 13 (não na 1); e O Município de 18/11/2023 dá os 10,30 m a **1984**, não a
2011.

**Registros novos (8):**

| Cidade | Data | Pico | Fonte | Confiança |
|---|---|---|---|---|
| Blumenau | 29/09/2009 · 29/06/2014 · 06/06/2017 · 05/10/2023 · 09/10/2023 06h · 29/10/2023 · 03/11/2023 | 8,06 · 8,13 · 8,52 · 8,78 · 10,19 · 8,38 · 9,50 m | Lista oficial "Enchentes Registradas" do AlertaBlu (original salvo) | alta, `referencia: null` |
| Botuverá | 22/07/2026 13h | 4,80 m | O Município ("Defesa Civil detalha cenário") | baixa |

As sete de Blumenau são as que a lista oficial tem e o repositório não tinha — o "dez datas ausentes" de
`docs/PESQUISA-2026-09-06-CRUZAMENTO.md`, conferido agora no original. O site agrupa 05, 09 e 13/10/2023 num
evento só (mesma referência, sete dias) e fica com o maior, então a tela daquele outubro não muda. A de
29/09/2009 dá par à cheia de Rio do Sul de set/2009, e o aviso do validador sobre ela sumiu.

**Hora da crista em registros existentes** (só onde a fonte diz pico/máximo e o valor é o adotado; fuso
não declarado em todas): Blumenau 24/11/2008 0h, 23/09/2013 2h, 23/10/2015 1h, 17/11/2023 9h45; Rio do
Sul 13/10/2023 3h10 e 18/11/2023 0h40; Brusque 17/11/2023 ~21h. Blumenau 19/05/2024 ficou sem hora: O
Auditório dá 8,67 m às 12h, mas não chama de pico.

**Divergências e confirmações (nenhum valor adotado mudou):** Blumenau 2011 — o 12,60 da Defesa Civil,
que estava "não conferido", agora tem original, e a hora (11h); o 12,8 adotado aparece na Tabela 3 do
Esboços (CEOPS), e a nota diz que o artigo ABRH citado como fonte dá 13,0. Blumenau out/2023 — +10,76 m
(lista oficial, 12/10); o 10,75 ganhou fonte (Mesorregional, meia-noite). Rio do Sul 2011 — +12,91 (ND,
22h de 09/09) e +12,98 (CEOPS); ago/2011 +8,76 (CEOPS); 1983 +13,53 (GCD); nov/2023 +13,02 à 1h (Jornal
Nacional). Taió 09/10/2023 — +12,11 (Diarinho, "marca histórica"; MetSul, leitura das 5h). Brusque 2011 —
+10,21 (CEOPS) e +10,3 (O Município 2026, sem atribuição, provável troca com 1984); 2008 +8,88 (Defesa
Civil via O Município); o 10,30 de 1984 que já era divergência ganhou fonte da Defesa Civil. Indaial
09/09/2011 +7,6 (CEOPS). Confirmados: Timbó 2011 (9,86, CEOPS), Rio do Sul 1911, 1983 e 2001 (ARMAX e
Esboços).

**Esboços, Tabela 3 (CEOPS): só a linha de 09/09/2011 tem os sete valores.** Nela a coluna é lida. Nas
outras a linha sai do PDF numa tira só, e a coluna é inferida — por isso os 11,72 m de "2008 24/11" ficaram
fora de `divergencias`, só na nota. O padrão que essa tabela mostra é o que importa para Blumenau: o CEOPS
fica **+0,20 m** acima do AlertaBlu em 31/08/2011 (8,7 × 8,5) e 09/09/2011 (12,8 × 12,6), e talvez em 2008
(11,72 × 11,52), mas **igual** em 2001 (11,02), 1992 (12,8) e 1983 (15,34).

**Blumenau, referência — a lista do AlertaBlu chegou, e não autoriza converter nada.**
`scripts/conferir_blumenau_alertablu.py` roda pela primeira vez, agora lendo o HTML original. O primeiro
resultado foi "AlertaBlu em IBGE, subtrair 0,20 m" — e estava errado por dois motivos, corrigidos com
teste: (1) o pareamento casava enchentes diferentes do mesmo mês (29/10/2023 com 13/10/2023, dando
−2,23 m); (2) os 58 pares rotulados IBGE vêm da Tabela 4 de Cordero & Medeiros, que **termina em 2001**,
e o veredito estendia a série inteira uma medida feita só até lá. Agora o veredito é
`so_ate_o_ultimo_rotulado` (saída 2): a lista reproduz a Tabela 4 ao centavo até 2001; de 2008 em diante
nada a julga, e o CEOPS diz +0,20 m. É o caso 3 do script — **muda com a época — não converter.**

**ANA 83800002, 1983 e 1984 (serviço `HidroSerieHistorica`, XML original).** Valores **diários** de régua
(`TipoMedicaoCotas` 1), sem unidade declarada: julho/1983 máximo 1519 no dia 9 (consistido); agosto/1984
1485 no dia 7 (bruto e consistido). Não é a crista, então **não é o teste que a regra pede**. Mas há uma
pista: se a unidade é cm e o zero é o da régua de 1983, um valor diário de 15,19 m não cabe abaixo de uma
crista de 15,14 m (15,34 − 0,20) — naquele ano o deslocamento seria de no máximo 0,15 m. 1984 (14,85 m)
não decide nada. O artigo da FURB (Cordero, Salvador, Refosco, XX SBRH) ainda diz que, depois de 2011, a
referência da régua da ANA "ficou 40 cm a menos do que as enchentes anteriores". Três números para a
mesma pergunta (0,20; ≤ 0,15 em 1983; 0,40 depois de 2011) — **a regra bloqueante fica**, e a pergunta à
FURB ganha três itens. Ver `docs/fontes-academicas.md`.

**JICA 2011, Tabela 7.5.1 (p. A-80) — lida na página.** As 20 células da matriz de
`transito.json._meta` (Indaial, Blumenau, Gaspar, Ilhota e Itajaí × 5/10/25/50 anos) e as 12 horas da coluna
de 5 anos em `hidrograma_de_projeto` batem uma a uma com a página renderizada (Rio do Sul às 08/06 22:00 em
todas as colunas). A pendência "confirmar na p. A-80" fecha; `horas_min`/`horas_max` não mudaram, porque nada aqui
pede isso. Ver `docs/JICA-2011-VERIFICADO.md`.

**Barragens, o que cada número mede.** 83 e 93,5 hm³ são a "gross/total storage capacity" da JICA
(Vol. III-B, Tabelas 2.2.1 e 7.1.1). O TCC da UFSC (Tabela 4.4, "adaptado de JICA 2011") mostra que 83,00 é
o volume acumulado até a cota **360,00 m** (crista do vertedouro), e 101,84 até 362,30 m; a JICA propôs
alteamento de 2 m (+16,2 hm³ na Oeste; Sul para 110 hm³). 100/110 (NSC 2023) e 104,03 (RWTV, Sul, 2026) são
números pós-alteamento. O 99,96 do painel Asthon não está em nenhum original. Nada muda no site: os
percentuais seguem os publicados pela Asthon.

**Maré:** a tábua de 2027 não está publicada nas capturas da CHM de 21 e 28/09/2026 (só 2026, 63ª ed.).

**Decidido pelo Jefferson em 02/10/2026** (aplicado no PR seguinte ao desta rodada):
- Blumenau: adotado **10,76 m em 12/10/2023** (lista oficial, data definida); o registro de 13/10 com 10,61 m (g1)
  virou divergência, com o 10,75 m do Mesorregional.
- Brusque 1984: adotado **10,30 m** (Defesa Civil via O Município, confiança média); o 10,5 m adotado antes ficou
  em divergências, com a fonte antiga.
- Ascurra: **cadastrado 01/09/2026, 10,13 m às 05:10** (hora de Brasília, carimbo da API historic), DCSC-00003 —
  Ponte do Beber, `referencia: régua`; a ND ("por volta das 6h", fuso não declarado) confirma.
- Gaspar 09/10/2023 e 09/09/2011 e Indaial 04/10/2023: **não** entram na série. Ficam em
  `data/eventos-pendentes-regua.json` (referência não declarada), fora de recordes, comparação com o nível atual,
  gráficos e modelos de propagação, até a fonte identificar a régua ou permitir reconciliar os zeros. Indaial não
  se vincula sozinho à DCSC-00006: o deslocamento dela para a régua da COMPDEC continua pendente.

**O que estava para decisão (registro de como a rodada foi entregue):**
- Blumenau out/2023: adotar 10,76 m (lista oficial, 12/10) no lugar de 10,61 (g1, sem original)?
- Brusque 1984: o 10,30 m agora tem fonte da Defesa Civil (O Município, duas matérias); o adotado é 10,5.
- Ascurra 01/09/2026: a ND (10,13 m "por volta das 6h", Ponte do Beber) bate com a crista da DCSC-00003
  (10,13 m às 05:10, platô 04:50–06:20). Segue fora, como o `CLAUDE.md` manda, até a sua decisão.
- Gaspar 09/10/2023 (pico 7,09 m às 7h50, boletim municipal, "acima da normalidade") e Gaspar 09/09/2011
  (9,42 m, CEOPS): Gaspar é toda `régua`; um registro sem referência para a comparação (mesmo caso de 2013).
  Os boletins de 13/10/2023 também marcam 7,48 m às 3h, acima dos 7,45 da tabela oficial — leitura, não pico.
- Indaial 04/10/2023 (5,75 m "máxima registrada", Defesa Civil via imprensa): mesmo motivo.
- Rio do Sul: o ARMAX (CEOPS) diz que 12,20 m de 1911 está "referenciada na régua da atual estação
  fluviométrica" — pista para a régua do Histórico de Cheias, não prova.

**Conferido, fora do cadastro:** Blumenau 08/10/2023 9,49 m (1º ciclo, AlertaBlu via ND; a lista oficial
não traz como enchente separada); Taió set/2013 (leituras: 5,46 m e 8,78 m) e a primeira cota de enchente,
7,5 m, região da antiga Apae (régua do Centro); cotas de Ascurra (8,50 / 9,76 / 10,76 m) — as mesmas de
`estacoes.json`, que vieram da resposta da Defesa Civil municipal (C18); Ituporanga 3,58 m e Apiúna 7,94 m
em 22/09/2013 15h (leituras, "cota de Alerta"). Ibirama, Botuverá, Guabiruba, Vidal Ramos e Lontras: nenhuma
cota oficial com nome de régua.

## 15. Oitava rodada (02/10/2026), conferida nos originais

Pacote `cheias_itajai_fontes_2026-10-01` em duas partes (21 arquivos + `README_resultados.md`, pesquisa de
01/10/2026 feita com o prompt v3.5). Todos os sha256 batem com o manifesto da pesquisa. Ficaram em
`data/brutos/pesquisa-picos-2026-09-24/rodada8/` com manifesto próprio; quatro arquivos são **duplicatas**
de rodadas anteriores (artigo ABRH de Blumenau, página de metragem de Rio do Sul, JICA Vol. III-A, boletim
SDE 008/2023) e entraram só com o hash; quatro PDFs grandes entraram como extrato das páginas citadas. A
pesquisa é quase toda de resultados negativos, e o que ela traz de novo é contexto, não pico:

- **Rio dos Cedros, 8,96 m de jun/2014.** (1) O relatório do CEOPS/FURB de dez/2016 (estudo hidrológico e
  mapeamento de Rio dos Cedros) diz que o evento "alcançou 8,96 m na régua de referência", que a cota
  topográfica foi tirada "na estação telemétrica" ("8,96 m na régua limnimétrica, atingindo a altura
  topográfica de 72,408 m") e que a recorrência é de cerca de 50 anos — entrou como "confirmado por" no
  registro. (2) **A pendência do registro estava errada:** dizia que a crista foi "provavelmente madrugada
  de 09/06". O registro do Anexo I (pp. 49–50), igual nas versões v1.07 e v10.4, tem 142 leituras sem salto
  e passa por DUAS meias-noites antes dos 8,96 m: a crista seria na madrugada de **10/06**, 00:45–02:00 —
  por contagem, porque a página não repete a data. Corrigido na pendência; a data do registro continua a
  da tabela (08/06).
- **Faixas por estação da ANA, em centímetros** — Manual de Operação da Sala de Situação ANA/Epagri/Ciram,
  pp. 63–67: atenção/alerta/emergência por código e nome de estação (ex.: 83800002 Blumenau 400/600/850 cm;
  83500000 "Apiúna - Régua Nova" 400/600/850; 83677000 Timbó Novo 300/500/700; 83050000 Taió 400/600/750;
  83250000 Ituporanga 200/300/400; 83300200 Rio do Sul - Novo 400/500/650; 83892990 Salseiro 300/400/500;
  83900000 Brusque 300/400/500). São faixas **operacionais da Sala de Situação para a régua da ANA**, não
  cotas da Defesa Civil municipal, e não entram em `estacoes.json` sem decisão. Servem, porém, a duas
  coisas: dão cotas com nome de régua para as estações da ANA que já estão no cadastro (Apiúna, Timbó Novo,
  Ituporanga), e mostram que a ANA trabalha com essas cotas **em cm** — apoio, não prova, à leitura do
  "1519" de 09/07/1983 como 15,19 m (§14).
- **Plano de Recursos Hídricos da bacia (cap. A2).** Tabela A2.3 (fonte CEOPS/FURB): as faixas normal/atenção/
  alerta/emergência por município, sem nome de régua — não servem para o cadastro, como a própria pesquisa
  marcou. Tabela A2.4 (fonte DEOH): "Volume do reservatório" Oeste 83,00 e Sul 93,50 × 10⁶ m³, níveis
  mínimo/máximo e cotas do vertedor; o texto da mesma página dá 97 × 10⁶ m³ para a Sul. Divergência
  guardada aqui; nada muda no site.
- **Rio do Sul, sistema novo.** A prefeitura inaugurou em jul/2026 oito estações fluviométricas novas, entre
  elas a da Ponte Dom Tito Buss, e diz que o histórico de níveis "faz parte do sistema antigo de
  monitoramento". Isso explica por que a régua do Histórico de Cheias não se resolve olhando a estação de
  hoje. Os registros históricos de Rio do Sul seguem com `referencia: null`, então o site não os compara
  com o nível ao vivo.
- **Guabiruba, notícia 46906:** finalmente baixada; não traz nível de rio. O item sai do prompt.
- **Negativos** (nada encontrado com original e régua): Ascurra e Guabiruba antigos, Itajaí por régua,
  boletim SDE de set/2026 (ainda não publicado em 01/10), Lontras, Vidal Ramos, Trombudo Central, Botuverá,
  réguas municipais de Ituporanga/Ibirama/Apiúna/Ilhota, Timbó 9,58 m, Taió 1983 e set/2013, Rio dos Cedros
  depois de 2022, tábua de marés de 2027.

O prompt v3.6 (§6) já sai com esses ajustes. Nenhum pico novo, nenhum valor adotado mudou.

## 9. Estado

- [x] Chat: cidade sem pico passa a dizer o motivo e mostrar o impacto do Atlas, sem metro (PR #409).
- [x] Pesquisa web, primeira rodada: pistas na §7, nenhuma conferida (rede bloqueada).
- [x] Segunda rodada conferida nos originais: 14 registros (§8).
- [x] Itajaí: máximos de set/2011 por estação (tese UEM, estações nº 1 e nº 3), em 25/09/2026 (§12).
- [ ] Itajaí: qual DC de hoje é cada estação telemétrica de 2011, e as outras cheias (1983, 1984, 2008, 2013…).
- [x] Séries da ANA baixadas: picos extraídos por `scripts/picos_ana_vale.py`, e os 5 maiores de Ituporanga, Ibirama, Apiúna e Ilhota entraram marcados como régua da ANA (confiança baixa) — ver `docs/HIDROWEB-VALE-2026-09-24.md`.
- [x] Terceira rodada conferida nos originais: 18 registros (§10).
- [x] Taió e Timbó: cheias da ANA que a série municipal não tem (7 + 26), em 25/09/2026 — ver `docs/HIDROWEB-VALE-2026-09-24.md`.
- [x] Quarta rodada conferida nos originais (§11).
- [x] Quinta rodada conferida nos originais: Rio dos Cedros nov/2022 e Itajaí set/2011 (§12).
- [x] Sexta rodada conferida nos originais: 8 registros (Trombudo ×3, Lontras, Vidal Ramos 2013, Rio dos Cedros ×3) e as divergências de 2013 da Autoridade Portuária, do Orli (Taió) e da AMVE (Timbó), em 27/09/2026 (§13). Gaspar 2013 e Ituporanga 2013 ficam para decisão.
- [x] Sétima rodada conferida nos originais: 8 registros (7 de Blumenau da lista oficial do AlertaBlu, Botuverá 22/07/2026), horas de crista, divergências do CEOPS/imprensa, Tabela 7.5.1 da JICA lida, e a lista do AlertaBlu cruzada com a série — não converter (§14), em 02/10/2026.
- [x] Decisões da sétima rodada aplicadas em 02/10/2026: Blumenau 12/10/2023 = 10,76 m; Brusque 1984 = 10,30 m; Ascurra 01/09/2026 = 10,13 m (primeiro pico da cidade); Gaspar e Indaial em `data/eventos-pendentes-regua.json`.
- [x] Prompt da §6 na versão 3.6 (02/10/2026): sai o que a sétima rodada e a FURB resolveram (JICA A-80, referência da Tabela 4), Ascurra e Guabiruba pedem só o que a série da DCSC não cobre, e entram a troca de régua de 2011 em Blumenau, Gaspar/Indaial sem régua e as páginas vistas só em resumo de busca.
- [x] Oitava rodada conferida nos originais (02/10/2026, §15): nenhum pico novo; Rio dos Cedros 2014 ganhou a régua (relatório CEOPS/FURB 2016) e a pendência do dia foi corrigida para 10/06 por contagem; faixas da Sala de Situação ANA/Epagri por estação, em cm, documentadas.
- [ ] Guabiruba: ainda sem pico. Ascurra: só 01/09/2026; o 10,46 m de 12/09/2026 continua candidato fora. (Botuverá ganhou dez/2023 e set/2026 na quarta rodada; Itajaí, set/2011 na quinta.)
- [x] Botuverá 8,61 m: **removido em 25/09/2026 por decisão do Jefferson**. Era exatamente o máximo da estação DCSC de Brusque em 17/11/2023 (Boletim SDE 011/2023, p. 18), e Botuverá não aparece na tabela. A cidade volta a zero pico.
