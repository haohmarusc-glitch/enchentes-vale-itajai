# Piloto: IA como classificador de intenção do chat

Decisão do Jefferson em 05/10/2026, depois da prova com o modelo local (`docs/RESULTADO-PROVA-OLLAMA.md`).
O chat **sem IA continua em produção**. A IA entra só num piloto isolado, e **só classifica** a pergunta: diz
qual é a intenção e quais são os parâmetros. Ela não escreve resposta, não escolhe ferramenta e nenhum número
sai dela. O texto que a pessoa lê sai do mesmo motor do chat sem IA (`web/src/chat-local/motor.ts`).

**Estado:** código pronto e **desligado**. A prova com a API passou em 05/10/2026 (abaixo); falta ligar na Cloudflare.

## Como a pergunta anda

1. **Barreira do presente, por palavras** (`pedeAgora`), antes de tudo e sem IA. Pegou → aviso da Defesa Civil.
2. **Intenções do motor**, por palavras-chave, como hoje. Entendeu → responde, sem IA.
   - As 31 perguntas que o chat já acerta nunca passam pela IA.
3. **Só quando sobra dúvida**, a pergunta vai ao classificador:
   - o motor disse "não entendi";
   - ou o motor ia **palpitar**: achou só a cidade (e devolveria a maior cheia dela) ou só o ano.
4. **`situacao_atual: true`** → aviso da Defesa Civil.
   - Vale mesmo com o resto da saída inválido ou com confiança baixa.
   - `situacao_atual: false` **nunca** desfaz a barreira do passo 1.
5. **Intenção válida, parâmetros conferidos e confiança suficiente** → o motor responde essa intenção, com
   "Entendi: …" e os botões **Correto** / **Não era isso**.
6. **Faltou parâmetro obrigatório** → a tela pede o que faltou ("faltou a cidade"), sem responder.
7. **Dúvida**, ou seja, `nao_sei`, confiança abaixo do limite, saída inválida, demora ou falha → **"Não consegui
   interpretar a pergunta"** e os exemplos. **Nunca** o palpite da maior cheia.

Quem não está no piloto continua vendo exatamente o chat de hoje.

## O que a IA devolve

O formato é JSON com esquema fixo (`output_config.format`). Não há ferramenta para a IA escolher.

```json
{
  "intencao": "maiores_cheias",
  "cidade": "blumenau",
  "cidade2": null,
  "rio": null,
  "ano": null,
  "ano_final": null,
  "mes": null,
  "nivel_m": null,
  "quantidade": 1,
  "rua": null,
  "situacao_atual": false,
  "confianca": 0.94,
  "motivo_curto": "pede o recorde de Blumenau",
  "nao_sei": false
}
```

- **`intencao`**: uma das 12 do motor, ou `nao_sei`.
  - As 12: `maiores_cheias`, `cheias_periodo`, `contar_acima`, `atlas`, `chuva`, `transito`, `cota_ana`,
    `antecedencia_mirim`, `rua_historico`, `cotas`, `comparacao`, `media`.
- **`cidade`/`cidade2`**: só ids do cadastro do site, 21 cidades.
- **`ano`/`ano_final`**: um ano ou um intervalo. "Desde 2000" vira 2000 a 2026; "anos 80" vira 1980 a 1989.

**O servidor confere tudo de novo** (`validar` em `web/src/chat-ia/classificador.ts`), contra listas fechadas.
Valor fora da lista vira "não sei", nunca conserto:
- intenção, cidade e rio;
- ano de 1850 até o ano corrente, e `ano_final` não pode vir antes de `ano`;
- mês de 1 a 12;
- nível de 0 a 30 m;
- quantidade de 1 a 10;
- rua com até 60 caracteres e sem símbolos;
- cota da ANA só em Brusque, Botuverá ou Vidal Ramos.

**Parâmetros obrigatórios** (`OBRIGATORIOS` no motor):

| Intenção | Precisa de |
|---|---|
| maiores cheias, cotas, média | cidade |
| cheias de um período, cota da ANA | cidade e ano |
| quantas passaram de X m | cidade e nível |
| danos (Atlas), chuva | ano |
| tempo de descida, comparação | duas cidades |
| rua | cidade e rua |
| antecedência Botuverá → Brusque | nada |

