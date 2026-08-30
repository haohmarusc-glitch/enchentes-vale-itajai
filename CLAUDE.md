# CLAUDE.md — Enchentes do Vale do Itajaí

Guia para o Claude Code trabalhar neste repositório. Leia inteiro antes de codificar.

## O que é o projeto

Site que mostra dados históricos de enchentes nos rios **Itajaí-Açu** e **Itajaí-Mirim** (Santa Catarina, Brasil), com:

- nível do rio em cada cidade ao longo do curso (montante → jusante);
- previsão empírica do nível na próxima cidade a jusante;
- tempo estimado de chegada da onda de cheia;
- painel especial para **Itajaí**, na foz, que recebe os dois rios e sofre influência da maré.

Público: moradores da região (Itajaí, Navegantes, Blumenau, Brusque…) sem formação técnica. Textos em **português do Brasil**.

**Não é um sistema oficial de alerta.** Toda tela deve trazer aviso de que não substitui o AlertaBlu, a Defesa Civil de SC e as Defesas Civis municipais (emergência: 199).

## Estrutura do repositório

```
data/
  estacoes.json   cidades por rio, ordem, códigos ANA, cotas de referência, URLs de tempo real
  enchentes.json  picos históricos: um registro por (evento, cidade), com fonte e confiança
  transito.json   tempos de trânsito da onda de cheia entre cidades
scripts/          Python 3.11+ — coleta (ANA, Defesa Civil) e cálculo de correlações
web/              React + Vite + TypeScript — o site
```

Os JSONs em `data/` são a **fonte de verdade**. O site lê deles; scripts escrevem neles.

## Stack e convenções

### web/
- React 18 + Vite + TypeScript (strict).
- Roteamento: `react-router-dom`.
- Gráficos: `recharts`.
- Mapa: começar com um **diagrama linear** do rio (cidades em sequência). Mapa geográfico (Leaflet) é etapa futura.
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

## Telas

1. `/acu` — **Itajaí-Açu**: Taió / Rio do Sul → Ibirama → Indaial → Blumenau → Gaspar → Ilhota → Itajaí
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
