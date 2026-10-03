# Décima rodada (03/10/2026) — incremental, prompt v3.7

Pacote `cheias_itajai_fontes_v3.7_incremental_2026-10-03.zip`
(sha256 `badd213790bc13ff9dec1fbd3ca3da7fd8d824990fc7c949354e0999b4f06560`), enviado pelo Jefferson.
Coleta da pesquisa externa em 03/10/2026, 00:04–00:06 BRT. O `MANIFEST_SHA256.txt` do pacote confere com
todos os arquivos.

* `instrucoes/prompt-picos-v3.7.txt` **não foi copiado**: é idêntico, byte a byte, ao da nona rodada
  (`../rodada9/prompt-picos-v3.7.txt`, sha256 `e0955209…` no manifesto do pacote).
* `fontes/boletim_hidrometeorologico.html` — página da SEMAE/SDC-SC (aguas.sc.gov.br), HTTP 200. Conferido aqui:
  a lista de 2026 tem 01, 02, 03, 06 e 07/2026 (07/07/2026 é o último); **não há 08 nem 09/2026**, e também
  faltam 04 e 05/2026.
* `fontes/chm_tabuas.html` e `chm_headers.txt` — Marinha/CHM respondeu HTTP 403 com desafio do Cloudflare
  (`cf-mitigated: challenge`). Não confirma nem nega a tábua de 2027.
* `README_resultados.md` e `resultados_documentos.csv` — relatório da pesquisa, como veio.

Nenhum pico novo; nada entra em `enchentes.json`. Ver `docs/PICOS-FALTANTES.md` §17.
