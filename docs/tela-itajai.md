# Tela de Itajaí — o que já existe, o que falta e o que não dá para fazer

Resposta à especificação recebida em 31/08/2026. Ela descreve cinco blocos para
`/itajai`. **Quatro já estão no site**; o quinto está bloqueado, e o motivo é o
mesmo erro de referência altimétrica que o `CLAUDE.md` proíbe em letra
maiúscula. Este documento diz onde cada coisa está e o que exatamente
destravaria o que falta.

## Bloco 1 — painel das 11 estações ✔ existe

`ReguasDaCidade` em `web/src/telas/TelaItajai.tsx`, lendo
`estacoes_tempo_real` de `data/estacoes.json`. As onze estações estão lá, com as
cotas de atenção / alerta / emergência do Plano de Contingência, cada uma na
régua dela.

Duas diferenças em relação à especificação, e as duas são deliberadas:

- **Nove das onze não disparam aviso** (`alerta_automatico: false`), e não só a
  DC-10. São réguas de estuário: sobem com a maré, e uma cota cruzada por
  preamar não é cheia de rio. Elas aparecem na tela com a cota; o que não fazem
  é tocar o telefone de ninguém. O porquê está no README, em "Por que nove delas
  não disparam aviso sozinhas".
- **A DC-11 (Santa Regina / Volta de Cima, 3,00 / 4,00 / 5,00) é de Itajaí.**
  Conferido no Plano de Contingência v17 (Tabela 11, p. 23) — que também põe Santa
  Regina e Volta de Cima na Zona 1 da Defesa Civil de Itajaí (p. 12). Fica no
  extremo a montante, na divisa com Ilhota, e é a única das onze réguas de Itajaí
  acima da maré, por isso dispara aviso. Esteve cadastrada por engano como régua
  de Ilhota; corrigido. Ilhota não tem régua própria.

### Ordem de descida no painel (T5, 02/09/2026) ✔ existe

Com as coordenadas das 11 réguas preenchidas (`preencher_coordenadas_dc.py`) e a
ordem calculada (`ordenar_estacoes_itajai.py`, campo `ordem_descida` no
`estacoes.json`), o painel deixou de ser uma lista plana por código. Agora
`ReguasDaCidade` recebe `agrupadoPorCurso` e mostra as réguas **sob o seu curso
d'água** — Rio Itajaí-Açu, Rio Itajaí-Mirim, Ribeirão da Murta, Ribeirão
Canhanduba, nessa ordem — e, dentro de cada um, **da nascente para o mar** por
`ordem_descida`. É o mesmo desenho do `/rios` do bot (`_reguas_agrupadas`), pela
mesma razão: numa cidade com quatro cursos, a lista plana faz o morador ler a
régua errada (a de Limoeiro, 26 km rio acima, encostava na do estuário).

**O Mirim aparece dividido em dois braços paralelos** (refino de 02/09/2026, a
partir do documento de rota do Jefferson — ver `coordenadas-dc-itajai.md`). Em
Itajaí o Mirim se separa depois de DC-10 (Limoeiro) em **curso antigo** (DC-05 →
DC-06) e **canal retificado** (DC-03 → DC-04), que se reencontram perto da foz.
A tela mostra DC-10, depois os dois braços sob o seu nome, e a ressalva do
reencontro — em vez de uma fila que intercalava os dois canais (DC-10, DC-05,
DC-03, DC-04≡DC-06) e fazia ler o nível de um braço achando que era do outro. O
rótulo do braço vem do **título** de cada régua (`(curso antigo)` / `(canal
retificado)`), não da coordenada — que segue em disputa. Lógica em
`agruparPorCurso`/`dividirEmBracos`, `CursoComBracos` na UI, travada por teste.

**DC-04 × DC-06 são o ponto de reencontro dos dois braços.** Ficam à mesma
distância da foz (~4,8 km); a fonte não distingue qual vem antes. Compartilham
`ordem_descida` e trazem `ordem_nota`; a tela as mostra cada uma no seu braço, com
a nota de que ocupam o mesmo ponto — nunca em fila. Fora do agrupamento por
braço (outras cidades), `emParesColocados` ainda junta co-locadas num par.

Sem coordenada (`ordem_descida` ausente), a régua cai para a ordem do id, que é
estável — nunca se deduz posição física a partir do número do código.

**Pendente (não neste commit): marcador de cada régua DC no mapa.** As 11 réguas
já têm `lat`/`lon` no `estacoes.json`, mas o `MapaRios` hoje ancora UM marcador
por cidade e usa essas âncoras para colorir o traçado por faixa. Espalhar 11
marcadores em Itajaí mexe nessa lógica (várias réguas na foz, algumas fora do
traçado — canal e ribeirões) e no enquadramento da bacia — é mudança à parte, com
teste próprio, para não arriscar a coloração que o morador lê. Fica como próximo
passo, separado desta entrega da sequência.

