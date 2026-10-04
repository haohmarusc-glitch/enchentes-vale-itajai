# Auditoria das cotas de rua de Rio do Sul (04/10/2026)

**Decisão que pediu esta auditoria (Jefferson, 04/10/2026):** *"As 555 cotas podem voltar a receber cor
depois de conferir amostra, fonte e referência da camada atual. Até essa revisão, manter false; não liberar
cor somente porque os registros existem."*

**O que este documento é:** a auditoria, não a liberação. `cotas_verificado` de Rio do Sul **continua
`false`**. Nenhuma cota e nenhuma estação mudou.

**Conclusão: (b) não está pronta, mas falta pouco.** Fonte e amostra passam: 30 de 30 na amostra e 554 de 555
no censo, contra um bruto com hash. A referência está declarada pela própria fonte, e há uma linha errada no
cadastro. Faltam duas coisas do lado do projeto e uma pergunta à COMPDEC (detalhes na seção 7).

Reproduzir: `python3 scripts/auditar_cotas_rio_do_sul.py` (só lê; sai com código 2 enquanto a divergência
da seção 5 existir). Testes: `python3 scripts/teste_auditar_cotas_rio_do_sul.py` (20).

---

## 1. O que `cotas_verificado` trava hoje em Rio do Sul

Isto foi lido no código antes de auditar, porque muda o tamanho da decisão.

| Onde | Usa `cotas_verificado`? | Efeito em Rio do Sul hoje |
|---|---|---|
| Mapa (`web/src/logica/cotasNoMapa.ts`, `pontosDeRua`) | sim, trava nº 1 | **nenhum**: as 555 não têm coordenada (`RUAS_SEM_COORDENADA`), então não há ponto para desenhar com `true` nem com `false`. |
| Faixa do bot no `/nivel` e no pino (`scripts/bot.py`, `faixa_da_leitura`) | sim | a cidade **cala** a faixa ("Acima da cota de Atenção"). |
| Aba "Minha rua" do site (`CotasDeRua.tsx`) | **não** | já compara cada rua com o nível de agora ("faltam X de subida" / "este nível já foi alcançado"), porque a cota está em `referencia: "régua"`. As duas abaixo do piso ficam fora (`usar_para_aviso: false`). |
| `/rua` do bot (`resposta_rua`) | **não** | também já compara, pelo mesmo motivo. |

**Consequência.** Pôr `true` hoje não acende cor de rua em lugar nenhum. O que muda é a **faixa da cidade no
bot**, e aí entra a pendência das quatro escalas de faixa (`cotas_divergencia` em `estacoes.json`). Ao
contrário, manter `false` não impede que o texto da aba "Minha rua" e do `/rua` compare as ruas com o nível.
Isso já acontece desde 31/08. Se a intenção de "não liberar cor" inclui esse texto, é uma trava que ainda não
existe. Não mexi nisso, porque é decisão sua.

---

## 2. Método

- **Ambiente:** o proxy recusou `defesacivil.riodosul.sc.gov.br` e `public.asthon.com.br` (CONNECT 403,
  04/10/2026). **Nada foi reaberto na fonte daqui.** Tudo foi conferido contra arquivos já guardados no
  repositório, com hash.
- **Bruto de referência:** o pacote JavaScript do portal da Defesa Civil de Rio do Sul, versão
  `assets/index-DyPsDK0O.js`, guardado pela rodada 7 da pesquisa externa (relatório gerado em
  01/10/2026, commit `3d74e51` de 02/10/2026):
  `data/brutos/pesquisa-picos-2026-09-24/rodada7/originais/DCRioDoSul_portal_bundle_index-DyPsDK0O.js`,
  360.669 bytes, sha256 `b77ba54f5a13290ec2b334b0b837502734547ecb2ec579632c13f3a91658dd4d`. **Confere** com
  `Manifesto_SHA256.json`. Se não conferisse, o script pararia com código 3.
- **Segunda leitura:** a transcrição da NSC Total de 14/08/2026, `data/brutos/rio-do-sul-nsc-2026-08-14.json`,
  sha256 `78da3c56eeb60d1d229d36a711693544de4bfc7c9665fa6f9124f218575b0916`. É uma transcrição de jornal,
  passada a JSON, e não o HTML da matéria.
