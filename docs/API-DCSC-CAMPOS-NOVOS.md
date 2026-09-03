# GraphQL da Defesa Civil de SC — campos que faltavam (03/09/2026)

Investigação no bundle e na resposta real de `POST monitoramento.defesacivil.sc.gov.br/graphql`
(query `Tags_data`, a exata do bundle — a allowlist recusa query customizada).

---

## ❌ O que a API NÃO tem: cotas / limiares
Os únicos campos de rio são `rio_nome`, `rio_nivel`, `rio_nivel_tendencia`, `rio_area_drenagem`.
Busca por `cota|limiar|threshold|faixa|atencao|alerta|emergencia` na query: **zero**.
No bundle inteiro: só 4 ocorrências de "threshold", nenhuma ligada a nível de rio.

**Conclusão:** a API estadual **não resolve** o problema do datum. Continua valendo a regra — nível
estadual é BRUTO, e sem `offset_datum` calibrado não vira cota nem faixa. As cotas têm de vir das
Defesas Civis municipais (ofícios) ou da EPAGRI (que classifica em faixas do lado dela).

---

## ✅ O que a API TEM e o projeto não usava

### 1. `type` — tipo da estação (resolve a classificação de vez)
Das 61 estações da bacia: **Hidro 44 · Meteo 13 · Barragem 2 · Pluvio 2**.

### 2. `filter.relacao.tem_nivel_do_rio` — a API DIZ se a estação mede nível
**43 das 61 declaram medir nível de rio; 18 não.** Isso substitui adivinhação por declaração da fonte.
Também há `tem_vazao_do_rio`, `tem_chuva_acumulada`, `tem_pressao_atmosferica`, `tem_umidade`,
`tem_sensacao_termica`.

**Impacto direto: substitui a heurística frágil do coletor.** Hoje o `coleta_nivel_sc.py` descarta
estações por regra própria (nome com "(H)", valor > 30 m). Isso continua útil como rede de segurança,
mas o critério primário passa a ser `tem_nivel_do_rio`.

### 3. `rio_area_drenagem` — km² que drenam para a estação
Preenchido em apenas 2 das 61 (as barragens), mas o que veio é ouro:
| Estação | Rio | Área de drenagem |
|---|---|---|
| Barragem Sul Ituporanga | **Itajaí do Sul** | **1.164 km²** |
| Barragem Oeste Taió | **Itajaí do Oeste** | **851 km²** |

**Confirmação oficial e independente da topologia:** a própria Defesa Civil do estado nomeia os dois
rios como distintos, com áreas de drenagem próprias. Soma: **2.015 km² acima de Rio do Sul.**

**E dá o peso relativo das cabeceiras:** Sul ≈ 58%, Oeste ≈ 42% da área. Isso qualifica a regra
"pico em Rio do Sul = soma Oeste + Sul" — não é 50/50; o Itajaí do Sul pesa mais. Uma cheia vinda de
Ituporanga tende a produzir mais efeito em Rio do Sul que a mesma chuva vinda de Taió.

### 4. `homologacao` — flag de homologação do dado (investigar o significado)

---

## 🔧 Correções que estes campos impõem ao projeto

| Registro atual | Correção |
|---|---|
| **Blumenau DCSC-00026** — eu havia concluído "é estação de chuva" a partir de estar a 3 km do rio e nunca reportar nível | **CONFIRMADO pela fonte:** `type = "Meteo"`, `tem_nivel_do_rio = false`. Não é dedução mais, é declaração. |
| **Gaspar DCSC-00005** — registrado como "tem sensor de rio, reporta de forma intermitente" | **ERRADO. `tem_nivel_do_rio = false`.** Gaspar NÃO mede nível de rio na rede estadual. Não é intermitência — é ausência. Corrigir o registro e parar de esperar leitura dela. |
| **Guabiruba DCSC-00029** — 24,81 m, marcada como "suspeita, ~4 km do talvegue" | `type = "Hidro"`, `tem_nivel_do_rio = true`. A estação **é** de rio; o valor alto continua suspeito (datum próprio), mas não é erro de tipo. |
| **Pomerode DCSC-00007** — marcada como "oscila absurdo, sensor suspeito" | `type = "Hidro"`, `tem_nivel_do_rio = true`, agora 0,72 m. É estação de rio de verdade; a oscilação é de datum/escala, não de tipo. |

