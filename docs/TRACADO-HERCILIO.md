# O Rio Hercílio (Itajaí do Norte) no Monitor

Pedido do Jefferson em 05/10/2026, para ajudar a Defesa Civil de Ibirama, que confirmou no mesmo dia que as
faixas do rio são lidas na DCSC-00020 (`docs/resposta-ibirama-c26-2026-10-05.md`).

## Por que faltava

O Monitor já pedia `data/rios/hercilio.geojson`, e o conversor já tinha a chave `hercilio`. O arquivo é que
nunca nasceu, por dois motivos:
- nenhuma consulta do Overpass pedia esse rio;
- no OSM o rio está partido em dois nomes: **"Rio Itajaí do Norte"** a montante (José Boiteux, a barragem
  Norte) e **"Rio Hercílio"** a jusante (Ibirama até o Açu).

A ANA cadastra os dois como um só rio, "Rio Itajaí do Norte ou Hercílio" (Hidrografia do SNIRH). Por isso os
dois nomes entram no mesmo arquivo, ao contrário do Rio Conceição, que é outro curso.

## Como entrou

1. `scripts/baixar_tracado_hercilio.py` consulta o Overpass com os dois nomes e confere o traçado antes de
   gravar. Ele precisa:
   - ter os dois nomes;
   - chegar ao Açu (a menos de 1 km);
   - passar pelo pino de Ibirama (a menos de 0,5 km).
2. Ele rodou no GitHub Actions (`.github/workflows/baixar-tracado-hercilio.yml`), porque o Overpass não
   responde ao ambiente da sessão. O resultado foi publicado no branch `tracado-hercilio`.
3. Resultado em 05/10/2026: 21 ways (16 "Rio Itajaí do Norte", 5 "Rio Hercílio"). O bruto, com a consulta,
   está em `data/brutos/tracado-hercilio-osm.json`.
4. `converter_tracado_rios.py` gerou `data/rios/hercilio.geojson`:
   - 11 trechos e 56 km;
   - o traçado passa a 0,06 km do pino de Ibirama e encosta no Açu a 0,14 km.

## O recorte

O Itajaí do Norte nasce em Itaiópolis, uns 55 km ao norte da borda do mapa de hoje. O Monitor enquadra a
bacia pela extensão de todos os rios, então o rio inteiro afastaria o mapa inteiro, e a regra é que o Monitor
não muda.

Por isso o traçado é recortado ao sul da latitude −26,84, que é a borda norte do Açu. O recorte guarda José
Boiteux, Ibirama e a chegada ao Açu.

A trava do Monitor (`npm run trava-monitor`) passou. Os arquivos do Monitor não foram tocados: ele já carregava
qualquer traçado que existisse.

## O que a tela mostra

- **O rio:** a linha passa por Ibirama e desce até o Açu.
- **A cor:** cinza, porque Ibirama não tem tabela de faixas vigente. A régua está confirmada, mas a tabela
  espera o PLAMCON 2026.

## Os outros rios que passam por Ibirama (05/10/2026)

Pedido do Jefferson: todos os rios que passam por Ibirama na tela.
- `scripts/baixar_rios_municipio.py --municipio Ibirama` pede ao OSM todo curso com nome (rio, ribeirão, canal)
  dentro do limite do município. Rodou no Actions (`baixar-rios-municipio.yml`), que publica no branch
  `rios-municipio`. O bruto está em `data/brutos/rios-ibirama-osm.json`.
- O OSM tem **cinco** cursos com nome em Ibirama:

  | curso | km | no Monitor |
  |---|---|---|
  | Rio Hercílio | 22,2 | já estava (`hercilio`) |
  | Rio Rafael Braço Grande | 11,8 | `rio-rafael-braco-grande`, chega ao Rio Rafael |
  | Rio Rafael | 8,7 | `rio-rafael`, chega ao Hercílio |
  | Rio Rafael Braço Pequeno | 3,3 | `rio-rafael-braco-pequeno`, chega ao Rio Rafael |
  | Ribeirão Taquaras | 0,7 | `ribeirao-taquaras`, chega ao Hercílio |

- O conversor gera um arquivo por nome, como o Rio Conceição; nenhum se funde a outro. Os rios do município
  também são recortados na borda norte do Açu.
- **Monitor:** o `MonitorBacia.tsx` passou a desenhar todo traçado de `data/rios/`, não só uma lista fixa. A
  mudança foi autorizada pelo Jefferson com o rótulo `monitor-autorizado`. Assim, um rio que ganhe traçado
  depois aparece sem mexer de novo no Monitor.
- **Cor:** os rios novos ficam cinza, sem cidade no cadastro. Eles mostram por onde a água corre, não pintam
  faixa.
- **Outro município:** rodar o workflow com o nome dele e depois o conversor.
- Um curso sem nome no OSM não entra. Melhorar o mapa ali é contribuir com o OpenStreetMap.

## O pino de Ibirama (06/10/2026)

O Jefferson viu no satélite, com o zoom novo, que o pino de Ibirama estava no mato, longe da cidade. O
motivo: o Monitor encaixava o pino de toda cidade do cadastro do Açu no ponto mais perto do **traçado do
Açu**. Ibirama fica a 2,6 km dele, então o pino caía no Açu, ao sul. A régua DCSC-00020 está no Hercílio,
a 0,06 km do traçado dele.

Correção em `mapaMotor.ts` (`pontoDoPino`, rótulo `monitor-autorizado`):
- a cidade do eixo continua encaixada no tronco, como sempre;
- a cidade **fora do eixo** vai para o traçado desenhado mais perto, se ele estiver a até 1 km;
- sem traçado perto, nada muda.

Ainda puxados para o tronco, porque o rio delas não está desenhado:

| cidade | distância do pino ao tronco |
|---|---|
| Timbó (Benedito) | 8,2 km |
| Rio dos Cedros | 16,6 km |
| Ituporanga (Itajaí do Sul) | 28 km |
| Trombudo Central | 10,6 km |
| Guabiruba | 4,2 km |

Desenhar esses rios corrige o pino delas sem mexer de novo no código.

## Refazer

Rodar o workflow "Baixar traçado do Hercílio" (Actions → Run workflow). Ele republica o branch
`tracado-hercilio`. Depois, na sessão, trazer os arquivos para o repositório:

```bash
git fetch origin tracado-hercilio
git show FETCH_HEAD:tracado-hercilio-osm.json > data/brutos/tracado-hercilio-osm.json
python3 scripts/converter_tracado_rios.py
```

Fonte do traçado: © OpenStreetMap contributors, ODbL.
