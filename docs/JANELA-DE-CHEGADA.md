> ## ⚠️ CONFERIDO NO DADO — A PREMISSA DESTE DOC NÃO SE SUSTENTA
> **04/09/2026.** Este documento afirma que "não existe medição de Rio do Sul → Indaial em
> nenhuma fonte do projeto", que "as cidades intermediárias não têm tempo medido" e que o 10 h
> foi copiado do limite superior da faixa de Blumenau. **As três afirmações são contrariadas
> pelo próprio `data/transito.json`.**
>
> Em `_meta.origem_das_faixas.hidrograma_de_projeto` está gravada a Tabela 7.5.1 da JICA, com
> valor para **todas** as cidades do tronco:
> `Rio do Sul +0 · Apiúna +9 · Indaial +10 · Blumenau +10 · Gaspar +12 · Ilhota +17 · Itajaí +27`.
>
> Dois fatos verificados por conta:
> 1. **A tabela sozinha é monotônica.** Não há contradição dentro dela.
> 2. **Os seis trechos gravados batem com a tabela no MÁXIMO**, um a um. O dado atual *é* o
>    hidrograma, com dois trechos alargados **para baixo** pelas faixas que o texto do estudo
>    afirma (Rio do Sul→Blumenau 7–10 h e Blumenau→Itajaí 14–17 h).
>
> Logo, o 10 h de Indaial **não é cópia** do limite de Blumenau: vem da mesma linha da mesma
> tabela que deu o +2 de Gaspar, o +5 de Ilhota e o +10 de Ilhota→Itajaí — que este documento
> mantém sem questionar. A sobreposição é artefato de comparar o **mínimo de uma fonte** com o
> **ponto de outra**, e nem chega a ser contradição: testados todos os pares montante/jusante,
> **não existe um só sem atribuição consistente** (o pior caso é Indaial 10 ≤ Blumenau máx 10 —
> empate, que é exatamente o que a tabela diz).
>
> **Por isso a reestruturação NÃO foi aplicada:** ela substituiria valores de fonte publicada
> (Indaial 10, Gaspar +2, Ilhota +5) por interpolação linear nossa (5,5–7,9 · 11,9–15,9 ·
> 16,0–20,9 h), e o próprio doc admite que a premissa da interpolação — velocidade constante —
> é falsa. Trocar fonte por estimativa no horário que o morador lê é o movimento errado.
> O `SESSAO-2026-09-03-resumo.md` diz a mesma regra: "onde este doc e o `main` divergirem, o
> `main` manda".
>
> **O que É aproveitável, e foi aproveitado:** a ideia do **validador de monotonia**. Ele entrou
> em `scripts/validar_dados.py`, comparando o que de fato é impossível (`min_montante >
> max_jusante`) em vez do início das janelas — assim pega dado contraditório de verdade sem
> alarme falso sobre faixas que apenas se sobrepõem.
>
> **O que decidiria a favor deste doc:** conferir no PDF da JICA se a Tabela 7.5.1 traz mesmo a
> linha de Indaial, ou se ela foi preenchida por inferência numa sessão anterior. Não temos o PDF.
> As seções "Achados de 03/09" (obra de 1986, correlação CEOPS Blumenau↔Gaspar, remanso dos
> ribeirões de Gaspar) **não** foram contestadas e estão no README.

# A janela de chegada da cheia — corrigindo a contradição de Indaial

## O problema
No `main`, `transito.json` tem:
- `rio-do-sul → blumenau` = **7–10 h** (JICA, literatura)
- `rio-do-sul → indaial` = **10 h fixo**

**Indaial fica ACIMA de Blumenau no tronco.** Com esses números, a água chegaria em Blumenau (7 h) três
horas **antes** de Indaial (10 h) — impossível. A tela afirma uma física que o próprio dado refuta.

**De onde veio o 10 h:** é exatamente o limite SUPERIOR da faixa de Blumenau. Foi copiado o número errado
da faixa. Não existe medição de Rio do Sul → Indaial em nenhuma fonte do projeto.

