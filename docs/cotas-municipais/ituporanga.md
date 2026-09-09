# Ituporanga — Itajaí do Sul (Ponte Vitório Sens)

**Prefeitura / Defesa Civil:** https://ituporanga.sc.gov.br/secretaria/view/15/defesa-civil
**Coordenador:** Elias Sieves · (47) 9148-1378 · 199
**Estação no monitor:** DCSC-00039 (datum estadual bruto, `usar_para_cota: false`)
**Régua municipal:** Ponte Vitório Sens (leitura diária compartilhada com a estadual)
**Consulta:** 8 e 9 de setembro de 2026
**Emergência:** 199. Este arquivo não substitui aviso oficial.

## Por que `cotas_m` está vazio

A SPDC/SC publica atenção > 1,40 / alerta > 1,90 / emergência > 2,60 m para
Ituporanga, mas para a estação **83250000** (ANA/EPAGRI), a 9,6 km — outra régua.
A tela lê a DCSC-00039. Ver `cotas_m_por_que_vazio` em `estacoes.json`.

## Ferramentas de 2026 (Google My Maps), lidas em 08/09/2026

| Mapa | `mid` | O que traz | Ressalva |
|---|---|---|---|
| Cotas de cheias ruas (Prefeitura, 07/10/2023) | `1o9xZ2BceCkPzaqQQ2m0HIn0ixHVOJcU` | 60 pontos, 3,38 a 10,48 m | um ponto de 27,77 m é lixo |
| Cotas com Manchas de Inundação | `19tpP2Tfsl58ue6GtY5ihBfK3MLkiUrA` | 78.547 polígonos, COTA 3,00 a 6,50 de 0,5 em 0,5 m (34 MB) | linkado pela URL `/edit` — pode ser editável por qualquer um |

KML: `https://www.google.com/maps/d/kml?mid=<mid>&forcekml=1`. Congelar snapshot
(pendência A3). Nenhum dos dois traz faixa de acionamento; as cotas de rua só
entram quando se souber a régua delas.

## Pistas que se cercam (nenhuma é faixa)

- primeira mancha: 3,00 m
- menor cota de rua: 3,38 m
- "primeira cota considerada crítica para alagamentos": 3,25 m, na região da
  antiga Lanchonete São Jorge (secretário de Planejamento Vilmar Schwambach,
  Rádio Educadora 90.3)

Pedir à Defesa Civil a tabela atenção/alerta/emergência amarrada à Ponte
Vitório Sens e o zero da régua.
