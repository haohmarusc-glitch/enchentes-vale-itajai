# Travas e histerese das réguas de Itajaí: auditoria com a série — 10/10/2026

**Pedido do Jefferson (10/10/2026):**
1. verificar o motivo das travas da DC-03 e da DC-06 antes de removê-las;
2. validar a histerese da DC-05 e da DC-11 com o histórico (a redução de 112 para 52 mensagens precisa preservar os
   avisos de novas subidas);
3. confirmar se 1,80 m e 1,70 m da DC-08 pertencem à mesma régua e ao mesmo zero;
4. confirmar a cota e a régua de referência da DC-07, para habilitar a Murta.

**Nada foi alterado** no cadastro nem nos avisos. Este documento só mede.

**Correção da lista de decisões.** O PR #520 já foi mesclado em 08/10. Por isso a DC-05 e a DC-08 já estão
destravadas, a DC-05 com histerese de 0,10 m e a DC-08 com 1,70 m provisória, e a DC-11 tem histerese de 0,30 m.
Os itens 1.1 e 1.2 de `DECISOES-PENDENTES-2026-10-08.md` estavam desatualizados, e o item 2 abaixo é uma
**auditoria do que já está ligado**.

**Série:** `arquivo-series`, de 30/08 16:00 a 05/10 15:21 (hora de Brasília), 35 dias completos.
- A chuva de 06–07/10 entrou depois, na cópia de 10/10 14h43 UTC (`8bc5ebe`, até 10/10 11:20): seção 6.
- O aviso é reproduzido leitura a leitura com o mesmo laço de `alerta_cotas.decidir`: `faixa_com_histerese` e
  repetição só depois de 3 h e 30 cm de subida.
- Script: `scripts/auditar_avisos_itajai.py`, testes em `teste_auditar_avisos_itajai.py`.

## 1. DC-03 e DC-06: o motivo da trava não se sustenta na série

O motivo cadastrado é o texto comum às réguas de estuário: *"oscilação de maré maior que a distância até a cota.
Em 30/08/2026 esta faixa de estações variou mais de 50 cm em três horas sem enchente."*

| | DC-03 (Mirim retificado, SEMASA) | DC-06 (Mirim antigo, Itamirim) |
|---|---|---|
| cotas (Plano v17 = portal) | 1,48 / 1,85 / 2,50 | 1,50 / 1,85 / 2,55 |
| 30/08: maior variação em 3 h | **0,67 m** (verdade: mais de 50 cm) | **0,59 m** (verdade) |
| 30/08: máximo do dia | 0,98 m, **0,50 m abaixo** da atenção | 1,01 m, **0,49 m abaixo** |
| amplitude diária (mediana / máx) | 0,86 / 1,43 m | 0,77 / 1,11 m |
| máximo diário mediano | 0,96 m, **0,52 m abaixo** da atenção | 1,07 m, **0,43 m abaixo** |
| maior leitura em 35 dias | 1,97 m (12/09, cheia) | 1,48 m (2 cm abaixo da atenção) |
| vezes que passou da atenção | 7, todas em **01/09, 12/09 e 22/09** (cheias) | **nenhuma** |

**Conclusão:**
- A metade verdadeira do motivo é que as duas réguas oscilam mais de 50 cm em 3 h com a maré. Mas oscilar não é
  chegar à cota. Nos 35 dias, a maré sozinha deixou a DC-03 sempre a 0,5 m da atenção, em mediana, e a DC-06 a
  0,4 m.
- A DC-03 só passou da cota quando a cheia levantou a base. Nesses dias, a maré a fez cruzar e recruzar a cota: o
  mesmo padrão da DC-11.
- **Ressalva da janela:** a maior preamar prevista nos 35 dias foi 1,15 m sobre o NR, e a maior do ano é 1,23 m
  (tábua da Marinha). São 40 preamares de 876 acima da janela, em fev–abr e out–dez. Com o fator de maré da régua
  (0,79 na DC-03, 0,77 na DC-06), são **~6 cm a mais**: não fecha a folga de 0,4–0,5 m. Maré de tempestade
  (ressaca) não está na tábua e não apareceu na série.

