# Recorte da série do coletor — Blumenau, Itajaí e Ilhota, 30/08 a 03/10/2026

Feito para reproduzir `docs/ANALISE-CHEGADA-ITAJAI-2026.md` sem o servidor (auditoria do PR #449, item A2).

- **Origem:** `series-2026.tar.gz`, gerado na VPS em 03/10/2026 às 18h23 com
  `tar -czf /root/series-2026.tar.gz data/tempo-real/*.ndjson* data/eventos-registro`.
  Tem 20 MB e sha256 `19136bdb38ee7a1c2a409b42e20cbcc5d4727fe8131c7f9f40dbb0165a738ab5`.
- **O que entrou:** só as linhas que a análise lê, com os campos originais e sem alterar nenhum valor.
  - `AAAA-MM.ndjson.gz`: leituras de nível com `cidade == "itajai"` (DC-01 a DC-11) e as duas publicações de
    Blumenau ("Blumenau (AlertaBlu)" e "Blumenau", a da página de Itajaí, com carimbo 3 h atrasado). Campos:
    `estacao`, `rio`, `cidade`, `medido_em`, `nivel_m`.
  - `chuva-AAAA-MM.ndjson.gz`: chuva das estações de Itajaí, só `mm.h1`. A de outubro ficou vazia e foi
    omitida.
  - `nivel-sc-AAAA-MM.ndjson.gz`: só a DCSC-00030 (Ilhota).
- **Fuso:** `medido_em` sem fuso, em horário de Brasília, como o coletor grava.
- **Conferido:** `scripts/analisar_chegada_itajai.py` e `scripts/estimar_zero_reguas_itajai.py` dão a MESMA
  saída, caractere por caractere, com este recorte e com o pacote inteiro. O teste
  `scripts/teste_analisar_chegada_itajai.py` (classe `TesteRecorteVersionado`) trava os números principais.
