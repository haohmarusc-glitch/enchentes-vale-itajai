# Inventário das réguas do mapa

Gerado por `scripts/inventario_reguas.py` (não editar à mão). Pedido do Jefferson em 06/10/2026, com a
auditoria visual das 19 cidades do Monitor.

- **Ficha DCSC:** coordenada da API da Defesa Civil de SC (`data/brutos/dcsc-estacoes-vale-2026-09-13.csv`).
  Só se compara com a ficha do MESMO código.
- **Antes de 06/10:** a quantos km do traçado do rio da tela a régua fica. Era onde o pino caía, porque
  ele era encaixado no traçado. Agora o pino fica na coordenada (ver `pontoDoPino` em `mapaMotor.ts`).
- **Candidata:** estação Hidro da DCSC a até 3 km de cidade sem código (fora as que o cadastro já
  declarou que não são régua, como a DCSC-00178). Não está vinculada e não foi
  usada para mudar nada: só indica onde conferir.
- Na auditoria, nenhuma coordenada mudou. Depois, por decisão do Jefferson (06/10/2026), Blumenau
  passou para a régua da Ponte Adolfo Konder, confirmada pela Prefeitura (`coordenadas_fonte`).

## Cidades

| Cidade | Régua no cadastro | Coordenada (lat, lon) | Código | Tipo na DCSC | Distância à ficha | Antes de 06/10 | Situação |
|---|---|---|---|---|---|---|---|
| Taió | Rio Itajaí do Oeste, régua do CENTRO da cidade — não a da Barragem Oeste | -27,1163, -50,0003 | DCSC-00041 | Hidro | 6 m | 0,04 km | confere com a ficha |
| Ituporanga | — | -27,4822, -49,5825 | DCSC-00039 | Hidro | 6 m | 27,99 km | confere com a ficha |
| Rio do Sul | Ponte Dom Tito Buss | -27,2072, -49,6335 | DCSC-00013 | Hidro | 2 m | 0,05 km | confere com a ficha |
| Ibirama | Régua do Rio Itajaí do Norte (Hercílio) em Ibirama | -27,0570, -49,5200 | DCSC-00020 | Hidro | 5 m | 2,61 km | confere com a ficha |
| Lontras | Régua do Itajaí-Açu em Lontras (a fonte não nomeia o ponto) | -27,1683, -49,5386 | — | — | — | 0,59 km | sem código: ponto do cadastro, fonte não confirma |
| Apiúna | Referência cadastral ANA 83500000; vínculo com a régua municipal pendente | -27,0375, -49,3919 | — | — | — | 0,28 km | sem código: ponto do cadastro, fonte não confirma |
| Ascurra | Ponte do Beber — Itajaí-Açu (DCSC-00003) | -26,9613, -49,3730 | DCSC-00003 | Hidro | 10 m | 0,10 km | confere com a ficha |
| Indaial | Régua do Itajaí-Açu em Indaial (a COMPDEC não nomeia o ponto) | -26,9109, -49,2700 | DCSC-00006 | Hidro | 5 m | 0,02 km | confere com a ficha |
| Blumenau | Ponte Adolfo Konder (Centro) | -26,9186, -49,0656 | DCSC-00026 | Meteo | — | 0,05 km | régua confirmada: Prefeitura de Blumenau/Defesa Civil — Ponte Adolfo Konder, Beira-Rio |
| Gaspar | Rio Itajaí Açu Gaspar — estação municipal 21 | -26,9264, -48,9643 | DCSC-00005 | Hidro | 2 m | 0,12 km | confere com a ficha |
| Ilhota | Estação hidrometeorológica da Ponte Cláudio Jeremias Cadorin (a régua que o PLANCON cita) | -26,8944, -48,8248 | DCSC-00030 | Hidro | 4 m | 0,02 km | confere com a ficha |
| Itajaí | — | -26,9078, -48,6619 | — | — | — | 0,88 km | sem código: ponto do cadastro, fonte não confirma |
| Timbó | Rio Benedito, Rua Equador | -26,8231, -49,2708 | — | — | — | 8,22 km | **coordenada não confirmada** (decisão de 06/10/2026): pino mantido, sem fonte que situe a régua |
| Rio dos Cedros | Estação da ponte próxima ao Paço Municipal (DCSC-00011) | -26,7400, -49,2727 | DCSC-00011 | Hidro | 1 m | 16,62 km | confere com a ficha |
| Trombudo Central | Régua do Rio Trombudo (a fonte não nomeia o ponto) | -27,3053, -49,7919 | — | — | — | 10,54 km | sem código: ponto do cadastro, fonte não confirma |
| Vidal Ramos | — | -27,3855, -49,3581 | DCSC-00024 | Hidro | 1 m | 0,02 km | confere com a ficha |
| Botuverá | — | -27,1862, -49,1206 | DCSC-00018 | Hidro | 1 m | 0,04 km | confere com a ficha |
| Guabiruba | — | -27,0868, -48,9774 | DCSC-00029 | Hidro | 2 m | 4,24 km | confere com a ficha |
| Brusque | Ponte Estaiada – DCSC | -27,1007, -48,9172 | DCSC-00019 | Hidro | 3 m | 0,01 km | confere com a ficha |

