# Varredura de 04/10/2026 — Ilhota, Timbó e Indaial

O Jefferson fez uma varredura externa na web em 03–04/10/2026 e a cruzou com a série estadual que já está
no repositório. Este documento registra o que foi conferido daqui, o que não pôde ser, e a proposta para
cada cidade.

**Nada entrou em `data/` nem no coletor.** Cada proposta espera a aprovação do Jefferson, cidade por cidade.
A regra nº 1 continua: cota só pinta amarrada à mesma régua da leitura.

## O que deu para reabrir daqui

**Fontes da web: nenhuma.** O proxy deste ambiente bloqueou todos os hosts em 04/10/2026:
- `bombeiroilhota.com`, `ilhota.sc.gov.br` (PLANCON);
- `misturebas.com.br`, `104fmpomerode.com.br`, `ndmais.com.br`, `cotalerta.com.br`;
- `riodoscedros.sc.gov.br`.

Tudo o que vem dessas páginas abaixo está marcado **não conferido daqui**: é a leitura do Jefferson no
navegador.

Também não usei a captura do GitHub Actions (`capturar_fontes.py`). Ela aceita só URL de coletor ou fonte
declarada em `fontes_tempo_real`, por regra testada ("nada entra por palpite"). Pôr matéria de jornal
nela quebraria essa regra. Se o Jefferson quiser os originais com sha256, o caminho é uma lista de captura
avulsa, separada dos alvos fixos, e isso é decisão dele.

**Dados do próprio projeto: tudo o que a varredura cita, e mais.**
- `data/brutos/dcsc-cheia-2026-09-11-12/*.csv`: série de 10 min da DCSC na cheia, 08/09 21:10 a 13/09 20:50.
- `nivel-sc-2026-09/10.ndjson` e `2026-0*.ndjson` da VPS, no pacote `series-2026.tar.gz` de 03/10. É a
  coleta estadual e municipal de 15 em 15 minutos, de 02/09 10:28 a 03/10 15:16.
- `data/brutos/dcsc-estacoes-vale-2026-09-13.csv`: o catálogo com as coordenadas das estações.

Carimbos em hora de Brasília, como em todo o projeto.

## 1. Ilhota — a escala municipal aparece aplicada à DCSC-00030

### Conferido daqui
- **A cheia de 12/09 chegou a 11,71 m na DCSC-00030**, de 05:10 a 05:20 (`DCSC-00030.csv`). Confere com
  a varredura.
- **A DCSC não publica faixa para a DCSC-00030.** Em 2.994 leituras de 02/09 a 03/10, `faixa_estadual`
  é sempre nula, como a varredura diz.
- **O cadastro já tem `codigo_dcsc: "DCSC-00030"`** e diz que o PLANCON cita "a estação
  hidrometeorológica da Ponte Cláudio Jeremias Cadorin". O pino de Ilhota está na coordenada da estação
  no catálogo (−26,8944, −48,8248). Que essa coordenada é a da ponte, não deu para conferir daqui.

### Não conferido daqui
- O painel dos Bombeiros Voluntários: `data-rio="DCSC-00030"`, "ATENÇÃO · 9,43 m · Normal: até 9,20 m",
  e o rodapé que atribui as cotas à COMPDEC.
- O PLANCON 2025/2028 de Ilhota: o host está bloqueado. A transcrição em `docs/cotas-municipais/ilhota.md`
  nomeia a estação da Ponte Cadorin, mas não a DCSC-00030 nem o zero.

### Três achados que pesam na decisão

**1. Com 9,20 m na DCSC-00030, Ilhota passaria quase todo setembro em "Atenção".**
- 2.659 das 2.994 leituras de 02/09 a 03/10 ficam acima de 9,20 m (89 %). A mediana é 9,57 m e o mínimo,
  8,69 m.
- Fora das cheias, a estação passa dias oscilando entre 9,17 e 9,22 m, no ritmo da maré. A análise da
  chegada a Itajaí mediu fator de maré 0,57 com atraso de 1 h em Ilhota.
- Pelo PLANCON, a faixa de 9,20 a 10,00 é "represamento dos ribeirões". Nela a COMPDEC monitora e
  **explicitamente não avisa a população**.

**2. O bot de cotas avisaria 81 vezes em 32 dias.**
- `alerta_cotas.py` avisa toda troca de faixa, para cima e para baixo, sem histerese.
- Com 9,20 / 10,00 / 10,50 na DCSC-00030, a série de setembro dá 81 trocas, 46 delas só em 9,20 m.
- Ilhota entraria no Telegram como Ascurra e Brusque. Isso é do desenho de `REGUAS_COM_COTA_PROPRIA`.

