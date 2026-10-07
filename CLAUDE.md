# CLAUDE.md — Enchentes do Vale do Itajaí

Guia para o Claude Code trabalhar neste repositório. Leia inteiro antes de codificar.

## O que é o projeto

Site que mostra dados históricos de enchentes nos rios **Itajaí-Açu** e **Itajaí-Mirim** (Santa Catarina, Brasil), com:

- nível do rio em cada cidade ao longo do curso (montante → jusante);
- previsão empírica do nível na próxima cidade a jusante;
- tempo estimado de chegada da cheia;
- painel especial para **Itajaí**, na foz, que recebe os dois rios e sofre influência da maré.

Público: moradores da região (Itajaí, Navegantes, Blumenau, Brusque…) sem formação técnica. Textos em **português do Brasil**.

**Não é um sistema oficial de alerta.** Toda tela deve trazer aviso de que não substitui o AlertaBlu, a Defesa Civil de SC e as Defesas Civis municipais (emergência: 199).

## Estrutura do repositório

```
data/
  estacoes.json   cidades por rio, ordem, códigos ANA, cotas de referência, URLs de tempo real
  enchentes.json  picos históricos: um registro por (evento, cidade), com fonte e confiança
  transito.json   tempo que a cheia leva para descer entre cidades
  eventos-pendentes-regua.json  números sem régua declarada — fora da série (ver regra abaixo)
scripts/          Python 3.11+ — coleta (ANA, Defesa Civil) e cálculo de correlações
web/              React + Vite + TypeScript — o site
```

Os JSONs em `data/` são a **fonte de verdade**. O site lê deles; scripts escrevem neles.

## Stack e convenções

### web/
- React 18 + Vite + TypeScript (strict).
- Roteamento: `react-router-dom`.
- Gráficos: `recharts`.
- Mapa: o **diagrama linear** do rio (cidades em sequência) e o **mapa do rio** (um `<canvas>` próprio, traçado do OSM colorido por trecho + correnteza animada que corre mais rápido quanto mais alto o nível) já existem, no estilo Kikikuru — ver `docs/kikikuru.md` para o mapa dos componentes e as regras (cor = faixa, nunca metro; animação = nível, cinza não corre; fuso; série de 24 h). O **Leaflet** ficou só no **mapa de manchas** de Itajaí (`MapaManchas`), onde o fundo de ruas é essencial; o mapa do rio não o usa mais.
- Estilo: CSS Modules ou Tailwind, escolher um e manter. Mobile-first — a maioria dos usuários vai acessar pelo celular durante a chuva.
- Sem backend por enquanto: importar os JSONs de `../data` diretamente (configurar alias no Vite).
- Deploy alvo: GitHub Pages ou Vercel (build estático).

### scripts/
- Python 3.11+, `requests`, `pandas`.
- Cada script é idempotente e escreve em `data/` sem apagar registros existentes.
- Nunca commitar credenciais. Chaves da ANA via `.env` (já no `.gitignore`).

### Dados
- Cada cidade tem sua **própria régua**; nunca comparar metros entre cidades sem dizer isso na tela.
- Todo registro novo em `enchentes.json` precisa de `fonte` e `confianca` (`alta` = oficial/acadêmica, `media` = imprensa, `baixa` = compilação informal).
- Campos com `verificado: false` ou `null` significam "ainda não conferido na fonte oficial" — não inventar valores.
- Datas em ISO (`AAAA-MM-DD`); só o ano quando o dia é desconhecido.

### Picos históricos faltantes
- O inventário e o prompt para pesquisa externa ficam em `docs/PICOS-FALTANTES.md` (não inventar número; só cadastrar com original aberto).
- Em **26/09/2026** a busca das prioridades 1 (Ascurra e Guabiruba) achou candidatos **ainda fora** de `enchentes.json`. Originais/CSV em evidência local; nada entra no JSON sem abrir a fonte de novo e seguir as regras da §5 do doc. **Exceção, 02/10/2026:** Ascurra 01/09/2026 **entrou** (10,13 m às 05:10, hora de Brasília, `referencia: régua` = DCSC-00003) por decisão do Jefferson — a ND e a crista da DCSC concordam. Os outros quatro continuam fora.

