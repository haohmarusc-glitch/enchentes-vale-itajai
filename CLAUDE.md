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

### Fuso dos carimbos de tempo real — REGRA (aprendida em 01/09/2026)
- **`medido_em` sem fuso = horário de Brasília (America/Sao_Paulo).** É o que a página da
  Defesa Civil de Itajaí publica, e o sistema inteiro já concorda nisso: `coleta_itajai.py`
  **grava** local, o site lê com `deBrasilia()` (com teste travando), o vigia lê com `FUSO`.
  Toda fonte nova de nível/chuva grava `medido_em` no MESMO horário de Brasília, sem fuso.
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

### Referência altimétrica de Blumenau — REGRA BLOQUEANTE
- Duas referências coexistem: **régua** da estação ANA 83800002 (Defesa Civil/AlertaBlu,
  leituras operacionais) e **zero do IBGE** = régua + 0,20 m (série CEOPS/FURB,
  Cordero & Medeiros, Tabela 4, 1852–2001).
- Evidência: set/2011 = 13,00 m (CEOPS) vs 12,80 m (Defesa Civil), diferença exata de 0,20 m.
  Os valores históricos populares (15,34 m em 1983, 15,46 m em 1984) coincidem com a tabela IBGE.
- Enquanto `data/enchentes.json._meta.REGRA_REFERENCIA_BLUMENAU` existir:
  1. `referencia` é rótulo do registro, com conjunto fechado: `"régua"`,
     `"IBGE (régua + 0,20 m)"` ou `null`. Hipóteses vão em `referencia_hipotese` ou `nota`,
     nunca no campo `referencia`. O validador rejeita registro sem o campo.
  2. Conflito de valor para o mesmo (cidade, evento) usa o mecanismo `divergencias`:
     um valor adotado, os demais guardados com fonte e referência. Não criar dois registros
     para o mesmo evento; `agruparEmEventos` não deve escolher por magnitude.
  3. Nenhuma conversão entre referências é gravada no JSON. A UI **exibe a referência de cada
     ponto e avisa quando o gráfico mistura referências** — feito. Um seletor régua/IBGE que
     aplique ±0,20 m só para visualização fica como pendência OPCIONAL, a fazer apenas se a
     verificação no HidroWeb demorar: enquanto a ambiguidade não for resolvida ele ajuda, e
     depois dela nasce e morre em dias.
  4. Busca "minha rua" e simulador usam somente nível em `régua` (cotas de rua e tempo real
     são régua). Há teste que trava isso.
  5. Previsão a jusante pareia igual com igual: montante e jusante na mesma referência.
     Se só houver série IBGE no montante, documentar o deslocamento e não parear com
     jusante em régua.
- Remoção da regra: teste no HidroWeb (estação 83800002, cotas de 09/07/1983 e 07/08/1984)
  ou resposta da FURB. Conversão para `régua` em um único commit, decisão registrada em
  `docs/fontes-academicas.md`.

## Telas

1. `/acu` — **Itajaí-Açu** (ÁRVORE, não fila — ver `docs/TOPOLOGIA-CANONICA.md`): cabeceiras paralelas **Taió** (Oeste) ‖ **Ituporanga** (Sul) → tronco **Rio do Sul → Ascurra → Indaial → Blumenau → Gaspar → Ilhota → Itajaí**; **Ibirama** é afluente lateral (Rio Hercílio), não elo do tronco. `ordem` é `null` no Açu; a posição vem de `ramo` + `ordem_no_ramo`. O validador (`scripts/validar_dados.py`) aborta se a fila global voltar.
2. `/mirim` — **Itajaí-Mirim**: Vidal Ramos → Botuverá → Brusque → Itajaí
3. `/itajai` — **Itajaí (foz)**: chegada dos dois picos + maré
4. `/` — início: escolha do rio + aviso legal

Cada tela de rio mostra: diagrama linear com as cidades; para cada cidade, nível atual (quando houver fonte), cotas de referência, seta para a próxima cidade com o tempo de trânsito; gráfico dos picos históricos daquele rio, com filtro por cidade.

## Lógica de previsão (v1 — empírica)

- Previsão a jusante = correlação linear entre picos históricos da cidade de cima e da cidade de baixo no mesmo evento (`enchentes.json`).
- Tempo de chegada = faixa de `transito.json`; mostrar sempre como **intervalo** ("14–17 h"), nunca número exato.
- Quando não houver pares suficientes (< 5 eventos), exibir "dados insuficientes" em vez de estimar.
- Para Itajaí: considerar os dois rios e mostrar o estado da maré no horário previsto de chegada de cada pico. Fonte de maré: tábuas da Marinha (DHN), porto de Itajaí — integração futura.

## Fontes externas

| Fonte | Uso | Observação |
|---|---|---|
| ANA / HidroWeb (SNIRH) | séries históricas de cota | API nova exige cadastro por e-mail (hidro@ana.gov.br) |
| Defesa Civil SC — monitoramento.defesacivil.sc.gov.br | tempo real | site em JS; endpoint JSON ainda a descobrir |
| AlertaBlu (Blumenau) | tempo real + cotas de ruas | |
| Defesa Civil de Itajaí | tempo real Açu, Mirim e ribeirões | |
| CEOPS/FURB (ceops.furb.br) | acervo histórico de picos | centro desativado em 2022; só acervo |

Respeitar rate limits e identificar o `User-Agent` com o nome do projeto em todos os scripts.

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
