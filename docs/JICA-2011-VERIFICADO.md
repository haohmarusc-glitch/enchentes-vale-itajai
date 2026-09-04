# ⛔ CORREÇÃO DE UM ERRO GRAVE MEU (03/09/2026) — LER PRIMEIRO

**Eu acusei um dado de ter sido fabricado. A acusação era falsa.**

Este documento afirmava: *"o Indaial +10 foi fabricado"* e *"não existe Tabela 7.5.1"*.
Auditoria externa contestou; eu fui ao PDF do **Volume III-A** conferir. O sumário diz, textualmente:

> `Table 7.5.1  Largest Discharge Peak Time from each City, by Return Period ...... A-80`

**A Tabela 7.5.1 existe**, com esse nome exato, no Volume III-A (Hydrology), página A-80. Cobre
Ituporanga, Taió, Rio do Sul, Apiúna, Ibirama, Indaial, Timbó, Blumenau, Gaspar, Ilhota, Itajaí e Brusque.

## O que eu errei, e por quê
1. **Li um volume e concluí sobre o relatório inteiro.** Os três números da seção 3.5.4 do Vol. II são o
   **resumo** de uma tabela que está em outro volume. Tratei o resumo como o inventário completo.
2. **Chamei de fabricação o que era dado de outra fonte.** O "Indaial +10 h" é, com toda a probabilidade,
   a célula de 5 anos da 7.5.1. Segundo a auditoria, nessa coluna **Blumenau também é +10 h** — os dois
   picam juntos.
3. **A "contradição física" que eu diagnostiquei não existe dentro de um cenário.** Os 7 h de Blumenau
   são a coluna de 25–50 anos; os 10 h de Indaial são a de 5 anos. **Eu misturei colunas de períodos de
   retorno diferentes e chamei o resultado de impossibilidade física.** No mesmo hidrograma, Indaial e
   Blumenau ficam a 0–1 h um do outro.

**Consequência prática:** eu escrevi "remover qualquer tempo que não seja um dos três". Se isso tivesse
sido executado, apagaria as células de Apiúna, Gaspar, Ilhota e das cabeceiras — dado real de uma tabela
oficial. Uma correção minha teria causado mais perda que o suposto erro que eu apontei.

## O que continua válido da crítica original
A ressalva de **método** sobrevive, e é mais importante que a acusação errada: a 7.5.1 é um **hidrograma
de projeto** (HEC-HMS, chuva de projeto, calendário sintético 06–08/08, comportas modeladas como
totalmente abertas). **Não são tempos de trânsito observados.** Evento real muda com onde choveu, com o
regime das barragens e com a magnitude — a própria tabela mostra o tempo ENCURTANDO na cheia maior
(Itajaí: +27 h em 5 anos → +19 h em 50 anos).

## Regra corrigida
- Usar a 7.5.1 como hidrograma canônico **de projeto**, **uma coluna por vez**.
- **Nunca** empilhar célula de um período de retorno com célula de outro.
- Rotular como "hidrograma de projeto", não como tempo medido.
- Âncora de Itajaí: **+27 / +24 / +21 / +19 h** para 5 / 10 / 25 / 50 anos. O "~1 dia" do Vol. II é a
  coluna de 10 anos.
- Ponderar por declividade **e por vazão** — declividade sozinha não explica a variação entre 5 e 50 anos.

## Pendente de verificação direta
Eu confirmei que a tabela **existe** (sumário do Vol. III-A). **Não consegui ler as células** — a extração
do PDF truncou por volta da página A-50. Os valores da matriz neste documento vêm da auditoria, não da
minha leitura. **Confirmar na página A-80 antes de gravar em `transito.json`.**

---

# Relatório JICA 2011 — lido na fonte, 03/09/2026

Fonte: **Preparatory Survey for the Project on Disaster Prevention and Mitigation Measures for the Itajaí
River Basin — Final Report, Volume II Main Report Part I: Master Plan Study**, Nippon Koei Co. Ltd.,
novembro/2011, para a JICA. PDF: `openjicareport.jica.go.jp/pdf/12043659_02.pdf`

---

## 1. ⚠️ SEÇÃO SUPERADA — ver a correção no topo deste arquivo
### O que o Vol. II diz (correto), mas é apenas o RESUMO da Tabela 7.5.1
**Passagem literal (seção 3.5.4, p. 3-31):**
> *"The difference in flood peak times between Rio do Sul and Blumenau cities is around **7 to 10 hours**,
> and around **14 to 17 hours** between Blumenau and Itajaí cities. The flood propagation time from Rio do
> Sul to Itajai cities is around **one day**."*

O relatório dá **exatamente três números** e nada mais:
| Trecho | JICA |
|---|---|
| Rio do Sul → Blumenau | **7–10 h** ✅ (é o que temos) |
| Blumenau → Itajaí | **14–17 h** ✅ (é o que temos) |
| Rio do Sul → Itajaí (total) | **~1 dia** |

~~"Não há tempo para Indaial..."~~ **ERRADO.** Há — na Tabela 7.5.1 do Vol. III-A, p. A-80. Ver correção no topo.

