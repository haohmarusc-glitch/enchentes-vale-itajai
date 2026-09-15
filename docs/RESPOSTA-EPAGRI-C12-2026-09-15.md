# Resposta da EPAGRI/CIRAM ao ofício C12 — os avisos de nov/2023 chegaram, e vêm com uma ressalva que muda como se lê qualquer aviso

**Fonte, conferida no Gmail em 15/09/2026:** e-mail de **sshidrosc@epagri.sc.gov.br**
(SSHidroSC — Sala de Situação Hidrologia SC), assinado por **Mariane**, enviado em
**15/09/2026 às 08:34** (Brasília), mensagem `1a0a4d946a23087b` na mesma thread do C5
(*"Re: Solicitação de acesso aos dados do Rios On-Line…"*), 6.040.840 bytes, **8 PDFs**.
Responde ao C12, que o Jefferson enviou em **11/09/2026 00:05 BRT**. Os anexos foram
salvos por ele e conferidos neste repositório em 15/09/2026.

Fecha o veredito de `docs/CIRAM-ACERVO.md`, que dizia que o Aviso 03 de 19/11/2023
"não existe em lugar nenhum acessível". Existe: **sai por e-mail, e veio.**

## ⚠️ A ressalva, que é bloqueante

Palavras da Mariane, na íntegra na parte que importa:

> "os avisos e boletins são um relatório extraído no momento em que o pdf automático é
> gerado, então nem sempre os níveis mais altos atingidos pelos rios em um dia estão nos
> avisos/boletins. Esse documento é uma visão 'instantânea' do rio no horário da coleta.
> **A série histórica completa dos dados telemétricos sempre será a fonte que vai fornecer
> o pico da enchente e o horário em que ele ocorreu**, caso não existam falhas."

Portanto: **um nível lido num aviso é piso, nunca pico.** Nenhum número deste arquivo
entra em `enchentes.json` como pico de evento.

Isto não é cautela teórica. Está medido abaixo, na seção "A ressalva, comprovada".

## Os três avisos, transcritos

Só aparecem as estações em **regime hídrico extremo** no momento da geração. A ausência de
uma estação **não** significa nível baixo — significa que ela não cruzou o limiar, ou que
não havia leitura. Não inferir nada de uma ausência.

### Aviso 01/2023 — Florianópolis, 17/11/2023 07:35
EMERGÊNCIA: José Boiteux, Rio do Sul – Novo, Taió, Joaçaba I, Itapiranga · ALERTA: São João Batista

| Código | Município | Estação | Data/hora | Nível | Taxa |
|---|---|---|---|---|---|
| 83360000 | José Boiteux | Jose Boiteux | 17/11 06:45 | 4,35 m | −5 cm/h |
| 83300200 | Rio do Sul | Rio do Sul – Novo | 17/11 07:00 | 10,62 m | +4 cm/h |
| 83050000 | Taió | Taió | 17/11 07:00 | 9,74 m | +6 cm/h |

Fora da bacia: São João Batista 84095500 5,91 m (−11); Joaçaba I 72849000 8,03 m (−20);
Itapiranga 74329000 11,07 m (+17).

### Aviso 02/2023 — Florianópolis, 18/11/2023 07:10
EMERGÊNCIA: Encruzilhada II, Taió, São João Batista, Itapiranga · ALERTA: Rio Bonito

| Código | Município | Estação | Data/hora | Nível | Taxa |
|---|---|---|---|---|---|
| 83050000 | Taió | Taió | 18/11 06:00 | 10,18 m | −3 cm/h |

Fora da bacia: Rio Bonito 71300000 7,96 m (+6); Encruzilhada II 71350001 7,90 m (+3);
São João Batista 84095500 7,21 m (−24); Itapiranga 74329000 13,58 m (+1).

**Rio do Sul não aparece neste aviso** — e reaparece em 19/11 a 11,57 m. Não pode ter caído
abaixo do limiar e voltado. Ou houve falha telemétrica em 18/11, ou o critério de listagem
mudou. **Não sei qual**; é pergunta para a Equipe de Hidrologia, não para inferência.

### Aviso 03/2023 — Florianópolis, 19/11/2023 10:19
EMERGÊNCIA: Rio Bonito, Encruzilhada II, Rio do Sul – Novo, Taió, Itapiranga

| Código | Município | Estação | Data/hora | Nível | Taxa |
|---|---|---|---|---|---|
| 83300200 | Rio do Sul | Rio do Sul – Novo | 19/11 09:00 | 11,57 m | −6 cm/h |
| 83050000 | Taió | Taió | 19/11 09:00 | 8,87 m | −5 cm/h |

Fora da bacia: Rio Bonito 71300000 9,58 m (+6); Encruzilhada II 71350001 8,56 m (+2);
Itapiranga 74329000 11,35 m (−12).

Rio do Sul a 11,57 m **já em recessão** (−6 cm/h): o pico foi antes e foi mais alto.

## ✅ A ressalva, comprovada — Taió, com telemetria da ANA na mão

`data/brutos/ana-telemetria-83050000-2023-11-{17,24}-DIAS_7.json` cobre 11/11 a 24/11/2023,
1.328 leituras de 15 min. Confronto direto:

| Momento | Aviso | Telemetria ANA |
|---|---|---|
| 17/11 07:00 | 9,74 m | **9,74 m** |
| 18/11 06:00 | 10,18 m | **10,18 m** |
| 19/11 09:00 | 8,87 m | **8,87 m** |

Os três batem **ao centímetro**. Os avisos são recortes fiéis da mesma série — a
procedência está confirmada, não suposta.

E é justamente por baterem que a ressalva fica demonstrada:

- maior valor **nos avisos**: 10,18 m (18/11 06:00);
- pico **na série**: **10,32 m em 17/11/2023 21:00**.

**14 cm e nove horas de diferença.** Quem tomasse o máximo dos avisos como pico do evento
erraria para baixo — exatamente o erro que este projeto não pode cometer.

A crista está bem amostrada: 10,28 → 10,32 entre 19:00 e 23:45 de 17/11, patamar plano.
Há 6 leituras nulas entre 18/11 00:15 e 01:30, mas as vizinhas (10,31 antes, 10,28 depois)
já estão em recessão — a lacuna não esconde crista. Única falha real da janela:
24/11 20:00→22:15, fora do evento.

**83029900 (Barragem Taió Montante)** tem série só até **17/11 02:15** — para nesse dia,
antes do pico de Taió. Máximo do que existe: 2,99 m em 17/11 00:30, que é piso.
**83250000 (Ituporanga)** não devolveu cota nenhuma na janela.
**83892990 (Salseiro, Vidal Ramos)**: máximo 5,23 m em 17/11 09:15 — bem amostrado.

## As notas hidrometeorológicas: tabelas da Defesa Civil/SPEHC

As cinco notas são e-mails do grupo `notamet@epagri.sc.gov.br` (remetente Contato Ciram).
O texto é meteorológico e qualitativo. **O que tem número está em imagem**, extraída dos
PDFs. Duas tabelas cobrem o Vale do Itajaí, com a coluna **"Situação Atual — Cota (m)"**:

### 16/11/2023 9h
| Local | Cota | Situação |
|---|---|---|
| Brusque | 1,7 m | Elevação |
| Ituporanga * | 3,7 m | Estabilidade |
| Taió | 6,6 m | Elevação |
| Rio do Sul | 6,5 m | Elevação |
| Blumenau | 4,2 m | Estabilidade |
| Timbó | 2,1 m | Elevação |
| Trombudo Central ** | 2,0 m | Elevação |

### 17/11/2023 08h
| Local | Cota | Situação |
|---|---|---|
| Brusque | 6,27 m | Recessão |
| Ituporanga * | 4,1 m | Elevação |
| Taió | 9,8 m | Elevação |
| Ascurra ** | 13,0 m | Elevação |
| Rio do Sul | 10,9 m | Elevação |
| Blumenau | 9,1 m | Elevação |
| Timbó | 3,9 m | Elevação |
| Trombudo Central ** | 4,5 m | Elevação |

Rodapé da própria tabela: `*` Ituporanga usa como referencial a **estação DCSC Ituporanga**;
`**` a previsão de Ascurra e Trombudo Central é **gerada a partir de eventos anteriores**,
não pelo modelo.

A coluna seguinte das tabelas, também rotulada "Cota (m)", é **previsão do SPEHC** para os
dias seguintes. Não confundir com medição: não transcrevi essa coluna aqui de propósito.

**O que essas tabelas NÃO dizem: a referência altimétrica.** A coluna diz "Cota (m)" e nada
mais. Para Blumenau isso esbarra direto na `REGRA_REFERENCIA_BLUMENAU`: sendo tabela
operacional da Defesa Civil, régua é a hipótese provável — mas **hipótese não é o campo
`referencia`**. Se algum dia esses valores forem usados, vão com `referencia: null` e a
suposição em `referencia_hipotese`.

Uma tabela do Vale do Itajaí existe também na nota de 21/11, mas está embutida a
**226×90 px** — ilegível na origem. Não dá para recuperar e não vou adivinhar o conteúdo.
As demais imagens são de outras bacias (Planalto Norte, Planalto Sul/Oeste, Litoral
Sul/Grande Florianópolis) e mapas de situação sem números.

## Uma divergência que fica registrada, não resolvida

Para **17/11/2023 por volta das 08h**, duas fontes da mesma casa:

| | Taió | Rio do Sul |
|---|---|---|
| Aviso 01 (07:00) + taxa | 9,74 m, +6 cm/h → ~9,80 às 08:00 | 10,62 m, +4 cm/h → ~10,66 às 08:00 |
| Tabela DCSC/SPEHC (08h) | **9,8 m** — bate | **10,9 m** — diverge em ~24 cm |

Taió fecha; Rio do Sul não. Fica como divergência anotada. Não escolher uma das duas.

## O que a carta rende além dos anexos

1. **Canal aberto, sem ofício formal.** "Sempre que precisar, é só solicitar os documentos,
   pois são dados públicos e podemos enviar desde que não contenham dados sensíveis."