- **Camada auditada:** as 555 linhas `cidade: "rio-do-sul"` de `data/cotas-ruas.json` (sha256 do arquivo na
  auditoria: `af2a2772…54f6d`).
- **Censo:** as 555 linhas foram comparadas uma a uma com as 555 do pacote, pelo nome sem acento e em caixa
  alta, em cinco pontos:
  - a mínima, ao centavo;
  - a máxima, em que o teto "20,00+" vira nota e não `cota_max_m`;
  - `usar_para_aviso: false` se, e só se, a mínima estiver abaixo do piso da cidade (4,50 m);
  - `referencia: "régua"`;
  - bairro e coordenada.

  Também foram procuradas duplicatas e valores implausíveis.
- **Amostra:** 30 ruas sorteadas com `random.Random(20261004)` sobre a lista ordenada pelo nome normalizado,
  conferidas linha a linha contra o pacote e a NSC.

## 3. Fonte

| Pergunta | Resposta | Evidência |
|---|---|---|
| De onde vieram | "Cota de Cheias por Rua", da Defesa Civil de Rio do Sul. A tabela viaja dentro do pacote JS do portal. | `fonte` das 554 linhas; `scripts/importar_cotas_rio_do_sul.py` |
| Script importador | `scripts/importar_cotas_rio_do_sul.py` (commit `95e1833`), rodado na VPS em 31/08/2026 (commit `58952cb`, autor haohmarusc-glitch) | `git log` |
| URL e data | `index.php?r=soscota-rua%2Ftabela`, dado em `assets/index-Ds6Xl8sw.js`, `data_fonte: 2026-08-31` | campo `fonte` |
| Bruto da importação no repo? | **Não.** O `index-Ds6Xl8sw.js` de 31/08 não foi guardado. | busca no histórico inteiro (`git log --all`) |
| Há bruto equivalente com hash? | **Sim, posterior:** `index-DyPsDK0O.js` (~01/10/2026), com hash no manifesto. Tem as mesmas 555 ruas, e 554 batem ao centavo com o cadastro. Logo, a tabela não mudou entre as duas versões nessas 554. | seção 5 |
| 555ª rua (Visconde de Cairu) | Veio da NSC (`confianca: media`), não do portal | `conferir_rio_do_sul_nsc.py` |
| Data do levantamento das cotas | **Desconhecida.** O portal publica a tabela sem data, e a NSC também não traz. | — |
| Bairro, ponto, coordenada | **A fonte não publica.** O pacote só tem `name`, `min`, `max` e `maxOpen`. | pacote |

**Por que o importador perdeu uma rua.** No pacote oficial a Visconde de Cairu é
`{name:'VISCONDE DE CAIRU', min:null, max:19.01}`. O `RE_MIN` do importador só aceita número. O objeto com
`min:null` foi descartado como "não é rua", sem aviso. Foi esse descarte silencioso, e não uma falha de rede,
que deixou 554.

## 4. Referência

O que se pode afirmar, e de onde vem cada afirmação. Não presumi equivalência entre réguas em nenhum ponto.

1. **A fonte declara a régua das cotas de rua.** O pacote diz, na legenda da tabela: *"'20,00+' é como a
   tabela oficial marca interdição total acima de 20 m na régua. Cotas em metros na régua da Ponte Dom Tito
   Buss."* (lido no bruto com hash).
2. **O próprio portal compara as cotas de rua com a leitura de uma estação, sem deslocamento.** No pacote, a
   tela "Cotas de Cheia por Rua" classifica cada rua como `closed`, `flooding` ou `safe` comparando `min` e
   `max` com o nível `_`. O `_` é o `level_m` da estação marcada `is_reference` na lista
   `/city-site/stations` (`let Y=fi?.station_id … pe(Number(Mt[Y].level_m))`). O cabeçalho mostra esse mesmo
   número como *"m na Ponte Dom Tito Buss"*.
3. **O portal corrige a estação estadual para essa régua.** O pacote traz
   `zo=Object.freeze({"d2f60af1-53e3-497f-81d6-c6498d28f5a2":-.17})`, e `Vo`/`Uo` somam −0,17 m ao nível dessa
   estação e recalculam a faixa. No bruto Asthon de 31/08 (`rio-do-sul-asthon-2026-08-31.json`, sha256
   `9c907fcc…251a`), esse `station_id` é a **"SDC-SC Rio do Sul"** (dono DCSC), a ~50 m da Asthon
   Tito Buss. Isso bate com a medição de 09/09/2026 (Tito Buss DCSC 4,63 m × Tito Buss Asthon 4,46 m, +0,17;
   `docs/sessoes/2026-09-09-SESSAO.md` §4). Ou seja, o operador do portal trata a estação estadual como **outra
   régua** e a traz para a da Tito Buss, enquanto a estação de referência entra sem correção.