| Cidade | Data | Pico | Régua | Fonte | Confiança |
|---|---|---|---|---|---|
| Ascurra | 01/09/2026 05:10 — **cadastrado 02/10/2026** | 10,13 m | DCSC-00003 Ponte do Beber | API `historic` DCSC + ND+ | alta |
| Ascurra | 12/09/2026 00:00 | 10,46 m | DCSC-00003 | API `historic` DCSC | alta |
| Guabiruba | 11/07/2026 14:40 | 2,14 m | DCSC-00029 | API `historic` DCSC | alta |
| Guabiruba | 31/08/2026 11:20 | 2,04 m | DCSC-00029 | API `historic` DCSC | alta |
| Guabiruba | 20/09/2026 06:30 | 1,96 m | DCSC-00029 | API DCSC + O Município | alta |

- **Não cadastrar ainda** as datas-alvo antigas (2008–2024) dessas cidades: a API não as cobre; `guabiruba.sc.gov.br/noticia-46906/` deu 403; SDE 006/2024 não lista Ascurra nem Guabiruba.
- Descartar: Travessa Zonta / Ribeirão São Paulo em Ascurra; Guabiruba em ~25 m ortométrica; lâmina d'água na rua.

### Eventos pendentes de identificação da régua — REGRA (decisão de 02/10/2026)
- `data/eventos-pendentes-regua.json` guarda números com fonte mas **sem régua declarada** em cidade cuja série tem referência
  conhecida (hoje: Gaspar 09/10/2023 e 09/09/2011; Indaial 04/10/2023, que **não** se vincula sozinho à DCSC-00006).
- Ficam **fora** de recordes, comparação com o nível atual, gráficos contínuos, modelos de propagação e calibração de trânsito.
  A garantia é ninguém ler o arquivo: site e bot não o importam, e `teste_validar_dados.py` trava isso.
- Migram para `enchentes.json` só quando a fonte identificar a régua ou permitir reconciliar os zeros, por decisão do Jefferson;
  migrar é **mover** (o validador acusa o mesmo evento nos dois arquivos).

### Cheias captadas pelo site — REGRA (07/10/2026)
- `data/eventos-captados.json` é **derivado**: `scripts/eventos_captados.py` o gera da série do coletor
  (`data/tempo-real/*.ndjson` na VPS, cópia semanal no branch `arquivo-series`; aqui, `--serie <pasta>`). Guarda, por
  régua, os episódios acima da cota de referência com a **maior leitura captada** e a hora dela, a maior lacuna e se
  o episódio já tem registro em `enchentes.json`.
- **Nunca entra em `enchentes.json` por esse caminho** (quem propõe registro é `extrair_picos.py`, com pessoa
  conferindo). O chat (15ª entrega) diz "a maior leitura que o site captou", nunca "pico", e "conferido e registrado"
  só quando `registro_em_enchentes` aponta um registro que existe — o validador cobra isso.
- Regras herdadas de `extrair_picos.py`: régua por `comum.regua_de`; cota da própria estação ou da cidade com uma
  publicação por vez; 18 h sem cheia separam episódios; o repasse de Blumenau (3 h atrasado) cede a hora ao
  AlertaBlu. Régua de estuário (`alerta_automatico: false`) não gera episódio; Ascurra e Gaspar ficam sem faixa.
- Regerar: `cd scripts && python3 eventos_captados.py --serie /caminho/tempo-real --gravar` depois de cada cheia
  (ou de cada cópia nova em `arquivo-series`).

### Qualidade do chat — REGRA (17ª entrega, 07/10/2026)
- `web/src/comandos/capacidades.ts` é o **catálogo único** dos passos do chat (`Record<Passo['tipo'], …>`): passo novo
  exige ficha com exemplos que o leitor entende (o teste roda cada um) e `mudaTela`/`precisaDoMapa` iguais aos
  conjuntos de `executar.ts`. `docs/CHAT-CAPACIDADES.md` é gerado — não editar à mão.
- Regras de extração de cidade, lista de cidades, cota, metros e mês moram em `comandos/entidades.ts`; leitor novo
  importa de lá, não copia.
- A bateria `comandos/avaliacao/` é a **linha de base** do handoff (`docs/HANDOFF-QUALIDADE-CHAT-2026-10-07.md`).
  Caso reprovado é achado: nunca ajustar o esperado para o número subir. Caso novo ou melhora → `npm run avaliar --
  --baseline` e commitar `baseline.json` junto com `docs/AVALIACAO-CHAT.md`. O teste trava zero ações indevidas,
  `dev` em 100 % e nenhum grupo abaixo da linha.
