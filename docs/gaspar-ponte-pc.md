# Gaspar: coleta pelo PC e entrega à VPS

O portal municipal responde no PC, mas a VPS não estabelece TCP com
186.250.184.3:443. DNS funciona; a falha precede TLS. A causa de rede não foi
determinada. Esta ponte transporta somente a leitura municipal da estação 21.

No PC, com Python, dependências do coletor e acesso SSH já configurado:

```powershell
python scripts/enviar_gaspar_pc.py --vps root@65.108.154.111
```

O envio confirma acesso ao portal, confere o título da estação 21 e envia JSON
pelo stdin do SSH. A chave e a senha não entram no código. Exige chave do host
já conhecida e autenticação não interativa. O arquivo é escrito atomicamente
em `/opt/enchentes-vale-itajai/data/tempo-real/gaspar-pc.json`.

O coletor da VPS aceita esse arquivo quando a consulta pelo PC tem até 30 min
e a medição municipal tem até 3 h (limite geral de leitura velha do monitor).
Datas futuras, estação/cidade/rio/fonte diferentes, números inválidos e arquivo
ilegível são recusados. A medição conserva o horário de Brasília sem fuso;
o horário da consulta é UTC. A idade nunca é renovada pelo envio.

Enquanto o arquivo for válido, o coletor evita a tentativa de rede que expira
na VPS. A leitura entra pelo fluxo existente em `ultimo.json`, série mensal,
linha do tempo e registro do evento. Sem arquivo válido, tenta a fonte direta.
O envio sozinho não altera `ultimo.json` nem publica um snapshot parcial.

Executar o envio a cada 15 min com o PC ligado e conectado. O cron existente
da VPS continua responsável pela coleta e publicação. É necessário integrar
esta alteração no main e atualizar a VPS antes de o arquivo ser consumido.

Em 12/09 às 21h38, o transporte foi confirmado, mas o portal só publicava
4,02 m de 19h04: dado atrasado, não uma medição feita às 21h38. Se o município
não renovar a medição, a ponte para de aceitá-la ao ultrapassar três horas.

Testes verificam identidade, carimbos, expiração, valores inválidos, arquivo
ausente/corrompido e uso pelo coletor sem tentar o host inacessível.

---

## 17/09/2026 — a ponte funciona; quem parou foi a estação do município

Primeiro caso real de silêncio com a ponte montada, e ele separou as duas coisas
que antes se confundiam.

O que está de pé, medido: a **tarefa agendada** no PC (Agendador do Windows, de
15 em 15 min) rodou a noite inteira sem falhar uma vez; o **portal responde** ao
PC; o **SSH** entrega. O que parou é a estação: a leitura mais recente que o
portal publica é de **16/09/2026 às 17h24**, e não avançou desde então — em
17/09 às 18h48 o envio a recusou com **25,4 h** de idade.

É exatamente a leitura que a ponte entregou na primeira execução, em 16/09 às
19h28 (1,75 m). Ou seja: a estação publicou aquele valor e **não publicou mais
nada**; o único dado de Gaspar que este projeto chegou a ter ao vivo foi o
último que ela produziu antes de parar.

Consequência, e ela é a projetada: o `gaspar_pc.validar` recusa medição com mais
de 3 h, então a VPS parou de aceitar o arquivo, Gaspar saiu do `ultimo.json` e o
mapa devolveu a cidade ao **cinza** — em vez de mostrar 1,75 m como se fosse
agora. O vigia passou a citá-la entre as que sumiram, e essa cobrança expira
sozinha em `MEMORIA_DIAS` (3 dias) depois da última vez que ela publicou.