4. **A estação de referência é a que o site lê, mas isso não está num bruto com hash.**
   - Quem é `is_reference` (ou `reference_station_id`) só aparece em anotações: a da leitura de 03–04/09
     (`docs/cotas-municipais/riodosul.md`) e a da sessão de 09/09 na VPS. Nas duas é a
     `f6360951-219f-4859-935f-b2e2d13962f1`, Ponte Dom Tito Buss (Asthon). É a estação que
     `scripts/coleta_asthon.py` lê (`POR_ESTACAO`).
   - Nenhum dos brutos guardados traz `is_reference` nem `reference_station_id`: nem o de 31/08 nem a captura
     de 28/09 (`captura-fontes-2026-09-28/rio-do-sul-asthon-panel.json`).
   - **Esse elo é anotação, não bruto.**
5. **O que ninguém documentou:**
   - se o zero do sensor Asthon foi nivelado ao zero da régua física com que as cotas de rua foram
     levantadas;
   - quando as cotas foram levantadas.

   A fonte afirma a equivalência implicitamente (usa as duas juntas na mesma tela), mas não há documento de
   nivelamento. **Não conferido daqui; só a COMPDEC responde.**
6. **Ponto de controle de 31/08 (um instante só).** SDC-SC 3,76 m às 12:21:58Z × Asthon Tito Buss 3,668 m às
   12:24:31Z, diferença +0,09 m. Não é +0,17. É um par só, com 2,5 min de distância, e serve de registro, não
   de prova. A correção de −0,17 é do operador do portal, não minha.

**Faixas da cidade (não são cotas de rua, mas viajam no mesmo campo).** O pacote usa `en={attention:4.5,
alert:5.5, emergency:6.5}` como padrão. A captura de 28/09 (hash no manifesto da captura) traz, para a Tito
Buss, `band_thresholds` 4,50/5,50/6,50 com `origin: "authored"`, ao lado dos campos antigos
`observation_level: 5.5` e `attention_level: 6.5`. As quatro escalas de `cotas_divergencia` continuam sem
confirmação da COMPDEC (`docs/PROPOSTAS-AUDITORIA-2026-10-03.md`, fim).

## 5. Censo (555 × 555)

| Item | Resultado |
|---|---|
| Linhas | cadastro 555 · pacote 555 |
| Só no cadastro / só no pacote | 0 / 0 |
| Duplicatas (nome sem acento, caixa alta) | cadastro 0 · pacote 0 |
| Conferem campo a campo | **554** |
| Divergem | **1, a Visconde de Cairu** |
| Teto "20,00+" no pacote | 216, todos com a nota de teto e sem `cota_max_m` no cadastro |
| Abaixo do piso da cidade (4,50 m) | 2: POUSO REDONDO 3,11 e SD 1604 3,26, os dois com `usar_para_aviso: false` (já conhecidos) |
| Mínima fora de 0–25 m, ou máxima abaixo da mínima | 0 |
| Com bairro / com coordenada | 0 / 0, porque a fonte não publica |

**A divergência.** O cadastro tem a VISCONDE DE CAIRU com `cota_m: 19,01` (fonte NSC, `media`). O pacote
oficial traz `min: null, max: 19,01`. A NSC publicou como **mínima** o número que a tabela oficial dá como
**máxima**. A rua não tem cota de início de alagamento publicada. O efeito prático é pequeno (19 m ficam
acima de todo pico conhecido, 13,58 m em 1983), mas o número está no campo errado. Proposta, **para você
decidir:**
- `cota_m: null` e `cota_max_m: 19,01`;
- `fonte` apontando para o pacote com hash;
- `confianca: alta`.

A correção deve sair de script (o importador com `min:null` aceito), e não à mão.

**Fora do município.** Não dá para testar: sem bairro e sem coordenada, não há como localizar a rua. Há nomes
iguais a cidades de SC (GASPAR, VIDEIRA, PIRATUBA, PORTO UNIAO, VIDAL RAMOS…), mas é costume local dar a ruas
nomes de municípios, e a tabela é do portal municipal. Não tratei isso como erro. **Não conferido.**

