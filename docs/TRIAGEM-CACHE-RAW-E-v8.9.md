# Triagem: o documento das "duas armadilhas" e o zip v8.9 — 04/09/2026

Chegaram juntos um relato de outra sessão (`CACHE-RAW-E-QUERY-RECUSADA.md`) e um snapshot
(`enchentesvaleitajaiv8.9.zip`). O relato faz duas afirmações verificáveis, e uma delas propõe uma
**regra nova de método**. Regra de método muda o comportamento de todas as sessões seguintes, então
foi medida antes de ser adotada. Este arquivo registra o que a medição deu.

---

## 1. "O `raw.githubusercontent.com` serve cache — nunca verifique deploy por ele"

### A afirmação
A sessão leu `serie-recente.json` pelo `raw.…`, viu um arquivo gerado **15:16 UTC** sem a chave
`reguas`, enquanto a VPS tinha `reguas: True` gerado às **22:01 UTC** — "quase 7 horas atrasado" —, e
concluiu que o `raw` serve cache de CDN. A partir daí escreveu três especificações de trabalho que já
estava no `main`.

### O que a medição deu — NÃO REPRODUZ

| rodada | `gerado_em` servido | atraso | tem `reguas` |
|---|---|---|---|
| 22:22 UTC (2 leituras seguidas) | 22:16:21 | **6 min** | sim |
| 22:29 UTC (2 leituras seguidas) | 22:16:21 | **13 min** | sim |
| 22:31 UTC (3 arquivos) | 22:16:21 / 22:16:21 / 22:16:25 | **15 min** | sim |

O cron publica a cada 15 minutos. **A idade observada é exatamente a idade esperada de um arquivo
publicado a cada 15 min** — não há atraso a explicar. E, nesta mesma sessão, uma leitura das 15:16 sem
`reguas` passou a `reguas: True` às **15:31** — 15 minutos, não 7 horas.

Prova adicional: a API do GitHub (`/commits/tempo-real`), que a própria sessão propôs como alternativa
*por não usar o mesmo cache*, dá o topo do branch em **22:16:25Z** — o mesmo segundo do conteúdo que o
`raw` entregou. **As duas vias concordam.**

### Por que a regra proposta é a errada, mesmo se o sintoma foi real
**O site lê pelo `raw`.** `web/src/dados/serie.ts`, `tempoReal.ts` e `nivelSc.ts` buscam os três
arquivos por `raw.githubusercontent.com`. Se o `raw` servisse conteúdo de 7 horas atrás, o problema
não seria "não verifique deploy por aí" — seria **todo morador vendo nível de rio de 7 horas atrás**.
A regra proposta trata como estorvo de verificação o que, se verdadeiro, é defeito de produção.

E o sintoma tem duas causas que uma leitura só **não distingue**:

| causa | quem conserta | gravidade |
|---|---|---|
| (a) o `raw` serve cache velho | ninguém aqui — e o site está entregando dado velho | grave |
| (b) a publicação da VPS travou por horas | o cron da VPS | grave, e o vigia devia pegar |
| (c) a leitura caiu no minuto de uma publicação em curso | ninguém | nenhuma |

Não dá para escolher entre (a) e (b) olhando o arquivo — e escolher errado manda consertar a metade
errada do caminho. O histórico do branch também não ajuda: `tempo-real` é órfão com `push --force`,
tem **um commit só**, e não guarda a lacuna.

### O que foi feito em vez de adotar a regra
`scripts/conferir_publicado.py` — lê três relógios no mesmo instante (o que o `raw` entrega, o que a
VPS gerou localmente, e o topo do branch pela API do GitHub) e separa as três causas, com
**"NÃO DÁ PARA DIZER"** quando a API não responde. Fecha o único trecho do caminho que ninguém vigiava:

```
VPS  →  branch tempo-real  →  raw.githubusercontent.com  →  navegador
        └────────── o saude_coleta.py não olha daqui para a frente ─────────┘
```

O vigia responde "a coleta rodou?" e "a fonte publicou?", lendo arquivos **locais**. Nenhuma das duas
cobre a entrega ao morador.

Rodar na VPS, onde a API do GitHub é alcançável (deste ambiente ela dá 403):

```
python3 scripts/conferir_publicado.py
```

### A parte da lição que é boa e fica
**Comparar `gerado_em` com o relógio em toda leitura de arquivo publicado.** É certo, é barato, e o
site já faz o equivalente para o morador: `idadeMin()`/`frescor()` em `web/src/logica/tempoReal.ts`
mostram a idade da leitura na tela. Uma leitura velha nunca é silenciosa para quem olha o site — só
era silenciosa para quem olhava o arquivo.

---

## 2. "A query do GraphQL estadual com os campos novos está sendo recusada" — CONFIRMADO, e já tratado

