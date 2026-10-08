# DC-11 (Santa Regina): manter, restringir ou trocar o aviso automático — proposta

**Situação:** proposta para decisão do Jefferson. **Nada foi aplicado.** O aviso automático da DC-11, o
cadastro e o mapa continuam como estavam. A leitura e a cor da DC-11 no mapa ficam iguais em todas as opções
recomendadas.

Pedido (08/10/2026): conferir a origem dos números de 04/09, o significado da folga de 0,20 m e como o motor
usa a DC-11. A conclusão não podia sair só da oscilação de 0,33 m. A proposta devia mostrar o efeito de
manter, de restringir e da alternativa com a DC-02.

## Resumo

| | |
|---|---|
| **A DC-11 sente a maré?** | Sim. Em 36 dias, a parte rápida da régua acompanha a tábua da Marinha com correlação **0,91**, uma hora depois, com **0,69 m** de régua para cada 1 m da tábua. O "não é maré (40 %)" de 05/09 foi medido dentro de uma cheia e não se repete. |
| **O que é a "folga"** | A distância entre a cota de atenção (3,00 m) e o nível **mediano da janela medida**. Não é uma propriedade da régua. Foi 0,20–0,25 m nas janelas de 04–05/09, ainda na descida da cheia de 01/09, e é **0,30 m** nos 36 dias. |
| **Por que isso pesa** | A maré move a régua cerca de **±0,33 m** em volta do nível de base (p5–p95). Com o nível típico 0,30 m abaixo da cota, quase toda preamar alta encosta na cota. |
| **Quantos avisos a DC-11 mandou** | **112 mensagens em 36 dias** pela regra de hoje: 64 de subida e 48 de "voltou ao normal". Em 12 dias foram mais de 4 mensagens. Das 48 passagens por 3,00 m, **41** aconteceram com o nível de base abaixo da cota, ou seja, foi a preamar que levou a régua até lá. |
| **Mas a maré é água de verdade** | A cota do Plano (Tabela 11) vale para a leitura da régua, com a maré dentro. Numa cheia, a preamar é justamente o momento de risco. Por isso descontar a maré (opção B2) ou desligar o aviso (opção B) não é o caminho recomendado. |
| **DC-02 como alternativa** | Não serve hoje. A série dela fica **parada**: 1,53–1,57 m por duas semanas e exatamente 1,53 m nas últimas 48 h, com 48–62 mm de chuva em Itajaí e a DC-11 subindo de 2,18 para 3,35 m. Antes disso, ficou 0,55–0,70 m por 18 dias e saltou ~1 m em poucas horas. |
| **Recomendação** | **Opção C1 — histerese de 0,30 m na descida, só para a DC-11.** Corta as mensagens de 112 para **52**, sem atrasar nenhum aviso de subida (+0,0 h em todos os episódios). O alerta de 4,00 m sai nas duas cheias na mesma leitura de hoje. A C3 (histerese + 2 h) corta mais (31), mas atrasa o primeiro aviso de 2 a 26 h e o alerta em 2 h: fica como segunda opção, se o volume de C1 ainda incomodar. |

## 1. De onde vêm os números de 04/09

Três medições, com métodos e janelas diferentes, explicam a contradição que o README guardava.

| data | onde está | método | janela | o que deu |
|---|---|---|---|---|
| 04/09/2026 | README, item "A DC-11 (Santa Regina) alarma e pinta" | `medir_mare.py` na VPS + média móvel de 13 h e correlação entre réguas | 6 dias, logo depois da cheia de 01/09 | oscila 0,85 m/dia; folga 0,20 m; 7 travessias em 3 dos 6 dias; parte rápida de 0,33 m pico a pico; correlação +0,92 com a DC-09 e +0,79 com a DC-03 |
| 05/09/2026 | `docs/MEDICAO-MARE-2026-09-05.md`, seção "O que a medição diz sobre as duas que HOJE disparam" | teste de frequência (fração da energia na banda da maré) | 6 dias | "**não é maré** (40 %)", folga 0,25 m, 7 travessias, uma de 45,5 h |
| 03/10/2026 | `docs/ANALISE-CHEGADA-ITAJAI-2026.md`, Tabela 1 | resíduo (régua − média de 25 h) contra a tábua da Marinha | 5 semanas | correlação **0,91**, atraso 1 h, fator **0,70** |
| **08/10/2026** | este documento | o mesmo de 03/10, refeito sobre o `arquivo-series` | **36 dias** (30/08 a 05/10, 3.268 leituras) | correlação **0,91**, atraso 1 h, fator **0,69**; resíduo p5–p95 de −0,34 a +0,33 m; amplitude diária mediana **0,83 m** (p90 1,13 m) |

