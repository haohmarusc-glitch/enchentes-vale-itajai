# O acervo de avisos e boletins da EPAGRI/CIRAM — o que custou caro descobrir

Garimpagem feita pelo Jefferson na VPS em 09/09/2026, atrás do **Aviso Hidrológico 03 de
19/11/2023** (leituras de Rio do Sul e Taió com hora e cm/h, item 2 da pendência A4 em
`docs/pendencias-navegador-e-oficios.md`). O aviso **não está em nenhuma via pública**;
o que sobrou foi conhecimento sobre o acervo, e é isso que este arquivo guarda para ninguém
repetir a busca.

> ## ✅ RESOLVIDO em 15/09/2026 — o aviso chegou por e-mail
>
> A EPAGRI respondeu ao ofício C12 em **15/09/2026 08:34 BRT** e mandou os três avisos de
> nov/2023 em anexo, mais cinco notas hidrometeorológicas. Transcrição, ressalva da fonte e
> confronto com a telemetria da ANA em **`docs/RESPOSTA-EPAGRI-C12-2026-09-15.md`**.
> Arquivos em `data/brutos/ciram-avisos-enchente/` e `data/brutos/ciram-notas-hidro/`.
>
> A garimpagem abaixo **continua válida** e a carta a confirma pelo lado deles: os PDFs
> ficam só temporariamente no portal e depois vão para servidor interno, e eles não
> compartilham os diretórios "por motivos de segurança". **Raspar o acervo está morto como
> estratégia; pedir por e-mail funciona** — e a Mariane deixou o canal aberto para pedidos
> futuros, sem ofício formal.
>
> ⚠️ E veio com uma ressalva que muda a leitura de **todo** aviso deste arquivo, os de
> 2021 e 2022 da tabela abaixo inclusive: o aviso é um **instantâneo do horário da coleta**,
> não o pico do dia. Comprovado em Taió/nov-2023 — maior valor nos avisos 10,18 m, pico real
> na série telemétrica **10,32 m**, nove horas antes. **Nível de aviso é piso, nunca pico.**

## Veredito sobre o Aviso 03 de nov/2023 — as vias públicas

Quatro vias, todas fechadas **com prova, não suposição**:

1. **Índice do portal** (`ciram.epagri.sc.gov.br`): publica só os **seis boletins mais
   recentes**. Nada de 2023.
2. **REST do WordPress**: os PDFs vivem em `ciram_arquivos/midia/hidro/`, **fora** do
   WordPress — a API não os enxerga. `midia/` não tem nada além de `hidro/`.
3. **Extrapolação do sufixo numérico**: o `<id>` no nome do arquivo é um contador global,
   com passo de 20 em 2026 e **irregular antes** — não dá para chutar o número de 2023.
4. **Internet Archive**: o diretório está coberto **só em 2020, 2021 e 2022**. 178 URLs no
   CDX, 84 avisos, **4 de enchente**. 2023 não existe no acervo.

**O Aviso 03 saiu por e-mail** — ofício C12 em `docs/oficios-prontos.md`, na mesma thread em
que a Equipe de Hidrologia respondeu ao C5 (Mariane Souza Melo de Liz, 09/09/2026).
Enviado em 11/09/2026, **respondido em 15/09/2026 com os três avisos em anexo**.

## Como o acervo funciona

- `ciram.epagri.sc.gov.br` responde à VPS **sem Cloudflare**; `marinha.mil.br` não (exige
  navegador — foi assim com a tábua de marés, que veio pelo Jefferson).
- Duas convenções de nome, no mesmo diretório `ciram_arquivos/midia/hidro/`:
  - `aviso_n<NN>_<ddmmaaaa><id>.pdf` — `NN` com zero à esquerda (ex.:
    `aviso_n03_191120236281.pdf`, que é o de 19/11/2023 e não está no acervo);
  - `Site-aviso_<tipo>_<n>_<ddmmaaaa><id>.pdf`.
- O `<id>` é contador global do portal, não do tipo de aviso: passo de 20 em 2026,
  irregular antes. **Não extrapolar.**
- No CDX do Wayback, `matchType=prefix` e `*` na URL são **mutuamente exclusivos** (o erro
  foi cometido duas vezes no mesmo dia: fica escrito).

## O que a garimpagem rendeu

| | quantos | o que são |
|---|---|---|
| Avisos de **enchente** | **4** | todos novos para o repo; o par de **22/01/2021** é o mais valioso: subida com hora e cm/h, dois dias antes da cheia de Brusque de 24/01/2021 (4,82 m, já em `enchentes.json`) |
| Avisos de **estiagem** | 80 | mesmo formato; linha de base e material para testar o parser antes de aplicá-lo nos quatro que importam |

⚠️ **Sobre o par de 22/01/2021 e o tempo de trânsito:** só vale como conferência de trânsito
se a estação lida no aviso estiver **a montante de Brusque no Itajaí-Mirim** (Salseiro,
Botuverá). Aviso do Açu ou de outra bacia não pareia com a cheia de Brusque. Ler a estação
antes de casar as datas.

## Onde os arquivos ficam

Os 70 MB (84 PDFs) ficam **na VPS**, como o KML das manchas de Ituporanga. O repositório
recebe:

- `data/brutos/ciram-avisos-enchente/` — os avisos de enchente (4 do raspão + **3 de
  nov/2023 que vieram por e-mail** em 15/09/2026);
