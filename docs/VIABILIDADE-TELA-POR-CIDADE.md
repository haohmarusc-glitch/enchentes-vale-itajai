# Viabilidade: tela por cidade com ruas alagadas e mancha gerada

Pedido (04/09/2026): (A) clicar no trecho do rio no Monitor e abrir a tela da cidade; (B) colorir as ruas
pela cota × nível atual; (C) **gerar uma mancha** no mapa, do rio até as ruas que "possivelmente" estão
com água, a partir das cotas de rua.

Resposta curta: **A e B são viáveis e valem a pena. C é tecnicamente possível e eu recomendo NÃO fazer
do jeito pedido** — porque produz uma imagem que parece medição e é modelo. Há uma alternativa honesta
que entrega quase o mesmo valor.

---

## O que existe hoje (inventário)

> ⚠️ **Contagens conferidas contra este repositório em 04/09/2026.** O documento original veio de
> outra linhagem de checkout e trazia números que não batem com o `data/` daqui; a tabela abaixo é a
> medida no repositório. O raciocínio do documento não muda — a divisão "quem tem coordenada e quem
> não tem" se confirma —, mas os totais sim.

| Cidade | Cotas em `cotas-ruas.json` | Coordenada | Mancha observada | Nível em tempo real |
|---|---|---|---|---|
| **Gaspar** | 1.619 | **sim** — `brutos/gaspar-cotas-2020.json`, 1.615 pontos com `lat`/`lon` | — | sim (DC Gaspar) — mas cota da régua em aberto |
| **Brusque** | 377 | **sim** — `brutos/brusque-cotas-2023.json`, 357 com `lat`/`lon`; e `brusque-mymaps-cotas.json`, 3.688 com a coordenada em `coord` (`"lon,lat,0"`, ainda não separada em campos) | — | sim (régua municipal) |
| Blumenau | 2.042 | **não** — só nome de rua e bairro | — | sim (AlertaBlu) |
| Rio do Sul | 555 | **não** | — | sim (3 réguas) |
| Itajaí | **nenhuma** (cota por endereço, ArcGIS fechado) | — | **10 manchas 1983–2015** (`data/manchas/itajai/`) | 11 réguas |

~~O `cotas-ruas.json` consolidado **não tem campo de coordenada nenhum**~~ — **feito em 04/09/2026.**
`scripts/juntar_coordenadas_cotas.py` levou a coordenada dos brutos para o consolidado:
**1.613 linhas de Gaspar** (por alinhamento de sequência — a ordem do bruto foi preservada, e é ela que
resolve as ruas repetidas) e **348 de Brusque** (por chave `(rua, cota)` — a ordem se perdeu). Ficaram
**2 linhas de Brusque sem coordenada** de propósito: a chave "General Osório, 7,87" tem dois pontos
reais a ~330 m um do outro e uma linha só no consolidado, então não há como saber qual — e escolher um
seria pintar 330 m de rua errada.

O bruto `brusque-mymaps-cotas.json` (3.688 pontos, com coordenada) **fica proibido**, pelo motivo que o
`_meta` dele mesmo dá: *"NÃO IMPORTADO. O campo `cota` deste arquivo não pôde ser identificado como
nível de régua."* Coordenada boa não redime cota não verificada. O script recusa por nome, com teste.

Itajaí tem ainda **5.237 pontos cotados altimétricos** (`brutos/itajai-pontos-cotados-altimetricos.geojson.json`).
O `_meta` do próprio arquivo avisa: é **altura do terreno, não cota de régua** — falta o offset para a
régua, que é a mesma pendência de datum do item 3 da alternativa honesta, abaixo.

Dois fatos que decidem o desenho:
- **Só Gaspar e Brusque têm cota de rua georreferenciada na fonte.** Blumenau e Rio do Sul precisam de
  geocodificação (nome da rua → traçado no OSM) antes de qualquer mapa.
- **Só Itajaí tem mancha observada** — e é a única cidade SEM cota de rua. Os dois modelos não se sobrepõem.

---

## (A) Tela por cidade — ✅ **JÁ FEITA** (conferido em 04/09/2026)

Existe: rota `/:rioId/:cidadeId` em `web/src/App.tsx`, tela em `web/src/telas/TelaCidade.tsx`, com
`ReguasDaCidade` (várias réguas separadas, via `reguasComCota`), `MapaRios` e `LinhaDoTempo`.
O que segue é a especificação original, mantida como registro do que a tela deve preservar —
**não é trabalho a fazer.**