- **Por que 04/09 e 05/09 discordam.** As duas janelas caem na descida da cheia de 01/09 (pico de 4,12 m na
  DC-11). Na descida, a energia da série fica na tendência lenta, e o teste de frequência
  divide pela energia total. A maré perde participação sem ter diminuído. O próprio documento de 05/09 avisa
  que o script "não distingue maré de cheia". A medição de 5 semanas (03/10) e a de hoje (36 dias) tiram a
  tendência antes e comparam com a tábua; as duas dão 0,91.
- **Os 0,33 m de 04/09** são a parte rápida pico a pico com média de 13 h em 6 dias. Com média de 25 h e
  36 dias, a faixa p5–p95 do resíduo é **0,67 m**. A diferença é de janela (6 dias pegam só parte do ciclo de
  sizígia e quadratura) e de filtro. Nenhum dos dois números, sozinho, decide trava.
- **A afirmação do cadastro está desatualizada.** A `nota_cidade` da DC-11 em `estacoes.json` diz que ela é
  "uma das DUAS réguas de Itajaí acima da maré". A medição diz o contrário. O texto não foi mudado aqui: é dado
  do cadastro, e a correção vai junto com a decisão.

## 2. O que é a "folga de 0,20 m"

`medir_mare.py` calcula `folga = cota de atenção − mediana dos níveis da janela`
(`scripts/medir_mare.py`, função `medir`). É uma medida da **janela**, não da régua:

| janela | mediana | folga |
|---|---|---|
| 6 dias depois de 01/09 (04/09) | ~2,80 m | 0,20 m |
| 6 dias (05/09) | ~2,75 m | 0,25 m |
| 36 dias (30/08 a 05/10) | 2,70 m | **0,30 m** |

A leitura ao vivo de 04/09 às 13h41 (2,82 m, 0,18 m abaixo da cota) é um instante, não um nível típico.
O número que importa para a decisão é outro: com o nível de base 0,30 m abaixo da cota e a maré somando até
+0,33 m, **basta a base subir uns centímetros para a preamar cruzar a cota.** Nos 36 dias, o nível de base
(média de 25 h) teve mediana 2,66 m, p90 3,30 m e máximo 3,91 m.

## 3. Como o motor usa a DC-11 hoje

Levantamento no código de 08/10/2026.

| onde | o que faz com a DC-11 | depende de `alerta_automatico`? |
|---|---|---|
| **Aviso automático** (`scripts/alerta_cotas.py`, `cotas_da_leitura` e `decidir`) | Usa as cotas da própria régua (3,00 / 4,00 / 5,00). Manda mensagem **a cada troca de faixa, para cima e para baixo**. Repete a mesma faixa só depois de 3 h **e** 30 cm de subida. Não há persistência nem histerese, e a maré não entra no caminho do aviso. | Sim. Só `false` explícito bloqueia; a DC-11 não tem o campo. |
| **Bot** (`scripts/bot.py`, `faixa_da_regua`) | Diz a faixa da DC-11 ("Acima da cota de Atenção (3,00 m)"). Não faz "faltam X m" com ela: Itajaí tem várias réguas. | Sim (`false` cala a faixa). |
| **Mapa do Monitor** (`MonitorBacia.tsx` → `mapaMotor.ts`, "referência visual da DC-11") | O Açu de Santa Regina até a foz pinta com a faixa da DC-11. Na reprodução, a referência fica desligada. | **Sim, indiretamente.** Com `false`, `reguasNoMapa.ts` dá `faixa: null` e o trecho fica **cinza**, sem voltar à cor de antes. |
| **Selos e textos** (`VariasReguas.tsx`, `ReguasAgora.tsx`, `ReguasDaCidade.tsx`) | Selo "maré"/"sem aviso" e "faltam X para a cota". | O selo, sim. A cor em `/itajai` (`reguasAgora.ts`) não. |
| **Chegada da cheia** (`analisar_chegada_itajai.py`) | Procura a crista da DC-11 sem a maré, só como relatório. O site não usa. A ordem DC-11 → DC-02 → DC-01 é só `ordem_descida`. | Não. |
| **Testes que travam o estado de hoje** | `teste_alerta_cotas.py` (DC-11 dispara), `teste_bot.py` (`{DC-10, DC-11}`, nove de estuário), `teste_conferir_mapa_e_alarme.py`, `rotulosDasReguas.test.ts`, `reguas.test.ts`, `referenciaDc11.test.ts`. | Quebram se a DC-11 ganhar `false`. |

