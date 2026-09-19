# Auditoria dos dados — Enchentes do Vale do Itajaí

Data: 19/09/2026. Conferência principal entre 12h46 e 13h05, horário de Brasília.

Site: https://enchentes.premercadosc.com/

Repositório: https://github.com/haohmarusc-glitch/enchentes-vale-itajai

Revisão auditada: `8481a0e3e99e6ab5a5c65cfc53af1a7636b03ef3`, main de 18/09/2026 às 21:27:50 UTC.

## Veredito

**Parcialmente correto. Os níveis recentes amostrados correspondem às fontes, mas há perda de cobertura e afirmações incorretas ou insuficientemente qualificadas na interface. Não é possível aprovar o conjunto como inteiramente correto.**

A falha mais importante é de integração: o portal de Itajaí mudou e o coletor consulta o endereço antigo. As onze réguas municipais continuam disponíveis no novo portal, mas estão ausentes do arquivo consumido pelo site.

Nenhum código do produto, dado de produção ou configuração da VPS foi alterado nesta auditoria. A cópia local contém somente os registros da investigação e este relatório como arquivos adicionais.

## Método e limites

- Site publicado inspecionado no Chrome do PC, após autenticação normal no Cloudflare: início, monitor, Blumenau, Ascurra, Rio do Sul, Taió, Indaial, Gaspar, Brusque, Vidal Ramos, Ilhota e Itajaí.
- Inspeção visual do mapa regional e leitura dos textos, níveis, datas, séries e simuladores dessas páginas.
- Downloads dos quatro arquivos publicados no branch `tempo-real`: `ultimo.json`, `ultimo_nivel_sc.json`, `ultimo_barragens.json` e `serie-recente.json`.
- Consultas diretas às fontes AlertaBlu, Asthon, Taió e Defesa Civil estadual. Consulta ao portal municipal de Gaspar e aos portais antigo e novo de Itajaí pelo Chrome.
- Revisão dos coletores, seleção de réguas, tratamento de idade, série recente, simulador de ruas e textos hidráulicos.
- Os dados mudam durante a auditoria. Diferenças entre medições de horários distintos não foram tratadas automaticamente como erro.
- Não houve aferição física dos sensores, inspeção da VPS nem validação individual de todas as cotas de rua, polígonos e picos históricos. A auditoria não certifica a calibração dos instrumentos nem garante a condição de uma rua.

## Achados, por prioridade

### 1. Alta — Itajaí perdeu as onze réguas por mudança do portal

**Reprodução:** `/monitor` informa fonte de Itajaí indisponível; `/itajai` informa ausência de leitura ao vivo. `ultimo.json` registra `fonte_itajai_ok: false` e não contém réguas DC-01 a DC-11.

O endereço usado pelo coletor, `https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios`, exibe **ERRO 404 / Página não encontrada** no Chrome. A consulta HTTP feita na auditoria recebeu um corpo sem leituras e o parser retornou lista vazia; o texto de erro da página é evidência, independentemente do código HTTP do transporte.

A página inicial oficial agora aponta para:

https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/rios

Esse novo endereço exibiu:

| Estação | Nível | Medição em 19/09 |
|---|---:|---|
| DC01 | 1,00 m | 12h41 |
| DC02 | 0,54 m | 12h41 |
| DC03 | 0,26 m | 12h40 |
| DC04 | 0,96 m | 12h41 |
| DC05 | 1,06 m | 12h41 |
| DC06 | 0,42 m | 12h40 |
| DC07 | 0,33 m | 12h40 |
| DC08 | 0,98 m | 12h40 |
| DC09 | 0,68 m | 12h40 |
| DC10 — Limoeiro | 3,40 m | 12h40 |
| DC11 — Santa Regina | 2,29 m | 12h40 |

**Causa no código:** `scripts/coleta_itajai.py:47` fixa o URL antigo. O parser também espera nomes/estrutura antigos e data sem vírgula; a nova interface apresenta identificadores como `DC01` e datas como `19/09/2026, 12:41`. Portanto, trocar apenas o domínio sem validar o contrato não basta. O portal novo separa municípios por `municipio_id` e tem novas rotas de chuva, barragens e marés.

**Correção recomendada:** adaptar o coletor ao novo contrato, mapear explicitamente cada identificador à régua existente e atualizar os links de fonte. Testar onze identidades, unidades, horários e rejeição de páginas de erro. Conferir a primeira publicação e a tela após o deploy da VPS.

### 2. Alta — Simulador inclui cotas explicitamente bloqueadas

Em `/acu/rio-do-sul`, com leitura de **3,76 m**, o simulador afirmou que **2 de 555 ruas já estariam alagadas**, listando Pouso Redondo (3,11 m) e SD 1604 (3,26 m).

O próprio `data/cotas-ruas.json` marca esses dois registros com `usar_para_aviso: false` e nota de pendência de conferência. O resumo do simulador não exibe essa ressalva junto dos dois pontos.

