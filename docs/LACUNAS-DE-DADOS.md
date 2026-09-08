# Lacunas de dados — o que falta e o que procurar

Gerado por `scripts/auditar_lacunas.py` em 08/09/2026. **Não editar à mão** — reexecutar.

Coluna **Leitura ao vivo** medida em `2026-09-08T14:31:22+00:00` (17 réguas com nível). As outras seis colunas não dependem de coleta.

Sete camadas por cidade. Cada uma acende uma parte diferente do site, e é
isso que ordena a busca: sem leitura o pino fica cinza; sem cota a cor não
existe nem com leitura; sem pico a previsão a jusante diz "dados
insuficientes"; sem hora de pico o tempo de trânsito continua sendo tabela
de projeto, nunca medida.

## Matriz por cidade

| Cidade | Rio | Leitura ao vivo | Cotas atenção+alerta | Cotas conferidas | Picos | Série ANA | Cotas de rua | Trânsito a jusante |
|---|---|---|---|---|---|---|---|---|
| Taió | acu | sim | sim | — | 1 | sim | — | sim |
| Ituporanga | acu | — | — | — | — | sim | — | sim |
| Rio do Sul | acu | sim | sim | — | 9 | sim | 555 | — |
| Ibirama | acu | — | — | — | — | — | — | — |
| Lontras | acu | — | — | — | — | — | — | — |
| Ascurra | acu | — | — | — | — | — | — | — |
| Indaial | acu | — | sim | sim | 16 | — | — | — |
| Blumenau | acu | sim | sim | — | 113 | sim | 2023 | sim |
| Gaspar | acu | — | sim | sim | 48 | sim | 1617 | sim |
| Ilhota | acu | — | sim | — | — | — | — | sim |
| Itajaí | acu | sim | 11× | — | — | — | — | n/a |
| Timbó | acu | — | — | — | 1 | — | — | — |
| Rio dos Cedros | acu | — | sim | — | — | — | — | — |
| Trombudo Central | acu | — | — | — | — | — | — | n/a |
| Vidal Ramos | mirim | sim | — | — | — | — | — | — |
| Botuverá | mirim | — | — | — | — | — | — | — |
| Guabiruba | mirim | — | — | — | — | — | — | — |
| Brusque | mirim | sim | — | sim | 8 | sim | 377 | sim |
| Itajaí | mirim | sim | 11× | — | — | — | — | n/a |

`n/a` em trânsito = a cidade é foz, ou entrou sem posição na árvore (Trombudo Central: a fonte diz o rio, não a confluência).

## Lista de busca, por impacto

### 1. Leitura ao vivo — o pino cinza

Sem leitura em: **Ituporanga**, **Ibirama**, **Lontras**, **Ascurra**, **Indaial**, **Gaspar**, **Ilhota**, **Timbó**, **Rio dos Cedros**, **Trombudo Central**, **Botuverá**, **Guabiruba**.

É o que mais escurece o mapa e o único item que não tem substituto histórico: nenhuma pesquisa em acervo acende um pino hoje. O pedido é ofício à Defesa Civil do município pedindo o endpoint que a página de monitoramento já consome.

### 2. Cotas oficiais — a cor que não existe nem com leitura

Sem cota nenhuma: **Ituporanga**, **Ascurra**, **Vidal Ramos**, **Botuverá**, **Guabiruba**.

Com cota incompleta (falta atenção ou alerta): **Ibirama**, **Lontras**, **Timbó**, **Trombudo Central**, **Brusque** — a tela não consegue pintar a faixa que falta.

**Com a escala nas RÉGUAS, não na cidade** — não é buraco, não procurar: **Itajaí** (11 de 12 réguas com escala, 11 conferidas na fonte). A cidade não tem uma escala porque tem VÁRIAS, uma por régua, e um número só ali seria mentira. A cor da tela sai da régua, então a cor existe.

Com as duas mas sem conferência na fonte: **Taió**, **Rio do Sul**, **Blumenau**, **Ilhota**, **Rio dos Cedros** — valor veio de resumo, levantamento ou imprensa, não de leitura do Plano de Contingência. Procurar o PDF do PLANCON de cada uma e guardar em `data/brutos/`.

### 3. Hora do pico — o que destrava `transito.json`