- Cada entrega que mexe no leitor acrescenta uma **família nova de frases reservadas** (`RESERVADOS_<n>` em `casos.ts`),
  escrita ANTES de rodar o leitor com elas, e o relatório diz quantas passaram na primeira rodada (18ª: 39/47) antes de
  corrigir. Esperado revisto é exceção documentada na seção da entrega, nunca ajuste silencioso.
- **Contexto da conversa (19ª):** `Contexto.cidadeAtual` é a tela; `cidadeDaConversa` (de `comandos/conversa.ts`) só
  vale sem cidade na tela, e a resposta diz "Pela conversa, entendi que é de X". Dita > tela > conversa. Continuação
  ("e Gaspar?") que mudaria a tela **confirma** antes (`decidirContinuacao`); a que só responde refaz com "Entendi como".
- O chat **não altera dados** (`pedeAlteracaoDeDado`), não abre endereço digitado e, com só o nome da cidade, pergunta
  o que a pessoa quer; o motor só palpita "maiores cheias" quando a pergunta fala do rio (`FALA_DO_RIO`).
- O piloto do classificador, listas de permissão, segredos, retenção e público **não** mudam em PR de refatoração.

### Ruas alagadas registradas à mão — REGRA (decisão de 05/10/2026)
- `data/ruas-alagadas.json` guarda a hora em que cada rua alagou, anotada durante a cheia (planilha
  `docs/modelos/ruas-alagadas.csv` → `scripts/ruas_alagadas.py`). Passo a passo: `docs/REGISTRO-RUAS-ALAGADAS.md`.
- `quando` é hora de Brasília sem fuso. `quando_e` separa `hora_do_fato` de `hora_da_publicacao`; esta última é
  limite (a água chegou antes), nunca o momento.
- Confiança com teto pelo tipo de fonte: relato é sempre `baixa`, e foto/vídeo no máximo `media`.
- Sem nome, telefone ou e-mail de morador.
- A importação só acrescenta.
- Não é alerta e não vai para a tela. Usa-se só na conta `nivel_antes.py --registradas`.
- As regras moram em `ruas_alagadas.validar`, que o `validar_dados.py` também chama.

### Maré medida do CIRAM — REGRA (decisão de 07/10/2026)
- Coleta a cada publicação (`coleta_mare_ciram.py --publicar`, uma consulta), arquivo `ultimo_mare_medida.json`,
  painel "Maré medida perto da foz" em `/itajai`. Detalhes em `docs/MARE-MEDIDA-CIRAM.md`.
- Número só com horário, estação, unidade e **referência vertical** identificados. Hoje a referência está pendente
  (`REFERENCIA_VERTICAL` vazio, teste trava): a tela diz "referência pendente", sem número. Entrada nova só com a
  fonte escrita, por decisão do Jefferson.
- A diferença se chama **"diferença entre nível observado e maré astronômica prevista"**, vem da mesma linha da mesma
  estação e nunca é atribuída só a vento e pressão (pode ter influência do rio). Nunca "maré meteorológica" na tela.
- Leitura antiga nunca como atual: medição com mais de 60 min ou do futuro é "Medição indisponível". A tábua da
  Marinha continua sendo a previsão, com fonte e horário à parte.

### Fuso dos carimbos de tempo real — REGRA (aprendida em 01/09/2026)
- **`medido_em` sem fuso = horário de Brasília (America/Sao_Paulo).** É o que a página da
  Defesa Civil de Itajaí publica, e o sistema inteiro já concorda nisso: `coleta_itajai.py`
  **grava** local, o site lê com `deBrasilia()` (com teste travando), o vigia lê com `FUSO`.
  Toda fonte nova de nível/chuva grava `medido_em` no MESMO horário de Brasília, sem fuso.
- **"A página publica em Brasília" não vale para tudo o que ela republica (03/10/2026).** Na página antiga da
  Defesa Civil de Itajaí, as réguas DC vinham em Brasília, mas a publicação **"Blumenau"** vinha **3 h atrasada**:
  na mesma coleta de 01/09, as DC marcavam 15h00, o AlertaBlu 15h00 e ela 12h05 (`docs/ANALISE-CHEGADA-ITAJAI-2026.md`,
  seção 3). Ela saiu do ar em 19/09. O portal novo publica em UTC com offset, e `coleta_itajai_portal.py`
  converte. Regra: antes de confiar no carimbo de uma estação republicada, comparar com outra fonte da mesma
  régua.
