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
- **A DC-11 (Santa Regina, 3,00 / 4,00 / 5,00) não existe no nosso cadastro.**
  Temos DC-01 a DC-10 mais a DC-00 (a própria Defesa Civil). Se a estação existe
  no Plano de Contingência v17, é dado que falta — mas não entra por transcrição
  de uma especificação: entra quando alguém abrir o Plano e conferir. Está nas
  pendências.

## Bloco 2 — maré ✔ existe

`PainelMare`, com `scripts/coleta_mares.py` (tábua oficial) e cálculo de
sizígia. A maré aparece marcada como **prevista**, não medida, exatamente como a
especificação pede — o marégrafo de Cabeçudas não publica dado aberto, e o
pedido está no ofício C3.

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