2. **Acesso programático está fechado, por decisão.** Os arquivos ficam só temporariamente
   na página do CIRAM e depois vão para servidor interno; não compartilham os diretórios
   "por motivos de segurança". Raspar o acervo morreu como estratégia — o caminho é pedir.
   Isso confirma, pelo lado deles, as quatro vias fechadas de `docs/CIRAM-ACERVO.md`.
3. **Inscrição na lista dos boletins diários feita.** O primeiro chegou no mesmo dia
   (Boletim nº 160/2026, 15/09 08:11 BRT; bacia do Itajaí-Açu em normalidade).

## O que isto confirma do cadastro

- **83050000 = Taió** e **83300200 = Rio do Sul**: os avisos de 2023 usam exatamente os dois
  códigos que `data/estacoes.json` já traz. **Resolve o "dois códigos, um nome"** levantado
  na resposta ao C5 (83270000 "Rio do Sul – Novo" vs 83300200): quem a operação usa é a
  **83300200**. Nada a mudar no cadastro — a dúvida é que sai.
- Em 2023 a EPAGRI chamava a 83050000 de **"Taió"**; na tabela do C5 (2026) ela aparece como
  **"Saltinho"**. Mesmo código, rótulo diferente em épocas diferentes.
### 83360000 "Jose Boiteux" — investigado em 15/09/2026, e não é lacuna

A primeira leitura ("estação nos avisos que falta no cadastro") estava errada. O que os
dados do repo dizem:

- **A cidade já é lida ao vivo.** `scripts/coleta_nivel_sc.py` mapeia **`DCSC-00021` →
  `jose-boiteux`** desde antes; a rede estadual entrega a leitura (3,06 m em 13/09/2026,
  −26,95484 / −49,63359). Não falta fonte.
- **O que falta é outra coisa:** José Boiteux não é cidade do `rios['itajai-acu'].cidades`
  (são 15). Aparece como régua estadual no Monitor, não como elo da árvore. Fica a montante
  do Ibirama no ramo `itajai_do_norte`, e entrar na árvore é decisão de topologia, não de
  cadastro de estação — `docs/TOPOLOGIA-CANONICA.md` manda a fonte dizer a confluência.
- **A estação da ANA está morta.** A tabela do C5 diz `83360000 · José Boiteux ·
  Desativada · 01/01/2012 → 04/12/2024`. Estava viva em nov/2023, então serve para a
  telemetria histórica — e **não** como fonte ao vivo.

**Terceiro caso da mesma armadilha.** O inventário da ANA de 08/09/2026
(`data/brutos/ana-inventario-api-2026-09-08.json`) diz `Operando: "1"` e
`Tipo_Estacao_Telemetrica: "1"` para a 83360000, com `Data_Periodo_Telemetrica_Fim: null` —
e a operadora (EPAGRI-SC) diz desativada desde 04/12/2024. É o mesmo padrão já registrado em
`docs/RESPOSTA-EPAGRI-C5-2026-09-09.md` para Brusque (83900000) e Blumenau (83800002).
**O campo `Operando` do inventário não prova estação viva**; quem sabe é a operadora.

## ⛔ O que NÃO fazer com estes arquivos

1. **Não gravar nível de aviso como pico** em `enchentes.json`. É piso, por escrito da fonte.
2. **Não inferir nada da ausência** de uma cidade num aviso. Só lista quem cruzou limiar.
3. **Não usar a coluna de previsão** das tabelas SPEHC como medição.
4. **Não atribuir referência** aos valores das tabelas DCSC — elas não declaram nenhuma.
5. **Não misturar** o 11,57 m de Rio do Sul (19/11, já em recessão) com um pico do evento.

## Próximo passo concreto, na VPS

Blumenau (83800002) e Rio do Sul (83300200) **estavam ativas em nov/2023** — foram
desativadas depois (04/04/2026 e as demais, conforme a resposta ao C5). A telemetria
histórica delas deve existir na API:

```
python3 scripts/sonda_ana_api.py --estacoes 83300200,83800002,83360000 --data 2023-11-24 --intervalo DIAS_7
python3 scripts/sonda_ana_api.py --estacoes 83300200,83800002,83360000 --data 2023-11-17 --intervalo DIAS_7
```

É o único caminho que dá **pico** para Rio do Sul e Blumenau em nov/2023 — e o único que a
própria EPAGRI reconhece como fonte de pico. Enquanto não rodar, o evento de nov/2023
continua **sem nenhum registro** em `enchentes.json`, que é o estado correto hoje.

## Arquivos

```
data/brutos/ciram-avisos-enchente/aviso_n01_17112023.pdf
data/brutos/ciram-avisos-enchente/aviso_n02_18112023.pdf
data/brutos/ciram-avisos-enchente/aviso_n03_19112023.pdf
data/brutos/ciram-notas-hidro/nota_hidrometeorologica_{16,17,20,21,28}112023.pdf
```

SHA-256 em `data/brutos/ciram-avisos.sha256` e `data/brutos/ciram-notas-hidro.sha256`.
Procedência diferente do restante do acervo: estes vieram **por e-mail**, não do raspão do
portal — por isso o manifesto os lista pelo caminho real, em `ciram-avisos-enchente/`.
