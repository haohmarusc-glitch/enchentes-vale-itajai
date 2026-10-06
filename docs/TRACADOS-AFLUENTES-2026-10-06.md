# Afluentes sem traçado no Monitor (06/10/2026)

Na inspeção visual de 06/10/2026, o Jefferson achou cinco cidades com pino e leitura, mas sem a linha do rio
junto à régua: Guabiruba, Timbó, Rio dos Cedros, Trombudo Central e Ituporanga.

## A causa, por cidade

O código desenha **todo** arquivo de `data/rios/`, em cinza, sem depender de leitura, cota ou faixa
(`OUTROS_TRACADOS` no Monitor). A cor só pinta trecho de tronco ou cabeceira com cidade e faixa. Por isso,
em todos os cinco casos, a linha faltava porque o **arquivo não existia**. A linha não estava escondida por
filtro, recorte ou falta de classificação.

| Cidade | Curso | Antes | Causa |
|---|---|---|---|
| Timbó | Rio Benedito | sem `benedito.geojson` | o traçado nunca foi baixado: o Overpass não responde à sessão |
| Rio dos Cedros | Rio dos Cedros | sem arquivo | idem |
| Trombudo Central | Rio Trombudo | sem arquivo | idem |
| Ituporanga | Rio Itajaí do Sul | só 10,5 km perto de Rio do Sul (Asthon) | o arquivo parava 21 km antes da régua |
| Guabiruba | Rio Guabiruba Norte → Rio Guabiruba | sem arquivo | idem; e o curso medido não era o que o nome da cidade sugere (abaixo) |

As cinco leituras e faixas não mudam: pino e cor seguem como estavam.

## Como entraram

1. `scripts/baixar_tracados_afluentes.py` pede cada rio ao Overpass pelo **nome exato**. Antes de gravar, ele
   confere:
   - o rio passa pela régua da cidade (`passa_km`);
   - ele **chega** a um rio já desenhado. A chegada conta só pelas linhas ligadas, por vértice comum, à linha
     da régua (`componente_da_regua`): um pedaço solto com o mesmo nome não prova continuidade.

   Rio que falha não grava. O script guarda o que veio e os cursos d'água a 1,5 km da régua, para a decisão
   ser feita à mão. Uma rodada caiu por timeout do espelho do Overpass e foi rodada de novo uma vez.
2. O script roda no GitHub Actions (`baixar-tracados-afluentes.yml`). Os brutos e o resumo vão para o branch
   `tracado-afluentes`.
3. `converter_tracado_rios.py` gera `data/rios/<id>.geojson`. Ele recorta na **caixa do mapa** (extensão do
   tronco e das réguas do cadastro) com **folga de 1,5 km** (`FOLGA_DA_CAIXA_GRAUS`).
   - **Por que a folga:** sem ela, a régua de Rio dos Cedros, a mais ao norte, ficava na ponta do rio
     recortado, a 137 m do fim da linha. O rio parecia nascer na cidade.
   - **Efeito no mapa:** o quadro do Monitor cresce no máximo isso. A trava do Monitor mede o retângulo do
     mapa, não o enquadramento, e passou.

Fonte de todos os traçados: © OpenStreetMap contributors, ODbL. Coordenadas em WGS 84 (lon, lat no GeoJSON).

| Rio (`id`) | No OSM | Desenhado | Ligação conferida | Distância ao pino |
|---|---|---|---|---|
| Rio Benedito (`benedito`) | 12 ways, 67,0 km | 49,6 km | nó comum com o Açu (abaixo) | Timbó, 0,63 km |
| Rio dos Cedros (`rio-dos-cedros`) | 10 ways, 70,1 km | 18,7 km | nó 1259385313 comum com o Benedito, em −26,82820, −49,27370 | Rio dos Cedros, 0,07 km |
| Rio Itajaí do Sul (`itajai-do-sul`) | 25 ways, 87,8 km | 58,5 km | chega ao Açu em Rio do Sul | Ituporanga, 0,02 km |
| Rio Trombudo (`trombudo`) | 17 ways, 40,9 km | 40,9 km | nó comum com o Itajaí do Oeste (abaixo) | Trombudo Central, 0,25 km |
| Rio Guabiruba Norte + Rio Guabiruba (`guabiruba`) | 11 ways, 15,5 km (Norte 11,1 + Guabiruba 4,4) | 9,5 km, só o trecho ligado à régua | Norte → Guabiruba no nó 3932444707; Guabiruba → Mirim no nó 1889983035 | Guabiruba, 0,01 km |

`conferir_afluentes_chegam.py` confirma que todos os afluentes desenhados chegam ao rio que os recebe a 0 m.

## Guabiruba: qual curso a estação mede

- **O que faltava:** a DCSC-00029 não declara o rio (`rio: null` na API). O cadastro dizia "ribeirão
  Guabiruba".
- **Primeira rodada, recusada:** pediu "Rio/Ribeirão Guabiruba". O único way com esse nome, "Rio Guabiruba", tem
  4,4 km e passa a **1,72 km** da estação. O script recusou.
