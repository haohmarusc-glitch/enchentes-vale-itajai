# Barragens no Monitor: painel e armazenamento em escala própria

Entrega 2 do pedido "Monitor: Ituporanga e barragens" (07/10/2026). A entrega 1, sobre o vínculo entre traçado,
cidade e régua, está em `docs/VINCULOS-DOS-TRACADOS.md`.

## O que mudou

| Antes | Agora |
|---|---|
| O marcador da barragem mostrava só as comportas (parede de aço, animação de operação). | Continua igual. Embaixo dele há uma **barra azul** com o percentual informado pela fonte, e o rótulo termina em `· 4,4 %`. |
| Não dava para tocar na barragem. | O toque abre um **painel compacto** (comportas e percentual). Em **Mais detalhes** aparece tudo o que a fonte publica, e o que ela não publica sai como **"não informado"**. |
| O percentual acima de 100 % sumia (o leitor aceitava só 0–100). | Sai o **valor real**, com a nota "acima da capacidade máxima publicada". Só acima de 200 % o valor é tratado como implausível: vira `null`, e o valor cru fica em `percentPublicado`. |
| O nível da barragem não saía do módulo. | Sai **só no painel expandido** e sempre com a referência: "Régua própria da barragem: o zero fica a 339 m de altitude…" e "Não se compara com régua de rio nem com a outra barragem". Sem altitude e zero coerentes (régua = altitude − zero, folga de 5 cm), ele não sai. |
| Camadas: não havia controle para as barragens. | Interruptor **"Barragens: armazenamento"** (`interruptor-armazenamento`) e item na legenda: "Barragem: % informado pela fonte (escala própria, não é faixa de cheia)". |
| Cartão "Agora" (Taió, Ituporanga, Rio do Sul): "reservatório em X % da capacidade". | "percentual informado pela fonte: X %". |

**O que não muda:**
- a **cor do rio** continua sendo a da régua de cada trecho. Percentual, nível e comportas não entram na classificação (teste `logica/barragensNaCena.test.ts`);
- a animação das comportas segue a regra de antes: estado conhecido, leitura fresca (≤ 60 min) e respeito ao "reduzir movimento";
- o percentual **não** controla velocidade de nada.

## Auditoria dos campos, por barragem

Fonte: `https://public.asthon.com.br/public/dams?city_id=4214805` (Asthon / Rio do Sul), lida por
`scripts/coleta_barragens.py` e publicada como `ultimo_barragens.json` no branch `tempo-real`. Valores da coleta
de 07/10/2026 20:08 (Brasília).

| Campo | Oeste (Taió) | Sul (Ituporanga) | Norte (José Boiteux) | No painel |
|---|---|---|---|---|
| Publicada pela fonte | sim | sim | **não**: lista vazia para Ibirama (4207106) e Blumenau (4202404) em 05/09/2026 | Norte fora do mapa e do painel |
| Coordenada | −27,0974, −50,0388 | −27,5039, −49,5536 | — | marcador |
| Nível na régua da barragem | 8,93 m | 20,52 m | — | "Nível na régua da barragem" com zero e altitude |
| Zero da régua | 339 m | 370 m | — | na nota do nível |
| Altitude da superfície (`altitude_montante_m`) | 347,93 m | 390,52 m | — | na nota do nível, em metros acima do nível do mar |
| Coerência régua = altitude − zero | exata | exata | — | condição para mostrar o nível |
| `percent_use` | 4,40 % | 25,09 % | — | "Percentual informado pela fonte" |
| Definição do percentual | a fonte **não define** | idem | — | nota: "Ele bate com a capacidade atual dividida pela máxima que ela publica" |
| atual ÷ máxima × 100 | 4,40 (diferença 0,00 pp) | 25,00 (diferença 0,09 pp) | — | a nota traz a diferença em pp quando ela não é zero |
| Capacidade atual / máxima | 4,40 / 99,96 | 26,01 / 104,03 | — | "Capacidade atual / máxima", com "A fonte não informa a unidade" |
| Vazão de entrada | não publicada | não publicada | — | "não informado" |
| Vazão de saída | não publicada (`vertido_bruto` = 0 com 12 comportas abertas: **não é** vazão) | idem | — | "não informado" |
| Nível a jusante (`jusante_m`) | 5,12 | 141,54 | — | "não informado", com a nota de que a fonte publica um número **sem referência identificada** (as duas grandezas não batem entre si) |
| Comportas | 7 de 7 abertas | 5 de 5 abertas | — | "Comportas", contadas pela lista (sem o campo `aberta` = fechada) |
| Horário | `measured_at` UTC, convertido para Brasília | idem | — | "Medido em" (data e hora de Brasília) e "Leitura de há N min" |
| Faixas operacionais oficiais | **nenhuma tabela** no repositório | nenhuma | — | sem categorias: só número e barra azul |

