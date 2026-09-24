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

## 7. Estado

- [x] Chat: cidade sem pico passa a dizer o motivo e mostrar o impacto do Atlas, sem metro (PR #409).
- [ ] Pesquisa web desta sessão (em andamento) — resultados entram em `enchentes.json` e aqui.
- [ ] Respostas de outras IAs: conferir URL e trecho de cada número antes de cadastrar.
