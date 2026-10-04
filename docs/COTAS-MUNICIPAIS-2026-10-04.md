# Cotas municipais — estado em 04/10/2026

Este documento junta três fontes:
- o handoff de pesquisa de 03/10/2026 ("cotas municipais do Vale do Itajaí");
- a rodada 6 da varredura (`docs/VARREDURA-2026-10-03-RODADA6.md`);
- a varredura de 04/10 (`docs/VARREDURA-2026-10-04.md`).

**Nada mudou em `estacoes.json`, no coletor ou no site.** Nenhuma faixa foi habilitada, nenhum `verificado`
virou `true` e nenhum deslocamento foi estimado.

## As cinco etapas, separadas

Achar uma tabela não fecha as outras etapas. Uma cidade só está **resolvida** quando tem as quatro primeiras
com evidência, e a quinta é conferida à parte.

1. **Tabela localizada:** existe um documento oficial com as faixas.
2. **Régua identificada:** o documento diz em que régua ou estação a tabela é lida.
3. **Equivalência comprovada:** essa régua é a mesma da leitura do site, ou há relação técnica documentada.
4. **Vigência conferida:** versão, data e validade declarada do documento.
5. **Leitura operacional:** a estação do site publica valor válido e recente.

Legenda: ✅ comprovado · 🟡 indício, candidato ou parcial · ❌ não há · — não se aplica.

| Cidade | 1 Tabela | 2 Régua | 3 Equivalência | 4 Vigência | 5 Leitura | Estado |
|---|---|---|---|---|---|---|
| Ibirama | ✅ PLAMCON 2024, p. 11 | ✅ estação da DCSC na ponte Beltramini (nota 1) | 🟡 o PLAMCON não escreve "DCSC-00020"; boletim × DCSC-00020 dá 4,04 × 4,04 m em 11/09 | ❌ validade até 07/08/2025 (p. 32); PLAMCON 2025 sem texto; boletim de 11/09 contradiz | ✅ DCSC-00020 viva | **pendente**; tabela de 2024 só histórica (decisão de 04/10); C26 enviado em 04/10 |
| Botuverá | 🟡 PLANCON 2026, seção 4.1 (não conferido daqui) | ❌ a tabela não nomeia régua | ❌ | 🟡 publicado em 15/09/2026; validade não conferida | 🟡 DCSC-00018 viva; DCSC-00027 sem leitura na coleta de 03/10 | **pendente**; complemento ao C17 enviado em 04/10 |
| Ilhota | ✅ PLANCON 2025/2028, p. 16 | 🟡 "régua instalada junto a ponte" (p. 15); a estação da ponte Cadorin só aparece na p. 21 | ❌ | 🟡 2025–2028 pelo título | ✅ DCSC-00030 viva | **pendente**; C11 atualizado enviado em 04/10 |
| Rio dos Cedros | ✅ Plano v10.9 (abr/2026), p. 9 | 🟡 "proximidade da régua de medição" ao Paço (p. 4); a tabela não nomeia | ❌ com a DCSC-00011 | ✅ abr/2026 | ✅ DCSC-00011 viva | **pendente**: falta a equivalência; C29 enviado em 04/10 |
| Timbó | 🟡 escala de imprensa e de post da prefeitura (2/3/4,29/4,30) | 🟡 "régua do Rio Benedito, Rua Equador" (2022) | 🟡 três pares entre o número divulgado e a DCSC-00023 | ❌ dez/2025 chamou 4,34 m de "atenção" | ✅ DCSC-00023 viva | **pendente**: não ligar ainda (decisão de 04/10); aparece como leitura estadual; C27 enviado em 04/10 a defesacivil@timbo.sc.gov.br |
| Indaial | ✅ faixa municipal 3/4/5,5 (prefeitura, 2023) | ✅ régua física nos fundos da Celesc | ❌ a prefeitura escreveu em 2023 que a estadual "não deve ser usada como base"; três pares dão ~2,43–2,53 m | 🟡 | ❌ DCSC-00006 sem leitura plausível desde 26/09 08h14 | **pendente**; C19 atualizado enviado em 04/10 |
| Ituporanga | ✅ SDC: 1,4/1,9/2,6 m | ✅ ANA 83250000 | — não é a régua do site (DCSC-00039) | ✅ manual SDC 2024 | ❌ não há leitura da 83250000 no site | **pendente**; complemento ao C22 enviado em 04/10 |
| Guabiruba | ❌ | ❌ | ❌ | — | ✅ DCSC-00029 no zero local abaixo de 10 m (decisão de 04/10); afluente lateral do Mirim | **pendente**; C20 enviado em 04/10 pela Ouvidoria |
| Lontras | ❌ (só o limite do SDE: 7,09 m "Emergência") | ❌ | ❌ | — | ❌ valor inválido (21.474.836) | **pendente** (C16) |
| Vidal Ramos | ❌ (limites do SDE e da DC de Brusque) | ❌ | ❌ | — | ✅ DCSC-00024 viva | **pendente** (C15) |
| Trombudo Central | ❌ | ❌ (a régua municipal "só até 6,15 m") | ❌ | — | ✅ DCSC-00035 ligada em 04/10, só identidade | **pendente**; C28 enviado em 04/10 |
| Apiúna | ❌ | ❌ | ❌ | — | ❌ DCSC-00178 publica altitude | **pendente**; C30 reenviado à DC em 04/10 |

