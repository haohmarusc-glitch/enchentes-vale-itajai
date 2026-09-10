# Evento de 10/09/2026 — onda de cheia descendo a bacia

Fotografia da cadeia às **19h40 BRT de 10/09/2026**. Registro feito porque este é
o material que o projeto persegue desde o começo: uma cheia real, com hora em cada
cidade, que permite medir tempo de trânsito em vez de estimá-lo.

---

## 1. Onde a onda está agora

| local | rio | nível | hora | tendência |
|---|---|---|---|---|
| **Taió, Centro** | Itajaí do Oeste | 4,56 m | 19:00 | **descendo** — pico de 5,46 m às 13h |
| Agronômica | Itajaí-Açu | 3,80 m | 19:36 | — |
| SDC-SC Pouso Redondo | — | 2,84 m | 19:37 | — |
| SDC-SC Laurentino | — | 4,21 m | 19:36 | — |
| **Rio do Sul, Ponte Dom Tito Buss** | Itajaí-Açu | **4,21 m** | 19:40 | subindo, atenção em 4,50 |
| Rio do Sul, Ponte BR 470 | Itajaí do Oeste | 4,40 m | 19:40 | — |
| Rio do Sul, Ponte Ricardo Kanitz | Itajaí do Sul | 3,39 m | 19:09 | — |
| **Blumenau** | Itajaí-Açu | 2,66 m | 18:00 | **estável** — onda ainda não chegou |
| **Gaspar** | Itajaí-Açu | 2,58 m | 19:07 | subindo, +0,75 m em 10 h |
| Brusque, Ponte Estaiada DCSC | Itajaí-Mirim | 2,19 m | 19:30 | subindo, 36,4 mm/24 h |
| Vidal Ramos | Itajaí-Mirim | 2,49 m | 19:36 | tranquilo |

Barragens: **Oeste (Taió)** montante 10,80 m, **0 de 7 comportas abertas** —
fechou às 13h, no pico. **Sul (Ituporanga)** montante 9,50 m.

**Leitura da situação:** Taió já passou o pico. A onda está entre Taió e Rio do
Sul. Blumenau ainda plana, Gaspar subindo por conta da chuva local e não da onda.
O Mirim tem evento próprio, menor, alimentado pelos 36 mm de Brusque.

---

## 2. Por que este evento importa mais que os outros

É a primeira cheia acompanhada **com a coleta funcionando e o cadastro
conferido**. Se o pico de Rio do Sul for registrado nas próximas horas, sai o
primeiro tempo de trânsito Taió → Rio do Sul medido em evento real, com hora nas
duas pontas e régua identificada nas duas.

O `coleta_niveis.py` roda a cada 15 min e o `coleta_asthon.py` entrou no
encadeamento — então **o dado está sendo gravado agora**, sem ação necessária. O
que falta é marcar o evento para não se perder no meio da série.

### O que capturar nas próximas 48 h

1. **Hora e valor do pico em cada cidade**, de montante para jusante. É a matéria
   bruta do tempo de trânsito.
2. **Estado das comportas da Barragem Oeste**, hora a hora. Elas fecharam no pico
   de Taió; qualquer trânsito Taió → Rio do Sul calculado neste evento carrega
   essa interferência e precisa dizer isso.
3. **O `dados/historico` de Taió**, que é janela móvel de 24 h — se ninguém puxar
   até amanhã às 19h, a subida de hoje **desaparece da fonte**. É o único dado
   deste evento com prazo de validade.

> A subida de Taió já está preservada no arquivo
> `B7-FONTES-E-EVENTO-TAIO-2026-09-10.md`, hora a hora, de 09/09 20h a 10/09 19h.

---

## 3. Ressalvas antes de usar como referência

**O montante da Barragem Oeste salta de forma não física** — 2,9 m até as 06h,
7,0 m às 07h, 10,4 m às 17h, 10,8 m às 19h36. Os dois primeiros saltos são grandes
demais para serem enchimento real. Ou troca de referência, ou erro de leitura.
Conferir antes de usar em qualquer cálculo.

**As comportas fecharam no pico**, de 7 abertas para 0 de 7 entre 12h e 13h. O
trânsito medido neste evento é o de um rio com barragem segurando água — não é o
trânsito natural, e não vale como caso geral.

**Rio do Sul tem três réguas** com escalas próprias; a de referência do município
é a **Ponte Dom Tito Buss** (`f6360951-219f-4859-935f-b2e2d13962f1`), onde a
atenção é 4,50 m. O site ainda lê a Estação MKS, que é outra régua — corrigir
antes de qualquer alerta desta noite.

**Gaspar sobe por chuva local**, não pela onda: Blumenau, que está entre Taió e
Gaspar, segue plana em 2,66 m. Não confundir as duas causas ao montar a curva de
propagação.

---

## 4. Estado das faixas neste momento

Nenhuma cidade da cadeia está em atenção pelas cotas municipais:

| cidade | nível | atenção | folga |
|---|---|---|---|
| Taió | 4,56 m | 7,00 m (5,00 m monitoramento) | passou o degrau de monitoramento hoje |
| Rio do Sul | 4,21 m | 4,50 m | **29 cm** |
| Blumenau | 2,66 m | 4,00 m | 1,34 m |
| Gaspar | 2,58 m | 5,00 m | 2,42 m |
| Brusque | 2,19 m | 3,00 m (régua DCSC) | 81 cm |

Rio do Sul é a que está mais perto, e é justamente a que o site lê pela régua
errada.
