# O SGB na "minha rua" — contexto do terreno, nunca cota (04/11/2026)

Decisão do Jefferson de 04/11/2026 (pendência 2 do relatório de ganhos da varredura, "aprovo todas"): a suscetibilidade a
inundação e a setorização de risco do **Serviço Geológico do Brasil (SGB/CPRM)** entram na busca "minha rua" como
**camada de contexto**.

## O que o SGB publica (geoportal, serviços `gestaoterritorial`)

| Serviço | O que é | Cidades da bacia | Ano |
|---|---|---|---|
| `inundacao/MapServer/0` | **Carta de suscetibilidade a inundação** — polígonos Alta / Média / Baixa, modelagem do IPT (2013) validada em campo | Apiúna, Benedito Novo, Blumenau, Botuverá, Brusque, Gaspar, Ilhota, Itajaí, Ituporanga, José Boiteux, Luiz Alves, Navegantes, Rodeio, Taió, Timbó, Vidal Ramos | 2013 (publicação 2016–2019) |
| `risco/MapServer/0` | **Setorização de risco geológico** — setores com grau (Alto, Muito alto, Médio), **tipologia** (Deslizamento, Inundação, Enxurrada, Rastejo, Queda, Erosão…) e data do levantamento | 24 cidades da bacia, de Taió a Navegantes; **Blumenau não aparece** neste serviço | 2012–2025 (Rio do Sul: set e nov/2025) |

Os GeoJSON são baixados pelo GitHub Actions (`.github/workflows/sondar-fontes.yml` → `scripts/baixar_sgb_suscetibilidade.py`,
branch `sondagem-fontes`), só GET, depois do `robots.txt` (o geoportal responde 404: nada proibido). Este ambiente e a VPS não
alcançam o geoportal. Tamanho: a carta de Gaspar tem 33 MB, a de Navegantes 32 MB — por isso o site **não** carrega os polígonos:
carrega o cruzamento já feito.

## O cruzamento (`scripts/cruzar_sgb_ruas.py` → `data/sgb-ruas.json`, 710 KB)

Para cada ponto de cota de rua **com coordenada** em `data/cotas-ruas.json` — hoje **Gaspar (1.615) e Brusque (348)**;
Blumenau e Rio do Sul não têm `lat`/`lon` —, o script diz:

- em que **classe de suscetibilidade** o ponto cai (polígono que o contém; na borda entre dois, a mais alta; fora de
  qualquer polígono, `null` = "fora da carta", nunca "sem risco");
- em que **setores de risco de água** ele está — só tipologias Inundação, Enxurrada, Enchente e Alagamento. Setor de
  deslizamento **não entra**: não é o assunto deste site, e chamá-lo de "risco de inundação" seria mentira.

Resultado de 04/11/2026 (GeoJSON lidos às 16h43 UTC):

| Cidade | Pontos | Alta | Média | Baixa | Fora da carta | Em setor de risco de água |
|---|---|---|---|---|---|---|
| Gaspar | 1.615 | 1.045 | 349 | — | 221 | 0 (o único setor de água de Gaspar não contém ponto cotado) |
| Brusque | 348 | 178 | 38 | 126 | 6 | 124 (36 setores de água de 199; os demais são de deslizamento) |

Exemplo que mostra por que as duas camadas aparecem separadas: a Rua Bartolomeu Pruner (Jardim Maluche, Brusque) cai em
suscetibilidade **Baixa** na carta de 2013 e dentro de um setor de risco **Alto** de inundação da setorização de 2019
(Avenida Beira Rio). As duas são verdadeiras; nenhuma é a cota de 7,65 m da Defesa Civil.

Para as outras cidades o arquivo guarda só o resumo (quantos polígonos por classe, quantos setores de água por grau), e a
tela diz que o cruzamento ponto a ponto não existe ali.

## Na tela (`CotasDeRua.tsx`, aba "Minha rua")

- Em cada resultado da busca, depois da cota e do abrigo, uma linha discreta: *"SGB: terreno com suscetibilidade Alta a
  inundação na carta do SGB (2013) · em setor de risco alto de inundação (SGB, 2019)"*. Sem metro, sem cor de faixa.
- Uma dobra fechada, "O que o Serviço Geológico do Brasil mapeou em {cidade} (contexto, não cota)", com o resumo da cidade
  e a ressalva: é classificação do **terreno**, com os critérios e a data do SGB; "Baixa" não quer dizer que não alaga,
  "Alta" não quer dizer que vai alagar hoje; não muda a cota, a contagem nem a cor; 199.
- O arquivo é carregado à parte (`dados/sgbRuas.ts`), só quando a busca abre e só em cidade que o SGB cobre.

## Regras

1. **Contexto, nunca cota, previsão ou cor.** Nada do SGB entra em `cotas-ruas.json`, nas faixas, no simulador, nos avisos
   nem no chat como número.
2. **Só setores de água.** O validador (`valida_sgb_ruas`) reprova setor com tipologia fora de Inundação/Enxurrada/
   Enchente/Alagamento.
3. **Todo ponto do arquivo é um ponto de `cotas-ruas.json`** (mesma cidade, mesma coordenada) — o validador cobra.
4. **Regerar** com `python3 scripts/cruzar_sgb_ruas.py --sgb <pasta do branch sondagem-fontes> --gravar` quando o SGB
   publicar carta nova ou quando `cotas-ruas.json` ganhar coordenadas (Blumenau e Rio do Sul entram sozinhas).
5. Testes: `scripts/teste_cruzar_sgb_ruas.py`, `teste_validar_dados.py` (`SgbRuasEContextoNaoCota`), `web/src/logica/sgbRuas.test.ts`.
