# Teste no navegador — Enchentes do Vale do Itajaí

> Para uma sessão do Claude **com acesso ao Chrome**. Leia tudo antes de começar.

## O que é este site e por que o teste importa

Site que mostra o nível dos rios **Itajaí-Açu** e **Itajaí-Mirim** (Santa Catarina) para
moradores decidirem se saem de casa durante uma cheia. **Não é sistema oficial de alerta** —
mas é lido como se fosse, por gente sem formação técnica, de celular, durante a chuva.

A regra que governa o projeto inteiro, e que deve governar o seu julgamento aqui:

> **Prefira "não sei" a um número errado. Nunca deixe alguém se sentir mais seguro do que está.**

Por isso, ao avaliar cada teste, o critério não é "está bonito?" e sim:

- a tela **afirma** alguma coisa que ela não mediu?
- a tela **cala** alguma coisa que ela mediu?
- um número aparece **sem a idade dele** ao lado?
- cinza (= "não sei") virou verde (= "está calmo") em algum lugar?

Qualquer "sim" nessas quatro é falha, mesmo que a lista abaixo não preveja o caso.

## Endereço

```
https://haohmarusc-glitch.github.io/enchentes-vale-itajai/
```

O site usa **HashRouter**, então as rotas levam `#`:

| Tela | URL |
|---|---|
| Início | `.../#/` |
| Monitor da bacia (mapa) | `.../#/monitor` |
| Itajaí-Açu | `.../#/acu` |
| Itajaí-Mirim | `.../#/mirim` |
| Itajaí (foz) | `.../#/itajai` |
| Uma cidade | `.../#/acu/gaspar`, `.../#/mirim/brusque` |

---

## PASSO 0 — Confira o pré-requisito antes de qualquer coisa

Abra:

```
https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/serie-recente.json
```

Procure a chave `"reguas"` no começo do arquivo (Ctrl+F).

- **Achou `"reguas"`** → o dado novo está no ar. Faça **todos** os testes.
- **Não achou** → a coleta na VPS ainda não foi atualizada. Faça todos **menos o 9 e o 10**,
  e leia a seção "O que NÃO reportar como falha" no fim.

Anote qual dos dois casos você encontrou — o relatório precisa dizer isso.

---

## Os testes

Para cada um: **o que fazer → o que tem que acontecer → o que é falha.**
Tire print de toda falha. Nos testes 2 e 10, tire print mesmo se passar.

### 1. O canal retificado do Mirim corre
`#/monitor` → dê zoom em Itajaí (canto inferior direito do mapa).

O Itajaí-Mirim chega à cidade em **dois braços paralelos**: o *canal retificado* e o
*curso antigo*. Os dois são o mesmo rio.

- ✅ Os dois braços com a **mesma cor** e **os dois com setas correndo**.
- ❌ Um verde e animado, o outro cinza e parado.

### 2. Os ribeirões continuam cinza e PARADOS
Mesma tela. Procure **Ribeirão da Murta**, **Ribeirão Canhanduba** e **Rio Conceição**.

As réguas deles são de estuário: a maré cruza a cota sem enchente nenhuma. Por isso eles
**não** recebem cor de perigo nem animação, mesmo tendo número.

**São duas verificações, e elas valem em zooms diferentes.** Faça as duas.

**2a — cinza e parado (vale em QUALQUER zoom).** É esta que impede o alarme de maré de
vazar para o mapa.

- ✅ Anel **vazado** (não bolinha cheia), traço do ribeirão **cinza**, **sem setas correndo**.
- ❌ Qualquer ribeirão **animado**, ou pintado de amarelo/laranja/vermelho.

**2b — número e idade (só de PERTO).** Aproxime até o mapa cobrir **menos de ~6 km** de
largura — na prática, o bairro, não a cidade.

- ✅ Cada régua com o número e a idade ao lado.
- ❌ Número sem idade; ou nenhum número mesmo com o mapa bem aproximado.

