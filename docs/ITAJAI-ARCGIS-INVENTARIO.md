# O ArcGIS de Itajaí — o que já temos, o que é novo, e a palavra "cota"

Levantamento de Jefferson (05–06/09/2026) sobre `arcgis.itajai.sc.gov.br/server/rest/services` —
**200 serviços públicos sem token**; a pasta `defesacivil` exige token, o resto da raiz é aberto.
Abaixo, o que eu **conferi contra o repositório**, porque metade já estava lá.

---

## ⛔ A armadilha central: TRÊS coisas diferentes se chamam "cota"

| o que é | faixa típica | onde aparece |
|---|---|---|
| **lâmina d'água** — quanto a água subiu NAQUELE ponto | **0 a 2,86 m**, mediana 0,60 | app "Cotas de Inundação" do ArcGIS, campo **`cota`**; campo `situa` das manchas |
| **cota de rua** — o NÍVEL DO RIO em que a rua alaga | **3,11 a 21,00 m** | `data/cotas-ruas.json`, campo `cota_m` |
| **cota altimétrica** — altura do terreno sobre um datum | **0,15 a 370 m** | `Relevo_Ponto_Cotado_Altimetrico`, `Relevo_Curva_Nivel` |

**O app da prefeitura chama a lâmina de "cota".** Se aqueles 3.434 pontos entrassem em
`cotas-ruas.json` porque "as duas têm cota", o site diria *"a sua rua alaga com o rio em 0,60 m"* — e o
rio está nesse nível quase sempre.

**A separação é medida, não estipulada.** As 4.588 cotas de rua do cadastro: Blumenau mín 7,40 ·
Gaspar 6,20 · Brusque 3,76 · Rio do Sul 3,11. **Nenhuma abaixo de 3,00 m.** As lâminas de Itajaí,
nenhuma acima de 2,86. **As duas faixas não se tocam**, e `valida_cota_de_rua_nao_e_lamina` põe o piso
no vão entre elas. Sabotagem conferida: uma lâmina de 0,60 m importada como cota reprova.

---

## O que JÁ ESTAVA no repositório (conferido feição a feição)

**As 357 manchas do `historico_inundacoes` são DUPLICATA** do que já temos pelo GeoItajaí. Comparação,
camada por camada:

| evento | ArcGIS | repo (`data/manchas/itajai/`) |
|---|---|---|
| 1983 · 1984 · 2001 · 2008 | 1 · 1 · 1 · 1 | 1 · 1 · 1 · 1 |
| 2011 (área atingida) | 32 | 32 |
| 2011-09 (lâmina) | 5 | 5 |
| 2013-07 · 2013-09 | 48 · 58 | 48 · 58 |
| **2014-06** | 55 | **55** |
| 2015-10 | 155 | 155 |

**Batem todas.** O arquivo de 1,9 MB **não foi acrescentado** — sustenta a decisão já tomada de não
trocar uma fonte pela outra.

**Duas correções ao levantamento:**
1. **2014-06 não é "evento novo"** — está em `inundajunho2014.geojson` desde o início, com as mesmas 55
   feições.
2. **Os 5.237 pontos cotados também já estão** em `data/brutos/itajai-pontos-cotados-altimetricos.geojson.json`,
   e o `_meta` de lá já avisa: *"ALTURA DO TERRENO, não cota de régua"*.

---

## O que é GENUINAMENTE NOVO e ainda falta baixar

| o quê | tamanho | por que importa |
|---|---|---|
| **3.434 lâminas por endereço** | 363 KB | **o achado.** Profundidade medida, endereço por endereço, em 4 eventos. Nenhuma outra cidade da bacia tem |
| 17.120 **curvas de nível a 1 m** | 456 MB em GeoJSON | 8.346 delas entre 1 e 10 m — resolução de modelo de terreno |
| 57.418 **lotes** (`malhacrs3857`) | — | geocodificação com precisão de LOTE, sem depender do OSM |
| 129.296 **edificações** com `numpav` | — | a orientação em enchente é **subir de andar**; saber quais têm mais de um pavimento é informação de segurança |
| `Hidrografia_Trecho_Drenagem` | — | **provável fonte dos ribeirões Murta e Canhanduba**, que hoje faltam no traçado |

⚠️ **Acentuação corrompida na origem** (`Bernardino Jo?o Victorino`): mojibake latin1→utf8 do próprio
ArcGIS. Corrigir no processamento, nunca no download.

---

## ⛔ O que trava o terreno: o DATUM VERTICAL não está declarado

Nem `Relevo_Curva_Nivel` nem `Relevo_Ponto_Cotado_Altimetrico` dizem o datum das cotas. O CRS
horizontal é EPSG:31982 (SIRGAS 2000 / UTM 22S); **o vertical não está em lugar nenhum**.

**Sem esse número, nada disso vira "até onde a água chega".** Subtrair o nível da régua DC-01 de uma
cota altimétrica é o erro de referência que o projeto já cometeu em Ilhota, em Brusque e na série de
Blumenau.

Dois caminhos: **perguntar ao GEOItajaí/COMPDEC** o datum e o offset para o zero de cada régua DC; ou
**derivar empiricamente**, cruzando as manchas por faixa de lâmina com as curvas de nível do mesmo
evento — se a mancha de "0,41 a 0,60 m" de out/2015 acompanha a curva de 3 m, o offset sai da
comparação. O segundo é mais atraente porque os dois lados vêm do mesmo levantamento.

---

## O que isto muda no inventário de Itajaí

Continua verdade que **Itajaí é a única cidade sem cota de rua**. Mas ela tem algo que **nenhuma outra
da bacia tem: profundidade medida por endereço, em quatro eventos**. Blumenau, Brusque, Gaspar e Rio do
Sul têm o limiar; Itajaí tem o registro do que aconteceu.

**O que isso permite dizer:** *"neste endereço, em setembro de 2011, a água chegou a 60 cm"*.
**O que não permite:** prever. E **continua faltando o pico do rio de cada evento** para indexar a
biblioteca por nível — o bloqueio de `ADENDO-2026-09-05-NOITE.md`, que a busca externa não resolveu.