- **Diagnóstico da rodada, cursos d'água a 1,5 km da estação:**

  | Way | Tipo | Nome | Distância |
  |---|---|---|---|
  | 755485903 | river | Rio Guabiruba Norte | 0,01 km |
  | 755485907 | stream | Rio Pomerânia | 0,32 km |
  | 755451586 | river | sem nome | 1,00 km |
  | 782419929 | river | Rio Guabiruba Sul | 1,27 km |

- **Continuidade no OSM:**
  - o **Rio Guabiruba Norte** termina no nó 3932444707, em −27,09580, −48,96326;
  - ali nascem o **Rio Guabiruba**, e o Rio Guabiruba Sul também chega;
  - o Rio Guabiruba termina no nó 1889983035, em −27,09784, −48,92983, que é vértice do **Itajaí-Mirim**.
- **Desenhado:** o Norte e o Rio Guabiruba, por nome **exato** (`NOMES_EXATOS` no conversor). Por substring,
  "rio guabiruba" pegaria também o Sul. O Sul não é o curso da estação e ficou de fora.
- **Lacuna no OSM:** cerca de 2 km rio acima da estação, o Rio Guabiruba Norte tem um vão de **1,8 km**, entre
  −27,0867, −49,0143 e −27,0797, −48,9978. Os sete ways da cabeceira ficam soltos. O conversor desenha só o trecho
  ligado à régua por vértice comum (`SO_O_LIGADO_A_REGUA`): 4 ways, 9,5 km, de ~2 km acima da estação até o
  Mirim.
  - Ligar o vão seria uma reta inventada.
  - Desenhar o pedaço solto seria um salto no mapa.
- **Incerteza:** a escolha do Norte vem da posição da estação, a 10 m do traçado. Nenhuma fonte da DCSC ou da
  prefeitura nomeia o curso. O Rio Pomerânia passa a 0,32 km. O `ramo` do cadastro (`ribeirao_guabiruba`) não
  mudou.

## Rio Benedito: a confluência (gravada)

- **Coordenada:** **−26,89134, −49,23557** (lat, lon), no centro urbano de Indaial.
- **Fonte:** OpenStreetMap. O way 700577287, "Rio Benedito" (com `wikipedia=pt:Rio Benedito`), termina no
  nó **1575465793**. O mesmo nó é a ponta de dois ways do "Rio Itajaí-Açu", 700778093 e 700577289
  (`data/brutos/tracado-rios-osm.json`). Ali o Açu se parte em dois ways, e o Benedito chega.
- **Método:**
  - `achar_confluencias.py` toma o ponto do Benedito mais perto do tronco (toque **0 m**);
  - mede a posição pela água no grafo do tronco (Dijkstra, como `medir_distancia_rio.py`), a partir de Rio do
    Sul: **90,4 km**;
  - a régua de Indaial (DCSC-00006, −26,9109, −49,27) fica a 85,8 km, e a de Blumenau, a 116,7 km;
  - logo, a confluência fica **4,6 km abaixo da régua de Indaial** e 26,3 km acima da de Blumenau.
- **Conferências:**
  - nenhum outro ponto do Benedito chega a 1 km do Açu;
  - a junção é a ponta mais ao sul do Benedito.
- **Fontes que concordam:**
  - a JICA 2011, seção 3.1: "the Benedito River in Indaial city" (`docs/JICA-2011-VERIFICADO.md`);
  - o AIBH 2021, "trecho entre os **municípios** de Ascurra e Indaial, a montante da confluência com o Rio
    Benedito". O AIBH fala dos municípios. Ele não situa a confluência em relação à régua.
- **O que isto corrige:** a leitura de 05/09/2026 gravada no cadastro, "a MONTANTE de Indaial", tomou o
  município pela régua. A correção está em `docs/AIBH-ITAJAI-ACU.md`, `docs/TOPOLOGIA-CANONICA.md` e no
  README.
- **O que não serve de prova:** a ordem dos picos na JICA (Blumenau antes de Indaial em algumas colunas) é
  contexto hidrológico. Não comprova onde fica a confluência e não entrou no argumento.
- **Gravação:** `python3 scripts/achar_confluencias.py --gravar`, por decisão do Jefferson.
  - **Defeito corrigido antes:** o regex do script exigia a entrada inteira numa linha. Com a entrada em
    várias linhas, ele nunca casava, e o `--gravar` só avisava.
  - **Diff revisado:** muda **uma linha** de `data/estacoes.json`, o `ponto_exato` da entrada
    `entra_perto_de: "indaial"`. O Luís Alves (sem traçado) não é tocado.
  - **Teste:** `teste_achar_confluencias.test_gravar_so_mexe_na_entrada_do_afluente_medido` trava isso.
- **Na tela:** o texto aparece na árvore do Monitor ("Entram no tronco sem régua no site"), com vírgula
  decimal. `arvoreDaBacia.test.ts` trava que ele diz "abaixo da régua".