**Consequência para a decisão:** pôr `alerta_automatico: false` na DC-11 cala o aviso **e** apaga a cor do
Açu de Santa Regina até a foz no Monitor. Isso vai contra o pedido de preservar a leitura no mapa. Se a
decisão for calar o aviso, o campo que decide o aviso tem de ser separado do que decide a pintura.

## 4. Simulação das opções nos 36 dias

`python3 scripts/simular_avisos_mare.py --serie <pasta com os AAAA-MM.ndjson>` (série do `arquivo-series`,
30/08 a 05/10). A regra de hoje é a de `alerta_cotas.decidir`, leitura a leitura.

| opção | o que muda | mensagens | voltas ao normal | 1º alerta (4,00) em 01/09 | 1º alerta em 12/09 | atraso do 1º aviso por episódio |
|---|---|---|---|---|---|---|
| **A · manter** | nada | **112** | 48 | 04:30 (4,06) | 02:00 (4,13) | — |
| **B · `alerta_automatico: false`** | cala a DC-11 | 0 | 0 | não avisa | não avisa | não avisa; **o Açu fica cinza no mapa** |
| **B2 · maré descontada** | compara `leitura − 0,69 × maré da tábua` com a cota | 45 | 16 | 08:30 (+4 h) | 04:00 (4,02: passa por 2 cm) | +1,3 a +23,7 h; três episódios sem aviso |
| **C1 · histerese 0,30 m** | a faixa só baixa quando o nível desce 0,30 m abaixo da cota | **52** | 21 | 04:30 (igual) | 02:00 (igual) | **+0,0 h em todos** |
| **C2 · persistência 2 h** | a faixa nova só vale depois de 2 h seguidas nela | 40 | 16 | 06:30 (+2 h) | 04:00 (+2 h) | +2 a +26 h; um episódio sem aviso |
| **C3 · C1 + C2** | as duas | **31** | 11 | 06:30 (+2 h) | 04:00 (+2 h) | +2 a +26 h; um episódio sem aviso |

**Atraso do primeiro aviso, por episódio** (passagens de 3,00 m separadas por 18 h abaixo):

| episódio | máx | base máx (25 h) | C1 | C2 / C3 | B2 |
|---|---|---|---|---|---|
| 30/08 16:20 → 02/09 | 4,12 | 3,91 | +0,0 h | +25,3 h* | +23,7 h* |
| 06/09 → 07/09 | 3,21 | 2,85 | +0,0 h | +2,5 h | +4,8 h |
| 10/09 → 15/09 (cheia de 12/09) | 4,37 | 3,54 | +0,0 h | +13,7 h | +17,5 h |
| 22/09 → 25/09 | 3,96 | 3,64 | +0,0 h | +2,5 h | +1,3 h |
| 26/09 → 28/09 | 3,31 | 2,64 | +0,0 h | +26,0 h | sem aviso |
| 29/09 | 3,18 | 2,61 | +0,0 h | +2,0 h | sem aviso |
| 01/10 → 02/10 | 3,25 | 3,00 | +0,0 h | +11,5 h | +8,2 h |
| 03/10 13:30 | 3,01 | — | +0,0 h | sem aviso | sem aviso |

\* A série começa em 30/08 às 16:00 com a régua já acima de 3,00 m. O atraso desse episódio é artefato do
início da série.

**Leitura dos números:**
- Os atrasos longos de C2/C3 acontecem quando a preamar passou da cota e o nível de base ficou abaixo dela
  (26/09, 01/10, o começo de 10/09). É o efeito pretendido de "esperar a régua se firmar acima da cota". O custo
  é que, numa cheia que começa pela preamar, o primeiro aviso sai horas depois.
- **C1 não tem esse custo.** Ela não mexe na subida: tira as mensagens de "voltou ao normal" na baixa-mar e,
  com elas, a nova "atenção" na preamar seguinte. As 52 que restam são subidas reais de faixa, repetições por
  30 cm e as voltas ao normal depois que o rio desce de fato.
- **B2 é frágil.** Em 12/09 a leitura real chegou a 4,37 m; descontada a maré, passa de 4,00 m por 2 cm. Uma
  diferença de método (o fator, a interpolação da tábua) basta para perder o alerta. Além disso, a cota do
  Plano vale para a régua como ela é lida.

## 5. A DC-02 como alternativa

