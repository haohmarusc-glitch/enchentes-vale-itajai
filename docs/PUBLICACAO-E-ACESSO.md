# Quem pode ver o site, e quando — opções e custos reais

Pedido (05/09/2026): *"preciso que só eu possa usar o site; só deixar público quando estiver pronto, eu
decido quando; mas preciso dar autorização para alguma autoridade que pedir."*

**É possível, e existe caminho gratuito.** Este documento registra o estado de hoje, as opções e o que
cada uma custa — para a escolha ser feita com os números na mesa, não por impressão.

---

## O estado de hoje (conferido em 05/09/2026)

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
