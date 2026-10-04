# Quem pode ver o site, e quando — opções e custos reais

Pedido (05/09/2026): *"preciso que só eu possa usar o site; só deixar público quando estiver pronto, eu
decido quando; mas preciso dar autorização para alguma autoridade que pedir."*

**É possível, e existe caminho gratuito.** Este documento registra o estado de hoje, as opções e o que
cada uma custa — para a escolha ser feita com os números na mesa, não por impressão.

---

## ✅ O DESENHO ESCOLHIDO — montado em 06/09/2026

| camada | o quê |
|---|---|
| endereço | **`enchentes.premercadosc.com`** |
| quem serve | **Cloudflare Pages**, projeto `enchentes-vale-itajai`, build automático do `main` |
| quem protege | **Cloudflare Access**, aplicação `enchentes`, política **"Autorizados"** (Action: Allow → Emails; chamava-se "Só eu" até 26/09/2026) |
| plano | **Zero Trust Free** (equipe `orange-glade-ea3f`) — sem custo |
| login | **código de uso único por e-mail**. Quem entra NÃO precisa de conta na Cloudflare |
| GitHub Pages | **despublicado**, e o fluxo `pages.yml` virou **só manual** |

### ✅ FECHADO E CONFERIDO em 06/09/2026 — as quatro portas

**O site não está mais acessível a ninguém além de quem você autorizar.** As quatro conferências foram
feitas em janela anônima, uma a uma.

Não existe um botão só. Foram quatro sistemas diferentes, e a própria Cloudflare avisa na tela:
*"This protects preview deployment URLs only. Production pages.dev and custom domains are managed
separately in Zero Trust."*

| porta | como se fechou | conferido |
|---|---|---|
| `enchentes.premercadosc.com` | destino da aplicação `enchentes` no Access | ✅ pede e-mail |
| `enchentes-vale-itajai.pages.dev` | **segundo destino** na MESMA aplicação (Subdomain vazio, Domain com o endereço inteiro) | ✅ pede e-mail |
| `*.enchentes-vale-itajai.pages.dev` (pré-visualizações) | Pages → Settings → **General → Preview access → Restrict previews** | ✅ pede e-mail |
| GitHub Pages | Settings → Pages → **Unpublish site** + `pages.yml` só manual | ✅ 404 |

**Três armadilhas que custaram tentativas, para não se repetirem:**

1. **O destino do Access é EXATO, não cobre subdomínios.** Cadastrar
   `enchentes-vale-itajai.pages.dev` **não** protege
   `claude-projeto-critico-segur.enchentes-vale-itajai.pages.dev` — medido: continuou abrindo sem pedir
   e-mail. As pré-visualizações precisam do `Restrict previews`, que é outro lugar.
2. **O campo `pages.dev` vai no Domain, com o Subdomain VAZIO.** Preenchido nos dois, monta
   `x.pages.dev.x.pages.dev`, um endereço que não existe — e a tela **salva assim sem reclamar**,
   parecendo protegida.
3. **A tela do `Restrict previews` disse "Access policy could not be created" E "previews are
   restricted" ao mesmo tempo.** O teste em janela anônima provou que estava protegido. **Mensagem de
   painel não é conferência.**

**A conferência tem de ser em JANELA ANÔNIMA.** Na janela normal a sessão do Access já está aberta e
tudo carrega, dando a impressão de que o site está liberado para todo mundo.

### Quando este documento precisa ser relido

- **Antes de dizer a alguém que o site está fechado.** A tabela acima é de 06/09/2026; portas novas
  aparecem sozinhas (foi o caso das pré-visualizações, que nasceram com o projeto no Cloudflare).
- **Se um dia alguém trocar o Cloudflare por outro serviço.** As quatro portas são de sistemas
  diferentes; trocar um deixa os outros três abertos.
- **Antes de publicar de vez.** Remover a política é um clique, e é irreversível na prática: o endereço
  já terá sido visto.

### Como AUTORIZAR uma autoridade que pedir
**Pelo terminal da VPS (desde 25/09/2026), um comando:**

```bash
python3 scripts/autorizar_email.py fulano@gmail.com            # autoriza
python3 scripts/autorizar_email.py --revogar fulano@gmail.com  # revoga
python3 scripts/autorizar_email.py --listar                    # quem entra hoje
python3 scripts/autorizar_email.py --renomear NOVO_NOME        # renomeia a política
```