## Bloco 2 — maré ✔ existe

`PainelMare`, com `scripts/coleta_mares.py` (tábua oficial) e cálculo de
sizígia. A maré aparece marcada como **prevista**, não medida, exatamente como a
especificação pede — o marégrafo de Cabeçudas não publica dado aberto, e o
pedido está no ofício C3.

**Pista de maré medida (RN EPAGRI, dez/2024):** a EPAGRI publica **altura de maré**
(5 min/horária, últimos 24 meses) como download GRATUITO em
`ciram.epagri.sc.gov.br/dadosambientaispublicos/` (só cadastro). Se houver uma PCD
maregráfica da EPAGRI no estuário de Itajaí — a confirmar por **coordenada**, não nome —,
dá para trocar a maré prevista por medida naquele ponto. Enquanto não confirmado por
coordenada e fuso, segue prevista. Detalhes em `docs/fontes-tempo-real.md` (seção EPAGRI).

## Bloco 3 — chegada dos dois rios ✔ existe

`janelaChegada` e `faixaHoras` em `web/src/logica/transito.ts`, com os tempos de
`data/transito.json`, sempre como intervalo. A tela recusa calcular chegada a
partir de leitura velha, em vez de dar um horário que já passou.

## Bloco 5 — mapa de manchas ✔ existe

`MapaManchas` (Leaflet, carregado sob demanda) sobre `data/manchas/itajai/`: dez
eventos entre 1983 e 2015, publicados pela própria Prefeitura de Itajaí no
GitHub da GeoItajaí, licença MIT. `data/manchas/index.json` guarda, por evento,
se há lâmina d'água e se o pico daquele evento está registrado.

## Bloco 4 — "meu ponto" ✘ bloqueado, e não por falta de trabalho

A especificação pede: pegar a elevação do ponto cotado mais próximo em
`itajai-pontos-cotados-altimetricos`, comparar com o nível atual do rio, e
responder "faltam Z m para a água chegar aqui".

**Essa subtração não pode ser feita.** Os dois números estão em referências
diferentes, e nada no repositório diz qual é a distância entre elas:

- a **elevação** dos pontos cotados é altura do terreno **acima do nível do
  mar**, de 0,15 m a 370 m;
- o **nível** das estações DC-01 a DC-10 é leitura na **régua de cada uma**, com
  zero próprio e não publicado — as cotas de emergência delas vão de 1,52 m a
  10,00 m, o que já mostra que os zeros são diferentes entre si, quanto mais em
  relação ao mar.

Subtrair um do outro dá um número com duas casas decimais e nenhum significado.
Pior: dá um número que **parece** medido. "Faltam 1,8 m para a água chegar na sua
casa", calculado assim, é o tipo de frase que faz alguém dormir tranquilo numa
noite em que não devia. É a mesma armadilha que o README já registra sobre o
`Relevo_Ponto_Cotado_Altimetrico` — "o campo `cota` dele é altura do terreno
acima do nível do mar, não nível de régua. Mesmo nome, grandeza oposta" — e a
mesma que fez a camada de 2011 de Brusque ser recusada.

Some-se a isso que os três GeoJSON que o bloco 4 usaria — pontos cotados,
terreno sujeito a inundação e o `itajai-arcgis-inundacoes` — **não estão no
repositório**. Só as manchas estão, já convertidas em `data/manchas/`.

**Os três chegaram em 01/09/2026**, por `scripts/baixar_itajai_arcgis.py`, que
busca direto do ArcGIS público da Prefeitura — sem navegador, com a paginação
dos 5.237 pontos e a conferência do `robots.txt` do host, que liberou.

E as contagens confirmaram o que o documento prometia, inclusive nos detalhes
que denunciariam erro: 32 polígonos em 2011, 5 · 48 · 58 · 55 · 155 nas camadas
de lâmina, 5.237 pontos cotados em seis páginas, 110 polígonos de terreno.

**Baixar não destravou o bloco 4**, e não ia destravar: o problema nunca foi a
falta do arquivo, foi a referência. O que os arquivos responderam foi outra
coisa — e uma das respostas foi um "não" que valia a viagem. Ver
`scripts/analisar_itajai_arcgis.py`.

### O "terreno sujeito a inundação" não vai para a tela ✘

A camada tem 110 polígonos somando **38,7 hectares**, com mediana de 1.786 m² e
o menor deles com **4 m²**. A mancha de 1983 sozinha cobre **7.086 ha** — **183
vezes mais**. Três quartos dos polígonos caem dentro das manchas históricas e um
quarto cai fora, espalhados por 19 km de município.

