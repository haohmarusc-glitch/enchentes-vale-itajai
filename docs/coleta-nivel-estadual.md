# Coletor de nível estadual — `scripts/coleta_nivel_sc.py`

O que é, por que existe, como rodar, como testar, o que ele NÃO faz.

> **Nota de fuso (correção do rascunho original).** A primeira versão deste coletor guardava
> `medido_em` em UTC cru, afirmando "contrato do projeto: sem fuso = UTC". Isso está **errado** e
> contradiz o `CLAUDE.md` e o irmão `coleta_chuva_sc.py`: no projeto, **`medido_em` sem fuso = hora de
> Brasília**. O coletor foi alinhado — converte o UTC do GraphQL para Brasília na entrada
> (`hora_local`), como todos os outros. `coletado_em` (momento da coleta) segue em UTC, que é o campo
> que realmente é UTC. É o mesmo erro de fuso que o projeto registra ter "custado uma sessão".

## O que é
Versão em Python do `curl` validado em 01/09/2026 no GraphQL da Defesa Civil de SC
(`POST monitoramento.defesacivil.sc.gov.br/graphql`, query `Tags_data`). Coleta o NÍVEL BRUTO de ~25
cidades da bacia num endpoint só, a cada ciclo de cron. É o coletor de nível estadual que o `main` não
tinha (existiam só `coleta_chuva_sc.py` e `gaspar_estadual.py`).

## Por que existe
Das 10 cidades do projeto sem nível ao vivo, 8 têm sensor de rio na rede estadual. Este coletor traz
esses números — mas como BRUTO, porque o zero da régua estadual NÃO é o zero das cotas municipais
(Ilhota 10,34 estadual × 3,25 régua; Rio do Sul 6,54 × 7,00; Brusque 2,90 × 4,81).

## O que ele faz quando chamado
1. POST no GraphQL (`Tags_data`), filtra `position.bacia ~ "Itaja"`.
2. Separa cada estação em TRÊS baldes:
   - `leituras` — nível bruto válido
   - `sem_leitura` — `rio_nivel.value == null` = sensor mudo AGORA (não "sem sensor"; ex.: Gaspar hoje)
   - `suspeitas` — grandeza/sensor errado (Guabiruba 24,91; Pomerode) ou valor > 30 m (altitude)
3. Descarta estações "(H)" — reportam altitude, não rio (Salete 399 m, Petrolândia 876 m…).
4. Grava `data/tempo-real/ultimo_nivel_sc.json`.

## Schema de cada leitura (regra do datum aplicada no código)
```json
{"codigo":"DCSC-00006","estacao":"SDC-SC Indaial","cidade":"indaial",
 "origem":"estadual","datum":"bruto_estadual","offset_datum":null,"usar_para_cota":false,
 "nivel_bruto_m":6.86,"medido_em":"2026-09-01T20:42:54","chuva_24h_mm":13.5,"lat":…,"lon":…}
```
- `datum` = `bruto_estadual`, ou `reservatorio` para as barragens (DCSC-00040 Oeste, 00038 Sul).
- **`usar_para_cota` é SEMPRE `false` na saída deste coletor.** Só vira `true` em outra etapa, quando um
  offset for calibrado POR ESTAÇÃO contra evento-âncora e validado em mais de um instante (Brusque provou
  que um ponto de coincidência não basta: 17h "offset ~0", 23h diferença 1,9 m).
- `medido_em` em **hora de Brasília, sem fuso** (convertido do UTC do GraphQL por `hora_local`). O contrato
  do projeto: sem fuso = Brasília; converter na exibição não é preciso, já está no fuso da tela.

## O que ele NÃO faz (de propósito)
- NÃO pinta faixa, NÃO compara com cota municipal, NÃO dispara aviso. O site pode mostrar
  "Indaial: 6,86 m (nível bruto estadual, régua própria da estação)" com fonte e horário — e só.
- NÃO usa `rio_nivel_tendencia` da API (é lixo: Pomerode 108, Ibirama 85, Trombudo 113). Tendência vem da
  NOSSA série.
- NÃO usa `rio_nivel.show.value` (é flag de exibição booleana, não o nível). Lê `rio_nivel.value`, e ainda
  com guarda `e_numero` (um booleano não é metro).

## As armadilhas que ele já trata (todas vistas em 01/09)
| # | Armadilha | Tratamento |
|---|---|---|
| 1 | `show.value` parece o nível mas é booleano | lê `rio_nivel.value`, com guarda `e_numero` |
| 2 | `value` null confundido com "sem sensor" | vai para `sem_leitura`, estação não some |
| 3 | estações "(H)" = altitude; valores > 30 m | descartadas / `suspeitas` |
| 4 | `rio_nivel_tendencia` é lixo | ignorado |
| 5 | timestamp UTC do GraphQL vs Brasília do projeto | **convertido** com `hora_local` (como `coleta_chuva_sc`) |
| 6 | `position.bacia` null quebra o filtro | tratado como `""` |
| 7 | Guabiruba 24,91 / Pomerode 0,86 (grandeza errada) | lista `SUSPEITAS` → balde `suspeitas` |

