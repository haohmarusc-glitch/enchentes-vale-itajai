# O Itajaí do Sul não estava no mapa — 05/09/2026

A cabeceira que se junta a Taió em Rio do Sul, e que traz a parcela maior da água a montante dali,
**não estava desenhada**. Achado por Jefferson no `#/monitor` em produção.

## A medida

| Ponto | Ao traçado mais perto | Situação |
|---|---|---|
| Barragem Oeste | 0,05 km | no traçado |
| Taió | 0,04 km | no traçado |
| Rio do Sul | 0,05 km | no traçado |
| Ascurra | 0,11 km | no traçado |
| Blumenau | 2,99 km | conhecido: a coordenada é a da ESTAÇÃO, ~3 km do talvegue |
| **Ituporanga** | **27,99 km** | ⛔ flutuando |
| **Barragem Sul** | **31,33 km** | ⛔ flutuando |

## A causa raiz — duas camadas da mesma omissão

1. **A consulta do Overpass nunca pediu o Sul.** Medido no bruto: `data/brutos/tracado-rios-osm.json`
   tem **50 ways "Rio Itajaí do Oeste" e ZERO "Rio Itajaí do Sul"**.
2. **O conversor não o listava.** `RIOS` em `scripts/converter_tracado_rios.py` era
   `{"itajai-acu": ["Rio Itajaí do Oeste", "Rio Itajaí-Açu"], "itajai-mirim": [...]}`.

O nome do arquivo escondeu o problema: `itajai-acu.geojson` contém **o tronco mais o Oeste**, então
Taió e a Barragem Oeste caem em cima dele e tudo parecia certo.

**É a terceira vez que a mesma omissão aparece.** Antes dela: os ribeirões de Itajaí (a consulta só
pediu `waterway=river`, e DC-07, DC-08 e DC-09 flutuavam) e o vão do Canhanduba. Agora o Sul — e, achado
pela trava nova, o **Ribeirão Guabiruba**.

## Por que importa mais do que "um pino fora do lugar"

A linha que passa perto de Ituporanga **é o Itajaí do Oeste**, vindo de Taió. Quem olha o mapa lê
`Taió → Ituporanga → Rio do Sul`, **em série**. É a fila voltando pela porta dos fundos: os dados, o popup
e a árvore do Monitor dizem a topologia certa, e o **desenho** dizia o contrário — e o desenho é o que o
morador lê primeiro.

Áreas de drenagem (JICA Vol. III-A, Tab. 2.1.1): Itajaí do **Sul 2.026,87 km²**, Oeste 3.014,37 km².
Pela rede estadual, a Barragem Sul drena **1.165 km²** contra 851 da Oeste. O ramo que não aparecia é o
que estava causando a atenção em Rio do Sul no dia do achado.

## O que foi feito

**Desenhado o que existe.** `data/brutos/rio-do-sul-rios-tracados.geojson` — a captura da API Asthon da
Defesa Civil de Rio do Sul, já no repositório desde 04/09 — traz **"Rio Itajaí do Sul", 35 pontos**.
Virou `data/rios/itajai-do-sul.geojson` e entra no mapa da bacia.

⚠️ **PARCIAL, e o arquivo diz isso** (`properties.cobertura`): são **10,5 km** de cobertura municipal.
Desenha as duas cabeceiras **chegando à confluência** — a afirmação que corrige o erro de leitura — e
**não alcança Ituporanga**, 21,4 km a montante. Ituporanga segue fora da guarda geométrica de 5 km, então
continua sem pintar traçado, que é o certo enquanto o rio dela não estiver desenhado até lá.

**Travado o que ninguém tinha medido.** `valida_pinos_no_tracado`, em `scripts/validar_dados.py`: cada
cidade tem de cair a **menos de 1 km** do traçado de algum rio dela. Exceções são **nomeadas, com motivo e
teto próprio** — piorar uma exceção também reprova. Ituporanga a 28 km teria reprovado antes de ir ao ar.

**A trava achou um segundo caso na primeira execução:** **Guabiruba, a 4,24 km** do Mirim e longe de todo
o resto. Não é coordenada errada — a cidade fica no **Ribeirão Guabiruba**, que não está desenhado. O
`coleta_nivel_sc.py` já dizia, por outro caminho, que a leitura dela é "implausível **para o ribeirão**".

## O que falta, e como fazer

Rodar na VPS, onde há rede (daqui o Overpass responde 403 no proxy):

```bash
curl -sS 'https://overpass-api.de/api/interpreter' --data-urlencode 'data=
[out:json][timeout:60];
(
  way["waterway"]["name"~"Itajaí do Sul",i](-27.60,-49.75,-27.15,-49.45);
  way["waterway"]["name"~"Guabiruba",i](-27.15,-49.05,-26.98,-48.90);
);
out geom;' > data/brutos/tracado-cabeceira-sul-osm.json
```

Depois: acrescentar `"itajai-do-sul": ["rio itajaí do sul", "rio itajai do sul"]` e
`"ribeirao-guabiruba": ["guabiruba"]` a `RIOS_AFLUENTES`, ler o bruto novo junto dos outros, rodar
`python3 scripts/converter_tracado_rios.py` e `python3 scripts/validar_dados.py`. Os dois números caem
para menos de 1 km, e as duas exceções saem de `LONGE_ACEITO` — a remoção da exceção é a prova de que
ficou pronto.

## Verificação

- [x] `itajai-do-sul.geojson` existe e é carregado pelo Monitor
- [x] As duas cabeceiras convergem visualmente em Rio do Sul
- [x] O teste de distância pino ↔ traçado roda no `validar_dados.py`
- [ ] Ituporanga e Barragem Sul a menos de 1 km (depende do Overpass)
- [ ] Guabiruba a menos de 1 km (idem)
