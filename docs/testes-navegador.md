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
mostram o número mas **não** recebem cor de perigo nem animação.

- ✅ Anel vazado (não bolinha cheia), com número e idade ao lado, **sem setas correndo**.
- ❌ Qualquer ribeirão **animado**, ou pintado de amarelo/laranja/vermelho.

> **Este é o teste mais importante da lista.** Se falhar, é o alarme de maré vazando para o
> mapa — reporte imediatamente e com print, antes de continuar.

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