- `data/brutos/ciram-notas-hidro/` — as **5 notas hidrometeorológicas** de nov/2023, também
  por e-mail, com o manifesto próprio `ciram-notas-hidro.sha256`;
- `data/brutos/ciram-avisos.sha256` — o sha256 dos 84 do raspão, mais os 3 de nov/2023
  (estes pelo caminho real em `ciram-avisos-enchente/`, porque a procedência é outra);
- `data/brutos/ciram-avisos-tipos.txt` — a classificação enchente/estiagem por arquivo.

Comandos que o Jefferson roda na VPS para fechar o material (a classificação está em
`/tmp/tipos.txt`, uma linha por arquivo, tipo em maiúsculas):

```bash
cd /opt/enchentes-vale-itajai
mkdir -p data/brutos/ciram-avisos-enchente
grep ENCHENTE /tmp/tipos.txt | cut -d' ' -f1 | \
  xargs -I{} cp data/brutos/ciram-avisos/{} data/brutos/ciram-avisos-enchente/
sha256sum data/brutos/ciram-avisos/*.pdf > data/brutos/ciram-avisos.sha256
cp /tmp/tipos.txt data/brutos/ciram-avisos-tipos.txt
```

✅ Chegaram em 09/09/2026 (branch `vps/brutos-2026-09-09`): 84 linhas no `.sha256` e na
classificação, 4 PDFs em `ciram-avisos-enchente/`.

## O que os quatro avisos dizem (lidos em 09/09/2026)

| arquivo | aviso | estação da bacia | leitura | faixa da EPAGRI |
|---|---|---|---|---|
| `aviso_n02_22012021310.pdf` | 02/2021, 22/01/2021 07:00 | 83050000 Taió | **6,69 m** às 05:00, +2 cm/h | ALERTA |
| | | 83800002 Blumenau | **6,59 m** às 05:00, −7 cm/h | ALERTA |
| `aviso_n03_22012021313.pdf` | 03/2021, 22/01/2021 16:04 | 83050000 Taió | **6,88 m** às 14:00, +2 cm/h | ALERTA |
| `aviso_n03_060520221856.pdf` | 03/2022, 06/05/2022 08:32 | 83050000 Taió | **8,37 m** às 08:00, −7 cm/h | EMERGÊNCIA |
| | | 83800002 Blumenau | **6,39 m** às 08:00, −10 cm/h | ALERTA |
| `aviso_n24_100120221423.pdf` | 24/2022, 10/01/2022 | — | estiagem em toda a bacia; a "enchente" é Camboriú (Rio Pequeno) | não é nossa |

O que se tira daí, e o que não:
- **O par de 22/01/2021 é Taió e Blumenau, no Itajaí-Açu.** Não pareia com a cheia de
  Brusque de 24/01/2021 (Itajaí-Mirim): a ressalva acima se confirmou. Serve como dois
  pontos da subida de Taió (6,69 → 6,88 m em 9 h, +2 cm/h) e um da descida de Blumenau.
- **Os limiares da EPAGRI para a 83050000 eram outros:** 6,69 m já era ALERTA em 2021, e
  8,37 m EMERGÊNCIA em 2022. A escala estadual de out/2024 diz alerta 7,00 / emergência
  8,00; o PLANCON de Taió, 8,00 / 9,00. Registrado em `estacoes.json` (Taió,
  `avisos_epagri_2021_2022`), sem mexer nas cotas em uso.
- **Nenhuma dessas leituras é pico.** Em 06/05/2022 o rio já descia às 08:00: a crista foi
  antes e foi ≥ 8,37 m.

  ✅ **A telemetria já foi pedida e está no repo** — a linha que mandava pedi-la estava
  vencida. Cristas, ordem Blumenau→Taió e os quatro candidatos a `enchentes.json` estão em
  `docs/ANA-API-2026-09-08.md`, "Quarta rodada". Reconferidas em 15/09/2026, batem.
- Para Blumenau, 6,59 m descendo às 05:00 de 22/01/2021 e 6,39 m descendo às 08:00 de
  06/05/2022 são pontos da descida da **régua da ANA (83800002)**, que não é a da Defesa
  Civil — vale a regra de referência de Blumenau.

## O que ainda não foi feito

- ✅ Os 4 avisos foram lidos (tabela acima). Nada entrou em `enchentes.json`.
- ✅ Janelas de jan/2021 e mai/2022 pedidas à ANA (09/09/2026): as cristas conferem com os avisos e estão em `docs/ANA-API-2026-09-08.md`, "Quarta rodada". Em mai/2022 a crista de Taió foi 9,49 m, 1,12 m acima da leitura do aviso.
- ✅ Ofício C12 enviado em 11/09/2026 e **respondido em 15/09/2026**: os três avisos de
  nov/2023 e cinco notas hidrometeorológicas vieram em anexo. Ver
  `docs/RESPOSTA-EPAGRI-C12-2026-09-15.md`. Jefferson foi inscrito na lista dos boletins
  diários; o primeiro chegou no mesmo dia.
- Pedir à ANA a telemetria de **nov/2023** para 83300200 (Rio do Sul), 83800002 (Blumenau) e
  83360000 (José Boiteux) — é o único caminho para o **pico** desse evento, e as três
  estações ainda transmitiam em 2023. Nenhuma cidade tem registro de nov/2023 hoje.