## A causa estrutural (mais importante que o número)
Guardar **tempo por trecho, cada um independente**, permite que dois trechos se contradigam. Nada no
formato impede `t(ponto acima) > t(ponto abaixo)`. O erro não foi de digitação — foi de **modelo de dados**.

## A solução: guardar ÂNCORAS, derivar o resto
Só existem **duas** medições de tempo no tronco (JICA), e elas são cumulativas a partir de Rio do Sul:

| Âncora | Distância acumulada | Tempo medido |
|---|---|---|
| Blumenau | 62,6 km | **7–10 h** |
| Itajaí | 111,2 km | **21–27 h** (7+14 a 10+17) |

As cidades intermediárias **não têm tempo medido**. Derivar por distância acumulada:

| Cidade | km do tronco | Janela |
|---|---|---|
| Rio do Sul | 0 | origem |
| Ascurra | 37,6 | 4,2–6,0 h *(derivado)* |
| **Indaial** | 49,2 | **5,5–7,9 h** *(derivado)* |
| Blumenau | 62,6 | **7–10 h** *(medido, JICA)* |
| Gaspar | 79,6 | 11,9–15,9 h *(derivado)* |
| Ilhota | 93,9 | 16,0–20,9 h *(derivado)* |
| Itajaí | 111,2 | **21–27 h** *(medido, JICA)* |

**Por que isto resolve de vez:** a distância acumulada é monotônica por definição, então as janelas
derivadas dela também são. **A contradição fica impossível de existir** — não depende de ninguém lembrar
a regra. Verificado: a sequência acima é monotônica.

### Ressalvas de honestidade
1. **Interpolação linear assume velocidade constante entre âncoras — e sabemos que é falso.** A onda
   desacelera para jusante (canal alarga, declividade cai, maré freia): Rio do Sul→Blumenau dá
   6,3–9,0 km/h; Blumenau→Itajaí, 2,9–3,5 km/h. Dentro de cada par de âncoras o erro é menor, mas existe.
   As janelas derivadas são **estimativas**, e a tela precisa dizer isso — regra do
   `AVISO-LEGAL-obrigatorio.md`: estimativa nunca vira medição.
2. **Distância em linha reta.** O ideal é a distância ao longo do rio (`km_rio` do
   `medir_distancia_rio.py`), mas ela está incompleta: Blumenau ficou de fora porque a coordenada da
   estação está a 3 km do talvegue. Quando houver `km_rio` até Blumenau, refazer a interpolação com ela —
   a proporção muda pouco (81% contra 78,6%), mas fica mais correta.
3. **A onda não é um objeto que "chega".** A janela descreve quando o efeito costuma aparecer, não um
   horário. Chuva a jusante, maré e barragens mudam tudo — já está dito na tela.

## O que fazer no código
1. **Remover `rio-do-sul → indaial`** e qualquer outro trecho intermediário com tempo inventado.
2. **Reestruturar `transito.json`**: guardar `ancoras` (medidas, com fonte) + `km_acumulado` por cidade.
   Derivar as janelas em runtime. Não guardar tempo por cidade intermediária.
3. **Rotular na UI:** "medido (JICA)" nas duas âncoras; "estimado por distância" nas demais.
4. **Validador** — o que impede a reincidência:

```python
def validar_monotonia_transito(cidades_do_tronco, janela):
    """A janela de chegada deve crescer ao longo do tronco. Falha = dado contraditório."""
    ant_min = ant_max = -1
    for c in cidades_do_tronco:                       # na ordem de _topologia.tronco_sequencia
        jmin, jmax = janela(c)
        if jmin is None: continue
        assert jmin >= ant_min, f"{c}: janela mínima {jmin} h < cidade a montante ({ant_min} h)"
        assert jmax >= ant_max, f"{c}: janela máxima {jmax} h < cidade a montante ({ant_max} h)"
        ant_min, ant_max = jmin, jmax
```
Rodar em `validar_dados.py`. **Com a derivação por distância acumulada, este teste nunca falha** — ele
existe para pegar quem voltar a gravar tempo por trecho à mão.