Clicar no trecho do rio no Monitor → `#/cidade/<id>`. O mapa da cidade com: o rio (traçado real), as réguas
da cidade (Itajaí tem 11, Rio do Sul tem 3+), o nível de cada uma com fonte e idade, as cotas de cada
régua, os abrigos (Itajaí 45, Rio do Sul 23, Gaspar 28 — Gaspar com cota própria), o histórico da cidade
(Gaspar 69 eventos, Blumenau 102), e o `fitBounds` na bbox da cidade.

Custo: baixo. Os dados existem; é roteamento + composição do que já está em `estacoes.json`.
Ganho: resolve o problema que a auditoria apontou — o Monitor geral não consegue mostrar 11 réguas de
Itajaí num pino só, nem as 3 de Rio do Sul.

**Regra a preservar:** a tela da cidade herda a coloração por faixa **da régua**, não do metro. Rio do Sul
mostra as três réguas separadas, com "os metros não se comparam entre elas" à vista.

---

## (B) Ruas coloridas por cota × nível — VIÁVEL em 2 cidades, com uma condição
Lógica: para cada rua com cota `c` e nível atual `n`: `n ≥ c` → "cota atingida"; `c − n < 0,5` → "próxima";
senão neutra. É o que o site já faz no slider "E se o rio estivesse em X" — só que no mapa.

**⚠️ Correção de 04/09/2026 — Brusque NÃO pode entrar já.** A versão original deste documento dizia
que sim. Conferido no cadastro e no coletor, não passa pela condição que o próprio documento impõe
mais abaixo ("rua colorida só onde `cotas_verificado = true` e a régua da cota = régua da leitura"):

| o que | Brusque |
|---|---|
| `cotas_verificado` em `estacoes.json` | **`false`** — e `fonte_cotas` é `null` |
| régua das cotas de rua | **Ponte Estaiada**, e isto está bem provado: o `_meta` do bruto registra cota + lâmina = 8,96 m (o pico de 17/11/2023) em **183 dos 184** pontos que têm lâmina |
| régua da leitura ao vivo | **não identificada** — as duas estações de Brusque em `estacoes_tempo_real` têm `regua: null` |
| de onde vem a leitura | `coleta_itajai.py`, isto é, a página da Defesa Civil **de Itajaí** — a MESMA que publica Rio do Sul |

Esse último item é o que decide. Foi exatamente nessa página que a leitura de **Rio do Sul** apareceu
como "Estação MKS" enquanto a cota era da "Ponte Dom Tito Buss" — réguas diferentes, e a cabeceira do
Açu ficou permanentemente amarela por causa disso. (O `conferir_par_regua.py` acabou provando que ali
eram a MESMA régua; o ponto não é que a página erre, é que **ninguém sabia**, e a resposta só veio de
medir.) Colorir 348 ruas de Brusque sobre um pareamento não provado multiplica o mesmo risco rua a rua.

**O que destrava, e não é ofício:** a segunda fonte já está mapeada. A ficha
`docs/cotas-municipais/brusque.md` registra o portal próprio da Defesa Civil de Brusque,
`https://defesacivil.brusque.sc.gov.br/monitoramento`, com **6 réguas de nível minuto a minuto** e a
câmera da ponte estaiada — é a página da régua a que as cotas pertencem. Capturar essa página de dentro
da região (ou da VPS), cadastrar o par em `conferir_par_regua.py` e rodar: se os dois números baterem,
as 348 ruas destravam.

O que falta para fazer isso é ver a página. Ela não responde de fora da região (`connect_rejected`,
igual à de Gaspar — mesma stack DEXTAK), e o `conferir_par_regua.py` de hoje só sabe ler o painel da
Asthon (`stations[].level_m`). Brusque vai precisar de um leitor próprio, escrito **contra o HTML real**,
como o `coleta_itajai.py` foi — nunca contra uma estrutura suposta.

Brusque só parecia liberada porque o número dela não chama atenção.

**Gaspar: também bloqueada**, pelo motivo já conhecido (`BLOQUEIO_NAO_PINTAR`) — não está provado que
a régua que o coletor lê é a da cota 6/7 m. Colorir rua com nível de régua errada é o mesmo erro, só
que rua por rua. Resolver o teste do par cota↔leitura antes.

Ou seja: **as duas cidades georreferenciadas estão bloqueadas pela mesma pergunta**, e é a mesma que
já trava Rio do Sul. Não é coincidência — é o formato do problema: cota e leitura vêm quase sempre de
páginas diferentes, e nome igual não prova régua igual.

**Blumenau e Rio do Sul: só depois de geocodificar.** Casar 2.042 nomes de rua com traçados do OSM é
factível (Nominatim/Overpass), mas com erro: ruas homônimas, grafias diferentes, trechos longos com cota
única. Tem que ser feito **uma vez, revisado, e gravado** — não em runtime. E cada rua geocodificada
precisa de `confianca` (casou exato / casou aproximado / não casou).

