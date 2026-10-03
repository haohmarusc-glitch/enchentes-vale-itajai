# Rodada incremental — prompt-picos v3.7

**Data/hora da coleta:** 2026-10-03 00:04–00:06 BRT (2026-10-03 03:04–03:06 UTC)

Esta é uma rodada incremental e parcial. O pacote anterior `cheias_itajai_fontes_2026-10-01.zip`, citado na conversa, não estava disponível entre os arquivos acessíveis nesta execução; portanto, não foi possível fazer comparação byte a byte nem reaproveitar seus originais.

## Resultado novo confirmado

### Item 4 — Boletim Hidrometeorológico de setembro de 2026

**Nada encontrado/publicado na página oficial até a coleta.** A página oficial foi obtida com HTTP 200 e salva integralmente como `fontes/boletim_hidrometeorologico.html`. A lista de 2026 termina em **07/07/2026 — Boletim Hidrometeorológico 07/2026**; não há ocorrência de `08/2026` nem `09/2026` no HTML coletado.

URL: https://www.aguas.sc.gov.br/instrumentos/ferramentas-de-gestao/monitoramento-instrumentos/boletim-hidrometeorologico

### Item 15 — Tábua de marés de 2027, Porto de Itajaí

**Original não obtido.** A URL oficial consultada respondeu HTTP 403 e apresentou desafio Cloudflare (`cf-mitigated: challenge`). O HTML devolvido e os cabeçalhos foram preservados em `fontes/chm_tabuas.html` e `fontes/chm_headers.txt`. Por causa do bloqueio, esta rodada não confirma publicação nem ausência da edição 2027 a partir da página original.

URL: https://www.marinha.mil.br/chm/dados-do-segnav-publicacoes/tabuas-das-mares

## Demais itens 1–3, 5–14 e 16

Nada novo validado nesta rodada incremental. Nenhum número sem arquivo original foi incluído.

## Integridade

O arquivo `MANIFEST_SHA256.txt` registra o SHA-256 de cada arquivo entregue.
