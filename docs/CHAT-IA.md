# Chat com IA — `/api/chat-ia`

Pedido do Jefferson (04/10/2026): *"Pode criar api para o chat responder muitas perguntas?"*

O chat local (`docs/CHAT-LOCAL.md`) só entende perguntas em alguns formatos. A API deixa uma IA
(Claude, da Anthropic) responder perguntas livres, **usando os mesmos dados do site** e as mesmas regras.

**Estado: o código está pronto e DESLIGADO.** A IA só liga quando o Jefferson põe a chave da Anthropic
no Cloudflare (passo a passo em `docs/PUBLICACAO-E-ACESSO.md`, "Chat com IA").

## Como funciona na tela

1. A pessoa pergunta; **o chat local responde primeiro, sempre**. Ele é grátis, não manda nada para
   fora e é o que já está testado.
2. Se a IA estiver ligada, cada resposta do chat local ganha um botão **"Perguntar à IA"**. Só com esse
   clique a pergunta vai à IA. É uma pergunta por clique.
3. A resposta da IA aparece com o rótulo *"Resposta da IA com os dados do site — pode errar"*.
4. Embaixo da caixa fica o aviso: *o botão envia o texto da pergunta à Anthropic (…) Não escreva nome,
   endereço ou telefone. A IA pode errar: confira a fonte citada.*

Pergunta sobre o **presente** (nível de agora, previsão, "vai encher?", "devo sair?") **nunca vai à IA**:
- a resposta do chat local para ela não ganha o botão;
- e o servidor recusa de novo com a mesma barreira (`pedeAgora` do motor). Ele devolve o texto do 199
  sem chamar a IA.

## O que a IA vê

A IA **não recebe os JSONs inteiros**. Ela consulta quatro ferramentas, que leem os dados do site:

| Ferramenta | O que devolve |
|---|---|
| `consultar_motor` | Roda **o motor do chat local** com uma pergunta reescrita. Assim herda as regras já testadas: régua × IBGE × ANA, Brusque antes de 2019, as onze réguas de Itajaí, a contagem de rua só na régua e a lista esparsa de Gaspar. |
| `picos_da_cidade` | Os picos da cidade, cada um com a sua **escala** (`regua`, `ibge`, `ana`, `nao-declarada`, `antes-da-regua`), a confiança, a fonte e o valor como foi publicado. |
| `info_da_cidade` | As cotas da Defesa Civil, com os nomes que a fonte usa, e as observações do cadastro. |
| `tempos_de_descida` | As faixas de `transito.json` e os trechos experimentais, que não têm faixa. |

O texto de instruções (`montarSistema` em `web/src/chat-ia/nucleo.ts`) repete as regras do `CLAUDE.md`:
- não inventar número;
- não falar do presente;
- não comparar metros entre cidades;
- não somar escalas diferentes;
- não eleger "a maior cheia de Itajaí";
- tempo de descida só como intervalo;
- sem previsão a jusante;
- sempre a fonte.

`eventos-pendentes-regua.json` continua fora: o servidor não o importa.

## Privacidade

- **Vai à Anthropic:**
  - o texto da pergunta;
  - as duas últimas trocas com a IA naquela página, como contexto;
  - o que as ferramentas devolvem.
- **Não vai à Anthropic:** IP, User-Agent e o **e-mail** de acesso. A função não lê IP nem User-Agent.
- **O e-mail fica registrado, por decisão do Jefferson (04/10/2026), para controlar o gasto.**
  - O e-mail é o que o Cloudflare Access põe no cabeçalho `cf-access-authenticated-user-email`.
  - Ele entra na linha de log de cada pergunta e, com o KV, no total do dia por e-mail.
  - O e-mail vai junto com a quantidade de perguntas e o custo, **nunca com o texto**.
  - A tela avisa isso antes de cada envio.
  - Sem o cabeçalho, ou com valor que não é e-mail, o registro sai com `null` (no KV, `(sem e-mail)`).
  - O cabeçalho serve para a conta de custo, não como prova de identidade.
- **O site não grava** a pergunta nem a resposta. Com o KV `CHAT_IA` ligado, guarda:
  - `ia|AAAA-MM-DD` → perguntas do dia, para o teto (some em 3 dias);
  - `uso|AAAA-MM-DD` → tokens e custo somados do dia, e `por_email` com perguntas e custo de cada
    e-mail (some em 90 dias).