O script lê a política, muda **só** a lista de e-mails (decisão, exclusões e duração da sessão ficam
como estão) e **relê para conferir** — resposta 200 da API não é prova. Recusa revogar o **último**
e-mail (trancaria o site para todo mundo) e não mexe em regra que não seja e-mail. A pessoa entra
digitando o e-mail no site e recebendo o código; sessão já aberta de quem foi revogado dura até expirar.

**Configuração, uma vez só**, no `.env` da VPS (modelo no `.env.example`): `CLOUDFLARE_API_TOKEN` —
painel da Cloudflare → *My Profile → API Tokens → Create Token → Custom*, com **uma** permissão de conta,
*Access: Apps and Policies — Edit*, e nada mais — e `CLOUDFLARE_ACCOUNT_ID`. O Account ID é o bloco de
32 caracteres que aparece no link do painel que o bot da Cloudflare Pages comenta em todo PR
(`dash.cloudflare.com/?to=/<account-id>/pages/view/...`). Opcional:
`CLOUDFLARE_ACCESS_POLICY_ID`, se o script não achar a política pelo nome ("Autorizados" ou "Só eu").
✅ **Conferido na conta real em 26/09/2026**, na VPS: `--listar` devolveu a política com o e-mail do
Jefferson, igual ao painel, e `--renomear Autorizados` trocou o nome de "Só eu" (relido pelo script).
A política é **reutilizável** (achada em `/access/policies`, não dentro da aplicação).

**Pelo painel**, se preferir: Zero Trust → **Access controls → Applications → `enchentes` → política
"Autorizados"** → em *Include / Emails*, acrescentar o e-mail. Ela recebe
um código por e-mail e entra. **Revogar é apagar a linha.** As pré-visualizações (`*.pages.dev`) têm
política própria em *Pages → Settings → General → Preview access*; o script não mexe nelas.

### Como PUBLICAR de vez, quando decidir
Remover a política da aplicação (ou apagar a aplicação). O site fica aberto **no mesmo endereço**, sem
mexer em build, DNS ou código.

### ⚠️ As portas que precisam ficar fechadas
1. **GitHub Pages** — despublicado. **E o gatilho do fluxo foi removido**: `pages.yml` só roda por
   `workflow_dispatch`. Sem isso, o próximo merge no `main` republicaria o endereço sozinho, e a porta
   recém-fechada voltaria a abrir sem ninguém perceber, porque nada falharia.
2. **`enchentes-vale-itajai.pages.dev`** — o endereço que o Cloudflare Pages dá de fábrica **continua
   público** e serve o mesmo site. Proteger o domínio próprio NÃO o fecha. Tentar acrescentá-lo como
   segundo destino da mesma aplicação (*Add public hostname → Switch to custom input*, ou *Add Workers*);
   uma aplicação aceita até cinquenta destinos, então ele fica sob a mesma política.
3. **Pré-visualizações de PR** — cada PR gera um endereço `*.pages.dev` próprio. Em Pages → Settings há
   uma política de acesso para *preview deployments*; vale ligar.

### O que continua público, de propósito
O **repositório** e o branch **`tempo-real`**. Fechá-los quebraria o nível ao vivo (ver opção D abaixo),
e o dado vem de fontes públicas — Defesa Civil e rede estadual. O pedido é sobre o site.

O branch **`coleta-gaspar`** (desde 04/10/2026) também fica público, pelo mesmo motivo: o GitHub Actions
grava ali a leitura da estação 21 de Gaspar e o HTML público de onde ela saiu, e a VPS lê o arquivo por
`raw.githubusercontent.com` (`scripts/gaspar_actions.py`, `.github/workflows/coletar-gaspar.yml`). Não
há credencial nem dado pessoal nele. Operação em `docs/gaspar-ponte-pc.md`.

### Modo aplicativo (instalar no celular) — decisão D5, 03/10/2026
O site instala como aplicativo (manifesto `web/public/manifest.webmanifest`) e guarda uma cópia no
aparelho por um *service worker* (`web/public/sw.js`, regras em `web/public/sw-regras.js`).