> **Por que 2b só vale de perto, e por que isto está escrito aqui.** Desde a regra de
> rótulos por zoom, régua que **não pode virar aviso** (as de estuário) só escreve o número
> com o mapa a menos de ~6 km. De longe ela é ponto, **de propósito**: em Itajaí são onze
> réguas em 20 km, e todas escrevendo ao mesmo tempo viram uma pilha ilegível — e pilha
> ilegível num mapa de cheia é pior que dado escondido, porque parece informação e não se
> lê. A legenda do mapa explica isso ao morador.
>
> A versão anterior deste teste pedia "anel vazado **com número e idade**" numa verificação
> só. Do jeito que estava, ele **acusava falha exatamente onde a regra está funcionando** —
> foi o que aconteceu na execução de 06/09/2026.

> **A verificação 2a é a mais importante da lista inteira.** Se falhar, é o alarme de maré
> vazando para o mapa — reporte imediatamente e com print, antes de continuar. A 2b é
> informativa: se falhar, o morador perde o número, mas ninguém se sente mais seguro do que
> está.

### 3. O Canhanduba chega no Mirim
`#/monitor`, zoom na parte sul de Itajaí.

- ✅ A linha do Ribeirão Canhanduba **encosta** no Itajaí-Mirim (o trecho final chama-se
  Rio Conceição), sem vão.
- ❌ A linha morre no meio da várzea, a algumas centenas de metros do rio.

### 4. Marca d'água no fundo do mapa
`#/monitor`, botão **"Escuro"** (é o padrão).

O provedor antigo (CARTO) passou a exigir chave e cobria o mapa com "API KEY REQUIRED".
Foi trocado pelo Esri. **Esta troca não pôde ser verificada por quem a fez** — é o teste
mais provável de falhar da lista.

- ✅ Mapa escuro limpo, sem texto repetido por cima.
- ❌ Qualquer "API KEY REQUIRED" ou marca de provedor sobre a cidade.

### 5. O fundo escuro tem nomes de bairro
Mesma tela, mesmo fundo.

O Esri separa desenho e rótulo em duas camadas; se a segunda não carregar, o mapa fica
bonito e **mudo** — e é pelo nome do bairro que a pessoa se localiza.

- ✅ Dá para ler "Itajaí", "Navegantes", "Santa Regina", nomes de rua.
- ❌ Mapa escuro sem texto nenhum.

### 6. Zoom no fundo escuro trava no nível 16
`#/monitor`, fundo "Escuro", dê zoom até o máximo.

- ✅ O fundo fica borrado depois de certo ponto, **e isso é esperado** (o Esri publica até
  o nível 16). Tocar em **"Mapa"** deve recuperar o detalhe.
- ❌ O fundo **some** (fica preto/branco) em vez de borrar; ou "Mapa" também não recupera.

### 7. O pino de Itajaí diz "sem leitura", não "sem régua"
`#/monitor`, ache o pino da cidade de **Itajaí**, na foz.

Itajaí tem **onze** réguas (DC-01 a DC-11). O pino da *cidade* não tem número próprio, e
até hoje dizia "sem régua" — o que é falso e faz o morador concluir que o site não cobre a
cidade dele.

- ✅ O rótulo diz **"sem leitura"**.
- ❌ Diz **"sem régua"**.

Confira também **Guabiruba** (`#/mirim`): essa sim deve dizer **"sem régua"**, porque
realmente não tem instrumento. As duas frases têm de existir e ser diferentes.

### 8. As onze réguas de Itajaí aparecem separadas
`#/monitor`, zoom em Itajaí. Devem aparecer pontos menores, um por régua:

| | | |
|---|---|---|
| DC-01 CEPSUL | DC-02 Praça | DC-03 SEMASA |
| DC-04 Vitalmar | DC-05 (curso antigo) | DC-06 Itamirim |
| DC-07 Portal (Murta) | DC-08 Rua Benjamin Dagnoni (Canhanduba) | DC-09 Bairro Murta |
| DC-10 Limoeiro | DC-11 Santa Regina | |

