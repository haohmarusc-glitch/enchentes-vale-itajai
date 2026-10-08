# Proposta: rodar o Atlas de Desastres pelo GitHub Actions

Proposta de 08/10/2026, a pedido do Jefferson. **Sem execução nesta tarefa.** Nada aqui muda dado, e a decisão de
ligar o workflow é dele.

## O problema que isto resolve

`scripts/atlas_desastres.py` está pronto e testado desde 19/09/2026, e a rodada canônica (21/09/2026, v1.1 de
06/08/2026, 507 ocorrências nas vinte cidades) só aconteceu porque o Jefferson baixou o CSV no navegador e rodou
`--arquivo` na VPS: o firewall de `atlasdigital.mdr.gov.br` recusa a VPS (HTTP 200 com página de bloqueio) e o
ambiente das sessões de código (403 no proxy). Desde então a base não foi reconferida. O Atlas publica versões novas
(a v1.1 saiu em agosto); a cada uma, as **lacunas** — datas de desastre reconhecido sem pico no projeto — podem
mudar, e é essa lista que diz onde procurar régua (Itajaí e Indaial primeiro).

O runner do GitHub alcança hosts que nem a VPS nem a sessão alcançam (foi assim com o Overpass:
`baixar-vao-oeste.yml`, `baixar-tracado-luiz-alves.yml`). A pergunta é se o firewall do Atlas também deixa.

## Fontes

| Fonte | O que dá | Como o script a usa |
|---|---|---|
| `https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml` | a página de downloads, com o link da versão vigente | `atlas_desastres.py` tenta descobrir o link novo nela e cai em `URL_PADRAO` se não achar |
| `https://atlasdigital.mdr.gov.br/arquivos/<ano>/BD_Atlas_<cobertura>_v<versão>_<data>_Consolidado.csv` (~86 MB, latin-1, `;`) | a base consolidada do S2ID (Sedec/MIDR + Ceped/UFSC) | `--arquivo` ou download com `User-Agent` do projeto e intervalo entre chamadas; `parece_a_base()` recusa HTML, vazio e cabeçalho sem as colunas |
| `data/cemaden-rede-observacional-sc.json` (já no repo) | os 20 códigos IBGE conferidos | recorte das cidades (`FORA_DO_RECORTE`: Ibirama, Rio dos Cedros, Trombudo Central) |
| `data/enchentes.json` (já no repo) | os picos | `atlas_correspondencias.py` cruza por ±5 dias e lista lacunas |

O `User-Agent` continua o do projeto. **Não** se troca por um de navegador para passar pelo firewall (CLAUDE.md:
identificar o projeto em toda requisição). Se o runner for recusado, a resposta é "o Atlas não aceita robô", e o
caminho segue sendo baixar no navegador e rodar `--arquivo`.

## Arquivos gerados

Tudo em `data/desastres/`, pelo próprio script, nunca à mão:

| Arquivo | Conteúdo | Muda `enchentes.json`? |
|---|---|---|
| `fonte.json` | nome original, versão, cobertura, publicação, sha256, bytes, `importado_em`, COBRADEs | não |
| `eventos.csv` / `eventos.json` | um registro S2ID por linha (as vinte cidades; 12100/12200/12300 + 13214) | não |
| `episodios.csv` / `episodios.json` | registros agrupados em episódios regionais | não |
| `correspondencias.json` (`atlas_correspondencias.py --escrever`) | pico × ocorrência: confirmado / provável / provável (mês) / divergente / fora da cobertura / sem correspondência; e as **lacunas** | não |

O bruto (`data/brutos/BD_Atlas_….csv`, 86 MB) fica **fora do git** (já é assim) — no Actions ele é artefato da
rodada, apagado pelo GitHub em 90 dias, e o `sha256` em `fonte.json` prova qual arquivo gerou a saída.

Há teste travando que `atlas_desastres.py` **não escreve** em `enchentes.json`, `estacoes.json` nem
`transito.json`. A regra do projeto continua: Atlas é roteiro de datas e contexto institucional, nunca pico.

