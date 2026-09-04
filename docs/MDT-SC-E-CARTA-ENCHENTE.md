# O MDT de Santa Catarina existe — e o método da "parte C" já foi validado no Vale

Descoberto em 04/09/2026. Muda a avaliação anterior de "sem precedente".

> **Conferido contra este repositório em 04/09/2026:** Timbó 2011 = 9,86 m ✅ e Blumenau 2011 com
> 13,00 m do CEOPS guardado em `divergencias` ✅ (adotado 12,80 m da série municipal) — os dois
> registros já estão em `data/enchentes.json`, e o artigo já está citado em `docs/fontes-academicas.md`.
> O que **não** estava no repositório, e é o que este documento acrescenta, é (1) o MDT de 1 m da SDS,
> (2) os números de acurácia das manchas e (3) a frase dos autores sobre linearização.

---

## 1. Santa Catarina tem MDT de 1 metro, público e gratuito

**Levantamento Aerofotogramétrico do Estado de SC** (SDS, executado pela Engemap, 2010–2012, concluído
em jan/2013). Cobriu os **97.037 km²** do estado. Produtos, todos em GEOTIFF:

| Produto | Resolução |
|---|---|
| **MDT — Modelo Digital de Terreno** | **1,0 m** |
| MDS — Modelo Digital de Superfície | 1,0 m |
| Ortofotos RGB e infravermelho | 0,39 m |
| Restituição da hidrografia | escala 1:10.000, **ottocodificada** |

**Download público:** `sigsc.sc.gov.br/download/`

Dois detalhes que importam:
- **O Vale do Itajaí foi PRIORIDADE no plano de voo** — a SDS setorizou o levantamento e as "regiões
  atingidas pelos desastres e deslizamentos no Vale do Itajaí e Litoral" vieram primeiro.
- Escala 1:10.000, com detalhamento que "mapeou até canais e valas de drenagem, sendo possível
  identificar qualquer objeto no solo maior que um metro".

⚠️ **É aerofotogrametria, não LiDAR.** Produz MDT de 1 m, mas por estereoscopia de fotos, não por laser.
Sob mata fechada é menos confiável que LiDAR; em área urbana — que é o que importa para rua alagada — a
diferença é pequena. **E é de 2012:** a cidade mudou em 14 anos.

---

## 2. ⭐ O método já foi feito e VALIDADO no Vale — com número de acurácia

**Nicoletti, Luconi, Moser, Refosco & Severo — "Validação de MDT em mapeamento de inundação em duas
cidades do Vale de Itajaí"**, XXII Simpósio Brasileiro de Recursos Hídricos. Autores do **CEOPS/FURB**.
`files.abrhidro.org.br/Eventos/Trabalhos/60/PAP022777.pdf`

Eles geraram carta-enchente de Blumenau e Timbó por dois caminhos — o MDT do CEOPS (curvas de nível das
prefeituras) e o **MDT da SDS** — e mediram a acurácia contra os pontos de cota-enchente levantados em
campo.

### A receita, passo a passo (é a resposta técnica à "parte C")
1. Coleta de **marcas de cheia** em campo com receptor geodésico GNSS
2. Pós-processamento → coordenadas horizontais e **verticais**
3. **Conversão de altitude geométrica para altitude ortométrica, apoiada em modelo geoidal** ← é o passo
   do datum que falta ao projeto
4. Geração da **superfície de inundação**
5. **Cruzamento com o MDT**
6. Edição e validação

### ⭐ Os números de acurácia — o que decide quanto confiar
| Cidade | Nível de referência | Mancha CEOPS | Mancha MDT SDS |
|---|---|---|---|
| **Blumenau** | 13,00 m (evento 09/09/2011) | **OA 89,05 ± 2,9%** · Kappa 78% | **OA 85,12 ± 3,26%** · Kappa 70% |
| **Timbó** | 9,86 m (mesmo evento) | **OA 74,1 ± 6,68%** · Kappa 48% | **OA 71,76 ± 6,9%** · Kappa 43% |

**Leitura honesta destes números:**
- A carta-enchente **oficial do CEOPS**, feita com equipe de campo e GNSS, acerta **89% dos pontos em
  Blumenau**. **Um ponto em cada nove está errado.**
- Em **Timbó cai para 74%** — **um em cada quatro errado** —, e o Kappa de 48% é "concordância moderada".
  Os autores atribuem à qualidade das curvas de nível da prefeitura.
- O MDT da SDS fica **4 pontos percentuais abaixo** do CEOPS em Blumenau (diferença estatisticamente
  significativa, teste Z) e **empata** em Timbó.

**Ou seja: mesmo o produto profissional erra. E erra mais onde a base cartográfica é pior.**