Confere com o código. `scripts/coleta_nivel_sc.py` tem `QUERY_CAMPOS_NOVOS`, tenta primeiro, e
`buscar()` cai para a `QUERY` de 01/09 quando a API recusa — imprimindo exatamente o aviso citado. Está
documentado como armadilha 9 no docstring do próprio coletor, com a razão (allowlist de query
persistida) e o caminho da solução (extrair a query exata do bundle, sem editar).

O documento diz "nada a consertar com urgência", e é a leitura certa: o fallback é o comportamento
correto e o aviso no log é o comportamento correto. **Nada a fazer.**

---

## 3. O zip v8.9 — o que entrou e o que não entrou

O zip é de **outra linhagem de checkout**, e está muito atrás deste repositório: **11 scripts contra
114**, sem `.github/`, sem `data/rios/`, sem `data/manchas/`, sem `data/hidraulica.json`, e com as
cotas ainda em quatro arquivos separados em vez do `cotas-ruas.json` consolidado. Os documentos de
04/09, esses sim, são novos.

### Entrou (3 documentos, conferidos contra o `data/` daqui)
| Documento | Por que entrou | O que foi corrigido na importação |
|---|---|---|
| `MDT-SC-E-CARTA-ENCHENTE.md` | MDT de 1 m da SDS/SC, gratuito, cobrindo o Vale; e a **acurácia medida** da carta-enchente do CEOPS (Blumenau 89,05 %, Timbó 74,1 %) | contagem de cotas de Blumenau (2.042 aqui, não 2.034); anotada a terceira contagem (1.851) que já estava em `fontes-academicas.md` |
| `PARTE-C-COMO-OS-PAISES-FAZEM.md` | Kikikuru, FIMAN e Environment Agency: **nenhum interpola cotas de rua em tempo real** — precedente para a regra do projeto | nada a corrigir; as 3 afirmações sobre dado nosso conferem |
| `VIABILIDADE-TELA-POR-CIDADE.md` | inventário e recomendação sobre tela por cidade, ruas coloridas e mancha gerada | tabela de inventário refeita com os números daqui; item (A) marcado como **já feito** (`TelaCidade.tsx`) |

Verificações que passaram: Timbó 2011 = 9,86 m ✅ · Blumenau 2011 com 13,00 m do CEOPS em
`divergencias` ✅ · 10 manchas em `data/manchas/itajai/` ✅ · 5.237 pontos cotados ✅ e o `_meta` deles
avisando que são **altura de terreno, não cota de régua** ✅.

Verificação que **falhou** e por isso a tabela foi refeita: o documento dizia "Brusque e Gaspar 100 %
georreferenciadas". O `cotas-ruas.json` consolidado **não tem campo de coordenada nenhum**. As
coordenadas existem, mas só nos brutos (`gaspar-cotas-2020.json`, 1.615 com `lat`/`lon`;
`brusque-cotas-2023.json`, 357). Levar as coordenadas dos brutos para o consolidado é **trabalho a
fazer**, não dado pronto — e era pré-requisito silencioso de "colorir as ruas".

### Não entrou
| O que | Por quê |
|---|---|
| `TAREFA-1-CONSERTAR-SERIE-ITAJAI.md`, `TAREFA-REGUAS-E-SERIE.md` | são as especificações que o próprio relato reconhece como trabalho já pronto (`reguas` na série, `conferir_saltos_serie.py`, `conferir_par_regua.py`) |
| `TESTE-NAVEGADOR-RESULTADO.md` | declara que os testes visuais **não foram executados**; a análise que traz é a da leitura em cache |
| `docs/cotas-por-cidade/` (40 fichas) | o repositório já tem as 40 em `docs/cotas-municipais/`, e a de Vidal Ramos **daqui é mais nova** (traz a medição do `panel` da Asthon, de 04/09) |
| `docs/cotas-por-cidade/taio.md` | é o mesmo conteúdo de `docs/TAIO-API-E-COTAS.md` |
| `REGUAS-RIO-DO-SUL.md`, `ALARME-FALSO-REGUAS-ITAJAI.md`, `COTAS-LEVANTAMENTO.md` | já triados antes, em `docs/reguas-rio-do-sul.md` e nos documentos do dossiê |
| todo o `scripts/`, `web/` e `data/` do zip | linhagem atrasada; importar qualquer arquivo daí desfaria trabalho |

---

## 4. A regra de método que sobra

O relato termina com *"antes de afirmar que algo falta, procurar onde estaria se existisse"*. É certo, e
vale igualmente para a afirmação contrária: **antes de adotar uma regra a partir de um sintoma,
reproduzir o sintoma.** Uma leitura não distingue cache de publicação travada, e a regra que sairia de
cada uma é diferente. Quando reproduzir é caro ou o momento passou, o que resta não é escolher a
explicação mais plausível — é **construir a medição** que separa as duas na próxima vez.
