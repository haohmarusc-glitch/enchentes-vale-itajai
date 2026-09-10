# B7 — investigação de fontes de histórico, e o evento de Taió de 10/09/2026

Coletado por navegador em 10/09/2026, entre 19h30 e 19h50 BRT.

---

## 1. Veredito do B7: bloqueado por ausência de fonte

O pedido — "baixar de novo a partir de 2022-06-01 Taió DCSC-00041 e as 16
estações da cadeia" — **não é executável**. Não é falta de execução, é falta de
fonte. Testado, não suposto:

### API Asthon (`public.asthon.com.br`)

Pedido de `2022-06-01` até hoje, nas quatro resoluções, para a estação de Taió e
para Vidal Ramos:

| estação | resolução | retorno |
|---|---|---|
| Barragem Oeste Taió | raw | n=7701, **desde 2026-07-17** |
| Barragem Oeste Taió | hourly | n=1288, desde 2026-07-17 |
| Barragem Oeste Taió | daily | n=7701, desde 2026-07-17 |
| Barragem Oeste Taió | monthly | n=7701, desde 2026-07-17 |
| Vidal Ramos | raw | n=8688, **desde 2026-07-28** |
| Vidal Ramos | hourly | n=1055, desde 2026-07-28 |
| Vidal Ramos | daily | n=8688, desde 2026-07-28 |
| Vidal Ramos | monthly | n=8688, desde 2026-07-28 |

Duas conclusões: a retenção é de **cerca de seis semanas** e nenhum parâmetro
destrava mais; e `daily`/`monthly` **não agregam** — devolvem o mesmo volume do
`raw`, então são rótulos aceitos e ignorados.

⚠ **A estação de Taió que aparece na lista de Rio do Sul é a Barragem Oeste, não a
DCSC-00041.** São réguas diferentes — baixar a barragem achando que é a régua do
rio repetiria o erro do Salseiro.

### API municipal de Taió (`api-scr.uniparking.com.br/v1/defesa-civil-taio/`)

Sondados 14 caminhos; dois existem:

| endpoint | conteúdo | serve? |
|---|---|---|
| `dados/cards` | estado atual | é o que o coletor já usa |
| `dados/historico` | **24 registros horários**, janela móvel | só as últimas 24 h |
| `dados/barragem` | 20 registros, mas de **16 a 24 de maio** | snapshot velho e congelado |

Todos os outros (`grafico`, `niveis`, `series`, `leituras`, `estacoes`,
`chuvas`, `historicos`, `historico` na raiz, `cards/historico`, `dados`) → 404.
Parâmetros de data e `limit` são ignorados.

### O que sobra para série longa

1. **Portal de Brusque** — `POST /estacao/baixar-historico`, chunks de 1 ano,
   cobre 2018 em diante. Só para as estações cadastradas lá. VPS alcança.
2. **Hidroweb/ANA** — para quem tem código ANA. **A DCSC-00041 precisa ter o dela
   confirmado antes** (pedir junto ao ofício da EPAGRI, que já pergunta o
   cruzamento código ANA ↔ coordenada).
3. **Acumulação própria** — o `baixar_historico_asthon.py` mescla em vez de
   sobrescrever; rodado semanalmente, em dois meses guarda mais série do que a API
   oferece hoje.

### Achado aproveitável

`dados/historico` de Taió entrega, na mesma linha e de hora em hora: **nível,
chuva, montante, jusante e comportas abertas/fechadas**. É mais rico que a
Asthon, que não traz estado de comporta. Coletado a cada 24 h vira série própria.
Vale um coletor.

---

## 2. Evento de Taió — 10/09/2026

A régua do Centro subiu de **2,17 m às 22h de 09/09** para **5,46 m às 13h de
10/09**: 3,29 m em quinze horas.

| hora | nível | | hora | nível |
|---|---|---|---|---|
| 09/09 20h | 2,19 | | 10/09 10h | **5,13** |
| 09/09 22h | 2,17 (mínima) | | 10/09 11h | 5,28 |
| 09/09 23h | 2,18 · chuva 3,6 mm | | 10/09 12h | 5,39 |
| 10/09 00h | 2,38 | | 10/09 13h | **5,46 (pico)** |
| 10/09 03h | 3,08 | | 10/09 14h | 5,42 |
| 10/09 06h | 4,00 | | 10/09 15h | 5,25 |
| 10/09 08h | 4,61 | | 10/09 16h | 5,06 |
| 10/09 09h | 4,91 | | 10/09 17h | 4,90 |
| | | | 10/09 19h | 4,56 |

Cruzou os 5,00 m entre 09h e 10h, ficou acima por cerca de sete horas, e às 19h
seguia descendo. Chuva acumulada em 24 h no cartão: **86,3 mm**.

### ⚠ Isto valida a decisão do `cotas_divergencias` de Taió

A decisão registrada ontem — avisar em 5,00 m, mesmo o PLANCON chamando o degrau
de "monitoramento" — **teria disparado hoje às 10h**. E o rio subiu mais 46 cm
depois de cruzar o degrau, chegando a 5,46 m.

Com a regra "monitoramento não avisa", o site teria ficado amarelo e mudo durante
a subida inteira. Deixou de ser argumento teórico: é evidência de campo, e vale
anexar ao registro da divergência.

### Barragem Oeste — dois pontos a conferir antes de usar

**O montante salta.** 2,9 m até as 06h → **7,0 m às 07h** → **10,4 m às 17h**.
Saltos grandes demais para serem físicos: ou é troca de referência no meio da
série, ou erro de leitura. Mesmo tipo de problema do "3 m" de Ituporanga.

**As comportas fecharam no pico.** De **7 abertas** até as 12h para **0 de 7** às
13h, exatamente quando o rio atingiu 5,46 m. Faz sentido operacional — a barragem
passou a segurar —, mas muda a vazão a jusante e afeta qualquer cálculo de
trânsito Taió → Rio do Sul que use este evento como referência.

---

## 3. Estado dos rios no momento da coleta (10/09, ~19h30)

| local | nível | situação | observação |
|---|---|---|---|
| Taió, Centro | 4,56 m | descendo | pico de 5,46 m às 13h; 86,3 mm em 24 h |
| Gaspar, Itajaí-Açu | 2,58 m (19:07) | NORMALIDADE | subiu 0,75 m em 10 h |
| Brusque, Ponte Estaiada DCSC | 2,19 m (19:30) | NORMALIDADE | 36,4 mm em 24 h |

O site de Gaspar exibe aviso de temporais com granizo e chuva intensa. **O B11 —
`apt upgrade` com reboot "numa hora sem chuva" — não é para agora.**

---

## 4. O que segue bloqueado, e por quê

| item | situação |
|---|---|
| B5, B6 | `scp` e anexos: operações no PC e na VPS, fora do meu alcance |
| B7 | **sem fonte** para 2022; redefinir escopo antes de reabrir |
| B10, B11 | shell na VPS; o B11 espera o tempo firmar |

### Sugestão de novo escopo para o B7

Trocar "baixar de 2022-06-01" por três tarefas independentes:

1. **Confirmar o código ANA da DCSC-00041** e, havendo, puxar a série do Hidroweb
   — é a única via com dado consistido e longo.
2. **Listar quais das 16 estações da cadeia existem no portal de Brusque**, e
   baixar essas por `baixar-historico` em chunks anuais, de 2018 em diante.
3. **Criar coletor para `dados/historico` de Taió**, rodando a cada 12 h para não
   perder a janela de 24, guardando nível + chuva + montante + comportas.
