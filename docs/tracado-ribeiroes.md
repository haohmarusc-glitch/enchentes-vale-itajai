# Os cursos de Itajaí que faltavam no mapa — e como foram baixados

Levantado em 04/09/2026, depois que as onze réguas da Defesa Civil viraram
pontos no Monitor e quatro flutuavam fora de qualquer rio.

## RESOLVIDO em 04/09/2026

A consulta rodou na VPS, os três cursos entraram em `data/rios/`
(commit `72037eb`) e a medição fechou:

| régua | lugar | antes | agora | curso |
|---|---|---|---|---|
| DC-08 | Rio do Meio | 4,41 km | **0,00 km** | `ribeirao-canhanduba` |
| DC-03 | SEMASA | 2,32 km | **0,03 km** | `mirim-canal-retificado` |
| DC-07 | Portal I | 2,25 km | **0,01 km** | `ribeirao-murta` |
| DC-09 | Bairro Murta | 0,87 km | **0,01 km** | `ribeirao-murta` |

**As onze réguas caem a menos de 50 m do curso delas**, e cada uma no curso
que o cadastro diz. A única diferença de nome é a DC-03, cadastrada como
`itajai-mirim` e casada com `mirim-canal-retificado`: é o mesmo rio, na obra
que o retificou, e o cadastro guarda essa distinção no título de cada régua
("canal retificado" contra "curso antigo", onde ficam a DC-05 e a DC-06).

A DC-11 continua a **0,09 km**, como já estava: não tinha o que consertar, e
serve de controle de que a mudança mexeu só nos ribeirões.

`scripts/teste_conferir_reguas_no_tracado.py` deixou de guardar o retrato das
quatro que faltavam e passou a cobrar a regra — **nenhuma régua sem curso
desenhado** —, mais o casamento de cada uma com o curso certo. Se um geojson
for apagado ou trocado, o teste diz qual régua voltou a flutuar.

O texto abaixo é o registro de como se chegou lá.

## O que foi medido (não olhado), em 04/09/2026 pela manhã

`python3 scripts/conferir_reguas_no_tracado.py` mede a distância de cada régua
à **linha** do traçado mais próximo:

| régua | lugar | distância | curso que falta |
|---|---|---|---|
| DC-08 | Rio do Meio | **4,41 km** | Rio Canhanduba |
| DC-03 | SEMASA | **2,32 km** | canal retificado do Mirim |
| DC-07 | Portal I | **2,25 km** | Ribeirão da Murta |
| DC-09 | Bairro Murta | **0,87 km** | Ribeirão da Murta |

As outras **sete** estão a menos de 0,2 km.

**O tronco está certo.** A DC-11 Santa Regina fica na margem do meandro da
**Volta de Cima** e cai a **0,09 km** do traçado — o que só acontece se a curva
estiver desenhada. A "linha reta" que aparecia num recorte era o meandro
**cortado pela moldura do gráfico**, não um defeito do dado: o traçado do Açu
vai até `lat -26,8378`, e o meandro sobe até ~−26,84.

## Por que faltavam

A consulta original pediu só `waterway=river`. Ribeirão é `waterway=stream` e o
canal é `waterway=canal` — nenhum dos dois entrou. O bruto que temos
(`data/brutos/tracado-rios-osm.json`) tem exatamente três nomes: *Rio Itajaí do
Oeste*, *Rio Itajaí-Açu* e *Rio Itajaí-Mirim*.

## Como baixar (na VPS — o egress do dev não alcança o Overpass)

O resultado vai para um arquivo **separado**, `tracado-ribeiroes-osm.json`. O
bruto do tronco **não é tocado**: ele já produz um traçado conferido, e
rebaixá-lo para acrescentar ribeirão arriscaria mexer no que está certo por
causa do que falta.

```
cd /opt/enchentes-vale-itajai
cat > /tmp/ribeiroes.overpassql <<'Q'
[out:json][timeout:180];
(
  way["waterway"]["name"~"Murta|Canhanduba|Rio do Meio",i](-27.10,-48.85,-26.83,-48.60);
  rel(15693594);
  way(r);
);
out geom;
Q
curl -sS --data-urlencode "data@/tmp/ribeiroes.overpassql" \
  https://overpass-api.de/api/interpreter \
  -o data/brutos/tracado-ribeiroes-osm.json
python3 -c "import json;d=json.load(open('data/brutos/tracado-ribeiroes-osm.json'));\
import collections;print(collections.Counter((e.get('tags') or {}).get('name') for e in d['elements']))"
python3 scripts/converter_tracado_rios.py
python3 scripts/conferir_reguas_no_tracado.py
```

A penúltima linha imprime os nomes que vieram — **confira antes de gravar**. Se
vier vazio ou com nome inesperado, o `converter_tracado_rios.py` pula com aviso
em vez de emitir um rio pela metade, que é o comportamento certo: meio rio no
mapa engana mais que rio nenhum.

`rel(15693594)` é a relação do **canal retificado do Mirim**, citada no
levantamento de 02/09. **Não foi verificada daqui** — se ela não for o canal, o
`conferir_reguas_no_tracado.py` continua acusando a DC-03, que é o sinal de que
o id está errado.

## Depois que os arquivos existirem

Nada mais a fazer no site: `MonitorBacia` já lista `ribeirao-murta`,
`ribeirao-canhanduba` e `mirim-canal-retificado` em `AFLUENTES`, que são
traçados **opcionais** — entram sozinhos quando o geojson aparece.

Eles entram como **linha cinza, sem cor de faixa**, porque nenhuma cidade os
pinta. As réguas que ficam neles (DC-07, DC-08, DC-09) também não pintam: têm
`alerta_automatico: false`. Ver `web/src/logica/reguasNoMapa.ts`.

## O que este número NÃO diz

Distância de régua a traçado **não** mede erro de coordenada da régua. A de
Blumenau fica ~3 km do talvegue porque a coordenada publicada é a da **estação**,
não a do ponto de medição. Por isso o script fala em "curso não desenhado" e não
em "coordenada errada" — e há teste travando esse texto.

## Uma ressalva sobre as figuras que circularam

O levantamento de 04/09 veio com várias imagens. As de traçado OSM
(`sinuosidade real`, `ribeirões + Volta de Cima`) batem com os nossos dados e
foram usadas. **Uma delas, estilizada, não serve como fonte**: põe a DC-01 perto
de Blumenau (ela está em Itajaí, `-26,909 / -48,652`), rotula DC-10 e DC-06
ambas como "Limoeiro" e desloca a DC-11. Ilustração não é levantamento — as
coordenadas continuam vindo do `Mapa.php` da Defesa Civil de Itajaí (02/09).
