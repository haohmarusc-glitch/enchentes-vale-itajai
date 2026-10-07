# Chuva e maré de Itajaí: investigação e correção — 07/10/2026

Continuação de `docs/AUDITORIA-DOMINIOS-2026-10-07.md` (§5), depois da liberação de domínios no ambiente.
Brutos desta investigação: `data/brutos/itajai-portal-2026-10-07/`.

## Resumo

| | Chuva | Maré |
|---|---|---|
| Endereço que o coletor lia | `defesacivil.itajai.sc.gov.br/monitoramento/chuvas` | `defesacivil.itajai.sc.gov.br/monitoramento/ajax/mares.php` |
| O que ele devolve hoje | HTTP 200 com casca HTML de 641 bytes | a mesma casca, HTTP 200 |
| Efeito antes desta correção | `parse()` devolvia `[]`, lido como "sem pluviômetro": o `ultimo.json` saía com `chuva_ok: true` e **nenhuma estação de Itajaí** | o `json.loads` falhava e nada era gravado, mas a mensagem dizia "ERRO ao baixar", sem o motivo |
| Fonte nova com dado real | `monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/chuvas` (página Inertia, `props.estacoes`) | **nenhuma legível por máquina**: o portal publica só uma imagem JPEG da tábua do mês |
| Última coleta válida conhecida | 19/09/2026, 17:30–17:31 (Brasília), as doze estações DC-00…DC-11 (cópia `arquivo-series` até 05/10) | este coletor **nunca** gravou tábua com preamar; a tábua do site é a da Marinha (CHM/DHN 2026) desde 09/09 |
| Mudança | coletor lê o portal novo e recusa resposta inválida | coletor recusa resposta inválida e não sobrescreve tábua de outra fonte |

## 1. Endpoints do portal novo que devolvem dado real

Lidos em 07/10/2026, por volta de 14h45–14h50 UTC, com o User-Agent do projeto. O `robots.txt` do host é
`Disallow:` vazio. Os endereços vêm do código da própria página (`defesacivil.itajai.sc.gov.br/assets/index-*.js`);
nenhum foi presumido.

| Endereço | Resposta | Conteúdo |
|---|---|---|
| `/monitoramento/chuvas` (HTML, `data-page`) | 200, 198.851 bytes | **12 estações DC00–DC11 com chuva** (10 min, 1 h, 12 h, 24 h, 48 h), qualidade e carimbo por janela, `serie_12_h` |
| `/data/current/app.json` | 200, 199.102 bytes | instantâneo com `estacoes`, `chuvas`, `rios`, `meteorologia`, `barragens`; **sem maré** |
| `/api/v1/chuvas`, `/rios`, `/barragens`, `/meteorologia`, `/municipios` | 200, JSON | só `{id, nome}`: são listas. O detalhe fica em `/{id}` e `/{id}/series-12h`, que não foram usados |
| `/api/v1/situacao-atual`, `/api/v1/mapa` | 200, JSON | situação geral; coordenadas |
| `/monitoramento/mares` (HTML, `data-page`) | 200, 1.520 bytes | `props.tabuaMare = {mes_referencia: "2026-10", arquivo_url: …/api/v1/tabuas-mare/5/arquivo}` |
| `/api/v1/tabuas-mare/5/arquivo` | 200, `image/jpeg`, 279.983 bytes | **imagem** "Maré prevista – Cabeçudas Iate Clube/UNIVALI – Itajaí/SC", outubro/2026 (sha256 `bbf55fb6…3a02`) |

A chuva lê a página `/monitoramento/chuvas`, a mesma forma (`data-page`) que `coleta_itajai_portal.py` já lê para
os rios. Isso dá um pedido só, com município e coordenada na mesma resposta.

## 2. Identificação, unidade e horário

- **Identificação:**
  - Pela coordenada contra `estacoes_tempo_real`, com a mesma folga do coletor de rios (50 m). DC-01…DC-11 batem a
    **0,0 m**.
  - A **DC-00** ("Defesa Civil de Itajaí", pluviômetro puro) não tem coordenada no cadastro. Ela fica **de fora**
    até decisão de cadastrá-la. O portal a publica em −26,9165821, −48,7016231.
- **Título:** sai do cadastro, e é **igual** ao das séries antigas nas doze estações (conferido contra
  `arquivo-series`). A série de chuva continua com a mesma chave, sem quebra.
- **Unidade:**
  - Os campos se chamam `*_mm`.
  - A **soma da `serie_12_h`** (incrementos de 10 min) bate com `chuva_12_h_mm` em todas as estações. A diferença
    máxima é 0,4 mm, um balde na borda da janela. É milímetro de chuva, conferido pelo próprio dado.
- **Horário:**
  - `qualidade.<janela>.medido_em` vem em UTC com offset e é convertido para Brasília sem fuso (`para_brasilia`).
  - Se as janelas tiverem carimbos diferentes, vale o **mais antigo** (nunca rejuvenescer).
  - `consultadoEm` não entra.
  - Ao vivo, às 14h55 UTC, as medições eram de 11h40–11h50 em Brasília.
- **Plausibilidade regional** (não é a mesma estação, então é só sanidade):
  - Itajaí: 24–31 mm em 24 h.
  - Na mesma rodada, pela rede estadual: Ilhota 43 mm, Gaspar 30 mm, Blumenau 36 mm.

## 3. Última coleta válida — o que foi possível conferir daqui

Esta sessão **não tem acesso à VPS**. O que se conferiu:

