# HidroWeb no Itajaí-Mirim: quatro réguas e seis pluviômetros da ANA, 1929–2026, conferidos (22/09/2026)

Em 22/09/2026, minutos depois da chuva do INMET, o Jefferson exportou do HidroWeb (ANA/SNIRH, pelo
navegador dele; o domínio não responde deste ambiente) as estações **convencionais** da ANA no
Itajaí-Mirim e entregou, junto, três derivados: cotas e chuva em formato longo e um JSON de
picos de Brusque com o pico a montante e a antecedência (1997–2021). Este documento diz o que os
arquivos são, o que foi conferido aqui, e o que eles respondem.

**Nada entrou em `enchentes.json`, `estacoes.json` ou `transito.json`.** O que sai daqui são
candidatos e medidas para decisão do Jefferson. Cota da ANA está no zero da ANA; antecedência é
horário, e horário não depende de zero.

## Os arquivos

Em `data/brutos/hidroweb-mirim-2026-09-22/`, os onze zips **como o HidroWeb os entregou** (dois
zips externos do portal, `HidroWEB_CSV_2026-09-22T15_42_22.512Z.zip` e `…T15_43_43.205Z.zip`,
abertos aqui; sha256 dos externos `42b9f7e5…` e `c7c1406c…`), mais os três derivados:

| estação | tipo | município | período com dado | o que veio |
|---|---|---|---|---|
| 83900000 Brusque (PCD) | cota | Brusque | 06/1929 → **03/2022** | cotas 07h/17h e média diária; vazões, curva-chave, seção |
| 83892990 Salseiro | cota | Vidal Ramos | 11/1987 → 04/2026 | idem |
| 83892998 Botuverá-Montante | cota | Botuverá | 05/1986 → 03/2026 | idem |
| 83893000 Botuverá | cota | Botuverá | 01/1978 → 08/1992 | idem (desativada) |
| 83905000 Brusque (SDE-SC) | cota | Brusque | — | **só qualidade de água**; sem cota |
| 2748000 Brusque (PCD) | chuva | Brusque | 01/1941 → 03/2022 | chuva diária |
| 2748014 Brusque (INMET) | chuva | Brusque | 03/1935 → 05/1966 | chuva diária e clima |
| 2749033 Vidal Ramos | chuva | Vidal Ramos | 04/1976 → 04/2026 | chuva diária |
| 2749038 Botuverá | chuva | Botuverá | 01/1978 → 08/1992 | chuva diária |
| 2749045 Botuverá-Montante | chuva | Botuverá | 08/1986 → 03/2026 | chuva diária |
| 2749107 Vidal Ramos – Rio das Pacas | chuva | Vidal Ramos | — | **zip vazio** (22 bytes) |

Coordenadas e períodos vêm do inventário público da ANA já versionado
(`data/brutos/ana-inventario-api-2026-09-08.json`); estão em `scripts/hidroweb_csv.py::ESTACOES`.

Derivados (sha256 dos originais; a cota e a chuva foram comprimidas aqui, `gzip -9`):

```
d1b6a97dae3a4e7bbe452b8098b7ca643a6f784afc6e17c9371e4a94328784b4  ana_cotas_itajai_mirim.csv
d403b325479e8af9f108e1efe17899aa0d5c69ad25f7b0e58f383790c226230a  ana_chuva_diaria_itajai_mirim.csv
75b2581802fa0abd4c25fcab962f4ddb60c96e7c85769efe12aaf47b9ae34ca1  picos_itajai_mirim_1997_2021.json
```

## O formato do HidroWeb, e a regra dos derivados

Uma linha por **mês**, uma coluna por dia (`Cota01…Cota31`), cada uma com status ao lado. Cotas em
**centímetros inteiros**; chuva em mm com vírgula, entre aspas. Para cota, o mês vem em até quatro
linhas: nível 1 (bruto) às 07h, às 17h e média diária, e nível 2 (consistido) só média diária.
Status: 1 real, 2 estimado, 3 duvidoso, 4 régua seca.

`scripts/hidroweb_csv.py` lê os zips e reproduz os três derivados
(`python3 scripts/hidroweb_csv.py --conferir`; `scripts/teste_hidroweb_csv.py`, 19 testes):

- **Cotas: 165 947 linhas iguais, 0 diferentes.** Regra: leitura das 07h/17h = nível 1; média
  diária = nível 2 quando o **dia** tem valor consistido, senão nível 1. `consistido` = nível 2.
  `suspeito` = status 3 (duvidoso) mais duas marcações manuais do Jefferson (abaixo).
- **Chuva: 69 087 linhas iguais, 0 diferentes.** Mesma regra por dia.
- **JSON de picos: 32 dos 34 eventos reproduzem exatamente** (cota de Brusque, cota e
  antecedência das duas estações a montante). Os 2 restantes — 27/01/1997 (503 cm) e
  16/10/2015 (462 cm) — são sub-picos a menos de 5 dias de um pico maior; a corrida de 5 dias
  deste script os funde ao maior, e o critério do Jefferson os separou. Nenhum dos 34 usa
  leitura implausível (teste).

