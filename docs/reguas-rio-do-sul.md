# Rio do Sul mede os três rios — uma régua em cada

Levantado em 03/09/2026 no portal da Defesa Civil de Rio do Sul e na API Asthon. Encaixa na topologia em
árvore de `docs/TOPOLOGIA-CANONICA.md`: as duas cabeceiras (Itajaí do Oeste e Itajaí do Sul) se juntam em
Rio do Sul e formam o Itajaí-Açu.

## Coleta em arquivo próprio (decisão do Jefferson, 10/10/2026)

`scripts/coleta_riodosul_rios.py --publicar`, chamado pelo `publicar_tempo_real.sh` a cada publicação, faz uma
consulta ao painel da Asthon e guarda, por lista fechada de `station_id` e com o rio conferido:

| régua | rio | `station_id` |
|---|---|---|
| Ponte Ricardo Kanitz | Itajaí do Sul | `30475400-b7ba-4551-9646-19df0c3bfa38` |
| Ponte Hannelore Hartmann Eyng | Itajaí do Sul | `039a5d4f-f58d-4fca-bef6-5d37e132a6f0` |
| **Ponte BR 470** | Itajaí do **Oeste** | `3167e629-3bbe-48f2-9244-c65dfe6882d8` — **está na API desde, pelo menos, 10/10/2026** |
| Ponte Dom Tito Buss (saída, já no site) | Itajaí-Açu | `f6360951-219f-4859-935f-b2e2d13962f1` |

- `data/tempo-real/ultimo_rio_do_sul_rios.json`: a última leitura de cada uma, com a idade e as cotas como a
  Asthon publica (`band_thresholds`: 4,50 / 5,50 / 6,50 m, `authored`, nas três do centro e na BR 470). **Arquivo
  próprio, nunca em `leituras`:** não pinta, não avisa e não está no cadastro. Mostrar na tela é outra decisão.
- `data/tempo-real/rio-do-sul-rios-AAAA-MM.ndjson`: a série, sem repetir leitura, para a calibração das duas
  cabeceiras. Vai para o `arquivo-series` na cópia semanal.

Primeira leitura (10/10/2026, ~07:28 em Brasília): Kanitz 5,00 m, Hannelore 4,85 m, BR 470 4,39 m, Tito Buss
4,55 m — cada uma na régua dela.

## As réguas

| Régua | Rio | Ramo | Situação da verificação |
|---|---|---|---|
| **Ponte Dom Tito Buss** | Itajaí-**Açu** | `tronco_acu` | ✅ confirmada em `stations_list` da API (`river_name: Rio Itajaí-Açu`) |
| **Ponte Ricardo Kanitz** | Itajaí do **Sul** | `itajai_do_sul` | ✅ confirmada (`river_name: Rio Itajaí do Sul`) |
| *Ponte Hannelore Hartmann Eyng* | Itajaí do **Sul** | `itajai_do_sul` | ✅ na API, **não** estava no levantamento do portal — é uma quarta régua |
| **Ponte BR 470** | Itajaí do **Oeste** | `itajai_do_oeste` | 🟡 vista no portal, **ausente** na captura da API de 01/09 — confirmar |

Cotas exibidas no portal para as três do centro: atenção **4,50** · alerta **5,50** · emergência **6,50**
· fim de escala 8,00 m.

> ⚠️ Essas cotas **não foram gravadas** em `data/estacoes.json`: vieram de leitura de portal, e a captura
> de API que existe no repo não traz `band_thresholds` para as réguas de rio (só para as barragens, em
> escala de reservatório). Ver a nota de verificação em `docs/API-ASTHON-COMPLETA.md`.

## Por que isto é o melhor ponto de calibração da bacia

A regra que a topologia impôs — *"pico em Rio do Sul = Oeste + Sul"* — era hipótese. Com régua nos três,
**as duas entradas e a saída são medidas na mesma cidade**, com minutos de diferença: dá para medir a
contribuição de cada cabeceira sem correlacionar cidades distantes.

Há um peso conhecido para confrontar: a área de drenagem (GraphQL da Defesa Civil de SC, ver
`docs/API-DCSC-CAMPOS-NOVOS.md`) é **Itajaí do Sul 1.164 km²** contra **Itajaí do Oeste 851 km²** — 58% ×
42%. Divergência grande entre o medido e essa proporção é informação nova (uso do solo, chuva desigual) —
ou operação de barragem: a **Barragem Sul** está no Itajaí do Sul e a **Barragem Oeste** no Itajaí do
Oeste, então a proporção medida depende também de como cada uma opera, não só da chuva.

## As cotas são de cada RÉGUA, não da cidade

Confirmado pelo usuário (morador da região) e coerente com a API: as três réguas do centro compartilharem
4,50/5,50/6,50 **não** é a cidade impondo escala única — é que os zeros foram cravados de modo que o mesmo
número signifique o mesmo risco nos três pontos, que estão em altitude parecida no núcleo urbano.

**Comparável** entre as três: a **faixa** e a distância até a próxima cota — quem está mais perto de
transbordar. **Não comparável:** o metro como volume ou altura absoluta; e nunca com réguas de outras
cidades.

## Correção registrada: nível alto no afluente não é erro de datum

Um levantamento anterior tratou "Itajaí do Oeste 5,48 m > Itajaí-Açu 5,25 m" como fisicamente estranho e
indício de datum errado. **Não é.** O canal do Açu, depois de receber os dois afluentes, é mais largo e
mais baixo: o mesmo volume produz **menos altura**. Nível é profundidade sobre o leito local, não medida
de volume — um afluente estreito pode marcar mais que o tronco largo, com os dois corretos.

A regra do datum continua valendo **entre cidades**; não se aplicava a esse caso.

## Perguntas para a Defesa Civil de Rio do Sul
1. ~~As cotas são da cidade ou de cada régua?~~ **De cada régua.**
2. Existe o **offset entre os zeros** das réguas (ou a cota altimétrica de cada uma)?
3. Qual delas é a régua **oficial** citada nos boletins e no acionamento de abrigos (7,00 m)?
4. A obra de melhorias fluviais (rebaixamento do leito + comporta, em licitação) muda **qual** delas?

## Pendências que isto abre
- Capturar o `panel` da Asthon na VPS e conferir se as réguas de rio trazem `band_thresholds` (comando em
  `docs/API-ASTHON-COMPLETA.md`). É o que fecharia a cota de Vidal Ramos e, talvez, das três de Rio do Sul.
- ~~Confirmar a "Ponte BR 470" (Oeste)~~ — **está no painel da Asthon (10/10/2026)**, com rio e cotas.
- ~~Coletar as réguas confirmadas~~ — **coletadas desde 10/10/2026**, em arquivo próprio (seção acima).
- Calibrar a contribuição de cada cabeceira quando a série tiver uma cheia (`rio-do-sul-rios-*.ndjson`).
