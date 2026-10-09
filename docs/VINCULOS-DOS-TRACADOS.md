# Vínculo traçado × cidade × régua no Monitor — auditoria e correção (07/10/2026)

Pedido do Jefferson ("Monitor: Ituporanga e barragens", seções 1 e 1B), com autorização para mexer nos arquivos do
Monitor (rótulo `monitor-autorizado`). Código: `web/src/logica/vinculosDosTracados.ts`, `web/src/logica/mapaMotor.ts`
e `web/src/telas/MonitorBacia.tsx`. Testes: `web/src/logica/vinculosDosTracados.test.ts` (16).

## O defeito

- O Monitor dava cidades só ao tronco (`itajai-acu`, `itajai-mirim`). Todo afluente e a cabeceira Sul entravam com
  `cidades: []` e ficavam **cinza por configuração**, não por falta de dado.
- Ituporanga tinha o pino vermelho (faixa estadual "emergência" da DCSC-00039) e o Itajaí do Sul cinza ao lado.
- O comentário antigo dizia que o traçado do Sul era parcial e não chegava a Ituporanga. Isso não vale mais: hoje o
  traçado tem 58 km, é contínuo (um componente) e passa a 19 m da estação.
- No tronco, a primeira régua pintava o rio **acima** dela:
  - Taió coloria 71,5 km do Itajaí do Oeste rio acima, incluindo o trecho da Barragem Oeste;
  - Vidal Ramos coloria 25,4 km do Mirim rio acima.

## A regra nova

- Cada curso fora do tronco tem um **vínculo explícito** (`VINCULOS`) ou fica **sem vínculo, com o motivo**
  (`SEM_VINCULO`). O vínculo separa quatro coisas:
  - a cidade do cadastro;
  - o grupo em que a leitura e a classificação dela moram (`itajai-acu`/`itajai-mirim`);
  - o traçado físico;
  - a estação que decide a cor.
- **Alcance:** a régua colore só o caminho, no próprio traçado, da estação até a confluência ou até a próxima estação
  rio abaixo, o que vier primeiro.
  - Fica de fora: o rio acima da estação, o rio que recebe a água e qualquer segmento desconectado (sem caminho, sem
    cor).
  - A distância geométrica é conferência, não prova de régua.
- **Cor:** é a mesma decisão do pino, com a mesma estação, medição, frescor e origem. O módulo não calcula faixa.
  - Faixa estadual pinta como a municipal (traço contínuo, brilho e correnteza, desde 08/10/2026); só o pino é
    pontilhado, e o nome segue "faixa estadual".
  - Na reprodução não há classificação estadual histórica, então o trecho fica cinza: o dado de agora não vai para o
    passado.
- **Tronco:** a primeira régua não pinta o rio acima dela, com folga de 0,5 km para meandro.
  - O resto da regra do tronco não mudou: a régua a montante dá a cor até a próxima, o DC-11 vale na foz e o canal
    retificado do Mirim segue a regra própria.
  - **DC-11, "a jusante" pelo traçado (08/10/2026):** a cor da DC-11 valia para os trechos cuja projeção na reta
    entre os pinos de Ilhota e Itajaí caía depois da régua. A Volta de Cima, logo abaixo da DC-11, volta para
    trás nessa reta: com a régua em atenção (3,17 m), 9 arestas, **2,86 km** de rio ao longo da Rua Santa Regina,
    ficavam cinza (print do Jefferson, 14:39). Agora `arestasAJusanteDe` mede no traçado: entra a aresta cujos dois
    vértices estão, pelo canal, mais perto da foz do que o vértice da régua (a 116 m dela). O rio acima da régua
    continua cinza; braços de ilha entram pelos dois lados. Teste com o traçado real em
    `vinculosDosTracados.test.ts` e com um meandro sintético em `referenciaDc11.test.ts`.