## Os erros de digitação do HidroWeb, e por que os "recordes" de Brusque não são

A instantânea bruta tem dedo de digitador que a consistência da ANA corrige na **média** e deixa
na **leitura**. `implausiveis()` acha leitura das 07h/17h maior que 2 × média consistida do dia
+ 1 m. O que ela pega:

| estação | leitura | valor | média consistida do dia | o que é |
|---|---|---|---|---|
| Salseiro | 24/12/2009 07h | 3 145 cm | 174 | 145, com um 3 na frente; `suspeito` no derivado |
| Salseiro | 03/10/2020 17h | 434 cm | 138 | **conferido na série de 15 min da DC de Brusque: 1,49 m** no dia |
| Salseiro | 15/04/2023 07h | 1 140 cm | 143 | **idem: 1,49 m** no dia; 140 com um 1 na frente. Não marcado no derivado |
| Salseiro | 25/03/2024 17h | 167 165 cm | (sem consistido) | 167 colado em 165; `suspeito` no derivado |
| Botuverá-M | 03/04/2002 17h · 29/10/2013 07h | 490 · **903** | 151 · 117 | os 903 cm eram o "recorde" da estação |
| Brusque | 19/11/1941 · 22/06/1943 · **04/02/1944** · **11/04/1958** · **20/02/1978** · 26/11/1985 · 22/10/1975 | 1 047 · 912 · **1 444** · **1 347** · **1 204** · 994 · 775 | 147 · 90 · 142 · 150 · 123 · 115 · 173 | os sete maiores números da série, todos com média do dia entre 0,9 e 1,7 m |

Ou seja: **os "14,44 m de 1944" e "13,47 m de 1958" de Brusque não existem**; quem ordenar a
série bruta por valor acha primeiro os erros. As cheias reais ficam abaixo (próxima seção). A
série da Defesa Civil de Brusque (`docs/SALSEIRO-DC-BRUSQUE-2026-09-08.md`) serviu de árbitro
independente para as duas de Salseiro que restavam em dúvida.

## Brusque: a régua da ANA é a régua municipal — e mostra cheias que o cadastro não tem

A 83900000 fica a ~51 m do pino de Brusque (DCSC-00019, `estacoes.json`). Os dados confirmam que
é a **mesma régua**: nas cheias com dia no cadastro, a leitura das 17h da ANA é o valor municipal
**ao centímetro** — 31/05/2019 **590 cm × 5,90 m**; 12/10/2021 **568 × 5,68**; 24/01/2021 442 ×
4,82 (crista entre leituras). Nas cheias grandes a leitura de 07h/17h **perde a crista**:
09/09/2011, 890 cm às 17h contra 10,03 m municipal (média do dia 790, do dia seguinte 450: a
crista foi de madrugada); nov/2008, **sem leitura de 20 a 24/11** (a consistência estimou 507 no
dia 24; o cadastro tem 8,50); ago/1984, 758 cm às 07h de 06/08 e depois **em branco** (o
cadastro tem 10,50). Leitura de 07h/17h é **piso**, nunca crista.

Com isso dito, corridas de ≥ 600 cm na 83900000 (sem as implausíveis), contra o cadastro:

| pico ANA (07h/17h) | cm | média consistida | cadastro de Brusque |
|---|---|---|---|
| 18/11/1939 07h | 640 | 640 | — |
| 02/08/1943 17h | 660 | 620 | — |
| 17/05/1948 17h | 667 | 618 | — |
| 06/12/1956 17h | 638 | 368 | — |
| **01/11/1961 07h** | **789** | **780** | — |
| 04/08/1972 17h | 680 | 640 | — |
| 17/08/1977 17h | 680 | 636 | — |
| **26/12/1978 17h** | **800** | 650 | — |
| 20/05/1983 07h | 690 | 686 | — |
| **12/07/1983 07h** | **754** | 704 | — (a cheia de jul/1983 do Açu, também no Mirim) |
| 02/08/1983 17h | 700 | 526 | — |
| 06/08/1984 07h | 758 | 758 | 1984-08, 10,50 m (leitura seguinte em branco) |
| 01/02/1997 17h | 664 | 654 | — |
| 27/11/1997 17h | 652 | 651 | — |
| 28/04/1998 17h | 646 | 622 | — |
| **01/10/2001 07h** | **745** | 609 | — |
| 12/03/2011 17h | 628 | 413 | — |
| 10/08/2011 07h | 650 | 535 | — |
| 30/08/2011 17h | 618 | 523 | — |
| 09/09/2011 17h | 890 | 790 | 2011-09, 10,03 m |
| 09/06/2014 07h | 630 | 515 | — |
| **22/10/2015 07h** | **772** | **756** | — |
| 01/06/2017 07h | 684 | 573 | — |