### ⭐⭐ A frase que decide a questão da interpolação
Os autores declaram as tolerâncias que aceitam:
> *"um erro de **20 cm** é aceitável nos pontos levantados para a **carta-enchente**. Para a
> **cota-enchente**, que está ligada em situações de alerta e projeção de nível de rio em situações
> extremas, se aceita um erro máximo de **50 cm**. Isto porque **os eventos de enchentes não tendem a
> linearização**."*

**"Os eventos de enchentes não tendem a linearização"** — é a autoridade local dizendo, com todas as
letras, que interpolar linearmente entre pontos de cheia é errado. Exatamente a objeção à parte C, dita
por quem faz o produto oficial.

### Escala do trabalho de campo (o custo real)
| | Blumenau | Timbó |
|---|---|---|
| Pontos de **cota-enchente** | 1.754 | 641 |
| Pontos de **carta-enchente** (GNSS) | 149 | 80 |
| Equipe cota-enchente | **11 pessoas** | 8 |
| Equipe carta-enchente | 2 | 2 |
| Escritório | 5 | 4 |
| Área inundada mapeada | ~1.566 ha (3% do município) | ~1.142 ha (10%) |

---

## 3. O que isto confirma dos nossos dados
- **Timbó 2011 = 9,86 m** — bate exatamente com o que está em `enchentes.json`. ✅
- **Blumenau 2011 = 13,00 m (CEOPS)** — é o valor da série acadêmica, e reforça a
  `REGRA_REFERENCIA_BLUMENAU`: o CEOPS usa 13,00 e a Defesa Civil registra 12,80 (diferença de 0,20 m =
  o offset IBGE × régua). Duas fontes, duas referências, o mesmo evento.
- **Blumenau: 1.754 pontos de cota-enchente** no levantamento de 2011. O nosso `data/cotas-ruas.json`
  tem **2.042** para Blumenau (contado em 04/09/2026). Números diferentes — o nosso vem do PDF de 2014,
  que pode ter agregado levantamentos. Vale conferir de onde vem a diferença de ~290 pontos.
  ⚠️ Nota de outro artigo do CEOPS já registrado em `fontes-academicas.md`: o levantamento pós-2011 é
  descrito lá como **1.851 pontos**. Três contagens (1.754 / 1.851 / 2.042) para o que parece ser o
  mesmo acervo — não escolher uma; a diferença é a pergunta.
- Confirma a topologia: *"O rio Itajaí-Açú… se forma pela confluência dos rios Itajaí do Oeste e Itajaí
  do Sul, no município de Rio do Sul"* e, em Timbó, *"o rio Benedito… recebe as águas do afluente rio dos
  Cedros no centro da cidade"*.

---

## 4. Como isto muda a resposta sobre a parte C

**Antes:** "não há precedente; não fazer."
**Agora:** há precedente local, validado e publicado — **e ele diz o quanto confiar.**

### O que passa a ser possível
Gerar mancha por nível **usando o MDT de 1 m da SDS**, seguindo a receita do CEOPS. É viável
tecnicamente e o insumo é gratuito.

### O que os números exigem que se diga junto
Uma mancha assim tem **~85% de acurácia em Blumenau** e **~72% em Timbó** — e só onde há base
cartográfica boa. Em cidade sem curva de nível decente, cai mais. **Isso precisa aparecer na tela.**
Não como nota de rodapé: como parte da informação. *"Mancha estimada a partir do modelo de terreno do
Estado — acurácia aferida de ~85% em estudo do CEOPS; um ponto em cada sete pode estar errado."*

### O que continua proibido
**Interpolar linearmente as cotas de rua** para desenhar polígono. Os próprios autores dizem que
"os eventos de enchentes não tendem a linearização". A mancha tem que sair do **cruzamento com o MDT**,
não da interpolação entre pontos.

### A diferença entre as duas coisas
| | Interpolar cotas de rua | Cruzar superfície com MDT |
|---|---|---|
| O que sabe do terreno | nada entre os pontos | altura de cada metro quadrado |
| Acurácia | desconhecida | **medida: 85% / 72%** |
| Precedente | nenhum | CEOPS, publicado |
| Honesto? | não | sim, se o número aparecer |

---

## 5. Próximos passos concretos
1. **Baixar o MDT do Vale** em `sigsc.sc.gov.br/download` — recortar as cidades do Açu e do Mirim.
   Verificar licença de uso (é dado público estadual, mas confirmar os termos).
2. **Pedir ao CEOPS/FURB** as carta-enchentes prontas de Blumenau e Timbó — o produto oficial é melhor
   que qualquer coisa que geremos, e o convênio com as prefeituras existe. Junto com a correlação
   Blumenau↔Gaspar, no mesmo ofício.
3. **Resolver o datum antes de qualquer cruzamento.** O passo 3 da receita — conversão de altitude
   geométrica para ortométrica com modelo geoidal — é exatamente o que falta para cruzar os 5.237 pontos
   cotados de Itajaí com o nível da régua. É também a pergunta nº 10 da reunião da Univali.
4. Só então avaliar gerar mancha própria — e **sempre com a acurácia à vista**.