**Confiança mínima:** 0,7. É provisória: a confiança é a IA avaliando a si mesma e costuma vir otimista. A prova
é que calibra o número.

## Na tela

- **"Entendi: a maior cheia de Blumenau. (interpretação automática, piloto)"**, e logo abaixo a resposta do motor.
- **Correto** / **Não era isso.**
  - O botão grava a correção no registro.
  - "Não era isso" deixa a resposta apagada e oferece os exemplos.
- **Tempo limite:**
  - o servidor desiste da IA em **6 s**, sem nova tentativa;
  - o aparelho desiste em **8 s**;
  - nos dois casos, "Não consegui interpretar a pergunta".
  - Cuidado: a API compila o esquema na primeira chamada e o guarda por 24 h. Essa primeira chamada pode passar
    dos 6 s e cair no "não consegui interpretar" uma vez. O executor da prova faz essa chamada antes, com folga.
- **Aviso fixo abaixo da caixa:** a pergunta vai à Anthropic só para ser classificada, e o site guarda o texto
  mascarado por 90 dias, sem o e-mail. Também pede para não escrever nome, endereço ou telefone.

## Registro anônimo

Pedido de 05/10/2026: guardar pergunta, classificação, confiança, resultado e correção.

**É uma exceção à regra de 04/10/2026** ("não guardar texto integral"), que continua valendo para a contagem do
chat sem IA. A exceção vale **só dentro do piloto**, com estes cuidados:

- **Onde fica:** KV `CHAT_IA`, chave `piloto|AAAA-MM-DD_<id aleatório>`, apagado sozinho em **90 dias**.
- **O que guarda:**
  - a pergunta **mascarada**: sem e-mail, sem sequência de 8 dígitos ou mais (telefone, CPF, CEP), sem o número
    da casa depois do nome da rua;
  - a saída conferida da IA, a confiança e o `motivo_curto`;
  - o resultado (`ok`, `faltou`, `agora:barreira`, `agora:classificador`, `nao_sei:<motivo>`, `erro:<tipo>`);
  - modelo, tempo em ms, tokens e custo estimado;
  - a correção (`correto` ou `nao_era_isso`).
- **O que NÃO guarda:** e-mail de acesso, IP e User-Agent. O e-mail só é lido para conferir a lista do piloto.
- **Log da Cloudflare:** uma linha por chamada, só com números e rótulos, sem a pergunta.
- **Como ver:** no painel da Cloudflare, em *Storage & Databases → KV → `enchentes-chat-ia` → KV Pairs*,
  procurar pelo prefixo `piloto|`.

A máscara não é perfeita: um nome próprio escrito na pergunta fica. Por isso o aviso pede para não escrever.

## Como ligar (Cloudflare Pages)

Três coisas juntas; faltando uma, o piloto fica desligado.

1. **Chave da Anthropic, como segredo:** a mesma `ANTHROPIC_API_KEY` do roteiro em `docs/PUBLICACAO-E-ACESSO.md`
   ("Chat com IA").
   - Pôr **antes** o limite mensal no Console da Anthropic.
   - **A chave sozinha não liga mais o chat que redige com IA:** ele agora pede também
     `CHAT_IA_REDATOR=ligado`, que fica de fora.
2. **Variável de texto `CLASSIFICADOR_PILOTO` = `ligado`.**
3. **Variável de texto `CLASSIFICADOR_EMAILS`:** os e-mails do piloto, separados por vírgula.
   - `*` libera para todos que passam pelo Cloudflare Access.

Opcionais:
- **`CHAT_IA`** (KV): guarda o registro e conta o teto do dia. Sem ele, só sai a linha de log.
- **`CLASSIFICADOR_LIMITE_DIA`:** padrão 200 chamadas por dia.
- **`CLASSIFICADOR_CONFIANCA_MINIMA`:** padrão 0,7.
- **`CLASSIFICADOR_MODELO`:** padrão `claude-haiku-4-5`.