**Causa:** `web/src/logica/cotasRuas.ts:99` filtra apenas existência de cota e comparação numérica. `CotasDeRua.tsx` usa esse resultado na contagem e na lista. A busca individual já respeita o bloqueio para a frase “este nível já foi alcançado”, mas o resumo não.

**Impacto:** o produto transforma números que ele próprio considera inadequados para aviso em uma afirmação de alcance de água. Não foi verificado se essas ruas estavam realmente alagadas; o defeito confirmado é a inconsistência entre o cadastro e a conclusão exibida.

**Correção recomendada:** separar pontos pendentes da contagem e das frases de alcance; preservá-los na consulta documental com sua ressalva. Contagens também deveriam dizer “pontos com cota” quando vários registros pertencem à mesma rua.

### 3. Alta — Gráficos apresentam leitura antiga como “Agora”

Em `/acu/gaspar`, o topo informa corretamente ausência de leitura ao vivo. Mais abaixo, a série mostra **“Agora: 1,32 m”, medido 18/09, 18:03**, seguida de **“descendo (3 cm/h)”**. Durante a auditoria já era aproximadamente 13h de 19/09: cerca de 19 horas depois.

A fonte municipal confirma exatamente **1,32 m às 18h03 de 18/09**:

https://defesacivil.gaspar.sc.gov.br/estacao/ver/21

O problema não é a transcrição desse número. É apresentar uma medição e tendência antigas como atuais. Em Brusque, a série também mostrou “Agora: 1,38 m”, medido às 07h55, já aproximadamente cinco horas antes, enquanto o topo exibia outro instrumento estadual recente.

**Causa:** `web/src/componentes/LinhaDoTempo.tsx:160` escreve “Agora” incondicionalmente. A faixa pode virar “sem leitura”, mas o rótulo e a tendência continuam sem uma indicação clara de vencimento.

**Correção recomendada:** aplicar idade ao texto e à tendência. Usar “Última leitura da série” e explicitar que a tendência se refere ao período encerrado naquele horário quando a série estiver vencida.

### 4. Média — Leituras estaduais na página da cidade não mostram idade

Nas páginas de Brusque, Vidal Ramos e Ilhota, o cartão “Agora” exibe o nível estadual sem o horário da medição. A idade visível logo depois pertence à chuva, não ao nível. No monitor regional, em contraste, o nível estadual tem sua idade.

**Causa:** `web/src/telas/TelaCidade.tsx:185` apresenta `bruto.nivelBrutoM` sem verificar nem mostrar `bruto.medidoEm`. `web/src/dados/nivelSc.ts` preserva a leitura anterior em falhas de transporte, o que é útil desde que a interface mantenha sua idade visível.

Os números estaduais consultados estavam recentes nesta auditoria; não se constatou uma leitura estadual vencida nesse instante. O defeito confirmado é a falta da informação e da guarda nesse caminho de apresentação.

**Correção recomendada:** utilizar a mesma política de horário, frescor e indisponibilidade do restante do site; indicar o código da estação e manter a distinção entre datum estadual e municipal.

### 5. Média — Blumenau: fontes diferentes são chamadas de réguas diferentes

Em `/acu/blumenau`, “Últimas horas” diz que há **duas réguas**, cada uma com zero próprio. As séries listadas são **Blumenau** e **Blumenau (AlertaBlu)**.

O repositório documenta essas entradas como duas publicações de uma mesma referência operacional. `scripts/coleta_niveis.py:491` explica por que elas são separadas na série: foram observadas divergências sistemáticas entre as publicações, e misturá-las criaria saltos e tendências artificiais.

**Separar as séries é uma decisão deliberada e justificável. O erro é transformar a separação por fonte em uma afirmação de duas réguas físicas com zeros distintos.**

**Causa:** `LinhaDoTempo.tsx:132` aplica a todas as séries múltiplas o texto genérico de réguas distintas; `serie-recente.json` usa o campo `reguas` para a identidade da fonte nesse caso.

**Correção recomendada:** manter as séries separadas e explicar que são duas fontes de publicação. Não fundir nem aplicar deslocamento numérico sem comprovação. A identificação física exata do instrumento continua uma pendência documental do cadastro.

### 6. Média — Chuva equivalente das barragens apresentada como limiar de enchimento

O bloco “De onde vem a água” afirma que a Oeste “enche com ~80 mm”, a Sul com 73 mm e a Norte com 154 mm.