**Candidatos para o Jefferson decidir**, e só ele: out/2015 (≥ 7,72 m, média do dia 7,56 — uma
cheia maior que a de nov/2023 no cadastro, e ausente), out/2001 (≥ 7,45), dez/1978 (≥ 8,00),
nov/1961 (≥ 7,89), jul/1983 (≥ 7,54). Todos com a ressalva de sempre: leitura de 07h/17h é piso
da crista, o zero é o da ANA (que coincide com o municipal em 2019–2021, e não se sabe desde
quando), e a fonte é o HidroWeb com `confianca` a definir. A série **para em 03/2022** no
HidroWeb, embora o inventário diga `Operando: 1`; é o quarto caso de `Operando` que não prova
estação viva.

## Salseiro e Botuverá-Montante: relógio a montante, com resolução de 10/14 h

As duas não são as réguas das cidades (Salseiro fica 6,8 km da sede de Vidal Ramos, rio abaixo;
Botuverá-Montante 3,5 km rio acima do pino de Botuverá — `docs/CODIGOS-ANA-PENDENTES.md`). Para
**horário** elas servem, e é o que o JSON do Jefferson mede: para cada pico de Brusque ≥ 450 cm
(1997–2021, 34 eventos), o maior valor nas 72 h anteriores em cada uma e a antecedência.

| antecedência (h) | 0 | 10 | 14 | 24 | 34 | 38 | 48 | 58 | 72 |
|---|---|---|---|---|---|---|---|---|---|
| Salseiro → Brusque | **14** | **10** | 3 | 2 | 1 | — | 2 | 2 | — |
| Botuverá-M → Brusque | **18** | **8** | 6 | — | — | 1 | — | — | 1 |

Leitura: com leituras às 07h e 17h, "0" quer dizer **o mesmo intervalo** (o pico de cima e o de
baixo caíram entre duas leituras), e "10" ou "14" quer dizer **o intervalo anterior**. Então:
**Botuverá-Montante → Brusque fica quase sempre dentro de 14 h** (32 de 34), e **Salseiro →
Brusque, dentro de 14 h em 27 de 34**, com uma cauda de 1–2 dias em cheias longas. É coerente
com o único par medido com hora nas duas pontas (15/12/2020: Salseiro 13h15 → Brusque 20h45,
**7,5 h**, `docs/SALSEIRO-DC-BRUSQUE-2026-09-08.md`) e com a estimativa de 6 h que
`transito.json` tem para Brusque → Itajaí. O que estes 34 eventos **não** dão é uma faixa
fina: a resolução é o dobro do valor. Se o Jefferson quiser um elo `vidal-ramos → brusque` ou
`botuvera → brusque` em `transito.json`, o número honesto é "**até ~14 h**, tipicamente
0–10 h", `confianca: media`, fonte esta série — e com a ressalva de que as estações não são as
réguas das cidades. Não escrevi.

## Novembro de 2008 no Mirim: os 160 mm do JICA

A mesma leitura feita para o Açu com o INMET (`docs/INMET-CHUVA-2026-09-22.md`) vale para o
Mirim com os pluviômetros da ANA:

| 21–24/11/2008 | 4 dias | 20–24 | novembro | maior dia |
|---|---|---|---|---|
| 2749045 Botuverá-Montante | **334,1 mm** | 349,6 | 560,3 | **165,2 (23/11)** e 106,5 (24/11) |
| 2748000 Brusque (PCD) | **287,0 mm** | 296,5 | 487,4 | 109,5 (24/11) |
| 2749033 Vidal Ramos | 53,8 mm | 61,2 | 218,2 | 28,5 (21/11) |

Os "160 mm em 4 dias na sub-bacia do Mirim" do JICA cabem numa **média** entre uma cabeceira
quase seca (Vidal Ramos, 54) e o médio/baixo Mirim encharcado (Botuverá 334, Brusque 287) — o
mesmo desenho do Açu (Ituporanga 46, Indaial 247). A pendência do JICA continua sendo qual área
e qual janela; o que muda é que os números deixaram de parecer errados.

## Cuidados de leitura, e o que não fazer

- **Sem horário de verão** nos carimbos "07:00" e "17:00": são a hora da leitura do observador,
  como o HidroWeb registra. Para antecedência em dezenas de horas, não importa.
- **Média consistida ≠ crista.** A consistência corrige dedo; não recupera o que o observador
  não leu.
- **Cota da ANA em cm, no zero da ANA.** Comparar com `enchentes.json` só onde se provou a mesma
  régua (Brusque, 2019–2021), e mesmo ali como piso.
- **Não copiar 14,44 / 13,47 / 12,04 m** para lugar nenhum: são erros de digitação.
- **HidroWeb e a referência de Blumenau:** já testado em 06/09
  (`docs/HIDROWEB-BLUMENAU-E-RIO-DO-SUL.md`) — para 1983/1984 a 83800002 só tem média diária, e
  o teste da REGRA_REFERENCIA_BLUMENAU não se faz com estes exports. Continua com a FURB.