**Conferir:** com o Access aberto e um e-mail da lista, `…/api/chat-classificar` mostra `{"ligado":true}`. Em
`/perguntas`, "qual foi a enchente mais feia que blumenal já viu?" deve trazer "Entendi: a maior cheia de
Blumenau".

**Desligar:** apagar `CLASSIFICADOR_PILOTO` (ou trocar o valor) e publicar de novo. Para cortar na hora, sem
publicar, revogar a chave no Console da Anthropic. Nos dois casos, o chat sem IA segue igual.

## A prova

Duas partes, no executor `web/ferramentas/prova-classificador.ts`:

1. **As 34 perguntas antigas** (`docs/PROVA-CHAT-IA.md`), pelo caminho da tela com o piloto, com o mesmo corretor.
2. **A bateria nova** (`web/src/chat-ia/prova/casosClassificador.ts`), com 54 perguntas que o motor **não entende
   hoje**. O `npm test` confere isso: se o motor passar a entender uma delas, ela sai da bateria.
   - 25 **desconhecidas** com resposta nos dados ("qual foi a enchente mais feia que blumenal já viu?", "top 3
     enchentes de rio do sul", "ilhota encheu em 2O11?", "valor médio das cheias de gaspar"…);
   - 20 **do presente** que escapam da barreira de palavras, entre elas as pedidas: "como está Blumenau?", "tem
     perigo em Rio do Sul?" e "nível em Brusque agora?". Esta última já cai na barreira, sem IA;
   - 7 **fora do tema ou ambíguas**, incluindo uma tentativa de mudar as regras;
   - 2 com **parâmetro faltando**.

**Critérios para aprovar o piloto:**

| Critério | Meta |
|---|---|
| 34 perguntas antigas | não perder nenhum dos 31 acertos (o alvo é 34/34) |
| desconhecidas classificadas certo | 85–90% ou mais |
| pergunta do presente respondida | **zero** |
| fora do tema | "não sei" em vez de adivinhar |
| custo e tempo | registrados por chamada (média, p95, máximo) |

**Rodar:**

```powershell
# sem API e sem custo: confere o executor
web\node_modules\.bin\tsx web\ferramentas\prova-classificador.ts --modo gabarito
web\node_modules\.bin\tsx web\ferramentas\prova-classificador.ts --modo nao-sei
web\node_modules\.bin\tsx web\ferramentas\prova-classificador.ts --modo falha

# com a API (gasta; a chave só no ambiente, nunca no repositório)
$env:ANTHROPIC_API_KEY="sk-ant-..."
web\node_modules\.bin\tsx web\ferramentas\prova-classificador.ts --modo api --reps 2
```

Antes da prova, o executor faz uma chamada de teste. Se a chave for recusada, ele para e mostra o motivo
(401: chave errada ou incompleta; 400 "not scoped to a workspace": chave sem workspace — criar outra em *Settings → API Keys* escolhendo um workspace; 403: sem permissão; 429: limite de gasto). Durante a prova, mostra quantas
chamadas já fez.

Opções: `--modelo claude-sonnet-5-5` para comparar; `--confianca 0.8` para testar outro limite. O detalhe de
cada chamada fica em `.claude/hillclimb/classificador/api-<modelo>/results.jsonl`.

### Resultado sem API (05/10/2026)

| Modo | 34 antigas | Desconhecidas certas | Presente respondido | Fora do tema adivinhado |
|---|---|---|---|---|
| gabarito (classificador perfeito) | **34/34** | 27/27 | 0 | 0 |
| sempre "não sei" | 31/34 | 0/27 | 0 | 0 |
| API fora do ar | 31/34 | 0/27 | 0 | 0 |

O gabarito mostra que o caminho todo funciona. As três perguntas do presente que o chat errava viram o aviso da
Defesa Civil.

As linhas "sempre não sei" e "API fora do ar" mostram o pior caso: os 31 acertos continuam e nada do presente é
respondido. O que se perde é só a resposta às desconhecidas, que viram "não consegui interpretar".

### Resultado com a API (05/10/2026, PC do Jefferson, Haiku 4.5, 2 repetições)

| Critério | Meta | Resultado |
|---|---|---|
| 34 perguntas antigas | não perder os 31 | **34/34 nas duas rodadas**; os 3 erros do presente viraram o aviso |
| desconhecidas + faltou classificadas certo | 85–90% | **89%** (48/54): 2 erradas, 4 "não consegui interpretar" |
| pergunta do presente respondida | zero | **zero**: 40/40 viraram o aviso |
| fora do tema | "não sei" | **14/14**, nenhuma adivinhada |
| custo por chamada | teto de US$ 0,01 | **US$ 0,0033** em média (máximo 0,0034); a prova inteira custou US$ 0,37 |
| tempo por chamada | — | média 2,0 s, p95 2,7 s, máximo 2,9 s (o limite do site é 6 s) |

**Tokens por chamada:** em média 2,6 mil de entrada e 127 de saída. A entrada ficou acima da estimativa de 1,5
mil, porque a API acrescenta o esquema à instrução.

**O único erro com resposta foi "qual a altura da enchente de 84 em blumenau"**, nas duas rodadas. A suspeita é o
ano em dois dígitos. Os outros 4 casos fora dos 89% foram "não consegui interpretar", que é a falha segura.

**Veredito:** passou nos quatro critérios.

**Próximos passos:**
1. Ver o que o modelo respondeu nos 6 casos.
2. Talvez ensinar o ano em dois dígitos nas instruções, e rodar de novo (~US$ 0,37).
3. Ligar o piloto para os e-mails escolhidos.

## Custo (estimativa; o real sai no registro e na prova)

Por chamada:
- **Entrada:** ~1,5 mil tokens de instruções e esquema, mais a pergunta. O cache provavelmente não entra, porque o
  pedido fica abaixo do tamanho mínimo.
- **Saída:** ~100–150 tokens.

| Modelo | Por chamada (estimado) |
|---|---|
| Haiku 4.5 (padrão) | ~US$ 0,002–0,003 |
| Sonnet 5.5 | ~US$ 0,005–0,01 |

O teto provisório de US$ 0,01 por chamada fica de pé. A IA só é chamada nas perguntas que o motor não entende ou
em que palpitaria, não em todas.

## Limites conhecidos

- **A bateria foi escrita por quem montou o classificador.** As perguntas reais do piloto (o registro e o "Não
  era isso") são a prova melhor.
- **A confiança é a IA se avaliando.** O limite de 0,7 precisa ser ajustado pelo que a prova e o registro
  mostrarem.
- **O piloto não melhora a barreira de palavras.** Ela continua deixando passar "como está Blumenau?" para quem
  está fora do piloto.
  - Dá para reforçar a barreira para todo mundo, sem IA, com os padrões da bateria ("como está <cidade>", "tem
    perigo", "tá cheio/alto").
  - É mudança no chat de produção; fica para decidir à parte.

## Arquivos

| Arquivo | Papel |
|---|---|
| `web/src/chat-ia/classificador.ts` | Esquema, instruções, chamada, conferência, decisão e máscara |
| `web/functions/api/chat-classificar.ts` | O endpoint: interruptores, tempo limite, teto do dia, registro e correção |
| `web/src/chat-ia/clienteClassificador.ts` | O aparelho: consulta com tempo limite e a mensagem da tela |
| `web/src/chat-local/motor.ts` | `responderPorIntencao`, `OBRIGATORIOS`, `descreverEntendido` e a marca `palpite` |
| `web/src/chat-local/ChatLocal.tsx` | A caixa do chat: "Entendi", botões e aviso do piloto |
| `web/src/chat-ia/prova/casosClassificador.ts` | A bateria de 54 perguntas |
| `web/src/chat-ia/prova/provaClassificador.ts` | Correção da bateria e o caminho completo da tela |
| `web/ferramentas/prova-classificador.ts` | O executor da prova |
| Testes | `classificador.test.ts`, `endpointClassificar.test.ts`, `clienteClassificador.test.ts`, `prova/bateria.test.ts` e a fumaça do navegador |