- **Blumenau de 5 min (PADKND, portal de Itajaí `?municipio_id=3`):** publicação `Blumenau (PADKND)` com
  `resgate_de: "Blumenau"`. Só entra se bater, na mesma coleta, com o AlertaBlu nas horas cheias em comum
  (`coleta_itajai_portal.conferir_com_alertablu`). O título `Blumenau` é reservado ao repasse antigo 3 h atrasado.
- **`coletado_em` é UTC** (campo diferente, do momento da coleta) — não confundir os dois.
  Uma fonte de resgate (AlertaBlu) gravou UTC "para honrar o contrato" e leu o comentário do
  `coletado_em` por engano: o vigia passou a ver a leitura como 2h no futuro. Custou uma sessão.
- Padronizar tudo em UTC é possível, mas **não é troca de uma linha**: teria que mudar junto o
  `coleta_itajai.py`, o `deBrasilia()` do site (e seu teste), o vigia e a série histórica. Fica
  como refatoração deliberada e testada — nunca no meio de uma cheia, porque mexe na idade da
  leitura que o morador vê na tela.
- Régua com fonte de resgate (primária + backup) marca a leitura de backup com
  `resgate_de: "<título da primária>"`. O vigia (`saude_coleta.regua_de`) junta as duas como UMA
  régua por esse campo — viva se qualquer das duas está fresca —, sem mascarar as réguas
  distintas de uma cidade com várias (Itajaí tem onze).

### Posição das réguas no mapa — REGRA (decisões de 06/10/2026)
- O pino de cada cidade fica na `coordenadas` dela, sem encaixe no traçado (`pontoDoPino`). A câmera centra no pino.
- **Blumenau:** a coordenada é a da régua da Ponte Adolfo Konder, Beira-Rio (−26,9186, −49,0656), confirmada pela
  Prefeitura (`coordenadas_fonte`). A DCSC-00026 de Blumenau é de chuva: fica em `codigo_dcsc` só para a chuva.
- **Estação estadual perto não é a régua da cidade.** Timbó, Trombudo Central e Lontras têm
  `equivalencia_estadual.status: "não confirmada"`.
  - **Rio dos Cedros: confirmada em 07/10/2026** (decisão do Jefferson): a COMPDEC respondeu ao C29 que a cidade tem
    uma única estação de nível, na ponte próxima ao Paço — a DCSC-00011, que agora está em `codigo_dcsc`, pinta pelas
    cotas da cidade (`REGUAS_COM_COTA_PROPRIA`) e leva o pino. O pico de 8,96 m de 2014 passou a 09/06/2014 00:45.
  - Fica "não confirmada" até existir documento, código comum ou comparação de referência/zero da régua (decisão fechada em 06/10/2026). Proximidade não basta.
  - O validador reprova o código em `codigo_dcsc` sem a confirmação, e "confirmada" sem `fonte`.
- Inventário em `docs/INVENTARIO-REGUAS.md` (`scripts/inventario_reguas.py --gravar`). Relatório em
  `docs/AUDITORIA-REGUAS-2026-10-06.md`.

### Cor dos cursos fora do tronco — REGRA (07/10/2026, com `monitor-autorizado`)
- Curso fora do tronco só ganha cor por **vínculo explícito** em `web/src/logica/vinculosDosTracados.ts`
  (`VINCULOS`): cidade, grupo dos dados, estação e alcance. O alcance vai da estação até a confluência ou a próxima
  estação rio abaixo, pelo caminho no próprio traçado. Sem vínculo, o curso fica cinza com o motivo em `SEM_VINCULO`.
- A cor do trecho é a **mesma decisão do pino**: nenhuma faixa calculada aqui. Faixa estadual continua tracejada e
  parada. Na reprodução, sem classificação estadual histórica, o trecho fica cinza.
- No tronco, a primeira régua **não pinta o rio acima dela** (folga de 0,5 km).
- Vínculo novo exige estação identificada pelo cadastro (código) e caminho no traçado. Proximidade não basta (Timbó
  segue sem vínculo). Auditoria em `docs/VINCULOS-DOS-TRACADOS.md`.

### Classificação estadual × municipal — REGRA (decisões de 07/10/2026)
- Duas classificações **independentes** por cidade. O motor é `scripts/classificar_reguas.py`; o relatório está em
  `docs/CLASSIFICACAO-ESTADUAL-MUNICIPAL.md`.