## 6. Amostra (semente 20261004, 30 ruas)

| # | Rua | Cadastro mín/máx | Pacote mín/máx | NSC mín | Bairro | Coord. | Resultado |
|---|---|---|---|---|---|---|---|
| 1 | FERNANDINO JAHN | 10,68 / — | 10,68 / 20,00+ | 10,68 | — | não | confere |
| 2 | ANTONIO JOSE POLEZA | 12,26 / — | 12,26 / 20,00+ | 12,26 | — | não | confere |
| 3 | LUIZ STEDILE | 8,89 / 10,79 | 8,89 / 10,79 | 8,89 | — | não | confere |
| 4 | RIO PRETO | 9,95 / 12,01 | 9,95 / 12,01 | 9,95 | — | não | confere |
| 5 | JULIO NAU | 9,00 / 12,26 | 9,00 / 12,26 | 9,00 | — | não | confere |
| 6 | VIDEIRA | 8,43 / 9,11 | 8,43 / 9,11 | 8,43 | — | não | confere |
| 7 | GENERAL OSORIO | 9,23 / 10,47 | 9,23 / 10,47 | 9,23 | — | não | confere |
| 8 | DO ACRE | 9,78 / — | 9,78 / 20,00+ | 9,78 | — | não | confere |
| 9 | SD 712 | 7,62 / 9,99 | 7,62 / 9,99 | 7,62 | — | não | confere |
| 10 | ELISEU GONCALO DO NASCIMENTO | 10,11 / — | 10,11 / 20,00+ | 10,11 | — | não | confere |
| 11 | PASTOR GERHOLD HOBUS | 11,78 / — | 11,78 / 20,00+ | 11,78 | — | não | confere |
| 12 | GUINO RIETER | 7,30 / 7,50 | 7,30 / 7,50 | 7,30 | — | não | confere |
| 13 | HEITOR LUZ | 11,80 / 14,32 | 11,80 / 14,32 | 11,80 | — | não | confere |
| 14 | BULCAO VIANA | 8,16 / 10,10 | 8,16 / 10,10 | 8,16 | — | não | confere |
| 15 | JOAO HOFFMANN | 8,50 / 19,01 | 8,50 / 19,01 | 8,50 | — | não | confere |
| 16 | FRAIBURGO | 9,21 / 10,76 | 9,21 / 10,76 | 9,21 | — | não | confere |
| 17 | JOSE CONINCK | 12,80 / 17,80 | 12,80 / 17,80 | 12,80 | — | não | confere |
| 18 | RODOLFO ODEBRECHT | 19,11 / — | 19,11 / 20,00+ | 19,11 | — | não | confere |
| 19 | JOHANN KEPLER | 8,92 / 10,00 | 8,92 / 10,00 | 8,92 | — | não | confere |
| 20 | GASPAR | 11,00 / 17,05 | 11,00 / 17,05 | 11,00 | — | não | confere |
| 21 | ENGENHEIRO BAUNGARTEN | 9,11 / 10,57 | 9,11 / 10,57 | 9,11 | — | não | confere |
| 22 | JOAO FRONZA | 8,13 / — | 8,13 / 20,00+ | 8,13 | — | não | confere |
| 23 | B - LOT LUIZ BIANCHET | 17,50 / — | 17,50 / 20,00+ | 17,50 | — | não | confere |
| 24 | ELVIRA GEORG FRIEDEL | 10,28 / 14,30 | 10,28 / 14,30 | 10,28 | — | não | confere |
| 25 | SD 1001 | 8,34 / 9,01 | 8,34 / 9,01 | 8,34 | — | não | confere |
| 26 | SD 1025 | 14,11 / 17,11 | 14,11 / 17,11 | 14,11 | — | não | confere |
| 27 | HERMANN BREHMER | 12,26 / — | 12,26 / 20,00+ | 12,26 | — | não | confere |
| 28 | PEDRO LUCAS | 10,01 / 11,01 | 10,01 / 11,01 | 10,01 | — | não | confere |
| 29 | ARI LEDRA | 19,36 / — | 19,36 / 20,00+ | 19,36 | — | não | confere |
| 30 | INTENDENTE GUSTAVO BRANDES | 10,23 / 17,78 | 10,23 / 17,78 | 10,23 | — | não | confere |