**Correção adicional na minha própria derivação:** eu usei "Itajaí = 21–27 h" (soma 7+14 a 10+17) como
âncora. O JICA diz **~1 dia (24 h)** — que é o meio da faixa, não a faixa. A âncora de Itajaí deve ser
"~24 h (JICA), faixa derivada 21–27 h".
A Tabela 7.5.1 não está NESTE volume (Vol. II) — está no **Vol. III-A, p. A-80**. O texto da seção 3.5.4 a resume.

## 2. ✅ Topologia confirmada por fonte oficial (seção 3.1)
> *"Both the Itajaí do Oeste and Itajaí do Sul Rivers… **join each other the Itajaí-açu River in Rio do Sul
> city**… and **this meeting point of these rivers is where the Itajaí-açu River starts**. In the middle
> valley, the Itajaí-açu River meets the **Itajaí do Norte River in Ibirama city**, then the **Benedito River
> in Indaial city** and it joins the **Luis Alves River Ilhota city**… and finally the **Itajaí Mirim River
> in Itajaí city**."*

Fecha as confluências: Norte em Ibirama · Benedito em Indaial · Luiz Alves em Ilhota · Mirim em Itajaí.
(O AIBH dizia "entre Ascurra e Indaial, a montante da confluência com o Benedito" — consistente.)

## 3. ⭐ DECLIVIDADE POR TRECHO — explica os tempos de trânsito (Tabela 3.6.2)
| Trecho do Açu | Declividade |
|---|---|
| Itajaí → montante de Blumenau | **1/20.000** (quase plano) |
| Blumenau → montante de Indaial | 1/400 |
| Indaial → confluência com Itajaí do Norte | 1/1.500 |
| Confluência do Norte → jusante de Lontras | **1/85** (muito íngreme) |
| Lontras → Rio do Sul | 1/3.000 |

**Isto explica fisicamente por que a interpolação linear por distância é ruim:** o trecho mais íngreme
(1/85) está no meio, entre a confluência do Norte e Lontras; o mais plano (1/20.000) é justamente o
trecho de baixo, até Blumenau. A onda não viaja a velocidade constante — acelera no meio e arrasta no fim.
**Usar a declividade para ponderar a derivação da janela, em vez de distância pura.**

> *"the riverbed elevation in **Blumenau city is lower than the mean sea level**"* — por isso Blumenau
> alaga tanto: o leito está abaixo do nível do mar.

Largura do canal: 200–300 m da foz até perto de Indaial; **150 m em Blumenau e 200 m em Gaspar**
("slight bottle necks"); ~150 m em Rio do Sul.

## 4. ⭐ CAPACIDADE DE VAZÃO POR CIDADE (Tabelas 3.6.3 e 3.6.4) — dado que faltava
Quanto o canal aguenta antes de transbordar, e a que período de retorno corresponde:
| Cidade / rio | Capacidade (m³/s) | Equivale a |
|---|---|---|
| **Itajaí** (Açu) | 2.000–3.000 | **~5 anos** — prioridade ALTA |
| **Rio do Sul** (Açu) | **1.220** | **~5 anos** — prioridade ALTA |
| Ilhota | 2.500–4.000 | 10–25 anos |
| Gaspar | 5.100–6.000 | 25–50 anos |
| Blumenau | 4.200–6.000 | 25–50 anos |
| Indaial | 5.700 | **>50 anos** — sem necessidade de obra |
| Lontras | 1.000–1.500 | 5–10 anos |
| **Mirim em Itajaí (após a reunião)** | **300** | **<5 anos** |
| Mirim — canal retificado | 500–600 | 25–50 anos |
| Mirim — curso antigo | 200–300 | <5 anos |
| Brusque (Mirim) | 550–700 | 25–50 anos |
| Timbó (Benedito) | 860 | 5–10 anos |
| Ibirama (Itajaí do Norte) | >2.000 | >50 anos |
| **Rio do Sul (Itajaí do Oeste)** | **760** | **<5 anos** |
| Taió (Itajaí do Oeste) | 440 | 5–10 anos |
| **Rio do Sul (Itajaí do Sul)** | **300–500** | **<5 anos** |
| Ituporanga (Itajaí do Sul) | 450 | 30–40 anos |

**Confirma por dado o que o site já mostra por cota:** Rio do Sul e Itajaí são os pontos mais frágeis da
bacia (capacidade de cheia de 5 anos), e **Indaial é o mais robusto** (>50 anos) — o que explica por que
Indaial quase não aparece nos relatos de dano.

## 5. ⭐ A DIVISÃO DO MIRIM: 2/3 no canal, 1/3 no curso antigo
> *"Distribution ratio of the flood discharge… is assumed to be **2/3 to the canal and 1/3 to the old Mirim
> River** based on the respective estimated flow capacity"*

Resposta direta para a topologia ramificada do Mirim. E a ressalva do próprio relatório:
> *"it might be said that the shortcut channel could not solve flooding issues because of some opinions
> that this shortcut channel had **caused an increase of flood discharge in the downstream reaches in
> Itajaí city**"*
O canal retificado pode ter **agravado** a jusante em Itajaí — controvérsia registrada em documento oficial.