- Migração em três PRs separados, nesta ordem:
  1. Python em paralelo: grava `data/tempo-real/ultimo_classificacao.json` (#510, em produção).
  2. Consumo pelo site: `dados/classificacao.ts` e `estadoDaCidade`, fora do Monitor. O site só segue o motor com o arquivo
     desta coleta (≤ 30 min), a cidade no arquivo e as **mesmas** medições da tela. A idade é refeita no relógio de agora.
     Senão, vale a regra de sempre.
  3. Origem da cor no Monitor (`monitor-autorizado`). `construirCena` passa pelos mesmos portões (só ao vivo, nunca na
     reprodução), e o painel diz "Cor do rio: classificação municipal/estadual — régua" (`textoDaOrigemDaCor`). Pela
     regra de sempre, a linha diz só o tipo, sem nomear régua.
- **O motor só LÊ `estacoes.json`.** Campo novo depende de proposta e aprovação do Jefferson.
- **Faixa estadual = a que a Defesa Civil de SC publica** (`rio_alarmes`, `classificar_alarmes`). Comparação numérica
  com limites por estação fica fora até haver limites oficiais e referência de régua validada.
- **Régua da leitura = régua das faixas**, por código; proximidade e título parecido não contam. Conversão entre
  réguas só com vínculo oficial, fórmula e fonte (nenhum cadastrado).
- **`regua_das_cotas_id` (campo aprovado pelo Jefferson em 07/10/2026):** `{codigo, fonte}`.
  - `codigo` é a identidade que a leitura carrega (`codigo` ou o título por `comum.regua_de`); `fonte` aponta a prova.
  - Está em Brusque, Ascurra, Rio dos Cedros, Rio do Sul, Blumenau e Gaspar.
  - Valor novo só com a prova escrita, por decisão do Jefferson. O validador cobra a coerência com `codigo_dcsc` e
    `REGUAS_COM_COTA_PROPRIA`.
- **A municipal manda.** A estadual pinta só sem leitura municipal de agora, como `fallback`, com aviso.
- **A saída diz a faixa, não a cor** (token do site).
- **Piloto (`CIDADES_PILOTO`): Brusque, Blumenau e Rio dos Cedros** (decisões do Jefferson de 07/10/2026). Cidade nova
  entra com o `--inventario` limpo e com casos no gabarito.
  - **Blumenau:** só pinta pelas publicações com referência validada (`PUBLICACOES_VALIDADAS`): o AlertaBlu e a PADKND
    conferida. O repasse antigo "Blumenau" não pinta pelas cotas.
  - **Rio dos Cedros** (`PILOTO_SEM_MUNICIPAL`): sem classificação municipal até a COMPDEC confirmar as cotas, sem exceção.
    - A faixa estadual válida aparece como "faixa estadual".
    - Sem ela, fica cinza: falta de cota municipal não é nível normal.
    - Nada compara o nível com as cotas não confirmadas (frase, medidor e quadro de cota).
  - **Brusque:** cor inalterada.
- **A municipal só segura a estadual com cotas confirmadas** (`segura_estadual`). A origem estadual se chama "faixa
  estadual" no motor, no painel e no cartão.
- **Gabarito:** `data/classificacao-esperada.json` trava motor e site juntos (`teste_classificar_reguas.py` e
  `classificacaoParidade.test.ts`). Divergência só declarada em `diverge_do_site`; esperado revisto é decisão, nunca
  ajuste para passar.

### Referência altimétrica de Blumenau — REGRA BLOQUEANTE (conversão parcial em 03/10/2026)
- Três referências para a régua da Ponte Adolfo Konder, pela FURB (Prof. Ademar Cordero, e-mails e
  planilha de 02/10/2026): **régua antiga** (até a troca, depois da cheia de set/2011); **zero do IBGE**
  = régua antiga + 0,20 m (Tabela 4 de Cordero & Medeiros, 1852–2001); **GPS = régua de hoje** =
  IBGE + 0,20 m = régua antiga + 0,40 m. A régua de hoje é a da Defesa Civil/AlertaBlu e da leitura
  ao vivo. Set/2011 nas três: 12,60 · 12,80 · 13,00 m. No rótulo `"IBGE (régua + 0,20 m)"`, "régua"
  é a ANTIGA.
- **Conversão parcial aplicada em 03/10/2026, por decisão do Jefferson** (`scripts/converter_blumenau.py
  --aplicar`, relatório em `docs/CONVERSAO-BLUMENAU.md`): os **57** registros de certeza alta estão na
  régua de hoje, com `pico_publicado_m`, `referencia_publicada` e `conversao` guardando como foram
  publicados. Ficaram como estavam **67**: 60 de 1929–1983 em que a Tabela 4 e a planilha do Cordero
  discordam em ~0,20–0,30 m, 4 inferidos sem par na lista do AlertaBlu e 3 pendentes (janela da troca
  em 2013; 12/07/2026 sem régua). **Sem mais perguntas ao Prof. Cordero** (decisão de 03/10/2026).
  Depois, também em 03/10/2026, entraram cinco cheias da planilha: quatro de jul–ago/1983 com `referencia: null`
  (trecho em disputa) e 08/10/2023 na régua; 26/05/2010 virou divergência de 26/04/2010.
- Enquanto `data/enchentes.json._meta.REGRA_REFERENCIA_BLUMENAU` existir:
  1. `referencia` é rótulo do registro, com conjunto fechado: `"régua"` (a de hoje),
     `"IBGE (régua + 0,20 m)"` ou `null`. Hipóteses vão em `referencia_hipotese` ou `nota`,
     nunca no campo `referencia`. O validador rejeita registro sem o campo.
  2. Conflito de valor para o mesmo (cidade, evento) usa o mecanismo `divergencias`:
     um valor adotado, os demais guardados com fonte e referência. Não criar dois registros
     para o mesmo evento; `agruparEmEventos` não deve escolher por magnitude. Em registro
     convertido, as divergências ficam **como publicadas**, com `referencia_publicada`.
  3. Conversão só pelo `converter_blumenau.py`, que guarda o valor publicado e não converte o que
     estiver em disputa, inferido ou pendente. **Nenhuma conversão à mão.** O validador refaz a conta
     de todo registro convertido (`valida_conversoes`). A UI exibe a referência de cada ponto, o valor
     como foi publicado e avisa quando o gráfico mistura referências.
  4. Busca "minha rua", simulador, painel "quanto falta" e bot usam somente nível em `régua`. Numa
     cidade com mistura, entram só os picos de régua e a tela diz quantos ficaram de fora — o IBGE e o
     `null` nunca entram na conta. Há teste que trava isso.
  5. Previsão a jusante pareia igual com igual: montante e jusante na mesma referência.
     Se só houver série IBGE no montante, documentar o deslocamento e não parear com
     jusante em régua.
- Remoção da regra: quando os 67 restantes forem resolvidos (desempate da Tabela 4 × planilha em
  1929–1983, data da troca para 2013, régua de 12/07/2026). Pelo lado da ANA, só uma fonte com o pico
  instantâneo da régua da 83800002 — a média diária não decide.

## Telas

1. `/acu` — **Itajaí-Açu** (ÁRVORE, não fila — ver `docs/TOPOLOGIA-CANONICA.md`): cabeceiras paralelas **Taió** (Oeste) ‖ **Ituporanga** (Sul) → tronco **Rio do Sul → Lontras → Ascurra → Indaial → Blumenau → Gaspar → Ilhota → Itajaí**; **Ibirama** (Rio Hercílio), **Timbó** (Rio Benedito) e **Rio dos Cedros** são afluentes laterais, não elos do tronco. **Trombudo Central** entrou sem posição na árvore (a fonte diz o rio, não a confluência) e a tela a mostra em "Outros pontos". `ordem` é `null` no Açu; a posição vem de `ramo` + `ordem_no_ramo`. O validador (`scripts/validar_dados.py`) aborta se a fila global voltar.
2. `/mirim` — **Itajaí-Mirim** (ÁRVORE desde 04/10/2026): tronco **Vidal Ramos → Botuverá → Brusque → Itajaí**; **Guabiruba** é afluente lateral (ribeirão Guabiruba, entra perto de Brusque), não elo do tronco. A DCSC-00029 é lida no **zero local**; valor ≥ 10 m continua suspeito (`SUSPEITA_SO_ACIMA_DE_M`).
3. `/itajai` — **Itajaí (foz)**: chegada dos dois picos + maré
4. `/` — início: **Minha cidade** (escolhida no aparelho) com o cartão "Agora", a cidade de cima do rio e as outras que a pessoa segue; abaixo, a escolha do rio.
5. `/:rio/:cidade` — página da cidade em abas: **Agora · Minha rua · Histórico · Fontes** (`?aba=rua|historico|fontes`).

Cada tela de rio mostra (versão 2): a lista compacta das cidades, agrupada em cabeceiras, tronco e afluentes, com faixa, número, tendência e idade; o tempo de descida só entre cidades do tronco; o mapa do rio sob pedido no celular; a reprodução das últimas horas; a busca "minha rua" por cidade. Os picos históricos de cada cidade ficam na aba Histórico dela.

### Versão 2 das telas — REGRAS (decisões D1–D7 de 03/10/2026)
- **O Monitor não muda.** `/monitor*` e `/municipal/ascurra*` mantêm a casca antiga (`cascaAntiga` em `App.tsx`, opção ③ da D2): o mapa soma à mão a altura dessa casca (`calc(100vh - 8.5rem)`). `testes-navegador/trava-monitor.mjs` compara a geometria do mapa com `baseline-monitor.json`, e a CI reprova PR que altere arquivos do Monitor sem o rótulo `monitor-autorizado`. Refazer o baseline é decisão do Jefferson.
  - **Exceção autorizada (07/10/2026): o redesenho do Monitor no celular**, em três etapas e PRs separados com o
    rótulo `monitor-autorizado` — `docs/REDESENHO-MONITOR-MOBILE-2026-10-07.md`. A casca antiga continua nas rotas
    do Monitor, mas em ≤ 700 px ela é compacta (faixa do 199 numa linha, cabeçalho com menu ☰ no lugar das abas) e o
    mapa mede `calc(100dvh - 5.875rem - 3.5rem)` (etapa 3: a barra Mapa · Réguas · Perguntar fica no fluxo, colada embaixo
    do mapa, nunca `fixed` — regra 6 da trava); no computador nada da casca muda. O baseline da trava é regravado em cada
    etapa, com a data no commit. **Nenhuma etapa é mergeada nem vai para produção sem o Jefferson dizer.**
- **D1 — aviso:** a regra de "toda tela traz o aviso" continua. A faixa presa no topo diz *"Emergência: 199 · não substitui a Defesa Civil"*; o texto completo (`AvisoLegal`) abre numa folha na primeira visita (sai só com "Entendi"; volta se o aparelho não lembrar) e fica no fim de toda página.
- **D3:** a "marca antiga mais próxima acima" (`PainelCenarioAnterior`) fica só na aba Histórico — perto do nível de agora, soaria previsão.
- **D4:** o texto do WhatsApp não leva endereço do site (está atrás do Cloudflare Access); só monta com leitura que não é velha, com a hora da medição, sem ordem de ação.
- **D6:** o chip da faixa usa o nome da Defesa Civil da cidade (`cotas_nomes_na_fonte`: "Alerta Máximo" em Blumenau, "Prontidão" em Ilhota). Muda o nome, nunca a cor nem a posição na escada.
- **D7:** a seta de tendência só aparece quando o último ponto da série É a leitura mostrada e é de agora (`tendenciaDaLeitura`); senão some.
- **Frases do cartão "Agora"** (`logica/agora.ts`): só com leitura de agora e cota de acionamento; nunca em Gaspar (legenda "maior que"), Ascurra (C18) nem Itajaí (várias réguas). Sem dado, a frase não aparece.
- **Tema escuro e letra maior** só dentro de `:root[data-app]`, que o App liga fora do Monitor. Cores novas vão como token em `global.css`, com o valor claro igual ao antigo.
- **Preferências** (minha cidade, aviso lido, letra) só no aparelho, por `logica/preferencias.ts`, sempre em try/catch.
- **Faixa da Defesa Civil de SC (03/10/2026):**
  - **Quando aparece:** só na cidade sem leitura municipal de agora, e só a faixa que a própria DCSC publica para
    a estação (`rio_alarmes`). Vale no cartão, nas listas e nas linhas de cidade.
  - **Como aparece:** chip tracejado "Atenção · Defesa Civil SC" e o número da rede estadual, com "zero
    próprio" escrito.
  - **Onde fica:** em `EstadoDaCidade.faixaEstadual`, nunca em `faixa`. Frase, WhatsApp e aviso não a leem.
    Teste em `dados/usarAoVivo.test.ts`.
  - **Réguas estaduais que pintam com as cotas da cidade:** só as de `REGUAS_COM_COTA_PROPRIA` em
    `scripts/coleta_estadual_com_cota.py`. Hoje são DCSC-00003 (Ascurra), DCSC-00019 (Brusque) e DCSC-00011
    (Rio dos Cedros, desde 07/10/2026).
- **D5 — modo aplicativo (PWA):** `web/public/sw.js` + `sw-regras.js` (testado em `src/logica/swRegras.test.ts`
  e no navegador por `testes-navegador/pwa.mjs`). Rede primeiro para a página e o nível ao vivo; a cópia
  guardada só sem rede, e o número guardado sai com a hora da medição. **Nunca guardar** desvio, resposta
  opaca, `*.cloudflareaccess.com` nem HTML no lugar de JS/JSON (é a tela de login do Access). Manifesto com
  `crossorigin="use-credentials"`. Interruptor em `web/public/pwa.json` (`"ativo": false` desliga e apaga
  tudo nos aparelhos). Os outros testes de navegador rodam com `serviceWorkers: 'block'`. Operação em
  `docs/PUBLICACAO-E-ACESSO.md`, "Modo aplicativo".

## Lógica de previsão (v1 — empírica)

- Previsão a jusante = correlação linear entre picos históricos da cidade de cima e da cidade de baixo no mesmo evento (`enchentes.json`).
- Tempo de chegada = faixa de `transito.json`; mostrar sempre como **intervalo** ("14–17 h"), nunca número exato.
- Quando não houver pares suficientes (< 5 eventos), exibir "dados insuficientes" em vez de estimar.
- Para Itajaí: considerar os dois rios e mostrar o estado da maré no horário previsto de chegada de cada pico. Fonte de maré: tábuas da Marinha (DHN), porto de Itajaí — integração futura.

## Fontes externas

| Fonte | Uso | Observação |
|---|---|---|
| ANA / HidroWeb (SNIRH) | séries históricas de cota | API nova exige cadastro por e-mail (hidro@ana.gov.br) |
| Defesa Civil SC — monitoramento.defesacivil.sc.gov.br | tempo real + histórico curto | GraphQL `historic` (MIN_10 / HOUR_1); janela móvel ~89 dias. Ascurra = DCSC-00003 (Ponte do Beber); Guabiruba = DCSC-00029 (zero local, **não** a cota ortométrica ~25 m dos boletins de Brusque). |
| AlertaBlu (Blumenau) | tempo real + cotas de ruas | |
| Defesa Civil de Itajaí | tempo real Açu, Mirim e ribeirões | |
| CEOPS/FURB (ceops.furb.br) | acervo histórico de picos | centro desativado em 2022; só acervo |

Respeitar rate limits e identificar o `User-Agent` com o nome do projeto em todos os scripts.

### E-mails e ofícios — REGRA (decisão de 02/10/2026)
- **Nunca colocar link do site** (GitHub Pages, `pages.dev` ou pré-visualização) em e-mail ou ofício. O site tem
  acesso restrito e só abre para e-mail cadastrado. Quem recebe um link sem cadastro encontra a tela fechada.
- No lugar do link, escrever que, **se a pessoa quiser ver o site, basta mandar o e-mail dela para cadastro**.
- Origem: o agradecimento ao Prof. Cordero (C25, 02/10/2026) saiu com o link, e o site não abriu para ele.

## Ordem de trabalho sugerida

1. `web/`: scaffold Vite + rotas + leitura dos JSONs + tela `/acu` com diagrama linear e gráfico de picos.
2. Tela `/mirim` reaproveitando os mesmos componentes.
3. Tela `/itajai` com os dois cronômetros de chegada.
4. `scripts/ana_hidroweb.py`: baixar séries das estações com `codigo_ana` preenchido.
5. `scripts/calibrar_transito.py`: calcular tempos reais a partir de horários de pico.
6. Integração de tempo real (Defesa Civil / AlertaBlu).

## Ao terminar uma tarefa

- Rodar `npm run build` em `web/` e garantir zero erros de tipo.
- Validar os JSONs (`python3 -c "import json; json.load(open('data/enchentes.json'))"` etc.).
- Atualizar a seção **Pendências** do `README.md` se algo foi concluído ou descoberto.
- Commits em português, no imperativo: "Adiciona tela do Itajaí-Mirim".
