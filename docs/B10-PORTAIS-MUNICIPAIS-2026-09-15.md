# B10 — por que a VPS não alcança os portais de Brusque e Gaspar

Medido em **15/09/2026**, depois do reboot do B11. Fecha a pergunta que o B10 fazia desde
10/09: *"é bloqueio dos portais ou da VPS?"*

**Resposta: dos portais.** A VPS está sã e alcança o Brasil; estes dois municípios é que não
respondem a ela.

## O que foi medido

Servidor: `ubuntu-4gb-hel1-2`, Hetzner, Helsinque — **65.108.154.111** (IPv6
`2a01:4f9:c014:4576::1`).

### Da VPS — as cinco URLs do B10

| URL | resultado |
|---|---|
| `defesacivil.brusque.sc.gov.br/` | **000**, timeout em 35,0 s |
| `defesacivil.brusque.sc.gov.br/estacao/ver/4` | **000**, timeout em 35,0 s |
| `defesacivil.brusque.sc.gov.br/estacao/ver/79` | **000**, timeout em 35,0 s |
| `defesacivil.brusque.sc.gov.br/mapas/cotas-de-ruas` | **000**, timeout em 35,0 s |
| `defesacivil.gaspar.sc.gov.br/` | **000**, timeout em 35,0 s |

### Do Windows do Jefferson, no Brasil — as mesmas URLs

| URL | resultado |
|---|---|
| `defesacivil.brusque.sc.gov.br/` | **200** em 21,6 s |
| `defesacivil.brusque.sc.gov.br/estacao/ver/79` | **200** em 2,3 s |
| `defesacivil.gaspar.sc.gov.br/` | **200** em 0,3 s |

### Da VPS — outros hosts brasileiros, nos mesmos minutos

Este é o grupo de controle, e é o que transforma "não conseguimos acessar" em prova:

| host | resultado |
|---|---|
| `monitoramento.defesacivil.sc.gov.br` | **200** em 0,69 s |
| `defesacivil.itajai.sc.gov.br` | **200** em 4,35 s |
| `www.ana.gov.br` | **302** em 0,74 s |
| `alertablu.blumenau.sc.gov.br` | conectou em 1,36 s (erro de cadeia de certificado, **não** de rede) |

Três hosts `.gov.br`, um deles a própria Defesa Civil estadual, todos respondendo do mesmo
servidor no mesmo intervalo. **O Brasil é alcançável da VPS.**

## O que isso descarta

- **Não é a VPS.** Ela publica a coleta a cada 15 minutos lendo fontes brasileiras, e as
  quatro do controle responderam.
- **Não é rota da Hetzner para o Brasil.** Mesma conclusão, pelo mesmo controle.
- **Não é escolha de IPv4 vs IPv6.** Brusque resolve nas duas famílias
  (`132.255.223.229` e `2804:4d44:14:8020::101`) e **as duas** dão timeout. Gaspar só tem
  IPv4 (`186.250.184.3`) e também falha. A hipótese de "o curl pegou IPv6 e o IPv6 não fecha"
  foi levantada e **derrubada pela medição**.
- **Não é WAF olhando a requisição.** O TCP nem abre:

  ```
  timeout 10 bash -c 'cat < /dev/null > /dev/tcp/defesacivil.brusque.sc.gov.br/443'  → TCP 443 nao abre
  timeout 10 bash -c 'cat < /dev/null > /dev/tcp/defesacivil.brusque.sc.gov.br/80'   → TCP 80 nao abre
  ```

  Descarte antes do handshake. **Mexer em `User-Agent` ou em cabeçalho não resolve** — a
  requisição nunca chega a existir.

- **Não é DNS.** Os dois nomes resolvem normalmente na VPS.

## O que fica como hipótese

Que tipo de filtro — geográfico, por ASN, ou bloqueio explícito do IP — **não foi medido**.
`traceroute -T -p 443` diria onde o pacote morre, e não chegou a ser rodado. A diferença
importa pouco para o encaminhamento: os três se resolvem pelo mesmo pedido.

Também não se sabe se o filtro é deliberado ou efeito colateral de um appliance de segurança
que os dois municípios calharam de usar. Dois municípios distintos, em blocos de IP distintos,
com o mesmo sintoma exato, sugere ferramenta comum — mas sugerir não é medir.

## O que muda para o projeto

**Pouco, e é importante dizer por quê:** o nível ao vivo de Brusque **não depende deste
portal**. Vem da rede estadual (DCSC), que a VPS alcança. O que fica inacessível é o acervo
municipal — cotas de rua e as páginas de estação.

Gaspar é outro caso, e pior, mas por motivo independente: mesmo com a rede aberta **não
haveria o que coletar**, porque a régua do Açu saiu da página na reformulação de 2026. Ver o
item do Gaspar em **Pendências** no `README.md`.

## Encaminhamento

O pedido a fazer é **liberação do IP 65.108.154.111** nas Defesas Civis de Brusque e de
Gaspar, com esta evidência junto:

> O site responde normalmente de uma conexão no Brasil (HTTP 200) e não responde do servidor
> do projeto, hospedado na Finlândia: a conexão TCP nas portas 80 e 443 não chega a abrir,
> tanto em IPv4 (132.255.223.229) quanto em IPv6 (2804:4d44:14:8020::101). No mesmo servidor
> e no mesmo horário, `monitoramento.defesacivil.sc.gov.br` e `defesacivil.itajai.sc.gov.br`
> respondem em menos de 5 s. O IP a liberar é 65.108.154.111.

Duas alternativas, se a liberação não vier:

1. **Coleta por outra rota** — um relé numa máquina no Brasil que busque e republique.
   Acrescenta um elo que pode falhar calado, então precisaria do mesmo vigia de frescor que
   as outras fontes têm.
2. **Coleta manual pelo Jefferson**, como já foi feito com o KML de Brusque e com a tábua de
   marés da Marinha. Serve para acervo (cotas de rua), não para tempo real.

⚠️ Registrado também porque é armadilha para o futuro: **um coletor novo que fale com portal
municipal pode falhar só em produção**, passando em todos os testes locais. O sintoma é
timeout, não erro — e timeout longo num coletor de 15 minutos atrasa a coleta inteira. Timeout
curto e explícito em qualquer fonte municipal nova.

### Nota lateral: a raiz de Brusque é lenta por conta própria

Do Brasil, `defesacivil.brusque.sc.gov.br/` levou **21,6 s** para responder 200, enquanto a
página de estação levou 2,3 s. Não é rede: é o site. Qualquer coletor que venha a falar com
ele precisa de timeout generoso — os 10 s de praxe recusariam uma resposta que ia chegar.