- No log da Cloudflare, um erro aparece só como tipo e status (`RateLimitError 429`), sem a pergunta.
- **Retenção do lado da Anthropic:** segue a política de dados da conta da API. Conferir no Console da
  Anthropic e nos termos comerciais antes de ligar; este documento não substitui essa leitura.

Isso é diferente da contagem do chat (`TELEMETRIA-CHAT.md`), que nunca manda o texto. Aqui o texto
precisa ir, senão não há resposta. Por isso a regra é o **clique por pergunta** com o aviso à vista, e não
um envio automático.

## Custo e limites

- **Modelo:** `claude-opus-5-5` por padrão, o mais capaz.
  - Dá para trocar sem mexer no código pela variável `CHAT_IA_MODELO`, por exemplo `claude-sonnet-5-5`,
    pela metade do preço.
  - O esforço de raciocínio é `low`: é chat e o celular espera a resposta.
- **Estimativa por pergunta.** Medida em 04/10/2026 pelo tamanho real das instruções (~3,9 mil caracteres),
  das ferramentas (~2,8 mil) e do que elas devolvem. Ainda **sem nenhuma pergunta real**.

  | Pergunta | Tokens (entrada / saída) | Opus 5.5 | Sonnet 5.5 |
  |---|---|---|---|
  | Comum ("maior cheia de Gaspar"): 1 consulta ao motor, 2 rodadas | ~7 mil / ~1 mil | ~US$ 0,05 | ~US$ 0,025 |
  | Pesada ("média por década em Blumenau"): lê os 129 picos (~33 mil caracteres), 3 rodadas | ~22 mil / ~2 mil | ~US$ 0,12–0,15 | ~US$ 0,06–0,08 |

  Por mês, com média de US$ 0,06: 10 perguntas/dia ≈ US$ 18; 50/dia ≈ US$ 90 (Opus). No Sonnet, metade.
  O gasto real aparece no log e no KV (abaixo) e no Console da Anthropic.
- **Tetos:**
  1. Máximo de 6 rodadas de ferramenta por pergunta.
  2. Pergunta com até 500 caracteres.
  3. `CHAT_IA_LIMITE_DIA` perguntas por dia no site todo (padrão **50**, baixado de 300 em 04/10/2026
     para começar com folga no bolso), quando o KV `CHAT_IA` está ligado. Sem o KV, não há teto diário.
  4. **O teto que garante o bolso é o limite mensal da chave no Console da Anthropic**
     (*Settings → Limits*). Configure-o ao criar a chave.
- **Recusa por política:**
  - O pedido leva `fallbacks: "default"` (beta `server-side-fallback-2026-07-01`): se o modelo declinar,
    a própria API tenta o modelo de reserva.
  - Se todos recusarem, a tela mostra um texto fixo.
- O site está atrás do Cloudflare Access, então só quem tem e-mail cadastrado chega a `/api/chat-ia`.

## Qual modelo (custo × benefício), 04/10/2026

Preços da API em US$ por milhão de tokens (entrada / saída). Custo por pergunta medido pelo tamanho real
das instruções e das ferramentas (seção acima); ainda sem pergunta real.

| Modelo | Preço | Pergunta comum | Pergunta pesada | Para este site |
|---|---|---|---|---|
| `claude-opus-5-5` (padrão do código) | 4 / 20 | ~US$ 0,05 | ~US$ 0,12–0,15 | O mais cuidadoso com as regras; caro para um chat de histórico. |
| **`claude-sonnet-5-5`** | 2 / 10 | ~US$ 0,025 | ~US$ 0,06–0,08 | **Recomendado.** Segue bem instruções e ferramentas; metade do preço; responde mais rápido no celular. |
| `claude-haiku-4-5` | 1 / 5 | ~US$ 0,012 | ~US$ 0,03–0,04 | O mais barato, mas mais propenso a escorregar nas regras: misturar réguas, comparar metros entre cidades, esquecer a fonte. Aqui um erro é afirmação falsa sobre enchente. |

