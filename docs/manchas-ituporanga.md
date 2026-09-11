# Camadas de inundação de Ituporanga

Consulta manual disponível em `/#/acu/ituporanga`. O componente não recebe leitura ao vivo; a referência da régua ainda está pendente no C22.

## Proveniência e reprodução

Mapa divulgado pela Prefeitura: https://www.google.com/maps/d/viewer?mid=19tpP2Tfsl58ue6GtY5ihBfK3MLkiUrA

Download: https://www.google.com/maps/d/kml?mid=19tpP2Tfsl58ue6GtY5ihBfK3MLkiUrA&forcekml=1

Recuperado em 11/09/2026 UTC, 33.999.491 bytes. SHA-256: `38c4501c9c08242a00c772b9fab745eaa02bf254ba27c22d9625ec591ae9ba05`, igual ao snapshot registrado em 09/09.

Oito pastas, de 3,00 a 6,50 m, totalizando 78.547 polígonos. Os LineStrings não são convertidos em áreas; as quantidades ficam no índice. Furos são preservados. Os limites internos dos polígonos são dissolvidos por união geométrica, sem buffer, interpolação, arredondamento ou simplificação. Isso evita que as faixas estreitas desapareçam na projeção para pixels do Leaflet. O arquivo KML original fica disponível no endereço de download; não é necessário ao runtime do site.

Reprodução:

```sh
python -m pip install -r scripts/requirements-mapas.txt
python scripts/importar_manchas_ituporanga.py arquivo.kml --saida data/manchas/ituporanga
python -m unittest discover -s scripts -p teste_importar_manchas_ituporanga.py
```

Cada camada é um GeoJSON independente, carregado quando selecionado. O mapa remove a anterior imediatamente ao trocar o seletor, cancela requisições superadas e permite ocultar a área. Mantém o enquadramento para comparar os níveis. A área azul representa a camada da fonte, não confirmação de alagamento atual. Não há licença própria atribuída ao material: a autoria e o link da fonte permanecem explícitos.

Para automatizar: obter identificação da régua das camadas e correspondência documentada com a leitura atual, além de validar os critérios de aplicação. Não ligar diretamente à DCSC-00039 por proximidade.