O [relatório JICA de 2011, seção 3.2.2 e tabela 3.2.4](https://openjicareport.jica.go.jp/pdf/12043659_02.pdf) define esses valores como **capacidade dividida pela área de drenagem**. Os números foram transcritos corretamente, mas a frase da interface transforma uma equivalência volumétrica em um limiar operacional de chuva. A condição inicial, o escoamento e a operação não entram nessa divisão.

Além disso, o bloco mostra capacidades históricas de **83 e 93,5 hm³**, enquanto a API Asthon consultada publica `capacidade_maxima` aproximadamente **99,96 e 104,03** para Oeste e Sul. Essa divergência exige conciliação de época e definição; não autoriza substituir automaticamente os valores.

**Causa:** `web/src/componentes/ArvoreDaBacia.tsx:36` usa “enche com”; a ressalva temporal de `data/hidraulica.json._meta` não acompanha essas fichas.

**Correção recomendada:** identificar explicitamente “referência histórica JICA 2011” e “chuva equivalente ao volume”, sem apresentar como quantidade de chuva que vai encher a barragem hoje.

## Valores que conferiram e limitações de cobertura

| Dado | Publicação usada pelo site | Consulta direta | Resultado |
|---|---|---|---|
| Blumenau / AlertaBlu | 2,63 m, 12h00 | 2,63 m, 12h00 | Coincide, inclusive horário |
| Rio do Sul / Asthon Tito Buss | 3,76 m, 12h42:02 | 3,76 m, 12h54:42 | Coincide em medições distintas |
| Taió / Centro | 5,05 m, 12h44:53 | 5,05 m, 12h54:05 | Coincide em medições distintas |
| Ascurra / DCSC-00003 | 7,32 m, 12h45:55 no municipal; 7,31 m, 12h46:10 no estadual | 7,32 m, consulta por volta de 12h55 | Variação de 1 cm entre horários; não prova erro |
| Rede estadual, 25 estações do arquivo | Coleta 12h46 | Consulta 12h55 | Diferenças de 0 a 4 cm; sem discrepância grosseira na amostra |
| Barragem Oeste | 7/7 abertas; 14,33% às 12h42:38 | 7/7 abertas; 14,29% às 12h52:24 | Consistente com horários diferentes |
| Barragem Sul | 5/5 abertas; 0% às 12h42:25 | 5/5 abertas; 0% às 12h52:25 | Coincide |
| Gaspar | Última série: 1,32 m às 18h03 de 18/09 | Fonte municipal: mesmo número e horário | Fonte também desatualizada; corrigir rótulo do gráfico |
| Indaial municipal | 4,10 m às 22h de 12/09 | Sem nova aferição municipal nesta auditoria | Site avisa corretamente “NÃO USE COMO NÍVEL ATUAL” |

Indaial estadual tinha 5,83 m recente, porém não é lícito substituir o valor municipal nem aplicar a ele as cotas municipais sem vincular as escalas. O mapa mostrou o valor municipal antigo em cinza com “há 6 dias”, não como faixa atual.

Os acumulados de chuva publicados foram inspecionados e a fonte estadual respondeu. As janelas mudaram entre as consultas; não foram declaradas equivalentes por comparação de instantes diferentes. Botuverá tem mais de um pluviômetro: o mapa seleciona um e a página da cidade agrega uma faixa, por regras diferentes existentes no código.

## Verificações do repositório

- `python scripts/validar_dados.py`: **0 erros, 14 avisos**. Entre os avisos estão vínculos de régua pendentes e divergências documentais de datas históricas. Passar no esquema não resolve essas pendências.
- `python -m unittest discover -s scripts -p 'teste_*.py' -q`: **1.853 testes executados, 17 ignorados, sem falhas**. O log contém avisos de cenários simulados e ResourceWarnings; não são falhas da produção.
- [CI da revisão auditada](https://github.com/haohmarusc-glitch/enchentes-vale-itajai/actions/runs/35396893856): concluída com sucesso. O workflow inclui validação, testes Python, testes web, build e verificações de navegador. Não executei novamente o build web local nesta auditoria.
- A publicação de tempo real estava viva: os arquivos foram gerados por volta de 15h46 UTC / 12h46 de Brasília, poucos minutos antes da consulta. A atualização do arquivo não implica atualização de todas as fontes.
- README e comentários antigos ainda descrevem publicação automática no GitHub Pages, embora `.github/workflows/pages.yml` seja manual e o site esteja em Cloudflare Access. Isso é dívida documental, não prova de falha do deploy atual.

## Ordem recomendada de correção

1. Restaurar a integração com o novo portal de Itajaí e validar a identidade das onze réguas.
2. Excluir cotas bloqueadas das conclusões de alcance do simulador.
3. Corrigir rótulos de atualidade e tendência nas séries e na alternativa estadual.
4. Distinguir fonte de publicação e régua na série de Blumenau.
5. Qualificar dados históricos e chuva equivalente das barragens; conciliar capacidades por fonte e época.

## Evidências locais

Na pasta `evidencias/` estão os quatro JSONs publicados, respostas brutas das consultas diretas em `fonte-*.json`, `comparacao.log`, `validacao.log` e `testes-python.log`.

Arquivos `fonte-*-erro.json` registram a primeira tentativa sem acesso de rede no ambiente restrito. **Não representam indisponibilidade das fontes oficiais**: as consultas autorizadas posteriores estão nos respectivos `fonte-*.json` e em `comparacao.log`.

As observações do Chrome, incluindo as onze leituras do portal novo e os textos contraditórios, estão transcritas neste relatório. Os valores são uma fotografia da auditoria, não um boletim atual.