- ✅ Cada uma com número e idade. **DC-10 e DC-11** podem ter cor (não são de estuário);
  as outras nove são anel vazado.
- ❌ Uma régua sobre terra seca longe de qualquer rio desenhado; ou alguma das nove com cor.

### 9. Uma linha por régua no gráfico de Itajaí
> **Só faça se o PASSO 0 achou `"reguas"`.**

`#/itajai` (ou `#/acu` e toque em Itajaí). Olhe o gráfico das últimas horas.

- ✅ **Várias linhas coloridas**, uma por régua, com os nomes das réguas na legenda ou no
  tooltip.
- ❌ Uma linha azul só, serrilhada, pulando ~1,7 m entre pontos vizinhos.

### 10. Itajaí NÃO mostra "subindo N cm/h"
> **Só faça se o PASSO 0 achou `"reguas"`.**

Mesma tela, o texto acima do gráfico.

As onze réguas têm zeros diferentes; comparar duas delas dá a diferença entre dois zeros,
não o movimento do rio. O site já chegou a poder afirmar **+2448 cm/h** — "o rio sobe 24
metros por hora".

- ✅ Em vez de "Agora: X", uma **lista com a última leitura de cada régua**, cada uma com
  um quadradinho da cor da linha dela no gráfico.
- ❌ Qualquer "subindo" ou "descendo" com cm/h para Itajaí. **Se aparecer um número acima
  de 30 cm/h, tire print — é o defeito voltando.**

### 11. As outras cidades não perderam nada
`#/acu/blumenau` e `#/acu/rio-do-sul`.

- ✅ Uma linha só, "Agora: X (faixa)", **e** a tendência em cm/h continuam aparecendo.
- ❌ Sumiu a tendência de Blumenau. (Seria a fonte de resgate do AlertaBlu sendo contada
  como uma régua separada da primária, quando são a mesma.)

### 12. Aviso legal em TODA tela
Passe por `#/`, `#/acu`, `#/mirim`, `#/itajai`, `#/monitor`.

- ✅ Todas dizem que o site **não substitui** o AlertaBlu / Defesa Civil, e trazem o **199**.
- ❌ Qualquer tela sem isso. É regra do projeto, não estética.

### 13. Página por cidade
Abra: `#/acu/gaspar`, `#/acu/blumenau`, `#/acu/indaial`, `#/mirim/brusque`,
`#/mirim/vidal-ramos`.

- ✅ Cada uma abre com o nome certo e o conteúdo da cidade.
- ✅ `#/acu/itajai` **redireciona** para `#/itajai` (a foz tem tela própria).
- ❌ Página em branco, erro, ou Itajaí abrindo a página genérica.

### 14. Todo número tem idade
Em qualquer tela com nível.

- ✅ Todo valor em metros vem acompanhado de "há N min" / "há N h".
- ❌ Número solto, sem quando foi medido. Leitura velha tem que **parecer** velha.

### 15. Reproduzir 24 h
`#/monitor`, botão **"Reproduzir 24 h"**.

- ✅ A onda desce de montante para a foz; as cores mudam de forma coerente no tempo.
- ❌ Cor piscando aleatoriamente, onda subindo o rio, ou a animação travando a página.

### 16. Sem rede
Com o site aberto, desligue a rede (DevTools → Network → Offline) e recarregue.

- ✅ A tela diz que está sem dado / mostra a idade crescendo.
- ❌ Mostra um número antigo **como se fosse de agora**, sem ressalva.

### 17. Celular de verdade
DevTools → modo dispositivo, largura ~360 px. Passe por todas as telas.

- ✅ Texto não corta, botões dão para acertar com o dedo, **a página não rola de lado**.
- ❌ Rolagem horizontal, texto sobreposto, botão inalcançável.

