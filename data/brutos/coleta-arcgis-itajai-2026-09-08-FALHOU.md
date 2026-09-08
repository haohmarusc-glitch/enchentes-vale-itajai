# Coleta ArcGIS — Itajaí / enchentes

Coleta executada em 2026-09-08T02:01:02.

## Fontes fornecidas

- Experience Builder: item `03542d8f541c4392bc542b01ca979c6d`, página `page_3`, view `view_2`.
- Web AppBuilder: item `131634abf81347b9a973e79746ae4ef3`.

## Serviço histórico oficial

`historico_inundacoes` — FeatureServer oficial da Prefeitura de Itajaí. O serviço declara EPSG:4326, limite de 1000 registros por consulta e dez camadas.

| ID | Camada | Registros baixados | Campos |
|---:|---|---:|---|

## Arquivos coletados

- `historico_inundacoes_ERROR.json`
- `inundacao_cotas_ERROR.json`
- `item_03542d8f541c4392bc542b01ca979c6d_data_ERROR.json`
- `item_03542d8f541c4392bc542b01ca979c6d_metadata_ERROR.json`
- `item_131634abf81347b9a973e79746ae4ef3_data_ERROR.json`
- `item_131634abf81347b9a973e79746ae4ef3_metadata_ERROR.json`

## Observações de integridade

- Os arquivos `*_metadata.json` preservam esquema, campos e metadados das camadas.
- Os arquivos `*_features.json` preservam atributos e geometrias retornados pelo REST.
- Quando aceito pelo servidor, também foi gravada uma versão `.geojson` em WGS84 para uso direto em GIS/web maps.
- Os JSONs dos dois aplicativos e dos itens referenciados foram preservados para rastrear WebMaps, Feature Layers e widgets.
- Não se deve interpretar automaticamente classes/polígonos de inundação como nível de régua fluvial; a associação precisa vir de fonte explícita.

## Conteúdo histórico confirmado

Camadas declaradas pelo serviço `historico_inundacoes`: 1983, 1984, 2001, 2008, 2011, cotas de setembro/2011, julho/2013, setembro/2013, junho/2014 e outubro/2015.

## Próximo alvo

Localizar, entre os itens/camadas referenciados pelos aplicativos, a tabela ou camada que represente as réguas/cotas por endereço (incluindo a possível Tabela 13 / conjunto das 11 réguas), mantendo separadas cotas altimétricas, manchas históricas e níveis de estação.