**Pendências de dados**, que não se resolvem no código:
1. **Barragem Norte:** nenhuma fonte pública conhecida publica comportas ou armazenamento.
2. **Unidade da capacidade:** as pistas da Oeste (99,3 / 99,96 / 100 hm³) estão no prompt de pesquisa (`docs/PICOS-FALTANTES.md` §16), mas sem original. O painel não escreve unidade até a fonte dizer.
3. **Definição do percentual:** a coincidência com atual ÷ máxima não prova que seja "volume útil". O nome na tela é "percentual informado pela fonte".
4. **Vazão:** o JICA já apontava que a operadora não publica vazão de saída.
5. **`jusante_m`:** sem referência. Fica guardado no arquivo e fora da tela.
6. **Polígonos dos reservatórios:** não existe geometria em `data/rios/` nem em outro arquivo do repositório. Pela regra do pedido, nada de polígono aproximado por buffer do rio. Ficam **marcador + painel** até haver geometria confiável (por exemplo, o contorno oficial do lago, com fonte).
7. **Faixas operacionais da barragem:** só entram com tabela oficial ligada à barragem, à variável e à referência. Até lá, o painel não tem "atenção", "alerta" nem "emergência".

## Escala própria

- Barra horizontal sob o marcador: trilho `rgba(70,120,170,0.35)` e preenchimento `rgb(90,170,240)` (`AZUL_VAZIO` e `AZUL_CHEIO` em `logica/barragensNoMapa.ts`). É azul de propósito, porque não é cor de faixa.
- 0 a 100 % enche a barra. Acima de 100 %, a barra fica cheia com um traço extra na ponta, e o número mostra o valor real.
- Leitura velha (> 60 min): a barra fica com opacidade 0,5, o painel diz "Leitura antiga (há N h): pode ter mudado desde então" e a animação para. Sem horário: "Leitura sem horário: estado não confirmado".

## Arquivos

- `web/src/dados/barragens.ts`: leitura dos campos novos (nível com referência coerente, capacidade, divergência, fonte, limite de 200 %).
- `web/src/logica/barragensNoMapa.ts`: `fichaDaBarragem` (linhas do painel), `textoPercentual` e a paleta azul.
- `web/src/logica/mapaMotor.ts`: barra e percentual no `desenharBarragens`, e `barragemNoPonto` para o toque.
- `web/src/telas/MonitorBacia.tsx`: toque, painel compacto e expandido, interruptor de camada e legenda.
- `web/src/componentes/EstadoDasBarragens.tsx`: texto do percentual no cartão "Agora".
- Testes: `dados/barragens.test.ts`, `logica/barragensNoMapa.test.ts` e `logica/barragensNaCena.test.ts`.

## Prints

`docs/prints/barragens-2026-10-07/`:
- `barr-compacto.png`: toque na Barragem Oeste, no celular;
- `barr-expandido.png`: o mesmo painel em "Mais detalhes".