**Se destravar**, a DC-03 precisa de histerese, pelo mesmo motivo da DC-11:

| DC-03 | mensagens em 35 dias |
|---|---|
| sem histerese | 20 |
| 0,10 m | 11 |
| 0,30 m | 11 |

Com 0,30 m:
- os três episódios avisam na **mesma leitura** (atraso 0,0 h);
- a primeira entrada em atenção (01/09 00:40) e em alerta (01/09 04:00) não muda;
- nenhuma subida para faixa mais alta deixa de sair.

A DC-06 não mandaria nenhuma mensagem nos 35 dias, com ou sem histerese.

**No mapa:** destravar dá cor ao pino pela leitura de agora (`reguasNoMapa.ts`), sem histerese. Pela série, isso só
acontece em dia de cheia.

## 2. Histerese da DC-05 (0,10 m) e da DC-11 (0,30 m): já ligada, auditada

Critérios do pedido, medidos:

| | DC-05, 0,10 m | DC-11, 0,30 m |
|---|---|---|
| mensagens em 35 dias | 16 → **16** | 112 → **52** |
| subidas de faixa | 6 → 6 | 52 → 23 |
| primeira entrada em atenção e em alerta | mesma leitura | mesma leitura (30/08 16:20; 01/09 04:30) |
| início de cada episódio (> 18 h separados) | 4 de 4 na mesma leitura | **8 de 8 na mesma leitura** (atraso 0,0 h) |
| subida para faixa mais alta que deixou de sair | 0 | **0** |
| subida de 30 cm depois de 3 h (repetição) | 4 → 4 | 8 → 6 |

**O que a histerese da DC-11 tira:**
- **29 reentradas na mesma faixa.** Em todas, o nível caiu abaixo da cota, mas não 0,30 m abaixo, e voltou. O tempo
  abaixo da cota foi de 0,5 h na mediana; 5 casos passaram de 6 h, e o maior foi de **8,3 h** (02/10, até 2,88 m,
  voltando a 3,02). Nenhum passou de 12 h.
- **Duas repetições** (13/09 16:40 a 3,38 m e 14/09 04:40 a 3,35 m), que sem histerese saíam porque a reentrada
  anterior tinha zerado a referência. Com histerese, a referência é o último nível anunciado (3,99 m em 12/09 01:10),
  e 3,38 m está abaixo dele: não é subida nova.
- A repetição de 12/09 00:10 (3,74 m) muda de hora: com histerese, o aviso de subida sai 1 h depois, a 3,99 m.

**Resposta ao critério "preservar os avisos de novas subidas":**
- toda subida para faixa mais alta é avisada na mesma leitura;
- todo episódio novo é avisado na primeira leitura acima da cota;
- toda subida de 30 cm acima do último nível anunciado, depois de 3 h, continua avisando.

O que deixa de ser avisado é a volta à mesma faixa a poucos centímetros da cota, depois de uma descida rasa.

**O caso de fronteira, para decisão:** uma "nova subida" depois de horas logo abaixo da cota (até 8,3 h na série)
não é avisada, porque a faixa ficou segurada. Se a regra deve ser outra, há uma alternativa medida: soltar a faixa
quando o nível fica **T horas** abaixo da cota, mesmo sem descer 0,30 m.

| DC-11, 0,30 m + soltar após T h abaixo da cota | mensagens em 35 dias |
|---|---|
| T = 3 h | 69 |
| T = 6 h | 61 (os 5 casos acima de 6 h voltam a avisar) |
| T = 12 h | 52 (igual a hoje) |

Isso não está implementado: é a pergunta. A DC-05 não tem esse caso: nenhuma mensagem some com 0,10 m.

## 3. DC-08: 1,70 m e 1,80 m — mesma régua; o zero só se prova para o 1,70