- **Rede primeiro.** Com internet, tudo vem da rede, como antes; só os arquivos com hash no nome
  (`assets/…-AbC123.js`), que nunca mudam, vêm do aparelho. **Sem internet**, abre a última cópia
  guardada e mostra o último nível guardado, com a hora da medição — o site já marca leitura velha como
  "não use como nível atual" — e o aviso "Sem conexão". O nível ao vivo espera a rede 2,5 s antes de
  cair na cópia (o site desiste aos 3 s).
- **Atrás do Access, dois cuidados já no código:** o manifesto é pedido com
  `crossorigin="use-credentials"` (sem isso o navegador o pede sem o cookie, recebe o desvio para o
  login e o site não instala); e o service worker **nunca guarda** desvio, resposta opaca, nada de
  `*.cloudflareaccess.com`, nem HTML no lugar de JS/JSON — senão a tela de login viraria "o site" naquele
  aparelho. O teste `web/testes-navegador/pwa.mjs` (na CI) simula a sessão vencida e confere isso.
- **Sessão vencida:** com internet, a pessoa vê o login do Access como sempre; sem internet, vê a cópia
  guardada (que ela já tinha visto com sessão válida).
- **Versão nova:** o service worker novo assume na hora; a aba aberta mostra "Há uma versão nova do site
  · Atualizar agora". Abas abertas conferem a cada 30 min.
- **INTERRUPTOR — se algo der errado:** trocar `"ativo": true` por `"ativo": false` em
  `web/public/pwa.json` e publicar. Na próxima abertura de cada aparelho com internet, o service worker
  apaga tudo o que guardou, se desregistra e recarrega a página; o site volta a funcionar como antes do
  modo aplicativo. Para religar, voltar a `true`.
- **Conferir em produção:** em janela anônima (sessão nova do Access), abrir o site, entrar, e no
  Chrome do Android ver "Instalar app"/"Adicionar à tela inicial"; depois, em modo avião, abrir o ícone.
  No iPhone a instalação é por Compartilhar → Adicionar à Tela de Início.
- O **Monitor** funciona sem internet pela mesma cópia, mas não ganhou avisos nem barra nova (D2).

### Contagem do chat (perguntas não entendidas) — decisão de 04/10/2026
O que é contado e o que não é: `docs/TELEMETRIA-CHAT.md`. O código está pronto e **desligado**: a
função `web/functions/api/chat-nao-entendi.ts` responde `contando: false` e não grava nada enquanto o
projeto Pages não tiver o binding de KV `CHAT_NAO_ENTENDI`. O site só mostra o aviso e só envia quando
essa resposta diz `true` — **o binding é o único interruptor**.

**Para LIGAR (uma vez, pelo painel da Cloudflare):**

1. **Conferir onde fica a pasta `functions/`.** O Pages procura `functions/` no *Root directory* do
   build. Em *Workers & Pages → `enchentes-vale-itajai` → Settings → Build → Build configuration*, ver
   o **Root directory**:
   - `web` → a pasta já está no lugar (`web/functions/`). Nada a fazer.
   - vazio (raiz do repositório) → a função **não será achada**. Pedir para mover `web/functions/` para
     `functions/` na raiz (e ajustar os dois `import` relativos do arquivo); não mover à mão sem rodar
     `npm test`.
2. **Criar o armazenamento:** *Storage & Databases → KV → Create namespace* → nome
   `enchentes-chat-nao-entendi`.
3. **Ligar ao site:** *Workers & Pages → `enchentes-vale-itajai` → Settings → Bindings → Add → KV
   namespace* → *Variable name* **`CHAT_NAO_ENTENDI`** (exatamente assim) → namespace
   `enchentes-chat-nao-entendi`. Fazer em **Production**; em *Preview* só se quiser contar também as
   pré-visualizações (não recomendado: misturaria testes com uso real).
4. **Publicar de novo** (*Deployments → … → Retry deployment* no último do `main`, ou o próximo merge):
   binding só vale para deploy feito depois dele. No log do build deve aparecer que a pasta de Functions
   foi encontrada e enviada.
