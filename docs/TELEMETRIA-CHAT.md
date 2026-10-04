# Contagem das perguntas que o chat não entende

Decisão do Jefferson (04/10/2026): *"Contar somente evento agregado: intenção/categoria, cidade quando
necessária, data arredondada, motivo da falha e versão do sistema. Não guardar texto integral, IP,
localização precisa, nome, telefone ou identificador persistente. Oferecer exclusão/opt-out e definir
retenção curta."*

**Estado: implementado e DESLIGADO.** Só começa a contar quando o Jefferson criar o KV na Cloudflare
(passo a passo em `docs/PUBLICACAO-E-ACESSO.md`, seção "Contagem do chat"). Até lá, o site não envia
nada e não mostra aviso de contagem.

## O que é contado

Cada vez que o chat do histórico não entende uma pergunta, o aparelho manda **um evento** com
exatamente estas cinco chaves, e nenhuma outra:

| chave | o que é | exemplo |
|---|---|---|
| `categoria` | a intenção que o chat reconheceu, ou `desconhecida` | `atlas`, `maiores_cheias`, `rua_historico`, `desconhecida` |
| `motivo` | por que não respondeu (lista fechada) | `sem_intencao`, `faltou_cidade`, `faltou_ano` |
| `cidade` | id da cidade no cadastro (`data/estacoes.json`), **só se a pergunta citou**; senão `null` | `blumenau` |
| `dia` | o dia em Brasília, sem hora | `2026-10-04` |
| `versao` | a versão do site (package.json + commit do build), igual para todo mundo | `0.1.0+abc1234` |

Motivos:
- `sem_intencao` — nada casou; é a resposta "Não entendi a pergunta".
- `faltou_cidade` — o chat entendeu o tipo de pergunta, mas não a cidade ("qual a maior enchente?").
- `faltou_ano` — entendeu o tipo, mas faltou o ano ("quantos desabrigados em Blumenau?").

O servidor não guarda o evento: soma 1 num contador com a chave `dia|categoria|motivo|cidade`
(ex.: `2026-10-04|atlas|faltou_ano|blumenau` → `3`). É só isso que existe no armazenamento.

## O que NÃO é contado

- **O texto digitado**, inteiro ou em pedaços. Nenhuma função da contagem recebe o texto; o teste passa
  perguntas com nome, telefone, e-mail e endereço pelo motor e confere que nenhum trecho de 4 caracteres
  delas aparece no evento.
- IP, User-Agent, e-mail do Cloudflare Access, cookies, cabeçalhos: o servidor não lê nenhum deles para
  gravar (o único cabeçalho lido é `Sec-Fetch-Site`, para recusar envio de outro site, e não é guardado).
- Hora, localização, identificador do aparelho ou da sessão. Não há como ligar dois eventos à mesma
  pessoa.
- Cidade que não está no cadastro (ex.: Navegantes, que só aparece no Atlas) vira `null`, e o servidor
  recusa qualquer cidade fora do cadastro — texto livre não entra pela chave.
- Perguntas que o chat **entendeu**, inclusive as de "agora/previsão" (que recebem o texto fixo do 199).

O servidor recusa (400) qualquer corpo com chave a mais, a menos, valor fora das listas, dia com hora ou
longe de hoje (só ontem, hoje e amanhã) e corpo maior que 512 bytes.

## Retenção: 90 dias

Cada contador vive **90 dias** a partir da última soma (TTL do KV) e some sozinho. Como a chave tem o
dia, isso dá cerca de três meses de histórico corrido. Por quê 90: cobre uma temporada de chuva e dá
tempo de o Jefferson olhar os números uma vez por mês e corrigir o motor; mais que isso só acumularia
dado que ninguém lê. Para guardar um resumo por mais tempo, copiar os totais à mão para um documento.

## Desligar e "excluir"

- **Para uma pessoa:** a caixa do chat mostra, quando a contagem está ligada, a opção marcada
  "Contar as perguntas que o chat não entender" e o texto do que é e não é contado. Desmarcar para
  tudo naquele aparelho (fica em `localStorage`, chave `enchentes:chat-contagem`, via
  `web/src/logica/preferencias.ts`).
- **Padrão:** marcado (o Jefferson pediu *opt-out*, e o evento é anônimo e agregado), **exceto** quando
  o navegador pede para não rastrear (Global Privacy Control ou Do Not Track) ou não consegue guardar a
  escolha (janela anônima, armazenamento bloqueado) — aí começa desmarcado. Escolha feita pela pessoa
  vence o sinal do navegador.
- **Exclusão:** como o evento não tem identificador, **não existe dado de uma pessoa para apagar** — o
  contador `2026-10-04|desconhecida|sem_intencao|-` é de todo mundo junto. Não há fila no aparelho:
  cada evento é enviado uma vez (`sendBeacon`, ou `fetch` com `keepalive`), sem repetição, e perdido se
  falhar. Desmarcar é o que para tudo.
- **Para todo mundo:** tirar o binding `CHAT_NAO_ENTENDI` do projeto Pages (ou apagar o namespace). O
  endpoint passa a responder `contando: false`, o site deixa de enviar e de mostrar o aviso. Apagar o
  namespace apaga todos os contadores na hora.
- No máximo 10 eventos por página aberta, para ninguém inflar o contador sozinho.

## Como ler os números

Painel da Cloudflare → **Storage & Databases → KV** → namespace `enchentes-chat-nao-entendi` →
*KV Pairs*: cada linha é `dia|categoria|motivo|cidade` com o total. Pelo terminal (com o wrangler
autenticado):

```bash
npx wrangler kv key list --namespace-id <ID> --remote          # as chaves
npx wrangler kv key get "2026-10-04|desconhecida|sem_intencao|-" --namespace-id <ID> --remote
```

O que procurar: muito `sem_intencao` → tipo de pergunta que o motor não conhece (vale olhar os exemplos
da tela); muito `faltou_cidade`/`faltou_ano` numa categoria → a sugestão daquela intenção não está
clara. Uma versão nova com queda brusca indica que a mudança do motor funcionou.

Os números são aproximados: o KV não soma de forma atômica, e duas perguntas no mesmo instante podem
virar uma. Para "o chat não entende muito disto", serve.

## Onde está o código

| arquivo | papel |
|---|---|
| `web/src/logica/telemetriaChat.ts` | esquema fechado, `montarEvento`, `validarEvento`, chave do contador, envio |
| `web/src/chat-local/motor.ts` | marca `falha` (motivo + cidade citada) nas respostas que não entendem |
| `web/src/chat-local/ChatLocal.tsx` | pergunta ao servidor se está contando, opção de desmarcar, envio |
| `web/src/logica/preferencias.ts` | `contagemChatPermitida` / `gravarContagemChat` |
| `web/functions/api/chat-nao-entendi.ts` | Pages Function: GET (está contando?) e POST (soma 1) |
| `web/public/sw-regras.js` | o service worker não se mete em `/api/…` (nem POST nem GET) |
| `web/src/logica/telemetriaChat.test.ts`, `telemetriaChatEndpoint.test.ts` | as travas |