- **Toque:**
  - no trecho colorido, abre o painel da cidade que decidiu a cor, com a linha "No mapa, a cor desta régua vale só
    para…";
  - no trecho cinza com motivo, abre "Sem classificação neste trecho" e diz por quê.
  - Antes, tocar num curso cinza não fazia nada.

## Auditoria por cidade e estação

Distâncias medidas em 07/10/2026 contra `data/rios/*.geojson`. "Faixa às 19h45" é a da coleta de produção das 19h45
(horário de Brasília).

### Afluentes e cabeceira Sul (vínculos novos)

| Cidade | Estação | Curso / traçado | Distância ao traçado | Continuidade | Alcance | Origem da cor | Faixa às 19h45 |
|---|---|---|---|---|---|---|---|
| Ituporanga | DCSC-00039 | Itajaí do Sul / `itajai-do-sul` | 19 m | 1 componente | até a confluência em Rio do Sul, 39,2 km | estadual | emergência |
| Ibirama | DCSC-00020 | Hercílio / `hercilio` | 67 m | 1 componente | até a confluência com o Açu, 4,6 km | estadual (a tabela de 2024 não vale agora) | atenção |
| Rio dos Cedros | DCSC-00011 | Rio dos Cedros / `rio-dos-cedros` | 49 m | 1 componente | até a estação Timbó 2 (DCSC-00034), 15,6 km | estadual (piloto sem municipal) | atenção |
| Trombudo Central | DCSC-00035 | Trombudo / `trombudo` | 11 m | 1 componente | até a estação de Agronômica (DCSC-00001), 17,2 km | estadual da própria estação; equivalência municipal não confirmada, sem conversão | normal |
| Guabiruba | DCSC-00029 | Ribeirão Guabiruba / `guabiruba` | 13 m | 1 componente | até a confluência com o Mirim, 6,7 km | estadual, quando publicada | sem faixa publicada → cinza |

### Cursos sem vínculo (pendência de dados mantida)

| Curso | Motivo |
|---|---|
| Benedito (Timbó) | A coordenada da régua municipal não está confirmada e a equivalência com a DCSC-00023 também não (decisão de 06/10/2026). O pino de Timbó continua com a faixa estadual da DCSC-00023, mas o rio não. |
| Ribeirão da Murta (Itajaí) | DC-07 e DC-09 estão sem aviso automático: cota não conferida (DC-07) e régua de estuário (DC-09). O traçado OSM estava partido entre a DC-07 e a foz (68 de 195 vértices alcançáveis) — **fechado em 08/10/2026** com os dois bueiros sem nome do OSM (`docs/VAO-MURTA.md`): 195 de 195 alcançáveis. O trecho do futuro vínculo (DC-07 → DC-09, 4,86 km) está delimitado lá, sem ativar. |
| ~~Ribeirão Canhanduba (Itajaí)~~ | ~~DC-08 sem aviso automático~~ — **vinculado por régua em 08/10/2026**, ver abaixo. |

### Cursos vinculados por RÉGUA (08/10/2026)

Decisão do Jefferson, 08/10/2026: "ribeirões com cota devem pintar conforme cota". A DC-08 foi destravada no #520
(cota de atenção provisória de 1,70 m) e o pino ficou verde ao lado de um curso cinza. `VINCULOS_DE_REGUA` liga o
traçado à **régua** (não à cidade): a cor do curso é a mesma decisão do pino da régua (`reguasNoMapa`), nada é
recalculado; régua sem cor (maré, sem cota, leitura velha) deixa o curso cinza com o motivo dela
(`regua-sem-cor`); na reprodução o curso fica cinza. O curso fica **parado**: correr é outra decisão.

| Curso | Régua | Distância ao traçado | Alcance | Fim | Acima da régua |
|---|---|---|---|---|---|
| Ribeirão Canhanduba / `ribeirao-canhanduba` | DC-08 "Rio do Meio" (Itajaí) | 13 m | 6,3 km | o último vértice do traçado OSM rio abaixo, 574 m antes do Mirim (o OSM não desenha a foz) | 11,5 km cinza (`fora-do-alcance`) |