**196 picos na base, 0 com hora.** Enquanto for zero, todo tempo de trânsito exibido é faixa de tabela de projeto (JICA/ABRH), nunca medida nesta bacia. `scripts/calibrar_transito.py` existe e não tem o que calibrar.

A hora só existe em boletim de cheia: boletim diário da Defesa Civil estadual, ofício municipal do dia, série horária da ANA/HidroWeb.

### 4. Picos históricos — a previsão a jusante

Menos de 5 eventos (mínimo da previsão v1): **Taió**, **Ituporanga**, **Ibirama**, **Lontras**, **Ascurra**, **Ilhota**, **Itajaí**, **Timbó**, **Rio dos Cedros**, **Trombudo Central**, **Vidal Ramos**, **Botuverá**, **Guabiruba**.

Sem nenhum: **Ituporanga**, **Ibirama**, **Lontras**, **Ascurra**, **Ilhota**, **Itajaí**, **Rio dos Cedros**, **Trombudo Central**, **Vidal Ramos**, **Botuverá**, **Guabiruba**.

2 registros têm só o ano, sem mês nem dia — não pareiam com jusante nem com mancha.

60 registros com `referencia: null` (Blumenau 41, Rio do Sul 9, Brusque 8, Taió 1, Timbó 1). Em Blumenau isso é a REGRA BLOQUEANTE do `enchentes.json`: régua ou IBGE (régua + 0,20 m) muda o valor em 20 cm. Resolve no HidroWeb, estação 83800002, cotas de 09/07/1983 e 07/08/1984.

### 5. Série da ANA — o acervo que fecha as lacunas de uma vez

Sem `codigo_ana` conferido no HidroWeb: **Ibirama**, **Lontras**, **Ascurra**, **Indaial**, **Ilhota**, **Itajaí**, **Timbó**, **Rio dos Cedros**, **Trombudo Central**, **Vidal Ramos**, **Botuverá**, **Guabiruba**.

Cada estação conferida traz série inteira de cota **por dia** — resolve o item 4 para aquela cidade, e é o item de maior alcance por unidade de esforço da lista. **Não resolve o item 3:** a série da ANA é diária, sem hora do pico (conferido na API em 08/09/2026 — ver `docs/ANA-API-2026-09-08.md`).

**Mas não são doze buscas iguais.** Só as do primeiro grupo são busca:

**Busca de verdade — ninguém olhou ainda** (7): **Lontras**, **Ascurra**, **Itajaí**, **Timbó**, **Rio dos Cedros**, **Trombudo Central**, **Guabiruba**.

⚠️ **A busca JÁ FOI FEITA e a estação achada foi RECUSADA** (4) — o que falta é uma estação **diferente**, e a recusada está nomeada aqui de propósito, para não voltar:

| Cidade | Estação recusada | Por quê, em uma linha |
|---|---|---|
| Indaial | `83520000 WARNOW` | 3,95 km deste pino |
| Ilhota | `83870001 ILHOTA-JUSANTE` | 1,18 km deste pino — acima do limite de 1 km que o projeto usa para dizer 'mesma régua' |
| Vidal Ramos | `83892990 SALSEIRO` | Mesmo município, estações diferentes: 6,8 km entre a nossa régua (-27.38547 / -49.35812, Asthon = DCSC) e a SALSEIRO no inventário da ANA |
| Botuverá | `83892998 BOTUVERA-MONTANTE` | 3,47 km deste pino, e o nome já avisava: MONTANTE |

O motivo inteiro, com a distância medida e o bruto do inventário, está em `codigo_ana_nao_e` de cada cidade em `data/estacoes.json`. **Trazer de volta uma destas é como um pareamento errado entra** — já custou caro em Brusque e no Salseiro de Vidal Ramos.

⛔ **Não é busca, é DECISÃO** (1): **Ibirama** (candidata `83440000 IBIRAMA`). A candidata já existe e a distância já foi medida; o que falta é critério. Pedir busca aqui aponta para a tarefa errada — o desbloqueio está escrito em `codigo_ana_candidatos`.

### 6. Cotas de rua — a busca "minha rua"

