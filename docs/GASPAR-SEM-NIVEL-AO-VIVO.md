# Gaspar ficou sem nível ao vivo — e ninguém percebeu por seis dias

Data: 07/09/2026. Diagnóstico fechado com o Jefferson, comparando a VPS, este
ambiente e o navegador do celular dele.

**Gaspar não tem nenhuma fonte de nível de rio ao vivo.** A cidade tem **1.619
cotas de rua** e, desde ontem, **49 picos históricos**: sabe-se em que nível cada
rua alaga e não se sabe em que nível o rio está.

---

## Duas coisas aconteceram juntas, e a segunda é a que decide

### 1. O host parou de responder à VPS

Medido em 07/09/2026, da VPS (Hetzner, Alemanha):

```
monitoramento/tabela : timeout após 30,00 s
enchentes            : timeout após 30,00 s
coleta_gaspar.py     : RECUSADO — nem o robots.txt respondeu
```

A **mesma página abre normalmente** no navegador de um celular no Brasil. Então
não é queda do site: é **bloqueio de IP estrangeiro ou rota**. Não se conserta
com código nosso.

### 2. ⛔ A régua do Açu saiu da página

Esta é a que importa, e ela torna a primeira quase irrelevante.

A página foi **reformulada** — o rodapé agora diz *"© 2026 Município de Gaspar |
Desenvolvido por DEXTAK"*. Comparando a última coleta que funcionou (31/08/2026
22:59) com o que a página mostra hoje:

| Estação | 31/08 | 07/09 |
|---|---|---|
| **Rio Itajaí Açu Gaspar** | **3,85 m** | **removida** |
| Ribeirão Belchior Central | 1,68 m | **0,00** |
| PLU LOC. - Sertão Verde | presente | removida |
| PLU. - Alto Gasparinho | presente | removida |
| Pluviômetro - Macucos | presente | removida |
| Barragem Norte José Boiteux (DCSC) | — | 273,75 |
| Barragem Oeste Taió (DCSC) | — | 350,44 |
| Barragem Sul Ituporanga (DCSC) | — | 388,07 |

**Mesmo com a rede funcionando, não haveria nível do Açu para coletar.**

⚠️ Os números das barragens são **altitude de reservatório**, não nível de rio —
a mesma armadilha já documentada em Taió (`nivelCentro` ~5 m contra `montante`
~17 m). O coletor separa `barragens` de `estacoes`, então isso não vira nível de
cidade por acidente. Fica registrado porque a próxima pessoa a olhar essa tabela
vai ver três números grandes e pode achar que são réguas.

⚠️ O `0,00` do Ribeirão Belchior é ausência publicada como zero, não um ribeirão
seco. Em 31/08 ele marcava 1,68 m.

---

## Não há plano B

| Fonte | Situação |
|---|---|
| Página municipal | régua do Açu removida na reformulação |
| API estadual (DCSC-00005) | `tem_nivel_do_rio = false` — não mede nível de rio |
| ANA 83840000 | escala encerrada em **12/2021**, **sem sucessora** (única das quatro mortas naquele mês sem substituta) |

O pino de Gaspar fica **cinza** no mapa, que é o honesto: o site se recusa a
afirmar o que não mediu. Mas o cinza não distingue "nunca teve fonte" de "a
fonte morreu esta semana", e é isso que este documento registra.

---

## ⚠️ O vigia avisou uma vez e calou — e o motivo está escrito no código

`saude_coleta.py` compara a coleta atual com a **rodada anterior**, não com o
cadastro. É deliberado, e o comentário diz por quê:

> *"A comparação é com a rodada anterior, e não com o cadastro, de propósito:
> Blumenau está cadastrada e nunca vem, e um vigia permanentemente vermelho
> ensina quem opera a ignorá-lo — que é o oposto do que ele serve."*

O raciocínio é bom e continua valendo. Mas tem uma consequência que não estava
prevista: quando Gaspar sumiu em 01/09, o vigia reclamou **uma vez**. Na rodada
seguinte, Gaspar já não estava em `vistas_antes` — e o alarme sumiu junto com a
estação.

**Uma fonte que morre é anunciada uma vez e depois fica invisível.** Foi assim
que seis dias passaram.

Some-se a isso que `coleta_niveis.py` chama Gaspar (linha 627) a cada 15 minutos
pelo cron: a coleta **vem falhando cerca de 96 vezes por dia**, gastando 30 s de
timeout em cada ciclo, sem que nada acuse.

### O conserto proposto, e por que não foi feito ainda

Lembrar das estações vistas nos **últimos N dias**, em vez de só na última
rodada. É o meio-termo que o comentário implica e não implementou:

- estação que **nunca** veio não é cobrada — Blumenau continua sem vermelho
  permanente;
- estação que veio ontem e não veio hoje **continua cobrada** por N dias.