### 18. Console e rede limpos
DevTools aberto durante todo o teste.

- ✅ Sem erro vermelho no Console; sem `403`/`404` na aba Network.
- ❌ Anote cada erro com a tela em que apareceu.

### 19. Links das fontes
Rodapé de `#/`. Abra 3 ou 4 (ANA/HidroWeb, AlertaBlu, Defesa Civil SC, CEOPS/FURB).

- ✅ Todos abrem.
- ❌ Anote os que dão 404 ou não respondem.

---

## O que NÃO reportar como falha

1. **Se o PASSO 0 não achou `"reguas"`:** o gráfico de Itajaí vai mostrar **uma linha só,
   serrilhada, com uma tendência em cm/h**. Isso é o comportamento **correto** para o dado
   antigo (a retrocompatibilidade é intencional e testada). Reporte apenas: *"passo 0 =
   sem reguas, testes 9 e 10 não executados"*.
2. **Fundo escuro borrado em zoom alto** — esperado (teste 6).
3. **Cidades cinza no mapa** — cinza significa "não sei" e é honesto. A maior parte da
   bacia está cinza de propósito: só 4 cidades têm cota **e** leitura ao vivo.
4. **Pinos sem número em Ilhota, Indaial, Gaspar** — essas cidades têm cota oficial mas a
   fonte não publica leitura. Devem dizer "sem leitura", e isso está certo.

---

## Como reportar

Para cada teste: **número → passou / falhou / não executado**, e nas falhas: print + a tela
(URL com o `#`) + o que você viu, em uma frase.

No fim, responda também estas três:

1. Você encontrou alguma coisa **fora da lista** que afirma um número sem dizer a idade,
   ou que pinta de verde onde deveria ser cinza?
2. Se um morador de Itajaí abrisse este site agora, no meio de uma chuva forte, alguma
   coisa na tela poderia fazê-lo **se sentir mais seguro do que está**?
3. O que na tela você **não entendeu** sem ler este arquivo? (Se você não entendeu, quem
   mora lá também não vai.)

A pergunta 2 é a que mais importa. Responda-a mesmo que todos os 19 testes passem.

---

# Execução de 06/09/2026 (Claude, ambiente remoto)

**PASSO 0: achou `reguas`** — logo, o 9 e o 10 valem.

O site foi servido de `vite preview` sobre a build do branch, com o **dado real
do branch `tempo-real`** (os quatro JSON baixados por `curl` e servidos à
página; o navegador deste ambiente não alcança o `raw.githubusercontent`, o
`curl` alcança). Blumenau 3,25 m, Rio do Sul 5,23 m em atenção, brutos em
violeta — dado vivo, não maquete.