- **Mesma régua: confirmado.**
  - Mesmo código, DC-08/DC08.
  - Mesma coordenada, −26,979694, −48,711948: Mapa.php de 02/09, página antiga de 13/09 e portal novo de 19/09,
    27/09 e 08/10.
  - O nome mudou de "Ribeirão da Canhanduba – Rio do Meio", o do Plano v17, para "Rua Benjamin Dagnoni".
- **O 1,70 m está no zero das leituras que o site usa: confirmado.**
  - A página antiga (13/09) e o portal novo (27/09 e 08/10) publicam 1,70 m junto com as leituras e classificam a
    régua por esse valor (`situacao`).
  - O nível de base em dia parado é **0,95–1,01 m antes** da troca de portal (19/09) e **1,00–1,02 m depois**. A
    troca de publicação não trocou o zero.
- **O 1,80 m: não dá para provar o zero.**
  - O Plano v17 (22/12/2025) publica só as três cotas, sem zero, altitude ou leitura de referência.
  - A série do projeto começa em 30/08/2026, e a régua municipal não está no histórico estadual. Não há leitura de
    dezembro a agosto que mostre se houve renivelamento.
  - A diferença de 10 cm pode ser revisão da cota, troca de zero ou transcrição. Só a Defesa Civil de Itajaí
    resolve, e a orientação de 14/09 continua sendo não mandar ofício ao município.
- **Efeito prático em 35 dias:** com 1,70 ou com 1,80 m, os mesmos 5 episódios e as mesmas **23 mensagens**,
  todas em dia de chuva ou de cheia. O 1,70 avisa de 10 a 30 min antes (31/08 10:00 × 10:30; 10/09 04:50 × 05:10;
  11/09 16:30 × 16:40; 19/09 21:20 × 21:50; 21/09 20:10 × 20:20).

**Recomendação:** manter o 1,70 m provisório, como está. É o único dos dois que se prova no zero das leituras, e é o
mais cauteloso. O 1,80 continua registrado em `cota_provisoria.plano_v17`.

## 4. DC-07 (Murta): régua confirmada; a atenção é a mesma nas duas fontes

- **Régua: confirmada.**
  - Código DC07.
  - Coordenada idêntica no Mapa.php de 02/09 e no portal de 08/10 (−26,892699, −48,735573).
  - O Plano chama a régua de "Ribeirão da Murta – Portal I", e o portal de "Ribeirão da Murta – Portal". Nenhuma
    fonte do projeto cita uma "Portal II".
  - Base em dia parado: 0,31–0,35 m antes da troca de portal e 0,32–0,34 m depois. É o mesmo zero nas duas
    publicações.
- **Cotas:**

  | | atenção | alerta | emergência |
  |---|---|---|---|
  | Plano v17 (cadastro) | **1,00** | 1,35 | 1,65 |
  | portal (13/09, 27/09, 08/10; classifica a régua) | **1,00** | 1,40 | 1,50 |
  | outra edição do Plano (lida em 08/09) | 0,98 | 1,23 | 1,60 |

  A **atenção de 1,00 m é a mesma** no Plano v17 e no portal, e o portal a aplica às leituras de hoje. Alerta e
  emergência divergem.
- **Na série:**
  - máximo de 1,47 m;
  - três episódios acima da atenção (31/08, 10/09 e 21/09), todos em dia de chuva ou de cheia;
  - com as cotas do Plano ou do portal, as **mesmas 10 mensagens** e as mesmas faixas (atenção e alerta, nunca
    emergência);
  - só 5 leituras ficaram entre 1,35 e 1,47 m, onde as duas tabelas discordam do nome da faixa;
  - nenhuma leitura entre 1,50 e 1,65 m, onde a do portal já seria emergência;
  - 15 dos 35 dias foram parados (base ~0,32 m em dia seco), mas a régua respondeu a toda chuva da série.