Não foi feito porque **muda quando o Telegram dispara**, e alarme demais é
exatamente o que o comentário original alerta. É decisão de quem opera.

---

## O que resolve, em ordem

1. **Perguntar à Superintendência de Proteção e Defesa Civil de Gaspar** se a
   régua do Açu mudou de endereço na reformulação do site, ou pedir o endpoint
   que a página consome. É a única pergunta que devolve o dado.
2. **Se a régua voltar**, resolver o acesso: a VPS não alcança o host. Um proxy
   no Brasil, ou coleta a partir de outra máquina.
3. **Consertar o vigia**, para o próximo desaparecimento não levar seis dias.

---

## Leitura direta da fonte (07/09/2026), pelo navegador

O Jefferson abriu as páginas e extraiu o conteúdo. Confirma tudo acima e
acrescenta quatro coisas.

### ✅ Confirma que Gaspar não mede o Açu

Sete estações, **uma só de rio, e é um ribeirão afluente**. A régua do Açu não
existe na página. O "sem leitura" que o app mostra em Gaspar **não é falha do
app**.

### 🔌 Endpoints, que o coletor ainda não usava

| O quê | Endpoint |
|---|---|
| Série histórica por estação | `POST /estacao/baixar-historico` — campos `codest`, `inicio`, `fim` |
| Detalhe + série de 12 h | `GET /estacao/ver/{id}` — Belchior **73**, Arraial d'Ouro 54, Bateias 13, Poço Grande 15 |
| Busca de cota por endereço | `POST /cotas/pesquisar` |

Servem para o **Belchior**, não para o Açu — que continua sem existir na fonte.
Ainda assim valem: `baixar-historico` aceita intervalo arbitrário, o que
resolveria série histórica se a régua voltar. **O formulário não foi acionado.**

### Cotas do Ribeirão Belchior Central

Publicadas na legenda de `/estacao/ver/73`: normalidade < 5,00 m · atenção
5,00 m (ou chuva atual > 6,00 mm) · emergência 7,00 m. **Não há faixa de alerta
intermediária** — a fonte pula de atenção para emergência.

⚠️ E a série de 12 h do Belchior é **0,00 em todos os 71 pontos**, de 03:28 a
15:18. Zero servido como medição, não como ausência. Qualquer coletor que aponte
para essa estação precisa tratar `0,00` como suspeito.

### ⚠️ Duas correções ao levantamento

**1. As cotas de rua de Gaspar já estão no repositório.** O relatório diz que
`data/cotas-ruas.json` *"hoje só tem Itajaí"*. É o inverso: o arquivo tem
**Gaspar 1.619**, Blumenau 2.023, Rio do Sul 555 e Brusque 377 — e **não tem
Itajaí**. As de Gaspar entraram pelo estudo CEOPS/FURB.

**2. A contagem difere em quatro.** A página serve **1.615** pontos; o
repositório tem **1.619**. Pode ser mudança da página na reformulação, ou quatro
duplicados do nosso lado. Não resolvido — anotado para não passar em silêncio.

---

## ✅ A referência vertical: a objeção era justa, e a medição respondeu

O levantamento anotou: *"A fonte não explicita a referência vertical da régua de
Gaspar. Cadastrar sem referência resolvida."* Está certo sobre a fonte — a
página não declara nada.

Os 49 registros entraram como `referencia: "régua"` mesmo assim, e o que
sustenta isso é uma **medição**, não uma suposição:

| | |
|---|---|
| menor cota de rua de Gaspar (1.619 pontos) | **6,20 m** |
| menor pico da lista histórica (70 registros) | **6,19 m** |
| **diferença** | **1 cm** |

As cotas de rua vêm do estudo CEOPS/FURB (coord. Ademar Cordeiro), que
**declara** a referência: *"régua da ANA na empresa Círculo"*. A lista histórica
**começa exatamente onde a primeira rua alaga**, a um centímetro. Dois conjuntos
publicados por caminhos diferentes não concordam no piso por acaso: é a mesma
escala, e a lista é de cheias **que alagaram**.

**É evidência forte, não prova.** Se a Superintendência disser que são pontos
diferentes, é isto que muda. `teste_importar_gaspar_enchentes.py` trava o 1 cm:
se os dois pisos se afastarem, a decisão precisa ser revista.

---

## O que este episódio ensinou, além de Gaspar

- **Fonte que some é mais perigosa que fonte errada**: a errada dispara trava, a
  que some não dispara nada, porque não há o que comparar.
- **Reformulação de site é evento de dado.** O host respondeu normalmente até
  01/09; nenhuma trava do projeto olha para "a página mudou de forma".
- O `ultimo_gaspar.json` versionado no repositório continuou com a leitura de
  01/09 esse tempo todo. Arquivo velho no git não parece quebrado — parece dado.