Como se soube de que lado estava o problema: até 17/09 o envio recusava com uma
frase só — *"Sem leitura municipal recente e válida"* —, que serve para portal
mudo, número implausível e leitura velha. Agora ele escreve o motivo e a idade
(PR #363). O log respondeu na primeira execução.

**Não afrouxar o teto de 3 h para Gaspar voltar ao mapa.** O teto é o que impede
um número de ontem de virar cor hoje; Gaspar cinza é a informação correta
enquanto a estação estiver parada.

O que destrava de verdade continua sendo institucional: a Defesa Civil de Gaspar
liberar o IP `65.108.154.111` (tira o PC do caminho) e responder se a régua do
Açu tem cadência declarada — hoje não se sabe se 22 h parada é defeito ou rotina
de rio baixo.

---

## 04/10/2026 — coleta pelo GitHub Actions (decisão do Jefferson)

O portal de Gaspar dá timeout na VPS e responde ao runner do GitHub (captura de
28/09, `docs/CAPTURA-FONTES-2026-09-28.md`). A coleta passou a rodar também no
Actions, sem depender do PC ligado.

**Caminho do dado.** `.github/workflows/coletar-gaspar.yml` roda nos minutos 7, 22,
37 e 52 de cada hora (e à mão, por *Run workflow*). Ele chama
`scripts/gaspar_actions.py`, que:

1. pede o `robots.txt` de `defesacivil.gaspar.sc.gov.br`. Se o caminho
   `/estacao/ver/21` for recusado, ou se o robots.txt responder 5xx ou não
   responder, a página **não é pedida** e a rodada falha. Só 4xx conta como
   "sem regras" (RFC 9309);
2. pede a estação 21 uma vez, com o User-Agent do projeto, 1,5 s depois do
   robots.txt, e com timeout de 10 s para conectar e 30 s para ler. Não insiste:
   a próxima rodada, 15 min depois, é a nova tentativa;
3. lê a régua do Açu com o mesmo parser da ponte (`coleta_gaspar.analisar_estacao`
   e `leitura_da_cidade`, por igualdade de rótulo);
4. compara com o `gaspar.json` publicado na rodada anterior. Se a régua, o nível e
   o horário da medição forem os mesmos, **não grava nada**. Se mudou, grava
   `gaspar.json` e o HTML bruto (`gaspar-estacao-21.html`, com o sha256 dentro do
   JSON) num commit órfão no branch **`coleta-gaspar`**, que substitui o anterior,
   como no `tempo-real`.

A VPS lê `https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/coleta-gaspar/gaspar.json`
em cada rodada do `coleta_niveis.py`. A validação é a da ponte
(`gaspar_pc.validar`: estação, cidade, rio, fonte, número plausível, medição com
até 3 h e fora do futuro), sem o teto de 30 min da consulta. Esse teto não se
aplica porque o arquivo só muda quando a leitura muda. Com a ponte do PC e o
Actions válidos ao mesmo tempo, vale a medição mais recente. Sem nenhum dos dois,
a VPS ainda tenta o portal direto, como antes.

**Fuso.** `leitura.medido_em` é horário de Brasília sem fuso, como a página
publica. `coletado_em` é UTC com offset e marca a hora em que essa leitura foi
vista pela primeira vez. Nenhum dos dois é renovado quando a leitura se repete.

**Leitura velha.** Quando a medição passa de 3 h, o run sai com um aviso amarelo
("a estação do município parou de atualizar, não a coleta"), mas o job continua
verde. A VPS recusa a leitura pela idade e Gaspar volta ao cinza, como já
acontecia com a ponte. **Não afrouxar o teto.**

**Falha.** Robots.txt recusando, timeout, HTTP diferente de 200, página sem a
régua do Açu ou medição no futuro deixam o job **vermelho**. Nesse caso:

- o motivo vai para o log e para o resumo do run;
- o diagnóstico (`falha.json` e o corpo, se chegou) fica como artefato por 7 dias;
- o fluxo abre a issue **"Coleta de Gaspar pelo Actions falhando"**. Nas falhas
  seguintes ele só reescreve o corpo da issue, sem notificar de novo, e fecha a
  issue com um comentário quando uma rodada volta a dar certo.

A falha do Actions sozinha não pinta nada de errado no site. Sem leitura válida,
Gaspar fica cinza, e o vigia da VPS cobra o sumiço da régua pela memória rolante.

**O que precisa estar ligado no GitHub.** O fluxo declara `contents: write`, para
empurrar o branch `coleta-gaspar`, e `issues: write`, para o aviso. Se em
*Settings → Actions → General → Workflow permissions* o repositório ou a conta
restringirem o token a leitura, o empurrão falha e o run fica vermelho. O
agendamento só vale depois do merge no `main`. O GitHub pode atrasar ou pular
execuções agendadas em horário de pico. Ele também desliga o agendamento de
repositório público depois de 60 dias sem atividade, o que hoje não é risco.

**A ponte do PC continua funcionando** e pode ficar ligada como reserva. Desligar
a tarefa agendada do PC é decisão do Jefferson, depois de ver o Actions publicando.
