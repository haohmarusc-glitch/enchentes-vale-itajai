# Blumenau × maré × chuva em Itajaí — a série de 2026 cruzada (03/10/2026)

Pedido do Jefferson (03/10/2026): *"a lógica de detecção deve cruzar maré, chuva local em Itajaí, juntas,
todos os dados históricos, analisar e simular"*. Também perguntou: *"cada régua de Itajaí tem parâmetros
diferentes para cálculo?"*. **Tem.** A tabela 1 mostra os parâmetros.

- **Dados:** a série que o coletor guardou na VPS (`data/tempo-real/*.ndjson`, 30/08 a 03/10/2026, ~750 h por
  régua), copiada em `series-2026.tar.gz`, mais a tábua da Marinha (`data/mare-itajai.json`).
- **Script:** `scripts/analisar_chegada_itajai.py <pasta>`. É somente leitura e reproduz as tabelas abaixo.
- **Teste:** `scripts/teste_analisar_chegada_itajai.py`.

> **Isto é descritivo, não calibração.** A faixa de chegada do site (JICA) e o `transito.json` **não
> mudam** por causa destes eventos. (Em 03/10/2026 a faixa passou de 14–17 h para 12–17 h, mas pela Tabela 7.5.1 da
> JICA inteira, não por esta análise.) Pela regra de `calibrar_chegada_itajai.py`, só mudam com cinco eventos
> conferidos e decisão do Jefferson. Os eventos daqui são moderados (4–8 m em Blumenau). Nenhum chegou perto de
> 2008, 2011 ou 2023.

## 1. Cada régua de Itajaí sente a maré do seu jeito

### Como cada régua foi medida

1. A régua tem duas partes: o **rio**, que muda devagar, e a **maré**, que sobe e desce duas vezes por dia.
2. A parte rápida da régua é a régua menos a média móvel de 25 h. A parte rápida da tábua da Marinha sai da
   mesma conta. A primeira foi comparada com a segunda, com atrasos de 0 a 5 h.
3. Cada régua sai com três números:
   - **correlação:** quanto da oscilação é maré;
   - **atraso:** quantas horas depois da tábua a maré chega à régua;
   - **fator:** quanto de 1 m de maré na tábua aparece na régua.

### Tabela 1 — maré em cada régua

| régua | onde | correlação | atraso | fator | a maré, nesta régua |
|---|---|---|---|---|---|
| **DC-01** | Açu — ICMBio/CEPSUL (foz) | 0,93 | 0 h | **0,90** | quase inteira |
| **DC-04** | Mirim — Vitalmar | 0,95 | 0 h | 0,81 | forte |
| **DC-03** | Mirim — Captação SEMASA | 0,91 | 0 h | 0,78 | forte |
| **DC-06** | Mirim — Itamirim | 0,95 | 1 h | 0,77 | forte, 1 h depois |
| **DC-11** | Açu — Santa Regina (Volta de Cima) | 0,91 | 1 h | 0,70 | forte, 1 h depois |
| **DC-09** | Rib. da Murta — Ponte R. Lidia Puel Peixer | 0,90 | 1 h | 0,65 | forte, 1 h depois |
| Ilhota (DCSC-00030) | Açu, a montante de Itajaí | 0,80 | 1 h | 0,57 | ainda grande |
| DC-02 | Açu — Praça Celso Pereira | 0,24 | 2 h | 0,07 | quase nada |
| DC-05 | Mirim curso antigo — propriedade privada | 0,16 | — | 0,04 | não sente |
| DC-07 | Rib. da Murta — Portal | 0,03 | — | 0,01 | não sente |
| DC-08 | Rib. Canhanduba | −0,02 | — | 0 | não sente |
| DC-10 | Mirim — Limoeiro | 0,00 | — | 0 | não sente |

### O que a tabela diz

- **Não existe um "número de maré" único para Itajaí.**
  - Na DC-01, uma preamar de 1,2 m na tábua move a régua ~1,1 m.
  - Na DC-11, a mesma preamar move a régua ~0,8 m, e uma hora depois.
  - Na DC-10, a régua não se move.
  - Qualquer conta que use a maré tem de usar o atraso e o fator **da régua**.
