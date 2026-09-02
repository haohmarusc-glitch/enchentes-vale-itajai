# TOPOLOGIA CANÔNICA — a bacia do Itajaí é uma ÁRVORE, não uma fila

**Este documento é a fonte única sobre a TOPOLOGIA da bacia.** Se o código, outro
doc ou uma figura discordarem dele sobre quem está a montante/jusante de quem,
**ele vence** — e o `estacoes.json` (o dado) manda no resto. Verificado em mapa +
Overpass em 02/09/2026 (marcador OSM na coordenada de cada estação, lendo o rótulo
da via de água sob ele; e `way["waterway"]["name"](around:1000,lat,lon)`).

A regra que sustenta tudo: **distância em linha reta não ordena rio ramificado.**
Antes de assumir cadeia linear em qualquer rio, verificar a ramificação.

## Itajaí-Açu — árvore

```
Itajaí do OESTE (Taió)  ‖  Itajaí do SUL (Ituporanga)   ← cabeceiras PARALELAS
              └───────────┬───────────┘
                     RIO DO SUL          ← aqui NASCE o Itajaí-Açu (começo do tronco)
                          │
                          │ ← entra o Rio Hercílio / Itajaí do Norte
                          │     [IBIRAMA = afluente lateral, NÃO elo do tronco]
                       ASCURRA            (tronco)
                          │ ← entra o Rio Benedito (Timbó), perto de Indaial *
                       INDAIAL → BLUMENAU → GASPAR
                          │ ← entra o Rio Luís Alves, perto de Ilhota *
                        ILHOTA
                          │ ← entra o ITAJAÍ-MIRIM (que é ramificado; ver abaixo)
                        ITAJAÍ → foz (Atlântico)
```

**\*** O **ponto exato** onde o Benedito e o Luís Alves entram (antes ou depois
da régua de Indaial / Ilhota) **ainda não está confirmado** — as fontes internas
divergiam (o `afluentes_monitorados` do Timbó dizia "entre Indaial e Blumenau").
Registrado como pendência em `_topologia.afluentes_rios`, para resolver no mapa
quando o Overpass voltar (esteve fora do ar em 02/09). Não se inventa o lado.

**A única sequência que a UI pode afirmar** (`_topologia.tronco_sequencia`):

`Rio do Sul → Ascurra → Indaial → Blumenau → Gaspar → Ilhota → Itajaí`

Fora dela:
- **Taió e Ituporanga são cabeceiras paralelas** — nenhuma vem "antes" da outra;
  as duas alimentam Rio do Sul. Um pico em Rio do Sul depende da SOMA Oeste + Sul.
- **Ibirama fica no Rio Hercílio** (afluente). O pico dele ENTRA no tronco perto de
  Rio do Sul, não desce por Indaial. Correlacionar Ibirama→Indaial isolado
  subestima (provável parte do r²=0,21 do `coleta_niveis.py`).
- **Apiúna saiu do eixo**: a estação estadual DCSC-00178 é de altitude ("(H)",
  reporta ~82 m) e cai em área de mata sem curso d'água — não é régua de rio.
  Fica em `_topologia.nao_e_regua_de_rio`. Ascurra (DCSC-00003, confirmada no
  tronco por Overpass) ocupa o lugar dela na sequência.

## Itajaí-Mirim — fila no eixo, árvore só nas réguas de Itajaí

As cidades do Mirim (Vidal Ramos → Botuverá → Guabiruba → Brusque → Itajaí) são
uma **fila** (`ordem` 1..N). A ramificação do Mirim aparece só entre as **réguas
DC de Itajaí**, na foz:

- **DC-10 Limoeiro** (tronco do Mirim) → divide-se em dois braços paralelos que se
  reencontram perto da foz:
  - **curso antigo:** DC-05 Sítio Hilário → DC-06 Itamirim
  - **canal retificado:** DC-03 SEMASA → DC-04 Vitalmar (reunião dos braços ≡ DC-06)

