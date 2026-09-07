# Lacunas de dados — o que falta e o que procurar

Gerado por `scripts/auditar_lacunas.py` em 07/09/2026. **Não editar à mão** — reexecutar.

Sete camadas por cidade. Cada uma acende uma parte diferente do site, e é
isso que ordena a busca: sem leitura o pino fica cinza; sem cota a cor não
existe nem com leitura; sem pico a previsão a jusante diz "dados
insuficientes"; sem hora de pico o tempo de trânsito continua sendo tabela
de projeto, nunca medida.

## Matriz por cidade

| Cidade | Rio | Leitura ao vivo | Cotas atenção+alerta | Cotas conferidas | Picos | Série ANA | Cotas de rua | Trânsito a jusante |
|---|---|---|---|---|---|---|---|---|
| Taió | acu | sim | sim | — | 1 | sim | — | sim |
| Ituporanga | acu | — | — | — | — | — | — | sim |
| Rio do Sul | acu | sim | sim | — | 9 | sim | 555 | — |
| Ibirama | acu | — | — | — | — | — | — | — |
| Lontras | acu | — | — | — | — | — | — | — |
| Ascurra | acu | — | — | — | — | — | — | — |
| Indaial | acu | — | sim | sim | 16 | — | — | — |
| Blumenau | acu | sim | sim | — | 113 | sim | 2023 | sim |
| Gaspar | acu | — | sim | sim | — | sim | 1619 | sim |
| Ilhota | acu | — | sim | — | — | — | — | sim |
| Itajaí | acu | sim | — | — | — | — | — | n/a |
| Timbó | acu | — | — | — | 1 | — | — | — |
| Rio dos Cedros | acu | — | sim | — | — | — | — | — |
| Trombudo Central | acu | — | — | — | — | — | — | n/a |
| Vidal Ramos | mirim | sim | — | — | — | — | — | — |
| Botuverá | mirim | — | — | — | — | — | — | — |
| Guabiruba | mirim | — | — | — | — | — | — | — |
| Brusque | mirim | sim | — | — | 9 | sim | 377 | sim |
| Itajaí | mirim | sim | — | — | — | — | — | n/a |

`n/a` em trânsito = a cidade é foz, ou entrou sem posição na árvore (Trombudo Central: a fonte diz o rio, não a confluência).

## Lista de busca, por impacto

### 1. Leitura ao vivo — o pino cinza

Sem leitura em: **Ituporanga**, **Ibirama**, **Lontras**, **Ascurra**, **Indaial**, **Gaspar**, **Ilhota**, **Timbó**, **Rio dos Cedros**, **Trombudo Central**, **Botuverá**, **Guabiruba**.

É o que mais escurece o mapa e o único item que não tem substituto histórico: nenhuma pesquisa em acervo acende um pino hoje. O pedido é ofício à Defesa Civil do município pedindo o endpoint que a página de monitoramento já consome.

### 2. Cotas oficiais — a cor que não existe nem com leitura

Sem cota nenhuma: **Ituporanga**, **Ascurra**, **Itajaí**, **Vidal Ramos**, **Botuverá**, **Guabiruba**.

Com cota incompleta (falta atenção ou alerta): **Ibirama**, **Lontras**, **Timbó**, **Trombudo Central**, **Brusque** — a tela não consegue pintar a faixa que falta.

Com as duas mas sem conferência na fonte: **Taió**, **Rio do Sul**, **Blumenau**, **Ilhota**, **Rio dos Cedros** — valor veio de resumo, levantamento ou imprensa, não de leitura do Plano de Contingência. Procurar o PDF do PLANCON de cada uma e guardar em `data/brutos/`.

### 3. Hora do pico — o que destrava `transito.json`

**149 picos na base, 0 com hora.** Enquanto for zero, todo tempo de trânsito exibido é faixa de tabela de projeto (JICA/ABRH), nunca medida nesta bacia. `scripts/calibrar_transito.py` existe e não tem o que calibrar.