- **Os números batem com a medição de 05/09/2026** (`docs/MEDICAO-MARE-2026-09-05.md`, 6 dias, pela componente
  M2):
  - DC-01, DC-03, DC-04 e DC-06 são maré.
  - DC-02, DC-05, DC-07 e DC-08 não são.
  - A DC-09, que lá ficou "por 3 pontos", aqui, com cinco semanas, aparece claramente com maré.
  - A DC-11 não estava naquela medição.
- **A DC-02 é a exceção do Açu.** Fica no centro, entre a DC-01 e a DC-11, que sentem forte, e quase não sente a
  maré. A régua pode estar num remanso ou ter outra instalação. Isso não está resolvido.
- **Ilhota ainda sente 57% da maré.** A maré entra rio acima além de Itajaí.

## 2. Os eventos de 2026: crista local sem maré astronômica, contada do platô de Blumenau

> **Leia antes da tabela (correção de 03/10/2026, pergunta do Jefferson: "Itajaí fica a quantos km de
> Blumenau? Esses dados estão corretos?").**
>
> - **Distância:** Blumenau fica a **~70 km da foz pelo rio** (`estacoes.json`, `km_da_foz`). A DC-11 está entre
>   Ilhota e o centro de Itajaí. Ilhota fica a 33 km da foz (`transito.json`).
> - **Referência de propagação:** a Tabela 7.5.1 da JICA (Vol. III-A, p. A-80, lida no original — ver
>   `docs/JICA-2011-VERIFICADO.md`) dá, entre os picos de vazão em Blumenau e em Itajaí, **17 / 15 / 14 / 12 h**
>   para as cheias de projeto de 5 / 10 / 25 / 50 anos. O texto do Vol. II resume como "14–17 h", mas a tabela
>   inteira vai de **12 a 17 h**. São intervalos entre picos de hidrogramas CALCULADOS, não o tempo de viagem
>   de uma mesma parcela de água.
> - **O que a tabela abaixo mede:** a diferença entre o meio do platô de Blumenau e uma crista LOCAL da régua de
>   Itajaí, com a maré astronômica tirada só em parte. **Não é o tempo de chegada da água de Blumenau** e não
>   acompanha a mesma onda passando por Blumenau, Gaspar, Ilhota e Itajaí. As horas estão medidas certo; o
>   rótulo antigo ("a cheia de Blumenau aparece em Itajaí") estava errado.
> - *Correção de 03/10/2026, revisão externa reproduzida com a série completa:* uma versão anterior deste
>   documento dizia que a água leva "~13–20 h, na velocidade habitual de 1 a 1,5 m/s". A conta fecha, mas a
>   velocidade não tinha fonte técnica, e saiu. A referência que fica é a da JICA.
> - **O que a tabela mostra:** o baixo vale **sobe junto** com Blumenau. Isso vem da mesma chuva, dos ribeirões
>   próximos e da maré meteorológica. Pode vir também do represamento: no trecho de maré, uma mudança de nível
>   corre muito mais rápido que a onda de cheia — a própria maré chega a Ilhota em 1 h.
> - **O provável sinal da água de Blumenau:** um "ombro". Entre **+12 e +18 h**, a DC-11 sem maré para de descer
>   (12/09: 3,82–3,85 m; 22/09: 3,52–3,54 m), enquanto Blumenau já caiu 0,3 a 1 m. Isso é compatível com a onda
>   de cima chegando, mas não está provado.

### Como a diferença foi medida

- Cada régua teve a maré tirada com os seus parâmetros: régua − fator × maré, com o atraso dela, e média de 5 h.
- Na série que sobrou, a crista em Itajaí foi procurada até 36 h depois do pico de Blumenau, e nunca dentro da
  subida do evento seguinte.
- A diferença conta a partir do **meio do platô** de Blumenau. É o mesmo critério do site
  (`web/src/logica/picoBlumenau.ts`: a menos de 5 cm do máximo).
- A crista só pode cair numa hora **com leitura bruta**. A média móvel preenche buracos, e um máximo dentro de um
  buraco não é crista.
- Se a janela tem **2 h seguidas ou mais sem leitura**, a crista sai como "primeira crista detectada", com
  horário indeterminado: a de verdade pode ter caído na lacuna.

### Tabela 2 — eventos

| pico em Blumenau (AlertaBlu) | nível | platô | chuva em Itajaí, 24 h antes | crista local DC-11 sem maré | crista local Ilhota sem maré |
|---|---|---|---|---|---|
| 01/09 09h | 7,57 m | 08h–12h | 20 mm | primeira crista detectada em +2,0 h; **horário indeterminado por lacuna** | sem série |
| 12/09 05h | 7,86 m | 04h–07h | 35 mm | primeira crista detectada em +0,5 h (06h); **horário indeterminado por lacuna** | **+3,5 h** (série completa) |
| 20/09 21h | 4,29 m | 20h–00h | — | não achada | não achada |
| 22/09 12h | 6,62 m | 11h–13h | — | **+5,0 h** | +6,0 h |
| 01/10 20h | 4,53 m | 16h–22h | — | **+3,0 h** | +3,0 h |

Notas da tabela:

- **12/09, DC-11:** não há leitura às 07h nem das 09h às 14h. A versão anterior dava +1,5 h, mas esse máximo
  caía às 07h, hora sem leitura, e vinha da suavização. Agora a crista só cai em hora com leitura: 06h (+0,5 h),
  a última antes do buraco. Uma crista mais alta pode ter ocorrido dentro da lacuna. **O valor mais confiável do
  evento é o de Ilhota, +3,5 h**, com a série completa no intervalo.
- **01/09, DC-11:** também tem lacuna de 2 h ou mais na janela, por isso o mesmo rótulo.
- **20/09:** a crista não foi achada porque a régua sobe até a cheia de 22/09.
- **10/09 (4,26 m às 18h):** ficou fora, porque o rio não desceu antes de subir de novo até 12/09. Na leitura à
  mão, a crista sem maré veio entre +0,5 e +1,5 h, mas sem separação limpa do evento seguinte.
- **Chuva:** as estações de chuva de Itajaí (DC-00 a DC-11) só vão até 19/09 nesta série. Por isso aparece "—"
  depois disso.

### O que os eventos dizem

1. **Nestes eventos, Itajaí sobe quase junto com Blumenau.** As cristas locais sem maré ficaram de **~2 a 6 h**
   depois do platô de Blumenau, contando as de série completa (22/09 e 01/10 nas duas réguas, 12/09 em Ilhota). A correlação cruzada de Blumenau com a DC-11 sem maré dá o mesmo: o
   melhor atraso fica entre 0 e 4 h, com r de 0,93 a 0,99. Pela distância (~70 km), **não é a água de Blumenau**.
   É o baixo vale reagindo ao mesmo tempo.
2. **A crista de 12/09 na DC-11 está num buraco da série** (ver as notas da tabela). Ilhota, com a série completa,
   marca +3,5 h. Em 01/09 só há a DC-11, também com lacuna: Ilhota ainda não era coletada.
3. **Isso não desmente os 12–17 h da JICA.** Quatro explicações para a subida simultânea, não conferidas:
   - **Chuva no baixo vale:** a mesma chuva cai em Blumenau, Gaspar, Ilhota e Itajaí, e o rio sobe em toda
     parte ao mesmo tempo. Em 01/09 e 12/09 choveu 20–35 mm em Itajaí nas 24 h antes.
   - **Maré meteorológica:** vento sul e ressaca levantam o nível no estuário por horas. A tábua astronômica não
     a enxerga, e ela fica no "sem maré". Na DC-01, a crista que sobra varia de +4 a +21 h, sem padrão. É a
     assinatura dela.
   - **A régua da cheia grande ainda não passou por esta série.** Os 12–17 h são de cheias de projeto de 5 a 50 anos
     (JICA, 2011), em que o volume de cima domina. Num evento de 7–8 m em Blumenau, o que se vê em Itajaí pode ser mais
     a chuva local e a maré do que a onda que desce.
   - **Cheias de Blumenau seguidas** (10→12/09, 20→22/09) se somam, e a crista de Itajaí fica entre as duas.
4. **A maré astronômica é a maior parte do sobe-e-desce das réguas do estuário.** Ela é previsível pela tábua.
   O que ela não explica é o rio, a chuva e a maré meteorológica.

## 3. A publicação "Blumenau" da página de Itajaí estava 3 h atrasada

### O que se viu

- Blumenau chegava por duas publicações da mesma régua: **"Blumenau (AlertaBlu)"** e **"Blumenau"**, lida na
  página da Defesa Civil de Itajaí.
- Na mesma coleta das ~15h10 de 01/09/2026:

  | publicação | `medido_em` |
  |---|---|
  | réguas de Itajaí | 15h00 |
  | Brusque | 15h05 |
  | AlertaBlu | 15h00 |
  | **"Blumenau" (página de Itajaí)** | **12h05** |

- Conferido ao vivo: coleta às 15h16 de Brasília, AlertaBlu em 15h00.

### Conclusão e consequências

- **A publicação da página de Itajaí carimbava 3 h antes da hora certa.** A do AlertaBlu está certa.
- A publicação "Blumenau" saiu do ar depois de 19/09/2026.
- O site já usava a publicação mais recente, que era sempre a do AlertaBlu.
- O gabarito de `picoBlumenau.test.ts` passou a usar só o AlertaBlu: pico de 7,86 m às 05h de 12/09, platô das
  04h às 07h.
- Este script usa a publicação da página de Itajaí só onde falta o AlertaBlu, somando 3 h.
- **Se essa publicação voltar, o coletor tem de corrigir o fuso antes de gravar.**

## 4. Limites

- **Cinco semanas, só eventos moderados.**
  - Nenhum evento chegou à cota de inundação de Itajaí.
  - Os parâmetros de maré foram medidos com o rio baixo e médio. Numa cheia grande, a maré pesa menos na
    régua, porque o rio "empurra", e o fator provavelmente cai.
- **A maré meteorológica não tem fonte na série.** O `coleta_mare_ciram.py` existe, mas a série dele não estava
  no pacote.
- **Mirim:** as réguas do Mirim estão na tabela 1, mas o cruzamento com Brusque não foi feito. A série de Brusque
  vai só até 19/09.
- **Tábua:** só 2026 (`mare-itajai.json`). Eventos antigos não têm maré astronômica nesta conta.
- **Pares históricos:** a busca externa de 03/10 não achou nenhum par completo de hora de pico Blumenau ×
  Itajaí. Os horários de Blumenau de 2011, 2013, 2015 e 2023 existem, mas não os de Itajaí.

## 5. Terreno e escape da maré — observação do Jefferson (03/10/2026)

> *"O que influencia muito é o nível do terreno perto do rio em relação ao nível do mar. E partes do rio com
> escape de maré também mudam muito: partes sem escape de maré represam mais o rio."*

### O que a tabela 1 já mostra nessa direção

- **Mirim, canal retificado:** as réguas DC-03 e DC-04 sentem 78–81% da maré. O canal leva direto ao estuário,
  e a maré entra e sai por ele.
- **Mirim, curso antigo, DC-05:** a régua quase não sente a maré (fator 0,04). Ainda assim, varia 1,5 m na
  série. É água que fica, não água que oscila. É o comportamento de um trecho represado.
- **Exceção, DC-06:** está no mesmo curso antigo e sente 77%. A diferença entre a DC-05 e a DC-06 precisa da
  geometria de cada trecho (ligação, comportas, largura) para ser explicada. Os números sozinhos não explicam.
- **Açu, DC-02:** sente quase nada, entre duas réguas que sentem forte. Também pede a geometria do lugar.

### O que falta para medir isso

Hoje não dá para medir, porque nada está na mesma referência:

1. **Zero de cada régua em altitude (IBGE).**
   - Cada régua tem o seu zero.
   - O `estacoes.json` não tem a altitude do zero das réguas DC-01 a DC-11.
2. **Altura do terreno junto a cada régua.**
   - Fonte: o MDT de 1 m da SDS (`docs/MDT-SC-E-CARTA-ENCHENTE.md`), que dá a altitude da margem e da rua mais
     baixa perto da régua.
3. **Tábua de maré na mesma referência.**
   - A tábua está no Nível de Redução da carta 1841, não no IBGE.
   - Converter exige o deslocamento NR → IBGE do porto de Itajaí, com fonte. Não se inventa.

### O que se pode fazer com isso

- **Por régua:** com as três coisas acima, sai "a preamar de hoje + o rio de agora chegam a X cm da margem
  aqui". Esse número vale para a régua, não para a cidade inteira.
- **Represamento:** pode ser medido nos dados de hoje.
  1. Comparar o fator de maré de cada régua com o rio baixo e com o rio alto.
  2. Nos trechos com escape, o fator deve cair na cheia, porque o rio empurra a maré.
  3. Nos trechos sem escape, o nível deve ficar alto por mais tempo depois que Blumenau desce.
- **Limite:** a série atual tem poucas horas de rio alto, e essa comparação ainda é fraca. Melhora a cada
  cheia que o coletor guarda.

## 6. Altitude do zero das réguas — estimada pela maré e cruzada com o terreno (03/10/2026)

Pedido do Jefferson: *"busca a altitude do zero das réguas e cruza com o terreno"*.

### O que se mede, e o que não se mede

- **Não é a altitude oficial do zero.** O número oficial só vem de levantamento a partir de uma RN do IBGE,
  publicado por quem instalou a régua. A busca por ele está mais abaixo.
- **O que se mede é a leitura de cada régua quando a água ali está no nível médio do mar.**
  - Vale só para as réguas que sentem a maré (correlação ≥ 0,8).
  - Conta: com o rio baixo (Blumenau < 3,5 m), régua = c0 + c1 · maré + c2 · Blumenau.
  - Avaliada com a maré em 0,60 m sobre o NR, que é o "nível médio" da tábua da Marinha, e Blumenau em 2,5 m.
- **A diferença "cota − essa leitura" é um LIMITE INFERIOR da altura da cota acima do nível médio do mar.**
  - Motivo: com o rio baixo a água ainda fica um pouco acima do mar, porque o rio empilha água para escoar.
  - Esse empilhamento é quase nada perto da foz. Na DC-11, que fica rio acima, entre Ilhota e o centro, pode chegar a dezenas de cm.
- **Terreno:** os 5.237 pontos cotados do ArcGIS de Itajaí (`data/brutos/itajai-pontos-cotados-altimetricos.geojson.json`),
  num raio de 300 m de cada régua.
  - O datum vertical deles não é declarado. Se for o do IBGE, fica perto do nível médio do mar, com
    incerteza de ±0,3 m.
  - Pontos de ~0,6 m junto ao rio parecem ser a lâmina d'água no dia do levantamento, não a margem.
- **Script:** `scripts/estimar_zero_reguas_itajai.py <pasta>`. **Teste:** `teste_estimar_zero_reguas_itajai.py`.

### Tabela 3 — régua, nível médio do mar e terreno

| régua | leitura com a água no nível médio do mar | emergência (Tabela 11, PLANCON v17) | emergência acima do mar (no mínimo) | terreno ≤ 300 m: mín · p25 · mediana |
|---|---|---|---|---|
| DC-01 (foz, CEPSUL) | 1,03 m | 1,56 m | **+0,53 m** | 0,60 · 1,79 · 1,92 |
| DC-03 (Mirim canal, SEMASA) | 0,37 m | 2,50 m | +2,13 m | 1,20 · 2,77 · 4,20 |
| DC-04 (Mirim, Vitalmar) | 1,15 m | 2,25 m | +1,10 m | 0,60 · 2,58 · 5,03 |
| DC-06 (Mirim antigo, Itamirim) | 0,58 m | 2,55 m | **+1,97 m** | 0,56 · 0,62 · 1,81 |
| DC-09 (Rib. da Murta, ponte) | 0,90 m | 1,52 m | **+0,62 m** | 0,92 · 1,14 · 2,07 |
| DC-11 (Santa Regina) | 2,47 m | 5,00 m | +2,53 m (pode ser mais) | 2,69 · 3,84 · 3,88 |
| DC-02, DC-05, DC-07, DC-08, DC-10 | não estimável: a régua não sente a maré | — | — | — |

### O que a tabela 3 diz

- **DC-01:** a cota de emergência fica só ~0,5 m acima do nível médio do mar.
  - A maior preamar da tábua de 2026 é 1,23 m no NR, ou 0,63 m acima do nível médio. Com o fator 0,90, ela
    sobe a régua ~0,57 m: chega ao limite da emergência só com a maré astronômica.
  - Com um pouco de maré meteorológica, passa. Por isso a DC-01 cruza as cotas sem enchente: cruzou 26 vezes em
    5 dias (`MEDICAO-MARE-2026-09-05.md`).
  - O terreno perto dela está em ~1,8–1,9 m. A emergência fica ~1,3 m abaixo do chão ao lado.
  - A cota não marca "água na rua" ali. A trava do aviso automático nessa régua continua certa.
- **DC-09 (Ribeirão da Murta):** o caso se parece com o da DC-01. A emergência fica ~0,6 m acima do mar e o
  terreno em volta, em 1,1–2,1 m.
- **DC-06 (Itamirim, curso antigo):** a emergência (~2,0 m acima do mar) **passa da mediana do terreno**
  (1,8 m). Na emergência dessa régua, a água já está no nível do chão em volta. É o trecho mais baixo dos
  medidos. Isso combina com a sua observação: o curso antigo, com pouca saída, é onde o rio represa sobre
  terreno baixo.
- **DC-03, DC-04 e DC-11:** a emergência fica de 0,6 a 1,5 m abaixo do terreno típico em volta.
  - Lembrete: o terreno a 300 m não é a rua mais baixa do bairro.
- **O mesmo número de régua quer dizer coisas diferentes em cada ponto.**
  - Exemplo: 1,5 m na DC-01 é ~0,5 m acima do mar; 1,5 m na DC-03 é ~1,1 m acima do mar.
  - Por isso o site nunca soma, compara nem faz média de réguas de Itajaí.

### Busca da altitude oficial (03/10/2026)

**A altitude do zero não foi achada para nenhuma régua**: nem DC-01 a DC-11, nem DCSC-00030 (Ilhota).

A rede deste ambiente bloqueou os originais: o PLANCON v17, a JICA, a Marinha e o IBGE. Os números abaixo vêm
de **trechos devolvidos pela busca**, não de documento aberto, e **nenhum entra em `data/`** antes de alguém
abrir o original.

| achado | valor | fonte | confiança |
|---|---|---|---|
| Conversão da maré da Marinha para o IBGE na foz | **IBGE = DHN − 0,463 m** (maré dos Práticos, ~1 km da foz, nov/2009–mai/2010) | JICA 2011, Anexo B (`openjicareport.jica.go.jp/pdf/12043618_02.pdf`) | média: a mesma fórmula voltou em 4 buscas; não está no repositório |
| Maré alta de projeto na foz | 1,49 m IBGE (média das máximas mensais) | JICA 2011, Anexo B | média |
| Ficha F-41 da estação 60235 (Capitania dos Portos, Itajaí) | NR = zero do marégrafo + 189,6 cm; nível médio = NR + 59,4 cm | Marinha, F-41 60235 v1/2012 | média-alta: os três números fecham entre si, e os 59,4 cm batem com o "Nível Médio 0,6 m" da tábua |
| ANA, campo "altitude" das estações de Ilhota/Itajaí | 0,0 ou vazio | `data/brutos/ana-inventario-api-2026-09-08.json` | o campo é marcador; não é o zero |

**Conta minha, não publicada:** nível médio do mar no porto ≈ 0,594 − 0,463 ≈ **+0,13 m IBGE**.

- Só vale se o NR da JICA (2009–10) for o mesmo da F-41 (2010–11). Nada confirma isso.
- Se valer, os pontos cotados do ArcGIS, se estiverem no IBGE, ficam uns 13 cm acima do "nível médio do mar" da
  tabela 3.

### O que fecharia a conta

1. **A altitude oficial do zero de cada régua, ou da RN dela.** Sem ofício ao município (regra do projeto).
   Serve documento público já existente: plano, edital ou relatório de instalação.
2. **O datum dos pontos cotados do ArcGIS.**
3. **A ligação entre o NR da tábua e o IBGE no porto de Itajaí** (ficha da estação maregráfica da DHN).
4. **Maré observada em Itajaí**, para tirar a maré meteorológica da conta. O CIRAM não publica a observada de
   Itajaí; a de Balneário Camboriú existe.
5. **O MDT de 1 m da SDS**, para achar a rua mais baixa junto a cada régua, e não só os pontos cotados.

## 7. O que isto muda no site, e o que não muda

- **Faixa de referência:** Blumenau → Itajaí passou de 14–17 h para **12–17 h** (envelope da Tabela 7.5.1 da JICA, 03/10/2026); não vem destes eventos. **Não muda por estes eventos:** o `transito.json` e o `historico-chegada-itajai.json` (só
  ganhou a nota da fonte).
- **Proposta, a decidir pelo Jefferson:** o painel "Hoje" do `/itajai` cruzar quatro coisas, cada uma com o seu
  rótulo:
  1. o pico de Blumenau de hoje, que já faz;
  2. a próxima preamar da tábua;
  3. a chuva das últimas horas em Itajaí;
  4. a régua de Itajaí **com a maré tirada pelos parâmetros dela** (tabela 1), para mostrar "quanto do nível de
     agora é maré e quanto é rio".

  A quarta só para as réguas com correlação ≥ 0,8 (DC-01, DC-03, DC-04, DC-06, DC-09, DC-11). Nas outras, a
  maré não explica o que se vê, e a tela não pode fingir que explica.
