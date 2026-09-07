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

## O que este episódio ensinou, além de Gaspar

- **Fonte que some é mais perigosa que fonte errada**: a errada dispara trava, a
  que some não dispara nada, porque não há o que comparar.
- **Reformulação de site é evento de dado.** O host respondeu normalmente até
  01/09; nenhuma trava do projeto olha para "a página mudou de forma".
- O `ultimo_gaspar.json` versionado no repositório continuou com a leitura de
  01/09 esse tempo todo. Arquivo velho no git não parece quebrado — parece dado.