## Como o workflow seria (`.github/workflows/atlas-desastres.yml`)

Mesmo molde do `baixar-vao-oeste.yml`: manual, publica num branch próprio, não toca o `main` nem o branch de PR.

1. **Sonda** (`curl -I`, 20 s): o runner alcança `atlasdigital.mdr.gov.br`? Se responder bloqueio ou 403, a rodada
   termina ali, com o relatório dizendo isso — sem tentar outro `User-Agent`.
2. **Descobrir a versão**: ler a página de downloads e comparar com `data/desastres/fonte.json` (`versao_mudou()`).
   Versão igual e sha igual → "sem novidade", encerra verde, nada publicado.
3. **Baixar** o CSV para `data/brutos/` e **`--dry-run`** primeiro: lê, filtra, verifica (fora da cobertura, valor
   negativo, versão) e imprime o resumo **sem gravar**.
4. **Rodada de verdade** (`atlas_desastres.py --arquivo <csv>`) e `atlas_correspondencias.py <saídas> --escrever`.
5. **Testes**: `teste_atlas_desastres.py` e `teste_atlas_correspondencias.py`, com a saída nova no lugar.
6. **Publicar** `data/desastres/*` + `RELATORIO.md` (versão, sha, contagens por cidade e COBRADE, lacunas novas e
   lacunas que fecharam em relação à rodada anterior) no branch `atlas-desastres`, um commit só, substituído a
   cada rodada — como `vao-oeste` e `tracado-luiz-alves`.
7. A **sessão** lê o branch, confere o relatório e abre o PR para `main` com os JSONs; o Jefferson decide o merge.

`permissions: contents: write` só para o branch de publicação; `concurrency` sem cancelamento (uma rodada de cada vez).

## Frequência

- **Manual** (`workflow_dispatch`) — a primeira rodada é só a sonda + `--dry-run`, para saber se o runner passa.
- **Mensal**, dia 10 (`cron: '0 9 10 * *'`, UTC): o Atlas publica versões poucas vezes por ano; mensal pega a versão
  nova com no máximo um mês de atraso e custa uma consulta à página de downloads por mês quando nada mudou (o
  download de 86 MB só acontece com versão nova).
- **No push** que alterar o workflow ou os dois scripts, como nos outros workflows de coleta.

Não roda na publicação de 15 min nem na VPS: não é dado ao vivo.

## Validação (o que tem de passar antes de alguém olhar o resultado)

1. `parece_a_base()`: o arquivo baixado é a base (cabeçalho com as colunas esperadas), não HTML de bloqueio.
2. Versão e sha registrados em `fonte.json`; `versao_mudou()` diz o que mudou em relação à rodada anterior.
3. Os 20 códigos IBGE do recorte conferem com `cemaden-rede-observacional-sc.json` (já é teste).
4. Nenhuma data inválida, nenhum valor negativo, nenhum protocolo duplicado — o script falha alto.
5. **Reprodução da rodada canônica**: com a mesma v1.1 (sha `78f7efd2…`), a saída tem de ser idêntica à de
   21/09/2026 (507 ocorrências, 166 episódios, correspondências iguais). Diferença com a mesma base é bug, não
   novidade.
6. Com versão nova: o relatório lista, cidade a cidade, as lacunas que entraram e as que saíram; **nenhum pico muda**.
7. Os testes dos dois scripts passam com a saída nova.

## O que NÃO entra

- Nada em `enchentes.json`, `estacoes.json` ou `transito.json`.
- Nenhuma altura, nenhuma faixa, nenhum aviso: o Atlas registra decreto e dano, não régua.
- Nenhum `User-Agent` de navegador, nenhum espelho não oficial da base.

## Decisões pedidas ao Jefferson

1. Autorizar a primeira rodada (sonda + `--dry-run`) para saber se o runner alcança o host.
2. Se alcançar: a cadência mensal acima, ou só manual.
3. Onde a sessão deve apontar as lacunas novas (README "Pendências" ou um doc por rodada).