A DC-02 (Praça Celso Pereira da Silva, `ordem_descida` 2, entre a DC-11 e a DC-01) não sente a maré
(correlação 0,23, fator 0,07). Isso pareceria fazer dela a régua "limpa" do Açu em Itajaí. A série não
sustenta isso:

| período | DC-02 | no mesmo período |
|---|---|---|
| 03/09 a 10/09 | 0,55–0,70 m, variação diária de 1 a 5 cm | a DC-11 oscila ~0,8 m por dia |
| 11/09 | salta de 0,70 para 1,57 m | a cheia de 12/09 chega |
| 14/09 a 21/09 | volta a 0,54–0,75 m e fica | |
| 22/09 | salta de 0,56 para 1,65 m em horas | |
| 23/09 a 05/10 | **1,53–1,57 m por duas semanas**, caindo ~1 cm por dia | a DC-11 passa de 3,00 m em cinco episódios |
| 06/10 a 08/10 (48 h) | **exatamente 1,53 m** em todas as leituras | 48–62 mm de chuva em 48 h nas onze DC; a DC-11 vai de 2,18 a 3,35 m |

Um ponto do rio aberto, entre duas réguas que oscilam 0,8 m por dia, não fica parado ao centímetro por 48 h com
chuva. As explicações possíveis são sensor travado, régua num poço ou bacia fechada (comporta, remanso), ou
leitura repetida pela fonte. **Nenhuma delas está provada.** Nas três cheias da série, a DC-02 passou de 1,60 m
depois da DC-11, não antes (22/09: 14 h depois). Pela regra de hoje, ela mandaria 18 mensagens em 36 dias, e
nenhuma de alerta.

**Proposta para a DC-02:** não usar como substituta nem como confirmação da DC-11 enquanto o comportamento
parado não for explicado. A pergunta é para a COMPDEC de Itajaí, mas a orientação vigente é **não enviar ofício
ao município de Itajaí** (decisão de 14/09/2026). Fica registrada aqui, sem rascunho.

## 6. Recomendação e o que ficaria para aplicar (depois da revisão)

1. **Manter a DC-11 disparando**, sem `alerta_automatico: false`, e sem descontar a maré.
2. **Aplicar a histerese de 0,30 m na descida só à DC-11** (opção C1). Isso pede um campo novo no cadastro,
   por exemplo `aviso_histerese_m: 0.30` na DC-11 (campo novo depende de aprovação), lido por
   `alerta_cotas.decidir`. Quando o nível desce mas fica a menos de 0,30 m abaixo da cota da faixa atual, a
   faixa guardada não baixa. A subida não muda.
3. **O mapa e o bot não mudam:** continuam pintando e dizendo a faixa da leitura de agora. Só a mensagem do
   Telegram ganha a histerese. É a mesma separação que já existe hoje entre a cor (instantânea) e o aviso
   (com repetição de 3 h + 30 cm).
4. **Corrigir a `nota_cidade` da DC-11** (sai "acima da maré"; entra "sente a maré: fator 0,69, 1 h depois;
   dispara aviso com histerese") e escrever `sente_mare: true`. **Isso não muda comportamento:** o campo
   ausente já conta como `true` no site e no bot, o selo "maré" só aparece com `alerta_automatico: false`, e o
   aviso não lê `sente_mare`.
5. **Testes a acrescentar junto:** a DC-11 sobe de faixa na mesma leitura de hoje; não volta ao normal a menos
   de 0,30 m abaixo da cota; uma cheia que passa de 4,00 m manda alerta; e a cor do mapa não muda.
6. **Se 52 mensagens em 36 dias ainda for demais:** a C3 (histerese + 2 h) desce para 31, ao custo de atrasar
   o primeiro aviso em 2 a 26 h. Os números estão na tabela da seção 4.

**Segue em aberto, fora desta proposta:** conferir a cota de 3,00 m da DC-11 contra o terreno (a altitude do
zero não foi achada para nenhuma régua DC; `docs/ANALISE-CHEGADA-ITAJAI-2026.md`, seção 4).

## Como refazer

```bash
# série do coletor: na VPS, data/tempo-real/; aqui, a cópia semanal do branch arquivo-series
git show origin/arquivo-series:tempo-real/2026-09.ndjson > /tmp/serie/2026-09.ndjson   # e os outros meses
python3 scripts/simular_avisos_mare.py --serie /tmp/serie                 # DC-11
python3 scripts/simular_avisos_mare.py --serie /tmp/serie --codigo DC-02
python3 scripts/teste_simular_avisos_mare.py
```
