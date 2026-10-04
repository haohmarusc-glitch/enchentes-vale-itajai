# Erratas do PR #449 (auditoria de 03/10/2026)

Registro só de texto. Não muda `data/`, `transito.json`, o site nem o Monitor.

O PR [#449](https://github.com/haohmarusc-glitch/enchentes-vale-itajai/pull/449) ("Cruza Blumenau, maré e chuva
na série de 2026 de Itajaí") foi mesclado em `cb4ea42`. Uma auditoria somente leitura (veredito **ajustar**, só
texto) apontou problemas na análise nova e na descrição do PR. Os números de tempo do site não estavam errados:
a faixa da JICA e o `data/transito.json` batem célula a célula com a Tabela 7.5.1 (Vol. III-A, p. A-80).

## A descrição do #449 não vale como registro do que entrou (item A1)

A descrição do PR e o título original ("Itajaí: as onze réguas na cidade, maré por régua e zero estimado")
prometiam, no item 1, as onze réguas na tela (`reguasAgora.ts`, `ReguasAgora.tsx`, `CartaoAgora`, `MedidorCotas`,
`Inicio`, `TelaCidade`, `TelaItajai`) e "676 testes". **Nada disso estava no diff do #449.** O diff tinha a
análise (`docs/ANALISE-CHEGADA-ITAJAI-2026.md`), dois scripts com testes, o gabarito de `picoBlumenau.test.ts`,
a nota de `data/historico-chegada-itajai.json` e o README.

- As onze réguas como cartões "Agora" entraram depois, no PR #450 (`eafa7da`).
- Para saber o que o #449 mudou, vale o commit `cb4ea42`, não a descrição do PR.

## Onde cada achado da auditoria foi corrigido

Os textos foram corrigidos no PR #453 (`ea04700`, "Corrige os achados das auditorias de 03/10…"). Conferido
em `main` (`36b2689`) em 04/10/2026:

| Item | Achado | Onde está corrigido |
|---|---|---|
| A1 | Descrição prometia código que não estava no diff | Esta nota. As onze réguas: #450. |
| A2 | Crista de 12/09 na DC-11 ("+1,5 h") não reproduzível; série não versionada | `data/brutos/serie-2026-itajai/` (recorte versionado, com `LEIAME.md`). Tabela 2 do doc: 12/09 DC-11 = "+0,5 h, horário indeterminado por lacuna"; valor mais confiável = Ilhota +3,5 h. |
| M1 | "~70 km" sem fonte; "33 km da foz" | Doc, aviso antes da tabela 2: "não tem fonte nem método"; 33,2 km são "até o ponto de Itajaí", ~2 km acima da foz. |
| M2 | "1 a 1,5 m/s" sem fonte | Removido; fica só a referência da JICA. |
| M3 | 14–17 h atribuídos à "cheia grande" | Doc, seção 2, item 3: o intervalo encurta quando a cheia cresce (17 h em 5 anos, 12 h em 50 anos). |
| M4 | "Blumenau já caiu 0,3 a 1 m" | Doc: ~1,6 a 2,4 m em 12/09. |
| M5 | `historico-chegada-itajai.json`: "maré domina a DC-02" | Nota reescrita: a DC-02 quase não sente a maré (fator 0,07). |
| M6 | Pares Blumenau × Itajaí de 2011 e 2023 não citados | Doc, seção 4: entram como **candidatos não conferidos** (19 h em 2011; 7 h 10 min e 26 h 50 min em 2023), sem recalibrar nada. |
| B1 | Referência do atraso inconsistente | Doc e README: contado do **meio do platô**, com a coluna "meio" na tabela 2. |
| B2 | "Preamar de 1,2 m move a régua ~1,1 m" | Doc: "amplitude, não altura sobre o nível médio". |
| B3 | "terreno típico" era o p25 | Doc: p25 e mediana ditos separadamente (0,6–1,5 m abaixo do p25; 1,3–3,9 m abaixo da mediana). |
| B4 | Regra de fuso do `CLAUDE.md` | `CLAUDE.md`, seção "Fuso dos carimbos de tempo real". |
| B5 | `publicacaoMaisRecente` podia escolher a publicação atrasada | `PUBLICACAO_ATRASADA` em `web/src/logica/picoBlumenau.ts`, com teste. |
| B6 | "1,5 a 5 h" omitia Ilhota (+6,0 h em 22/09) | Tabela 2 do doc tem a coluna de Ilhota. |

## O que continua em aberto

- O cadastro `km_da_foz: 70` de Blumenau (`data/estacoes.json`) continua sem fonte e sem método. O doc diz isso,
  mas o campo em si não foi alterado (é dado, fora de um PR só de texto). **Não publicar** 70 km nem os ~81–83 km
  medidos pela auditoria no OSM.
- As horas de 2011 e 2023 (M6) seguem sem conferência de fuso e de estação.
- A faixa de chegada do site não muda por esta análise. Só muda com cinco eventos conferidos e decisão do Jefferson
  (regra de `calibrar_chegada_itajai.py`).