## Leituras no momento da consulta (03/09 ~13:56 UTC), nível BRUTO
Ituporanga 3,71 · Taió 4,65 · Ilhota 9,53 · Vidal Ramos 2,57 · Pomerode 0,72 · Timbó 2,04 ·
Indaial 6,22 · Ibirama 2,46 · Botuverá 3,14 · Ascurra 7,99 · Guabiruba 24,81 ·
Barragem Sul 26,17 · Barragem Oeste 17,40. **Gaspar e Blumenau: não medem nível nesta rede.**

## Tarefa para o coletor
Em `coleta_nivel_sc.py`, acrescentar à query os campos `type` e `filter { relacao { tem_nivel_do_rio
tem_vazao_do_rio tem_chuva_acumulada } }` e `rio { rio_nome rio_area_drenagem }` — **usando a query exata
do bundle** (a allowlist recusa query montada à mão). Gravar `tipo_estacao` e `declara_nivel` em cada
leitura; descartar por `declara_nivel === false` antes de aplicar as heurísticas atuais.

## Estado desta tarefa
**03/09/2026**: as correções de classificação (Gaspar, Blumenau, Guabiruba, Pomerode) foram aplicadas em
`coleta_nivel_sc.py` como valores hardcoded (`NAO_MEDE_NIVEL`, `SUSPEITAS` reescrito) — mesmo padrão
já usado para `SUSPEITAS` desde a versão de 01/09. A adição dos campos novos à `QUERY` em si não foi
feita: quem investigou este documento tinha acesso à resposta real da API; a sessão que aplicou a
correção não tem acesso de rede a este host (roda só na VPS) e por isso não podia validar a string
exata do bundle.

**04/09/2026**: adicionada `QUERY_CAMPOS_NOVOS` em `coleta_nivel_sc.py`, com `type`,
`filter { relacao { tem_nivel_do_rio tem_vazao_do_rio tem_chuva_acumulada } }` e
`rio { rio_nome rio_area_drenagem }` — reconstruída por nome de campo, não copiada do bundle (este
ambiente segue sem acesso de rede ao host). Para não arriscar quebrar o coletor em produção com uma
string não testada, `buscar()` tenta essa query primeiro e cai automaticamente para a `QUERY`
original (validada em 01/09) se a API devolver `errors` — nunca decide às cegas qual string
funciona. `converter()` já sabe usar os campos quando eles vêm (prioridade sobre os dicionários
hardcoded) e ignorá-los quando não vêm (comportamento idêntico ao de antes).

**04/09/2026 (mesmo dia, confirmação real na VPS): a allowlist RECUSA `QUERY_CAMPOS_NOVOS`** —
`400 Client Error: Bad Request`. O fallback funcionou: o coletor caiu para a `QUERY` original e
rodou normalmente (25 leituras, nenhum erro fatal). A reconstrução por nome de campo, sem a string
exata do bundle, não passa pela allowlist — confirma o aviso original deste documento ("usando a
query exata do bundle — a allowlist recusa query customizada"). `type`/`tem_nivel_do_rio`/
`rio_area_drenagem` continuam vindos como `None`; as classificações de Gaspar/Blumenau/Guabiruba/
Pomerode seguem só pelos dicionários hardcoded. Para destravar isto de verdade, alguém precisa
capturar a query exata que o bundle do site envia (inspecionando a aba Network de um navegador real
em `monitoramento.defesacivil.sc.gov.br/mapa`, não reconstruindo por nome de campo) — ver
`docs/coleta-nivel-estadual.md`.