- **Para habilitar a Murta:**
  - a atenção (1,00 m) está confirmada nas duas fontes;
  - falta escolher alerta e emergência: Plano v17 (1,35 / 1,65) ou portal (1,40 / 1,50).

  O precedente da DC-08 seria o portal como provisório, com o Plano registrado ao lado. Com a cota escolhida, o
  vínculo DC-07 → DC-09 (4,86 km, `docs/VAO-MURTA.md`) entra parado, como o Canhanduba. Na série, a DC-07 não
  precisa de histerese: são 10 mensagens sem, 8 com 0,30 m.

## 5. Decisões do Jefferson (10/10/2026) — mescladas no #539, auditadas com 06–07/10 na seção 6

| régua | decisão | no cadastro |
|---|---|---|
| DC-03 | destravar, histerese 0,30 m e liberação após 6 h abaixo da cota | `aviso_histerese_m: 0.3`, `aviso_libera_apos_h: 6` |
| DC-06 | destravar, atenção 1,50 m | sem histerese |
| DC-05 | manter | 0,10 m, sem liberação |
| DC-11 | liberação após 6 h abaixo da cota (61 mensagens em vez de 52) | `aviso_libera_apos_h: 6` |
| DC-08 | manter 1,70 m provisório | `cota_provisoria.atencao.zero_do_plano`: pendência do zero do Plano |
| DC-07 | cotas do portal provisórias (1,00 / 1,40 / 1,50 m), divergência com o Plano documentada; Murta habilitada | `cota_provisoria` de alerta e emergência; vínculo DC-07 → DC-09, parado |

**A liberação por tempo** (`alerta_cotas.liberar_por_tempo`): quando a histerese segura a faixa, o estado guarda
`segurada_desde`. Se o nível passa `aviso_libera_apos_h` horas abaixo da cota, a faixa solta (sai o "baixou"), e a
volta à cota avisa de novo. Voltar à cota antes disso zera a contagem.

**Com a série de 30/08 a 05/10 e o cadastro novo** (`auditar_avisos_itajai.py`, seção "Configuração do cadastro"):

| régua | mensagens | episódios com aviso na 1ª leitura | subida de faixa sem aviso | maior rajada em 24 h |
|---|---|---|---|---|
| DC-03 | 11 | 3 de 3 | 0 | 5 |
| DC-05 | 16 | 4 de 4 | 0 | 4 |
| DC-06 | 0 | — | 0 | 0 |
| DC-07 | 10 | 3 de 3 | 0 | 6 |
| DC-08 | 23 | 5 de 5 | 0 | 5 |
| DC-10 | 4 | 2 de 2 | 0 | 2 |
| DC-11 | 61 | 8 de 8 | 0 | 6 |

A auditoria com a chuva de 06–07/10, pedida antes de ativar, está na seção 6.

## 6. Com a chuva de 06–07/10 (série até 10/10 11:20)

**Série:** `arquivo-series` em `8bc5ebe` (cópia da VPS de 10/10 14h43 UTC), de 30/08 16:00 a 10/10 11:20, hora de
Brasília. De 05/10 12h em diante, a maior lacuna foi de 1,3 h (07/10 12h50) nas réguas que avisam, 2,5 h na DC-03.

**Conferido com o motor de verdade.** A série inteira, leitura a leitura, por `alerta_cotas.decidir` com o cadastro
do #539, dá os mesmos números da seção "Configuração do cadastro" do script:

| régua | mensagens até 05/10 | até 10/10 | episódios com aviso na 1ª leitura | subida de faixa sem aviso | maior rajada em 24 h |
|---|---|---|---|---|---|
| DC-03 | 11 | 11 | 3 de 3 | 0 | 5 |
| DC-05 | 16 | **18** | **5 de 5** | 0 | 4 |
| DC-06 | 0 | 0 | — | 0 | 0 |
| DC-07 | 10 | 10 | 3 de 3 | 0 | 6 |
| DC-08 | 23 | **26** | **6 de 6** | 0 | 5 |
| DC-10 | 4 | 4 | 2 de 2 | 0 | 2 |
| DC-11 | 61 | **72** | **9 de 9** | 0 | 6 |

