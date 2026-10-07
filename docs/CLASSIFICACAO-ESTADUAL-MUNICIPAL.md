# Classificação estadual × municipal (07/10/2026)

O plano está em `PLANO_BACKEND_CLASSIFICACAO_ESTADUAL_MUNICIPAL.md`, enviado pelo Jefferson em 07/10/2026. O trabalho foi
dividido em três PRs, começando depois da decisão sobre os PRs #504–#509, que foram todos mergeados:

1. **PR 1 (#510, mergeado).** O motor Python gera o estado em paralelo, e o site não muda o que consome. Em produção
   desde a coleta das 17h30 UTC de 07/10/2026.
2. **PR 2 (#511, mergeado).** O site passa a seguir o estado (`ultimo_classificacao.json`) nas telas que usam
   `estadoDaCidade` — ver a seção "PR 2" abaixo.
3. **PR 3.** O mapa do Monitor segue a mesma decisão, e o painel da cidade diz qual classificação deu a cor — ver a
   seção "PR 3" abaixo.

## Decisões fechadas (Jefferson, 07/10/2026)

- **Cadastro:** o motor lê o `estacoes.json` sem alterá-lo. Campos novos dependem de proposta e da aprovação do Jefferson.
- **Faixa estadual:** vale a classificação publicada pela Defesa Civil de SC (`rio_alarmes`, validada em
  `coleta_nivel_sc.classificar_alarmes`). Nenhuma comparação numérica com limites por estação até haver limites
  oficiais e referência de régua validada.
- **As regras ficam registradas no `CLAUDE.md`**, na seção "Classificação estadual × municipal".

## O que entra

| Arquivo | Papel |
|---|---|
| `scripts/classificar_reguas.py` | O motor. Calcula as duas classificações de cada cidade do piloto, escolhe a que pinta e valida a saída. `--gravar` grava `data/tempo-real/ultimo_classificacao.json`; `--inventario` mostra o que bloqueia cada cidade. |
| `data/classificacao-esperada.json` | Gabarito com 17 casos, compartilhado entre o motor e o site. |
| `scripts/teste_classificar_reguas.py` | Paridade com o gabarito e a lista do §11 do plano que cabe aqui: limites, frescor, régua diferente, faixas não confirmadas, fallback e validador. |
| `web/src/logica/classificacaoParidade.test.ts` | Exige que o site de **hoje** produza o lado `site` do gabarito, pelos mesmos caminhos da tela (parser do `ultimo.json`, `montarNivelSc`, `estadoDaCidade`). |
| `scripts/validar_dados.py` | `valida_classificacao_piloto`: a cidade do piloto precisa ter um cadastro que o motor aceite. |
| `scripts/publicar_tempo_real.sh` | Roda o motor (só fora do `--seco`, com `timeout 60`) e publica o arquivo no branch `tempo-real` quando ele é JSON, tem cidades e foi gerado há no máximo 30 min. Uma falha nunca segura o nível ao vivo. |

O site **não lê** o arquivo novo. Nenhum componente, tipo ou consumo do `web/` mudou; só entrou o teste de paridade.

## As regras do motor

1. **A régua da leitura tem de ser a régua das faixas.** A classificação municipal só sai quando a leitura é da régua das
   cotas da cidade, por identidade (código). Proximidade e título parecido não contam.
   - A identidade vem do campo `regua_das_cotas_id` (`{codigo, fonte}`, aprovado pelo Jefferson em 07/10/2026 — ver a
     seção "O campo `regua_das_cotas_id`"). O `codigo` é o que a leitura carrega: o `codigo` dela (`DCSC-…`) ou, sem
     código, o título da publicação como `comum.regua_de` o devolve.
   - Estação estadual que pinta com as cotas da cidade (`REGUAS_COM_COTA_PROPRIA`) tem de concordar com o campo, e um
     código `DCSC-…` tem de ser o `codigo_dcsc` da cidade. Se as fontes discordarem, a cidade fica sem classificação.
2. **Não há conversão entre réguas.** Nenhum vínculo oficial está cadastrado, e o motor não converte.
3. **A estadual é a faixa publicada pela própria Defesa Civil de SC.** O metro da estação não é comparado com nada: ele
   aparece com a observação de que o zero é o da estação.
4. **A municipal manda.** A estadual só pinta quando a cidade **não tem leitura municipal de agora**, com o mesmo critério do
   site (`estadoDaCidade`). Nesse caso, a saída leva `fallback: true` e um aviso: *"Cor pela classificação que a Defesa Civil
   de SC publica para a estação …, no zero dela. Não são as cotas do município."*
5. **Não classificam:**
   - leitura velha (> 180 min; em Blumenau, > 120 min);
   - carimbo no futuro (> 15 min);
   - leitura sem carimbo;
   - nível fora de (0, 25) m na municipal ou de (0, 30) m na estadual;
   - cidade com várias réguas.

   O número continua na saída, com o motivo.
6. **A municipal também não classifica** nestes casos:
   - sem `fonte_cotas` (a fonte das faixas) ou sem a `fonte` do `regua_das_cotas_id` (a prova da régua);
   - `cotas_verificado` diferente de `true`;
   - cotas de acionamento fora de ordem;
   - cidade com comparador especial ainda não transcrito: Ascurra (C18) e Gaspar ("maior que").
7. **A saída diz a faixa, não a cor.** A cor de cada faixa é um token do site (tema claro e escuro), e "cor = faixa,
   nunca metro" continua sendo regra da tela.

Os limites de frescor, o vocabulário das fases e o arredondamento da idade são cópia do site
(`logica/tempoReal.ts`, `logica/cotasOperacionais.ts` e `dados/nivelSc.ts`). O gabarito trava os dois lados.

## Formato de `ultimo_classificacao.json`

```json
{
 "versao": 1,
 "gerado_em": "2026-10-07T17:10:00+00:00",
 "piloto": ["brusque"],
 "cidades": {
  "brusque": {
   "classificacoes": {
    "municipal": {"tipo": "municipal", "regua_id": "DCSC-00019", "regua_da_leitura": "DCSC-00019",
                  "nivel_m": 2.29, "medido_em": "2026-10-07T12:59:55", "status_leitura": "valida",
                  "status_faixas": "confirmada", "cotas_m": {"atencao": 3.0, "emergencia": 5.0},
                  "fonte_faixas": "…", "faixa": "normal", "motivo": null},
    "estadual":  {"tipo": "estadual", "regua_id": "DCSC-00019", "nivel_m": 2.29,
                  "zero": "o da própria estação estadual …", "status_leitura": "valida",
                  "fonte_faixas": "Defesa Civil de SC — rio_alarmes.inundacao …", "faixa": "normal", "motivo": null}
   },
   "classificacao_aplicada": {"tipo": "municipal", "faixa": "normal", "regua_id": "DCSC-00019", "fallback": false,
                              "rotulo": "Classificação municipal — Ponte Estaiada – DCSC (DCSC-00019)",
                              "aviso": null, "motivo": null},
   "faixa_do_rio": "normal"
  }
 }
}
```

`medido_em` segue o contrato do projeto: hora de Brasília, sem fuso. `gerado_em` é em UTC.

O exemplo acima é a saída real com a última publicação do branch `tempo-real` (coleta das 16h00 UTC de 07/10/2026).
Brusque estava com 2,29 m e normal nas duas classificações.

## Piloto: Brusque

Brusque é a cidade em que leitura e faixas estão comprovadamente na mesma estação: DCSC-00019, com 1.287 pares e diferença
máxima de 3 cm (`docs/BRUSQUE-DCSC-00019.md`). A Defesa Civil de SC também publica faixa própria para essa estação, então
as duas classificações existem lado a lado. No `--inventario`, é a única cidade sem nenhum bloqueio.

## Paridade com o site, e a divergência que é de propósito

Em 16 dos 17 casos, o motor pinta exatamente o que o site pinta hoje. O caso `leitura-de-outra-regua` é a exceção
declarada (`diverge_do_site`):
- **Situação:** a única leitura municipal de Brusque é de outra régua (título "Brusque", sem código).
- **Site hoje:** compara essa leitura com as cotas da DCSC-00019 e pinta.
- **Motor:** recusa, pela regra 1, e a cidade fica sem cor (a estadual não entra, porque há leitura municipal de agora).

O site adota a regra no PR 2, quando recebe o arquivo do motor desta coleta.

## Inventário: o que falta para cada cidade entrar

Situação em 07/10/2026, depois do campo `regua_das_cotas_id` e do piloto ampliado (`--inventario`):

| Cidade | Bloqueios |
|---|---|
| `itajai-acu/taio` | sem `regua_das_cotas_id`; `cotas_verificado` ≠ true |
| `itajai-acu/ituporanga` | sem cota de acionamento; sem `regua_das_cotas_id`; sem `fonte_cotas`; `cotas_verificado` ≠ true |
| `itajai-acu/rio-do-sul` | publicações sem referência validada no motor; `cotas_verificado` ≠ true |
| `itajai-acu/ibirama` | sem cota de acionamento; sem `regua_das_cotas_id`; `cotas_verificado` ≠ true |
| `itajai-acu/lontras` | sem cota de acionamento; sem `regua_das_cotas_id`; `cotas_verificado` ≠ true |
| `itajai-acu/apiuna` | sem cota de acionamento; sem `regua_das_cotas_id`; sem `fonte_cotas`; `cotas_verificado` ≠ true |
| `itajai-acu/ascurra` | comparador especial (C18) |
| `itajai-acu/indaial` | sem `regua_das_cotas_id` |
| `itajai-acu/blumenau` | **no piloto** |
| `itajai-acu/gaspar` | comparador especial (estação 21, "maior que"); publicações sem referência validada no motor |
| `itajai-acu/ilhota` | sem `regua_das_cotas_id`; `cotas_verificado` ≠ true |
| `itajai-acu/itajai` | sem cota de acionamento; sem `regua_das_cotas_id`; sem `fonte_cotas`; `cotas_verificado` ≠ true |
| `itajai-acu/timbo` | sem cota de acionamento; sem `regua_das_cotas_id`; `cotas_verificado` ≠ true |
| `itajai-acu/rio-dos-cedros` | **no piloto, sem classificação municipal** (cotas não confirmadas; faixa estadual quando válida) |
| `itajai-acu/trombudo-central` | sem cota de acionamento; sem `regua_das_cotas_id`; `cotas_verificado` ≠ true |
| `itajai-mirim/vidal-ramos` | sem cota de acionamento; sem `regua_das_cotas_id`; sem `fonte_cotas`; `cotas_verificado` ≠ true |
| `itajai-mirim/botuvera` | sem cota de acionamento; sem `regua_das_cotas_id`; sem `fonte_cotas`; `cotas_verificado` ≠ true |
| `itajai-mirim/guabiruba` | sem cota de acionamento; sem `regua_das_cotas_id`; sem `fonte_cotas`; `cotas_verificado` ≠ true |
| `itajai-mirim/brusque` | **no piloto** |
| `itajai-mirim/itajai` | sem cota de acionamento; sem `regua_das_cotas_id`; sem `fonte_cotas`; `cotas_verificado` ≠ true |

### Como ler os bloqueios

- **"sem `regua_das_cotas_id`"**: o cadastro ainda não tem a prova escrita de qual publicação é a régua das cotas.
  - Taió: o próprio cadastro diz que a régua das cotas continua em aberto (`regua_nota`).
  - Indaial e Ilhota: estão sem leitura municipal hoje.
  - As demais: não têm cota de acionamento.
- **"publicações sem referência validada no motor"** vale para régua identificada por título (Rio do Sul, Gaspar). Cada
  publicação aceita entra em `PUBLICACOES_VALIDADAS`, com a prova, quando a cidade entrar no piloto.
- **"`cotas_verificado` ≠ true"** em Rio dos Cedros é coerente com a resposta ao C29: a COMPDEC não falou do zero nem da
  vigência da escala depois do desassoreamento. Por decisão do Jefferson de 07/10/2026, Rio dos Cedros está no piloto
  sem classificação municipal até essa confirmação, sem exceção: a cor é a faixa estadual quando válida, e cinza sem
  ela (`PILOTO_SEM_MUNICIPAL`). A pergunta à COMPDEC é o C32 (`docs/oficios-prontos.md`).
- **Comparador especial**: Ascurra e Gaspar precisam ter a regra transcrita com o mesmo comparador da fonte, e um caso
  no gabarito, antes de entrar.

## O campo `regua_das_cotas_id` (aprovado pelo Jefferson em 07/10/2026)

```json
"regua_das_cotas_id": {
  "codigo": "Rio do Sul, Ponte Dom Tito Buss (Asthon)",
  "fonte": "onde está a prova de que esta publicação é a régua das cotas",
  "registro": "Campo aprovado pelo Jefferson em 07/10/2026; o valor transcreve a prova que o cadastro já registrava."
}
```

- `codigo` é a identidade que a leitura carrega (`codigo` da leitura ou o título por `comum.regua_de`), e não um nome
  parecido.
- `fonte` aponta a prova, que já estava no cadastro. Nenhum valor foi decidido aqui.
- O `validar_dados.py` (`valida_regua_das_cotas_id`) cobra:
  - `codigo` e `fonte`;
  - só as chaves `codigo`, `fonte` e `registro` (conversão não entra por este campo);
  - nenhum código em duas cidades do mesmo rio;
  - `DCSC-…` igual ao `codigo_dcsc`;
  - `REGUAS_COM_COTA_PROPRIA` concordando nos dois sentidos.

Entrou em seis cidades, as que têm a prova no cadastro:

| Cidade | `codigo` | De onde vem a prova |
|---|---|---|
| Brusque | `DCSC-00019` | par provado (07/09 e 03/10/2026, `docs/BRUSQUE-DCSC-00019.md`) + `REGUAS_COM_COTA_PROPRIA` |
| Ascurra | `DCSC-00003` | resposta ao C18 (11/09/2026) + `REGUAS_COM_COTA_PROPRIA` |
| Rio dos Cedros | `DCSC-00011` | resposta ao C29 (07/10/2026) + `REGUAS_COM_COTA_PROPRIA` |
| Rio do Sul | `Rio do Sul, Ponte Dom Tito Buss (Asthon)` | cotas = `band_thresholds` da Asthon na própria estação; par resolvido em 09/09/2026 |
| Blumenau | `Blumenau` | escala e nível no mesmo `nivel_oficial.json` do AlertaBlu; par provado por medição (18/09/2026) |
| Gaspar | `Gaspar — Rio Itajaí-Açu (Defesa Civil de Gaspar)` | cotas da legenda da estação 21, a mesma estação lida |

Ficou de fora quem não tem a prova escrita (Taió, Indaial, Ilhota e as cidades sem cota de acionamento).

**Na saída do motor**, `fonte_faixas` passou a ser a `fonte_cotas` da cidade (a fonte das faixas). A prova da régua foi para
um campo próprio, `fonte_regua`, que o validador da saída também exige. A faixa e quem pinta não mudam.

## Piloto ampliado: Blumenau e Rio dos Cedros (decisões do Jefferson, 07/10/2026)

As três decisões:
- **Blumenau entra**, "desde que a leitura e as cotas estejam vinculadas à mesma régua, com referência validada".
- **Rio dos Cedros** fica "sem classificação municipal até confirmar as cotas. Não abra exceção. Se houver classificação
  estadual válida para a estação, pode exibi-la, identificada como 'faixa estadual'. A ausência de cotas municipais não
  significa nível normal".
- **Brusque** mantém a cor atual.

### Blumenau: a condição conferida
- **Mesma régua.** A escala das cotas (`condicoes`: Observação 3 · Atenção 4 · Alerta 6 · Alerta Máximo 8 m) e o nível
  (`niveis`) saem do **mesmo** `nivel_oficial.json` do AlertaBlu. A escala foi conferida no bruto
  `data/brutos/blumenau-alertablu-nivel-oficial-sem-serie-2026-09-09.json`, e o par foi provado por medição
  (`regua_nota`, 18/09/2026).
- **Referência validada.** As cotas e a leitura ao vivo estão na régua de hoje, que é a do AlertaBlu (CLAUDE.md, referência
  altimétrica de Blumenau). A regra bloqueante de Blumenau trata dos picos históricos, não da leitura ao vivo.
- **Só publicações validadas** (`PUBLICACOES_VALIDADAS`):
  - `Blumenau (AlertaBlu)`: o mesmo arquivo das cotas;
  - `Blumenau (PADKND)`: só entra quando bate com o AlertaBlu na mesma coleta, com 1 cm de folga
    (`conferir_com_alertablu`).
- O repasse antigo `Blumenau` da Defesa Civil de Itajaí tem a mesma identidade, mas vinha 3 h atrasado e até 0,245 m acima.
  Está fora do ar desde 19/09; se voltar, **não pinta pelas cotas**. É o caso `blumenau-repasse-sem-referencia-validada`
  do gabarito, uma divergência declarada.
- **Na tela:** *"Cor do rio: classificação municipal — régua do AlertaBlu (Blumenau)."* O nome da ponte não entra porque a
  fonte não nomeia o ponto.
- **Não há classificação estadual:** a DCSC-00026 de Blumenau é meteorológica.

### Rio dos Cedros: sem classificação municipal
- Entra no piloto **de propósito sem classificação municipal** (`PILOTO_SEM_MUNICIPAL`). O motor nunca compara o nível com
  as cotas 4,80/5,30/5,70 m enquanto `cotas_verificado` não for `true`, e o validador só aceita essa exceção para Rio dos
  Cedros.
- **A municipal só segura a estadual com cotas confirmadas** (`segura_estadual` na saída do motor). Aqui a leitura municipal
  de agora não segura, e a faixa que a Defesa Civil de SC publica para a DCSC-00011 aparece, como *faixa estadual*:
  - chip tracejado "Atenção · Defesa Civil SC";
  - no Monitor, "Cor do rio: faixa estadual (Defesa Civil de SC) — DCSC-00011. Não representa as cotas municipais.".
- **Sem faixa estadual válida**, a cidade fica **cinza**, nunca verde. O cartão diz: "Sem classificação municipal: as
  cotas de Rio dos Cedros ainda não foram confirmadas pela Defesa Civil do município. Isso não quer dizer que o nível
  esteja normal." O "Por que está cinza?" do Monitor diz o mesmo.
- **Nada compara o nível com as cotas não confirmadas:**
  - o cartão não mostra a frase "Faltam X cm para a cota" nem o medidor;
  - o quadro de cota do Monitor diz "Cotas municipais — ainda não confirmadas";
  - o bot já exigia `cotas_verificado: true`.
- **O que muda para quem olha Rio dos Cedros:**
  - **antes:** às 17h16 de 07/10, com 3,69 m, o site pintava *normal* pelas cotas não confirmadas;
  - **agora:** mostra a faixa estadual publicada, *atenção*.

### Brusque
Sem mudança: as cotas estão confirmadas e a municipal continua mandando. Os 17 casos dela no gabarito ficaram iguais.

### Nome "faixa estadual"
- A origem estadual passou a se chamar **faixa estadual** no rótulo do motor (`Faixa estadual (Defesa Civil de SC) — …`),
  no painel do Monitor ("Faixa estadual: Atenção" e "Cor do rio: faixa estadual …") e no cartão.
- O chip continua "Atenção · Defesa Civil SC", tracejado.

### Testes e conferência
- **Gabarito:** 29 casos, 12 novos.
  - Blumenau: AlertaBlu; PADKND mais nova; Observação exata e abaixo dela; Alerta Máximo; 120 e 121 min; repasse sem
    referência validada.
  - Rio dos Cedros: estadual em atenção; sem faixa estadual; acima da atenção não confirmada; estadual velha.
  - Divergências declaradas em `diverge_do_site`, com a decisão de 07/10.
- **Motor e site:** os testes do motor cobrem o piloto, a exceção restrita a Rio dos Cedros, as publicações validadas e
  `segura_estadual`. `classificacaoNoMapa.test.ts` cobre mapa e cartão iguais nos 29 casos e os textos de Blumenau e de
  Rio dos Cedros.
- **Navegador**, com a coleta de produção das 20h31 UTC e o motor novo:
  - Blumenau: 4,85 m, atenção, "régua do AlertaBlu";
  - Rio dos Cedros: 3,69 m, faixa estadual atenção, com o porquê;
  - Brusque: 2,17 m, normal, sem mudança.

  A trava do Monitor passou sem regravar o baseline.

## PR 2: o site segue o motor

`web/src/dados/classificacao.ts` lê o `ultimo_classificacao.json` (rede primeiro, como o resto do branch `tempo-real`) e
`estadoDaCidade` passa a usar a decisão do motor. Isso vale para o cartão "Agora", as listas, o início e o chat. O Monitor
(`MonitorBacia`, `mapaMotor`) não lê o arquivo; isso é o PR 3.

O site só segue o motor quando **todas** as condições abaixo valem. Basta uma falhar para a cidade voltar, naquela
renderização, à regra de sempre (`faixaDaCidade` + `faixaDaRedeEstadual`):

1. **O arquivo é desta coleta.** `versao: 1`, `gerado_em` com fuso, e no máximo 30 min de idade
   (`MAX_IDADE_CLASSIFICACAO_MIN`, o mesmo limite do publicador).
2. **A cidade está no arquivo e no mesmo rio.** Hoje é só Brusque.
3. **O motor viu as mesmas medições que a tela mostra.** O `medido_em` da municipal e o da estadual precisam ser iguais
   aos do `ultimo.json` e do `ultimo_nivel_sc.json` que o site buscou. Os três arquivos são buscados em separado e podem
   vir de publicações vizinhas; sem isso, a cor seria de um número que não está na tela.
4. **O arquivo é entendido.** Faixa fora do vocabulário, cor sem carimbo, municipal com `regua_da_leitura` ≠ `regua_id`
   ou classificações trocadas fazem a cidade ser ignorada.

**A idade é refeita no relógio de agora.** O motor rodou na hora da coleta. Uma leitura que estava "atrasada" naquela
hora pode ter ficado velha minutos depois. O site então descarta a faixa velha e refaz a escolha (municipal manda;
estadual só sem municipal de agora), com as faixas que o motor deu.

`EstadoDaCidade` ganhou `classificadaPor` (`motor` ou `site`) e `origemDaCor` (tipo, régua, rótulo e, na estadual, o
aviso "Não são as cotas do município"). A tela ainda não mostra a origem: os chips de hoje já separam a faixa municipal
da estadual, que é tracejada e diz "Defesa Civil SC". Mostrar a origem é o PR 3.

**O que muda para quem olha a tela de Brusque:** nada, enquanto a leitura vier da DCSC-00019, que é o caso real. Só muda
no caso `leitura-de-outra-regua`: com uma leitura de outra régua, o cartão fica sem cor em vez de comparar com as cotas da
DCSC-00019.

**Entre o PR 2 e o PR 3, o mapa do Monitor seguiu a regra antiga.** Nesse caso, e só nele, o mapa do Monitor pintaria e
o cartão não. Isso não chegou a acontecer: a única leitura de Brusque é a DCSC-00019, porque o portal antigo de Itajaí saiu
do ar em 19/09. O PR 3 alinhou o mapa.

### Testes do PR 2

- **`data/classificacao-esperada.json`:** cada caso guarda agora a saída real do motor (`motor`), regerada por
  `python3 scripts/classificar_reguas.py --gabarito`. O `teste_classificar_reguas.py` reprova se ela estiver
  desatualizada.
- **`web/src/logica/classificacaoParidade.test.ts`:**
  - sem o arquivo do motor, o site dá o lado `site` (regra de sempre);
  - com o arquivo, o site dá o `esperado` nos 17 casos, inclusive na divergência declarada.
- **`web/src/dados/classificacao.test.ts`:** os portões (idade do arquivo, medições diferentes, cidade fora do piloto,
  envelhecimento depois da coleta, arquivo quebrado ou estranho, arquivo ausente).
- **Arquivos reais de produção (17h30 UTC de 07/10/2026):** o site usou o motor para Brusque (normal, municipal,
  DCSC-00019).
- **Navegador:** `/mirim/brusque` e `/mirim` abriram sem erro no console, com "Abaixo da atenção · 2,25 m".

## PR 3: a origem da cor no Monitor

O PR tem o rótulo `monitor-autorizado`.

- **O mapa segue o motor.** `construirCena` (`mapaMotor.ts`) recebe a classificação e passa por `faixasDoMotor`, com os
  mesmos portões dos cartões. Com isso, o mapa do Monitor e o cartão nunca pintam Brusque diferente. Isso vale só ao
  vivo: na reprodução a cor é do instante passado, e o motor só fala da coleta de agora. Cada pino carrega
  `classificadaPor` e `origemDoMotor`.
- **O painel diz quem pintou** (`textoDaOrigemDaCor`, em `textosDoPainel.ts`), no bloco completo — o do computador e o
  expandido do celular:
  - pelo motor, municipal: *"Cor do rio: classificação municipal — Ponte Estaiada – DCSC (DCSC-00019)."*;
  - pelo motor, estadual: *"Cor do rio: classificação estadual (Defesa Civil de SC) — DCSC-00019. Não representa as cotas
    municipais."*;
  - pela regra de sempre, só o tipo: *"Cor do rio: classificação municipal — cotas da cidade."* (o site não confere ali
    a identidade da régua, e o texto não afirma mais do que a conta fez), ou a estadual com o código da estação;
  - cinza ou várias réguas: nenhuma linha. O "Por que está cinza?" já explica.
- **A geometria não muda.** A trava do Monitor passou sem regravar o baseline.
- **Testes** (`logica/classificacaoNoMapa.test.ts`):
  - mapa e cartão pintam igual nos 17 casos do gabarito;
  - leitura de outra régua: o mapa pinta pela regra antiga e fica cinza com o motor;
  - estadual tracejada, com o aviso;
  - o painel nomeia a régua;
  - na reprodução, o motor não entra;
  - pela regra de sempre, o painel diz só o tipo.
- **Navegador**, com os arquivos de produção das 17h45 UTC: `/monitor/brusque` em 1280 e 390 px mostrou "Cor do rio:
  classificação municipal — Ponte Estaiada – DCSC (DCSC-00019).", sem erro no console.

**O que ainda segue a regra antiga:** o mapa do rio fora do Monitor (`MapaRios`, na tela do rio). Ele não lê a rede
estadual, então não tem como passar pelo portão das medições. A diferença só apareceria no caso `leitura-de-outra-regua`,
que hoje não acontece.

## Depois do deploy, na VPS

```bash
cd /opt/enchentes-vale-itajai
python3 scripts/classificar_reguas.py            # imprime Brusque: municipal, estadual e quem pinta
ls -l data/tempo-real/ultimo_classificacao.json  # regravado a cada publicação (15 min)
```

No branch `tempo-real`, o `ultimo_classificacao.json` passa a ir junto com o `ultimo.json`. Se ele faltar, o
`/var/log/niveis.log` mostra o motivo (linha "aviso: classificação estadual × municipal não gerada" ou "ERRO:
classificação recusada").

## Fora destes PRs

- **Conversões entre réguas** (§4 do plano): não há vínculo oficial cadastrado. Quando houver, entram como dado auditável,
  com testes próprios.
- **Comparação numérica do lado estadual**: fica fora por decisão de 07/10/2026.
- **Outras cidades no motor:** dependem das duas decisões do Jefferson listadas no README (campo da régua das cotas
  por código; Rio dos Cedros com `cotas_verificado: false`).