**Condição que vale para as quatro:** a cota de rua está na referência da régua da cidade. Comparar com o
nível **daquela** régua é válido. Comparar com nível de outra fonte (estadual bruto, por exemplo) não é.

**Como mostrar:** rua como **segmento colorido**, com o número: "Rua X · cota 8,20 m · rio a 7,45 m ·
faltam 0,75 m". Isso é **dado**: a cota foi levantada, o nível foi medido, a subtração é aritmética.

---

## (C) Mancha gerada do rio até as ruas — POSSÍVEL, mas eu recomendo NÃO
### Por que não
Uma mancha é um **polígono contínuo**. As cotas de rua são **pontos** (ou segmentos). Para virar polígono é
preciso **interpolar** entre os pontos — e a interpolação inventa o que acontece nos vazios: entre uma rua
de cota 8 e outra de cota 9, o polígono decide sozinho onde passa a linha d'água. Na realidade essa linha
depende do **terreno** (um quintal mais baixo, um muro, um bueiro), que a cota de rua não descreve.

O resultado é uma imagem que **parece a mancha observada de Itajaí** (que é levantamento de campo pós-
evento) mas é um chute geométrico. É exatamente a regra do projeto — *"estimativa nunca vira medição"* —
violada em forma visual, onde é mais convincente e mais difícil de questionar.

Os dois erros possíveis são graves nos dois sentidos:
- A mancha **não cobre** a casa do morador → ele se sente seguro → é a falha que o protocolo de teste chama
  de "a pergunta que mais importa".
- A mancha **cobre** onde não há água → alarme falso → o morador aprende a ignorar o site.

O Kikikuru (JMA), que é a referência do projeto, **não gera mancha em tempo real**. Mostra nível observado
e mapas de risco oficiais. A decisão deles é deliberada.

### A alternativa honesta — entrega quase o mesmo
1. **Ruas como pontos/segmentos discretos** (item B), sem preencher entre eles. O morador vê "a Rua X está
   com cota atingida; a Rua Y, não" — e a ausência de cor entre as duas diz corretamente "não sabemos".
2. **Mancha observada como referência, por nível.** Onde há mancha real (Itajaí, 10 eventos), ao invés de
   gerar: *"o rio está em 2,8 m; em 2015 chegou a 3,1 m e a água alcançou até AQUI"* — e desenha a mancha
   **de 2015**, rotulada como "observada em 2015", não como "agora". É dado histórico usado como régua
   visual. Para Gaspar (69 eventos com pico) dá para fazer o mesmo **se** houver mancha por evento — hoje
   não há.
3. **"Até onde a água chegaria" só com DEM.** Se um dia o projeto quiser mancha calculada de verdade, o
   caminho é o modelo digital de terreno (os 5.237 pontos cotados de Itajaí são um começo, mas estão em
   datum altimétrico — precisa do offset para a régua, que ainda não temos). E mesmo assim, rotulada como
   simulação, com o modelo e a data à vista. É outro projeto.

---

## Recomendação
| Parte | Fazer? | Quando |
|---|---|---|
| A — tela por cidade | ✅ **feita** | `TelaCidade.tsx`, rota `/:rioId/:cidadeId` |
| B — ruas por cota × nível | a coordenada já está no `cotas-ruas.json` (1.613 Gaspar + 348 Brusque), mas **as duas cidades estão bloqueadas** pelo par cota↔leitura não provado | após o teste do par, nas duas |
| B — Blumenau e Rio do Sul | Sim, após geocodificação revisada | depois |
| C — mancha gerada por interpolação | **Não** | — |
| C' — mancha observada por nível (Itajaí) | **Sim** | após A |

**O que preserva a confiança:** tudo que aparece no mapa da cidade tem que ser uma de três coisas — uma
**medição** (nível), um **levantamento** (cota de rua, mancha histórica) ou uma **conta aritmética entre os
dois** (faltam X m). Um polígono interpolado não é nenhuma das três.

## Verificação antes de fechar
- [ ] Clicar no trecho do rio abre a cidade certa, com `fitBounds` na bbox dela
- [ ] Rio do Sul mostra 3 réguas separadas; Itajaí mostra 11 — sem misturar metros
- [ ] Rua colorida só onde `cotas_verificado = true` e a régua da cota = régua da leitura
- [ ] Nenhum polígono preenchido que não venha de arquivo de mancha observada, rotulado com o ano
- [ ] Toda rua colorida mostra cota, nível e diferença — o número, não só a cor