**O que a chuva de 06–07/10 fez com os avisos** (todas as mensagens de 06/10 em diante):

| hora (Brasília) | régua | nível | mensagem |
|---|---|---|---|
| 06/10 07:10 | DC-08 | 1,71 m | atenção (provisória) |
| 06/10 09:21 | DC-05 | 1,60 m | atenção |
| 06/10 10:20 | DC-08 | 2,04 m | atenção, repetida (3 h e +0,33 m) |
| 06/10 23:50 | DC-11 | 3,01 m | atenção |
| 07/10 10:20 | DC-08 | 1,68 m | normal |
| 07/10 14:10 | DC-11 | 3,35 m | atenção, repetida |
| 07/10 17:51 | DC-05 | 1,50 m | normal (1,60 − 0,10) |
| 08/10 a 10/10 | DC-11 | 3,00–3,04 m / 2,67–2,70 m | quatro pares atenção → normal, um por preamar alta |

Máximos de 06/10 em diante: DC-08 2,28 m (07/10 02:50), DC-11 3,35 m, DC-05 1,71 m, DC-10 5,26 m, DC-06 1,13 m,
DC-03 1,04 m, DC-07 0,87 m.

**O que se aprende:**
- **Nenhuma subida ficou sem aviso.** Os três episódios novos (DC-05, DC-08 e DC-11) avisaram na primeira leitura
  acima da cota.
- **As três réguas destravadas ficaram quietas, como devem.** A chuva não levou a DC-03 (1,04 m contra 1,48), a DC-06
  (1,13 contra 1,50) nem a DC-07 (0,87 contra 1,00) à atenção. Nenhuma mensagem delas. Com as cotas do Plano, a DC-07
  também não avisaria: a atenção é a mesma, 1,00 m.
- **A liberação após 6 h não custou mensagem nesta chuva.** De 06/10 em diante, a DC-11 manda 11 mensagens com ou sem
  ela (sem histerese seriam 21). No total, 72 com a liberação e 63 sem: a diferença de 9 é toda de antes de 05/10.
- **A DC-11 depois da chuva é maré, não cheia.** De 08 a 10/10, com a DC-10 abaixo de 5,3 m, a preamar levou a
  DC-11 a 3,00–3,04 m quatro vezes, e a baixa-mar a 2,67–2,70 m, o bastante para a histerese de 0,30 m soltar a
  faixa. São oito mensagens em três dias, com ou sem a liberação. É o comportamento já descrito na seção 2: a
  histerese reduz repetição, não tira a maré. Com o rio ainda alto depois da chuva, a preamar passa da cota.
- **A DC-08 chegou a 2,28 m, 2 cm abaixo do alerta**, sem nova mensagem depois da das 10:20 (2,04 m): a repetição
  pede +0,30 m. É a regra de repetição de sempre, que este PR não muda.

**Situação que nenhuma das duas janelas testou:** subida da DC-07 acima de 1,40 m com as cotas novas (só 31/08, com
1,47 m), DC-06 na cota, e a DC-03 na liberação depois de uma cheia longa. O código dessas três está coberto por
testes (`LiberacaoPorTempo` em `teste_alerta_cotas.py`); a série ainda não tem o caso.

**Conclusão:** a chuva de 06–07/10 não trouxe situação que mude as decisões de 10/10. O #539 foi mesclado às 14h45
UTC de 10/10, dois minutos depois da cópia e antes desta conferência; o resultado confirma o que entrou. Os avisos
passam a valer na VPS depois do `deploy.sh`.

## Como refazer

```bash
mkdir -p /tmp/serie && for m in 2026-08 2026-09 2026-10; do
  git show origin/arquivo-series:tempo-real/$m.ndjson > /tmp/serie/$m.ndjson; done
python3 scripts/auditar_avisos_itajai.py --serie /tmp/serie
```
