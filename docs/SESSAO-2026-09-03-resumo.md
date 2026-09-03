# Sessão 03/09/2026 — resumo para o Claude Code

Sequência do dia: camadas de mapa → API estadual → API Asthon → sites das Defesas Civis.
**8 correções de dados e 6 achados novos.** Onde este doc e o `main` divergirem, o `main` manda.

---

## CORREÇÕES DE DADOS (aplicar com prioridade)

| # | O que estava errado | Correto | Onde |
|---|---|---|---|
| 1 | Gaspar: cotas "5/6/7" | **6,00 (atenção) / 7,00 (emergência)**. Só 2 cotas, 3 estados, SEM faixa de alerta. Atenção dispara por nível **OU chuva > 6 mm** | `estacoes.json` ✅ |
| 2 | Gaspar DCSC-00005 "tem sensor, reporta intermitente" | **`tem_nivel_do_rio = false`** — NÃO mede nível na rede estadual. Não é intermitência, é ausência | `_correcoes` ✅ |
| 3 | Blumenau DCSC-00026 (dedução: "é de chuva") | **CONFIRMADO pela fonte:** `type = "Meteo"`, `tem_nivel_do_rio = false` | `_correcoes` ✅ |
| 4 | "API Asthon entrega cotas para 21 réguas" | **11** têm cota; 21 têm sensor. 10 sem cota, incl. **Vidal Ramos** | `API-ASTHON-COMPLETA.md` ✅ |
| 5 | "Oeste 5,48 > Açu 5,25 é erro de datum" | **ERRADO.** Canal do Açu é mais largo → mesma água, menos altura. Não é problema de datum | `REGUAS-RIO-DO-SUL.md` ✅ |
| 6 | Mirim com `ordem` global | `ramo: mirim_tronco` + `ordem_no_ramo` | `estacoes.json` ✅ |
| 7 | Timbó 2011 com `rio: itajai-acu` | `rio: benedito` (afluente) | `enchentes.json` ✅ |
| 8 | `rio-do-sul → indaial = 10 h` (contradiz Blumenau 7 h) | Modelo de **âncoras + derivação por distância**, monotônico por construção | `JANELA-DE-CHEGADA.md` ✅ |

---

## ACHADOS NOVOS

### 1. ⚠️ A Barragem Oeste tem DOIS REGIMES — quebra previsão
Defesa Civil de Taió: *"a barragem Oeste está cheia e vertendo em mais de 1 metro… a chuva que cai sobre
as localidades acima de Taió **não é mais retida pela estrutura**"*. São **7 comportas**, operadas uma a uma.
- **Retendo:** amortece a chuva de montante
- **Vertendo:** deixa de amortecer, a água passa direto

Correlação calibrada no primeiro regime **subestima drasticamente** o segundo. Provável parte da
explicação das correlações fracas no Alto Vale, junto com a topologia em árvore.
**LACUNA NOVA:** coletamos o *nível* das barragens, não o *estado das comportas*. O site deveria mostrar
"retendo × vertendo" junto do nível de Taió e Rio do Sul. Verificar se `dams` da Asthon traz comportas.
Provável que a Barragem Sul (Ituporanga) tenha o mesmo comportamento.

### 2. Gaspar: 69 enchentes (1852–2023) + a quebra de 1986 visível nos dados
Baixado `gaspar-historico-enchentes.json`. O projeto não tinha nenhum evento de Gaspar.
Picos: 1880 = 12,56 · 1911 = 12,42 · 1852 = 12,00 · 1983 = 11,50 · 1984 = 11,40 · 2008 = 9,80.
**55 eventos antes de 1986, 14 depois.** Antes, picos de 9 a 12,5 m eram comuns; depois, o maior é 9,80.
Consistente com a **retificação e alargamento do canal na divisa Blumenau/Gaspar em 1986**
(Santos & Pinheiro, Rev. Bras. Geomorfologia, 2002): canal mais largo marca menos altura para a mesma água.
**Não é que as cheias diminuíram — é que a régua mudou.** NUNCA comparar pico pré e pós-1986.

### 3. Gaspar: 28 abrigos COM COTA PRÓPRIA (único na bacia)
Baixado `gaspar-abrigos.json`. 1.110 famílias. **14 abrigos informam a cota do rio a partir da qual são
atingidos** (6, 9, 10, 11, 12, 14, 15 m). Itajaí (45) e Rio do Sul (23) não têm esse campo.
Permite dizer *"com o rio em X m, estes abrigos seguem acima da água"*.
⚠️ **Unidades incompatíveis:** Gaspar conta FAMÍLIAS, Itajaí VAGAS, Rio do Sul PESSOAS. Nunca somar.

