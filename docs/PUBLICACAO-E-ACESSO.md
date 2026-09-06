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
| quem protege | **Cloudflare Access**, aplicação `enchentes`, política **"Só eu"** (Action: Allow → Emails) |
| plano | **Zero Trust Free** (equipe `orange-glade-ea3f`) — sem custo |
| login | **código de uso único por e-mail**. Quem entra NÃO precisa de conta na Cloudflare |
| GitHub Pages | **despublicado**, e o fluxo `pages.yml` virou **só manual** |

### As QUATRO portas, e como cada uma se fecha (medido em 06/09/2026)

Não existe um botão só. Foram quatro sistemas diferentes, e a própria Cloudflare avisa na tela:
*"This protects preview deployment URLs only. Production pages.dev and custom domains are managed
separately in Zero Trust."*

| porta | como se fechou | conferido |
|---|---|---|
| `enchentes.premercadosc.com` | destino da aplicação `enchentes` no Access | ✅ pede e-mail |
| `enchentes-vale-itajai.pages.dev` | **segundo destino** na MESMA aplicação (Subdomain vazio, Domain com o endereço inteiro) | ✅ pede e-mail |
| `*.enchentes-vale-itajai.pages.dev` (pré-visualizações) | Pages → Settings → **General → Preview access → Restrict previews** | ✅ pede e-mail |
| GitHub Pages | Settings → Pages → **Unpublish site** + `pages.yml` só manual | a confirmar no navegador |

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

### Como AUTORIZAR uma autoridade que pedir### Como AUTORIZAR uma autoridade que pedir
Zero Trust → **Access controls → Applications → `enchentes` → política "Só eu"** → em *Include / Emails*,
acrescentar o e-mail. Ela recebe um código por e-mail e entra. **Revogar é apagar a linha.**

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
