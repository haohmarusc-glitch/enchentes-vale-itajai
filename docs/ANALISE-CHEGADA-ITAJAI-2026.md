# Blumenau × maré × chuva em Itajaí — a série de 2026 cruzada (03/10/2026)

Pedido do Jefferson (03/10/2026): *"a lógica de detecção deve cruzar maré, chuva local em Itajaí, juntas,
todos os dados históricos, analisar e simular"*. Também perguntou: *"cada régua de Itajaí tem parâmetros
diferentes para cálculo?"*. **Tem.** A tabela 1 mostra os parâmetros.

- **Dados:** a série que o coletor guardou na VPS (`data/tempo-real/*.ndjson`, 30/08 a 03/10/2026, ~750 h por
  régua), copiada em `series-2026.tar.gz`, mais a tábua da Marinha (`data/mare-itajai.json`).
- **Script:** `scripts/analisar_chegada_itajai.py <pasta>`. É somente leitura e reproduz as tabelas abaixo.
- **Teste:** `scripts/teste_analisar_chegada_itajai.py`.

> **Isto é descritivo, não calibração.** A faixa de chegada do site (14–17 h, JICA) e o `transito.json` **não
> mudam** por causa deste documento. Pela regra de `calibrar_chegada_itajai.py`, só mudam com cinco eventos
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

## 2. Os eventos de 2026: quando a cheia de Blumenau aparece em Itajaí

### Como o atraso foi medido

- Cada régua teve a maré tirada com os seus parâmetros: régua − fator × maré, com o atraso dela, e média de 5 h.
- Na série que sobrou, a crista em Itajaí foi procurada até 36 h depois do pico de Blumenau, e nunca dentro da
  subida do evento seguinte.
- O atraso conta a partir do **meio do platô** de Blumenau. É o mesmo critério do site
  (`web/src/logica/picoBlumenau.ts`: a menos de 5 cm do máximo).

### Tabela 2 — eventos

| pico em Blumenau (AlertaBlu) | nível | platô | chuva em Itajaí, 24 h antes | crista DC-11 sem maré | crista Ilhota sem maré |
|---|---|---|---|---|---|
| 01/09 09h | 7,57 m | 08h–12h | 20 mm | **+2,0 h** | sem série |
| 12/09 05h | 7,86 m | 04h–07h | 35 mm | **+1,5 h** | +3,5 h |
| 20/09 21h | 4,29 m | 20h–00h | — | não achada | não achada |
| 22/09 12h | 6,62 m | 11h–13h | — | **+5,0 h** | +6,0 h |
| 01/10 20h | 4,53 m | 16h–22h | — | **+3,0 h** | +3,0 h |

Notas da tabela:

- **20/09:** a crista não foi achada porque a régua sobe até a cheia de 22/09.
- **10/09 (4,26 m às 18h):** ficou fora, porque o rio não desceu antes de subir de novo até 12/09. Na leitura à
  mão, a crista sem maré veio entre +0,5 e +1,5 h, mas sem separação limpa do evento seguinte.
- **Chuva:** as estações de chuva de Itajaí (DC-00 a DC-11) só vão até 19/09 nesta série. Por isso aparece "—"
  depois disso.

### O que os eventos dizem

1. **Nestes eventos, a água sobe em Itajaí quase junto com Blumenau, não 14–17 h depois.** O atraso da crista
   sem maré ficou entre +1,5 e +5 h nos quatro eventos medidos. A correlação cruzada de Blumenau com a DC-11
   sem maré dá o mesmo: o melhor atraso fica entre 0 e 4 h, com r de 0,93 a 0,99.
2. **Isso não desmente os 14–17 h.** Quatro hipóteses, não conferidas:
   - **Chuva no baixo vale:** a mesma chuva cai em Blumenau, Gaspar, Ilhota e Itajaí, e o rio sobe em toda
     parte ao mesmo tempo. Em 01/09 e 12/09 choveu 20–35 mm em Itajaí nas 24 h antes.
   - **Maré meteorológica:** vento sul e ressaca levantam o nível no estuário por horas. A tábua astronômica não
     a enxerga, e ela fica no "sem maré". Na DC-01, a crista que sobra varia de +4 a +21 h, sem padrão. É a
     assinatura dela.
   - **A régua da cheia grande ainda não passou por esta série.** Os 14–17 h são da onda de cheia grande (JICA,
     2011), em que o volume de cima domina. Num evento de 7–8 m em Blumenau, o que se vê em Itajaí pode ser mais
     a chuva local e a maré do que a onda que desce.
   - **Cheias de Blumenau seguidas** (10→12/09, 20→22/09) se somam, e a crista de Itajaí fica entre as duas.
3. **A maré astronômica é a maior parte do sobe-e-desce das réguas do estuário.** Ela é previsível pela tábua.
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

## 6. O que isto muda no site, e o que não muda

- **Não muda:** a faixa de chegada (14–17 h, JICA), o `transito.json` e o `historico-chegada-itajai.json` (só
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
