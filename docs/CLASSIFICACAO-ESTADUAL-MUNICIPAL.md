# Classificação estadual × municipal (07/10/2026)

O plano está em `PLANO_BACKEND_CLASSIFICACAO_ESTADUAL_MUNICIPAL.md`, enviado pelo Jefferson em 07/10/2026. O trabalho foi
dividido em três PRs, começando depois da decisão sobre os PRs #504–#509, que foram todos mergeados:

1. **PR 1 (#510, mergeado).** O motor Python gera o estado em paralelo, e o site não muda o que consome. Em produção
   desde a coleta das 17h30 UTC de 07/10/2026.
2. **PR 2.** O site passa a seguir o estado (`ultimo_classificacao.json`) nas telas que usam `estadoDaCidade` — ver
   a seção "PR 2" abaixo.
3. O Monitor passa a dizer qual classificação deu a cor.

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
   - Hoje, o único caminho provado é o da estação estadual que é a própria régua das cotas: o código precisa estar em
     `codigo_dcsc` da cidade **e** em `REGUAS_COM_COTA_PROPRIA` apontando para ela. Se as duas fontes discordarem, a
     cidade fica sem classificação.
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
   - sem `regua_das_cotas_fonte`;
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

Saída de `python3 scripts/classificar_reguas.py --inventario` em 07/10/2026:

| Cidade | Bloqueios |
|---|---|
| `itajai-acu/taio` | régua das cotas sem código; sem `regua_das_cotas_fonte`; `cotas_verificado` ≠ true |
| `itajai-acu/ituporanga` | sem cota de acionamento; régua das cotas sem código; sem `regua_das_cotas_fonte`; `cotas_verificado` ≠ true |
| `itajai-acu/rio-do-sul` | régua das cotas sem código; `cotas_verificado` ≠ true |
| `itajai-acu/ibirama` | sem cota de acionamento; régua das cotas sem código; `cotas_verificado` ≠ true |
| `itajai-acu/lontras` | sem cota de acionamento; régua das cotas sem código; sem `regua_das_cotas_fonte`; `cotas_verificado` ≠ true |
| `itajai-acu/apiuna` | sem cota de acionamento; régua das cotas sem código; sem `regua_das_cotas_fonte`; `cotas_verificado` ≠ true |
| `itajai-acu/ascurra` | comparador especial (C18) |
| `itajai-acu/indaial` | régua das cotas sem código; sem `regua_das_cotas_fonte` |
| `itajai-acu/blumenau` | régua das cotas sem código; sem `regua_das_cotas_fonte` |
| `itajai-acu/gaspar` | comparador especial (estação 21, "maior que"); régua das cotas sem código; sem `regua_das_cotas_fonte` |
| `itajai-acu/ilhota` | régua das cotas sem código; sem `regua_das_cotas_fonte`; `cotas_verificado` ≠ true |
| `itajai-acu/itajai` | sem cota de acionamento; régua das cotas sem código; sem `regua_das_cotas_fonte`; `cotas_verificado` ≠ true |
| `itajai-acu/timbo` | sem cota de acionamento; régua das cotas sem código; sem `regua_das_cotas_fonte`; `cotas_verificado` ≠ true |
| `itajai-acu/rio-dos-cedros` | `cotas_verificado` ≠ true |
| `itajai-acu/trombudo-central` | sem cota de acionamento; régua das cotas sem código; sem `regua_das_cotas_fonte`; `cotas_verificado` ≠ true |
| `itajai-mirim/vidal-ramos` | sem cota de acionamento; régua das cotas sem código; sem `regua_das_cotas_fonte`; `cotas_verificado` ≠ true |
| `itajai-mirim/botuvera` | sem cota de acionamento; régua das cotas sem código; sem `regua_das_cotas_fonte`; `cotas_verificado` ≠ true |
| `itajai-mirim/guabiruba` | sem cota de acionamento; régua das cotas sem código; sem `regua_das_cotas_fonte`; `cotas_verificado` ≠ true |
| `itajai-mirim/brusque` | **pode entrar** (piloto) |
| `itajai-mirim/itajai` | sem cota de acionamento; régua das cotas sem código; sem `regua_das_cotas_fonte`; `cotas_verificado` ≠ true |

### Como ler os bloqueios

- **"régua das cotas sem código"** é limite do motor, não falta da cidade. Blumenau, Indaial, Rio do Sul, Taió e outras
  leem a régua municipal por título de publicação (AlertaBlu, portal de Itajaí, Asthon), e o `estacoes.json` não tem um
  campo que diga, sem ambiguidade, qual título é a régua das cotas. O `regua_das_cotas` é texto livre. Resolver isso
  exige um campo novo, e **campo novo depende de proposta e aprovação do Jefferson**. Fica como proposta para o PR em que
  a próxima cidade entrar.
- **"`cotas_verificado` ≠ true"** em Rio dos Cedros é coerente com a resposta ao C29: a COMPDEC não falou do zero nem da
  vigência da escala depois do desassoreamento. Hoje o site pinta Rio dos Cedros mesmo assim; quando ela entrar no motor,
  ficará sem cor municipal até essa confirmação. É uma decisão a tomar junto com o PR 2.
- **Comparador especial**: Ascurra e Gaspar precisam ter a regra transcrita com o mesmo comparador da fonte, e um caso
  no gabarito, antes de entrar.

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

**Até o PR 3, o mapa do Monitor ainda segue a regra antiga.** Nesse caso, e só nele, o mapa do Monitor pintaria e o cartão
não. Hoje não acontece: a única leitura de Brusque é a DCSC-00019, porque o portal antigo de Itajaí saiu do ar em 19/09.

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
- **Origem da cor no Monitor (PR 3).** O PR 3 mexe em arquivos do Monitor e precisa do rótulo
  `monitor-autorizado`.