**3. O painel dos bombeiros mistura dois zeros.**
- Pela varredura, o painel lista ruas alagando a partir de 12,20 m ao lado da leitura da DCSC-00030.
- O PLANCON, na transcrição do repositório, diz que as cotas de rua são altitude em relação ao nível do
  mar ("Régua Municipal", a partir de 12,00 m) e não o zero da ponte: "Não misturar 12 m de rua com
  9,20 m da ponte".
- Ou seja: quem montou o painel aplica sobre a DCSC-00030 também um número que o plano diz ser de outra
  referência. Isso enfraquece o painel como prova de qual régua é a do 9,20.

### O que o painel prova e o que não prova
- **Prova:** uma entidade local aplica o limite de 9,20 m sobre a leitura da DCSC-00030 e atribui as cotas
  à COMPDEC.
- **Não prova:**
  - não é a COMPDEC escrevendo;
  - os 10,00 e 10,50 não aparecem no painel;
  - o mesmo painel mistura altitude de rua com a régua.

### Proposta (não aplicada)

**A regra hoje.** `REGUAS_COM_COTA_PROPRIA` pede, no comentário do código, "prova escrita da COMPDEC".
- Ascurra entrou assim, com a resposta ao C18.
- Brusque entrou com outra prova: a legenda da própria estação no portal **oficial** da Defesa Civil de
  Brusque, mais 1.287 pares de leitura.
- Aceitar Ilhota agora seria aceitar um terceiro tipo de prova: **painel de terceiro que republica a
  estação e atribui as cotas à COMPDEC**. Isso é decisão do Jefferson, não minha.

**Recomendação: esperar a resposta ao C11 atualizado.** O painel aponta a direção, mas pelos três achados
acima não basta. Se a decisão for aceitar, estes seriam os campos.

**`data/estacoes.json`, Ilhota**
- `codigo_dcsc`: já é `"DCSC-00030"`; não muda.
- `regua_das_cotas`: `"DCSC-00030 — estação hidrometeorológica da Ponte Cláudio Jeremias Cadorin (rede estadual da Defesa Civil de SC)"`
- `regua_das_cotas_fonte`: `"Painel dos Bombeiros Voluntários de Ilhota (bombeiroilhota.com/monitoramento/), lido pelo Jefferson em 03/10/2026 às 23h20: cartão com data-rio=\"DCSC-00030\", 'Normal: até 9,20 m' e rodapé que atribui as cotas à COMPDEC de Ilhota. Não é documento da COMPDEC; 10,00 e 10,50 m não aparecem no painel. O PLANCON 2025/2028 v016 cita a estação da Ponte Cláudio Jeremias Cadorin. Aceito por decisão do Jefferson em <data>."`
- `cotas_nomes_na_fonte.atencao`: `"Represamento dos ribeirões"`. Assim o chip diz o nome do plano, e não
  "Atenção", na faixa em que a COMPDEC não avisa a população (regra D6).
- `cotas_aviso_publico` tem de ser reescrito. Hoje ele diz "Não compare … com a estação estadual de Ilhota:
  são réguas com zeros diferentes", o que deixaria de ser a posição do cadastro.
- `cotas_verificado` continua `false`.

**`scripts/coleta_estadual_com_cota.py`**
```python
"DCSC-00030": {
    "cidade": "ilhota",
    "rio": "itajai-acu",
    "estacao": "Ilhota — Ponte Cláudio Jeremias Cadorin (DCSC-00030)",
    "fonte": ("Rede estadual (Defesa Civil de SC), estação DCSC-00030. Faixas do PLANCON "
              "2025/2028 de Ilhota (9,20 / 10,00 / 10,50 m), aplicadas a esta estação pelo "
              "painel dos Bombeiros Voluntários de Ilhota, que as atribui à COMPDEC "
              "(lido em 03/10/2026). Sem confirmação escrita da COMPDEC."),
},
```

**Efeito na tela, se aplicado**
- Com 9,43 m, Ilhota entra em "Atenção", ou em "Represamento dos ribeirões" com o nome do plano. A cor é
  amarela; hoje é cinza.
- O cartão "Agora" passa a ter a frase da cota e o "quanto falta".
- Ilhota entra no Telegram. Em setembro seriam 81 mensagens, como no achado 2.
- O trecho de 36,4 km do Açu em Ilhota passa a pintar (A4 do checklist).

### C11 atualizado
O texto para envio está em `docs/oficios-prontos.md`, logo abaixo do C11 original. Ele pergunta só o que
falta.