**30 de 30 conferem**, nas três leituras (cadastro, pacote e NSC). "—" na máxima do cadastro é o teto
"20,00+" do pacote, guardado como nota. Bairro e coordenada estão vazios nos dois lados, porque a fonte não
publica.

## 7. Conclusão: (b) não pronta

| Critério do Jefferson | Estado |
|---|---|
| Amostra | **passa**: 30/30, e o censo dá 554/555 |
| Fonte | **passa com ressalva**: a camada se reproduz contra um bruto com hash (versão de ~01/10). O bruto da importação de 31/08 não foi guardado. A data do levantamento é desconhecida. |
| Referência | **declarada pela fonte**: "régua da Ponte Dom Tito Buss", e o portal compara as ruas com a sua estação de referência sem deslocamento. O elo "estação de referência = `f6360951`, a que o site lê" está só em anotação de 03/09 e 09/09, sem bruto com hash. O nivelamento sensor × régua física não está documentado. |

### O que falta, e de quem

1. **Você (decisão de dado):** a Visconde de Cairu (seção 5). Enquanto ela estiver como está, a camada tem uma
   linha que a fonte oficial não sustenta. Correção por script, nunca à mão.
2. **Projeto, pela captura do GitHub Actions:** guardar com sha256 duas coisas.
   - O corpo de `https://public.asthon.com.br/public/cities/4214805` ou de
     `…/public/city-site/stations?city_id=4214805`, que mostra `reference_station_id` / `is_reference`.
   - A página do portal com o pacote do dia.

   Isso fecha, com bruto, o elo "a régua das cotas é a estação que lemos". O portal
   (`https://defesacivil.riodosul.sc.gov.br/`) já está em `fontes_tempo_real`. Os dois endpoints da Asthon
   não estão, e incluí-los na lista de alvos de `scripts/capturar_fontes.py` é decisão sua ("nada entra por
   palpite").
3. **COMPDEC de Rio do Sul (ofício):** três perguntas, que podem ir no ofício já pendente das quatro escalas:
   - (a) a "régua da Ponte Dom Tito Buss" das cotas de rua é a leitura do sensor Asthon que o portal mostra,
     com o mesmo zero?
   - (b) quando a tabela "Cota de Cheias por Rua" foi levantada ou revisada?
   - (c) qual escala de faixa vale hoje?

   A pergunta (c) não trava as cotas de rua, mas trava a faixa do bot, que vira junto com a mesma chave
   (seção 1).

Os itens 1 e 2 bastam para os três critérios da sua decisão. O item 3 é o que a regra do projeto pediria
para ir além de "a fonte declara".

### O que exatamente mudar, quando estiver pronta

- `data/estacoes.json`, cidade `rio-do-sul`:
  - `cotas_verificado: true`;
  - um `cotas_verificado_nota` novo (mesmo formato do das DC-10 e DC-11 de Itajaí) com a data, este
    documento, os sha256 do pacote e da captura do `reference_station_id`, e "30/30 · 555/555".
- `scripts/teste_bot.py::test_rio_do_sul_nao_ganha_faixa_a_cota_e_de_outra_regua` precisa ser reescrito.
  - Ele usa o título "Rio do Sul Estação MKS" e conta com o `false`.
  - `faixa_da_leitura` não confere o título da estação, então com `true` uma leitura da MKS ganharia faixa.
  - O teste novo deve usar o título da Tito Buss (Asthon) e travar que a MKS continua fora da coleta.
- Comentários desatualizados:
  - `web/src/logica/cotasNoMapa.ts` (linhas 14–15);
  - a docstring de `faixa_da_leitura` em `scripts/bot.py`;
  - os dois itens do README.
- **Antes de virar:** decidir se `cotas_verificado` deve liberar faixa do bot e cotas de rua de uma vez (hoje
  é uma chave só), e se a aba "Minha rua" e o `/rua` devem respeitar o `false` (seção 1).

## 8. O que não foi feito

- Nenhuma fonte foi reaberta na web (hosts bloqueados). Tudo o que depende do portal ao vivo ou da COMPDEC
  está marcado **não conferido daqui**.
- `cotas_verificado`, `cotas-ruas.json` e `estacoes.json` **não foram alterados**. O teste
  `TestArquivosReais.test_nao_grava_nada` trava que o script só lê.