5. **Mesma regra para o Mirim:** só existe `brusque → itajai` (~6 h, confiança baixa). Vidal Ramos e
   Botuverá não têm tempo. Derivar por distância acumulada a partir dessa única âncora, ou não mostrar
   janela — não inventar.

## Resposta direta à pergunta "o que fazer com a janela de Indaial?"
**Mostrar 5,5–7,9 h, rotulada como estimativa derivada da distância** — nunca como medição. Ou, se a
equipe preferir rigor máximo, não mostrar janela para cidades sem medição e dizer "a cheia passa aqui
antes de Blumenau". As duas são honestas; a primeira é mais útil ao morador, desde que o rótulo esteja lá.

**O que não fazer:** manter um número fixo que contradiz o vizinho de jusante.

---

## Achados de 03/09 que afetam a janela

### 1. A obra de 1986 encurtou o trecho Blumenau→Gaspar
Em **1986**, depois das enchentes de 1983/84, foi feita a **retificação e alargamento do canal** do
Itajaí-Açu na **divisa Blumenau/Gaspar**, para aliviar Blumenau.
Fonte: Santos & Pinheiro, *Transformações Geomorfológicas e Fluviais Decorrentes da Canalização do Rio
Itajaí-Açu na Divisa dos Municípios de Blumenau e Gaspar (SC)*, Rev. Bras. de Geomorfologia, 3(1), 2002.
O estudo documenta alteração da **hidrodinâmica**, não só da morfologia.

**O que isso faz com a janela:**
- Canal retificado escoa **mais rápido** → o tempo Blumenau→Gaspar de hoje é **menor** que o histórico.
- Os tempos do JICA precisam ser datados: se forem de estudo pós-1986, valem; se anteriores, superestimam.
- **A série histórica de Blumenau atravessa essa quebra.** Picos antes e depois de 1986 não têm a mesma
  relação nível↔vazão naquele trecho. Marcar 1986 como divisor em `enchentes.json`, do mesmo modo que a
  obra de Rio do Sul (em licitação) exigirá no futuro.

### 2. Existe correlação oficial Blumenau↔Gaspar (CEOPS/FURB)
O CEOPS publicou estudo estatístico das cheias máximas em Gaspar no qual, para **estender a série de
Gaspar**, usou os picos de **Blumenau através de uma correlação**, e calculou períodos de retorno por
**Gumbel**. Fonte: `ceops.furb.br` → Publicações → Artigos.

**Isso é a previsão a jusante que o projeto tenta construir** — já feita por quem tem a série completa e
com método declarado. **Pedir no ofício à FURB/CEOPS:** o coeficiente da correlação Blumenau→Gaspar e as
cotas por período de retorno em Gaspar. Com ela, o trecho Blumenau→Gaspar deixa de ser interpolação por
distância e passa a ter base estatística publicada.

### 3. Gaspar: previsão é feita pelo Prof. Ademar Cordeiro (FURB)
Os boletins da Defesa Civil de Gaspar citam nominalmente o professor que **desenvolveu as cotas de
enchente do município**, com prognósticos de 4 a 8 h de antecedência ("pode chegar a 7,4 m às 2h",
"pode chegar de 8 a 9 m até a madrugada"). Confirma que a cadeia de previsão para Gaspar existe e é
humana/institucional — não é modelo automático.

### 4. Gaspar tem ribeirões que REPRESAM
Boletim da Defesa Civil: *"o município possui alguns ribeirões que podem represar água"* — e a orientação
a quem tem cota entre 6 e 7 m é **esperar antes de mover móveis**, por causa da água que desce do Alto
Vale somada à chuva local. Efeito de remanso: em Gaspar o nível pode subir por bloqueio de saída dos
ribeirões, não só pela onda do rio principal. A janela de chegada não captura isso.