## 6. ⭐ AS BARRAGENS: por que a Oeste enche e a Norte não (Tabela 3.2.4)
| | Oeste | Sul | Norte |
|---|---|---|---|
| Área de drenagem | 1.042 km² | 1.273 km² | 2.318 km² |
| Capacidade | 83 Mm³ | 93,5 Mm³ | 357 Mm³ |
| **Chuva equivalente** | **80 mm** | **73 mm** | **154 mm** |
| Ano | 1973 | 1976 | 1992 |
| **Condutos (comportas)** | **7** | 5 | 2 c/ + 5 s/ comporta |

> *"the estimated equivalent rainfalls of the Oeste and Sul Dams are 80 mm and 73 mm, which are almost half
> value of the Norte dam. **Therefore, the reservoirs of these two dams easily become full.** Especially the
> **Oeste Dam has been full of water due to the floods in 2001 and 2010, causing overflowing through
> spillway**, although no overflowing occurred at the Sul Dam."*

**Confirma e explica o regime da Barragem Oeste** que eu havia descoberto pela imprensa: bastam ~80 mm de
chuva sobre a bacia dela para enchê-la. E as **7 comportas** batem com o boletim da Defesa Civil.
Também: contra cheia de 50 anos, o reservatório da Oeste **excede em 0,9 m a crista do vertedouro**.
⚠️ As áreas de drenagem diferem da API estadual (Sul 1.164 e Oeste 851 lá; 1.273 e 1.042 aqui) —
delimitações diferentes. Registrar as duas, não misturar.

## 7. ⭐ CURVA-CHAVE: três pontos H→Q da cheia de 2008
> Blumenau H=11,5 m → Q=4.200 m³/s · Timbó H=8,0 m → Q=710 m³/s · Indaial H=6,0 m → Q=3.100 m³/s

Primeiros pontos de curva-chave que o projeto tem. Permite converter nível em vazão nessas três estações.

## 8. Picos históricos com nível (Tabela 3.3.2) — na referência ANTIGA
Blumenau: 1983-07 = **15,34 m** · 1984-08 = **15,46 m** · 1983-05 = 12,46 · 1991-11 = 12,8 ·
1992-01 = 10,62 · 1997-01 = 9,44 · 2001-10 = 11,02.
**Estes são os valores da série IBGE** (régua + 0,20 m) que estão em `enchentes.json` — o JICA é uma
fonte independente confirmando-os. Reforça a hipótese registrada na `REGRA_REFERENCIA_BLUMENAU`.

Períodos de retorno (Tabela 3.3.3): **1983 = 76 anos · 1984 = 66 anos · 1992 = 33 anos**;
2008 calculado em 5 anos pela chuva média da bacia, mas **reavaliado como 50 anos** pelo dano real
(a chuva de 2008 foi localizada: 575 mm em 4 dias em Blumenau = retorno de 8.400 anos para 4 dias).

## 9. ⚠️ POR QUE A PREVISÃO DE RIO DO SUL NÃO FUNCIONA (seção 4.2.2)
> *"Defesa Civil in Rio do Sul city tries to conduct flood forecasting; however, the present forecasting is
> **not appropriate for practical use**. One of the reasons is that **DEINFRA, the operator of the Oeste dam
> and Sul dams… has not recorded and informed the outflow discharges from the dams to the downstream
> rivers**."*

**É a confirmação institucional do problema das barragens.** Não é limitação de modelo: o operador das
barragens **não informa a vazão de saída**. Sem isso, prever Rio do Sul é impossível — e é exatamente a
lacuna que identifiquei hoje pela imprensa ("estado das comportas").

E sobre o CEOPS:
> *"FURB/CEOPS carries out flood forecasting **only for Blumenau city not for other cities**"*, usando
> apenas **3 das 14 estações** (Blumenau, Apiúna, Timbó); e *"no data has been transmitted from CIRAM to
> FURB/CEOPS"*.

Contexto de 2011 — pode ter mudado. Mas explica por que Gaspar depende de prognóstico manual do
Prof. Ademar Cordeiro e por que não há previsão pública para as demais cidades.

---

## O que fazer com isto
1. **Remover** qualquer tempo de trânsito que não seja um dos três do JICA. Corrigir a âncora de Itajaí
   para "~24 h (JICA)".
2. **Ponderar a janela por declividade**, não só por distância (seção 3).
3. **Gravar as capacidades de vazão** — dizem quanto cada cidade aguenta, e a que retorno corresponde.
4. **Gravar a divisão 2/3–1/3 do Mirim** na topologia dos ramos.
5. **Gravar os 3 pontos de curva-chave** (Blumenau, Timbó, Indaial).
6. **Pedir à DEINFRA a vazão de saída das barragens Oeste e Sul** — é a lacuna que o próprio JICA aponta
   como causa de a previsão de Rio do Sul não funcionar. Novo ofício.
7. Baixar o **Volume III-A (Hydrology)** — `openjicareport.jica.go.jp/pdf/12043584_01.pdf` — que tem as
   séries e a calibração detalhada.
