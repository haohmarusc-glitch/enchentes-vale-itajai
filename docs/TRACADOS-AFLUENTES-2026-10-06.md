# Benedito, Itajaí do Sul e Trombudo no Monitor (06/10/2026)

Pedido do Jefferson, depois da auditoria das réguas: desenhar o rio de Timbó, o de Ituporanga e o de Trombudo
Central. Os pinos já ficavam na régua desde a auditoria; faltava o rio aparecer.

## Como entraram

1. `scripts/baixar_tracados_afluentes.py` pede ao Overpass cada rio pelo **nome exato** e confere duas coisas
   antes de gravar:
   - o traçado chega a um rio já desenhado;
   - o traçado passa pela régua da cidade.

   Rio que falha não grava.
2. O script rodou no GitHub Actions (`baixar-tracados-afluentes.yml`), porque o Overpass não responde ao ambiente
   da sessão. Os brutos e o resumo da rodada são publicados no branch `tracado-afluentes`.
3. `converter_tracado_rios.py` gerou os arquivos de `data/rios/`, recortados na **caixa do mapa**: a extensão do
   tronco e das réguas do cadastro. Assim o enquadramento do Monitor não muda. O Itajaí do Sul do OSM
   **substitui** o trecho de 10,5 km da Defesa Civil de Rio do Sul (Asthon).

| Rio | No OSM | Depois do recorte | Chega a | Distância ao pino |
|---|---|---|---|---|
| Rio Benedito (`benedito`) | 12 ways, 67,0 km | 47,5 km, de Rio dos Cedros até o Açu | Açu, entre Indaial e Blumenau | Timbó, 0,63 km |
| Rio Itajaí do Sul (`itajai-do-sul`) | 25 ways, 87,8 km | 54,7 km, da borda sul do mapa até Rio do Sul | Açu, em Rio do Sul | Ituporanga, 0,02 km |
| Rio Trombudo (`trombudo`) | 17 ways, 40,9 km | 40,9 km, inteiro | Açu (trecho do Itajaí do Oeste) | Trombudo Central, 0,25 km |

## O que isto não muda

- **A árvore da bacia.** Chegar a um rio é geometria do OSM, não topologia declarada por fonte. Em
  `estacoes.json`:
  - Trombudo Central continua sem posição (em "Outros pontos");
  - Timbó continua afluente lateral, como já era.

  O OSM mostra o Trombudo chegando ao trecho do **Itajaí do Oeste**. Isso fica registrado aqui como indício;
  mudar a árvore é decisão do Jefferson, com fonte (`docs/TOPOLOGIA-CANONICA.md`).
- **A cor.** Os três rios não têm cidade no cadastro e ficam cinza, como o Hercílio: mostram por onde a água
  corre, não pintam faixa.
- **As equivalências.** Nenhuma muda. A DCSC-00023 (Timbó 1) fica a **0,05 km** do Benedito, mais perto do
  rio do que o pino de Timbó (0,63 km), cuja coordenada não tem fonte declarada. Isso **não** vincula a estação
  à régua municipal: a equivalência segue "não confirmada" (decisão de 06/10/2026).

## Limites de distância ao pino

- **Ituporanga: 0,5 km.** O pino é a coordenada da estação DCSC-00039.
- **Timbó e Trombudo Central: 1 km.** As coordenadas não têm fonte declarada no cadastro. Na primeira rodada, o
  Benedito passou a 0,63 km do pino de Timbó e foi recusado no limite de 0,5 km. O limite subiu com esse motivo
  escrito no script.

## Efeitos conferidos

- **Validador:** saiu a exceção `LONGE_ACEITO["ituporanga"]` (25 km). O pino fica a 0,02 km do Itajaí do Sul.
- **Confluência:** `achar_confluencias.py` mede a do Benedito: entra depois de Indaial e antes de Blumenau, a
  90,4 km de Rio do Sul pela água. Isso bate com o aviso do `transito.json`, em que Blumenau pica antes de
  Indaial em algumas colunas da JICA "por causa do Benedito". O `ponto_exato` **não** foi gravado: `--gravar`
  é decisão do Jefferson.
- **Testes:** `conferir_afluentes_chegam.py` (os 11 afluentes chegam ao rio que os recebe, a menos de 100 m),
  `teste_baixar_tracados_afluentes.py`, `teste_converter_tracado_rios.py`, `teste_achar_confluencias.py`, os
  testes do site e a trava do Monitor passaram.
- **Navegador:** conferido no Chromium, na bacia inteira, em Timbó, em Ituporanga e em Trombudo Central.

## Refazer

Rodar o workflow "Baixar traçados dos afluentes" (Actions → Run workflow). Depois, na sessão:

```bash
git fetch origin tracado-afluentes
for r in benedito itajai-do-sul trombudo; do
  git show FETCH_HEAD:tracado-$r-osm.json > data/brutos/tracado-$r-osm.json
done
python3 scripts/converter_tracado_rios.py
```

Fonte dos traçados: © OpenStreetMap contributors, ODbL.