### 4. API estadual: `type` e `tem_nivel_do_rio` + área de drenagem
Das 61 estações da bacia: Hidro 44 · Meteo 13 · Barragem 2 · Pluvio 2; **43 declaram medir nível**.
Substitui a heurística do coletor (nome "(H)", valor > 30 m) por declaração da fonte.
**`rio_area_drenagem`:** Itajaí do Sul **1.164 km²** × Itajaí do Oeste **851 km²** → 58% / 42%.
Qualifica a regra "pico em Rio do Sul = soma Oeste + Sul": **não é 50/50**.
⚠️ A API estadual **NÃO tem cotas/limiares** — buscado em toda a query e no bundle.

### 5. Rio do Sul: 3 réguas em 3 rios diferentes — o melhor dado de calibração da bacia
Ponte Dom Tito Buss (**Açu**, tronco) · Ponte Ricardo Kanitz (**Itajaí do Sul**) · Ponte BR 470
(**Itajaí do Oeste**). Mais a Ponte Hannelore Hartmann (Itajaí do Sul).
**As duas entradas e a saída medidas na MESMA cidade** — dá para calibrar a soma das cabeceiras sem
correlacionar cidades distantes.
✅ **Confirmado pelo usuário e pela API: as cotas são POR RÉGUA** ("a altitude muda muito na cidade").
As 4 pontes do centro compartilham 4,5/5,5/6,5 porque estão em altitude semelhante e os zeros foram
calibrados para o mesmo significado de risco; os ribeirões têm limiares de 1 a 3,7 m.
⚠️ **Duas entradas para a Ponte Dom Tito Buss** ("…" e "… - DCSC"), leituras diferentes no mesmo instante
(5,36 e 5,53). Investigar qual é a oficial antes de coletar — senão duplica a régua do tronco.

### 6. Só 5 das 23 cidades da bacia têm portal próprio de Defesa Civil
Itajaí · Blumenau · Rio do Sul · Gaspar · **Taió** (novo, não explorado).
As outras 18 dependem só da rede estadual → nível bruto sem cota. **A regra `usar_para_cota=false` afeta
tantas cidades por ausência de fonte municipal, não por limitação do coletor.**
E cada um dos 5 portais tem algo que os outros não têm — não existe formato comum, cada integração é sob medida.

---

## PENDÊNCIAS ABERTAS (acionáveis)
1. **`defesacivil.taio.sc.gov.br`** — não explorado (permissão do navegador negada 3×). Buscar: cotas,
   histórico, abrigos e **estado das comportas** da Barragem Oeste. Pico conhecido: **12,11 m em 09/10/2023**.
2. **Exportar as cotas de rua de Rio do Sul** pelo próprio site: `index.php?r=soscota-rua/tabela` tem
   **555 itens e botão "Exportar Dados"** — é a fonte exata dos nossos dados, e exportar é melhor que raspar.
3. **"Planilha Histórica Rio"** no menu de Rio do Sul — fecharia o histórico da cidade, hoje lacuna.
4. **Estado das comportas** das barragens Oeste e Sul (ver achado 1).
5. Páginas de Gaspar não abertas: `/cotas` (busca por endereço), `/barragens`,
   `/mapas/rota-de-fuga-para-os-abrigos` (único na bacia), `/plano-de-contingencia`.
6. **Correlação Blumenau↔Gaspar do CEOPS/FURB** — existe estudo publicado que estendeu a série de Gaspar
   com os picos de Blumenau "através de uma correlação" + Gumbel. Pedir no ofício à FURB: o coeficiente e
   as cotas por período de retorno. Substituiria a interpolação por distância naquele trecho.
7. **Camadas de mapa** — decisão tomada, spec em `docs/CAMADAS-DE-MAPA.md`. Começar pela tela de Itajaí.

## Arquivos baixados nesta sessão (mover para `data/brutos/`)
`gaspar-historico-enchentes.json` · `gaspar-abrigos.json` · `rio-do-sul-estacoes-cotas.json` ·
`rio-do-sul-rios-tracados.geojson` (10 rios, inclui as duas cabeceiras) ·
`dcsc-estacoes-coordenadas-bacia-itajai.json` · `cemaden-estacoes-bacia-itajai.json`

## Docs criados hoje
`CAMADAS-DE-MAPA.md` · `API-DCSC-CAMPOS-NOVOS.md` · `API-ASTHON-COMPLETA.md` · `REGUAS-RIO-DO-SUL.md` ·
`JANELA-DE-CHEGADA.md` · `GASPAR-DADOS-NOVOS.md` · `PORTAIS-POR-CIDADE.md` · `TAIO-E-BARRAGEM-OESTE.md` ·
`AIBH-ITAJAI-ACU.md` · `TOPOLOGIA-CANONICA.md`