| # | Resultado | Observação |
|---|---|---|
| 1 | ✅ | Os dois braços do Mirim (canal retificado e curso antigo) verdes e **os dois com setas correndo**. |
| 2 | ✅ **2a** · ⏳ 2b | A verificação que importa passa: o ribeirão é **cinza e sem seta nenhuma**, com anel vazado. A 2b (número e idade) não foi confirmada porque exige zoom abaixo de ~6 km. **O teste foi reescrito depois desta execução**, separando as duas — ver o enunciado. |
| 3 | ✅ | **Medido no traçado, não a olho**: a ponta do Ribeirão Canhanduba encosta no **Rio Conceição a 0 m** — que é exatamente o que o teste pede (o trecho final do Mirim ali chama-se Conceição; a distância de 578 m até a linha `itajai-mirim` é para outro traçado, e não é vão). |
| 4, 5, 6 | ⏳ **impossível daqui** | o proxy bloqueia os tiles do Esri (`server.arcgisonline.com`). Só com o site no ar. |
| 7 | ✅ | Itajaí diz **"sem leitura"**; Guabiruba diz **"Sem cota / sem leitura"**. |
| 8 | ✅ | **Medido, não olhado.** As onze réguas estão sobre o rio desenhado: distância ponto-a-segmento de **2 a 111 m**, mediana ~26 m. Nenhuma em terra seca. O `DC-00` que aparece no cadastro **não é uma das onze**: é `tipo: "pluviometro"`, `rio: null`, `verificado: false` — corretamente tipado e fora da conta. |
| 9 | ⚠️ **defeito de outro tipo** | Não é a "linha azul serrilhada" que o roteiro temia. **Não há gráfico de Itajaí em tela nenhuma** — `#/itajai` traz a tabela de cotas das onze réguas, e `#/monitor/itajai` não desenha série. O dado existe e é rico (955+565+191+381 pontos, com índice de régua). É lacuna, não perigo. |
| 10 | ✅ | **Nenhum cm/h na tela de Itajaí.** A assimetria está certa: Blumenau mostra 1 e 3 cm/h, Rio do Sul 2 cm/h, Itajaí nenhum. |
| 11 | ✅ | Blumenau "Agora 3,25 m há 1 h 04" com tendência; Rio do Sul "Agora 5,23 m · ACIMA DA COTA DE ATENÇÃO". A tendência de Blumenau **não sumiu**. |
| 12 | ✅ | As 5 telas trazem o 199 e o "não substitui". |
| 13 | ✅ | As 5 páginas de cidade abrem; `#/acu/itajai` **redireciona** para `#/itajai`. |
| 14 | ✅ | Nenhum número ao vivo sem idade. (A primeira sonda acusou falha e estava errada: o painel de reprodução carrega o horário **uma vez para o conjunto**, não por linha.) |
| 15 | ✅ **na mecânica** | O botão vira "⏸ Pausar", o instante avança, e a página **continua respondendo durante a animação** (494 ms para um toque no zoom; travada seria segundos). A parte visual — "a onda desce de montante para a foz" — **não pôde ser observada hoje: não há cheia descendo**. Rio do Sul em atenção, Blumenau abaixo, o resto cinza. Sem onda, nada a ver descer. |
| 16 | ✅ | Sem rede: nenhum número ao vivo na tela, e a tela **diz** que está sem dado. |
| 17 | ✅ | 360 px: nenhuma das 5 telas rola de lado. |
| 18 | ✅ | Nenhum erro de console além dos tiles bloqueados por este ambiente. |
| 19 | ⏳ **impossível daqui** | as fontes são bloqueadas pelo proxy. |

## Um susto conferido antes de virar relato

Medindo o traçado, a ponta do **Ribeirão da Murta** aparecia a 1.234 m do
Itajaí-Açu — o vão que o teste 3 existe para pegar. Medindo a linha inteira, e
não só as pontas: ela **toca o Açu a 0 m**, no ponto 188 de 197, e segue mais
1,2 km além da confluência. Não é vão, é sobra. Medida de ponta não é medida de
linha.

## O mesmo erro de método, duas vezes no mesmo dia

Na primeira, a PONTA do Ribeirão da Murta parecia a 1.234 m do Açu; a linha
inteira toca o rio a 0 m. Na segunda, a régua **DC-03** parecia a 534 m do
canal retificado; medindo **ponto-a-segmento** em vez de ponto-a-vértice, são
**20 m**. O traçado do canal tem 12 pontos, e num polígono esparso a distância
até o vértice mais próximo não tem nada a ver com a distância até a linha.

Quem for medir geometria aqui: **ponto-a-segmento, sempre**, e a linha inteira,
não as pontas. As duas medidas erradas apontariam defeito onde não há.

## O teste 2 foi reescrito (feito em 06/09/2026)

Ele pedia "anel vazado, **com número e idade ao lado**, sem setas correndo" numa
verificação só, e era anterior à regra de rótulos por zoom. Do jeito que estava,
**acusava falha exatamente onde a regra está funcionando**.