5. **Conferir**, com a sessão do Access aberta no navegador, abrindo
   `https://enchentes.premercadosc.com/api/chat-nao-entendi`: deve mostrar
   `{"contando":true,"retencao_dias":90}`. Depois, na página de uma cidade, a caixa do chat passa a
   mostrar a opção "Contar as perguntas que o chat não entender". Perguntar algo sem sentido ("me conta
   uma piada") e, em *KV → `enchentes-chat-nao-entendi` → KV Pairs*, ver a linha
   `AAAA-MM-DD|desconhecida|sem_intencao|-` com `1`.

**Para DESLIGAR:** remover o binding `CHAT_NAO_ENTENDI` (passo 3) e publicar de novo. Para apagar
também os números, apagar o namespace. Sem binding, a página volta a não mostrar nada da contagem.

**Atrás do Access:** a rota `/api/chat-nao-entendi` fica sob a mesma aplicação `enchentes` — só quem
entra no site consegue enviar. A função não lê o e-mail que o Access repassa nem o IP. O service worker
não se mete em `/api/…` (`sw-regras.js`, com teste). Custo: plano gratuito do Workers/KV (100 mil
chamadas de função e mil gravações de KV por dia — muito acima do uso de um chat de histórico); as
Functions só rodam nessa rota, o resto do site continua estático.

### Chat com IA (`/api/chat-ia`) — pedido de 04/10/2026
O que faz, o que vai à Anthropic e quanto custa: `docs/CHAT-IA.md`. O código está pronto e
**desligado**. O **segredo `ANTHROPIC_API_KEY`** é o interruptor: sem ele, o GET diz `ligado: false` e o
botão "Perguntar à IA" não aparece.

**Para LIGAR (uma vez):**

1. **Root directory `web`:** o mesmo passo 1 da contagem do chat, acima.
2. **Criar a chave da Anthropic.**
   - Em `https://console.anthropic.com` → *API Keys → Create Key*, nome `enchentes-site`.
   - **Antes de usar, pôr o limite mensal** em *Settings → Limits*, por exemplo US$ 20. É ele que
     garante o bolso.
   - A chave **não** vai para o repositório nem para e-mail.
3. **Guardar como segredo no Pages.**
   - Caminho: *Workers & Pages → `enchentes-vale-itajai` → Settings → Variables and Secrets → Add*.
   - *Type* **Secret**, *Variable name* **`ANTHROPIC_API_KEY`**, valor = a chave.
   - Em **Production**.
4. **(Opcional, recomendado) Teto do dia.**
   - Criar o namespace KV `enchentes-chat-ia`.
   - Ligar com o *Variable name* **`CHAT_IA`**.
   - Se quiser outro teto, criar a variável de texto `CHAT_IA_LIMITE_DIA`. O padrão é 50 perguntas por
     dia no site todo.
5. **(Opcional) Trocar o modelo.**
   - Variável de texto `CHAT_IA_MODELO`.
   - Vazio = `claude-opus-5-5`; `claude-sonnet-5-5` sai pela metade do preço.
6. **Publicar de novo** (*Retry deployment* ou o próximo merge).
7. **Conferir.**
   - Com o Access aberto, `https://enchentes.premercadosc.com/api/chat-ia` deve mostrar
     `{"ligado":true}`.
   - Na página `/perguntas`, perguntar "Qual foi a maior cheia de Gaspar?" e apertar **Perguntar à IA**.
   - A resposta chega com o rótulo da IA.
   - No Console da Anthropic, em *Usage*, aparece o gasto da pergunta.

**Para DESLIGAR:** apagar o segredo `ANTHROPIC_API_KEY` e publicar de novo; o botão some. Para cortar na
hora, sem publicar: **revogar a chave** no Console. A IA passa a responder "desligada" e o chat local
continua.

---

## O estado de hoje (conferido em 05/09/2026)## O estado de hoje (conferido em 05/09/2026)

| o quê | como está |
|---|---|
| repositório | **público** (`visibility: public`) |
| site | **GitHub Pages, público** — qualquer pessoa com o endereço abre |
| código | público junto com o repositório |
| dados ao vivo | branch `tempo-real`, lidos pelo navegador em `raw.githubusercontent.com` |

**Não há nenhuma barreira de acesso hoje.** Quem tiver o endereço, entra.

## ⚠️ A ressalva que decide tudo: senha em site estático não existe

Um "campo de senha" numa página do GitHub Pages **não protege nada**. O site é um punhado de arquivos
que o servidor entrega a quem pedir; a senha estaria dentro do próprio arquivo que a pessoa baixou, e o
conteúdo pode ser lido sem nunca abrir a tela de login. Isso não é opinião de estilo: é como a web
estática funciona. Proteção de verdade exige um servidor que **recuse a entrega** antes de mandar o
arquivo.

Por isso as opções abaixo passam todas por trocar quem entrega o site, ou por desligá-lo.

---

## As opções

### A) Desligar o site agora, publicar quando decidir — **grátis, imediato, reversível**
GitHub → **Settings → Pages → Source: None**. O endereço deixa de responder na hora.

- ✅ resolve "só deixar público quando eu decidir"
- ✅ **nada mais para de funcionar**: a coleta de 15 min na VPS, o branch `tempo-real`, os testes e a CI
  seguem iguais — o Pages é só a vitrine
- ❌ **não** resolve "dar autorização para uma autoridade": não há a quem liberar, o site está fora do ar
  para todos, inclusive para você

Serve como **primeiro passo hoje**, e combina com a opção B depois.

### B) Cloudflare Access na frente do site — **grátis até 50 pessoas**, é o que atende ao pedido inteiro
O site passa a ser servido pelo Cloudflare (Pages, ou a própria VPS por trás de um túnel) e o Cloudflare
**exige identificação antes de entregar a página**. Você cadastra e-mails; cada pessoa recebe um código
de uso único por e-mail e entra. Sem e-mail na lista, não entra.

- ✅ **só você** enquanto só o seu e-mail estiver na lista
- ✅ **autoridade que pedir**: acrescenta o e-mail dela, e ela entra. Tirar depois é remover a linha
- ✅ **publicar** é apagar a política de acesso — um clique, sem mexer no site
- ✅ registra quem entrou e quando, o que é bom quando a Defesa Civil está avaliando o projeto
- ⚠️ **a conferir antes de escolher**: preciso da documentação atual da Cloudflare para o limite gratuito
  e para proteger um endereço `*.pages.dev` sem domínio próprio. **Não tenho acesso à internet neste
  ambiente**, então isto é conhecimento anterior, não verificação de hoje
- ⚠️ pode exigir um **domínio próprio** (algo como R$ 40–60 por ano), a confirmar

### C) Proteção de senha da Vercel ou da Netlify — **paga**
Funciona e é simples, mas é senha única compartilhada (não dá para tirar o acesso de uma pessoa só) e
está nos planos pagos das duas.

### D) Repositório privado — **resolve o CÓDIGO, e QUEBRA os dados ao vivo**
Deixar o repositório privado esconde o código, mas o site busca o nível do rio em
`raw.githubusercontent.com`, que **só responde a repositório público**. Em repositório privado seria
preciso um token — e token dentro de um site que roda no navegador **é público por definição**, então
não serve.

Se um dia o código precisar ser privado, o caminho é a **VPS servir os JSON** (ela já roda a coleta) ou
um armazenamento próprio. É trabalho, não uma chave para virar.

**Vale separar as duas coisas:** os dados de nível vêm de fontes públicas (Defesa Civil, rede estadual)
e continuarem públicos não expõe nada de ninguém. O pedido é sobre **o site**, e o site é o que a
opção B fecha.

---

## Recomendação

1. **Hoje, grátis:** desligar o Pages (opção A). Tira o site do ar em segundos e não atrapalha nada.
2. **Quando quiser mostrar a alguém:** montar a opção B, que é a única que atende às três coisas ao
   mesmo tempo — só você, autorizar quem pedir, e publicar quando decidir.
3. **Deixar o repositório público** por enquanto: o código aberto não é o que o pedido protege, e
   fechá-lo quebra o dado ao vivo.

## O que NÃO fazer

- **Senha na página.** Não protege, e dá a sensação de que protege — que é pior que não ter.
- **Endereço secreto.** Um endereço difícil de adivinhar continua público para quem o receber por
  encaminhamento, e ele será encaminhado.
- **Desligar a coleta** junto com o site. São coisas separadas: manter a coleta rodando enquanto o site
  está fora do ar preserva a série histórica, que não se recupera depois.
