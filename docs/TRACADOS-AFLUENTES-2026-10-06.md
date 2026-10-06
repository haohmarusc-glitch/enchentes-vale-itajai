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
   ser feita à mão.

   **Falha do Overpass:** duas rodadas caíram por timeout do espelho `overpass.kumi.systems`. O erro subia
   sem tratamento: o terceiro espelho nunca era tentado, e os rios seguintes nem eram pedidos. Desde
   06/10/2026, por decisão do Jefferson:
   - **timeout e queda de conexão** contam como fila: espera progressiva, nova tentativa e, esgotadas as
     tentativas, o próximo espelho;
   - **cada rio é isolado:** o que fica sem resposta não para os outros, que são conferidos e publicados;
   - **último arquivo válido:** quem falha mantém o arquivo anterior, o do checkout. Nada é apagado ou
     sobrescrito;
   - **`rodada.json`** (publicado junto com `resumo.txt`) registra, por rio:
     - a situação (`baixado`, `recusado`, `sem_resposta` ou `desatualizado`);
     - o espelho e cada tentativa, com o resultado e o motivo do erro;
     - a data da base OSM da resposta (`base_osm`) e a do arquivo gravado (`base_do_arquivo`);
   - **a rodada termina verde**, com a anotação "Coleta parcial" (ou "Coleta não realizada", se nenhum rio
     veio) dizendo quais rios ficaram com o último arquivo válido e por quê.

   **Espelho atrasado (desde 06/10/2026, decisão do Jefferson):** a resposta é julgada pela **data da base
   OSM** (`osm3s.timestamp_osm_base`), comparada com a do arquivo válido existente. A data do download nunca
   substitui a da base: um espelho atrasado responde hoje com dados de meses atrás.

   | Base recebida × base do arquivo | O arquivo | Na busca |
   |---|---|---|
   | posterior | substituído (`substituído, base recebida mais nova`) | serve |
   | igual | `mantido, mesma base` (nada a reescrever) | serve |
   | anterior | `mantido, base existente mais nova` | tenta o próximo espelho |
   | resposta sem data ou com data inválida | `mantido, resposta sem data de base válida (incerto)` | tenta o próximo espelho |
   | arquivo sem data ou com data inválida | `mantido, arquivo existente sem data de base válida (incerto)` | serve, mas não grava |
   | não há arquivo | `novo (não havia arquivo)` | serve |

   - **Data inválida:** a que não é ISO 8601 com fuso.
   - **Quando nenhum espelho serve:** o rio sai `desatualizado` (algum espelho respondeu com base antiga) ou
     `incerto` (sem data), e o arquivo fica.
   - **O que `rodada.json` grava:** as duas datas (`base_osm`, `base_do_arquivo`), o espelho consultado e cada
     tentativa, com a base e a decisão.
   - **Procedência:** o arquivo aceito leva `base_osm`, `espelho` e `baixado_em` em `_consulta`.
   - **Integridade primeiro:** a data não passa por cima da conferência. Resposta recusada (não chega, não
     passa pela régua, sem continuidade) nunca grava, por mais nova que seja.
   - **Onde vale:** também no Hercílio (`baixar_tracado_hercilio.py`) e nos rios de município
     (`baixar_rios_municipio.py`), que usam a mesma busca.

   **Diagnóstico das rodadas de 06/10/2026.** Os arquivos publicados no branch `tracado-afluentes` foram
   comparados com os do repositório (base, ways, geometria e conferência). Nenhum chegou a `data/`.

   | Rodada | Rio | Base publicada (espelho) | Base no repositório | Geometria | Conferência | Pela regra |
   |---|---|---|---|---|---|---|
   | `488117b`, 15:39 UTC | Benedito | 01/06/2026 08:52 (kumi) | 06/10/2026 12:21 | **difere** (13 ways × 12) | passa | mantido, base existente mais nova |
   | | Guabiruba | 01/06/2026 08:52 (kumi) | 06/10/2026 12:56 | igual | passa | mantido, base existente mais nova |
   | | Rio dos Cedros, Itajaí do Sul, Trombudo | 06/10 15:22–15:27 (overpass-api.de) | 06/10 12:21–12:38 | igual | passa | substituído, base mais nova |
   | `704153c` (main), 15:52 UTC | Rio dos Cedros | 15/07/2026 15:22 (kumi) | 06/10/2026 12:38 | igual | passa | mantido, base existente mais nova |
   | | Benedito, Itajaí do Sul, Trombudo, Guabiruba | 06/10 15:48–15:50 (overpass-api.de) | 06/10 12:21–12:56 | igual | passa | substituído, base mais nova |

   - **Três artefatos regressivos.** Todos vieram do `overpass.kumi.systems`, com a base atrasada em meses.
   - **A geometria não basta como prova.** O Benedito difere, mas a contagem de 13 contra 12 ways sozinha
     não provaria nada. O Guabiruba e o Rio dos Cedros têm geometria **idêntica** e são regressivos do mesmo
     jeito: a procedência que eles carregam é mais velha. Quem decide é a data da base. Os três passam na
     conferência: são válidos, só antigos.
   - **A correção:** a rodada do PR que trouxe esta regra publica de novo o branch. Quem vier de espelho
     atrasado fica com o arquivo do repositório; nada é trocado por versão que não seja comprovadamente mais
     nova.

2. O script roda no GitHub Actions (`baixar-tracados-afluentes.yml`). Os brutos e o resumo vão para o branch
   `tracado-afluentes`.
3. `converter_tracado_rios.py` gera `data/rios/<id>.geojson`. Ele recorta na **caixa do mapa** (extensão do
   tronco e das réguas do cadastro) com **folga de 1,5 km** (`FOLGA_DA_CAIXA_GRAUS`).
   - **Por que a folga:** sem ela, a régua de Rio dos Cedros, a mais ao norte, ficava na ponta do rio
     recortado, a 137 m do fim da linha. O rio parecia nascer na cidade.
   - **Efeito no mapa:** o quadro do Monitor cresce no máximo isso. A trava do Monitor mede o retângulo do
     mapa, não o enquadramento, e passou.
   - **Aprovada pelo Jefferson (06/10/2026):** a margem fica. Não há motivo para reduzi-la agora.

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
  - **Decisão do Jefferson (06/10/2026):** não completar o traçado no projeto. O certo é corrigir primeiro o vão no
    OpenStreetMap, com imagem ou conhecimento local verificável. Depois, rodar de novo o workflow e o conversor.
    O vão aparece sozinho como ligado. Nada foi alterado no OSM.
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
    - **Decisão do Jefferson (06/10/2026):** o pino fica onde está, marcado como **coordenada não confirmada**.
      A busca não achou fonte oficial que situe a régua "Rio Benedito, Rua Equador". A proximidade dos rios
      não basta para mover o pino nem para vincular a régua à estação estadual.
      - **No cadastro:** `coordenadas_status: "não confirmada"`, com o porquê em `coordenadas_status_nota`.
      - **Trava:** `valida_coordenada_nao_confirmada` exige a nota e reprova o status junto com fonte declarada.
      - **No painel:** "Coordenada não confirmada (−26,8231, −49,2708): nenhuma fonte oficial situa a régua
        “Rio Benedito, Rua Equador”…" (`posicaoDoPino.ts`). O mesmo texto vale no inventário
        (`docs/INVENTARIO-REGUAS.md`).
      - **O que confirmaria:**
        - cadastro municipal da estação;
        - documento da Defesa Civil;
        - coordenada divulgada pelo órgão responsável;
        - fotografia georreferenciada verificável.

        O portal oficial do município está no ar, mas a busca pública não trouxe esse dado.
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