Sem nenhuma cota de rua: **Taió**, **Ituporanga**, **Ibirama**, **Lontras**, **Ascurra**, **Indaial**, **Ilhota**, **Itajaí**, **Timbó**, **Rio dos Cedros**, **Trombudo Central**, **Vidal Ramos**, **Botuverá**, **Guabiruba**.

Com cota mas **sem coordenada** (2609 endereços): **Blumenau** 2023, **Rio do Sul** 555, **Brusque** 29, **Gaspar** 2. Aparecem na busca por nome, não no mapa. Geocodificação pendente.

### 7. Trânsito — os elos que faltam, e quais valem procurar

São 10, e **não são 10 coisas a procurar**. 7 faltam por falta de fonte; 3 não são tempo de trânsito nenhum.

**Vale procurar — falta fonte:**

| De | Para | Rio | Por quê |
|---|---|---|---|
| Rio do Sul | Lontras | acu | a Tabela 7.5.1 da JICA não lista lontras |
| Lontras | Ascurra | acu | a Tabela 7.5.1 da JICA não lista lontras nem ascurra |
| Ascurra | Indaial | acu | a Tabela 7.5.1 da JICA não lista ascurra |
| Rio dos Cedros | Timbó | acu | a Tabela 7.5.1 da JICA não lista rio-dos-cedros |
| Vidal Ramos | Botuverá | mirim | a Tabela 7.5.1 da JICA não lista vidal-ramos nem botuvera |
| Botuverá | Guabiruba | mirim | a Tabela 7.5.1 da JICA não lista botuvera nem guabiruba |
| Guabiruba | Brusque | mirim | a Tabela 7.5.1 da JICA não lista guabiruba |

**⛔ Não procurar — o elo não é um tempo de trânsito:**

Nestes, a grandeza não existe: nem outra fonte nem uma cheia medida resolvem. Um número aqui teria cara de tempo de trânsito sem ser um.

`Ibirama → Rio do Sul`

- ibirama é afluente lateral (Rio Hercílio (Itajaí do Norte)) e a outra ponta está no tronco: o pico do tronco vem da cheia que desce o tronco, o do afluente vem da chuva na sub-bacia dele. O vão entre os dois é coincidência de hidrogramas, não viagem — muda de valor e até de sinal a cada cheia
- ibirama tem relógio próprio — o pico vem da chuva na sub-bacia, não da cheia descendo o Açu, então nem a tabela nem uma cheia medida dão tempo de roteamento aqui

`Indaial → Blumenau`

- a JICA tem as DUAS pontas e a diferença não é positiva (5 anos +0 h, 10 anos +0 h, 25 anos -1 h, 50 anos -1 h)
- o Rio Benedito entra entre as duas e adianta o pico de baixo
- não é um tempo de trânsito: inventar um positivo daria horas que não existem

`Timbó → Indaial`

- timbo é afluente lateral (Rio Benedito) e a outra ponta está no tronco: o pico do tronco vem da cheia que desce o tronco, o do afluente vem da chuva na sub-bacia dele. O vão entre os dois é coincidência de hidrogramas, não viagem — muda de valor e até de sinal a cada cheia
- timbo tem relógio próprio — o pico vem da chuva na sub-bacia, não da cheia descendo o Açu, então nem a tabela nem uma cheia medida dão tempo de roteamento aqui

### 8. Maré de Itajaí

Tábua cobre **30 dias, até 2026-09-30**; altura em metros: **não** (só horário).

Depois dessa data a tela da foz fica sem maré.

**Não é busca, é importação.** A tábua do CHM para o Porto de Itajaí **já foi encontrada** e cobre outubro, novembro e dezembro de 2026 — os 92 dias que faltam existem e estão disponíveis. A parede real da FONTE é 31/12/2026, não a data acima, que é da tabela IMPORTADA. **2027 ainda não existe no portal**: aí sim é espera, não busca.

A altura em metros foi omitida de propósito: o datum da planilha não está conferido contra o da DHN — mesmo problema do datum de Blumenau. Importar o horário sem a altura continua certo enquanto isso.

### 9. Manchas de inundação

10 manchas, todas de uma cidade (Itajaí 10); 10 sem pico associado.

Sem o pico daquele evento na cidade, a mancha mostra onde a água chegou mas não a que nível — não dá para ler como "se o rio chegar a X". Nenhuma outra cidade da bacia tem mancha publicada aqui.