Sejam o que forem — pontos de alagamento localizado, lotes levantados,
estruturas de drenagem —, **não são "a área inundável de Itajaí"**. Publicar isso
com esse rótulo diria a quem mora fora dos polígonos que sua rua não alaga,
quando a mancha de 1983 diz o contrário para uma área 183 vezes maior. É o mesmo
erro do bloco 4 por outro caminho: um número certo respondendo a pergunta
errada, com toda a aparência de resposta.

Nada nisso aparece em conferência de formato: o arquivo é válido, os polígonos
são reais, as coordenadas estão em EPSG:4326 e dentro do município. Só a
comparação de ordem de grandeza denuncia — e há teste travando a conclusão, que
passa a falhar se a camada for substituída por um levantamento de verdade.

O que falta para usá-la: o **dicionário de dados** da Prefeitura, dizendo o que a
camada representa e em que escala. Virou pergunta no ofício C2.

### As manchas do ArcGIS não substituem as que já temos ✘

Um documento afirmou que as do ArcGIS são "mais ricas que os GeoJSON do GitHub
GeoItajaí". São — de **atributo derivado**, não de geometria: mesma contagem de
feições nas dez camadas, mesmo campo `situa`, e por cima `Shape__Area` e
`Shape__Length`, que se calculam da própria geometria.

O que se perderia na troca é concreto: as nossas vêm do GitHub da GeoItajaí com
**licença MIT declarada**, e o serviço do ArcGIS não declara licença nenhuma —
que é justamente o item 2 do ofício C2. Trocar piora a procedência para ganhar
número derivável.

### O que os arquivos acrescentaram de verdade: a área de cada cheia ✔

Três camadas publicam a área atingida, e ela confere com a área calculada da
geometria dentro de 0,4%:

| evento | área atingida |
|---|---|
| jul/1983 | **7.086 ha** |
| ago/1984 | **7.015 ha** |
| 2001 | **3.425 ha** |

A de 2011 **não** entra: somar o campo `areas` dos 32 polígonos dá 6.995 ha
contra 7.634 ha calculados, porque eles se sobrepõem — e soma de polígono
sobreposto não é área.

### O que destrava, em ordem de qualidade

1. **A cota por endereço oficial** (ArcGIS da Prefeitura, pasta `defesacivil`,
   hoje fechada por token). Resolve o bloco inteiro sem estimativa nenhuma: a
   resposta passa a ser a cota que a Defesa Civil levantou, na régua dela. É o
   ofício **C2**, já redigido em `docs/pendencias-navegador-e-oficios.md`.
2. **O zero de cada régua DC em relação ao nível do mar.** Com isso a conta do
   bloco 4 passa a ser legítima, com a ressalva de que é estimativa por terreno.
   São onze números, e quem os tem é a Defesa Civil de Itajaí — cabe no mesmo
   ofício C2.

### O que já foi feito da parte que não depende de referência ✔

A parte do bloco 4 que não precisa de referência nenhuma **está no site**: tocar
num ponto do mapa responde **em quais enchentes aquele ponto ficou dentro da
área atingida**. É um fato sobre polígonos que já estão no repositório —
verdadeiro ou falso, não estimado —, e não uma conta entre grandezas
incompatíveis.

Está em `web/src/logica/pontoNaMancha.ts` (lógica pura, dez testes) e no clique
de `MapaManchas`. Detalhes que importam:

- **A ordem das coordenadas é trocada uma vez só, na borda.** GeoJSON guarda
  `[longitude, latitude]` e o Leaflet entrega o contrário; a troca fica no
  manipulador do clique, e a lógica pura continua falando a língua do arquivo.
  Há teste que cobra que o mar aberto fique fora, que é o que quebra se a troca
  sumir.
- **Buraco de polígono é fora**, e um vértice na altura exata do ponto não é
  contado duas vezes — os dois casos que fazem uma contagem de cruzamentos
  ingênua dizer "dentro" para um ponto de fora.
- **"Nenhuma mancha" não vira "não alaga".** A resposta negativa vem com a
  ressalva de que o levantamento cobre o que foi mapeado e de que a cidade mudou
  desde 1983.
- Os nove arquivos só são baixados **no clique**, e ficam em cache: o seletor de
  evento continua trazendo um por vez.

O que continua faltando é a outra metade do bloco: a busca por endereço (precisa
de geocodificação) e a resposta em metros, que depende dos itens 1 ou 2 acima.

## `scripts/preparar_itajai.py`

A tarefa 1 da especificação — reprojetar e enxugar os três GeoJSON — está feita
para as manchas, por `scripts/baixar_manchas_itajai.py`, que já grava
`data/manchas/itajai/` com `_meta` por evento. Para os outros dois arquivos, a
tarefa só faz sentido depois que eles existirem no repositório, e os pontos
cotados só depois que houver o que fazer com eles.