## Como rodar na VPS
Repo vivo: `/opt/enchentes-vale-itajai`.
```bash
cd /opt/enchentes-vale-itajai
python3 scripts/coleta_nivel_sc.py            # primeira execução à mão
python3 scripts/coleta_nivel_sc.py --so-acu   # só as estações mapeadas na CADEIA
```
Cron — **encadeado na linha do `coleta_niveis.py`, ANTES do publish**, para o `ultimo_nivel_sc.json`
sair fresco no mesmo ciclo (é `publicar_tempo_real.sh` quem o empacota junto do `ultimo.json`). A linha
é uma só:
```
*/15 * * * * cd /opt/enchentes-vale-itajai && python3 scripts/coleta_niveis.py >> /var/log/niveis.log 2>&1 && (python3 scripts/alerta_cotas.py; python3 scripts/coleta_nivel_sc.py ; ./scripts/publicar_tempo_real.sh) >> /var/log/niveis.log 2>&1
```
Usa `;` (não `&&`) antes do publish para um tropeço do coletor estadual não travar a publicação do nível
principal.

> **INCIDENTE 02/09/2026 — não repetir.** Na migração pro `/opt` esta entrada de cron se perdeu, e o
> `coleta_nivel_sc.py` ficou **13 h sem rodar**: as cabeceiras (Taió, Ituporanga, Rio do Sul…) congelaram
> no site enquanto o nível principal seguia fresco. O `saude_coleta.py` não pegou porque só vigiava o
> `ultimo.json` — corrigido: ele agora vigia também o `ultimo_nivel_sc.json` (`avaliar_bruto`). Numa
> próxima migração, confira que esta linha continua no `crontab -l`.

Aviso honesto: o parser (`converter`) foi testado offline com a estrutura real de 01/09
(`teste_coleta_nivel_sc.py`: Indaial→leitura, Gaspar→sem_leitura, Salete(H)→descartada, Guabiruba→suspeita,
barragem→reservatorio, bacia null→ok, fuso→Brasília). A chamada de REDE não foi testada pelo assistente (o
container não alcança o host) — o primeiro `python3` real é na VPS. Se der erro, colar a saída.

## Tarefas que ele habilita (próximas)
1. **Série de nível bruto** — acumular `ultimo_nivel_sc.json` em ndjson (como `coleta_niveis.py` faz para
   Itajaí). É dela que sai a tendência confiável e o offset.
2. **Calibração de offset** — para Ibirama (00020) e Indaial (00006), as mais próximas: um evento-âncora
   (cheia documentada com cota oficial) → `offset = bruto_no_evento − cota_oficial`, validado em ≥2 instantes.
   Indaial: antes, confirmar se a PCD mede o Açu ou o afluente Benedito.
3. **Integrar ao `coleta_niveis.py`** como fonte secundária (molde de `baixar_chuva_sc`), trazendo estas
   leituras para a mesma lista — SEM promover a cota. Como `medido_em` já está em Brasília (igual ao resto),
   o vigia (`saude_coleta.py`) não precisa de mudança de fuso; a única pendência antes de integrar é ele
   agrupar por cidade para não contar a mesma cidade duas vezes.
4. **Docs de apoio a criar**: `docs/cobertura-nivel-por-cidade.md` (o mapa de quem tem/nao tem nível) e
   `docs/nivel-estadual-itajai-acu.md` (o levantamento das estações e offsets). Referenciados aqui, ainda
   não escritos.

## Estações na CADEIA (código → cidade)
Açu: 00025 agrolândia · 00039 ituporanga · 00033 pouso-redondo · 00041 taió · 00031 laurentino ·
00001 agronômica · 00013 rio-do-sul · 00032 lontras · 00020 ibirama · 00043 presidente-getúlio ·
00021 josé-boiteux · 00003 ascurra · 00006 indaial · 00023 timbó · 00004 benedito-novo ·
00011 rio-dos-cedros · 00028 doutor-pedrinho · 00007 pomerode(suspeita) · 00026 blumenau(não reporta) ·
00005 gaspar(intermitente) · 00030 ilhota · 00163 ilhota-arraial-dos-cunhas
Mirim: 00024 vidal-ramos · 00018 botuverá · 00027 botuverá-2 · 00019 brusque · 00029 guabiruba(suspeita)
Barragens (reservatório): 00040 oeste-taió · 00038 sul-ituporanga