Agora são **2a** (cinza e parado, vale em qualquer zoom — é a que impede o
alarme de maré de vazar) e **2b** (número e idade, só abaixo de ~6 km de
largura). O enunciado no alto deste arquivo já está separado assim, com o motivo
escrito para quem for testar não repetir o engano.

**Lição que vale além deste teste:** quando uma regra de exibição muda, o
roteiro de teste envelhece junto — e um teste velho não falha em silêncio, ele
aponta o defeito errado.

## O que este ambiente NÃO alcança

`server.arcgisonline.com` (tiles), `indaial.atende.net`, `marinha.mil.br`,
`ciram.epagri.sc.gov.br`, `defesacivil.*.sc.gov.br`, `*.ana.gov.br`,
`overpass-api.de`, `nominatim.openstreetmap.org` e a preview do Cloudflare.
Tudo que depender dessas fontes é do Jefferson ou do VPS.

---

# Execução de 06/09/2026 (Chrome do Jefferson)

Complementa a execução acima. Rodada no **Chrome local**, sobre a **preview do
Cloudflare** do branch, com dado ao vivo. O objetivo era só o que o ambiente
remoto não alcança: os tiles do Esri (4, 5, 6) e os links do rodapé (19); mais
uma segunda passada em 3 e 15.

| # | Resultado | Como foi verificado |
|---|---|---|
| 3 | ✅ | medido, não olhado — ver abaixo |
| 4 | ✅ | nenhum "API KEY REQUIRED"; `World_Dark_Gray_Base` e `World_Dark_Gray_Reference` todos **200** |
| 5 | ✅ | rótulos carregam em três zooms: bacia, cidade e rua |
| 6 | ✅ | pela rede: há `tile/16/`, **nenhum `tile/17/`**; "Mapa" recupera o detalhe |
| 15 | ✅ | 3 quadros ao longo da reprodução, valores contínuos |
| 19 | ⚠️ parcial | 8 links abertos; 1 achado; 4 não verificados |

## 3 — a cadeia inteira, medida

Distância mínima **ponto-a-segmento** entre os traçados de `data/rios/`:

| Par | Distância |
|---|---:|
| `ribeirao-canhanduba` ↔ `rio-conceicao` | **0,0 m** |
| `rio-conceicao` ↔ `itajai-mirim` | **0,0 m** |
| `itajai-mirim` ↔ `mirim-canal-retificado` | **0,0 m** |
| `ribeirao-murta` ↔ `itajai-acu` | **0,0 m** |

> **TERCEIRA ocorrência do mesmo erro de método, evitada a tempo.** A primeira
> medida usou as EXTREMIDADES das linhas e deu **393 m** entre a ponta do
> Canhanduba e o Conceição — o que teria sido reportado como falha. A junção
> não está na ponta da linha.
>
> Extremidade não é conexão, do mesmo modo que vértice não é segmento. Foram
> três vezes no mesmo dia: a ponta do Murta (1.234 m que eram 0), a régua DC-03
> (534 m que eram 20) e esta.
>
> **Antes de reportar qualquer distância neste projeto: ponto-a-segmento, sobre
> a LINHA INTEIRA, nunca extremidade contra extremidade.**

## 6 — um falso alarme que vale registrar

No primeiro zoom o fundo escuro pareceu **sumir** — a tela ficou azul-escura
lisa. Era carregamento: os tiles chegam com alguns segundos de atraso nesse
nível. Depois de esperar, o fundo aparece completo.

Quem testar no celular com rede fraca vai ver a mesma coisa. **Não é o defeito
que o teste 6 procura** — o defeito seria o fundo sumir e não voltar.

## 15 — a onda, com dado de verdade

Três quadros, 05/09 20:44 → 06/09 07:44 → 06/09 16:14, sem travar a página:

| | Taió | Rio do Sul |
|---|---:|---:|
| 05/09 20:44 | 5,47 m | 5,37 m |
| 06/09 07:44 | 5,31 m | 5,25 m |
| 06/09 16:14 | 5,17 m | 5,22 m |

Valores contínuos, maré alternando de forma coerente, e as cidades sem dado
naquele instante dizendo **"sem leitura"** em vez de herdar cor do quadro
anterior. Nada piscando ao acaso. É a metade que a execução remota não pôde
observar por não haver cheia descendo.

## 19 — links das fontes

**Abrem:** AlertaBlu (redireciona para o portal da Defesa Civil de Blumenau),
Defesa Civil de SC (raiz e `/mapa`), HidroWeb séries históricas, Defesa Civil de
Itajaí (`nivel-rios`, `mares`, `barragem`) e Defesa Civil de Gaspar
(`/monitoramento/tabela`).

**Dois pontos a resolver:**

1. **O link do CEOPS/FURB é `http://`, não `https://`.** Num site que as pessoas
   abrem no meio da chuva, link em texto claro no rodapé não é detalhe estético.
   **Não foi trocado**: deste ambiente não dá para saber se o `ceops.furb.br`
   serve https (o proxy devolve 000 no https e 403 no http — os dois são dele,
   não da fonte), e link quebrado no rodapé é pior que link em texto claro.
   Resolver é abrir o endereço em https no navegador: se abrir, trocar; se não,
   registrar aqui que a fonte só serve http.
2. **`defesacivil.gaspar.sc.gov.br/enchentes` devolveu conteúdo idêntico ao
   `/monitoramento/tabela`.** Pode ser SPA, pode ser 404 caindo na home.
   Precisa de conferência humana. Importa porque é a fonte dos **70 registros
   históricos candidatos de Gaspar**.

**Não verificados** (a extensão negou permissão de domínio): `labgeo.furb.br`,
`libgeo.acad.univali.br/mapi/`, `snirh.gov.br/hidrotelemetria` e o PDF da JICA
em `openjicareport.jica.go.jp`.

---

# Placar acumulado — 18 dos 19

| | |
|---|---|
| ✅ **passaram** | 1, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18 |
| ⚠️ **2** | a metade perigosa passa (cinza e parado, o que impede o alarme de maré vazar). O texto do teste é anterior à regra de rótulos por zoom e **precisa ser reescrito**, senão acusa falha onde a regra funciona. |
| ⚠️ **9** | **não existe gráfico de Itajaí em tela nenhuma** — e o dado existe, farto (955+565+191+381 pontos, com índice de régua). Lacuna, não perigo. |
| ⚠️ **19** | parcial: 8 abrem, 1 achado (http do CEOPS), 1 a conferir (Gaspar), 4 não verificados. |

## As três perguntas do fim

**1. Algo fora da lista que afirme número sem idade, ou pinte verde onde devia
ser cinza?** Sim, dois, os dois achados nesta rodada e **os dois já corrigidos**:
a reprodução elegia uma das onze réguas de Itajaí em silêncio (trocando de régua
a cada minuto, 3,10 m virando 1,47 m), e rótulos de cidades fora da tela
flutuavam sobre bairros a 60 km de onde a leitura foi feita.

**2. Um morador de Itajaí, no meio de uma chuva forte, poderia se sentir mais
seguro do que está?** Hoje, não — mas **até esta rodada, sim, e não em Itajaí**:
Indaial estava com `atencao: 6,00 m` quando a emergência do município é 5,50 m.
Um morador de Indaial vendo 5,6 m lia "abaixo da atenção". Corrigido.

**3. O que não se entende sem ler este arquivo?** Por que a maior parte do mapa
é cinza. A legenda explica ("cinza = sem faixa para afirmar"), mas quem abre no
meio da chuva vê um mapa quase todo apagado e pode concluir que o site não
funciona, em vez de que o site não sabe. É honesto e é a decisão certa — mas o
custo de compreensão existe e não está resolvido.
