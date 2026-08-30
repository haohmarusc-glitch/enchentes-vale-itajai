# Cotas de enchente por rua — análise e tarefas para o Claude Code

> Levantamento feito em 30/08/2026 a partir de fontes públicas. Objetivo: adicionar ao site a camada
> "a partir de qual nível do rio cada rua alaga" e as manchas de inundação históricas.
> Leia o `CLAUDE.md` antes. Tudo aqui segue as mesmas regras: cada cidade tem sua própria régua,
> todo dado precisa de `fonte` e `confianca`, nada é inventado.

## 1. O que existe, por cidade

### Itajaí (Açu + Mirim) — dados abertos em GeoJSON, licença MIT ⭐
A prefeitura mantém a organização **GeoItajaí** no GitHub. O repositório `geoitajai/sie`
(licença MIT) tem o webmap `dcitajai.html` ("Defesa Civil de Itajaí, áreas atingidas por
inundações") e, em `data/`, as manchas de inundação por evento:

| Arquivo | Evento | Conteúdo |
|---|---|---|
| `enchente1983.geojson` | jul/1983 | 1 MultiPolygon, mancha total, sem atributos |
| `enchente1984.geojson` | ago/1984 | idem |
| `enchente2001.geojson` | 2001 | idem |
| `enchente2008.geojson` | nov/2008 | idem |
| `enchente2011.geojson` | set/2011 | idem |
| `inundasetembro2011.geojson` | set/2011 | 5 polígonos com `situa` = lâmina d'água (0,50 / 0,51 a 1 / 1,01 a 1,50 / 1,51 a 2 / 2,01 a 3 m) |
| `inundajulho2013.geojson` | jul/2013 | 48 polígonos, `situa` em classes (0,20 / 0,21 a 0,40 / 0,41 a 0,60) |
| `inundasetembro2013.geojson` | set/2013 | 58 polígonos |
| `inundajunho2014.geojson` | jun/2014 | 55 polígonos |
| `inundaoutubro2015.geojson` | out/2015 | 155 polígonos (0,20 / 0,21 a 0,40 / 0,41 a 0,60 / 0,51 a 1) |

URL base (raw): `https://raw.githubusercontent.com/geoitajai/sie/master/data/<arquivo>`
Repositório: `https://github.com/geoitajai/sie` — webmap de referência: `https://geoitajai.github.io/sie/dcitajai.html`

Observações:
- Os arquivos "enchenteAAAA" são a mancha total do evento; os "inundaMÊSAAAA" trazem a
  **profundidade da lâmina d'água por trecho** (`situa`), que é o dado mais útil para ruas.
- Não há cota de rio associada a cada polígono. A ligação evento → pico do rio vem de
  `data/enchentes.json` (cruzar pela data).
- A prefeitura também publica "cotas por endereço" no GeoItajaí (portal de geoprocessamento);
  não localizei o serviço aberto — **tarefa de investigação**.
- Bairros historicamente atingidos: Cidade Nova, Imaruí, Nossa Senhora das Graças, Fazenda,
  São Vicente, Murta, Cordeiros, Salseiros, Canhanduba, Dom Bosco, Nova Brasília, Bambuzal,
  Itaipava (junto à BR-101). Fonte: mapeamento da Defesa Civil no evento de 2015.

### Blumenau — tabela oficial de cotas por rua (AlertaBlu)
- Página: `https://alertablu.blumenau.sc.gov.br/p/cotas` (também `https://defesacivil.blumenau.sc.gov.br/p/cotas`)
  e "Ruas alagadas agora": `https://defesacivil.blumenau.sc.gov.br/p/ruas-alagadas`.
- O site bloqueia acesso automatizado (robots.txt). **Não raspar.** Opções: (a) pedir a tabela à
  Defesa Civil de Blumenau; (b) digitar manualmente a partir da página; (c) usar o que a imprensa
  reproduziu (abaixo).
- Referências da régua (Ponte Adolfo Konder): cota de inundação urbana 8,00–8,50 m; ruas mais
  baixas começam a alagar a partir de ~7,40 m.
- O mapa do AlertaBlu permite simular o nível e ver as ruas atingidas; há também mapa de rotas de
  fuga. A FURB foi contratada em 2026 para atualizar as cotas (~20 mil edificações) — quando sair,
  substitui tudo.
- Amostra de cotas publicadas (mai/2022, fonte: relação oficial reproduzida pelo ND+):

| Rua | Bairro | Cota (m) | Ponto |
|---|---|---|---|
| Rua São Rafael | Itoupava Norte | 7,40 | final da rua |
| Rua Martha Cordeiro | Fortaleza | 7,60 | ponto mais baixo |
| Rua Albert Goll | Fortaleza | 7,65 | esquina com Rua 1º de Janeiro |
| Rua São Rafael | Itoupava Norte | 7,75 | próximo ao nº 169 |
| Rua Martha Cordeiro | Fortaleza | 7,80 | esquina com Rua 1º de Janeiro |
| Rua Max Scheidemantel | Fortaleza | 7,90 | próximo ao nº 85 |
| Rua Max Aldemann | Fortaleza | 7,95 | início / ponto mais baixo |

### Gaspar — mapa de cotas por rua (CEOPS/FURB, 2016–2017)
- Estudo feito pelo CEOPS/FURB (coord. Ademar Cordeiro), rua por rua, referenciado à régua da
  ANA na empresa Círculo, usando as marcas de 2011 e, em alguns casos, 1983.
- Consulta: site da Defesa Civil de Gaspar → menu → "Mapas" → "Pesquise sua cota"
  (`https://defesacivil.gaspar.sc.gov.br/` — a tabela de estações em `/monitoramento/tabela`
  é HTML simples; verificar se o mapa de cotas também tem endpoint acessível).
- Referências: alerta a partir de 4,00 m; primeiras ruas a partir de 6,00–6,20 m; emergência
  acima de 7,00 m. A 7 m: 53 ruas (3,8%); a 9 m (como em 2011): 329 ruas (24%); a 11 m metade
  da cidade.
- Cotas publicadas: Rua Petúnia e Rua Costa Rica 6,20 m; Av. Hilberto Gaertner 6,25 m;
  Rua Sertão Verde 6,34 m; Rua Lino 6,57 m. Lista das primeiras ruas atingidas a 6,20 m:
  Av. Hilberto Gaertner, Alfazema, Alício Hugo Hostins, Amor Perfeito, Costa Rica, das Palmeiras,
  Flor de Laranjeira, Francisco Wessling, Heinrich Gorisch, Lírio, Maestro Egon Bohn, Magnólia,
  Maria da Silva, Olga Sabel, Petúnia, Rio do Sul, Sertão Verde. A ~7,4 m entram ainda: Imaruí,
  Francisco Laguna, Augusto Jacinto dos Santos, José Eberhardt, Frei Canisio.

### Brusque (Itajaí-Mirim) — planilha da Defesa Civil, atualizada após nov/2023
- A Defesa Civil de Brusque mantém planilha de cotas por rua; após a enchente de 17/11/2023
  (8,96 m) atualizou as cotas até 8,96 m e iniciou uma 2ª etapa para os pontos não atingidos.
  Não há página pública da planilha — **pedir por e-mail/ofício**.
- Régua: Ponte Estaiada. Cota de inundação da Beira-Rio: **4,80 m**. Loteamentos Beira Rio
  Lote I e II tiveram obras após a última enchente e ainda não têm cota consolidada (jul/2026).
- Cotas publicadas (lista oficial de out/2023, reproduzida por O Município em 17/11/2023):

| Rua | Cota (m) |
|---|---|
| Rua Coelho Neto | 5,64 |
| Rua Celia Zen | 6,72 |
| Rua Adelino da Silva Vale | 6,82 |
| Rua Hugo Schlosser | 7,30 |
| Rua Manoel João Flor | 7,62 |
| Rua Alemanha | 7,62 |
| Rua Francisco Sassi | 7,71 |
| Rua Beira Rio | 7,76 |
| Rua Teodoro H. Staack | 7,77 |
| Rua México | 7,80 |
| Rua Teodoro Henrique | 7,80 |
| Rua SR-005 | 7,82 |
| Rua SC 221 | 7,83 |
| Rua Francisco Heil | 7,90 |
| Rua Júlio Orthmann | 7,94 |
| Rua Padre Gracher | 7,95 |
| Rua Vitório Demarchi | 7,95 |
| Rua Francisco Staack | 7,95 |
| Rua Carlos Hort | 7,97 |
| Rua Laura Diegoli Battistotti | 8,01 |
| Rua Mathias Moritz | 8,01 |

- Pontos que alagam antes disso (5,46–5,80 m): embaixo da Ponte Estaiada, fundos dos
  loteamentos Ema I/II e Santa Mônica (Limoeiro), túnel do Terminal Urbano, Beira Rio na altura
  do Loteamento Malossi/Santa Rita. Bairros primeiro atingidos: Taboão, Pamplona, Bela Aliança,
  Santa Rita; depois Centro, Guarani, Santa Terezinha, Rio Branco, Maluche, Dom Joaquim.
- Afluente relevante: rio Guabiruba, com estação própria (nova, 2025).

### Rio do Sul — tabela "Cota de Cheias por Rua" com exportação
- Portal: `https://defesacivil.riodosul.sc.gov.br/` → "Cota de Cheias por Rua" (555 itens, campos
  `logradouro`, `minima`, `maxima`, botão "Exportar Dados").
  URL: `https://defesacivil.riodosul.sc.gov.br/index.php?r=soscota-rua%2Ftabela`
- O portal é JS puro; a exportação provavelmente chama um endpoint interno. **Descobrir com
  DevTools** (aba Network ao clicar em Exportar). Há também "Planilha Histórica Rio", "Atestado
  Enchente" e "Mapa Inund. e Abrigos".
- Referências: enchente a partir de ~7,00 m (abrigos abertos a 7 m); cota de alerta usual
  6,50–7,50 m.

### Indaial, Ilhota, Timbó, Ibirama, Taió, Vidal Ramos, Botuverá
- Nada aberto localizado. Indaial tem portal da Defesa Civil em `indaial.atende.net`.
  Tratar como pendência de contato.

### Universidades
- UFSC (TCC 2025) consolidou em QGIS polígonos/pontos de inundação fornecidos pelas Defesas
  Civis de Blumenau, Brusque, Gaspar, Itajaí e Rio do Sul. Vale pedir os arquivos ao autor.
- LabGeo/FURB: GeoServer com carta-enchente de Blumenau 2011 (12,8 m) em WMS. Pedido enviado.

## 2. Modelo de dados a criar

### `data/cotas-ruas.json`
```json
{
  "_meta": {
    "descricao": "Nível do rio (régua local) a partir do qual cada rua/ponto alaga.",
    "campos": {
      "cidade": "id de data/estacoes.json",
      "rio": "itajai-acu | itajai-mirim",
      "rua": "nome oficial",
      "bairro": "opcional",
      "ponto": "trecho/esquina/número, quando a fonte informa",
      "cota_m": "nível do rio na régua da cidade",
      "fonte": "URL ou documento",
      "data_fonte": "AAAA-MM-DD da publicação",
      "confianca": "alta | media | baixa"
    }
  },
  "cotas": []
}
```
Popular com todas as tabelas da seção 1 (Blumenau, Gaspar, Brusque). Confiança: `media`
(oficial reproduzido pela imprensa). Quando vier a tabela oficial, sobrescrever com `alta`.

### `data/manchas/` (GeoJSON)
- `scripts/baixar_manchas_itajai.py`: baixa os 10 arquivos do GeoItajaí para `data/manchas/itajai/`,
  gera `data/manchas/index.json` com `{cidade, evento, data, arquivo, tem_lamina, licenca: "MIT", fonte}`
  e, para os arquivos com `situa`, normaliza a classe para `lamina_min_m` / `lamina_max_m`.
- Cruzar cada evento com o pico correspondente em `data/enchentes.json` (adicionar os picos de
  Itajaí que faltam: 1983, 1984, 2001, 2008, 2011, jul/2013, set/2013, jun/2014, out/2015 —
  buscar na Defesa Civil de Itajaí).

## 3. Telas / componentes

1. **Busca "minha rua"** (por cidade): campo de texto com autocomplete sobre `cotas-ruas.json`;
   retorna a cota, o nível atual da cidade (`data/tempo-real/ultimo.json`) e a diferença
   ("faltam 2,3 m para sua rua"). Mostrar sempre a régua de referência da cidade.
2. **Simulador de nível**: slider por cidade; lista as ruas com `cota_m <= nível` ordenadas.
   Rodapé com contagem ("a 7 m, N ruas conhecidas").
3. **Mapa de manchas (Itajaí)**: Leaflet + GeoJSON; seletor de evento; cor por lâmina d'água;
   legenda com o pico do rio naquele evento; crédito "GeoItajaí / Prefeitura de Itajaí (MIT)".
4. Na tela do rio, ao lado de cada cidade, badge "N ruas alagam a partir de X m" quando houver dados.

## 4. Tarefas, em ordem

1. Criar `data/cotas-ruas.json` com as tabelas da seção 1 (Blumenau, Gaspar, Brusque). ✔ dados neste arquivo
2. `scripts/baixar_manchas_itajai.py` + `data/manchas/index.json`.
3. Componente de busca por rua + simulador (item 3.1 e 3.2).
4. Mapa Leaflet com as manchas de Itajaí (3.3). Adicionar `leaflet` e `react-leaflet` ao `web/`.
5. Investigar endpoints: exportação de Rio do Sul (DevTools), mapa de cotas de Gaspar, "cotas por
   endereço" do GeoItajaí. Registrar o que achar em `docs/cotas-de-ruas.md` (esta seção).
6. Pendências de contato (não são código): tabela completa de Blumenau (Defesa Civil), planilha de
   Brusque (Defesa Civil), arquivos QGIS do TCC da UFSC, WMS do LabGeo.

## 5. Avisos obrigatórios na interface
- "Cotas são aproximadas e podem estar desatualizadas; obras e novas enchentes mudam os valores."
- "Cada cidade usa sua própria régua. 7 m em Gaspar não é 7 m em Blumenau."
- "Em emergência, ligue 199. Siga a Defesa Civil da sua cidade."