- **Chuva:** na cópia semanal das séries (`origin/arquivo-series`, cópia de 05/10/2026 18:38 UTC), a última leitura
  de Itajaí é de **19/09/2026, 17:30–17:31**, nas doze estações. Entre 19/09 e 05/10 não há nenhuma. O
  `ultimo.json` publicado hoje (`tempo-real`, 14:46 UTC) tem 17 estações de chuva, todas da rede estadual, e nenhuma
  de Itajaí, com `chuva_ok: true`.
- **Maré:** em todo o histórico de `data/mare-itajai.json`, as duas versões gravadas por este coletor (30/08/2026)
  têm zero preamares. Depois vieram a planilha da UNIVALI (03/09) e a Tábua de Marés 2026 da Marinha (09/09,
  876 preamares), que o site usa hoje. A maré **observada** vem do CIRAM (`coleta_mare_ciram.py` →
  `data/tempo-real/ultimo_mare_ciram.json`), e esse arquivo não é publicado no branch `tempo-real`.

Para conferir **na VPS**, rodar na pasta do repositório:

```bash
# última chuva de Itajaí gravada pelo coletor (série acumulada)
python3 - <<'EOF'
import json, glob
ult = {}
for arq in sorted(glob.glob("data/tempo-real/chuva-*.ndjson")):
    for linha in open(arq, encoding="utf-8"):
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        if str(d.get("estacao", "")).startswith("DC-"):
            ult[d["estacao"]] = max(ult.get(d["estacao"], ""), d.get("medido_em") or "")
for e, q in sorted(ult.items()):
    print(q, e)
EOF

# maré observada (CIRAM): quando foi a última coleta e a última medida
python3 -c "import json; d=json.load(open('data/tempo-real/ultimo_mare_ciram.json')); print(d.get('coletado_em')); print(json.dumps(d, ensure_ascii=False)[:600])"

# se o cron chama coleta_mares.py: o que ele disse na última rodada
grep -n "coleta_mares\|mares.php" /var/log/*.log 2>/dev/null | tail -5
crontab -l | grep -n "mare"
```

## 4. O que mudou no código

- **`scripts/coleta_chuva.py`:**
  - `URL` passou a ser a página nova.
  - `parse()` lê o `data-page` e aplica as regras do coletor de rios: coordenada, título do cadastro e Brasília sem
    fuso.
  - `parse()` **levanta `FonteInvalida`** quando a resposta não é a página esperada: vazia, HTML sem `data-page`,
    outro município, outra seção, lista de estações vazia, ou nenhuma estação aceita. `coleta_niveis.baixar_chuva`
    transforma isso em `chuva_ok: false`.
  - A estação isolada fica de fora, com o motivo no stderr, quando:
    - falta uma das cinco janelas no esquema;
    - um valor não é chuva em mm;
    - falta carimbo.
  - `estado: "sem_dados"` vira janela **ausente** (`null`), nunca zero.
  - A página antiga continua legível por `parse_pagina_antiga()` (e `--antiga --arquivo`), só para reler capturas.
    Nenhum caminho de coleta a usa.
- **`scripts/coleta_niveis.py`:** o `fonte_chuva` publicado no `ultimo.json` aponta o endereço novo
  (`URL_CHUVA_ITAJAI`, com teste que trava a igualdade com `coleta_chuva.URL`).
- **`scripts/coleta_mares.py`:**
  - `validar_resposta()` recusa HTML, vazio, não-JSON e JSON sem `tides`/`astronimical_tides`, mesmo com 200, e diz
    "A tábua NÃO foi alterada".
  - `tabua_de_outra_fonte()` impede sobrescrever a tábua da Marinha. Trocar de fonte só com `--substituir`.
  - O endereço **não** foi trocado: não há endpoint de maré no portal novo para pôr no lugar.
- **Testes:**
  - `teste_coleta_chuva.py`: 35 testes, 17 novos, com a captura real, a casca real e as variações de esquema.
  - `teste_coleta_mares.py`: 21 testes, 6 novos.
  - A suíte Python inteira, o `validar_dados.py` e o `ruff` passam.

**Preservação:** nenhuma série é apagada nem reescrita. Os `.ndjson` só recebem linhas novas, com o **mesmo** título
de estação. A tábua da Marinha fica intacta e protegida.

## 5. O que ainda falta (decisões e passos fora desta sessão)

1. **Deploy na VPS:** a correção só vale depois de atualizar o repositório lá. Depois, rodar
   `python3 scripts/coleta_chuva.py` uma vez e conferir as 11 estações e as horas.
2. **DC-00:** cadastrar ou não a coordenada que o portal publica (−26,9165821, −48,7016231) em
   `estacoes_tempo_real`. A mudança em `estacoes.json` é decisão do Jefferson. Até lá, a DC-00 fica fora da chuva.
3. **Maré:** a tábua do portal é imagem. Transcrever a imagem seria criar dado. A tábua oficial da Marinha já cobre
   2026. Se a Defesa Civil vier a publicar a maré em JSON, cabe um coletor novo, com validação contra a CHM.
4. **`chuva_ok`:** a marca hoje cobre **só** a fonte de Itajaí. Se Itajaí falhar, o chat responde "Não consegui
   buscar a chuva agora", embora a chuva estadual e a do CEMADEN tenham chegado. É anterior a esta correção e ficou
   como estava. Separar a marca por fonte é mudança de contrato do `ultimo.json`.