**Resolvido nesta etapa: nenhuma cidade.** Avançaram de etapa:
- Ibirama: régua identificada por escrito;
- Rio dos Cedros: vigência confirmada no plano de 2026;
- Botuverá: tabela localizada, candidata;
- Timbó: terceiro par.

## O que foi conferido em original e o que não foi
| Fonte | Conferido daqui? |
|---|---|
| Ibirama, Decreto 5.431/2024: p. 9, p. 11 (tabela e nota 1) e p. 32 ("Este plano tem validade até 07/08/2025") | ✅ em `data/brutos/varredura-pintar-2026-10-03/` |
| Ibirama, Decreto 5.824/2025 (homologa o PLAMCON 2025, uma página) | ✅ idem |
| Ilhota, PLANCON 2025/2028: p. 15, 16 e 21 | ✅ idem |
| Rio dos Cedros, Plano v10.9: p. 4 e 9 | ✅ idem |
| Botuverá, Decreto 3.651/2026 (PLANCON, seção 4.1) | ❌ host bloqueado daqui; transcrição do handoff |
| Guabiruba, Ouvidoria (ouvidoria@guabiruba.sc.gov.br, Atende.net) | ❌ host bloqueado; o telefone (47) 3308-3100 confere com `Guabiruba_telefones-uteis.html` da rodada 6 |
| Rio dos Cedros, notícia 235108 (13/03/2014) | ❌ não está nos originais; a 234732 (2011) está |
| Ituporanga, página "nível do rio" (02/10/2026 7h, "Centro", 2 m, "Alerta") | ❌ host bloqueado; a página é alvo do `capturar_fontes.py` e pode ser capturada pelo workflow |
| Ibirama, site da COMPDEC ("versão 2026 em breve") | ❌ host bloqueado |

## Regras que seguem valendo
- **Nomes municipais preservados.** A "Observação" de Ibirama e o "Alarme" de Rio dos Cedros não viram
  "atenção" nem "emergência" na tela: o nome vai em `cotas_nomes_na_fonte` (regra D6).
- **Operador no limite:** a tabela de Botuverá sobrepõe os pontos 3,0 e 4,0 m. Não escolher `>=` ou `>` por
  conta própria. Isso vai na pergunta do C17.
- Classificação estadual continua rotulada como estadual. Leitura vencida não classifica. Pico, cota de rua e
  faixa operacional ficam separados.

## Complementos de ofício (enviados em 04/10/2026 por decisão do Jefferson)
Estão em `docs/oficios-b1-c15-c22.md`, logo abaixo de cada ofício original:
- **C17 (Botuverá):** régua da tabela do PLANCON 2026 e os pontos exatos de 3,0 e 4,0 m.
- **C20 (Guabiruba):** o mesmo pedido, endereçado à COMPDEC pela Ouvidoria, com protocolo.
- **C22 (Ituporanga):** fonte e ponto da página "nível do rio" e as faixas desse ponto.

Já enviados em 04/10, que cobrem o que o handoff pede para Ilhota e Ibirama sem duplicar:
- o C11 atualizado (Ilhota);
- o C26 (Ibirama), que pergunta o vínculo com a DCSC-00020 e qual tabela vale.

Enviados pelo Jefferson em 04/10, registrados em `docs/oficios-prontos.md`:
- **C28 (Trombudo Central):** faixas da página da Defesa Civil e se a régua municipal é a da DCSC-00035;
- **C29 (Rio dos Cedros):** se a DCSC-00011 lê na régua do Paço e a data do pico de 8,96 m de 2014;
- **C30 (Apiúna):** reenvio à Defesa Civil: régua, faixas e o zero da estação de altitude.