A hora só existe em boletim de cheia: boletim diário da Defesa Civil estadual, ofício municipal do dia, série horária da ANA/HidroWeb.

### 4. Picos históricos — a previsão a jusante

Menos de 5 eventos (mínimo da previsão v1): **Taió**, **Ituporanga**, **Ibirama**, **Lontras**, **Ascurra**, **Gaspar**, **Ilhota**, **Itajaí**, **Timbó**, **Rio dos Cedros**, **Trombudo Central**, **Vidal Ramos**, **Botuverá**, **Guabiruba**.

Sem nenhum: **Ituporanga**, **Ibirama**, **Lontras**, **Ascurra**, **Gaspar**, **Ilhota**, **Itajaí**, **Rio dos Cedros**, **Trombudo Central**, **Vidal Ramos**, **Botuverá**, **Guabiruba**.

3 registros têm só o ano, sem mês nem dia — não pareiam com jusante nem com mancha.

61 registros com `referencia: null` (Blumenau 41, Rio do Sul 9, Brusque 9, Taió 1, Timbó 1). Em Blumenau isso é a REGRA BLOQUEANTE do `enchentes.json`: régua ou IBGE (régua + 0,20 m) muda o valor em 20 cm. Resolve no HidroWeb, estação 83800002, cotas de 09/07/1983 e 07/08/1984.

### 5. Série da ANA — o acervo que fecha as lacunas de uma vez

Sem `codigo_ana` conferido no HidroWeb: **Ituporanga**, **Ibirama**, **Lontras**, **Ascurra**, **Indaial**, **Ilhota**, **Itajaí**, **Timbó**, **Rio dos Cedros**, **Trombudo Central**, **Vidal Ramos**, **Botuverá**, **Guabiruba**.

Cada estação conferida traz série inteira de cota, com hora — resolve os itens 3 e 4 juntos para aquela cidade. É o item de maior alcance por unidade de esforço da lista.

### 6. Cotas de rua — a busca "minha rua"

Sem nenhuma cota de rua: **Taió**, **Ituporanga**, **Ibirama**, **Lontras**, **Ascurra**, **Indaial**, **Ilhota**, **Itajaí**, **Timbó**, **Rio dos Cedros**, **Trombudo Central**, **Vidal Ramos**, **Botuverá**, **Guabiruba**.

Com cota mas **sem coordenada** (2613 endereços): **Blumenau** 2023, **Rio do Sul** 555, **Brusque** 29, **Gaspar** 6. Aparecem na busca por nome, não no mapa. Geocodificação pendente.

### 7. Trânsito — os elos que faltam

| De | Para | Rio |
|---|---|---|
| Rio do Sul | Lontras | acu |
| Ibirama | Rio do Sul | acu |
| Lontras | Ascurra | acu |
| Ascurra | Indaial | acu |
| Indaial | Blumenau | acu |
| Timbó | Indaial | acu |
| Rio dos Cedros | Timbó | acu |
| Vidal Ramos | Botuverá | mirim |
| Botuverá | Guabiruba | mirim |
| Guabiruba | Brusque | mirim |

### 8. Maré de Itajaí

Tábua cobre **30 dias, até 2026-09-30**; altura em metros: **não** (só horário).

Depois dessa data a tela da foz fica sem maré. A altura foi omitida de propósito porque o datum da planilha não está conferido contra o da DHN — mesmo problema do datum de Blumenau. Procurar a tábua anual do CHM/Marinha para o porto de Itajaí.

### 9. Manchas de inundação

10 manchas, todas de uma cidade (Itajaí 10); 10 sem pico associado.

Sem o pico daquele evento na cidade, a mancha mostra onde a água chegou mas não a que nível — não dá para ler como "se o rio chegar a X". Nenhuma outra cidade da bacia tem mancha publicada aqui.