Isso já está em `estacoes_tempo_real` (campo do título: "(curso antigo)" /
"(canal retificado)") e na tela de Itajaí (`agruparPorCurso` / `dividirEmBracos`).

## Contrato no `estacoes.json` (vocabulário do `main`)

- `ordem`: sequência montante→jusante **só em rio não ramificado** (Mirim). Em rio
  ramificado (Açu) é **`null`** — usar ordem global afirmaria uma fila inexistente.
- `ramo`: em rio ramificado, o braço da cidade — `itajai_do_oeste | itajai_do_sul
  | itajai_do_norte | tronco_acu`. Só se compara posição DENTRO do mesmo ramo.
- `ordem_no_ramo`: posição montante→jusante dentro do ramo (1 = mais a montante).
- `codigo_dcsc`: liga a cidade à estação estadual (por coordenada), `DCSC-NNNNN`.
- `_topologia`: `tronco_sequencia`, `cabeceiras_paralelas`, `afluentes_laterais`,
  `nao_e_regua_de_rio`.

## O que TRAVA isso (a lição que custou versões)

Documentar a topologia **não impediu** o JSON de ficar errado por versões seguidas.
O que impede é o validador **abortar**. `scripts/validar_dados.py` agora falha se:

1. Aparecer `ordem` global (não-null) em rio ramificado.
2. Faltar `ramo`/`ordem_no_ramo` no Açu, ou `ordem_no_ramo` não for 1..N por ramo.
3. `tronco_sequencia` não bater com as cidades de `ramo: tronco_acu`.
4. Um `codigo_dcsc` esperado sumir ou trocar (a cidade ligada a uma estação
   estadual conhecida não pode desaparecer em silêncio).
5. Uma régua com `alerta_automatico: false` não disser o motivo (ela não pode
   virar faixa de perigo enganosa).

`scripts/teste_validar_dados.py` trava cada uma dessas — mudar a regra sem querer
fica vermelho. Rode `python3 scripts/validar_dados.py` antes de todo commit em
`data/`.

## Pendências (não bloqueiam a topologia)

- **Ponto exato** onde o Benedito e o Luís Alves entram (antes/depois das réguas
  de Indaial e Ilhota) — registrado em `_topologia.afluentes_rios` como "a
  confirmar por coordenada"; depende do Overpass/mapa (fora do ar em 02/09).
- Distância **ao longo do rio** no `transito.json` — **medida** (02/09/2026) por
  `scripts/medir_distancia_rio.py`, montando os segmentos do OSM num grafo e
  caminhando pela água. Gravada como `km_rio` (contexto/QA, **não** muda os
  tempos, que seguem do JICA) onde as duas pontas estão no traçado: Rio do Sul→
  Indaial 85,8 km, Gaspar→Ilhota 16,9 km, Ilhota→Itajaí 33,2 km — sinuosidade de
  **1,2 a 2,0×** a reta, velocidade implícita 3–9 km/h (coerente com o JICA).
  Fica de fora quem está longe do traçado (Blumenau, coordenada da estação ~3 km
  do talvegue) ou em braço não mapeado (Taió/Ituporanga, cabeceiras).
- ~~Trazer a estrutura de árvore ao `/rios` do bot~~ — **feito** (02/09/2026):
  `resposta_rios` mostra o Açu em três blocos (cabeceiras / tronco / afluentes),
  como a tela; o Mirim segue em fila. Travado por `teste_bot.py`.
- Chuva de Apiúna: os mapeamentos (CEMADEN, DCSC-00178) foram removidos com a
  saída do município do eixo; se um dia quiser mostrar chuva de ponto fora do
  eixo, é uma feature à parte.
- Coordenadas das 11 réguas DC: divergência do documento de rota × Mapa.php
  registrada em `docs/coordenadas-dc-itajai.md` (mantidos os marcadores do Mapa.php).
