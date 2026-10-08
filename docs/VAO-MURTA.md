# Os dois trechos que faltavam no Ribeirão da Murta, entre a DC-07 e a foz (08/10/2026)

## O problema

A auditoria dos vínculos (`docs/VINCULOS-DOS-TRACADOS.md`) mediu, em 08/10/2026, que o traçado do Ribeirão da Murta
(`data/rios/ribeirao-murta.geojson`) estava em **três pedaços** que não se tocavam. A partir da DC-07, só 68 dos 195
vértices eram alcançáveis — e vínculo de régua só pinta caminho **contínuo** em arestas do traçado (`arestasDoAlcance`).
Jefferson, 08/10/2026: "destravar a DC-07 exige também conferir a continuidade do traçado e delimitar o trecho do novo
vínculo".

| via do OSM ("Ribeirão da Murta") | ponta | vão |
|---|---|---|
| 138922683 (onde fica a DC-07) termina em | −26,89213, −48,720949 | **78 m** até… |
| 390147234 começa em | −26,892064, −48,720167 | |
| 390147234 termina em | −26,891344, −48,716999 | **38 m** até… |
| 556881889 começa em | −26,891114, −48,71671 | (segue, já ligada às outras duas, até a foz no Açu, passando pela DC-09) |

A consulta que gerou o bruto dos ribeirões (`docs/tracado-ribeiroes.md`, 04/09/2026) pedia o curso **pelo nome**.

## A busca

`scripts/baixar_vao_murta.py` pede ao Overpass **todo** curso d'água numa caixa de 1,2 km em volta das quatro pontas,
sem filtrar por nome, e encadeia por conectividade cada vão — como o `baixar_vao_oeste.py`, mas mais rigoroso: a
cadeia só conta como chegada quando **termina** a menos de 30 m da ponta de jusante (o alvo de 100 m do Canhanduba é
maior que os dois vãos inteiros), e via que já está no bruto dos ribeirões não serve de emenda. Se as próprias vias da
Murta no OSM de hoje ligarem as pontas, o script recusa emendar e pede para rebaixar o bruto dos ribeirões. Roda no
Actions (`baixar-vao-murta.yml`), porque o Overpass não responde ao ambiente das sessões, e publica no branch
`vao-murta`.

**1ª rodada (base OSM de 08/10/2026 16:49 UTC):** o espelho principal deu 504 duas vezes e respondeu na terceira. A
caixa tem 8 cursos (6 `river`, 2 `ditch`; 4 "Ribeirão da Murta" e 4 sem nome) e nenhuma área de água. Os dois vãos são
**bueiros** — exatamente o que se esperava de falhas do tamanho de uma rua:

| vão | via | tags | pontos | comprimento | pontas |
|---|---|---|---|---|---|
| 1 | **138922682** | `waterway=river`, `tunnel=culvert`, `layer=-1`, sem nome | 2 | 78 m (reta 78 m) | os **mesmos nós** das vias 138922683 e 390147234 (0 m) |
| 2 | **556881887** | `waterway=river`, `tunnel=culvert`, sem nome | 2 | 38 m (reta 38 m) | os **mesmos nós** das vias 390147234 e 556881889 (0 m) |

O vão 2 foi recusado nessa rodada por **0,3 mm**: a cadeia saiu "mais curta que a reta" porque as pontas cadastradas em
`VAOS` têm seis casas decimais e a via tem sete. O script ganhou `TOLERANCIA_M = 1.0` (continua recusando via que pare
2 m antes), e a **2ª rodada** gravou o segundo bueiro.

## Como entrou

- O `converter_tracado_rios.py` emenda as duas vias no `data/rios/ribeirao-murta.geojson` **pelo número** (`EMENDAS`,
  antes `EMENDAS_DO_TRONCO`, agora também para afluentes), nunca pelo nome — bueiro sem nome não vira nome aceito.
- Via que vier com outro nome aborta a conversão e pede nova conferência.
- O arquivo registra as emendas em `properties.emendas` (com `tunnel: culvert`) e o bruto novo em `properties.origem`.
- Sem o bruto `data/brutos/vao-murta-osm.json`, o ribeirão volta a ser o de antes. O arquivo do Açu não muda.

## O que muda na tela

- O traçado da Murta fica **contínuo** da nascente desenhada até a foz no Açu: 5 → 7 trechos, **195 de 195** vértices
  alcançáveis a partir da DC-07 (antes, 68 de 195).
- **Nenhuma cor muda.** A Murta continua sem vínculo (`SEM_VINCULO`): a DC-07 segue com `alerta_automatico: false` (cota
  não conferida contra a série, decisão do Jefferson) e a DC-09 é régua de estuário. A continuidade do traçado é a
  **condição (a)** para destravar a DC-07, não a decisão.
- Dois bueiros de 78 m e 38 m sob ruas não mudam o enquadramento do Monitor.

## O trecho do futuro vínculo DC-07 (delimitado, NÃO ativado)

Medido no traçado contínuo (`scripts/medir_alcance_murta.py`), com as réguas na coordenada do cadastro:

| | |
|---|---|
| Régua | DC-07 "Ribeirão da Murta - Portal" (Itajaí), a **10 m** do traçado |
| Início do alcance | o ponto do traçado mais próximo da DC-07: **−26,89278, −48,735539** |
| Próxima régua rio abaixo | DC-09 "Ribeirão da Murta - Ponte da Rua Lidia Puel Peixer", a **9 m** do traçado, em **−26,8797, −48,700295** |
| **DC-07 → DC-09** | **4,86 km** pelo traçado |
| DC-09 → foz no Açu (−26,879284, −48,691469) | 1,43 km |
| DC-07 → foz | 6,29 km |
| Acima da DC-07 (fica cinza, `fora-do-alcance`) | o ribeirão até a nascente desenhada, −26,899397, −48,748696 |

Pela regra de `VINCULOS_DE_REGUA` (o alcance vai da régua até a **próxima régua rio abaixo** ou a confluência, o que
vier antes), o vínculo da DC-07 vai **até a DC-09**, não até a foz: os 1,43 km finais são da DC-09, que é de estuário e
não pinta. O rascunho, para quando o Jefferson destravar a DC-07:

```ts
{ tracado: 'ribeirao-murta', cidade: 'itajai', regua: 'DC-07',
  inicio: [-48.735573, -26.892699], fim: [-48.700308, -26.879777],
  fimDescricao: 'a régua DC-09 (Ponte da Rua Lidia Puel Peixer), 1,4 km antes da foz no Itajaí-Açu', km: 4.9 }
```

Isto **não** está em `VINCULOS_DE_REGUA`. Condições que faltam, na ordem: (1) decisão sobre a cota da DC-07 (Plano v17
× portal, `docs/AUDITORIA-2026-09-19-fechamento.md`); (2) `alerta_automatico: true` na DC-07, por decisão do Jefferson;
(3) o teste de `VINCULOS_DE_REGUA` confere o caminho contínuo e o km.

## O que não faz

- Não desenha reta: as duas vias são geometria do OSM (o bueiro, com `tunnel=culvert`), não traço nosso.
- Não muda vínculo, cota, classificação nem `alerta_automatico`.
- Não mexe em arquivo protegido do Monitor.