## Cidades sem código: estações estaduais por perto

Não vincular por proximidade: a régua municipal e a estação estadual podem ser equipamentos
diferentes, com zeros, seções do rio ou referências diferentes. Decisão do Jefferson (06/10/2026):
fica "não confirmada" até existir documento, código comum ou comparação de referência/zero da
régua. A equivalência fica em `equivalencia_estadual` no cadastro, e o validador trava o vínculo.

| Cidade | Estação | Nome na DCSC | Distância | Equivalência |
|---|---|---|---|---|
| Lontras | DCSC-00032 | Lontras | 0,82 km | não confirmada |
| Timbó | DCSC-00023 | Timbó 1 | 1,61 km | não confirmada |
| Trombudo Central | DCSC-00035 | Trombudo Central 2 | 0,90 km | não confirmada |

Sem estação Hidro da DCSC a até 3 km: Apiúna, Itajaí.

## Réguas com coordenada própria (desenhadas no mapa uma a uma)

| Código | Cidade | Rio | Coordenada (lat, lon) | Fonte da coordenada |
|---|---|---|---|---|
| DC-01 | itajai | itajai-acu | -26,9092, -48,6516 | defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php (marcadores Leaflet), 02/09/2026 |
| DC-02 | itajai | itajai-acu | -26,8757, -48,7102 | defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php (marcadores Leaflet), 02/09/2026 |
| DC-03 | itajai | itajai-mirim | -26,9118, -48,7192 | defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php (marcadores Leaflet), 02/09/2026 |
| DC-04 | itajai | itajai-mirim | -26,8941, -48,6884 | defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php (marcadores Leaflet), 02/09/2026 |
| DC-05 | itajai | itajai-mirim | -26,9334, -48,7478 | defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php (marcadores Leaflet), 02/09/2026 |
| DC-06 | itajai | itajai-mirim | -26,9244, -48,6858 | defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php (marcadores Leaflet), 02/09/2026 |
| DC-07 | itajai | ribeirao-murta | -26,8927, -48,7356 | defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php (marcadores Leaflet), 02/09/2026 |
| DC-08 | itajai | ribeirao-canhanduba | -26,9797, -48,7119 | defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php (marcadores Leaflet), 02/09/2026 |
| DC-09 | itajai | ribeirao-murta | -26,8798, -48,7003 | defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php (marcadores Leaflet), 02/09/2026 |
| DC-10 | itajai | itajai-mirim | -27,0335, -48,8614 | defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php (marcadores Leaflet), 02/09/2026 |
| DC-11 | itajai | itajai-acu | -26,8796, -48,7615 | defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php (marcadores Leaflet), 02/09/2026 |