- **Incertezas:**
  - o OSM é colaborativo, e a posição do nó tem precisão de dezenas de metros;
  - a margem de 4,6 km pela água é larga diante disso;
  - a régua usada é a coordenada da DCSC-00006. Ela bate com a ficha da DCSC a 10 m, mas a COMPDEC não
    nomeia o ponto da régua municipal. Se a régua municipal estiver em outro lugar, a relação muda.

## Rio Trombudo → Itajaí do Oeste (ligação registrada, sem posição na árvore)

- **Coordenada:** **−27,24510, −49,69070**.
- **Fonte:** OpenStreetMap. O way 660933103, "Rio Trombudo", termina no nó **534975895**. O mesmo nó é a
  ponta dos ways 660933101 e 705279282, do "Rio Itajaí do Oeste".
- **Método:** o nó é comum aos dois traçados (toque 0 m); não se usou proximidade. Pela água, fica 6,3 km
  acima da confluência do Oeste com o Sul e 8,4 km acima da régua de Rio do Sul.
- **Onde está no cadastro:** `rio_chega_a` da cidade, com `fonte`, `metodo`, `incerteza` e
  `posicao_na_arvore: null`.
- **A trava:** `valida_rio_chega_a` reprova:
  - `posicao_na_arvore` diferente de null;
  - a cidade em `tronco_sequencia`, `cabeceiras_paralelas` ou `afluentes_laterais`;
  - a falta de fonte ou de incerteza.
- **Decisão do Jefferson:** a cidade continua sem posição confirmada na árvore. Ela segue em "Outros pontos".
  O menu agora diz: "Rio Trombudo → Itajaí do Oeste (traçado do OpenStreetMap) · sem posição na árvore".
- **Incerteza:**
  - geometria colaborativa; nenhuma fonte hidrológica oficial foi lida para a ligação;
  - o traçado do Oeste entre Taió e a junção não é contínuo no grafo. Por isso não se sabe a posição em
    relação à régua de Taió.
- **O traçado:** continua visível em cinza. Ele não depende de `rio_chega_a` nem da posição na árvore.

## O que isto não muda

- **A árvore:** `_topologia` e as posições não mudam, exceto o texto do `ponto_exato` do Benedito.
- **A cor:** os afluentes novos ficam cinza, como o Hercílio. Mostram por onde a água corre e não afirmam área
  alagada.
- **As equivalências:** nenhuma muda; as quatro seguem "não confirmada".
  - **Timbó:** o pino tem coordenada sem fonte declarada. Ele fica a **0,28 km do Rio dos Cedros** e a 0,64 km
    do Benedito, perto da confluência dos dois (0,04 km pela água). A régua é declarada "Rio Benedito, Rua
    Equador".
    - O pino não foi mexido. É mais um motivo para a coordenada de Timbó precisar de fonte.
  - **Estações estaduais perto:** a DCSC-00023 (Timbó 1) fica a 0,05 km do Benedito; a DCSC-00034 (Timbó 2), a
    0,13 km do Rio dos Cedros; a DCSC-00011 (Rio dos Cedros 1), a 0,05 km do Rio dos Cedros.
    - Proximidade não vincula (decisão de 06/10/2026).

## Verificação

- **Testes:**
  - `teste_baixar_tracados_afluentes.py`: chegada, continuidade, pedaço solto, nomes;
  - `teste_converter_tracado_rios.py`: recorte com folga; o Rio dos Cedros segue além da régua; nome exato
    sem o Sul;
  - `teste_achar_confluencias.py`;
  - `teste_validar_dados.py` (`RioChegaASemPosicaoNaArvore`);
  - `conferir_afluentes_chegam.py`, `validar_dados.py`;
  - os testes do site (`menuDasCidades`, `arvoreDaBacia`), o build e a trava do Monitor.
- **Navegador:** Chromium, build de produção, sem leitura ao vivo, com as camadas de mancha fechadas.
  - Bacia inteira (1100×800): os cinco cursos aparecem, em cinza, ligados ao rio que os recebe:
    - Rio dos Cedros → Benedito → Açu;
    - Trombudo → Oeste;
    - Itajaí do Sul de Ituporanga a Rio do Sul;
    - Guabiruba → Mirim em Brusque.
  - Cada uma das cinco cidades aberta: a linha passa pelo pino, sem salto, e continua dos dois lados. No Rio
    dos Cedros, a linha segue além da régua, para o norte.
  - Guabiruba também em 390×844.
  - Todas as cidades estavam sem leitura e sem faixa, e a linha estava lá. Isso é o caso "sem leitura / sem
    cota" pedido.
  - O satélite não carrega no ambiente de teste; a conferência foi sobre o fundo escuro.

## Refazer

Rodar o workflow "Baixar traçados dos afluentes" (Actions → Run workflow). Depois, na sessão:

```bash
git fetch origin tracado-afluentes
for r in benedito rio-dos-cedros itajai-do-sul trombudo guabiruba; do
  git show FETCH_HEAD:tracado-$r-osm.json > data/brutos/tracado-$r-osm.json
done
python3 scripts/converter_tracado_rios.py
python3 scripts/achar_confluencias.py          # relatório; --gravar só por decisão
```