O toque no trecho pintado abre o painel da régua, e o painel diz até onde a cor vale (`textoDoAlcanceDaRegua`) e o
que ela é: a classificação medida **na régua**, aplicada ao trecho vinculado — não medição em cada ponto do curso nem
mancha de inundação.

Regras confirmadas pelo Jefferson em 08/10/2026:

- **Os 574 m até o Mirim ficam sem linha e sem cor.** Nada é completado por aproximação; o alcance é só caminho em
  arestas existentes do traçado.
- **Reprodução: cinza** enquanto não houver leitura histórica da régua encaixada no instante escolhido e classificação
  correspondente. Hoje `construirCena` não recebe as réguas na reprodução; o motivo diz isso no toque.
- **Murta (destravar a DC-07):** além da decisão sobre a cota, é preciso (a) conferir a continuidade do traçado — estava
  partido entre a DC-07 e a foz, só 68 de 195 vértices alcançáveis; **fechado em 08/10/2026** pelos dois bueiros do OSM
  (`docs/VAO-MURTA.md`) — e (b) delimitar o trecho do vínculo novo: **da DC-07 até a DC-09** (próxima régua rio abaixo,
  4,86 km pelo traçado), não até a foz; os 1,43 km finais são da DC-09, de estuário. O rascunho do vínculo está no doc e
  **não** está em `VINCULOS_DE_REGUA`. O teste de `VINCULOS_DE_REGUA` exige caminho contínuo com o km declarado e reprova
  vínculo sem caminho.
| Rio Conceição, Ribeirão Taquaras, Rio Rafael e braços | Não há régua cadastrada. |

### Tronco

| Rio | Âncoras que pintam | Correção | Pendência |
|---|---|---|---|
| Itajaí-Açu (com o Oeste) | Taió, Rio do Sul, Lontras, Apiúna, Ascurra, Indaial, Blumenau, Gaspar, Ilhota, Itajaí (Ituporanga fica fora: a 23 km do Açu) | 71,5 km acima de Taió deixam de receber a cor de Taió | O traçado do Oeste tinha uma falha de **2,1 km** no OSM, rio abaixo de Taió (−27,14508, −49,91523 → −27,14841, −49,89417). **Fechada em 08/10/2026:** a via 1207901475 ("Rio Itajaí" no OSM, 6,0 km) liga as duas pontas (`docs/VAO-ITAJAI-DO-OESTE.md`). |
| Itajaí-Mirim | Vidal Ramos, Botuverá, Brusque, Itajaí | 25,4 km acima de Vidal Ramos deixam de receber a cor de Vidal Ramos | — |

As réguas de Itajaí (DC-01 a DC-11): a chegada da cheia segue a regra de sempre (DC-11 primeiro, DC-02 depois). A
DC-01 é referência do mar. Nenhuma faixa única de Itajaí se espalha pelos ribeirões.

## Defeitos corrigidos × pendências mantidas

- **Corrigidos (associação):**
  - os cinco cursos com estação vinculada passam a acompanhar a faixa do pino, no alcance;
  - Taió e Vidal Ramos deixam de pintar o rio acima;
  - o toque no cinza explica o motivo.
- **Mantidos (dados):**
  - Timbó/Benedito sem vínculo;
  - ribeirões de Itajaí sem respaldo de cota;
  - Guabiruba sem faixa publicada;
  - a falha de 2,1 km no Oeste (fechada em 08/10/2026, `docs/VAO-ITAJAI-DO-OESTE.md`);
  - Lontras, Apiúna e Indaial sem leitura municipal, como antes.

## Prints (390 px, dados de produção das 19h45)

`docs/prints/vinculos-tracados-2026-10-07/`:
- `ituporanga-antes-390.png` e `ituporanga-depois-390.png`;
- `ituporanga-depois-detalhes-390.png`: a origem da cor e o alcance no painel;
- `benedito-toque-cinza-390.png`: o motivo do cinza;
- `taio-antes-depois-390.png`.
