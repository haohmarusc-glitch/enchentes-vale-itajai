# HidroWeb: o que os CSV responderam, e o que NÃO responderam — 06/09/2026

Jefferson conseguiu acesso ao HidroWeb (ANA/SNIRH v3.3) pelo Chrome do PC — o proxy deste ambiente
bloqueia o domínio, o navegador dele não — e baixou as séries de **83800002 (Blumenau)** e
**83300200 (Rio do Sul)**. Abaixo, o que **eu li nos arquivos**, não o que se esperava deles.

---

## ✅ O que ficou confirmado

**Os três códigos ANA existem e são fluviométricas** (pergunta 2 do ofício C6, respondida sem esperar):

| código | nome oficial na ANA | como foi conferido |
|---|---|---|
| **83800002** | BLUMENAU (PCD) | arquivo lido: 2.654 linhas-mês, **1939 a 2026** |
| **83300200** | RIO DO SUL - NOVO | arquivo lido: **1978 a 2026, sem lacuna de ano** |
| 83050000 | TAIÓ | consulta ao portal (arquivo não veio) |

Gravado em `estacoes.json` como `codigo_ana_verificado`, `codigo_ana_nome` e `codigo_ana_verificacao`.

**As datas de `enchentes.json` estão certas.** O máximo mensal de Blumenau cai exatamente em
**09/07/1983** e **07/08/1984** — os dias que o cadastro registra.

**O "NOVO" de "RIO DO SUL - NOVO" não é quebra de série no nosso período.** A estação cobre 1978–2026
sem nenhum ano faltando; a substituição que o nome sugere é anterior a 1978.

---

## ⛔ O teste da REGRA_REFERENCIA_BLUMENAU **não pôde ser executado**

O teste previsto era: se o HidroWeb marcar 15,34/15,46 → datum IBGE; se 15,14/15,26 → régua.
**Ele pressupõe que o arquivo dê o PICO. Não dá.**

**Para 1983 e 1984 o HidroWeb só tem MÉDIA DIÁRIA** (`MediaDiaria = 1`). Leitura instantânea
(`MediaDiaria = 0`) só começa em **1989** — conferido ano a ano. O que o arquivo traz:

| data | HidroWeb (média diária, consistido) | `enchentes.json` (pico) | diferença |
|---|---|---|---|
| 09/07/1983 | **15,19 m** | 15,34 m | 0,15 m |
| 07/08/1984 | **14,85 m** | 15,46 m | 0,61 m |

**Comparar média do dia com pico instantâneo é comparar grandezas diferentes** — o mesmo erro de
natureza que o projeto recusa em outros lugares. O pico é sempre ≥ a média, então as diferenças são
esperadas em sinal; o que não dá para dizer é se sobra ou falta datum no meio.

**A regra continua valendo.** E agora por um motivo MEDIDO, não por falta de tentativa.

---

## ⚠️ Um achado que precisa de explicação antes de qualquer conversão

Em **setembro de 2011** — o evento que originou a regra, com CEOPS dizendo 13,00 m e a Defesa Civil
12,80 m — o arquivo de Blumenau traz três séries que **não fecham entre si**:

| série | pico no mês |
|---|---|
| consistido, média diária | **8,85 m** (dia 8) — e o dia 9 aparece como 8,47 |
| bruto, instantâneo 07:00 | **12,48 m** (dia 9) |
| bruto, instantâneo 17:00 | 10,40 m (dia 8) |

A série **consistida não captura a cheia**: ela dá 8,47 m no dia 9, enquanto o bruto do mesmo dia às
07:00 marca 12,48 m. E **nenhum dos três** é 12,80 ou 13,00.

**Conclusão prudente:** a série consistida do HidroWeb para Blumenau **não é** a mesma série que o
projeto usa, e não serve como árbitro do datum enquanto essa divergência não for explicada. Converter
com base nela seria trocar uma incerteza conhecida por outra desconhecida.

Para comparação, Rio do Sul no mesmo evento: **12,32 m** (consistido) e 12,39 (bruto), ambos no dia 9 —
ali as duas séries concordam. O problema é específico de Blumenau.

---

## O que ainda falta buscar, em ordem de valor

1. ~~**⭐ O INVENTÁRIO da estação 83800002.**~~ **FEITO em 06/09/2026, e o item estava errado.**
   O inventário público foi baixado (`Inventario31_08_2026.mdb`) e **não traz a cota do zero da
   régua**: a tabela `fichareferencianivel` existe, com a coluna `cota`, e está **vazia**. Ele é só
   o catálogo de estações. A pergunta do datum **não** foi respondida por aí — segue pela API ou
   pelos picos instantâneos pós-1989.
   O que ele resolveu: a lacuna de **coordenada** do ofício C6 (as três estações caem sobre o
   traçado, medido), o **tipo** de cada estação — que virou trava no validador —, e a dúvida
   Salseiro × Vidal Ramos. Tudo em `docs/INVENTARIO-ANA.md`.
   ⚠️ E acrescentou um alerta: a escala da 83800002 **encerrou em 12/2021**; para o presente a
   estação é a **83800003**.
2. **A série instantânea consistida de um evento pós-1989** em que o projeto também tenha valor — aí o
   teste original passa a ser executável, com grandezas iguais dos dois lados.
3. **Por que a série consistida de Blumenau não captura set/2011.** Pode ser correção deliberada da
   consistência, pode ser lacuna. Muda o quanto se pode confiar nela.
4. **A estação da foz de Itajaí**, se existir: buscar por MUNICÍPIO em vez de por código. ⚠️ No teste de
   Jefferson o campo Código não limpou ao trocar para Município — limpar o formulário antes.
5. `/hidroweb/acesso-api` — pode adiantar o pedido de API do ofício C6 sem esperar e-mail.

## O que NÃO fazer

- **Não converter a série de Blumenau** com base nestes arquivos. O teste não foi executado.
- **Não usar a média diária como pico** em lugar nenhum.
- **Não tratar a série consistida do HidroWeb como verdade** para Blumenau enquanto set/2011 não fechar.