- **Recomendação:** `CHAT_IA_MODELO = claude-sonnet-5-5`.
  - O trabalho é ler o que as ferramentas devolvem e reescrever em português simples, sem quebrar
    regras.
  - O motor local já faz a parte delicada (régua, escala, Itajaí).
  - Se as respostas reais mostrarem erro de regra, volta para o Opus mudando só a variável.
- O código ajusta o pedido a cada modelo (`opcoesDoModelo`): o Haiku vai sem `effort` e sem reserva por
  recusa, que ele não aceita. Trocar a variável não quebra o pedido.

## Acompanhar o custo (pedido do Jefferson, 04/10/2026)

Cada pergunta respondida escreve **uma linha** no log da Cloudflare, com o e-mail de acesso e números:

```
{"evento":"chat-ia","email":"fulano@exemplo.com","tipo":"ia","modelo":"claude-opus-5-5","rodadas":2,"entrada":6800,"cache_criado":0,"cache_lido":0,"saida":950,"custo_usd":0.0462}
```

- **Os campos:**
  - `entrada` é a parte sem cache; `cache_criado` e `cache_lido`, a parte que passou pelo cache.
  - `modelo` é o que respondeu de fato, que pode ser o de reserva depois de uma recusa.
  - `custo_usd` sai da tabela de preços em `nucleo.ts` (`PRECOS`). Modelo fora da tabela fica com
    `null`, nunca com palpite.
- **Onde ver ao vivo:** *Workers & Pages → `enchentes-vale-itajai` → Deployments → (o deploy de
  produção) → Functions → Real-time logs → Begin log stream*. O log ao vivo do Pages **não guarda
  histórico**.
- **Histórico:** com o KV `CHAT_IA` ligado, a função soma o dia em `uso|AAAA-MM-DD`, mantido por 90 dias:

  ```
  {"perguntas":12,"entrada":81000,"cache_criado":0,"cache_lido":3000,"saida":11500,"custo_usd":0.5546,
   "por_email":{"fulano@exemplo.com":{"perguntas":9,"custo_usd":0.41},"(sem e-mail)":{"perguntas":3,"custo_usd":0.1446}}}
  ```

  Para ler: *Storage & Databases → KV → `enchentes-chat-ia` → KV Pairs*.
- **O que não vai no log nem no KV:** a pergunta, a resposta e o IP. Há teste que trava isso
  (`endpoint.test.ts`), e outro que trava que o e-mail não vai à Anthropic.
- **Pergunta que falhou no meio** (erro da API depois de uma rodada) não entra na conta. O Console da
  Anthropic continua sendo o valor oficial.
- A pergunta de agora, que não vai à IA, aparece no log com `tipo: "agora"` e custo 0.

## Arquivos

| Arquivo | Papel |
|---|---|
| `web/src/chat-ia/nucleo.ts` | Instruções, ferramentas e o laço de consulta. Sem rede: o cliente da API entra de fora. |
| `web/src/chat-ia/cliente.ts` | O lado do aparelho: o GET de "ligado?", o envio de uma pergunta e as mensagens de erro. |
| `web/functions/api/chat-ia.ts` | A Pages Function: chave, limite do dia, origem, corpo e erros. |
| `web/src/chat-local/ChatLocal.tsx` | O botão "Perguntar à IA", o rótulo e o aviso. |
| `nucleo.test.ts`, `endpoint.test.ts`, `cliente.test.ts` | Travas com cliente **falso**: nenhum teste chama a API. |
| `testes-navegador/fumaca.mjs` | Botão só com o servidor ligado, aviso visível, pergunta de agora sem botão, envio e rótulo. |

**Conferido em 04/10/2026:**
- A função compila com o `wrangler pages functions build`: ~6,6 MB, ~630 KB comprimidos, abaixo do
  limite de 3 MB do plano gratuito.
- Ela roda no `workerd` local (`wrangler pages dev`):
  - o GET responde `ligado: true`;
  - a pergunta de agora volta sem chamar a IA;
  - com uma chave falsa, a API da Anthropic respondeu "chave inválida" e a função devolveu
    `{"erro":"chave"}`.

**Ainda não foi feita nenhuma chamada real** (não há chave aqui). A primeira pergunta depois de ligar é o
teste de verdade.
